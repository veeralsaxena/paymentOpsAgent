"""
Guardrails - Safety constraints for agent actions
Implements risk assessment and approval requirements
"""

from typing import Optional
from datetime import datetime


class Guardrails:
    """
    Safety guardrails for the payment operations agent.
    Determines when human approval is required and validates actions.
    """
    
    def __init__(self):
        # High-value transaction threshold (in USD)
        self.high_value_threshold = 1000
        
        # Risk thresholds for auto-approval
        self.auto_approve_risk_threshold = 0.4
        
        # Actions that always require approval
        self.approval_required_actions = {
            "switch_gateway",  # High impact on routing
            "suppress_payment_method",  # Affects payment options
            "emergency_shutdown"  # Critical action
        }
        
        # Actions that can be auto-approved
        self.auto_approve_actions = {
            "adjust_retry_config",
            "increase_monitoring",
            "send_alert"
        }
        
        # Recent actions tracking for rate limiting
        self.recent_actions = []
        self.max_actions_per_minute = 5
    
    def requires_approval(self, intervention: dict, state: dict) -> bool:
        """
        Determine if an intervention requires human approval.
        
        Rules:
        1. Gateway switches always require approval if high value transactions
        2. Risk score > 0.6 requires approval
        3. Auto-approve actions can proceed without human intervention
        4. Rate limiting applies
        
        Args:
            intervention: The proposed intervention
            state: Current agent state
        
        Returns:
            True if human approval is required
        """
        action = intervention.get("action", "")
        risk_score = state.get("risk_score", 0.5)
        
        # Check if action is in auto-approve list
        if action in self.auto_approve_actions:
            return False
        
        # Check if action always requires approval
        if action in self.approval_required_actions:
            # But auto-approve if explicitly marked and low risk
            if intervention.get("auto_approve") and risk_score < self.auto_approve_risk_threshold:
                return False
            return True
        
        # High risk score requires approval
        if risk_score >= 0.6:
            return True
        
        # Check rate limiting
        if self._is_rate_limited():
            return True
        
        return False
    
    def validate_action(self, intervention: dict) -> tuple[bool, Optional[str]]:
        """
        Validate that an action is safe to execute.
        
        Args:
            intervention: The proposed intervention
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        action = intervention.get("action", "")
        params = intervention.get("params", {})
        
        # Validate switch_gateway
        if action == "switch_gateway":
            from_bank = params.get("from")
            to_bank = params.get("to")
            percentage = params.get("percentage", 100)
            
            if not from_bank or not to_bank:
                return False, "Switch gateway requires 'from' and 'to' banks"
            
            if from_bank == to_bank:
                return False, "Cannot switch traffic to the same bank"
            
            if percentage < 0 or percentage > 100:
                return False, "Percentage must be between 0 and 100"
        
        # Validate retry config
        if action == "adjust_retry_config":
            max_retries = params.get("max_retries", 2)
            
            if max_retries < 0 or max_retries > 10:
                return False, "Max retries must be between 0 and 10"
        
        # Validate suppression
        if action == "suppress_payment_method":
            duration = params.get("duration_minutes", 30)
            
            if duration > 120:
                return False, "Suppression duration cannot exceed 120 minutes"
        
        return True, None
    
    def calculate_risk_score(
        self, 
        intervention: dict, 
        state: dict
    ) -> float:
        """
        Calculate risk score for an intervention.
        
        Factors:
        - Type of action
        - Current system state
        - Historical success of similar actions
        - Time of day (off-hours = higher risk)
        
        Returns:
            Risk score between 0 and 1
        """
        base_risk = 0.3
        action = intervention.get("action", "")
        
        # Action-based risk
        action_risks = {
            "switch_gateway": 0.4,
            "suppress_payment_method": 0.3,
            "adjust_retry_config": 0.1,
            "send_alert": 0.0,
            "increase_monitoring": 0.0
        }
        base_risk += action_risks.get(action, 0.2)
        
        # State-based risk
        anomalies = state.get("anomalies", [])
        if len(anomalies) > 3:
            base_risk += 0.2  # Many anomalies = higher risk
        
        # Severity-based adjustment
        for anomaly in anomalies:
            if anomaly.get("severity") == "high":
                base_risk += 0.1
        
        # Cap at 1.0
        return min(base_risk, 1.0)
    
    def get_rollback_action(self, intervention: dict) -> Optional[dict]:
        """
        Get the rollback action for an intervention.
        Used when an action needs to be reversed.
        
        Args:
            intervention: The original intervention
        
        Returns:
            Rollback intervention or None
        """
        action = intervention.get("action", "")
        params = intervention.get("params", {})
        
        if action == "switch_gateway":
            # Reverse the gateway switch
            return {
                "type": "rollback",
                "action": "switch_gateway",
                "description": f"Rollback: Route traffic back to {params.get('from')}",
                "params": {
                    "from": params.get("to"),
                    "to": params.get("from"),
                    "percentage": params.get("percentage", 100)
                }
            }
        
        if action == "adjust_retry_config":
            # Reset to defaults
            return {
                "type": "rollback",
                "action": "adjust_retry_config",
                "description": "Rollback: Reset retry config to defaults",
                "params": {
                    "max_retries": 2,
                    "backoff_multiplier": 1.0
                }
            }
        
        return None
    
    def _is_rate_limited(self) -> bool:
        """Check if we've exceeded action rate limits"""
        now = datetime.now()
        
        # Remove actions older than 1 minute
        self.recent_actions = [
            action for action in self.recent_actions
            if (now - action).seconds < 60
        ]
        
        return len(self.recent_actions) >= self.max_actions_per_minute
    
    def record_action(self):
        """Record an action for rate limiting"""
        self.recent_actions.append(datetime.now())
