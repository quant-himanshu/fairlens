"""
FairLens Explainer
Uses Google Gemini API (free tier) to translate raw fairness metrics
into plain-language audit reports.

Setup:
  1. Go to https://aistudio.google.com/apikey
  2. Click "Create API Key" (free, no credit card needed)
  3. Add to your .env:  GEMINI_API_KEY=your_key_here
"""

import os
import json
import urllib.request
import urllib.error
from models.schemas import AuditResult, ExplainResponse, FairnessVerdict


SYSTEM_PROMPT = """You are FairLens, an expert AI fairness auditor.
Your role is to explain bias audit results to non-technical decision-makers
(HR managers, loan officers, hospital administrators) clearly and honestly.

Rules:
- Never use jargon without explaining it
- Be specific: name the affected groups, cite the exact metric values
- Be actionable: every finding must have a concrete recommendation
- Be calibrated: do not catastrophize marginal issues or downplay severe ones
- Respond ONLY with a valid JSON object — no markdown, no preamble, no explanation"""


def _severity_label(verdict: FairnessVerdict) -> str:
    return {
        FairnessVerdict.FAIR: "Low Risk",
        FairnessVerdict.MARGINAL: "Moderate Risk",
        FairnessVerdict.BIASED: "High Risk",
        FairnessVerdict.SEVERELY_BIASED: "Critical Risk",
    }[verdict]


def _build_prompt(audit: AuditResult) -> str:
    metrics_summary = [
        {
            "metric": m.name,
            "value": m.value,
            "ideal_range": list(m.ideal_range),
            "verdict": m.verdict.value,
            "affected_group": m.affected_group,
        }
        for m in audit.metrics
    ]

    group_summary = [
        {
            "group": g.group_name,
            "attribute": g.attribute,
            "positive_rate": g.positive_rate,
            "true_positive_rate": g.true_positive_rate,
        }
        for g in audit.group_stats
    ]

    severely_biased = sum(1 for m in audit.metrics if m.verdict == FairnessVerdict.SEVERELY_BIASED)
    biased          = sum(1 for m in audit.metrics if m.verdict == FairnessVerdict.BIASED)
    marginal        = sum(1 for m in audit.metrics if m.verdict == FairnessVerdict.MARGINAL)
    fair            = sum(1 for m in audit.metrics if m.verdict == FairnessVerdict.FAIR)

    return f"""{SYSTEM_PROMPT}

You have just completed a fairness audit on a dataset called "{audit.dataset_name}".

AUDIT OVERVIEW:
- Rows analysed: {audit.row_count}
- Sensitive attributes audited: {", ".join(audit.sensitive_attributes)}
- Overall fairness verdict: {audit.overall_verdict.value}
- Most problematic attribute: {audit.top_biased_feature or "none identified"}

METRIC RESULTS:
{json.dumps(metrics_summary, indent=2)}

GROUP STATISTICS:
{json.dumps(group_summary, indent=2)}

BIAS COUNTS:
- Severely biased: {severely_biased}
- Biased: {biased}
- Marginal: {marginal}
- Fair: {fair}

Respond ONLY with this JSON — no markdown fences, no extra text:
{{
  "summary": "2-3 sentence plain-English summary of the overall finding",
  "root_cause": "1-2 sentences on the likely root cause of the bias",
  "business_impact": "1-2 sentences on real-world harm this bias could cause if deployed",
  "recommended_actions": ["action 1", "action 2", "action 3", "action 4"],
  "severity_label": "one of: Low Risk / Moderate Risk / High Risk / Critical Risk"
}}"""


def _clean_json(raw: str) -> str:
    """Strip markdown fences if Gemini adds them anyway."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        raw = "\n".join(inner).strip()
    return raw


class AIExplainer:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. "
                "Get a free key at https://aistudio.google.com/apikey "
                "and add it to your .env file."
            )
        # gemini-1.5-flash: free tier, fast, 1M tokens/day
        self.url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={self.api_key}"
        )

    def explain(self, audit: AuditResult) -> ExplainResponse:
        prompt = _build_prompt(audit)

        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            self.url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Gemini API error {e.code}: {error_body}") from e

        try:
            raw = body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Gemini response shape: {body}") from e

        raw = _clean_json(raw)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Gemini returned invalid JSON.\nRaw:\n{raw}\nError: {e}"
            ) from e

        return ExplainResponse(
            audit_id=audit.audit_id,
            summary=data.get("summary", "No summary available."),
            root_cause=data.get("root_cause", "Unknown."),
            business_impact=data.get("business_impact", "Unknown."),
            recommended_actions=data.get("recommended_actions", []),
            severity_label=data.get(
                "severity_label", _severity_label(audit.overall_verdict)
            ),
        )
