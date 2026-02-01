"""
Agentic Payment Operations System - FastAPI Backend
A Self-Healing Financial Nervous System
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
from datetime import datetime
from typing import List
import structlog

from app.services.ml_service import MLService

logger = structlog.get_logger()

from app.services.webhook_service import WebhookService
from pydantic import BaseModel
from app.services.redis_service import RedisService
from app.services.simulator_service import SimulatorService
from app.agent.graph import PaymentOpsAgent
from app.models.schemas import SystemMetrics, BankHealth, Intervention
# ... (Imports)

# Models for Public API
class PaymentRequest(BaseModel):
    amount: float
    currency: str = "INR"
    method: str = "upi" # upi, card, netbanking
    merchant_id: str
    description: str = "Payment Transaction"

class RefundRequest(BaseModel):
    payment_id: str
    reason: str = "requested_by_customer"

# ... (Service Globals)
# ... (Service Globals)
agent: PaymentOpsAgent = None
simulator: SimulatorService = None
redis_service: RedisService = None
ml_service: MLService = None
webhook_service: WebhookService = None

# WebSocket Connection Manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                dead_connections.append(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            self.disconnect(conn)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global agent, simulator, redis_service, ml_service, webhook_service
    
    logger.info("🚀 Starting Payment Operations Agent...")
    
    # Initialize services
    redis_service = RedisService()
    await redis_service.connect()
    
    # Initialize Webhook Service
    webhook_service = WebhookService()
    
    # Initialize and train ML model
    ml_service = MLService()
    await ml_service.train_model()
    
    simulator = SimulatorService(redis_service, ml_service)
    
    # Pass ML service to agent
    agent = PaymentOpsAgent(redis_service, manager, simulator, ml_service)
    
    # Start background tasks
    asyncio.create_task(agent.run_observation_loop())
    asyncio.create_task(simulator.run_if_enabled())
    asyncio.create_task(broadcast_loop())
    
    logger.info("✅ All services initialized")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down services...")
    await redis_service.disconnect()
    await webhook_service.close()

async def broadcast_loop():
    """Background task to broadcast real-time metrics to frontend"""
    logger.info("📡 Starting metrics broadcast loop...")
    while True:
        try:
            if redis_service and redis_service.is_connected:
                # Get latest data
                metrics = await redis_service.get_latest_metrics()
                banks = await redis_service.get_bank_health()
                
                # Broadcast if available
                if metrics:
                    await manager.broadcast({"type": "metrics", "data": metrics})
                
                if banks:
                    await manager.broadcast({"type": "banks", "data": banks})
                    
            await asyncio.sleep(1) # Broadcast every second
        except Exception as e:
            logger.error(f"Broadcast loop error: {e}")
            await asyncio.sleep(5)

# Create FastAPI app
app = FastAPI(
    title="Payment Operations Agent",
    description="Self-Healing Financial Nervous System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== PUBLIC PAYMENT API (Integration-Ready) ==============

@app.post("/v1/payments", tags=["Public API"])
async def create_payment(payment: PaymentRequest):
    """
    Standard Payment Initiation Endpoint.
    Simulates a payment gateway (like Stripe/Razorpay).
    """
    txn_id = f"txn_{int(datetime.now().timestamp() * 1000)}"
    
    logger.info(f"💳 Payment Initiated: {txn_id} for {payment.amount} {payment.currency}")
    
    # Return 'processing' status immediately (Async flow)
    response = {
        "id": txn_id,
        "object": "payment_intent",
        "amount": payment.amount,
        "currency": payment.currency,
        "status": "processing",
        "client_secret": f"sec_{txn_id}"
    }
    
    # Trigger Async Webhook (Simulate bank callback delay)
    async def process_async():
        await asyncio.sleep(2) # Bank delay
        
        # Decide success/failure based on randomness (or agent state!)
        import random
        success = random.random() > 0.1 # 90% success baseline
        
        # If High Risk, fail more often (coupling with Agent knowledge!)
        if agent and agent.tools:
            risk_map = await agent.tools.get_failure_predictions()
            hdfc_risk = risk_map.get("HDFC", {}).get("risk", 0.0)
            if hdfc_risk > 0.6:
                success = random.random() > 0.5 # 50/50 if high risk
            
        final_status = "succeeded" if success else "failed"
        
        event_type = f"payment.{final_status}"
        payload = response.copy()
        payload["status"] = final_status
        
        if not success:
            payload["failure_code"] = "bank_decline"
            payload["failure_message"] = "Bank declined transaction due to high risk"
            
        # Dispatch Webhook
        if webhook_service:
            await webhook_service.dispatch_event(event_type, payload)
            
    asyncio.create_task(process_async())
    
    return response

@app.post("/v1/refunds", tags=["Public API"])
async def create_refund(refund: RefundRequest):
    """
    Standard Refund Endpoint.
    """
    refund_id = f"re_{int(datetime.now().timestamp() * 1000)}"
    
    logger.info(f"💸 Refund Initiated: {refund_id} for {refund.payment_id}")
    
    response = {
        "id": refund_id,
        "object": "refund",
        "payment_intent": refund.payment_id,
        "status": "succeeded"
    }
    
    # Dispatch Webhook
    if webhook_service:
        await webhook_service.dispatch_event("charge.refunded", response)
        
    return response

# ============== REST API Routes ==============

@app.get("/")
async def root():
    return {
        "name": "Payment Operations Agent",
        "status": "operational",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "services": {
            "agent": agent is not None,
            "redis": redis_service.is_connected if redis_service else False,
            "simulator": simulator is not None
        }
    }

@app.get("/api/metrics", response_model=SystemMetrics)
async def get_metrics():
    """Get current system metrics"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return await agent.get_current_metrics()

@app.get("/api/banks", response_model=List[BankHealth])
async def get_bank_health():
    """Get health status of all banks/issuers"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return await agent.get_bank_health()

@app.get("/api/interventions", response_model=List[Intervention])
async def get_interventions():
    """Get recent interventions"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return await agent.get_recent_interventions()

@app.get("/api/interventions/pending")
async def get_pending_interventions():
    """Get pending interventions awaiting approval"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return list(agent.pending_interventions.values())

@app.post("/api/interventions/{intervention_id}/approve")
async def approve_intervention(intervention_id: str):
    """Approve a pending intervention"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    success = await agent.approve_intervention(intervention_id)
    if not success:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return {"status": "approved", "intervention_id": intervention_id}

@app.post("/api/interventions/{intervention_id}/reject")
async def reject_intervention(intervention_id: str):
    """Reject a pending intervention"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    success = await agent.reject_intervention(intervention_id)
    if not success:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return {"status": "rejected", "intervention_id": intervention_id}

@app.post("/api/simulator/start")
async def start_simulator():
    """Start the transaction simulator"""
    if not simulator:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    await simulator.start()
    return {"status": "started"}

@app.post("/api/simulator/stop")
async def stop_simulator():
    """Stop the transaction simulator"""
    if not simulator:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    await simulator.stop()
    return {"status": "stopped"}

@app.post("/api/simulator/scenario/custom")
async def trigger_custom_scenario(scenario: dict):
    """Trigger a custom failure scenario"""
    if not simulator:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    
    # Apply custom scenario
    target_bank = scenario.get("targetBank", "HDFC")
    failure_increase = scenario.get("failureIncrease", 20)
    latency_increase = scenario.get("latencyIncrease", 500)
    duration = scenario.get("duration", 60)
    
    # Create custom scenario
    await simulator.apply_custom_scenario(
        bank=target_bank,
        failure_rate_increase=failure_increase,
        latency_increase=latency_increase,
        duration=duration
    )
    
    # Broadcast to connected clients
    await manager.broadcast({
        "type": "scenario_triggered",
        "data": {
            "name": scenario.get("name", "Custom Scenario"),
            "target_bank": target_bank,
            "failure_increase": failure_increase,
            "latency_increase": latency_increase,
            "duration": duration
        }
    })
    
    return {"status": "triggered", "scenario": scenario}

@app.post("/api/simulator/scenario/{scenario_name}")
async def trigger_scenario(scenario_name: str):
    """Trigger a specific failure scenario"""
    if not simulator:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    success = await simulator.trigger_scenario(scenario_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_name}' not found")
    return {"status": "triggered", "scenario": scenario_name}

# ============== WEBSOCKET ENDPOINT ==============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            # Echo back or handle client commands if needed
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
