from fastapi import APIRouter, HTTPException
from models.schemas import ExplainRequest, ExplainResponse
from core.explainer import AIExplainer

router = APIRouter()

# Shared explainer instance (reuses the Anthropic client)
_explainer = AIExplainer()

# Cache: audit_id → ExplainResponse (don't burn API credits on re-fetches)
_explain_cache: dict[str, ExplainResponse] = {}


@router.post("/", response_model=ExplainResponse)
async def explain_audit(req: ExplainRequest):
    """
    Call Claude to explain the audit result in plain language.
    Returns structured explanation: summary, root cause, business impact, actions.
    """
    # Lazy import to avoid circular reference
    from api.audit import _audit_store

    if req.audit_id not in _audit_store:
        raise HTTPException(status_code=404, detail="Audit not found.")

    if req.audit_id in _explain_cache:
        return _explain_cache[req.audit_id]

    audit_result, _, _ = _audit_store[req.audit_id]
    explanation = _explainer.explain(audit_result)
    audit_result.claude_summary = explanation.summary

    _explain_cache[req.audit_id] = explanation
    return explanation
