# 🧠 Agentic AI Payment Operations System

> **Self-Healing Financial Nervous System** - A real-time AI-powered payment operations manager that observes, reasons, decides, acts, and learns.

![Next.js](https://img.shields.io/badge/Next.js-15+-black)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-0.0.40+-purple)
![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-orange)

## 👥 Team B042

| Name                | Role                 |
| ------------------- | -------------------- |
| **Veeral Saxena**   | Full Stack Developer |
| **Srishtee Varule** | Full Stack Developer |

---

## 🎯 Overview

This project implements an **Agentic AI system** that acts as a 24/7 expert payment operations manager. Unlike traditional monitoring dashboards, this AI:

- **Observes** real-time payment streams and detects anomalies
- **Reasons** about failure patterns using Gemini 2.0 Flash
- **Decides** on interventions using a Contextual Bandit policy learner
- **Acts** with guardrails (auto-approve low-risk, require approval for high-risk)
- **Learns** from outcomes and stores successful strategies in long-term memory

---

## ✅ Hackathon Requirements Compliance

| Requirement                                                    | Implementation                                                                                               |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Real agent logic (state, memory, tools, decision policies)** | ✅ LangGraph StateGraph with typed AgentState, vector memory (pgvector), 10+ tools, contextual bandit policy |
| **Not just a single LLM call**                                 | ✅ 5-stage loop (Observe→Reason→Decide→Act→Learn) + ML models                                                |
| **Payment data ingestion**                                     | ✅ Simulator → Redis Streams → Agent observes                                                                |
| **How decisions are made**                                     | ✅ Contextual Bandit predicts utility, picks highest                                                         |
| **How actions are executed**                                   | ✅ Tools: switch_gateway, adjust_retry, send_alert                                                           |
| **Outcomes feed back into reasoning**                          | ✅ Reward → Policy update → Memory storage                                                                   |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js 15+ War Room Dashboard               │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐  │
│  │ Real-time     │ │ Bank Health   │ │ Agent Thought         │  │
│  │ Metrics       │ │ Grid          │ │ Stream                │  │
│  └───────────────┘ └───────────────┘ └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Python FastAPI + LangGraph Agent                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────┐  │
│  │ Observe │──│ Reason  │──│ Decide  │──│  Act    │──│ Learn │  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └───────┘  │
│        │          │            │            │            │       │
│        ▼          ▼            ▼            ▼            ▼       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Agent Tools: get_bank_status | switch_gateway | send_alert│  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    ▼                         ▼                         ▼
┌─────────┐            ┌─────────────┐           ┌─────────────┐
│  Redis  │            │ PostgreSQL  │           │   ML Layer  │
│ Streams │            │ + pgvector  │           │ IF + XGBoost│
└─────────┘            └─────────────┘           └─────────────┘
```

---

## 🤖 Agent Loop Explained

```mermaid
graph LR
    A[📡 Observe] --> B[🧠 Reason]
    B --> C{Anomaly?}
    C -->|Yes| D[⚖️ Decide]
    C -->|No| F[📚 Learn]
    D --> E{Approved?}
    E -->|Yes| G[🚀 Act]
    E -->|Pending| F
    G --> F
    F --> A
```

### The 5 Stages:

| Stage          | What Happens                                                      |
| -------------- | ----------------------------------------------------------------- |
| **1. OBSERVE** | Ingest metrics from Redis, run Isolation Forest anomaly detection |
| **2. REASON**  | Gemini 2.0 + XGBoost predictions + Memory recall → Hypothesis     |
| **3. DECIDE**  | Contextual Bandit evaluates utility of each action                |
| **4. ACT**     | Execute tool (reroute traffic, adjust retries, send alert)        |
| **5. LEARN**   | Calculate reward, update policy, store memory if successful       |

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Gemini API Key

### 1. Clone and Setup Infrastructure

```bash
git clone https://github.com/your-repo/taqneeq-hackathon.git
cd taqneeq-hackathon

# Start Redis + PostgreSQL
docker-compose up -d
```

### 2. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start backend
uvicorn app.main:app --reload --port 8000
```

### 3. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open Dashboard

Navigate to `http://localhost:3000` to see the War Room Dashboard.

---

## 📂 Project Structure

```
├── frontend/                    # Next.js 15+ Application
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # War Room Dashboard
│   │   │   ├── war-room/       # Main monitoring view
│   │   │   └── globals.css     # Premium dark theme
│   │   ├── components/         # React components
│   │   └── hooks/              # Custom hooks (WebSocket, etc.)
│
├── backend/                     # Python FastAPI Backend
│   ├── app/
│   │   ├── main.py             # FastAPI entry + WebSocket
│   │   ├── agent/
│   │   │   ├── graph.py        # LangGraph state machine (5 stages)
│   │   │   ├── tools.py        # Agent tools (10+)
│   │   │   └── guardrails.py   # Safety constraints
│   │   ├── ml/
│   │   │   ├── anomaly.py      # Isolation Forest detector
│   │   │   └── predictor.py    # XGBoost + Policy Learner
│   │   ├── services/
│   │   │   ├── redis_service.py
│   │   │   └── simulator_service.py
│   │   └── models/
│   │       └── schemas.py      # Pydantic models
│
├── docs/
│   └── WALKTHROUGH.md          # Detailed system explanation
├── docker-compose.yml          # PostgreSQL + Redis
└── README.md
```

---

## 🛠️ Tech Stack

| Layer    | Technology                      | Purpose                         |
| -------- | ------------------------------- | ------------------------------- |
| Frontend | Next.js 15, Shadcn/UI, Tailwind | War Room Dashboard              |
| Backend  | FastAPI, LangGraph              | Agent orchestration             |
| AI/LLM   | Gemini 2.0 Flash                | Reasoning and hypothesis        |
| ML       | Isolation Forest, XGBoost       | Anomaly detection, prediction   |
| RL       | Contextual Bandit               | Decision policy learning        |
| Data     | Redis Streams                   | Real-time transaction ingestion |
| Memory   | PostgreSQL + pgvector           | Agent long-term memory          |

---

## 🧪 Demo Scenarios

Click these buttons in the dashboard to trigger failure scenarios:

| Scenario            | Effect                     | Agent Response                     |
| ------------------- | -------------------------- | ---------------------------------- |
| 🏦 HDFC Timeout     | 30% failure, 800ms latency | Detects anomaly, reroutes to ICICI |
| 💳 Visa Degradation | 20% failure on Visa        | Increases monitoring, alerts ops   |
| 🔴 Bank Outage      | 95% failure on ICICI       | Emergency reroute + critical alert |
| 📈 System Overload  | 15% global failure         | Adjust retry config, alert team    |

---

## 🔐 Guardrails & Safety

| Action                    | Risk Level | Auto-Approve?     |
| ------------------------- | ---------- | ----------------- |
| `increase_monitoring`     | LOW        | ✅ Yes            |
| `adjust_retry_config`     | LOW        | ✅ Yes            |
| `send_alert`              | LOW        | ✅ Yes            |
| `switch_gateway`          | HIGH       | ⚠️ Demo: auto     |
| `suppress_payment_method` | MEDIUM     | Requires approval |

---

## 🏆 Key Features

- ✅ **Complete Agent Loop** - Observe→Reason→Decide→Act→Learn
- ✅ **Real-time WebSocket** - Streaming agent thoughts to UI
- ✅ **ML Anomaly Detection** - Isolation Forest
- ✅ **Predictive Throttling** - XGBoost failure prediction
- ✅ **Policy Learning** - Contextual Bandit (RL)
- ✅ **Long-term Memory** - pgvector similarity search
- ✅ **Premium UI** - Glassmorphism dark theme
- ✅ **Failure Simulator** - Test various scenarios

---

## 📊 How It Works

### Payment Flow

1. **Simulator** generates 50 transactions/second
2. Transactions pushed to **Redis Streams**
3. **Agent observes** every 5 seconds
4. **Anomaly detection** flags issues
5. **Gemini reasons** about root cause
6. **Policy learner** picks best action
7. **Tool executes** intervention
8. **Reward calculated** → Policy updated

### Learning Feedback Loop

```
Reward = (Success Gain × 2) - Latency Penalty - Action Cost
         ↓
Update Q-values in Contextual Bandit
         ↓
Store successful patterns in vector memory
         ↓
Next similar anomaly → Agent recalls what worked
```

---

## 📝 Environment Variables

### Backend (.env)

```env
GEMINI_API_KEY=your_key_here
DATABASE_URL=postgresql://paymentops:paymentops_secret@localhost:5432/paymentops
REDIS_URL=redis://localhost:6379
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

---

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run all services
docker-compose -f docker-compose.prod.yml up -d
```

### Vercel (Frontend)

```bash
cd frontend
vercel deploy
```

---

## 📚 Documentation

- [WALKTHROUGH.md](./docs/WALKTHROUGH.md) - Detailed system explanation
- [API Documentation](http://localhost:8000/docs) - FastAPI Swagger UI

---

## 🤝 Team B042

Built for **Taqneeq Hackathon 2026**

|                     |                      |
| ------------------- | -------------------- |
| **Veeral Saxena**   | Full Stack Developer |
| **Srishtee Varule** | Full Stack Developer |

---

_Powered by LangGraph + Gemini 2.0 Flash_
