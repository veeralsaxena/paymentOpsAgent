"""
LangGraph Agent - Payment Operations State Machine
Implements the Observe → Reason → Decide → Act → Learn loop
"""

from typing import TypedDict, Annotated, Literal, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import google.generativeai as genai
from datetime import datetime
import asyncio
import json
import os
from dotenv import load_dotenv

from app.agent.tools import PaymentOpsTools
from app.agent.guardrails import Guardrails
from app.models.schemas import (
    Anomaly, 
    Intervention, 
    AgentThought,
    BankHealth,
    SystemMetrics
)

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))


class AgentState(TypedDict):
    """State for the payment operations agent"""
    # Current observations
    metrics: dict
    anomalies: List[dict]
    bank_health: List[dict]
    error_logs: List[dict]
    
    # Agent reasoning
    thoughts: Annotated[list, add_messages]
    hypothesis: str
    risk_score: float
    
    # Decision
    intervention: Optional[dict]
    requires_approval: bool
    
    # Learning
    outcome: Optional[dict]
    should_remember: bool
    
    # Control flow
    iteration: int
    should_continue: bool


class PaymentOpsAgent:
    """
    LangGraph-based agent for payment operations management.
    Implements a continuous observe → reason → decide → act → learn loop.
    """
    
    def __init__(self, redis_service, ws_manager, simulator_service=None, ml_service=None):
        self.redis = redis_service
        self.ws = ws_manager
        self.tools = PaymentOpsTools(redis_service, simulator_service, ml_service)
        self.guardrails = Guardrails()
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Build the state graph
        self.graph = self._build_graph()
        
        # Runtime state
        self.pending_interventions: dict = {}
        self.intervention_history: List[Intervention] = []
        self.is_running = False
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("observe", self._observe_node)
        workflow.add_node("reason", self._reason_node)
        workflow.add_node("decide", self._decide_node)
        workflow.add_node("act", self._act_node)
        workflow.add_node("learn", self._learn_node)
        
        # Set entry point
        workflow.set_entry_point("observe")
        
        # Add edges
        workflow.add_edge("observe", "reason")
        workflow.add_conditional_edges(
            "reason",
            self._should_intervene,
            {
                "intervene": "decide",
                "continue": "learn"
            }
        )
        workflow.add_conditional_edges(
            "decide",
            self._check_guardrails,
            {
                "approved": "act",
                "pending_approval": "learn",
                "rejected": "learn"
            }
        )
        workflow.add_edge("act", "learn")
        # Always end after learn - the outer run_observation_loop handles continuous monitoring
        workflow.add_edge("learn", END)
        
        return workflow.compile()
    
    async def _observe_node(self, state: AgentState) -> dict:
        """Observe: Ingest current system state"""
        
        thought = AgentThought(
            timestamp=datetime.now().isoformat(),
            stage="observe",
            content="📡 Scanning payment infrastructure..."
        )
        await self._broadcast_thought(thought)
        
        # Get current metrics
        metrics = await self.tools.get_current_metrics()
        print(f"  📊 Observed metrics: success={metrics.get('success_rate')}, latency={metrics.get('avg_latency')}, errors={metrics.get('error_rate')}")
        
        # Get bank health
        bank_health = await self.tools.get_bank_status()
        
        # Get recent error logs
        error_logs = await self.tools.get_error_logs(limit=100)
        
        # Run anomaly detection
        anomalies = await self.tools.detect_anomalies(metrics)
        print(f"  🔍 Anomalies detected: {len(anomalies)} - {[a.get('type') for a in anomalies]}")
        
        observe_thought = AgentThought(
            timestamp=datetime.now().isoformat(),
            stage="observe",
            content=f"📊 Metrics: {metrics.get('success_rate', 0):.1f}% success rate | "
                   f"{len(anomalies)} anomalies detected | "
                   f"Latency: {metrics.get('avg_latency', 0):.0f}ms"
        )
        await self._broadcast_thought(observe_thought)
        
        return {
            "metrics": metrics,
            "bank_health": bank_health,
            "error_logs": error_logs,
            "anomalies": anomalies,
            "iteration": state.get("iteration", 0) + 1
        }
    
    async def _reason_node(self, state: AgentState) -> dict:
        """Reason: Analyze patterns and form hypotheses"""
        
        thought = AgentThought(
            timestamp=datetime.now().isoformat(),
            stage="reason",
            content="🧠 Analyzing patterns and forming hypotheses..."
        )
        await self._broadcast_thought(thought)
        
        if not state["anomalies"]:
            return {
                "hypothesis": "No significant anomalies detected. System operating normally.",
                "risk_score": 0.0,
                "thoughts": [{"role": "assistant", "content": "System healthy, no intervention needed."}]
            }
        
        # Get ML predictions
        predictions = await self.tools.get_failure_predictions()
        if predictions:
            # Filter for high risk only to reduce noise
            # predictions is now Dict[str, Dict] -> {"HDFC": {"risk": 0.8, "reason": "Latency(+0.4)"}}
            high_risk = {
                k: v for k, v in predictions.items() 
                if v.get("risk", 0.0) > 0.5
            }
            if high_risk:
                # Format for prompt
                risk_desc = [f"{k}: {v['risk']:.0%} ({v['reason']})" for k, v in high_risk.items()]
                state["anomalies"].append(f"ML High Risk Alert: {', '.join(risk_desc)}")
                print(f"  🤖 ML Model predicts failure for: {risk_desc}")

            # Retrieve past memories for similar patterns
            memories = await self.tools.recall_similar_patterns({"anomalies": state["anomalies"]})
            if memories:
                print(f"  🧠 Recalled {len(memories)} past relevant interventions")
                # Format memories for context
                memory_context = [
                    f"Past Action: {m.get('intervention', {}).get('description')} -> Result: {m.get('outcome')} (Improvement: {m.get('improvement', 0):.1f}%)"
                    for m in memories
                ]
            else:
                memory_context = ["No relevant past memories found."]

            # Build context for Gemini
            context = self._build_reasoning_context(state)
            context["ml_predictions"] = predictions
            context["relevant_memories"] = memory_context
            
            # Use Gemini for reasoning (Enriched with Memory)
            prompt = f"""You are a payment operations AI agent. Analyze the following data and form a hypothesis about what's happening.
CRITICAL: Use 'relevant_memories' to inform your decision. If a past action worked for a similar pattern, recommend it.
CRITICAL: Pay attention to 'ml_predictions'. If available, they contain the FAILURE PROBABILITY and ROOT CAUSE (SHAP explanation).

CURRENT SYSTEM STATE:
{json.dumps(context, indent=2)}

Based on this data:
1. What patterns do you observe?
2. Do any past memories provide a solution?
3. What is your hypothesis about the root cause?
4. How severe is this issue (0-1 scale)?
5. What intervention would you recommend?

Respond in JSON format:
{{
    "patterns": ["pattern1", "pattern2"],
    "analyzed_memories": "Summary of how past memories influenced this decision",
    "hypothesis": "Your hypothesis",
    "severity": 0.7,
    "recommended_action": "action description"
}}"""

            try:
                print(f"  🤖 Calling Gemini API...")
                response = await asyncio.wait_for(
                    asyncio.to_thread(self.model.generate_content, prompt),
                    timeout=30.0
                )
                print(f"  ✅ Gemini response received")
                
                # Parse response
                result_text = response.text
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]
                
                result = json.loads(result_text.strip())
                
                hypothesis = result.get("hypothesis", "Unable to form hypothesis")
                risk_score = float(result.get("severity", 0.5))
                memory_analysis = result.get("analyzed_memories", "No memory analysis provided")
                
                # ML Logic Integration: Boost risk score if ML model is confident of failure
                if predictions:
                    # predictions values are dicts, need to extract max risk
                    max_ml_risk = max([v.get("risk", 0.0) for v in predictions.values()]) if predictions else 0.0
                    
                    if max_ml_risk > 0.6:  # Threshold for ML influence
                        print(f"  🤖 ML overriding risk score: {risk_score} -> {max(risk_score, max_ml_risk)}")
                        risk_score = max(risk_score, max_ml_risk)
                        if "ML" not in hypothesis:
                            try:
                                # Find the bank with max risk to explain
                                risky_bank = max(predictions.items(), key=lambda x: x[1].get("risk", 0.0))
                                reason = risky_bank[1].get("reason", "Unknown")
                                hypothesis = f"ML Model predicts failure ({max_ml_risk:.1%}) due to {reason}. " + hypothesis
                            except:
                                hypothesis = f"ML Model predicts high failure probability ({max_ml_risk:.1%}). " + hypothesis
                
                reason_thought = AgentThought(
                    timestamp=datetime.now().isoformat(),
                    stage="reason",
                    content=f"💡 Hypothesis: {hypothesis}\n⚠️ Risk: {risk_score:.2f}\n🧠 {memory_analysis}"
                )
                await self._broadcast_thought(reason_thought)
                
                return {
                    "hypothesis": hypothesis,
                    "risk_score": risk_score,
                    "thoughts": [{"role": "assistant", "content": json.dumps(result)}]
                }
            
            except asyncio.TimeoutError:
                print(f"  ⚠️ Gemini API timeout - using fallback")
                fallback_thought = AgentThought(
                    timestamp=datetime.now().isoformat(),
                    stage="reason",
                    content=f"⚠️ API timeout: Using fallback reasoning"
                )
                await self._broadcast_thought(fallback_thought)
                
                return {
                    "hypothesis": f"Anomaly detected: {state['anomalies'][0] if state['anomalies'] else 'Unknown'}",
                    "risk_score": 0.4,
                    "thoughts": [{"role": "system", "content": "Timeout - fallback reasoning"}]
                }
            except Exception as e:
                print(f"  ⚠️ Gemini API error: {e}")
                fallback_thought = AgentThought(
                    timestamp=datetime.now().isoformat(),
                    stage="reason",
                    content=f"⚠️ Fallback reasoning: {len(state['anomalies'])} anomalies detected"
                )
                await self._broadcast_thought(fallback_thought)
                
                return {
                    "hypothesis": f"Anomaly detected: {state['anomalies'][0] if state['anomalies'] else 'Unknown'}",
                    "risk_score": 0.5 + (len(state['anomalies']) * 0.1),
                    "thoughts": [{"role": "assistant", "content": f"Fallback: {str(e)}"}]
                }
    
    async def _decide_node(self, state: AgentState) -> dict:
        """Decide: Choose intervention based on Policy Learner (Contextual Bandit)"""
        
        thought = AgentThought(
            timestamp=datetime.now().isoformat(),
            stage="decide",
            content="⚖️ Evaluating actions via Policy Learner (RL)..."
        )
        await self._broadcast_thought(thought)
        
        # Prepare context for policy learner
        # Use average health for now or worst bank
        bank_health_avg = 100
        if state.get("bank_health"):
            bank_health_avg = sum([b.get("success_rate", 100) for b in state["bank_health"]]) / len(state["bank_health"])
            
        policy_context = {
            "risk_score": state["risk_score"],
            "bank_health_score": bank_health_avg
        }
        
        candidate_actions = [
            {
                "id": "monitor",
                "type": "monitor",
                "action": "increase_monitoring", 
                "description": "Increase monitoring frequency",
                "params": {}
            },
            {
                "id": "retry",
                "type": "retry", 
                "action": "adjust_retry_config",
                "description": "Increase retry attempts",
                "params": {"max_retries": 5, "backoff_multiplier": 1.5}
            },
            {
                "id": "switch_gateway",
                "type": "reroute",
                "action": "switch_gateway",
                "description": "Switch Gateway (Reroute Traffic)",
                "params": self._identify_problematic_bank(state)
            },
            {
                "id": "alert",
                "type": "alert",
                "action": "send_alert",
                "description": "Send Escalation Alert",
                "params": {"message": f"Critical Risk {state['risk_score']:.2f}", "severity": "critical"}
            }
        ]
        
        best_action = None
        max_utility = -float('inf')
        decision_log = []
        
        for action in candidate_actions:
            # Query Policy Learner
            # Map clean action names to what policy learner knows
            # Correction: PolicyLearner expects: "monitor", "retry", "switch_gateway", "send_alert"
            learner_key = "monitor"
            if action["id"] == "retry": learner_key = "retry"
            if action["id"] == "switch_gateway": learner_key = "switch_gateway"
            if action["id"] == "alert": learner_key = "send_alert"
            
            predicted_utility = 0.0
            if self.tools.ml:
                 predicted_utility = self.tools.ml.policy.predict_utility(policy_context, learner_key)
            
            decision_log.append(f"{action['id']}: U={predicted_utility:.1f}")
            
            if predicted_utility > max_utility:
                max_utility = predicted_utility
                best_action = action
                
        # If policy not trained or all zeros, fall back to safe default (monitor or retry if risk high)
        if max_utility == 0.0 and best_action is None:
             if state["risk_score"] > 0.6:
                 best_action = candidate_actions[1] # retry
             else:
                 best_action = candidate_actions[0] # monitor
        
        if not best_action:
            best_action = candidate_actions[0]

        print(f"  ⚖️ Policy Decision: {', '.join(decision_log)}")
        
        intervention = {
            "type": best_action["type"],
            "action": best_action["action"],
            "description": best_action["description"],
            "params": best_action.get("params", {}),
            "auto_approve": True,
            "policy_context": policy_context, # Pass context for learning later
            "learner_key": best_action["id"] if best_action["id"] in ["monitor", "retry", "switch_gateway", "alert"] else "monitor" # Hacky mapping
        }
        
        # Mapping fix
        if intervention["learner_key"] == "alert": intervention["learner_key"] = "send_alert" 
        if intervention["learner_key"] == "retry": intervention["learner_key"] = "retry" 
        
        # Check for duplicates in pending interventions
        is_duplicate = False
        current_params_str = json.dumps(intervention.get("params", {}), sort_keys=True)
        
        for pending in self.pending_interventions.values():
            if pending.get("status") == "pending":
                pending_int = pending.get("intervention", {})
                pending_params_str = json.dumps(pending_int.get("params", {}), sort_keys=True)
                
                # Check if it's the exact same action and params (e.g. same banks involved)
                if (pending_int.get("action") == intervention.get("action") and 
                    pending_params_str == current_params_str):
                    is_duplicate = True
                    break
        
        if is_duplicate:
            print(f"  ⚠️ Skipping duplicate intervention: {intervention['description']}")
            intervention = {
                "type": "monitor",
                "action": "continue_monitoring",
                "description": "Monitor system stability (duplicate intervention skipped)",
                "auto_approve": True,
                "learner_key": "monitor",
                "policy_context": policy_context
            }
        
        # Human-in-the-loop: Check if intervention requires human approval
        requires_approval = self.guardrails.requires_approval(intervention, state)
        
        decide_thought = AgentThought(
            timestamp=datetime.now().isoformat(),
            stage="decide",
            content=f"⚖️ Policy Chosen: {intervention['description']} (Predicted Reward={max_utility:.1f})\n"
                   f"Options: {', '.join(decision_log)}"
        )
        await self._broadcast_thought(decide_thought)
        
        return {
            "intervention": intervention,
            "requires_approval": requires_approval
        }
    
    async def _act_node(self, state: AgentState) -> dict:
        """Act: Execute the intervention"""
        
        intervention = state["intervention"]
        
        thought = AgentThought(
            timestamp=datetime.now().isoformat(),
            stage="act",
            content=f"🚀 Executing: {intervention['description']}"
        )
        await self._broadcast_thought(thought)
        
        # Execute the action
        action = intervention["action"]
        params = intervention.get("params", {})
        
        success = False
        
        if action == "switch_gateway":
            success = await self.tools.switch_gateway(
                from_bank=params.get("from"),
                to_bank=params.get("to"),
                percentage=params.get("percentage", 100)
            )
        elif action == "adjust_retry_config":
            success = await self.tools.adjust_retry_config(
                max_retries=params.get("max_retries", 5),
                backoff_multiplier=params.get("backoff_multiplier", 1.5)
            )
        elif action == "increase_monitoring":
            success = True  # Always succeeds
        elif action == "continue_monitoring":
            success = True
        elif action == "send_alert":
            success = await self.tools.send_alert(
                message=params.get("message", "Alert from Payment Agent"),
                severity=params.get("severity", "warning")
            )
        
        # Record intervention
        intervention_record = Intervention(
            id=f"int_{datetime.now().timestamp()}",
            timestamp=datetime.now().isoformat(),
            type=intervention["type"],
            action=action,
            description=intervention["description"],
            success=success,
            requires_approval=state["requires_approval"]
        )
        self.intervention_history.append(intervention_record)
        
        act_thought = AgentThought(
            timestamp=datetime.now().isoformat(),
            stage="act",
            content=f"{'✅ Action completed successfully' if success else '❌ Action failed'}"
        )
        await self._broadcast_thought(act_thought)
        
        # Broadcast intervention to frontend
        await self.ws.broadcast({
            "type": "intervention",
            "data": intervention_record.model_dump()
        })
        
        return {
            "outcome": {"success": success, "intervention": intervention}
        }
    
    async def _learn_node(self, state: AgentState) -> dict:
        """Learn: Update Policy based on Reward"""
        
        thought = AgentThought(
            timestamp=datetime.now().isoformat(),
            stage="learn",
            content="📚 Calculating Reward and updating Policy..."
        )
        await self._broadcast_thought(thought)
        
        outcome = state.get("outcome")
        intervention = state.get("intervention", {})
        
        if outcome:
            # Wait briefly to evaluate impact
            await asyncio.sleep(2)
            
            # Get new metrics
            new_metrics = await self.tools.get_current_metrics()
            old_metrics = state.get("metrics", {})
            
            # --- Reward Calculation ---
            # Reward = SuccessGain - LatencyPenalty - Cost
            
            success_gain = new_metrics.get("success_rate", 0) - old_metrics.get("success_rate", 0)
            
            latency_penalty = 0
            if new_metrics.get("avg_latency", 0) > old_metrics.get("avg_latency", 0):
                latency_penalty = (new_metrics.get("avg_latency", 0) - old_metrics.get("avg_latency", 0)) / 10.0
            
            action_cost = 0
            learner_key = intervention.get("learner_key", "monitor")
            
            if learner_key == "monitor": action_cost = 0
            elif learner_key == "retry": action_cost = 5
            elif learner_key == "send_alert": action_cost = 10
            elif learner_key == "switch_gateway": action_cost = 20
            
            reward = (success_gain * 2.0) - latency_penalty - action_cost
            
            # Special case: If action failed (execution error), big penalty
            if not outcome.get("success"):
                reward -= 50
                
            print(f"  💰 Reward Calc: Gain={success_gain:.1f}, LatPen={latency_penalty:.1f}, Cost={action_cost} -> R={reward:.1f}")
            
            # --- Update Policy ---
            if self.tools.ml and intervention.get("policy_context"):
                 self.tools.ml.policy.update_policy(
                     intervention["policy_context"],
                     learner_key,
                     reward
                 )
                 
            # Store memory if really good
            if success_gain > 5:
                # Store successful strategy in memory
                await self.tools.store_memory({
                    "anomaly_pattern": state.get("anomalies"),
                    "hypothesis": state.get("hypothesis"),
                    "intervention": state.get("intervention"),
                    "outcome": "success",
                    "improvement": success_gain
                })
                
                learn_thought = AgentThought(
                    timestamp=datetime.now().isoformat(),
                    stage="learn",
                    content=f"💾 Strong improvement! Stored in memory. Reward={reward:.1f}"
                )
                await self._broadcast_thought(learn_thought)
            else:
                 learn_thought = AgentThought(
                    timestamp=datetime.now().isoformat(),
                    stage="learn",
                    content=f"🎓 Policy Updated. Reward={reward:.1f}"
                )
                 await self._broadcast_thought(learn_thought)

        
        # Broadcast any pending interventions that need approval
        if self.pending_interventions:
            for int_id, pending in list(self.pending_interventions.items()):
                if pending.get("status") == "pending":
                    await self.ws.broadcast({
                        "type": "approval_required",
                        "data": {
                            "intervention_id": int_id,
                            "intervention": pending.get("intervention"),
                            "risk_score": pending.get("risk_score"),
                            "hypothesis": pending.get("hypothesis")
                        }
                    })
                    print(f"  📣 Broadcasted approval request: {int_id}")
        
        return {
            "should_remember": outcome.get("success", False) if outcome else False,
            "should_continue": True
        }
    
    # ============== Decision Functions ==============
    
    def _should_intervene(self, state: AgentState) -> Literal["intervene", "continue"]:
        """Decide if intervention is needed (lowered threshold for demo)"""
        # Intervene if: anomalies exist OR risk score is above threshold
        if state["anomalies"] or state["risk_score"] > 0.15:
            return "intervene"
        return "continue"
    
    def _check_guardrails(self, state: AgentState) -> Literal["approved", "pending_approval", "rejected"]:
        """Check guardrails and approval requirements"""
        if not state["requires_approval"]:
            return "approved"
        
        intervention = state["intervention"]
        intervention_id = f"int_{datetime.now().timestamp()}"
        
        # Add to pending interventions (will be broadcast by act node)
        self.pending_interventions[intervention_id] = {
            "intervention_id": intervention_id,
            "intervention": intervention,
            "state": state,
            "status": "pending",
            "risk_score": state["risk_score"],
            "hypothesis": state["hypothesis"]
        }
        
        print(f"  ⏳ Intervention requires approval: {intervention_id}")
        
        return "pending_approval"
    
    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        """Decide if agent should continue the loop - always end after one iteration"""
        # Always end after one observe->reason->decide->act->learn cycle
        # The outer run_observation_loop handles the continuous monitoring
        return "end"
    
    # ============== Helper Methods ==============
    
    def _build_reasoning_context(self, state: AgentState) -> dict:
        """Build context for LLM reasoning"""
        return {
            "metrics": state.get("metrics", {}),
            "anomalies": state.get("anomalies", [])[:5],  # Limit to 5
            "bank_health": [
                {"bank": b.get("name"), "status": b.get("status"), "success_rate": b.get("success_rate")}
                for b in state.get("bank_health", [])[:5]
            ],
            "recent_errors": state.get("error_logs", [])[:10]
        }
    
    def _identify_problematic_bank(self, state: AgentState) -> dict:
        """Identify the bank/issuer causing issues"""
        bank_health = state.get("bank_health", [])
        
        # Find the worst performing bank
        worst_bank = None
        lowest_rate = 100
        
        for bank in bank_health:
            if bank.get("success_rate", 100) < lowest_rate:
                lowest_rate = bank.get("success_rate", 100)
                worst_bank = bank.get("name", "Unknown")
        
        # Find a healthy alternative (must be > 95% success rate)
        best_alternative = None
        highest_rate = 0
        
        for bank in bank_health:
            rate = bank.get("success_rate", 0)
            # Only consider as alternative if it's not the worst bank AND it's healthy
            if bank.get("name") != worst_bank and rate > highest_rate and rate > 95:
                highest_rate = rate
                best_alternative = bank.get("name")
                
        # If no healthy alternative found, pick the best of the rest but log warning
        if not best_alternative:
             for bank in bank_health:
                rate = bank.get("success_rate", 0)
                if bank.get("name") != worst_bank and rate > highest_rate:
                    highest_rate = rate
                    best_alternative = bank.get("name")
        
        # If the best alternative is also performing poorly (e.g. < 80%), don't switch
        if highest_rate < 80:
            print(f"  ⚠️ No healthy alternative found (best is {best_alternative} at {highest_rate}%). Suggesting alert instead.")
            # Fallback to alert/monitor instead of a bad switch
            return {
                "from": worst_bank or "HDFC",
                "to": worst_bank or "HDFC", # Stay on same if no better option
                "percentage": 0, # Don't move traffic
                "action_override": "send_alert",
                "message": f"Critical: All banks performing poorly. Best alternative {best_alternative} is at {highest_rate}%."
            }

        return {
            "from": worst_bank or "HDFC",
            "to": best_alternative or "ICICI",
            "percentage": 100
        }
        

    
    async def _broadcast_thought(self, thought: AgentThought):
        """Broadcast agent thought to connected clients"""
        await self.ws.broadcast({
            "type": "thought",
            "data": {
                "timestamp": thought.timestamp,
                "stage": thought.stage,
                "content": thought.content
            }
        })
    
    # ============== Public Methods ==============
    
    async def run_observation_loop(self):
        """Run the continuous observation loop"""
        self.is_running = True
        print("🤖 Agent observation loop started!")
        
        while self.is_running:
            try:
                print(f"🔄 Agent loop iteration starting...")
                
                initial_state = AgentState(
                    metrics={},
                    anomalies=[],
                    bank_health=[],
                    error_logs=[],
                    thoughts=[],
                    hypothesis="",
                    risk_score=0.0,
                    intervention=None,
                    requires_approval=False,
                    outcome=None,
                    should_remember=False,
                    iteration=0,
                    should_continue=True
                )
                
                # Run one iteration of the graph
                step_count = 0
                async for step in self.graph.astream(initial_state):
                    step_count += 1
                    # Log what step we're on
                    step_name = list(step.keys())[0] if step else "unknown"
                    print(f"  → Step {step_count}: {step_name}")
                
                print(f"✅ Agent loop iteration complete ({step_count} steps)")
                
                # Wait before next iteration
                await asyncio.sleep(5)
                
            except Exception as e:
                import traceback
                print(f"❌ Agent loop error: {e}")
                traceback.print_exc()
                await asyncio.sleep(10)
    
    async def get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        return await self.tools.get_current_metrics()
    
    async def get_bank_health(self) -> List[BankHealth]:
        """Get bank health status"""
        return await self.tools.get_bank_status()
    
    async def get_recent_interventions(self) -> List[Intervention]:
        """Get recent interventions"""
        return self.intervention_history[-20:]
    
    async def approve_intervention(self, intervention_id: str) -> bool:
        """Approve a pending intervention"""
        if intervention_id in self.pending_interventions:
            pending = self.pending_interventions.pop(intervention_id)
            # Execute the intervention
            await self._act_node(pending["state"])
            return True
        return False
    
    async def reject_intervention(self, intervention_id: str) -> bool:
        """Reject a pending intervention"""
        if intervention_id in self.pending_interventions:
            del self.pending_interventions[intervention_id]
            return True
        return False
