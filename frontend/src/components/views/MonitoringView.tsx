"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { InterventionTimeline } from "@/components/InterventionTimeline";
import _ from "lodash";

interface MonitoringViewProps {
  metrics: any;
  banks: any[];
  interventions: any[];
  pendingApprovals: any[];
  onApprove: (approval: any) => void;
  onReject: (approval: any) => void;
  onApproveAll: () => void;
  onRejectAll: () => void;
  onRollback: (intervention: any) => void;
}

export function MonitoringView({
  metrics,
  banks,
  interventions,
  pendingApprovals,
  onApprove,
  onReject,
  onApproveAll,
  onRejectAll,
  onRollback,
}: MonitoringViewProps) {
  const formatNumber = (num: number, decimals = 1) => num.toFixed(decimals);
  const formatTime = (timestamp: string) => new Date(timestamp).toLocaleTimeString();

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy": return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "degraded": return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "down": return "bg-red-500/20 text-red-400 border-red-500/30";
      default: return "bg-gray-500/20 text-gray-400";
    }
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 95) return "text-emerald-500";
    if (rate >= 90) return "text-amber-500";
    return "text-red-500";
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-8 animate-in fade-in duration-300">
      {/* LEFT COLUMN - STATS & GRIDS */}
      <div className="lg:col-span-8 space-y-4 lg:space-y-8">
        
        {/* 1. Metric Strip (Minimal) */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4">
           <MetricItem 
              label="Success Rate" 
              value={`${metrics.success_rate.toFixed(1)}%`}
              trend="up"
              statusColor={getSuccessRateColor(metrics.success_rate)}
           />
           <MetricItem 
              label="Avg Latency" 
              value={`${metrics.avg_latency.toFixed(0)}ms`}
              trend="stable"
              statusColor={metrics.avg_latency > 400 ? "text-red-500" : "text-zinc-300"}
           />
           <MetricItem 
              label="Volume (TPM)" 
              value={(metrics.transaction_volume / 1000).toFixed(1) + "k"}
              trend="up"
              statusColor="text-zinc-300"
           />
           <MetricItem 
              label="Error Rate" 
              value={`${metrics.error_rate.toFixed(1)}%`}
              trend="down"
              statusColor={metrics.error_rate > 5 ? "text-red-500" : "text-zinc-300"}
           />
        </div>

        {/* 2. Bank Health Grid (Clean Cards) */}
        <div>
           <SectionHeader title="Bank Connectivity Status" />
           <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              {banks.map((bank) => (
                <div key={bank.name} className="bg-zinc-900/40 border border-white/5 rounded-lg p-5 hover:border-white/10 transition-colors group backdrop-blur-md">
                   <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-3">
                         <div className={`w-2 h-2 rounded-full ring-2 ring-black ${bank.status === 'healthy' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]' : 'bg-red-500'}`} />
                         <span className="font-medium text-sm text-zinc-200">{bank.display_name}</span>
                      </div>
                      <span className={`text-sm font-mono font-medium ${getSuccessRateColor(bank.success_rate)}`}>
                         {bank.success_rate.toFixed(1)}%
                      </span>
                   </div>
                   
                   <div className="space-y-1.5">
                      <div className="flex justify-between text-xs text-zinc-500">
                         <span>Latency</span>
                         <span className="text-zinc-400 font-mono">{bank.avg_latency.toFixed(0)}ms</span>
                      </div>
                      <div className="flex justify-between text-xs text-zinc-500">
                         <span>Traffic</span>
                         <span className="text-zinc-400 font-mono">{bank.weight}%</span>
                      </div>
                   </div>

                   {bank.predicted_failure_probability > 0.1 && (
                      <div className="mt-4 pt-3 border-t border-white/5 flex items-center gap-2">
                         <span className="text-[10px] text-amber-500 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
                            Risk: {(bank.predicted_failure_probability * 100).toFixed(0)}%
                         </span>
                      </div>
                   )}
                </div>
              ))}
           </div>
        </div>

        {/* 3. Intervention Timeline */}
        <div className="bg-zinc-900/40 border border-white/5 rounded-lg backdrop-blur-md">
          <div className="px-5 py-3 border-b border-white/5">
             <h3 className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">Recent Automated Interventions</h3>
          </div>
          <div className="p-0">
             <InterventionTimeline interventions={interventions} onRollback={onRollback} />
          </div>
        </div>

      </div>

      {/* RIGHT COLUMN - APPROVALS */}
      <div className="lg:col-span-4 flex flex-col space-y-4 lg:space-y-6">
         <SectionHeader title="Pending Approvals" action={
            pendingApprovals.length > 0 && (
               <Button variant="ghost" size="sm" onClick={onApproveAll} className="h-6 text-[10px] text-emerald-500 hover:text-emerald-400 hover:bg-emerald-500/10 px-2">
                  Approve All
               </Button>
            )
         } />
         
         <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
            {pendingApprovals.length === 0 ? (
               <div className="h-32 flex flex-col items-center justify-center border border-dashed border-zinc-800 rounded-lg text-zinc-600 bg-zinc-900/20">
                  <span className="text-sm">No pending approvals</span>
               </div>
            ) : (
               pendingApprovals.map((item) => (
                  <div key={item.intervention_id} className="bg-zinc-900/60 border border-white/5 rounded-lg p-4 relative overflow-hidden backdrop-blur-md group hover:border-white/10 transition-all">
                     <div className="absolute top-0 left-0 w-0.5 h-full bg-amber-500" />
                     <div className="pl-2">
                        <div className="flex justify-between items-start mb-2">
                           <span className="text-[10px] font-mono text-zinc-600">{new Date().toLocaleTimeString()}</span>
                           <span className="text-[10px] font-medium text-amber-500 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                              Risk: {(item.risk_score * 100).toFixed(0)}%
                           </span>
                        </div>
                        <p className="text-sm text-zinc-200 font-medium leading-relaxed mb-3">
                           {item.intervention.description}
                        </p>
                        
                        <div className="bg-black/30 rounded p-2 mb-4 border border-white/5">
                           <p className="text-[10px] text-zinc-500 uppercase tracking-wide mb-1">Reasoning</p>
                           <p className="text-xs text-zinc-400 italic leading-relaxed">
                              "{item.hypothesis}"
                           </p>
                        </div>
                        
                        <div className="flex gap-2">
                           <button 
                              onClick={() => onApprove(item)}
                              className="flex-1 bg-zinc-800 hover:bg-zinc-700 border border-white/5 hover:border-white/10 text-emerald-500 text-xs py-1.5 rounded-md transition-all font-medium"
                           >
                              Approve
                           </button>
                           <button 
                              onClick={() => onReject(item)}
                              className="flex-1 bg-transparent hover:bg-red-500/10 border border-transparent hover:border-red-500/20 text-zinc-500 hover:text-red-500 text-xs py-1.5 rounded-md transition-all"
                           >
                              Reject
                           </button>
                        </div>
                     </div>
                  </div>
               ))
            )}
         </div>
      </div>
    </div>
  );
}

// Sub-components for Cleaner Code
function MetricItem({ label, value, trend, statusColor }: { label: string, value: string, trend: "up" | "down" | "stable", statusColor: string }) {
   return (
      <div className="bg-zinc-900/40 border border-white/5 rounded-lg p-3 sm:p-5 flex flex-col justify-between h-20 sm:h-28 backdrop-blur-md overflow-hidden">
         <span className="text-[9px] sm:text-[11px] text-zinc-500 font-semibold uppercase tracking-wider truncate">{label}</span>
         <div className={`text-xl sm:text-3xl font-medium tracking-tight ${statusColor} font-sans truncate`}>
            {value}
         </div>
         {trend === 'up' && <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden mt-1 sm:mt-2"><div className="h-full bg-zinc-700 w-3/4 rounded-full"/></div>}
      </div>
   )
}

function SectionHeader({ title, action }: { title: string, action?: React.ReactNode }) {
   return (
      <div className="flex items-center justify-between mb-2 px-1">
         <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">{title}</h3>
         {action}
      </div>
   )
}
