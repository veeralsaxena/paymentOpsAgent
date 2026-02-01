"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface AgentControlsProps {
  isRunning: boolean;
  isManualMode: boolean;
  autoApproveThreshold: number;
  riskTolerance: number;
  loopInterval: number;
  onToggleRunning: () => void;
  onToggleManualMode: () => void;
  onThresholdChange: (value: number) => void;
  onRiskToleranceChange: (value: number) => void;
  onLoopIntervalChange: (value: number) => void;
  onForceObserve: () => void;
  className?: string;
}

export function AgentControls({
  isRunning,
  isManualMode,
  autoApproveThreshold,
  riskTolerance,
  loopInterval,
  onToggleRunning,
  onToggleManualMode,
  onThresholdChange,
  onRiskToleranceChange,
  onLoopIntervalChange,
  onForceObserve,
  className,
}: AgentControlsProps) {
  return (
    <Card className={cn("glass-card border-0", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-medium flex items-center gap-2">
            🎛️ Agent Controls
          </CardTitle>
          
          {/* Status Badge */}
          <Badge
            variant={isRunning ? "default" : "secondary"}
            className={cn(
              "text-xs",
              isRunning
                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                : "bg-gray-500/20 text-gray-400"
            )}
          >
            <span
              className={cn(
                "w-2 h-2 rounded-full mr-1.5",
                isRunning ? "bg-emerald-400 animate-pulse" : "bg-gray-400"
              )}
            />
            {isRunning ? "Running" : "Paused"}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* Main Controls */}
        <div className="flex gap-2">
          <Button
            onClick={onToggleRunning}
            variant={isRunning ? "destructive" : "default"}
            className={cn(
              "flex-1",
              !isRunning && "bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-600 hover:to-green-600"
            )}
          >
            {isRunning ? "⏸️ Pause Agent" : "▶️ Resume Agent"}
          </Button>
          
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                onClick={onForceObserve}
                disabled={!isRunning}
              >
                🔄
              </Button>
            </TooltipTrigger>
            <TooltipContent>Force observation cycle</TooltipContent>
          </Tooltip>
        </div>

        {/* Manual Mode Toggle */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-white/5">
          <div className="space-y-1">
            <Label className="text-sm font-medium">Manual Mode</Label>
            <p className="text-xs text-muted-foreground">
              Agent suggests actions but doesn&apos;t execute
            </p>
          </div>
          <Switch
            checked={isManualMode}
            onCheckedChange={onToggleManualMode}
          />
        </div>

        {/* Auto-Approve Threshold */}
        <div className="space-y-3">
          <div className="flex justify-between">
            <Label className="text-sm">Auto-Approve Threshold</Label>
            <Badge variant="outline" className="font-mono text-xs">
              Risk ≤ {(autoApproveThreshold * 100).toFixed(0)}%
            </Badge>
          </div>
          <Slider
            value={[autoApproveThreshold * 100]}
            onValueChange={([v]) => onThresholdChange(v / 100)}
            max={100}
            step={5}
          />
          <p className="text-xs text-muted-foreground">
            Actions with risk score below this are auto-approved
          </p>
        </div>

        {/* Risk Tolerance */}
        <div className="space-y-3">
          <div className="flex justify-between">
            <Label className="text-sm">Risk Tolerance</Label>
            <Badge
              variant="outline"
              className={cn(
                "font-mono text-xs",
                riskTolerance > 0.7
                  ? "text-red-400 border-red-500/30"
                  : riskTolerance > 0.4
                  ? "text-amber-400 border-amber-500/30"
                  : "text-emerald-400 border-emerald-500/30"
              )}
            >
              {riskTolerance > 0.7 ? "🔥 Aggressive" : riskTolerance > 0.4 ? "⚡ Moderate" : "🛡️ Conservative"}
            </Badge>
          </div>
          <Slider
            value={[riskTolerance * 100]}
            onValueChange={([v]) => onRiskToleranceChange(v / 100)}
            max={100}
            step={10}
          />
          <p className="text-xs text-muted-foreground">
            Higher = agent takes more aggressive actions
          </p>
        </div>

        {/* Loop Interval */}
        <div className="space-y-3">
          <div className="flex justify-between">
            <Label className="text-sm">Observation Interval</Label>
            <Badge variant="outline" className="font-mono text-xs">
              {loopInterval}s
            </Badge>
          </div>
          <Slider
            value={[loopInterval]}
            onValueChange={([v]) => onLoopIntervalChange(v)}
            min={2}
            max={30}
            step={1}
          />
          <p className="text-xs text-muted-foreground">
            How often the agent runs its observation loop
          </p>
        </div>

        {/* Quick Actions */}
        <div className="pt-2 border-t border-white/5">
          <Label className="text-sm mb-2 block">Quick Actions</Label>
          <div className="grid grid-cols-2 gap-2">
            <Button variant="outline" size="sm" className="text-xs">
              📊 Force Metrics
            </Button>
            <Button variant="outline" size="sm" className="text-xs">
              🧠 Clear Memory
            </Button>
            <Button variant="outline" size="sm" className="text-xs">
              🔄 Reset Config
            </Button>
            <Button variant="outline" size="sm" className="text-xs text-amber-400 border-amber-500/30">
              ⚠️ Test Alert
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default AgentControls;
