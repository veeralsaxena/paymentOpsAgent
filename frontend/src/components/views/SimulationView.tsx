"use client";

import { Card, CardContent } from "@/components/ui/card";
import { AgentTerminal } from "@/components/AgentTerminal";
import { ScenarioBuilder } from "@/components/ScenarioBuilder";
import { AgentControls } from "@/components/AgentControls";

interface SimulationViewProps {
  logs: any[];
  agentRunning: boolean;
  manualMode: boolean;
  autoApproveThreshold: number;
  riskTolerance: number;
  loopInterval: number;
  chaosMode: boolean;
  simulatorRunning: boolean;
  onToggleRunning: () => void;
  onToggleManualMode: () => void;
  onThresholdChange: (val: number) => void;
  onRiskToleranceChange: (val: number) => void;
  onLoopIntervalChange: (val: number) => void;
  onToggleChaos: (val: boolean) => void;
  onTriggerScenario: (scenario: any) => void;
  onTriggerChaos: () => void;
  onForceObserve: () => void;
  onToggleSimulator: () => void;
}

export function SimulationView({
  logs,
  agentRunning,
  manualMode,
  autoApproveThreshold,
  riskTolerance,
  loopInterval,
  chaosMode,
  simulatorRunning,
  onToggleRunning,
  onToggleManualMode,
  onThresholdChange,
  onRiskToleranceChange,
  onLoopIntervalChange,
  onToggleChaos,
  onTriggerScenario,
  onTriggerChaos,
  onForceObserve,
  onToggleSimulator,
}: SimulationViewProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-6 animate-in fade-in duration-500">
      {/* Left Column - Controls & Chaos */}
      <div className="lg:col-span-4 space-y-4 lg:space-y-6">
        <AgentControls
          isRunning={agentRunning}
          isManualMode={manualMode}
          autoApproveThreshold={autoApproveThreshold}
          riskTolerance={riskTolerance}
          loopInterval={loopInterval}
          onToggleRunning={onToggleRunning}
          onToggleManualMode={onToggleManualMode}
          onThresholdChange={onThresholdChange}
          onRiskToleranceChange={onRiskToleranceChange}
          onLoopIntervalChange={onLoopIntervalChange}
          onForceObserve={onForceObserve}
        />

        <ScenarioBuilder
          onTriggerScenario={onTriggerScenario}
          onTriggerChaos={onTriggerChaos}
          chaosMode={chaosMode}
          onToggleChaos={onToggleChaos}
        />
        
        {/* Simulator Control Card */}
        <Card className="glass-card border-0 bg-indigo-950/20 border-indigo-500/20">
             <CardContent className="p-4 flex items-center justify-between">
                 <div className="space-y-1">
                     <h3 className="font-medium text-indigo-400">Simulator Engine</h3>
                     <p className="text-xs text-muted-foreground">{simulatorRunning ? "Running" : "Stopped"}</p>
                 </div>
                 <button 
                    onClick={onToggleSimulator}
                    className={`px-4 py-2 rounded-md font-medium text-sm transition-all ${
                        simulatorRunning 
                            ? "bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30" 
                            : "bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30"
                    }`}
                 >
                     {simulatorRunning ? "Stop Engine" : "Start Engine"}
                 </button>
             </CardContent>
        </Card>
      </div>

      {/* Right Column - Terminal */}
      <div className="lg:col-span-8">
        <AgentTerminal logs={logs} className="h-[50vh] lg:h-[calc(100vh-140px)]" />
      </div>
    </div>
  );
}
