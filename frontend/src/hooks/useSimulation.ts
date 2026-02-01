
import { useState, useEffect } from "react";
import { AgentLog, BankHealth, SystemMetrics } from "@/types/dashboard";

interface UseSimulationProps {
  isConnected: boolean;
  simulatorRunning: boolean;
  agentRunning: boolean;
  setMetrics: React.Dispatch<React.SetStateAction<SystemMetrics>>;
  setBanks: React.Dispatch<React.SetStateAction<BankHealth[]>>;
  addAgentLog: (log: AgentLog) => void;
  setCurrentStage: (stage: string) => void;
}

export function useSimulation({
  isConnected,
  simulatorRunning,
  agentRunning,
  setMetrics,
  setBanks,
  addAgentLog,
  setCurrentStage,
}: UseSimulationProps) {
  
  // Agent Thought Simulation
  useEffect(() => {
    if (!isConnected && simulatorRunning) {
      const stages: Array<"observe" | "reason" | "decide" | "act" | "learn"> = [
        "observe",
        "reason",
        "decide",
        "act",
        "learn",
      ];
      let stageIndex = 0;

      const thoughtMessages: Record<
        string,
        { content: string; type: "thought" | "prompt" | "response" | "action" | "error" }[]
      > = {
        observe: [
          { type: "thought", content: "📡 Scanning payment infrastructure..." },
          { type: "prompt", content: "[Gemini] Analyze current metrics: success_rate=97.2%, latency=215ms" },
          { type: "response", content: "[Gemini] Metrics within normal parameters. No immediate concerns." },
          { type: "thought", content: "📊 Collected 50 transactions, 0 anomalies detected" },
        ],
        reason: [
          { type: "thought", content: "🧠 Analyzing patterns and forming hypotheses..." },
          { type: "prompt", content: "[Gemini] Given error_rate=2.8%, what is the likely cause?" },
          { type: "response", content: "[Gemini] Normal variance. Recommend continued monitoring." },
          { type: "thought", content: "💡 Hypothesis: System operating normally, risk score: 0.15" },
        ],
        decide: [
          { type: "thought", content: "⚖️ Evaluating intervention options..." },
          { type: "thought", content: "📋 Risk below threshold - no intervention needed" },
          { type: "thought", content: "✅ Decision: Continue monitoring" },
        ],
        act: [
          { type: "action", content: "🚀 Executing: Maintain current configuration" },
          { type: "thought", content: "✅ No changes required" },
        ],
        learn: [
          { type: "thought", content: "📚 Recording observations for future reference" },
          { type: "thought", content: "💾 Pattern stored in memory" },
        ],
      };

      const interval = setInterval(() => {
        if (!agentRunning) return;

        const stage = stages[stageIndex];
        const messages = thoughtMessages[stage];
        const msg = messages[Math.floor(Math.random() * messages.length)];

        addAgentLog({
          id: `demo_${Date.now()}`,
          timestamp: new Date().toISOString(),
          stage,
          type: msg.type,
          content: msg.content,
        });
        setCurrentStage(stage);

        stageIndex = (stageIndex + 1) % stages.length;
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [isConnected, simulatorRunning, agentRunning, addAgentLog, setCurrentStage]);

  // Metrics Simulation
  useEffect(() => {
    if (!isConnected) {
      const interval = setInterval(() => {
        setMetrics((prev) => ({
          ...prev,
          success_rate: Math.max(85, Math.min(99, prev.success_rate + (Math.random() - 0.5) * 2)),
          avg_latency: Math.max(100, Math.min(500, prev.avg_latency + (Math.random() - 0.5) * 50)),
          transaction_volume: Math.floor(prev.transaction_volume + (Math.random() - 0.5) * 500),
          error_rate: Math.max(1, Math.min(15, 100 - prev.success_rate)),
          timestamp: new Date().toISOString(),
        }));

        setBanks((prev) =>
          prev.map((bank) => ({
            ...bank,
            success_rate: Math.max(80, Math.min(99.5, bank.success_rate + (Math.random() - 0.5) * 1)),
            avg_latency: Math.max(100, Math.min(400, bank.avg_latency + (Math.random() - 0.5) * 20)),
            status:
              bank.success_rate < 85 ? "down" : bank.success_rate < 92 ? "degraded" : "healthy",
            last_updated: new Date().toISOString(),
            // Ensure weight exists if not present in previous state for some reason
            weight: bank.weight || 25
          }))
        );
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [isConnected, setMetrics, setBanks]);
}
