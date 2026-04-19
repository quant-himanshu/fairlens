export type FairnessVerdict = "fair" | "marginal" | "biased" | "severely_biased";
export type AuditStatus = "pending" | "running" | "complete" | "failed";
export type MitigationStrategy = "reweighing" | "threshold_optimizer" | "resampling";

export interface MetricResult {
  name: string;
  value: number;
  ideal_range: [number, number];
  verdict: FairnessVerdict;
  description: string;
  affected_group?: string;
  delta?: number;
}

export interface GroupStats {
  group_name: string;
  attribute: string;
  count: number;
  positive_rate: number;
  true_positive_rate?: number;
  false_positive_rate?: number;
}

export interface AuditResult {
  audit_id: string;
  status: AuditStatus;
  dataset_name: string;
  row_count: number;
  sensitive_attributes: string[];
  overall_verdict: FairnessVerdict;
  metrics: MetricResult[];
  group_stats: GroupStats[];
  top_biased_feature?: string;
  claude_summary?: string;
  created_at: string;
}

export interface ExplainResponse {
  audit_id: string;
  summary: string;
  root_cause: string;
  business_impact: string;
  recommended_actions: string[];
  severity_label: string;
}

export interface MitigationResult {
  strategy: MitigationStrategy;
  before_metrics: MetricResult[];
  after_metrics: MetricResult[];
  accuracy_delta: number;
  fairness_improvement: number;
  claude_explanation?: string;
}

export const VERDICT_CONFIG: Record<FairnessVerdict, {
  label: string;
  color: string;
  bg: string;
  border: string;
}> = {
  fair:             { label: "Fair",            color: "#3B6D11", bg: "#EAF3DE", border: "#97C459" },
  marginal:         { label: "Marginal",        color: "#854F0B", bg: "#FAEEDA", border: "#EF9F27" },
  biased:           { label: "Biased",          color: "#993C1D", bg: "#FAECE7", border: "#F0997B" },
  severely_biased:  { label: "Severely Biased", color: "#791F1F", bg: "#FCEBEB", border: "#F09595" },
};
