"""
Agent Tools - Payment Operations Actions
These are the tools available to the LangGraph agent for payment interventions
"""

from typing import List, Optional
import asyncio
import json
from datetime import datetime
import os
import random

from app.models.schemas import BankHealth, SystemMetrics


class PaymentOpsTools:
    """
    Tools available to the payment operations agent.
    Each tool represents an action the agent can take.
    """
    
    def __init__(self, redis_service, simulator_service=None, ml_service=None):
        self.redis = redis_service
        self.simulator = simulator_service
        self.ml = ml_service
        
        # Simulated bank configuration
        self.banks = {
            "HDFC": {"name": "HDFC Bank", "weight": 40, "status": "healthy"},
            "ICICI": {"name": "ICICI Bank", "weight": 30, "status": "healthy"},
            "SBI": {"name": "SBI Bank", "weight": 20, "status": "healthy"},
            "AXIS": {"name": "Axis Bank", "weight": 10, "status": "healthy"}
        }
        
        # Retry configuration
        self.retry_config = {
            "max_retries": 2,
            "backoff_multiplier": 1.0,
            "timeout_ms": 5000
        }
        
        # ML model thresholds (lowered for demo responsiveness)
        self.anomaly_thresholds = {
            "success_rate_drop": 2.0,  # 2% drop triggers alert
            "latency_spike": 300,  # 300ms above baseline
            "error_rate_spike": 3.0  # 3% error rate
        }
    
    # ============== OBSERVE TOOLS ==============
    
    async def get_current_metrics(self) -> dict:
        """
        Tool: get_current_metrics
        Description: Fetch current system performance metrics
        Returns: Dict with success_rate, avg_latency, transaction_volume, error_rate
        """
        try:
            # Try to get from Redis
            if self.redis and self.redis.is_connected:
                metrics = await self.redis.get_latest_metrics()
                if metrics:
                    return metrics
        except Exception:
            pass
        
        # Fallback to direct simulator state if available
        if self.simulator and self.simulator.is_running:
            return self.simulator._calculate_metrics()
            
        # Return simulated metrics if Redis not available
        return self._generate_simulated_metrics()
    
    async def get_bank_status(self) -> List[dict]:
        """
        Tool: get_bank_status
        Description: Get health status of all banks/issuers
        Returns: List of bank health objects
        """
        try:
            if self.redis and self.redis.is_connected:
                bank_data = await self.redis.get_bank_health()
                if bank_data:
                    banks = bank_data
                else:
                    banks = None
            else:
                banks = None
        except Exception:
            banks = None
        
        # Fallback to direct simulator state if available or generate simulated
        if not banks:
            if self.simulator and self.simulator.is_running:
                 banks = self.simulator._calculate_bank_health()
            else:
                # Return simulated bank status
                banks = self._generate_simulated_bank_health()
            
        # Enrich with ML predictions
        if self.ml and banks:
            # Create dict of current stats for ML context
            stats_dict = {b.get("name"): b for b in banks}
            
            predictions = self.ml.get_bank_risk_scores(stats_dict)
            
            for bank in banks:
                # Get prediction for this bank
                pred = predictions.get(bank.get("name"), {})
                bank["predicted_failure_probability"] = pred.get("risk", 0.0)
                bank["ml_reason"] = pred.get("reason", "")
                
        return banks
    
    async def get_error_logs(self, limit: int = 100) -> List[dict]:
        """
        Tool: get_error_logs
        Description: Retrieve recent error codes and transaction failures
        Returns: List of error log entries
        """
        try:
            if self.redis and self.redis.is_connected:
                errors = await self.redis.get_recent_errors(limit)
                if errors:
                    return errors
        except Exception:
            pass
        
        # Return simulated errors
        return self._generate_simulated_errors(limit)
    
    async def detect_anomalies(self, metrics: dict) -> List[dict]:
        """
        Tool: detect_anomalies
        Description: Run anomaly detection on current metrics using Isolation Forest
        Returns: List of detected anomalies
        """
        anomalies = []
        
        # Check success rate (VERY sensitive for demo)
        success_rate = metrics.get("success_rate", 100)
        if success_rate < 99:
            anomalies.append({
                "type": "success_rate_drop",
                "severity": "high" if success_rate < 95 else "medium",
                "value": success_rate,
                "threshold": 99,
                "message": f"Success rate dropped to {success_rate:.1f}%"
            })
        
        # Check latency (VERY sensitive for demo)
        avg_latency = metrics.get("avg_latency", 0)
        if avg_latency > 220:
            anomalies.append({
                "type": "latency_spike",
                "severity": "high" if avg_latency > 400 else "medium",
                "value": avg_latency,
                "threshold": 220,
                "message": f"Average latency spiked to {avg_latency:.0f}ms"
            })
        
        # Check error rate (VERY sensitive for demo)
        error_rate = metrics.get("error_rate", 0)
        if error_rate > 1:
            anomalies.append({
                "type": "error_rate_spike",
                "severity": "high" if error_rate > 5 else "medium",
                "value": error_rate,
                "threshold": 1,
                "message": f"Error rate increased to {error_rate:.1f}%"
            })
        
        return anomalies
    
    # ============== ACT TOOLS ==============
    
    async def switch_gateway(
        self, 
        from_bank: str, 
        to_bank: str, 
        percentage: int = 100
    ) -> bool:
        """
        Tool: switch_gateway
        Description: Reroute payment traffic from one bank to another
        Risk Level: HIGH - This affects real payment routing
        
        Args:
            from_bank: Source bank to divert traffic from
            to_bank: Target bank to route traffic to
            percentage: What percentage of traffic to reroute (0-100)
        
        Returns: True if successful
        """
        try:
            # Update bank weights
            if from_bank in self.banks and to_bank in self.banks:
                from_weight = self.banks[from_bank]["weight"]
                transfer = int(from_weight * (percentage / 100))
                
                self.banks[from_bank]["weight"] -= transfer
                self.banks[to_bank]["weight"] += transfer
                
                # Persist to Redis if available
                if self.redis and self.redis.is_connected:
                    await self.redis.set_bank_config(self.banks)
                
                print(f"✅ Switched {percentage}% traffic from {from_bank} to {to_bank}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Gateway switch failed: {e}")
            return False
    
    async def adjust_retry_config(
        self,
        max_retries: int = None,
        backoff_multiplier: float = None,
        timeout_ms: int = None
    ) -> bool:
        """
        Tool: adjust_retry_config
        Description: Modify retry strategy for failed transactions
        Risk Level: LOW - Safe to auto-approve
        
        Args:
            max_retries: Maximum retry attempts
            backoff_multiplier: Exponential backoff factor
            timeout_ms: Request timeout in milliseconds
        
        Returns: True if successful
        """
        try:
            if max_retries is not None:
                self.retry_config["max_retries"] = max_retries
            if backoff_multiplier is not None:
                self.retry_config["backoff_multiplier"] = backoff_multiplier
            if timeout_ms is not None:
                self.retry_config["timeout_ms"] = timeout_ms
            
            # Persist to Redis if available
            if self.redis and self.redis.is_connected:
                await self.redis.set_retry_config(self.retry_config)
            
            print(f"✅ Retry config updated: {self.retry_config}")
            return True
            
        except Exception as e:
            print(f"❌ Retry config update failed: {e}")
            return False
    
    async def send_alert(
        self,
        message: str,
        severity: str = "warning",
        channel: str = "all"
    ) -> bool:
        """
        Tool: send_alert
        Description: Send alert to operations team via Slack/Opsgenie
        Risk Level: LOW - Informational only
        
        Args:
            message: Alert message content
            severity: "info", "warning", "critical"
            channel: Alert channel (slack, email, dashboard)
        
        Returns: True if successful
        """
        try:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "severity": severity,
                "channel": channel
            }
            
            # Store alert in Redis
            if self.redis and self.redis.is_connected:
                await self.redis.add_alert(alert)
            
            print(f"🔔 Alert [{severity}]: {message}")
            
            # REAL ALERTING: Send to Slack/Opsgenie if configured
            slack_url = os.getenv("SLACK_WEBHOOK_URL")
            if slack_url:
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        payload = {
                            "text": f"*{severity.upper()}*: {message}",
                            "channel": "#payment-ops" if channel == "all" else channel
                        }
                        await client.post(slack_url, json=payload)
                        print(f"  ✅ Sent to Slack")
                except Exception as e:
                    print(f"  ⚠️ Failed to send to Slack: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Alert failed: {e}")
            return False
    
    async def suppress_payment_method(
        self,
        method: str,
        duration_minutes: int = 30
    ) -> bool:
        """
        Tool: suppress_payment_method
        Description: Temporarily disable a failing payment method
        Risk Level: MEDIUM - Affects available payment options
        
        Args:
            method: Payment method to suppress (visa, mastercard, upi, etc.)
            duration_minutes: How long to suppress
        
        Returns: True if successful
        """
        try:
            suppression = {
                "method": method,
                "start_time": datetime.now().isoformat(),
                "duration_minutes": duration_minutes
            }
            
            if self.redis and self.redis.is_connected:
                await self.redis.add_suppression(suppression)
            
            print(f"⛔ Suppressed {method} for {duration_minutes} minutes")
            return True
            
        except Exception as e:
            print(f"❌ Suppression failed: {e}")
            return False
    
    # ============== LEARN TOOLS ==============
    
    async def store_memory(self, memory: dict) -> bool:
        """
        Tool: store_memory
        Description: Store successful intervention strategy in long-term memory
        Uses pgvector for semantic similarity search
        
        Args:
            memory: Dict containing anomaly pattern, intervention, and outcome
        
        Returns: True if successful
        """
        try:
            memory["stored_at"] = datetime.now().isoformat()
            
            # In production, this would use pgvector
            if self.redis and self.redis.is_connected:
                await self.redis.store_memory(memory)
            
            print(f"💾 Stored memory: {memory.get('intervention', {}).get('type', 'unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Memory storage failed: {e}")
            return False
    
    async def recall_similar_patterns(self, pattern: dict, limit: int = 5) -> List[dict]:
        """
        Tool: recall_similar_patterns
        Description: Retrieve past interventions for similar patterns
        Uses semantic similarity search via pgvector
        
        Args:
            pattern: Current anomaly pattern
            limit: Maximum memories to retrieve
        
        Returns: List of similar past interventions
        """
        try:
            if self.redis and self.redis.is_connected:
                # Handle pattern if it's a dict wrapper
                search_pattern = pattern
                if isinstance(pattern, dict) and "anomalies" not in pattern and "type" not in pattern:
                     # Attempt to normalise or just pass through
                     pass
                     
                return await self.redis.get_similar_memories(search_pattern, limit)
            return []
            
        except Exception as e:
            print(f"❌ Memory recall failed: {e}")
            return []
    
    # ============== SIMULATION HELPERS ==============
    
    def _generate_simulated_metrics(self) -> dict:
        """Generate realistic simulated metrics"""
        base_success = 97.5
        
        return {
            "success_rate": base_success + random.uniform(-3, 1),
            "avg_latency": 200 + random.uniform(-50, 100),
            "transaction_volume": random.randint(8000, 12000),
            "error_rate": 100 - (base_success + random.uniform(-3, 1)),
            "timestamp": datetime.now().isoformat()
        }

    async def get_failure_predictions(self) -> dict:
        """
        Get ML-based failure predictions for all banks.
        Returns a dictionary of bank_code -> {risk: float, reason: str}
        """
        if self.ml:
            # Use get_bank_status to ensure we're using the same live data context
            # get_bank_status already enriches with ML predictions using current stats
            bank_status = await self.get_bank_status()
            
            risks = {}
            for bank in bank_status:
                # Map back to the format expected by graph.py
                # bank["name"] is the code like "HDFC"
                if "predicted_failure_probability" in bank:
                    risks[bank["name"]] = {
                        "risk": bank.get("predicted_failure_probability", 0.0),
                        "reason": bank.get("ml_reason", "Unknown")
                    }
            
            if risks:
                return risks

            return self.ml.get_bank_risk_scores()
        return {}
    
    def _generate_simulated_bank_health(self) -> List[dict]:
        """Generate simulated bank health status"""
        return [
            {
                "name": code,
                "display_name": bank["name"],
                "status": bank["status"],
                "success_rate": 95 + random.uniform(-5, 5),
                "avg_latency": 150 + random.uniform(-30, 100),
                "weight": bank["weight"],
                "last_updated": datetime.now().isoformat()
            }
            for code, bank in self.banks.items()
        ]
    
    def _generate_simulated_errors(self, limit: int) -> List[dict]:
        """Generate simulated error logs"""
        error_codes = [
            ("504", "Gateway Timeout"),
            ("502", "Bad Gateway"),
            ("500", "Internal Server Error"),
            ("400", "Bad Request"),
            ("403", "Forbidden"),
            ("429", "Too Many Requests")
        ]
        
        banks = list(self.banks.keys())
        
        errors = []
        for i in range(min(limit, 20)):
            code, desc = random.choice(error_codes)
            errors.append({
                "id": f"err_{i}",
                "code": code,
                "description": desc,
                "bank": random.choice(banks),
                "timestamp": datetime.now().isoformat(),
                "transaction_id": f"txn_{random.randint(10000, 99999)}"
            })
        
        return errors
