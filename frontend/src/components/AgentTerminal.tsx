"use client";

import { useRef, useEffect, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";

interface AgentLog {
  id: string;
  timestamp: string;
  stage: "observe" | "reason" | "decide" | "act" | "learn" | "system";
  type: "thought" | "prompt" | "response" | "action" | "error";
  content: string;
  metadata?: Record<string, unknown>;
}

interface AgentTerminalProps {
  logs: AgentLog[];
  className?: string;
}

const stageColors: Record<string, string> = {
  observe: "text-cyan-400",
  reason: "text-purple-400",
  decide: "text-amber-400",
  act: "text-emerald-400",
  learn: "text-indigo-400",
  system: "text-gray-400",
};

const stageIcons: Record<string, string> = {
  observe: "📡",
  reason: "🧠",
  decide: "⚖️",
  act: "🚀",
  learn: "📚",
  system: "⚙️",
};

const typeStyles: Record<string, string> = {
  thought: "text-foreground",
  prompt: "text-blue-300 font-mono text-xs",
  response: "text-green-300 font-mono text-xs",
  action: "text-amber-300 font-bold",
  error: "text-red-400 font-bold",
};

export function AgentTerminal({ logs, className }: AgentTerminalProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [showRaw, setShowRaw] = useState(false);
  const [filter, setFilter] = useState<string>("all");

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const filteredLogs = logs.filter((log) => {
    if (filter === "all") return true;
    if (filter === "thoughts") return log.type === "thought";
    if (filter === "raw") return log.type === "prompt" || log.type === "response";
    if (filter === "actions") return log.type === "action";
    return log.stage === filter;
  });

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  };

  return (
    <div
      className={cn(
        "flex flex-col rounded-xl overflow-hidden",
        "bg-[#0d1117] border border-[#30363d]",
        "font-mono text-sm",
        className
      )}
    >
      {/* Terminal Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#161b22] border-b border-[#30363d]">
        <div className="flex items-center gap-2">
          {/* Traffic lights */}
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-[#ff5f56]" />
            <div className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
            <div className="w-3 h-3 rounded-full bg-[#27c93f]" />
          </div>
          <span className="text-gray-400 text-xs ml-2">agent@paymentops ~ thinking</span>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Show Raw Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Raw</span>
            <Switch
              checked={showRaw}
              onCheckedChange={setShowRaw}
              className="scale-75"
            />
          </div>
          
          {/* Auto-scroll Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Auto-scroll</span>
            <Switch
              checked={autoScroll}
              onCheckedChange={setAutoScroll}
              className="scale-75"
            />
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-1 px-3 py-2 bg-[#161b22]/50 border-b border-[#30363d] overflow-x-auto">
        {["all", "observe", "reason", "decide", "act", "learn", "actions"].map((f) => (
          <Button
            key={f}
            variant="ghost"
            size="sm"
            onClick={() => setFilter(f)}
            className={cn(
              "h-6 px-2 text-xs capitalize",
              filter === f
                ? "bg-[#30363d] text-white"
                : "text-gray-500 hover:text-gray-300"
            )}
          >
            {f === "all" ? "All" : f}
          </Button>
        ))}
      </div>

      {/* Terminal Content */}
      <ScrollArea className="flex-1 h-[400px]" ref={scrollRef}>
        <div className="p-4 space-y-2">
          {filteredLogs.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <div className="text-2xl mb-2">🤖</div>
              <p>Agent terminal ready...</p>
              <p className="text-xs mt-1">Start the simulator to see agent thinking</p>
            </div>
          ) : (
            filteredLogs.map((log) => (
              <div
                key={log.id}
                className={cn(
                  "flex gap-2 group hover:bg-[#161b22] px-2 py-1 rounded transition-colors",
                  log.type === "error" && "bg-red-900/20"
                )}
              >
                {/* Timestamp */}
                <span className="text-gray-600 text-xs shrink-0 w-20">
                  {formatTime(log.timestamp)}
                </span>
                
                {/* Stage Badge */}
                <span className={cn("shrink-0 w-6", stageColors[log.stage])}>
                  {stageIcons[log.stage]}
                </span>
                
                {/* Stage Label */}
                <Badge
                  variant="outline"
                  className={cn(
                    "shrink-0 text-[10px] px-1.5 py-0 h-4 uppercase",
                    stageColors[log.stage],
                    "border-current/30"
                  )}
                >
                  {log.stage}
                </Badge>
                
                {/* Content */}
                <span className={cn("flex-1 break-words", typeStyles[log.type])}>
                  {log.type === "prompt" && showRaw && (
                    <span className="text-gray-500 mr-2">[PROMPT]</span>
                  )}
                  {log.type === "response" && showRaw && (
                    <span className="text-gray-500 mr-2">[RESPONSE]</span>
                  )}
                  {log.content}
                </span>
              </div>
            ))
          )}
          
          {/* Cursor blink effect */}
          <div className="flex items-center gap-2 text-emerald-400">
            <span className="text-gray-600 text-xs w-20">&nbsp;</span>
            <span className="animate-pulse">▋</span>
          </div>
        </div>
      </ScrollArea>

      {/* Terminal Footer */}
      <div className="px-4 py-2 bg-[#161b22] border-t border-[#30363d] flex justify-between items-center">
        <span className="text-xs text-gray-500">
          {filteredLogs.length} logs • {logs.filter((l) => l.type === "action").length} actions
        </span>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 text-xs text-gray-500 hover:text-white"
          onClick={() => {
            if (scrollRef.current) {
              scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
            }
          }}
        >
          ↓ Jump to bottom
        </Button>
      </div>
    </div>
  );
}

export default AgentTerminal;
