"""
ML Failure Predictor - XGBoost
Predictive throttling and failure probability estimation
"""

import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os


class FailurePredictor:
    """
    XGBoost-based failure probability predictor.
    Implements predictive throttling by forecasting issuer load and failure probability.
    """
    
    def __init__(self):
        self.model: Optional[XGBClassifier] = None
        self.scaler = StandardScaler()
        self.bank_encoder = LabelEncoder()
        self.method_encoder = LabelEncoder()
        self.is_trained = False
        
        # Feature columns
        self.feature_columns = [
            'bank_encoded',
            'method_encoded',
            'hour_of_day',
            'day_of_week',
            'recent_success_rate',
            'recent_latency',
            'recent_volume',
            'bank_success_rate',
            'bank_latency',
            'method_success_rate'
        ]
        
        # Known banks and methods
        self.known_banks = ['HDFC', 'ICICI', 'SBI', 'AXIS', 'KOTAK', 'YES', 'UNKNOWN']
        self.known_methods = ['visa', 'mastercard', 'upi', 'rupay', 'amex', 'unknown']
        
        # Prediction cache
        self.prediction_cache: Dict[str, Dict] = {}
        self.cache_ttl_seconds = 60
        
        # Model path
        self.model_path = os.path.join(os.path.dirname(__file__), 'models', 'failure_predictor.joblib')
    
    def train(self, data: pd.DataFrame) -> bool:
        """
        Train the XGBoost failure predictor.
        
        Args:
            data: DataFrame with transaction history including 'success' column
        
        Returns:
            True if training successful
        """
        try:
            if 'success' not in data.columns:
                raise ValueError("Data must contain 'success' column")
            
            if len(data) < 500:
                print("Warning: Less than 500 samples, model may not be reliable")
            
            # Fit encoders
            self.bank_encoder.fit(self.known_banks)
            self.method_encoder.fit(self.known_methods)
            
            # Prepare features
            X, y = self._prepare_training_data(data)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train XGBoost
            self.model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                objective='binary:logistic',
                random_state=42,
                n_jobs=-1,
                eval_metric='auc'
            )
            self.model.fit(X_scaled, y)
            
            self.is_trained = True
            
            # Save model
            self._save_model()
            
            # Calculate feature importance
            importance = dict(zip(self.feature_columns, self.model.feature_importances_))
            print(f"✅ Failure predictor trained on {len(data)} samples")
            print(f"Top features: {sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Training failed: {e}")
            return False
    
    def predict_failure_probability(
        self,
        bank: str,
        payment_method: str,
        current_metrics: Dict,
        bank_metrics: Optional[Dict] = None
    ) -> Dict:
        """
        Predict failure probability for a specific bank/method combination.
        
        Args:
            bank: Bank/issuer code
            payment_method: Payment method
            current_metrics: Current system metrics
            bank_metrics: Optional bank-specific metrics
        
        Returns:
            Dict with probability, risk_level, and recommendation
        """
        # Check cache
        cache_key = f"{bank}_{payment_method}"
        if cache_key in self.prediction_cache:
            cached = self.prediction_cache[cache_key]
            if (datetime.now() - cached['timestamp']).seconds < self.cache_ttl_seconds:
                return cached['prediction']
        
        # Calculate features
        features = self._calculate_prediction_features(
            bank, payment_method, current_metrics, bank_metrics
        )
        
        if self.is_trained and self.model is not None:
            prediction = self._ml_predict(features)
        else:
            prediction = self._rule_based_predict(features, bank_metrics)
        
        # Cache result
        self.prediction_cache[cache_key] = {
            'timestamp': datetime.now(),
            'prediction': prediction
        }
        
        return prediction
    
    def predict_throttling_need(
        self,
        bank_metrics: List[Dict],
        time_horizon_minutes: int = 5
    ) -> List[Dict]:
        """
        Predict which banks need proactive throttling.
        
        Args:
            bank_metrics: List of bank health metrics
            time_horizon_minutes: Prediction horizon
        
        Returns:
            List of throttling recommendations
        """
        recommendations = []
        
        for bank in bank_metrics:
            bank_name = bank.get('name', 'UNKNOWN')
            success_rate = bank.get('success_rate', 100)
            latency = bank.get('avg_latency', 200)
            weight = bank.get('weight', 0)
            
            # Skip banks with no traffic
            if weight == 0:
                continue
            
            # Calculate load factor
            load_factor = weight / 100  # Normalized
            
            # Trend analysis
            trend = self._analyze_trend(bank_name)
            
            # Predict future state
            predicted_success = success_rate + trend.get('success_rate_slope', 0) * time_horizon_minutes
            predicted_latency = latency + trend.get('latency_slope', 0) * time_horizon_minutes
            
            # Risk assessment
            risk_score = self._calculate_risk_score(
                current_success=success_rate,
                predicted_success=predicted_success,
                current_latency=latency,
                predicted_latency=predicted_latency,
                load_factor=load_factor
            )
            
            if risk_score > 0.5:
                action = 'reroute' if risk_score > 0.7 else 'reduce_traffic'
                percentage = min(90, int(risk_score * 100))
                
                recommendations.append({
                    'bank': bank_name,
                    'risk_score': risk_score,
                    'action': action,
                    'percentage': percentage,
                    'reason': f"Predicted success rate: {predicted_success:.1f}%, latency: {predicted_latency:.0f}ms",
                    'urgency': 'high' if risk_score > 0.7 else 'medium',
                    'time_horizon_minutes': time_horizon_minutes
                })
        
        # Sort by risk
        recommendations.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return recommendations
    
    def _prepare_training_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from raw transactions"""
        features = []
        labels = []
        
        for i in range(len(data)):
            row = data.iloc[i]
            
            # Encode categorical
            bank = row.get('bank', 'UNKNOWN')
            bank = bank if bank in self.known_banks else 'UNKNOWN'
            bank_encoded = self.bank_encoder.transform([bank])[0]
            
            method = row.get('payment_method', 'unknown')
            method = method if method in self.known_methods else 'unknown'
            method_encoded = self.method_encoder.transform([method])[0]
            
            # Time features
            timestamp = pd.to_datetime(row.get('timestamp', datetime.now()))
            hour = timestamp.hour
            dow = timestamp.dayofweek
            
            # Rolling metrics (mock if not available)
            recent_success = row.get('recent_success_rate', 95)
            recent_latency = row.get('recent_latency', 200)
            recent_volume = row.get('recent_volume', 10000)
            bank_success = row.get('bank_success_rate', 95)
            bank_latency = row.get('bank_latency', 200)
            method_success = row.get('method_success_rate', 95)
            
            features.append([
                bank_encoded,
                method_encoded,
                hour,
                dow,
                recent_success,
                recent_latency,
                recent_volume,
                bank_success,
                bank_latency,
                method_success
            ])
            
            # Label: 1 for failure, 0 for success
            success = row.get('success', True)
            labels.append(0 if success else 1)
        
        return np.array(features), np.array(labels)
    
    def _calculate_prediction_features(
        self,
        bank: str,
        payment_method: str,
        current_metrics: Dict,
        bank_metrics: Optional[Dict]
    ) -> Dict:
        """Calculate features for prediction"""
        now = datetime.now()
        
        # Encode
        bank = bank if bank in self.known_banks else 'UNKNOWN'
        method = payment_method if payment_method in self.known_methods else 'unknown'
        
        bank_encoded = self.bank_encoder.transform([bank])[0] if self.is_trained else 0
        method_encoded = self.method_encoder.transform([method])[0] if self.is_trained else 0
        
        return {
            'bank_encoded': bank_encoded,
            'method_encoded': method_encoded,
            'hour_of_day': now.hour,
            'day_of_week': now.weekday(),
            'recent_success_rate': current_metrics.get('success_rate', 95),
            'recent_latency': current_metrics.get('avg_latency', 200),
            'recent_volume': current_metrics.get('transaction_volume', 10000),
            'bank_success_rate': bank_metrics.get('success_rate', 95) if bank_metrics else 95,
            'bank_latency': bank_metrics.get('avg_latency', 200) if bank_metrics else 200,
            'method_success_rate': 95  # Would need method-specific tracking
        }
    
    def _ml_predict(self, features: Dict) -> Dict:
        """Make prediction using trained model"""
        try:
            X = np.array([[
                features['bank_encoded'],
                features['method_encoded'],
                features['hour_of_day'],
                features['day_of_week'],
                features['recent_success_rate'],
                features['recent_latency'],
                features['recent_volume'],
                features['bank_success_rate'],
                features['bank_latency'],
                features['method_success_rate']
            ]])
            
            X_scaled = self.scaler.transform(X)
            
            # Get probability
            proba = self.model.predict_proba(X_scaled)[0][1]  # Probability of failure
            
            # Determine risk level
            if proba > 0.7:
                risk_level = 'critical'
                recommendation = 'Immediately reroute traffic to backup'
            elif proba > 0.5:
                risk_level = 'high'
                recommendation = 'Consider reducing traffic to this path'
            elif proba > 0.3:
                risk_level = 'medium'
                recommendation = 'Monitor closely, prepare backup'
            else:
                risk_level = 'low'
                recommendation = 'Normal operation'
            
            return {
                'failure_probability': float(proba),
                'risk_level': risk_level,
                'recommendation': recommendation,
                'confidence': 0.85,  # Model confidence
                'source': 'ml'
            }
            
        except Exception as e:
            print(f"ML prediction error: {e}")
            return self._rule_based_predict(features, None)
    
    def _rule_based_predict(self, features: Dict, bank_metrics: Optional[Dict]) -> Dict:
        """Rule-based fallback prediction"""
        success_rate = features.get('bank_success_rate', 95)
        latency = features.get('bank_latency', 200)
        
        # Simple risk calculation
        risk = 0.0
        
        if success_rate < 90:
            risk += 0.3
        if success_rate < 80:
            risk += 0.3
        if latency > 400:
            risk += 0.2
        if latency > 600:
            risk += 0.2
        
        # Time-based risk (higher during peak hours)
        hour = features.get('hour_of_day', 12)
        if 10 <= hour <= 14 or 18 <= hour <= 21:
            risk += 0.1  # Peak hours
        
        risk = min(1.0, risk)
        
        if risk > 0.6:
            risk_level = 'high'
            recommendation = 'Consider traffic rerouting'
        elif risk > 0.3:
            risk_level = 'medium'
            recommendation = 'Monitor closely'
        else:
            risk_level = 'low'
            recommendation = 'Normal operation'
        
        return {
            'failure_probability': risk,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'confidence': 0.5,  # Lower confidence for rules
            'source': 'rule-based'
        }
    
    def _analyze_trend(self, bank_name: str) -> Dict:
        """Analyze trend for a bank (simplified)"""
        # In production, this would use historical data
        return {
            'success_rate_slope': -0.1,  # Slight decline per minute
            'latency_slope': 2  # Slight increase per minute
        }
    
    def _calculate_risk_score(
        self,
        current_success: float,
        predicted_success: float,
        current_latency: float,
        predicted_latency: float,
        load_factor: float
    ) -> float:
        """Calculate composite risk score"""
        risk = 0.0
        
        # Success rate risk
        if predicted_success < 85:
            risk += 0.4
        elif predicted_success < 90:
            risk += 0.2
        
        # Decline risk
        decline = current_success - predicted_success
        if decline > 5:
            risk += 0.3
        elif decline > 2:
            risk += 0.1
        
        # Latency risk
        if predicted_latency > 500:
            risk += 0.2
        
        # Load amplification
        risk *= (1 + load_factor)
        
        return min(1.0, risk)
    
    def _save_model(self):
        """Save model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'bank_encoder': self.bank_encoder,
                'method_encoder': self.method_encoder
            }, self.model_path)
            print(f"Model saved to {self.model_path}")
        except Exception as e:
            print(f"Failed to save model: {e}")
    
    def load_model(self) -> bool:
        """Load model from disk"""
        try:
            if os.path.exists(self.model_path):
                data = joblib.load(self.model_path)
                self.model = data['model']
                self.scaler = data['scaler']
                self.bank_encoder = data['bank_encoder']
                self.method_encoder = data['method_encoder']
                self.is_trained = True
                print(f"Model loaded from {self.model_path}")
                return True
        except Exception as e:
            print(f"Failed to load model: {e}")
        
        # Initialize encoders even if model not loaded
        self.bank_encoder.fit(self.known_banks)
        self.method_encoder.fit(self.known_methods)
        return False


# Singleton instance
_predictor: Optional[FailurePredictor] = None

def get_failure_predictor() -> FailurePredictor:
    """Get or create failure predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = FailurePredictor()
        _predictor.load_model()
    return _predictor
