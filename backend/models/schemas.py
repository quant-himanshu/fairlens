from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AuditStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class FairnessVerdict(str, Enum):
    FAIR = "fair"
    MARGINAL = "marginal"
    BIASED = "biased"
    SEVERELY_BIASED = "severely_biased"


class AuditConfig(BaseModel):
    label_column: str = Field(..., description="Column name of the model's predicted outcome (0/1)")
    ground_truth_column: str = Field(..., description="Column name of actual ground truth labels")
    sensitive_attributes: list[str] = Field(..., description="Column names of sensitive attributes to audit (e.g. ['gender', 'race'])")
    score_column: Optional[str] = Field(None, description="Column of probability scores if available")


class MetricResult(BaseModel):
    name: str
    value: float
    ideal_range: tuple[float, float]
    verdict: FairnessVerdict
    description: str
    affected_group: Optional[str] = None
    delta: Optional[float] = None  # used post-mitigation


class GroupStats(BaseModel):
    group_name: str
    attribute: str
    count: int
    positive_rate: float
    true_positive_rate: Optional[float] = None
    false_positive_rate: Optional[float] = None


class AuditResult(BaseModel):
    audit_id: str
    status: AuditStatus
    dataset_name: str
    row_count: int
    sensitive_attributes: list[str]
    overall_verdict: FairnessVerdict
    metrics: list[MetricResult]
    group_stats: list[GroupStats]
    top_biased_feature: Optional[str] = None
    claude_summary: Optional[str] = None
    created_at: str


class MitigationStrategy(str, Enum):
    REWEIGHING = "reweighing"
    THRESHOLD_OPTIMIZER = "threshold_optimizer"
    RESAMPLING = "resampling"
    ADVERSARIAL_DEBIASING = "adversarial_debiasing"


class MitigationRequest(BaseModel):
    audit_id: str
    strategy: MitigationStrategy
    sensitive_attribute: str


class MitigationResult(BaseModel):
    strategy: MitigationStrategy
    before_metrics: list[MetricResult]
    after_metrics: list[MetricResult]
    accuracy_delta: float
    fairness_improvement: float
    claude_explanation: Optional[str] = None


class ExplainRequest(BaseModel):
    audit_id: str
    context: Optional[str] = None


class ExplainResponse(BaseModel):
    audit_id: str
    summary: str
    root_cause: str
    business_impact: str
    recommended_actions: list[str]
    severity_label: str
