"""
Redis Service - Streaming data and caching
Handles Redis Streams for transaction data
"""

import redis.asyncio as redis
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class RedisService:
    """
    Redis service for transaction streaming and caching.
    Uses Redis Streams for high-speed transaction log ingestion.
    """
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client: Optional[redis.Redis] = None
        self.is_connected = False
        
        # Stream names
        self.TRANSACTIONS_STREAM = "transactions"
        self.METRICS_STREAM = "metrics"
        self.ALERTS_STREAM = "alerts"
        
        # Key prefixes
        self.METRICS_KEY = "current:metrics"
        self.BANK_HEALTH_KEY = "current:banks"
        self.CONFIG_KEY = "config"
        self.MEMORY_KEY = "agent:memory"
    
    async def connect(self):
        """Establish Redis connection"""
        try:
            self.client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            self.is_connected = True
            print(f"✅ Connected to Redis at {self.redis_url}")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}. Running in simulation mode.")
            self.is_connected = False
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self.is_connected = False
    
    # ============== Transactions ==============
    
    async def add_transaction(self, transaction: dict) -> str:
        """Add a transaction to the stream"""
        if not self.is_connected:
            return ""
        
        try:
            # Filter out None values - Redis can't handle them
            clean_transaction = {
                k: str(v) for k, v in transaction.items() 
                if v is not None
            }
            
            # Add to stream
            msg_id = await self.client.xadd(
                self.TRANSACTIONS_STREAM,
                clean_transaction,
                maxlen=10000  # Keep last 10k transactions
            )
            return msg_id
        except Exception as e:
            print(f"Redis add_transaction error: {e}")
            return ""
    
    async def get_recent_transactions(self, count: int = 100) -> List[dict]:
        """Get recent transactions from stream"""
        if not self.is_connected:
            return []
        
        try:
            # Read from stream
            entries = await self.client.xrevrange(
                self.TRANSACTIONS_STREAM,
                count=count
            )
            return [entry[1] for entry in entries]
        except Exception as e:
            print(f"Redis get_transactions error: {e}")
            return []
    
    # ============== Metrics ==============
    
    async def set_metrics(self, metrics: dict):
        """Update current metrics"""
        if not self.is_connected:
            return
        
        try:
            await self.client.hset(self.METRICS_KEY, mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in metrics.items()
            })
            
            # Also add to metrics stream for history
            await self.client.xadd(
                self.METRICS_STREAM,
                {"data": json.dumps(metrics)},
                maxlen=1000
            )
        except Exception as e:
            print(f"Redis set_metrics error: {e}")
    
    async def get_latest_metrics(self) -> Optional[dict]:
        """Get current metrics"""
        if not self.is_connected:
            return None
        
        try:
            data = await self.client.hgetall(self.METRICS_KEY)
            if data:
                return {
                    k: float(v) if v.replace('.', '').replace('-', '').isdigit() 
                    else json.loads(v) if v.startswith('{') or v.startswith('[')
                    else v
                    for k, v in data.items()
                }
            return None
        except Exception as e:
            print(f"Redis get_metrics error: {e}")
            return None
    
    async def get_metrics_history(self, count: int = 100) -> List[dict]:
        """Get metrics history"""
        if not self.is_connected:
            return []
        
        try:
            entries = await self.client.xrevrange(
                self.METRICS_STREAM,
                count=count
            )
            return [json.loads(entry[1].get("data", "{}")) for entry in entries]
        except Exception as e:
            print(f"Redis get_metrics_history error: {e}")
            return []
    
    # ============== Bank Health ==============
    
    async def set_bank_health(self, banks: List[dict]):
        """Update bank health status"""
        if not self.is_connected:
            return
        
        try:
            await self.client.set(
                self.BANK_HEALTH_KEY,
                json.dumps(banks)
            )
        except Exception as e:
            print(f"Redis set_bank_health error: {e}")
    
    async def get_bank_health(self) -> Optional[List[dict]]:
        """Get current bank health"""
        if not self.is_connected:
            return None
        
        try:
            data = await self.client.get(self.BANK_HEALTH_KEY)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Redis get_bank_health error: {e}")
            return None
    
    # ============== Errors ==============
    
    async def add_error(self, error: dict):
        """Add an error to the errors list"""
        if not self.is_connected:
            return
        
        try:
            await self.client.lpush("errors", json.dumps(error))
            await self.client.ltrim("errors", 0, 999)  # Keep last 1000
        except Exception as e:
            print(f"Redis add_error error: {e}")
    
    async def get_recent_errors(self, count: int = 100) -> List[dict]:
        """Get recent errors"""
        if not self.is_connected:
            return []
        
        try:
            errors = await self.client.lrange("errors", 0, count - 1)
            return [json.loads(e) for e in errors]
        except Exception as e:
            print(f"Redis get_errors error: {e}")
            return []
    
    # ============== Configuration ==============
    
    async def set_bank_config(self, config: dict):
        """Update bank routing configuration"""
        if not self.is_connected:
            return
        
        try:
            await self.client.hset(
                f"{self.CONFIG_KEY}:banks",
                mapping={k: json.dumps(v) for k, v in config.items()}
            )
        except Exception as e:
            print(f"Redis set_bank_config error: {e}")
    
    async def set_retry_config(self, config: dict):
        """Update retry configuration"""
        if not self.is_connected:
            return
        
        try:
            await self.client.hset(
                f"{self.CONFIG_KEY}:retry",
                mapping={k: str(v) for k, v in config.items()}
            )
        except Exception as e:
            print(f"Redis set_retry_config error: {e}")
    
    # ============== Alerts ==============
    
    async def add_alert(self, alert: dict):
        """Add an alert"""
        if not self.is_connected:
            return
        
        try:
            await self.client.xadd(
                self.ALERTS_STREAM,
                {"data": json.dumps(alert)},
                maxlen=500
            )
        except Exception as e:
            print(f"Redis add_alert error: {e}")
    
    async def get_alerts(self, count: int = 50) -> List[dict]:
        """Get recent alerts"""
        if not self.is_connected:
            return []
        
        try:
            entries = await self.client.xrevrange(
                self.ALERTS_STREAM,
                count=count
            )
            return [json.loads(entry[1].get("data", "{}")) for entry in entries]
        except Exception as e:
            print(f"Redis get_alerts error: {e}")
            return []
    
    # ============== Memory ==============
    
    async def store_memory(self, memory: dict):
        """Store agent memory"""
        if not self.is_connected:
            return
        
        try:
            memory_id = f"mem_{datetime.now().timestamp()}"
            await self.client.hset(
                self.MEMORY_KEY,
                memory_id,
                json.dumps(memory)
            )
        except Exception as e:
            print(f"Redis store_memory error: {e}")
    
    async def get_similar_memories(self, pattern: dict, limit: int = 5) -> List[dict]:
        """
        Get similar memories (simplified without vector search).
        In production, this would use pgvector for semantic similarity.
        """
        if not self.is_connected:
            return []
        
        try:
            all_memories = await self.client.hgetall(self.MEMORY_KEY)
            memories = [json.loads(v) for v in all_memories.values()]
            
            # Simple matching by anomaly type
            pattern_types = set(a.get("type") for a in pattern.get("anomalies", []) if isinstance(a, dict))
            
            matched = []
            for mem in memories:
                mem_types = set(a.get("type") for a in mem.get("anomaly_pattern", []) if isinstance(a, dict))
                if pattern_types & mem_types:
                    matched.append(mem)
            
            return matched[:limit]
        except Exception as e:
            print(f"Redis get_memories error: {e}")
            return []
    
    # ============== Suppression ==============
    
    async def add_suppression(self, suppression: dict):
        """Add payment method suppression"""
        if not self.is_connected:
            return
        
        try:
            await self.client.hset(
                "suppressions",
                suppression["method"],
                json.dumps(suppression)
            )
        except Exception as e:
            print(f"Redis add_suppression error: {e}")
