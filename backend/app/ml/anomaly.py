"""
ML Anomaly Detection - Isolation Forest
Real-time anomaly detection for payment streams
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os

class AnomalyDetector:
    """
    Isolation Forest-based anomaly detector for payment metrics.
    Detects micro-anomalies in success rates, latency, and error patterns.
    """
    
    def __init__(self):
        self.model: Optional[IsolationForest] = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = [
            'success_rate',
            'avg_latency',
            'error_rate',
            'transaction_volume',
            'latency_std',
            'success_rate_change',
            'latency_change'
        ]
        
        # Thresholds for rule-based detection (fallback)
        self.thresholds = {
            'success_rate_min': 90.0,  # Minimum acceptable success rate
            'latency_max': 500,  # Maximum acceptable latency (ms)
            'error_rate_max': 10.0,  # Maximum acceptable error rate %
            'success_rate_drop': 5.0,  # Significant drop in success rate
            'latency_spike': 200,  # Significant latency increase (ms)
        }
        
        # Historical data for trend analysis
        self.history: List[Dict] = []
        self.history_max_size = 1000
        
        # Model path
        self.model_path = os.path.join(os.path.dirname(__file__), 'models', 'anomaly_detector.joblib')
    
    def train(self, data: pd.DataFrame) -> bool:
        """
        Train the Isolation Forest model on historical data.
        
        Args:
            data: DataFrame with columns matching feature_columns
        
        Returns:
            True if training successful
        """
        try:
            if len(data) < 100:
                print("Warning: Less than 100 samples, model may not be reliable")
            
            # Prepare features
            X = self._prepare_features(data)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Isolation Forest
            self.model = IsolationForest(
                n_estimators=100,
                contamination=0.05,  # Expect 5% anomalies
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X_scaled)
            
            self.is_trained = True
            
            # Save model
            self._save_model()
            
            print(f"✅ Anomaly detector trained on {len(data)} samples")
            return True
            
        except Exception as e:
            print(f"❌ Training failed: {e}")
            return False
    
    def detect(self, metrics: Dict) -> List[Dict]:
        """
        Detect anomalies in current metrics.
        
        Args:
            metrics: Dict with success_rate, avg_latency, error_rate, etc.
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Add to history
        self._update_history(metrics)
        
        # Calculate derived features
        features = self._calculate_features(metrics)
        
        # Rule-based detection (always runs)
        anomalies.extend(self._rule_based_detection(metrics, features))
        
        # ML-based detection (if model trained)
        if self.is_trained and self.model is not None:
            ml_anomalies = self._ml_detection(features)
            anomalies.extend(ml_anomalies)
        
        # Deduplicate and score
        return self._score_anomalies(anomalies)
    
    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare feature matrix from raw data"""
        features = []
        
        for i in range(len(data)):
            row = data.iloc[i]
            
            # Basic features
            success_rate = row.get('success_rate', 100)
            avg_latency = row.get('avg_latency', 200)
            error_rate = row.get('error_rate', 0)
            volume = row.get('transaction_volume', 10000)
            
            # Derived features (use previous rows if available)
            latency_std = 0
            success_rate_change = 0
            latency_change = 0
            
            if i >= 5:
                window = data.iloc[max(0, i-5):i]
                latency_std = window['avg_latency'].std() if 'avg_latency' in window else 0
                
                prev_success = window['success_rate'].mean() if 'success_rate' in window else success_rate
                success_rate_change = success_rate - prev_success
                
                prev_latency = window['avg_latency'].mean() if 'avg_latency' in window else avg_latency
                latency_change = avg_latency - prev_latency
            
            features.append([
                success_rate,
                avg_latency,
                error_rate,
                volume,
                latency_std or 0,
                success_rate_change,
                latency_change
            ])
        
        return np.array(features)
    
    def _calculate_features(self, metrics: Dict) -> Dict:
        """Calculate features for a single metric point"""
        features = {
            'success_rate': metrics.get('success_rate', 100),
            'avg_latency': metrics.get('avg_latency', 200),
            'error_rate': metrics.get('error_rate', 0),
            'transaction_volume': metrics.get('transaction_volume', 10000),
        }
        
        # Calculate from history
        if len(self.history) >= 5:
            recent = self.history[-5:]
            
            features['latency_std'] = np.std([h['avg_latency'] for h in recent])
            features['success_rate_change'] = features['success_rate'] - np.mean([h['success_rate'] for h in recent])
            features['latency_change'] = features['avg_latency'] - np.mean([h['avg_latency'] for h in recent])
        else:
            features['latency_std'] = 0
            features['success_rate_change'] = 0
            features['latency_change'] = 0
        
        return features
    
    def _rule_based_detection(self, metrics: Dict, features: Dict) -> List[Dict]:
        """Simple rule-based anomaly detection"""
        anomalies = []
        
        success_rate = features['success_rate']
        avg_latency = features['avg_latency']
        error_rate = features['error_rate']
        
        # Check success rate
        if success_rate < self.thresholds['success_rate_min']:
            severity = 'high' if success_rate < 85 else 'medium'
            anomalies.append({
                'type': 'success_rate_low',
                'severity': severity,
                'value': success_rate,
                'threshold': self.thresholds['success_rate_min'],
                'message': f"Success rate critically low at {success_rate:.1f}%",
                'source': 'rule'
            })
        
        # Check for sudden drops
        if features['success_rate_change'] < -self.thresholds['success_rate_drop']:
            anomalies.append({
                'type': 'success_rate_drop',
                'severity': 'high',
                'value': features['success_rate_change'],
                'threshold': -self.thresholds['success_rate_drop'],
                'message': f"Sudden success rate drop of {abs(features['success_rate_change']):.1f}%",
                'source': 'rule'
            })
        
        # Check latency
        if avg_latency > self.thresholds['latency_max']:
            severity = 'high' if avg_latency > 800 else 'medium'
            anomalies.append({
                'type': 'latency_high',
                'severity': severity,
                'value': avg_latency,
                'threshold': self.thresholds['latency_max'],
                'message': f"Latency spike to {avg_latency:.0f}ms",
                'source': 'rule'
            })
        
        # Check latency spike
        if features['latency_change'] > self.thresholds['latency_spike']:
            anomalies.append({
                'type': 'latency_spike',
                'severity': 'medium',
                'value': features['latency_change'],
                'threshold': self.thresholds['latency_spike'],
                'message': f"Sudden latency increase of {features['latency_change']:.0f}ms",
                'source': 'rule'
            })
        
        # Check error rate
        if error_rate > self.thresholds['error_rate_max']:
            severity = 'high' if error_rate > 15 else 'medium'
            anomalies.append({
                'type': 'error_rate_high',
                'severity': severity,
                'value': error_rate,
                'threshold': self.thresholds['error_rate_max'],
                'message': f"Error rate elevated to {error_rate:.1f}%",
                'source': 'rule'
            })
        
        return anomalies
    
    def _ml_detection(self, features: Dict) -> List[Dict]:
        """ML-based anomaly detection using Isolation Forest"""
        anomalies = []
        
        try:
            # Prepare feature vector
            X = np.array([[
                features['success_rate'],
                features['avg_latency'],
                features['error_rate'],
                features['transaction_volume'],
                features['latency_std'],
                features['success_rate_change'],
                features['latency_change']
            ]])
            
            # Scale
            X_scaled = self.scaler.transform(X)
            
            # Predict
            prediction = self.model.predict(X_scaled)[0]
            score = self.model.score_samples(X_scaled)[0]
            
            # -1 means anomaly
            if prediction == -1:
                # Determine severity based on anomaly score
                severity = 'high' if score < -0.3 else 'medium' if score < -0.1 else 'low'
                
                anomalies.append({
                    'type': 'ml_anomaly',
                    'severity': severity,
                    'value': score,
                    'threshold': -0.1,
                    'message': f"ML model detected unusual pattern (confidence: {abs(score):.2f})",
                    'source': 'ml'
                })
        
        except Exception as e:
            print(f"ML detection error: {e}")
        
        return anomalies
    
    def _score_anomalies(self, anomalies: List[Dict]) -> List[Dict]:
        """Score and deduplicate anomalies"""
        if not anomalies:
            return []
        
        # Add timestamps and IDs
        for i, anomaly in enumerate(anomalies):
            anomaly['id'] = f"anomaly_{datetime.now().timestamp()}_{i}"
            anomaly['detected_at'] = datetime.now().isoformat()
        
        # Sort by severity
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        anomalies.sort(key=lambda x: severity_order.get(x.get('severity', 'low'), 3))
        
        return anomalies
    
    def _update_history(self, metrics: Dict):
        """Update historical data"""
        self.history.append({
            'success_rate': metrics.get('success_rate', 100),
            'avg_latency': metrics.get('avg_latency', 200),
            'error_rate': metrics.get('error_rate', 0),
            'transaction_volume': metrics.get('transaction_volume', 10000),
            'timestamp': datetime.now().isoformat()
        })
        
        # Trim history
        if len(self.history) > self.history_max_size:
            self.history = self.history[-self.history_max_size:]
    
    def _save_model(self):
        """Save model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler
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
                self.is_trained = True
                print(f"Model loaded from {self.model_path}")
                return True
        except Exception as e:
            print(f"Failed to load model: {e}")
        return False


# Singleton instance
_detector: Optional[AnomalyDetector] = None

def get_anomaly_detector() -> AnomalyDetector:
    """Get or create anomaly detector instance"""
    global _detector
    if _detector is None:
        _detector = AnomalyDetector()
        _detector.load_model()
    return _detector
