"""
Pydantic Models / Schemas
Data models for the Payment Operations system
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============== Enums ==============

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class InterventionType(str, Enum):
    MONITOR = "monitor"
    RETRY = "retry"
    REROUTE = "reroute"
    SUPPRESS = "suppress"
    ALERT = "alert"


class BankStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class AgentStage(str, Enum):
    OBSERVE = "observe"
    REASON = "reason"
    DECIDE = "decide"
    ACT = "act"
    LEARN = "learn"


# ============== Core Models ==============

class SystemMetrics(BaseModel):
    """Real-time system performance metrics"""
    success_rate: float = Field(..., ge=0, le=100, description="Transaction success rate %")
    avg_latency: float = Field(..., ge=0, description="Average transaction latency in ms")
    transaction_volume: int = Field(..., ge=0, description="Transactions per minute")
    error_rate: float = Field(default=0, ge=0, le=100, description="Error rate %")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class BankHealth(BaseModel):
    """Health status of a bank/issuer"""
    name: str = Field(..., description="Bank identifier")
    display_name: str = Field(..., description="Friendly bank name")
    status: BankStatus = Field(default=BankStatus.HEALTHY)
    success_rate: float = Field(..., ge=0, le=100)
    avg_latency: float = Field(default=0, ge=0)
    weight: int = Field(default=0, ge=0, le=100, description="Traffic weight %")
    predicted_failure_probability: float = Field(default=0.0, ge=0.0, le=1.0, description="ML Predicted failure prob")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())


class Anomaly(BaseModel):
    """Detected anomaly in the payment system"""
    type: str = Field(..., description="Type of anomaly")
    severity: str = Field(..., description="low, medium, high")
    value: float = Field(..., description="Current value")
    threshold: float = Field(..., description="Normal threshold")
    message: str = Field(..., description="Human-readable description")
    detected_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Intervention(BaseModel):
    """Record of an agent intervention"""
    id: str = Field(..., description="Unique intervention ID")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    type: str = Field(..., description="Type of intervention")
    action: str = Field(..., description="Action taken")
    description: str = Field(..., description="Human-readable description")
    params: Optional[Dict[str, Any]] = Field(default=None)
    success: bool = Field(default=False)
    requires_approval: bool = Field(default=False)
    approved_by: Optional[str] = Field(default=None)
    outcome: Optional[Dict[str, Any]] = Field(default=None)


class AgentThought(BaseModel):
    """Agent's reasoning thought"""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    stage: str = Field(..., description="observe, reason, decide, act, learn")
    content: str = Field(..., description="Thought content")


class ApprovalRequest(BaseModel):
    """Request for human approval of an intervention"""
    intervention_id: str
    intervention: Dict[str, Any]
    risk_score: float
    hypothesis: str
    urgency: str = Field(default="normal")
    expires_at: Optional[str] = None


class ErrorLog(BaseModel):
    """Transaction error log entry"""
    id: str
    code: str = Field(..., description="HTTP error code")
    description: str
    bank: str
    timestamp: str
    transaction_id: str
    payment_method: Optional[str] = None
    amount: Optional[float] = None


# ============== Transaction Models ==============

class Transaction(BaseModel):
    """Individual payment transaction"""
    id: str
    amount: float = Field(..., gt=0)
    currency: str = Field(default="INR")
    payment_method: str = Field(..., description="visa, mastercard, upi, etc.")
    bank: str = Field(..., description="Issuing/acquiring bank")
    status: str = Field(..., description="success, failed, pending")
    error_code: Optional[str] = None
    latency_ms: float = Field(..., ge=0)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    retry_count: int = Field(default=0, ge=0)


class TransactionBatch(BaseModel):
    """Batch of transactions for processing"""
    transactions: List[Transaction]
    batch_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============== Memory Models ==============

class AgentMemory(BaseModel):
    """Long-term memory entry for the agent"""
    id: str
    anomaly_pattern: Dict[str, Any]
    hypothesis: str
    intervention: Dict[str, Any]
    outcome: str = Field(..., description="success, failure, partial")
    improvement: float = Field(default=0, description="Success rate improvement %")
    stored_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")


# ============== Simulator Models ==============

class SimulatorConfig(BaseModel):
    """Configuration for the transaction simulator"""
    transactions_per_second: int = Field(default=50, ge=1, le=1000)
    banks: List[str] = Field(default=["HDFC", "ICICI", "SBI", "AXIS"])
    payment_methods: List[str] = Field(default=["visa", "mastercard", "upi", "rupay"])
    base_success_rate: float = Field(default=97.5, ge=0, le=100)
    base_latency_ms: float = Field(default=200, ge=0)
    enabled: bool = Field(default=True)


class FailureScenario(BaseModel):
    """Predefined failure scenario for testing"""
    name: str
    description: str
    target_bank: Optional[str] = None
    target_method: Optional[str] = None
    failure_increase: float = Field(default=20, ge=0, le=100)
    latency_increase_ms: float = Field(default=500, ge=0)
    duration_seconds: int = Field(default=60, ge=1)


# ============== API Response Models ==============

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    services: Dict[str, bool]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class InterventionResponse(BaseModel):
    """Response after intervention action"""
    status: str
    intervention_id: str
    message: Optional[str] = None
