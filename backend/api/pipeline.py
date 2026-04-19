from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.pipeline_auditor import (
    SimulatedAIPipeline, PipelineAuditor, PipelineAuditResult
)

router = APIRouter()


class PipelineAuditRequest(BaseModel):
    pipeline_name: Optional[str] = "loan_approval_pipeline"
    sensitive_attributes: list[str] = ["gender", "income_tier", "age_group"]
    n_decisions: Optional[int] = 800
    bias_config: Optional[dict] = None


@router.post("/run")
async def run_pipeline_audit(req: PipelineAuditRequest):
    """
    Simulate an AI decision pipeline and audit it for bias.
    Returns group-level decision rates, disparate impact,
    counterfactual flip rate, and concrete demo examples.
    """
    if req.n_decisions > 5000:
        raise HTTPException(status_code=400, detail="Max 5000 decisions per audit.")

    pipeline = SimulatedAIPipeline(
        pipeline_name=req.pipeline_name or "ai_pipeline",
        bias_config=req.bias_config,
    )
    logs    = pipeline.run_batch(n=req.n_decisions)
    auditor = PipelineAuditor(logs)
    result  = auditor.audit(req.sensitive_attributes)

    return {
        "audit_id":               result.audit_id,
        "pipeline_name":          result.pipeline_name,
        "total_decisions":        result.total_decisions,
        "sensitive_attributes":   result.sensitive_attributes,
        "overall_verdict":        result.overall_verdict,
        "disparate_impact":       result.disparate_impact,
        "demographic_parity":     result.demographic_parity,
        "equalized_odds":         result.equalized_odds,
        "counterfactual_flip_rate": result.counterfactual_flip_rate,
        "group_allow_rates":      result.group_allow_rates,
        "group_deny_rates":       result.group_deny_rates,
        "group_ask_rates":        result.group_ask_rates,
        "stage_bias":             result.stage_bias,
        "counterfactual_examples": result.counterfactual_examples,
    }


@router.get("/demo")
async def get_demo_pipeline_audit():
    """Pre-run demo audit — instant response for live demos."""
    pipeline = SimulatedAIPipeline(pipeline_name="hiring_ai_demo")
    logs     = pipeline.run_batch(n=600)
    auditor  = PipelineAuditor(logs)
    result   = auditor.audit(["gender", "income_tier"])

    return {
        "audit_id":               result.audit_id,
        "pipeline_name":          "Hiring AI — Demo Pipeline",
        "total_decisions":        result.total_decisions,
        "overall_verdict":        result.overall_verdict,
        "disparate_impact":       result.disparate_impact,
        "counterfactual_flip_rate": result.counterfactual_flip_rate,
        "group_allow_rates":      result.group_allow_rates,
        "counterfactual_examples": result.counterfactual_examples,
        "architecture_note": (
            "This pipeline simulates real AI agent decision architecture: "
            "Input → Context Check → Permission Check (allow/deny/ask) → Classifier → Final Decision. "
            "FairLens audits each stage for demographic bias."
        ),
    }
