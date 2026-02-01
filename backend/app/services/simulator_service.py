"""
Simulator Service - Payment Transaction Generator
Generates realistic payment transactions for testing the agent
"""

import asyncio
import random
from datetime import datetime
from typing import Optional, List, Dict
import json

from app.services.redis_service import RedisService
from app.models.schemas import Transaction, FailureScenario


class SimulatorService:
    """
    Payment transaction simulator.
    Generates realistic payment data and can trigger failure scenarios.
    """
    
    def __init__(self, redis_service: RedisService, ml_service=None):
        self.redis = redis_service
        self.ml = ml_service
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        
        # Configuration
        self.transactions_per_second = 50
        self.base_success_rate = 97.5
        self.base_latency_ms = 200
        
        # Banks with weights
        self.banks = {
            "HDFC": {"weight": 40, "success_modifier": 0, "latency_modifier": 0},
            "ICICI": {"weight": 30, "success_modifier": 0, "latency_modifier": 0},
            "SBI": {"weight": 20, "success_modifier": 0, "latency_modifier": 0},
            "AXIS": {"weight": 10, "success_modifier": 0, "latency_modifier": 0}
        }
        
        # Payment methods with weights
        self.payment_methods = {
            "visa": {"weight": 35, "success_modifier": 0},
            "mastercard": {"weight": 30, "success_modifier": 0},
            "upi": {"weight": 25, "success_modifier": 0},
            "rupay": {"weight": 10, "success_modifier": 0}
        }
        
        # Error codes by type
        self.error_codes = {
            "timeout": ("504", "Gateway Timeout"),
            "server_error": ("500", "Internal Server Error"),
            "bad_gateway": ("502", "Bad Gateway"),
            "rate_limit": ("429", "Too Many Requests"),
            "declined": ("400", "Transaction Declined"),
            "insufficient_funds": ("402", "Insufficient Funds")
        }
        
        # Active scenarios
        self.active_scenarios: List[dict] = []
        
        # Metrics aggregation - larger window for better per-bank accuracy
        self.metrics_window: List[dict] = []
        self.window_size = 200  # Increased for better per-bank statistics
        
        # Predefined scenarios
        self.scenarios = {
            "hdfc_timeout": FailureScenario(
                name="hdfc_timeout",
                description="HDFC Bank experiencing 504 timeouts",
                target_bank="HDFC",
                failure_increase=30,
                latency_increase_ms=800,
                duration_seconds=120
            ),
            "visa_degradation": FailureScenario(
                name="visa_degradation",
                description="Visa network degradation",
                target_method="visa",
                failure_increase=20,
                latency_increase_ms=400,
                duration_seconds=90
            ),
            "system_overload": FailureScenario(
                name="system_overload",
                description="System-wide rate limiting",
                failure_increase=15,
                latency_increase_ms=500,
                duration_seconds=60
            ),
            "bank_outage": FailureScenario(
                name="bank_outage",
                description="Complete ICICI Bank outage",
                target_bank="ICICI",
                failure_increase=95,
                latency_increase_ms=2000,
                duration_seconds=180
            )
        }
    
    async def start(self):
        """Start the transaction simulator"""
        if self.is_running:
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._run_loop())
        print(f"🚀 Transaction simulator started (ML Service: {self.ml is not None})")
    
    async def stop(self):
        """Stop the transaction simulator"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("🛑 Transaction simulator stopped")
    
    async def run_if_enabled(self):
        """Run simulator if enabled by default"""
        await asyncio.sleep(2)  # Wait for other services
        await self.start()
    
    async def trigger_scenario(self, scenario_name: str) -> bool:
        """Trigger a failure scenario"""
        if scenario_name not in self.scenarios:
            return False
        
        scenario = self.scenarios[scenario_name]
        
        # Apply scenario modifiers
        end_time = datetime.now().timestamp() + scenario.duration_seconds
        
        scenario_data = {
            "scenario": scenario,
            "end_time": end_time,
            "started_at": datetime.now().isoformat()
        }
        
        self.active_scenarios.append(scenario_data)
        
        # Apply modifiers to banks/methods
        if scenario.target_bank and scenario.target_bank in self.banks:
            self.banks[scenario.target_bank]["success_modifier"] = -scenario.failure_increase
            self.banks[scenario.target_bank]["latency_modifier"] = scenario.latency_increase_ms
        
        if scenario.target_method and scenario.target_method in self.payment_methods:
            self.payment_methods[scenario.target_method]["success_modifier"] = -scenario.failure_increase
        
        print(f"⚡ Triggered scenario: {scenario.description}")
        return True
    
    async def apply_custom_scenario(
        self, 
        bank: str, 
        failure_rate_increase: float, 
        latency_increase: float, 
        duration: int
    ):
        """Apply a custom failure scenario"""
        # Create a custom scenario
        scenario = FailureScenario(
            name="custom",
            description=f"Custom scenario on {bank}",
            target_bank=bank if bank != "ALL" else None,
            failure_increase=failure_rate_increase,
            latency_increase_ms=latency_increase,
            duration_seconds=duration
        )
        
        end_time = datetime.now().timestamp() + duration
        
        scenario_data = {
            "scenario": scenario,
            "end_time": end_time,
            "started_at": datetime.now().isoformat()
        }
        
        self.active_scenarios.append(scenario_data)
        
        # Apply modifiers
        if bank != "ALL" and bank in self.banks:
            self.banks[bank]["success_modifier"] = -failure_rate_increase
            self.banks[bank]["latency_modifier"] = latency_increase
        elif bank == "ALL":
            for b in self.banks:
                self.banks[b]["success_modifier"] = -failure_rate_increase / len(self.banks)
                self.banks[b]["latency_modifier"] = latency_increase / 2
        
        print(f"💥 Custom scenario applied: {bank} +{failure_rate_increase}% failures, +{latency_increase}ms latency for {duration}s")
    
    async def _run_loop(self):
        """Main simulation loop"""
        while self.is_running:
            try:
                # Generate batch of transactions
                batch_size = max(1, self.transactions_per_second // 10)
                
                transactions = []
                for _ in range(batch_size):
                    txn = self._generate_transaction()
                    transactions.append(txn)
                    
                    # Add to metrics window
                    self.metrics_window.append({
                        "success": txn["status"] == "success",
                        "latency": txn["latency_ms"],
                        "bank": txn["bank"]
                    })
                    
                    # Keep window bounded
                    if len(self.metrics_window) > self.window_size:
                        self.metrics_window.pop(0)
                
                # Push to Redis
                if self.redis.is_connected:
                    for txn in transactions:
                        await self.redis.add_transaction(txn)
                    
                    # Update metrics
                    metrics = self._calculate_metrics()
                    await self.redis.set_metrics(metrics)
                    
                    # Update bank health
                    bank_health = self._calculate_bank_health()
                    await self.redis.set_bank_health(bank_health)
                
                # Check for expired scenarios
                self._cleanup_scenarios()
                
                # Sleep for interval
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Simulator error: {e}")
                await asyncio.sleep(1)
    
    def _generate_transaction(self) -> dict:
        """Generate a single transaction"""
        # Select bank based on weights
        bank = self._weighted_random(self.banks)
        bank_config = self.banks[bank]
        
        # Select payment method
        method = self._weighted_random(self.payment_methods)
        method_config = self.payment_methods[method]
        
        # Calculate success rate with modifiers
        success_rate = self.base_success_rate
        success_rate += bank_config.get("success_modifier", 0)
        success_rate += method_config.get("success_modifier", 0)
        
        # Apply any global modifiers from scenarios
        for scenario_data in self.active_scenarios:
            scenario = scenario_data["scenario"]
            if not scenario.target_bank and not scenario.target_method:
                success_rate -= scenario.failure_increase
        
        success_rate = max(0, min(100, success_rate))
        
        # Determine success
        is_success = random.random() * 100 < success_rate
        
        # Calculate latency
        latency = self.base_latency_ms
        latency += random.uniform(-50, 100)
        latency += bank_config.get("latency_modifier", 0)
        
        if not is_success:
            latency += random.uniform(100, 500)  # Failures take longer
        
        latency = max(50, latency)
        
        # Generate error code if failed
        error_code = None
        if not is_success:
            error_type = random.choice(list(self.error_codes.keys()))
            error_code = self.error_codes[error_type][0]
        
        # Generate transaction
        return {
            "id": f"txn_{random.randint(100000, 999999)}",
            "amount": round(random.uniform(10, 5000), 2),
            "currency": "INR",
            "payment_method": method,
            "bank": bank,
            "status": "success" if is_success else "failed",
            "error_code": error_code,
            "latency_ms": round(latency, 2),
            "timestamp": datetime.now().isoformat(),
            "retry_count": 0
        }
    
    def _weighted_random(self, options: dict) -> str:
        """Select randomly based on weights"""
        total = sum(opt.get("weight", 1) for opt in options.values())
        r = random.uniform(0, total)
        
        cumulative = 0
        for key, opt in options.items():
            cumulative += opt.get("weight", 1)
            if r <= cumulative:
                return key
        
        return list(options.keys())[0]
    
    def _calculate_metrics(self) -> dict:
        """Calculate current metrics from window"""
        if not self.metrics_window:
            return {
                "success_rate": self.base_success_rate,
                "avg_latency": self.base_latency_ms,
                "transaction_volume": self.transactions_per_second * 60,
                "error_rate": 100 - self.base_success_rate,
                "timestamp": datetime.now().isoformat()
            }
        
        successes = sum(1 for m in self.metrics_window if m["success"])
        success_rate = (successes / len(self.metrics_window)) * 100
        
        avg_latency = sum(m["latency"] for m in self.metrics_window) / len(self.metrics_window)
        
        return {
            "success_rate": round(success_rate, 2),
            "avg_latency": round(avg_latency, 2),
            "transaction_volume": self.transactions_per_second * 60,
            "error_rate": round(100 - success_rate, 2),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_bank_health(self) -> List[dict]:
        """Calculate health for each bank - isolated per-bank metrics"""
        bank_metrics = {bank: {"success": 0, "total": 0, "latency": []} for bank in self.banks}
        
        for m in self.metrics_window:
            bank = m.get("bank")
            if bank in bank_metrics:
                bank_metrics[bank]["total"] += 1
                if m["success"]:
                    bank_metrics[bank]["success"] += 1
                bank_metrics[bank]["latency"].append(m["latency"])
        
        health = []
        for bank, config in self.banks.items():
            metrics = bank_metrics[bank]
            
            # Get the current success modifier for this specific bank
            bank_success_modifier = config.get("success_modifier", 0)
            
            # If no transactions yet for this bank, use base rate adjusted by any active modifiers
            if metrics["total"] == 0:
                # Use base success rate adjusted by this bank's specific modifier
                success_rate = max(0, min(100, self.base_success_rate + bank_success_modifier))
                avg_latency = self.base_latency_ms + config.get("latency_modifier", 0)
            elif metrics["total"] < 5:
                # Not enough samples yet - blend with expected rate
                measured_rate = (metrics["success"] / metrics["total"]) * 100
                expected_rate = max(0, min(100, self.base_success_rate + bank_success_modifier))
                # Weight more toward expected when we have fewer samples
                weight = metrics["total"] / 5
                success_rate = (measured_rate * weight) + (expected_rate * (1 - weight))
                avg_latency = sum(metrics["latency"]) / len(metrics["latency"]) if metrics["latency"] else self.base_latency_ms
            else:
                # Enough samples - use measured values
                success_rate = (metrics["success"] / metrics["total"]) * 100
                avg_latency = sum(metrics["latency"]) / len(metrics["latency"]) if metrics["latency"] else self.base_latency_ms
            
            # Determine status
            status = "healthy"
            if success_rate < 90:
                status = "degraded"
            if success_rate < 70:
                status = "down"
            
            bank_data = {
                "name": bank,
                "display_name": f"{bank} Bank",
                "status": status,
                "success_rate": round(success_rate, 2),
                "avg_latency": round(avg_latency, 2),
                "weight": config["weight"],
                "last_updated": datetime.now().isoformat()
            }
            
            # Enrich with ML predictions if available
            if self.ml:
                predictions = self.ml.get_bank_risk_scores()
                bank_data["predicted_failure_probability"] = predictions.get(bank, 0.0)
            
            health.append(bank_data)
        
        return health
    
    def _cleanup_scenarios(self):
        """Remove expired scenarios"""
        now = datetime.now().timestamp()
        
        expired = [s for s in self.active_scenarios if s["end_time"] < now]
        
        for scenario_data in expired:
            scenario = scenario_data["scenario"]
            
            # Remove modifiers
            if scenario.target_bank and scenario.target_bank in self.banks:
                self.banks[scenario.target_bank]["success_modifier"] = 0
                self.banks[scenario.target_bank]["latency_modifier"] = 0
            
            if scenario.target_method and scenario.target_method in self.payment_methods:
                self.payment_methods[scenario.target_method]["success_modifier"] = 0
            
            print(f"✅ Scenario ended: {scenario.name}")
        
        self.active_scenarios = [s for s in self.active_scenarios if s["end_time"] >= now]
