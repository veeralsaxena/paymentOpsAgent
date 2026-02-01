"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";

interface ScenarioBuilderProps {
  onTriggerScenario: (scenario: CustomScenario) => void;
  onTriggerChaos: () => void;
  chaosMode: boolean;
  onToggleChaos: (enabled: boolean) => void;
}

interface CustomScenario {
  name: string;
  targetBank: string;
  targetMethod: string;
  failureIncrease: number;
  latencyIncrease: number;
  duration: number;
}

const banks = ["HDFC", "ICICI", "SBI", "AXIS", "ALL"];
const methods = ["visa", "mastercard", "upi", "rupay", "all"];

const presetScenarios = [
  {
    name: "Bank Timeout",
    icon: "🏦",
    color: "amber",
    config: { failureIncrease: 30, latencyIncrease: 800, duration: 60 },
  },
  {
    name: "Network Degradation",
    icon: "📡",
    color: "blue",
    config: { failureIncrease: 15, latencyIncrease: 400, duration: 120 },
  },
  {
    name: "Complete Outage",
    icon: "🔴",
    color: "red",
    config: { failureIncrease: 95, latencyIncrease: 2000, duration: 30 },
  },
  {
    name: "Gradual Decline",
    icon: "📉",
    color: "purple",
    config: { failureIncrease: 5, latencyIncrease: 100, duration: 300 },
  },
];

export function ScenarioBuilder({
  onTriggerScenario,
  onTriggerChaos,
  chaosMode,
  onToggleChaos,
}: ScenarioBuilderProps) {
  const [scenario, setScenario] = useState<CustomScenario>({
    name: "Custom Scenario",
    targetBank: "HDFC",
    targetMethod: "all",
    failureIncrease: 20,
    latencyIncrease: 500,
    duration: 60,
  });

  const handlePreset = (preset: (typeof presetScenarios)[0]) => {
    setScenario({
      ...scenario,
      name: preset.name,
      ...preset.config,
    });
  };

  const handleTrigger = () => {
    onTriggerScenario(scenario);
  };

  return (
    <Card className="glass-card border-0">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-medium flex items-center gap-2">
            ⚡ Scenario Builder
          </CardTitle>
          
          {/* Chaos Mode Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Chaos Mode</span>
            <Switch
              checked={chaosMode}
              onCheckedChange={onToggleChaos}
            />
            {chaosMode && (
              <Badge variant="destructive" className="animate-pulse">
                🎲 ACTIVE
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Preset Scenarios */}
        <div className="grid grid-cols-4 gap-2">
          {presetScenarios.map((preset) => (
            <Button
              key={preset.name}
              variant="outline"
              size="sm"
              onClick={() => handlePreset(preset)}
              className={`flex flex-col h-auto py-2 hover:bg-${preset.color}-500/10 hover:border-${preset.color}-500/50`}
            >
              <span className="text-lg">{preset.icon}</span>
              <span className="text-xs mt-1">{preset.name}</span>
            </Button>
          ))}
        </div>

        {/* Custom Configuration */}
        <div className="grid grid-cols-2 gap-4">
          {/* Target Bank */}
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Target Bank</Label>
            <Select
              value={scenario.targetBank}
              onValueChange={(v) => setScenario({ ...scenario, targetBank: v })}
            >
              <SelectTrigger className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {banks.map((bank) => (
                  <SelectItem key={bank} value={bank}>
                    {bank}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Target Method */}
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Payment Method</Label>
            <Select
              value={scenario.targetMethod}
              onValueChange={(v) => setScenario({ ...scenario, targetMethod: v })}
            >
              <SelectTrigger className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {methods.map((method) => (
                  <SelectItem key={method} value={method}>
                    {method}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Failure Increase */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <Label className="text-xs text-muted-foreground">Failure Increase</Label>
            <span className="text-xs text-red-400 font-mono">
              +{scenario.failureIncrease}%
            </span>
          </div>
          <Slider
            value={[scenario.failureIncrease]}
            onValueChange={([v]) => setScenario({ ...scenario, failureIncrease: v })}
            max={100}
            step={5}
            className="py-2"
          />
        </div>

        {/* Latency Increase */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <Label className="text-xs text-muted-foreground">Latency Spike</Label>
            <span className="text-xs text-amber-400 font-mono">
              +{scenario.latencyIncrease}ms
            </span>
          </div>
          <Slider
            value={[scenario.latencyIncrease]}
            onValueChange={([v]) => setScenario({ ...scenario, latencyIncrease: v })}
            max={2000}
            step={100}
            className="py-2"
          />
        </div>

        {/* Duration */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <Label className="text-xs text-muted-foreground">Duration</Label>
            <span className="text-xs text-muted-foreground font-mono">
              {scenario.duration}s
            </span>
          </div>
          <Slider
            value={[scenario.duration]}
            onValueChange={([v]) => setScenario({ ...scenario, duration: v })}
            min={10}
            max={300}
            step={10}
            className="py-2"
          />
        </div>

        {/* Trigger Buttons */}
        <div className="flex gap-2 pt-2">
          <Button
            onClick={handleTrigger}
            className="flex-1 bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600"
          >
            💥 Inject Failure
          </Button>
          
          <Button
            variant="outline"
            onClick={onTriggerChaos}
            disabled={!chaosMode}
            className="border-purple-500/30 hover:bg-purple-500/10"
          >
            🎲 Random
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default ScenarioBuilder;
