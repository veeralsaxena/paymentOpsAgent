
export interface SystemMetrics {
  success_rate: number;
  avg_latency: number;
  transaction_volume: number;
  error_rate: number;
  timestamp: string;
}

export interface BankHealth {
  name: string;
  display_name: string;
  status: "healthy" | "degraded" | "down";
  success_rate: number;
  avg_latency: number;
  weight: number;
  last_updated: string;
}

export interface AgentLog {
  id: string;
  timestamp: string;
  stage: "observe" | "reason" | "decide" | "act" | "learn" | "system";
  type: "thought" | "prompt" | "response" | "action" | "error";
  content: string;
  metadata?: Record<string, unknown>;
}

export interface Intervention {
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

export interface ApprovalRequest {
  intervention_id: string;
  intervention: {
    type: string;
    action: string;
    description: string;
    params?: Record<string, unknown>;
  };
  risk_score: number;
  hypothesis: string;
}

export interface CustomScenario {
  name: string;
  targetBank: string;
  targetMethod: string;
  failureIncrease: number;
  latencyIncrease: number;
  duration: number;
}
