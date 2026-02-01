"""
ML Service - Early Failure Prediction
Uses XGBoost to predict transaction failure probability based on context.
"""

import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from datetime import datetime
import joblib
import os
import asyncio
from typing import Dict, List, Optional
import shap
import numpy as np
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

class PolicyLearner:
    """
    Contextual Bandit Policy Learner.
    Learns to predict the Utility (Reward) of an action given the context.
    Uses SGDRegressor for online learning (partial_fit).
    """
    def __init__(self):
        # We start with a simple linear model: Reward ~ w * (Context + Action)
        # Context dimensions: [RiskScore, BankHealth, IsActionRetry, IsActionSwitch, IsActionAlert, IsActionMonitor]
        self.model = SGDRegressor(learning_rate='constant', eta0=0.01)
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Action IDs for encoding
        self.actions = ["monitor", "retry", "switch_gateway", "send_alert"]
        self.action_map = {a: i for i, a in enumerate(self.actions)}
        
    def _encode_context(self, context: dict, action_name: str) -> np.ndarray:
        """Encode context and action into a feature vector"""
        # Feature 1: Risk Score (0-1)
        risk_score = context.get("risk_score", 0.0)
        
        # Feature 2: Bank Health (0-100 normalized to 0-1)
        bank_health = context.get("bank_health_score", 100.0) / 100.0
        
        # One-hot encode action
        action_vec = [0] * len(self.actions)
        if action_name in self.action_map:
            action_vec[self.action_map[action_name]] = 1
            
        return np.array([risk_score, bank_health] + action_vec).reshape(1, -1)

    def predict_utility(self, context: dict, action_name: str) -> float:
        """Predict expected utility/reward for an action in this context"""
        if not self.is_trained:
            return 0.0
            
        features = self._encode_context(context, action_name)
        return float(self.model.predict(features)[0])
        
    def update_policy(self, context: dict, action_name: str, reward: float):
        """Update model with observed reward (Online Learning)"""
        features = self._encode_context(context, action_name)
        
        # SGDRegressor.partial_fit expects arrays
        self.model.partial_fit(features, [reward])
        self.is_trained = True
        print(f"  🧠 Policy Updated: {action_name} | Reward: {reward:.2f}")

class MLService:
    def __init__(self):
        self.model: Optional[xgb.XGBClassifier] = None
        self.explainer: Optional[shap.TreeExplainer] = None
        self.policy: PolicyLearner = PolicyLearner() # Initialize Policy Learner
        self.encoders: Dict[str, LabelEncoder] = {}
        self.is_ready = False
        self.model_path = "app/models/failure_predictor.json"
        self.data_path = "../data/historical_payments.csv"
        
        # Advanced Features
        self.feature_columns = [
            'bank_encoded', 'method_encoded', 'hour', 'amount',
            'rolling_success_rate_5m', 'latency_p90', 'retry_depth', 'error_entropy'
        ]
        
    async def train_model(self):
        """Train XGBoost model + Initialize Policy"""
        try:
            print("🧠 Starting ML Model Training (Advanced Features + SHAP)...")
            
            # Pre-train the policy with some heuristic examples so it's not totally random
            # (Bootstrapping the bandit)
            print("  🤖 Bootstrapping Policy Learner...")
            
            # Example 1: High Risk -> Switch is good
            ctx_high_risk = {"risk_score": 0.9, "bank_health_score": 20}
            self.policy.update_policy(ctx_high_risk, "switch_gateway", 100)
            self.policy.update_policy(ctx_high_risk, "monitor", -50)
            
            # Example 2: Low Risk -> Monitor is good
            ctx_low_risk = {"risk_score": 0.1, "bank_health_score": 95}
            self.policy.update_policy(ctx_low_risk, "monitor", 10)
            self.policy.update_policy(ctx_low_risk, "switch_gateway", -20)
            
            # Load data
            if not os.path.exists(self.data_path):
                print(f"⚠️ Training data not found at {self.data_path}")
                return
                
            df = pd.read_csv(self.data_path)
            
            # Preprocessing
            # 1. Encode Categoricals
            le_bank = LabelEncoder()
            df['bank_encoded'] = le_bank.fit_transform(df['bank'])
            self.encoders['bank'] = le_bank
            
            le_method = LabelEncoder()
            df['method_encoded'] = le_method.fit_transform(df['payment_method'])
            self.encoders['method'] = le_method
            
            # 2. Advanced Feature Engineering
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            df['hour'] = df['timestamp'].dt.hour
            
            # Rolling Metrics (simulated for training based on bank-level history)
            # In a real system, this would be complex window functions.
            # Simplified for hackathon: calculate simulated rolling stats
            
            # Rolling Success Rate (5m)
            df['success_int'] = (df['status'] == 'success').astype(int)
            # Group by bank to get bank-specific rolling stats
            df['rolling_success_rate_5m'] = df.groupby('bank')['success_int'].transform(
                lambda x: x.rolling(window=5, min_periods=1).mean()
            ).fillna(1.0)
            
            # Latency P90 (rolling 10 txn window)
            df['latency_p90'] = df.groupby('bank')['latency_ms'].transform(
                lambda x: x.rolling(window=10, min_periods=1).quantile(0.9)
            ).fillna(200)
            
            # Retry Depth (Avg retry count rolling)
            df['retry_depth'] = df.groupby('bank')['retry_count'].transform(
                lambda x: x.rolling(window=10, min_periods=1).mean()
            ).fillna(0)
            
            # Error Entropy (Diversity of errors) - Simplified: Just unique error count in window
            df['error_entropy'] = df.groupby('bank')['error_code'].transform(
                lambda x: x.rolling(window=10, min_periods=1).apply(lambda y: len(pd.unique(y.dropna())))
            ).fillna(0)

            # Shift features to prevent leakage (we predict NEXT transaction based on PAST window)
            feature_cols_to_shift = ['rolling_success_rate_5m', 'latency_p90', 'retry_depth', 'error_entropy']
            df[feature_cols_to_shift] = df.groupby('bank')[feature_cols_to_shift].shift(1).fillna(0)
            
            # 3. Target Variable
            df['target'] = (df['status'] == 'failed').astype(int)
            
            # Select features
            X = df[self.feature_columns]
            y = df['target']
            
            # Train/Test Split
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train XGBoost
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            self.model.fit(X_train, y_train)
            
            # Initialize SHAP Explainer
            print("  📊 Initializing SHAP Explainer...")
            self.explainer = shap.TreeExplainer(self.model)
            
            # Evaluate
            accuracy = self.model.score(X_test, y_test)
            print(f"✅ ML Model Trained! Accuracy: {accuracy:.2f}")
            
            self.is_ready = True
            
        except Exception as e:
            print(f"❌ ML Training Failed: {e}")
            self.is_ready = False
            import traceback
            traceback.print_exc()

    def predict_failure_probability(self, context: dict) -> float:
        """Predict prob with context"""
        if not self.is_ready or not self.model:
            return 0.0
        
        try:
            input_df = self._prepare_input(context)
            return float(self.model.predict_proba(input_df)[0][1])
        except Exception as e:
            print(f"⚠️ Prediction Error: {e}")
            return 0.0
            
    def explain_prediction(self, context: dict) -> str:
        """Get SHAP-based explanation for prediction"""
        if not self.is_ready or not self.explainer:
            return ""
            
        try:
            input_df = self._prepare_input(context)
            shap_values = self.explainer.shap_values(input_df)
            
            # Handle standard SHAP output (list for classification) vs newer object
            if isinstance(shap_values, list): 
                shap_values = shap_values[1] # Class 1 (Failure)
                
            # Get top 3 features contributing to failure (positive SHAP values)
            feature_names = self.feature_columns
            contributions = zip(feature_names, shap_values[0])
            
            # Sort by absolute contribution or just positive contribution?
            # We want to know why it FAILED (positive contribution to class 1)
            sorted_contribs = sorted(contributions, key=lambda x: x[1], reverse=True)
            
            reasons = []
            for name, val in sorted_contribs[:3]:
                if val > 0.01: # Only significant positive contributors
                    reasons.append(f"{name} (+{val:.2f})")
            
            if not reasons:
                return "Baseline Risk"
                
            return ", ".join(reasons)
            
        except Exception as e:
            print(f"⚠️ Explainability Error: {e}")
            return "Analysis Failed"

    def _prepare_input(self, context: dict) -> pd.DataFrame:
        """Helper to prepare input DataFrame"""
        bank = context.get('bank', 'HDFC')
        method = context.get('method', 'upi')
        
        # Encode inputs
        try:
            bank_enc = self.encoders['bank'].transform([bank])[0]
        except:
            bank_enc = 0
            
        try:
            method_enc = self.encoders['method'].transform([method])[0]
        except:
            method_enc = 0
            
        return pd.DataFrame([{
            'bank_encoded': bank_enc,
            'method_encoded': method_enc,
            'hour': datetime.now().hour,
            'amount': context.get('amount', 1000.0),
            'rolling_success_rate_5m': context.get('rolling_success_rate', 0.95),
            'latency_p90': context.get('latency_p90', 200),
            'retry_depth': context.get('retry_depth', 0.1),
            'error_entropy': context.get('error_entropy', 0.5)
        }])

    def get_bank_risk_scores(self, current_stats: Dict = None) -> Dict[str, Dict]:
        """
        Get risk scores AND explanations for all banks.
        current_stats: Dict of bank -> {success_rate, latency, etc} from Redis/Sim
        Returns: Dict { "HDFC": {"risk": 0.8, "reason": "Latency P90 (+0.4)"} }
        """
        if not self.is_ready:
            return {}
            
        risks = {}
        try:
            for bank in self.encoders['bank'].classes_:
                bank_str = str(bank)
                
                # Default context (healthy)
                context = {
                    'bank': bank_str,
                    'method': 'upi',
                    'amount': 2500.0,
                    'rolling_success_rate': 0.98,
                    'latency_p90': 180,
                    'retry_depth': 0.05,
                    'error_entropy': 0.1
                }
                
                # If we have real stats, use them
                if current_stats and bank_str in current_stats:
                     stats = current_stats[bank_str]
                     context.update({
                         'rolling_success_rate': stats.get('success_rate', 98) / 100.0,
                         'latency_p90': stats.get('avg_latency', 180) * 1.5, # P90 heuristic
                         'retry_depth': 0.1, # Not tracked in simple stats yet
                         'error_entropy': 0.2
                     })
                
                prob = self.predict_failure_probability(context)
                reason = self.explain_prediction(context) if prob > 0.4 else "Healthy"
                
                risks[bank_str] = {
                    "risk": round(prob, 4), 
                    "reason": reason
                }
                
            return risks
        except Exception as e:
            print(f"risk score calc error: {e}")
            import traceback
            traceback.print_exc()
            return {}
