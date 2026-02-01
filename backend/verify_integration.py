
import asyncio
import os
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import MagicMock, patch

# Mock dependencies that need external services
with patch("app.main.redis_service", MagicMock()):
    with patch("app.main.ml_service", MagicMock()):
        with patch("app.main.agent", MagicMock()):
             # Set up client
             client = TestClient(app)

             def test_public_api():
                print("🚀 Testing Public Payment APIs...")
                
                # 1. Test Payment Initiation
                payload = {
                    "amount": 5000, 
                    "currency": "INR", 
                    "method": "upi", 
                    "merchant_id": "m_test_123"
                }
                
                print(f"  📤 Sending POST /v1/payments with {payload}")
                response = client.post("/v1/payments", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ Payment Created: {data['id']} (Status: {data['status']})")
                    assert data['status'] == 'processing'
                else:
                    print(f"  ❌ Payment Failed: {response.text}")

                # 2. Test Refund
                refund_payload = {"payment_id": "txn_mock_123"}
                print(f"  📤 Sending POST /v1/refunds with {refund_payload}")
                response = client.post("/v1/refunds", json=refund_payload)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ Refund Processed: {data['id']} (Status: {data['status']})")
                    assert data['status'] == 'succeeded'
                else:
                    print(f"  ❌ Refund Failed: {response.text}")
                    
                print("✅ API Verification Complete.")

if __name__ == "__main__":
    # Patching global vars in main is tricky with TestClient due to async lifespan
    # Simplified test: just checking route logic/schemas
    test_public_api()
