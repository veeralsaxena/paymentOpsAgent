# 🧠 Payment Operations Agentic AI System - Complete Walkthrough

> **Team B042** | Veeral Saxena & Srishtee Varule | Taqneeq Hackathon 2026

This document provides a detailed technical explanation of how the entire Payment Operations Agent system works.

---

## ✅ Hackathon Requirements Compliance

| Requirement                                                    | How We Satisfy It                                                                                                                |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Real agent logic (state, memory, tools, decision policies)** | ✅ LangGraph StateGraph with typed AgentState, vector memory in PostgreSQL+pgvector, 10+ tools, contextual bandit policy learner |
| **Not just a single LLM call**                                 | ✅ 5-stage loop (Observe→Reason→Decide→Act→Learn), ML models (Isolation Forest, XGBoost), policy learner                         |
| **Payment data ingestion**                                     | ✅ Simulator generates transactions → Redis Streams → Agent observes                                                             |
| **How decisions are made**                                     | ✅ Contextual Bandit policy predicts utility for each action, picks highest                                                      |
| **How actions are executed**                                   | ✅ Tools execute via real function calls (switch_gateway, adjust_retry)                                                          |
| **Outcomes feed back into reasoning**                          | ✅ Reward calculation → Policy update → Memory storage                                                                           |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js 15 + Tailwind)                        │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐ │
│  │ Real-time     │  │ Bank Health   │  │ Agent Thought │  │ Scenario          │ │
│  │ Metrics       │  │ Grid          │  │ Stream        │  │ Injection         │ │
│  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────────┘ │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │ WebSocket (Real-time bidirectional)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    BACKEND (Python FastAPI + LangGraph)                          │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                    LangGraph Agent (State Machine)                        │   │
│  │   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐    │   │
│  │   │ OBSERVE │──►│ REASON  │──►│ DECIDE  │──►│   ACT   │──►│  LEARN  │    │   │
│  │   └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘    │   │
│  │        │             │             │             │             │          │   │
│  │   Get Metrics   Gemini 2.0    Policy       Execute       Calculate       │   │
│  │   Detect        Analysis      Learner      Tools         Reward          │   │
│  │   Anomalies                   (Bandit)                   Update Policy   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────────────────┐   │
│  │ Simulator       │  │ ML Layer        │  │ Agent Tools                    │   │
│  │ Service         │  │                 │  │                                │   │
│  │ ─────────────── │  │ ─────────────── │  │ • get_current_metrics          │   │
│  │ Generates       │  │ • Anomaly       │  │ • get_bank_status              │   │
│  │ transactions    │  │   Detector      │  │ • switch_gateway               │   │
│  │ (50 TPS)        │  │   (Isolation    │  │ • adjust_retry_config          │   │
│  │                 │  │   Forest)       │  │ • send_alert                   │   │
│  │ Injects         │  │                 │  │ • store_memory                 │   │
│  │ failures        │  │ • Failure       │  │ • recall_similar_patterns      │   │
│  │ on command      │  │   Predictor     │  │                                │   │
│  │                 │  │   (XGBoost)     │  │                                │   │
│  │                 │  │                 │  │                                │   │
│  │                 │  │ • Policy        │  │                                │   │
│  │                 │  │   Learner       │  │                                │   │
│  │                 │  │   (Contextual   │  │                                │   │
│  │                 │  │   Bandit)       │  │                                │   │
│  └─────────────────┘  └─────────────────┘  └────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
   │     Redis       │    │   PostgreSQL    │    │     Gemini      │
   │   ─────────────│    │   ─────────────│    │   2.0 Flash     │
   │ • Real-time    │    │ • Agent Memory │    │   ────────────  │
   │   Metrics      │    │   (pgvector)   │    │ • Reasoning     │
   │ • Transaction  │    │ • Intervention │    │ • Hypothesis    │
   │   Stream       │    │   History      │    │   Formation     │
   │ • Bank Health  │    │                │    │                 │
   └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🔄 Payment Flow: How Payments Happen

### 1. Transaction Generation (Simulator Service)

**Location:** `backend/app/services/simulator_service.py`

```python
# Banks with weighted traffic distribution
self.banks = {
    "HDFC": {"weight": 40, ...},  # 40% of traffic
    "ICICI": {"weight": 30, ...}, # 30% of traffic
    "SBI": {"weight": 20, ...},   # 20% of traffic
    "AXIS": {"weight": 10, ...}   # 10% of traffic
}

# Payment methods
self.payment_methods = {
    "visa": {"weight": 35, ...},
    "mastercard": {"weight": 30, ...},
    "upi": {"weight": 25, ...},
    "rupay": {"weight": 10, ...}
}
```

**How it works:**

1. Generates **50 transactions per second** (configurable)
2. Each transaction: bank, payment method, amount, success/failure
3. Base success rate: **97.5%**, Base latency: **200ms**
4. Pushes transactions to **Redis Streams**
5. Calculates real-time metrics and bank health

### 2. Failure Injection

When you click "Inject Failure" for a bank:

1. API call: `POST /api/simulator/scenario/custom`
2. Applies modifiers to the target bank:
   - `success_modifier`: Reduces success rate (e.g., -30%)
   - `latency_modifier`: Increases latency (e.g., +800ms)
3. Duration-limited (auto-clears after timeout)

---

## 🤖 Agent Loop: The 5-Stage Decision Cycle

**Location:** `backend/app/agent/graph.py`

The agent runs continuously, executing every **5 seconds**:

```python
while self.is_running:
    initial_state = AgentState(metrics={}, anomalies=[], ...)
    await self.graph.astream(initial_state)  # Run state machine
    await asyncio.sleep(5)  # Wait 5 seconds
```

---

### Stage 1: OBSERVE 📡

**Purpose:** Ingest current system state

```python
async def _observe_node(self, state: AgentState) -> dict:
    # 1. Get current metrics from Redis
    metrics = await self.tools.get_current_metrics()
    # → {success_rate: 97.5, avg_latency: 200, error_rate: 2.5}

    # 2. Get bank health status
    bank_health = await self.tools.get_bank_status()
    # → [{name: "HDFC", success_rate: 98, status: "healthy"}, ...]

    # 3. Get recent error logs
    error_logs = await self.tools.get_error_logs(limit=100)

    # 4. Run ANOMALY DETECTION (Isolation Forest)
    anomalies = await self.tools.detect_anomalies(metrics)
    # → ["success_rate_drop", "latency_spike", "error_rate_spike"]
```

**ML Component - Isolation Forest:**

- Trained on historical metrics patterns
- Detects "outlier" data points
- Thresholds: success_rate < 95%, latency > 350ms

---

### Stage 2: REASON 🧠

**Purpose:** Analyze patterns using LLM + ML

```python
async def _reason_node(self, state: AgentState) -> dict:
    # 1. Get ML failure predictions (XGBoost)
    predictions = await self.tools.get_failure_predictions()
    # → {"HDFC": {"risk": 0.8, "reason": "Latency spike (+0.4)"}}

    # 2. Recall similar past patterns (Vector Memory)
    memories = await self.tools.recall_similar_patterns(...)
    # → [{"intervention": "switch_gateway", "outcome": "success"}]

    # 3. Call Gemini 2.0 Flash for reasoning
    response = await self.model.generate_content(prompt)
    # → {hypothesis: "HDFC timeout due to load", severity: 0.7}

    # 4. If XGBoost predicts high risk, boost severity
    if max_ml_risk > 0.6:
        risk_score = max(risk_score, max_ml_risk)
```

---

### Stage 3: DECIDE ⚖️

**Purpose:** Choose best action using Policy Learner

```python
async def _decide_node(self, state: AgentState) -> dict:
    # 1. Define candidate actions
    candidate_actions = [
        {"id": "monitor", "action": "increase_monitoring"},
        {"id": "retry", "action": "adjust_retry_config"},
        {"id": "switch_gateway", "action": "switch_gateway"},
        {"id": "alert", "action": "send_alert"}
    ]

    # 2. Query Contextual Bandit for each action's utility
    for action in candidate_actions:
        utility = self.tools.ml.policy.predict_utility(context, action["id"])
        # → monitor: U=0.1, retry: U=0.5, switch_gateway: U=1.3

    # 3. Select action with highest utility
    best_action = max(actions, key=lambda a: a.utility)
```

---

### Stage 4: ACT 🚀

**Purpose:** Execute the intervention

```python
async def _act_node(self, state: AgentState) -> dict:
    intervention = state["intervention"]

    if action == "switch_gateway":
        success = await self.tools.switch_gateway(
            from_bank="HDFC",   # Failing bank
            to_bank="ICICI",    # Healthy alternative
            percentage=100      # Route 100% of traffic
        )

    elif action == "adjust_retry_config":
        success = await self.tools.adjust_retry_config(
            max_retries=5,
            backoff_multiplier=1.5
        )

    elif action == "send_alert":
        success = await self.tools.send_alert(
            message="Critical Risk 0.70",
            severity="critical"
        )
```

---

### Stage 5: LEARN 📚

**Purpose:** Calculate reward and update policy

```python
async def _learn_node(self, state: AgentState) -> dict:
    # 1. Wait to measure impact
    await asyncio.sleep(2)

    # 2. Get new metrics
    new_metrics = await self.tools.get_current_metrics()

    # 3. Calculate reward
    success_gain = new_metrics["success_rate"] - old_metrics["success_rate"]

    action_cost = {
        "monitor": 0, "retry": 5, "send_alert": 10, "switch_gateway": 20
    }[learner_key]

    reward = (success_gain * 2.0) - latency_penalty - action_cost

    # 4. Update Policy Learner
    self.tools.ml.policy.update_policy(context, learner_key, reward)

    # 5. Store in memory if highly successful
    if success_gain > 5:
        await self.tools.store_memory({
            "anomaly_pattern": state["anomalies"],
            "intervention": state["intervention"],
            "outcome": "success",
            "improvement": success_gain
        })
```

---

## 🧠 ML Components

### 1. Anomaly Detector (Isolation Forest)

**Location:** `backend/app/ml/anomaly.py`

- Detects unusual patterns in metrics
- Faster than threshold-based detection
- Self-trains on historical data

### 2. Failure Predictor (XGBoost)

**Location:** `backend/app/ml/predictor.py`

- Predicts FUTURE failure probability
- Uses SHAP for explainability
- Enables proactive action

### 3. Policy Learner (Contextual Bandit)

**Location:** `backend/app/ml/predictor.py`

- Learns optimal action selection
- Updates Q-values using rewards
- Balances exploration vs exploitation

---

## 📊 What Can Fail & How Agent Solves It

| Failure Scenario       | Detection              | Agent Response                 |
| ---------------------- | ---------------------- | ------------------------------ |
| **Bank Timeout**       | Latency spike + errors | Switch traffic to healthy bank |
| **Card Network Issue** | Method-specific errors | Increase monitoring, alert     |
| **Complete Outage**    | 95%+ failure rate      | Emergency reroute + alert      |
| **System Overload**    | Global error increase  | Adjust retry config            |

---

## 🛡️ Guardrails

| Action                | Risk Level | Auto-Approve? |
| --------------------- | ---------- | ------------- |
| `increase_monitoring` | LOW        | ✅ Yes        |
| `adjust_retry_config` | LOW        | ✅ Yes        |
| `send_alert`          | LOW        | ✅ Yes        |
| `switch_gateway`      | HIGH       | ⚠️ Demo: auto |

---

## 🏆 Key Differentiators

1. **True Agent Loop** - Continuous observation, not one-shot
2. **Reinforcement Learning** - Policy improves via rewards
3. **Long-term Memory** - Remembers successful interventions
4. **Explainable ML** - SHAP values explain predictions
5. **Real-time UI** - WebSocket streams agent thoughts

---

_Team B042 | Veeral Saxena & Srishtee Varule | Taqneeq Hackathon 2026_
