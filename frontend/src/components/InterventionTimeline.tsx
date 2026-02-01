"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { cn } from "@/lib/utils";

interface Intervention {
  id: string;
  timestamp: string;
  type: string;
  action: string;
  description: string;
  params?: Record<string, unknown>;
  success: boolean;
  requires_approval: boolean;
  approved_by?: string;
  canRollback: boolean;
  rollbackAction?: string;
}

interface InterventionTimelineProps {
  interventions: Intervention[];
  onRollback: (intervention: Intervention) => void;
  className?: string;
}

const actionIcons: Record<string, string> = {
  switch_gateway: "🔀",
  adjust_retry_config: "🔄",
  send_alert: "🔔",
  suppress_payment_method: "🚫",
  monitor: "👁️",
  reroute: "↩️",
};

const actionColors: Record<string, string> = {
  switch_gateway: "from-blue-500 to-cyan-500",
  adjust_retry_config: "from-amber-500 to-orange-500",
  send_alert: "from-purple-500 to-pink-500",
  suppress_payment_method: "from-red-500 to-rose-500",
  monitor: "from-gray-500 to-slate-500",
  reroute: "from-emerald-500 to-green-500",
};

export function InterventionTimeline({
  interventions,
  onRollback,
  className,
}: InterventionTimelineProps) {
  const [rollingBack, setRollingBack] = useState<string | null>(null);

  const handleRollback = async (intervention: Intervention) => {
    setRollingBack(intervention.id);
    await onRollback(intervention);
    setRollingBack(null);
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return {
      time: date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }),
      date: date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }),
    };
  };

  const formatTimeDiff = (timestamp: string) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return `${seconds}s ago`;
  };

  return (
    <Card className={cn("glass-card border-0", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-medium flex items-center gap-2">
            📜 Intervention History
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            {interventions.length} actions
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <ScrollArea className="h-[300px] px-6 pb-4">
          {interventions.length === 0 ? (
            <div className="text-center text-muted-foreground py-12">
              <div className="text-3xl mb-2">🎯</div>
              <p>No interventions yet</p>
              <p className="text-xs mt-1">Agent actions will appear here</p>
            </div>
          ) : (
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-border" />

              <div className="space-y-4">
                {interventions.map((intervention, index) => {
                  const { time, date } = formatTime(intervention.timestamp);
                  const icon = actionIcons[intervention.action] || "⚡";
                  const color = actionColors[intervention.action] || "from-gray-500 to-slate-500";

                  return (
                    <div
                      key={intervention.id}
                      className={cn(
                        "relative pl-10 group",
                        rollingBack === intervention.id && "opacity-50"
                      )}
                    >
                      {/* Timeline dot */}
                      <div
                        className={cn(
                          "absolute left-2 w-5 h-5 rounded-full flex items-center justify-center text-xs",
                          "bg-gradient-to-br shadow-lg",
                          color,
                          intervention.success ? "" : "ring-2 ring-red-500"
                        )}
                      >
                        {icon}
                      </div>

                      {/* Content */}
                      <div
                        className={cn(
                          "p-3 rounded-lg border transition-all",
                          "bg-muted/30 border-white/5",
                          "hover:bg-muted/50 hover:border-white/10"
                        )}
                      >
                        {/* Header */}
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={intervention.success ? "default" : "destructive"}
                              className="text-[10px] px-1.5 py-0"
                            >
                              {intervention.success ? "✓ Success" : "✗ Failed"}
                            </Badge>
                            {intervention.requires_approval && (
                              <Badge variant="outline" className="text-[10px] px-1.5 py-0 text-amber-400 border-amber-500/30">
                                👤 Approved
                              </Badge>
                            )}
                          </div>
                          
                          <Tooltip>
                            <TooltipTrigger>
                              <span className="text-xs text-muted-foreground">
                                {formatTimeDiff(intervention.timestamp)}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent>
                              {date} at {time}
                            </TooltipContent>
                          </Tooltip>
                        </div>

                        {/* Description */}
                        <p className="text-sm mb-2">{intervention.description}</p>

                        {/* Action type */}
                        <div className="flex items-center justify-between">
                          <code className="text-xs text-muted-foreground bg-background/50 px-2 py-0.5 rounded">
                            {intervention.action}
                          </code>

                          {/* Rollback button */}
                          {intervention.canRollback && (
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 text-xs text-amber-400 hover:text-amber-300 hover:bg-amber-500/10 opacity-0 group-hover:opacity-100 transition-opacity"
                                  disabled={rollingBack !== null}
                                >
                                  ↩️ Rollback
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent className="bg-zinc-950 border border-white/10 shadow-2xl">
                                <AlertDialogHeader>
                                  <AlertDialogTitle className="flex items-center gap-2">
                                    ↩️ Confirm Rollback
                                  </AlertDialogTitle>
                                  <AlertDialogDescription>
                                    This will undo the following action:
                                    <br />
                                    <strong className="text-foreground">{intervention.description}</strong>
                                    <br /><br />
                                    {intervention.rollbackAction && (
                                      <span className="text-amber-400">
                                        Rollback action: {intervention.rollbackAction}
                                      </span>
                                    )}
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => handleRollback(intervention)}
                                    className="bg-amber-500 hover:bg-amber-600"
                                  >
                                    ↩️ Confirm Rollback
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

export default InterventionTimeline;
