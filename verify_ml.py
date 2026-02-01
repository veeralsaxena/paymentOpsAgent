
import asyncio
import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.ml_service import MLService
from app.agent.tools import PaymentOpsTools

# Mock Redis
class MockRedis:
    def __init__(self):
        self.is_connected = True
    async def get_latest_metrics(self):
        return {"success_rate": 98.0, "avg_latency": 150, "error_rate": 2.0}
    async def get_bank_health(self):
        return [{"name": "HDFC", "status": "healthy"}, {"name": "ICICI", "status": "healthy"}]
    async def get_similar_memories(self, *args):
        return []

async def verify_ml():
    print("🚀 Starting ML Verification...")
    
    # 1. Initialize ML Service
    ml_service = MLService()
    # Mock data path to be correct relative to where we run
    ml_service.data_path = "backend/data/historical_payments.csv" 
    # Create dummy data if not exists (for this test script)
    if not os.path.exists(ml_service.data_path):
        print(f"Creating dummy data at {ml_service.data_path}")
        os.makedirs(os.path.dirname(ml_service.data_path), exist_ok=True)
        with open(ml_service.data_path, "w") as f:
            f.write("timestamp,bank,payment_method,amount,status,latency_ms,retry_count,error_code\n")
            # Add some dummy rows
            for i in range(100):
                f.write(f"2023-01-01 10:00:{i%60},HDFC,upi,1000,success,150,0,\n")
            # Add some failures
            for i in range(20):
                 f.write(f"2023-01-01 10:05:{i%60},HDFC,upi,1000,failed,500,2,504\n")
    
    await ml_service.train_model()
    
    if not ml_service.is_ready:
        print("❌ ML Service not ready.")
        return

    # 2. Test Prediction & SHAP
    print("\n📊 Testing Prediction & SHAP...")
    context = {
        'bank': 'HDFC', 'rolling_success_rate': 0.8, 'latency_p90': 400, 'retry_depth': 2
    }
    prob = ml_service.predict_failure_probability(context)
    reason = ml_service.explain_prediction(context)
    print(f"Prediction for risky context: {prob:.4f}")
    print(f"Explanation: {reason}")
    
    if prob < 0.5:
        print("⚠️ Warning: Prediction prob seems low for risky context (expected > 0.5)")
        # Force high just to check explanation if needed, but SHAP depends on model
    
    # 3. Test Tools Integration
    print("\n🛠 Testing Tools Integration...")
    tools = PaymentOpsTools(MockRedis(), ml_service=ml_service)
    
    # Force some bad simulated bank health to trigger ML context
    # We need to mock get_bank_status logic or just call get_failure_predictions
    
    predictions = await tools.get_failure_predictions()
    print(f"Tool Predictions: {predictions}")
    
    if "HDFC" in predictions and "risk" in predictions["HDFC"]:
        print("✅ Tools correctly returned ML predictions structure.")
    else:
        print("❌ Tools output format unknown or empty.")

    # 4. Test Policy Learner
    print("\n🧠 Testing Policy Learner (RL)...")
    if hasattr(ml_service, "policy"):
        ctx = {"risk_score": 0.8, "bank_health_score": 20}
        
        # Initial check
        u_switch = ml_service.policy.predict_utility(ctx, "switch_gateway")
        u_monitor = ml_service.policy.predict_utility(ctx, "monitor")
        print(f"Initial: Switch U={u_switch:.2f}, Monitor U={u_monitor:.2f}")
        
        # Train it
        print("Training: Giving positive reward for Switch in High Risk...")
        for _ in range(5):
             ml_service.policy.update_policy(ctx, "switch_gateway", 100.0)
             ml_service.policy.update_policy(ctx, "monitor", -20.0)
             
        # Check again
        u_switch_new = ml_service.policy.predict_utility(ctx, "switch_gateway")
        u_monitor_new = ml_service.policy.predict_utility(ctx, "monitor")
        print(f"Post-Train: Switch U={u_switch_new:.2f}, Monitor U={u_monitor_new:.2f}")
        
        if u_switch_new > u_switch and u_switch_new > u_monitor_new:
            print("✅ Policy Learner successfully updated weights!")
        else:
            print("❌ Policy Learner did not learn as expected.")
    else:
        print("❌ Policy Learner not found in MLService.")

    print("\n✅ Verification Complete.")

if __name__ == "__main__":
    asyncio.run(verify_ml())
