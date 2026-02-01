
import httpx
import asyncio
import os
from typing import Dict, Any
import structlog
from datetime import datetime

logger = structlog.get_logger()

class WebhookService:
    """
    Service to dispatch webhooks to registered merchant URLs.
    Simulates a real-world webhook delivery system (like Stripe).
    """
    def __init__(self):
        # In a real system, this would be loaded from DB per merchant
        self.default_webhook_url = os.getenv("MERCHANT_WEBHOOK_URL", "http://localhost:9000/webhook")
        self.client = httpx.AsyncClient(timeout=5.0)
        
    async def dispatch_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Dispatch an event to the merchant's webhook URL.
        
        Args:
            event_type: e.g., 'payment.success', 'payment.failed'
            payload: The data associated with the event
        """
        event_id = f"evt_{datetime.now().timestamp()}"
        
        webhook_payload = {
            "id": event_id,
            "object": "event",
            "type": event_type,
            "created": int(datetime.now().timestamp()),
            "data": {
                "object": payload
            }
        }
        
        logger.info(f"🚀 Dispatching webhook: {event_type} to {self.default_webhook_url}")
        
        # Fire and forget (or retry queue in prod)
        asyncio.create_task(self._send_request(self.default_webhook_url, webhook_payload))
        
    async def _send_request(self, url: str, payload: Dict):
        try:
            resp = await self.client.post(url, json=payload)
            if resp.status_code >= 200 and resp.status_code < 300:
                logger.info(f"✅ Webhook delivered: {payload['type']}")
            else:
                logger.warn(f"⚠️ Webhook failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"❌ Webhook dispatch error: {str(e)}")

    async def close(self):
        await self.client.aclose()
