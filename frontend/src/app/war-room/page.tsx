"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MonitoringView } from "@/components/views/MonitoringView";
import { SimulationView } from "@/components/views/SimulationView";
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

// Icons
import { 
  LayoutDashboard, 
  Activity, 
  Terminal, 
  Settings, 
  Search, 
  Bell, 
  Command, 
  Zap,
  Shield,
  Server
} from "lucide-react";

// Types
import { 
  SystemMetrics, 
  BankHealth, 
  AgentLog, 
  Intervention, 
  ApprovalRequest, 
  CustomScenario 
} from "@/types/dashboard";
import { useSimulation } from "@/hooks/useSimulation";

// New Linear-Style Layout Component
export default function WarRoomDashboard() {
  // --- STATE ---
  const [activeView, setActiveView] = useState<"monitoring" | "simulation">("monitoring");
  
  // Data State
  const [metrics, setMetrics] = useState<SystemMetrics>({
    success_rate: 97.5,
    avg_latency: 215,
    transaction_volume: 12450,
    error_rate: 2.5,
    timestamp: new Date().toISOString(),
  });
  const [banks, setBanks] = useState<BankHealth[]>([
    { name: "HDFC", display_name: "HDFC Bank", status: "healthy", success_rate: 98.2, avg_latency: 180, weight: 40, last_updated: new Date().toISOString() },
    { name: "ICICI", display_name: "ICICI Bank", status: "healthy", success_rate: 97.8, avg_latency: 195, weight: 30, last_updated: new Date().toISOString() },
    { name: "SBI", display_name: "SBI Bank", status: "healthy", success_rate: 96.5, avg_latency: 220, weight: 20, last_updated: new Date().toISOString() },
    { name: "AXIS", display_name: "Axis Bank", status: "healthy", success_rate: 97.1, avg_latency: 205, weight: 10, last_updated: new Date().toISOString() },
  ]);
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([]);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [currentStage, setCurrentStage] = useState<string>("observe");
  const [pendingApprovals, setPendingApprovals] = useState<ApprovalRequest[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [simulatorRunning, setSimulatorRunning] = useState(false);
  
  const [agentRunning, setAgentRunning] = useState(true);
  const [manualMode, setManualMode] = useState(false);
  const [autoApproveThreshold, setAutoApproveThreshold] = useState(0.3);
  const [riskTolerance, setRiskTolerance] = useState(0.5);
  const [loopInterval, setLoopInterval] = useState(5);
  const [chaosMode, setChaosMode] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);

  // --- WEBSOCKET CONNECTION ---
  const connectWebSocket = useCallback(() => {
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws");
    
    ws.onopen = () => {
      setIsConnected(true);
      addSystemLog("Connected to backend WebSocket");
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case "thought":
          addAgentLog(data.data);
          setCurrentStage(data.data.stage);
          break;
        case "metrics":
          setMetrics(data.data);
          break;
        case "banks":
          setBanks(data.data);
          break;
        case "intervention":
          const intervention = {
            ...data.data,
            canRollback: ["switch_gateway", "adjust_retry_config", "suppress_payment_method"].includes(data.data.action),
            rollbackAction: getRollbackAction(data.data.action),
          };
          setInterventions((prev) => [intervention, ...prev.slice(0, 49)]);
          addAgentLog({
            id: `action_${Date.now()}`,
            timestamp: new Date().toISOString(),
            stage: "act",
            type: "action",
            content: `Executed: ${data.data.description}`,
          });
          break;
        case "approval_required":
          setPendingApprovals((prev) => {
            const exists = prev.some(p => p.intervention_id === data.data.intervention_id);
            if (exists) return prev;
            return [data.data, ...prev].slice(0, 50);
          });
          break;
      }
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      setTimeout(connectWebSocket, 3000);
    };
    
    wsRef.current = ws;
  }, []);

  const addSystemLog = (content: string) => {
    setAgentLogs((prev) => [...prev.slice(-100), {
      id: `sys_${Date.now()}`,
      timestamp: new Date().toISOString(),
      stage: "system",
      type: "thought",
      content,
    }]);
  };

  const addAgentLog = useCallback((log: AgentLog) => {
    setAgentLogs((prev) => [...prev.slice(-100), log]);
  }, []);

  const getRollbackAction = (action: string): string | undefined => {
    const rollbacks: Record<string, string> = {
      switch_gateway: "Restore original routing weights",
      adjust_retry_config: "Revert to previous retry settings",
      suppress_payment_method: "Re-enable payment method",
    };
    return rollbacks[action];
  };

  useEffect(() => {
    connectWebSocket();
    return () => wsRef.current?.close();
  }, [connectWebSocket]);

  useSimulation({
    isConnected,
    simulatorRunning,
    agentRunning,
    setMetrics,
    setBanks,
    addAgentLog,
    setCurrentStage,
  });

  // --- HANDLERS ---
  const handleApprove = async (approval: ApprovalRequest) => {
    /* ... (Same implementation) ... */
     try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/interventions/${approval.intervention_id}/approve`, { method: "POST" });
      addAgentLog({ id: `approved_${Date.now()}`, timestamp: new Date().toISOString(), stage: "act", type: "action", content: `✅ Approved: ${approval.intervention.description}` });
       setInterventions((prev) => [{ ...approval.intervention, id: approval.intervention_id, timestamp: new Date().toISOString(), type: "switch_gateway", action: "switch_gateway", success: true, requires_approval: true, approved_by: "human", canRollback: true }, ...prev]);
    } catch {
       setInterventions((prev) => [{ ...approval.intervention, id: approval.intervention_id, timestamp: new Date().toISOString(), type: "switch_gateway", action: "switch_gateway", success: true, requires_approval: true, approved_by: "human", canRollback: true }, ...prev]);
    }
    setPendingApprovals((prev) => prev.filter((p) => p.intervention_id !== approval.intervention_id));
  };
    
  const handleReject = async (approval: ApprovalRequest) => {
    /* ... (Same implementation) ... */
    try { await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/interventions/${approval.intervention_id}/reject`, { method: "POST" }); } catch {}
    setPendingApprovals((prev) => prev.filter((p) => p.intervention_id !== approval.intervention_id));
  };
  
  const handleApproveAll = () => pendingApprovals.forEach(handleApprove);
  const handleRejectAll = () => setPendingApprovals([]);

  const triggerScenario = async (scenario: CustomScenario) => {
    try {
      addSystemLog(`🔥 Injecting scenario: ${scenario.name}`);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/simulator/scenario/custom`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(scenario),
      });
      
      if (response.ok) {
        addSystemLog(`✅ Scenario applied: ${scenario.targetBank} will experience +${scenario.failureIncrease}% failures for ${scenario.duration}s`);
      } else {
        addSystemLog(`❌ Failed to apply scenario: ${response.statusText}`);
      }
    } catch (error) {
      addSystemLog(`❌ Error triggering scenario: ${error}`);
    }
  };

  
  const triggerChaos = async () => {
    const banks = ["HDFC", "ICICI", "SBI", "AXIS"];
    const randomBank = banks[Math.floor(Math.random() * banks.length)];
    const randomFailure = Math.floor(Math.random() * 60) + 20; // 20-80%
    const randomLatency = Math.floor(Math.random() * 1500) + 500; // 500-2000ms
    const randomDuration = Math.floor(Math.random() * 120) + 30; // 30-150s
    
    await triggerScenario({
      name: "🎲 Chaos Scenario",
      targetBank: randomBank,
      targetMethod: "all",
      failureIncrease: randomFailure,
      latencyIncrease: randomLatency,
      duration: randomDuration,
    });
  };
  const toggleSimulator = async () => { setSimulatorRunning(!simulatorRunning); };
  const handleRollback = async (intervention: Intervention) => { /* ... */ };


  // --- LAYOUT ---
  return (
    <div className="flex h-screen bg-black text-white font-sans selection:bg-white/20 selection:text-white overflow-hidden">
      
      {/* 1. SIDEBAR (Vertical Navigation) */}
      <aside className="w-64 border-r border-white/5 flex flex-col bg-zinc-950/50 backdrop-blur-xl">
        {/* Workspace Brand */}
        <div className="h-12 flex items-center px-4 border-b border-white/5 gap-2">
           <div className="w-5 h-5 bg-white text-black rounded flex items-center justify-center text-[10px] font-bold">
             P
           </div>
           <span className="text-sm font-medium text-white tracking-tight">PaymentOps</span>
           <span className="text-xs text-zinc-500 ml-auto font-mono">PRO</span>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 p-2 space-y-0.5 mt-2">
          <NavItem 
            icon={<LayoutDashboard size={14} />} 
            label="Monitoring" 
            isActive={activeView === "monitoring"}
            onClick={() => setActiveView("monitoring")}
          />
          <NavItem 
            icon={<Terminal size={14} />} 
            label="Simulation" 
            isActive={activeView === "simulation"}
            onClick={() => setActiveView("simulation")}
          />
          <NavItem 
            icon={<Activity size={14} />} 
            label="Analytics" 
            isActive={false}
          />
          
          <div className="my-4 border-t border-white/5 mx-2" />
          
           <div className="px-3 pb-2 pt-1 text-[10px] font-medium text-zinc-500 uppercase tracking-wider">
            Your Team
          </div>
          <NavItem icon={<Shield size={14} />} label="Security" isActive={false} />
          <NavItem icon={<Zap size={14} />} label="Incidents" isActive={false} />
          <NavItem icon={<Server size={14} />} label="Infrastructure" isActive={false} />
        </nav>

        {/* Bottom Actions */}
        <div className="p-3 border-t border-white/5">
          <NavItem icon={<Settings size={14} />} label="Settings" isActive={false} />
        </div>
      </aside>

      {/* 2. MAIN CONTENT AREA */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-black relative">
        {/* Subtle Gradient Glow for Depth */}
        <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-zinc-900/20 to-transparent pointer-events-none" />
        
        {/* 2a. TOP BAR (Global Search & Status) */}
        <header className="h-12 border-b border-white/5 flex items-center justify-between px-4 bg-black/50 backdrop-blur-sm relative z-10">
          {/* Breadcrumbs / Title */}
          <div className="flex items-center gap-2 text-sm z-10">
             <span className="text-zinc-500">PaymentOps</span>
             <span className="text-zinc-700">/</span>
             <span className="text-white font-medium">{activeView === 'monitoring' ? 'Live Monitoring' : 'Simulation Console'}</span>
          </div>

          {/* Quick Actions / Search */}
          <div className="flex items-center gap-3">
             <div className="relative group">
                <Search size={13} className="absolute left-2.5 top-1.5 text-zinc-500 group-focus-within:text-white transition-colors" />
                <input 
                  type="text" 
                  placeholder="Search..." 
                  className="bg-zinc-900/50 border border-white/5 rounded text-sm pl-8 pr-3 py-1 h-7 w-64 text-zinc-300 placeholder-zinc-600 focus:outline-none focus:border-white/10 focus:ring-1 focus:ring-white/10 transition-all font-sans"
                />
                <div className="absolute right-2 top-1.5 flex items-center gap-0.5">
                   <span className="text-[10px] text-zinc-600 border border-zinc-800 rounded px-1 group-focus-within:border-zinc-700">⌘K</span>
                </div>
             </div>

             <button className="text-zinc-500 hover:text-white transition-colors">
               <Bell size={14} />
             </button>
             
             {/* Profile / Connection Dot */}
             <div className="h-6 w-6 rounded bg-zinc-800 flex items-center justify-center text-xs font-bold text-white relative border border-white/5">
                VS
                <div className={`absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full border border-black ${isConnected ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]' : 'bg-red-500'}`} />
             </div>
          </div>
        </header>

        {/* 2b. ACTIVE VIEW CONTENT */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 relative z-10">
           <div className="max-w-[1600px] mx-auto space-y-8">
              
              {/* Header Metrics Row (Linear Style: clean text mostly) */}
              <div className="flex items-baseline justify-between mb-4">
                 <h2 className="text-lg font-medium text-white tracking-tight">System Status</h2>
                 <div className="flex items-center gap-6 text-xs font-mono text-zinc-500">
                    <span className="flex items-center gap-2">UPTIME <span className="text-emerald-500">99.99%</span></span>
                    <span className="flex items-center gap-2">LAST INCIDENT <span className="text-zinc-300">2d ago</span></span>
                    <span className="flex items-center gap-2">AGENT <span className={`${agentRunning ? 'text-emerald-500' : 'text-amber-500'}`}>{agentRunning ? 'ONLINE' : 'PAUSED'}</span></span>
                 </div>
              </div>

              {activeView === "monitoring" ? (
                 <MonitoringView 
                  metrics={metrics}
                  banks={banks}
                  interventions={interventions}
                  pendingApprovals={pendingApprovals}
                  onApprove={handleApprove}
                  onReject={handleReject}
                  onApproveAll={handleApproveAll}
                  onRejectAll={handleRejectAll}
                  onRollback={handleRollback}
                />
              ) : (
                <SimulationView
                   logs={agentLogs}
                   agentRunning={agentRunning}
                   manualMode={manualMode}
                   autoApproveThreshold={autoApproveThreshold}
                   riskTolerance={riskTolerance}
                   loopInterval={loopInterval}
                   chaosMode={chaosMode}
                   simulatorRunning={simulatorRunning}
                   onToggleRunning={() => setAgentRunning(!agentRunning)}
                   onToggleManualMode={() => setManualMode(!manualMode)}
                   onThresholdChange={setAutoApproveThreshold}
                   onRiskToleranceChange={setRiskTolerance}
                   onLoopIntervalChange={setLoopInterval}
                   onToggleChaos={setChaosMode}
                   onTriggerScenario={triggerScenario}
                   onTriggerChaos={triggerChaos}
                   onForceObserve={() => addSystemLog("Observation forced.")}
                   onToggleSimulator={toggleSimulator}
                />
              )}
           </div>
        </div>

      </main>
    </div>
  );
}

// Minimal Navigation Item Component
function NavItem({ icon, label, isActive, onClick }: { icon: any, label: string, isActive: boolean, onClick?: () => void }) {
  return (
    <div 
      onClick={onClick}
      className={`
        flex items-center gap-2.5 px-3 py-1.5 rounded-md text-[13px] cursor-pointer select-none transition-all
        ${isActive 
          ? 'bg-zinc-800/50 text-white font-medium border border-white/5 shadow-sm' 
          : 'text-zinc-500 hover:bg-zinc-900 hover:text-zinc-300'}
      `}
    >
      <span className={isActive ? 'text-zinc-300' : 'text-zinc-600'}>
        {icon}
      </span>
      {label}
    </div>
  );
}
