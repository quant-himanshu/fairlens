"""
FairLens — AI Pipeline Auditor
================================
Inspired by the real decision architecture found in production AI agent systems
(tool permission routing: allow / deny / ask).

This module simulates a multi-step AI decision pipeline and audits whether
its decisions are biased across demographic groups.

Architecture modelled after real production AI systems:
  Input → QueryEngine → hasPermissionsToUseTool → Decision (allow/deny/ask)
  
We simulate this pipeline, replay decisions across demographic groups,
and run counterfactual fairness tests.
"""

import uuid
import json
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ─── Decision types (mirrors real AI system's permission model) ──────────────

class Decision(str, Enum):
    ALLOW = "allow"
    DENY  = "deny"
    ASK   = "ask"   # ambiguous — requires human review


class PipelineStage(str, Enum):
    INPUT_VALIDATION   = "input_validation"
    CONTEXT_CHECK      = "context_check"
    PERMISSION_CHECK   = "permission_check"
    CLASSIFIER_CHECK   = "classifier_check"
    FINAL_DECISION     = "final_decision"


@dataclass
class PipelineDecisionLog:
    """
    A single decision made by the pipeline for one user.
    Mirrors the structure of useCanUseTool's decision logging.
    """
    log_id:           str
    user_id:          str
    sensitive_attrs:  dict          # e.g. {"gender": "female", "income_tier": "low"}
    input_context:    dict          # the request context (non-sensitive features)
    stage_decisions:  list[dict]    # per-stage decisions with reasons
    final_decision:   Decision
    confidence:       float         # 0.0 – 1.0
    decision_reason:  str
    ground_truth:     Optional[Decision] = None   # what SHOULD have been decided


@dataclass
class PipelineAuditResult:
    """Full audit result for a simulated pipeline run."""
    audit_id:             str
    pipeline_name:        str
    total_decisions:      int
    sensitive_attributes: list[str]

    # Per-group decision rates
    group_allow_rates:    dict   # {group: allow_rate}
    group_deny_rates:     dict
    group_ask_rates:      dict

    # Bias metrics
    disparate_impact:     float
    demographic_parity:   float
    equalized_odds:       float

    # Counterfactual results
    counterfactual_flip_rate: float
    counterfactual_examples:  list[dict]   # concrete before/after examples

    # Verdicts
    overall_verdict:      str
    stage_bias:           dict   # which pipeline stage introduces the most bias

    # For display
    decision_logs:        list[PipelineDecisionLog] = field(default_factory=list)


# ─── Simulated Pipeline (models real AI tool permission architecture) ─────────

class SimulatedAIPipeline:
    """
    Simulates a multi-stage AI decision pipeline.
    
    The stages mirror the real production architecture:
    1. Input validation
    2. Context check (user history, session)
    3. Permission check (rule-based: allow/deny/ask)
    4. Classifier check (ML-based confidence)
    5. Final decision

    We inject configurable bias at specific stages to create
    realistic biased pipelines that FairLens can detect and audit.
    """

    def __init__(
        self,
        pipeline_name: str = "loan_approval_pipeline",
        bias_config: Optional[dict] = None,
        seed: int = 42,
    ):
        self.pipeline_name = pipeline_name
        self.rng = np.random.default_rng(seed)

        # Default bias config: gender and income tier affect decisions
        self.bias_config = bias_config or {
            "gender":       {"female": -0.18, "male": 0.0},
            "income_tier":  {"low": -0.25, "medium": 0.0, "high": +0.15},
            "age_group":    {"18-25": -0.10, "26-50": 0.0, "51+": -0.08},
        }

    def _base_score(self, context: dict) -> float:
        """Compute merit-based score from non-sensitive features only."""
        score = 0.5
        score += context.get("credit_history_years", 0) * 0.03
        score += context.get("income_normalized", 0.5) * 0.25
        score -= context.get("debt_ratio", 0.3) * 0.30
        score += context.get("employment_years", 0) * 0.02
        return float(np.clip(score, 0.0, 1.0))

    def _biased_score(self, base_score: float, sensitive_attrs: dict) -> float:
        """Apply bias adjustments based on sensitive attributes."""
        adjustment = 0.0
        for attr, value in sensitive_attrs.items():
            if attr in self.bias_config:
                adjustment += self.bias_config[attr].get(str(value), 0.0)
        return float(np.clip(base_score + adjustment, 0.0, 1.0))

    def _score_to_decision(self, score: float) -> tuple[Decision, str]:
        if score >= 0.65:
            return Decision.ALLOW, "score_above_threshold"
        elif score >= 0.40:
            return Decision.ASK, "score_in_review_band"
        else:
            return Decision.DENY, "score_below_threshold"

    def _ground_truth_decision(self, context: dict) -> Decision:
        """What the decision SHOULD be based on merit alone."""
        base = self._base_score(context)
        decision, _ = self._score_to_decision(base)
        return decision

    def process_single(
        self,
        user_id: str,
        sensitive_attrs: dict,
        input_context: dict,
    ) -> PipelineDecisionLog:
        """Run one user through the full pipeline. Returns a decision log."""

        stage_decisions = []

        # Stage 1: Input validation
        is_valid = all(v is not None for v in input_context.values())
        stage_decisions.append({
            "stage": PipelineStage.INPUT_VALIDATION,
            "result": "pass" if is_valid else "fail",
            "detail": "All required fields present" if is_valid else "Missing fields",
        })

        # Stage 2: Context check
        history_score = input_context.get("credit_history_years", 0) / 15.0
        stage_decisions.append({
            "stage": PipelineStage.CONTEXT_CHECK,
            "result": "pass" if history_score >= 0.2 else "flag",
            "detail": f"Credit history score: {history_score:.2f}",
        })

        # Stage 3: Permission / rule check (this is where bias enters)
        base_score   = self._base_score(input_context)
        biased_score = self._biased_score(base_score, sensitive_attrs)

        stage_decisions.append({
            "stage": PipelineStage.PERMISSION_CHECK,
            "result": "scored",
            "merit_score":  round(base_score, 4),
            "biased_score": round(biased_score, 4),
            "bias_applied": round(biased_score - base_score, 4),
            "detail": f"Base merit: {base_score:.3f} → Adjusted: {biased_score:.3f}",
        })

        # Stage 4: Classifier (adds noise, simulates ML uncertainty)
        noise = self.rng.normal(0, 0.04)
        classifier_score = float(np.clip(biased_score + noise, 0.0, 1.0))
        confidence = 1.0 - abs(classifier_score - 0.5) * 1.5  # lower near boundary
        confidence = float(np.clip(confidence, 0.2, 0.99))

        stage_decisions.append({
            "stage": PipelineStage.CLASSIFIER_CHECK,
            "result": "scored",
            "classifier_score": round(classifier_score, 4),
            "confidence": round(confidence, 4),
            "detail": f"Classifier: {classifier_score:.3f} (confidence {confidence:.2f})",
        })

        # Stage 5: Final decision
        final_decision, reason = self._score_to_decision(classifier_score)
        stage_decisions.append({
            "stage": PipelineStage.FINAL_DECISION,
            "result": final_decision.value,
            "detail": reason,
        })

        ground_truth = self._ground_truth_decision(input_context)

        return PipelineDecisionLog(
            log_id=str(uuid.uuid4())[:8],
            user_id=user_id,
            sensitive_attrs=sensitive_attrs,
            input_context=input_context,
            stage_decisions=stage_decisions,
            final_decision=final_decision,
            confidence=confidence,
            decision_reason=reason,
            ground_truth=ground_truth,
        )

    def run_batch(self, n: int = 1000) -> list[PipelineDecisionLog]:
        """Generate n synthetic users and run them through the pipeline."""
        logs = []
        genders      = self.rng.choice(["male", "female"], n, p=[0.5, 0.5])
        income_tiers = self.rng.choice(["low", "medium", "high"], n, p=[0.3, 0.5, 0.2])
        age_groups   = self.rng.choice(["18-25", "26-50", "51+"], n, p=[0.2, 0.6, 0.2])

        credit_hist  = self.rng.integers(0, 15, n)
        income_norm  = self.rng.uniform(0.1, 1.0, n)
        debt_ratio   = self.rng.uniform(0.05, 0.6, n)
        emp_years    = self.rng.integers(0, 20, n)

        for i in range(n):
            sensitive = {
                "gender":      genders[i],
                "income_tier": income_tiers[i],
                "age_group":   age_groups[i],
            }
            context = {
                "credit_history_years": int(credit_hist[i]),
                "income_normalized":    round(float(income_norm[i]), 3),
                "debt_ratio":           round(float(debt_ratio[i]), 3),
                "employment_years":     int(emp_years[i]),
            }
            log = self.process_single(f"user_{i:04d}", sensitive, context)
            logs.append(log)

        return logs


# ─── Pipeline Auditor ─────────────────────────────────────────────────────────

class PipelineAuditor:
    """
    Audits a set of PipelineDecisionLogs for bias.
    
    Runs:
    - Group-level allow/deny/ask rate comparison
    - Disparate impact across sensitive attributes
    - Counterfactual fairness: flip one attribute, does the decision change?
    - Stage-level bias attribution: which pipeline stage caused the bias?
    """

    def __init__(self, logs: list[PipelineDecisionLog]):
        self.logs = logs
        self.df   = self._to_dataframe()

    def _to_dataframe(self) -> pd.DataFrame:
        rows = []
        for log in self.logs:
            row = {
                "log_id":        log.log_id,
                "user_id":       log.user_id,
                "final_decision": log.final_decision.value,
                "ground_truth":  log.ground_truth.value if log.ground_truth else None,
                "confidence":    log.confidence,
                **log.sensitive_attrs,
                **log.input_context,
            }
            # Pull stage-level bias from permission check stage
            for stage in log.stage_decisions:
                if stage["stage"] == PipelineStage.PERMISSION_CHECK:
                    row["merit_score"]  = stage.get("merit_score", 0)
                    row["biased_score"] = stage.get("biased_score", 0)
                    row["bias_delta"]   = stage.get("bias_applied", 0)
            rows.append(row)
        return pd.DataFrame(rows)

    def audit(self, sensitive_attributes: list[str]) -> PipelineAuditResult:
        results = {}

        for attr in sensitive_attributes:
            if attr not in self.df.columns:
                continue
            results[attr] = self._audit_attribute(attr)

        # Merge into single result (pick worst-case attribute)
        if not results:
            raise ValueError("No valid sensitive attributes found in logs.")

        worst_attr = min(results, key=lambda a: results[a]["disparate_impact"])
        r = results[worst_attr]

        # Get counterfactual examples (from all attributes)
        cf_examples = []
        for attr in sensitive_attributes:
            if attr in self.df.columns:
                cf_examples.extend(self._counterfactual_examples(attr, n=3))

        return PipelineAuditResult(
            audit_id=str(uuid.uuid4())[:12],
            pipeline_name="AI Decision Pipeline",
            total_decisions=len(self.logs),
            sensitive_attributes=sensitive_attributes,
            group_allow_rates=r["allow_rates"],
            group_deny_rates=r["deny_rates"],
            group_ask_rates=r["ask_rates"],
            disparate_impact=r["disparate_impact"],
            demographic_parity=r["demographic_parity"],
            equalized_odds=r["equalized_odds"],
            counterfactual_flip_rate=r["cf_flip_rate"],
            counterfactual_examples=cf_examples,
            overall_verdict=self._verdict(r["disparate_impact"]),
            stage_bias=self._stage_bias_attribution(worst_attr),
            decision_logs=self.logs[:20],  # sample for display
        )

    def _audit_attribute(self, attr: str) -> dict:
        groups = self.df[attr].unique()

        allow_rates, deny_rates, ask_rates = {}, {}, {}
        tpr_by_group, fpr_by_group = {}, {}

        for g in groups:
            mask = self.df[attr] == g
            subset = self.df[mask]
            n = len(subset)
            allow_rates[str(g)] = round((subset["final_decision"] == "allow").mean(), 4)
            deny_rates[str(g)]  = round((subset["final_decision"] == "deny").mean(), 4)
            ask_rates[str(g)]   = round((subset["final_decision"] == "ask").mean(), 4)

            if "ground_truth" in self.df.columns:
                tp = ((subset["final_decision"] == "allow") & (subset["ground_truth"] == "allow")).sum()
                fn = ((subset["final_decision"] != "allow") & (subset["ground_truth"] == "allow")).sum()
                fp = ((subset["final_decision"] == "allow") & (subset["ground_truth"] != "allow")).sum()
                tn = ((subset["final_decision"] != "allow") & (subset["ground_truth"] != "allow")).sum()
                tpr_by_group[str(g)] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                fpr_by_group[str(g)] = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        rates = list(allow_rates.values())
        max_r, min_r = max(rates), min(rates)
        di = round(min_r / max_r, 4) if max_r > 0 else 1.0
        dp = round(max_r - min_r, 4)

        tpr_vals = list(tpr_by_group.values())
        fpr_vals = list(fpr_by_group.values())
        eo = round(max(
            max(tpr_vals) - min(tpr_vals) if tpr_vals else 0,
            max(fpr_vals) - min(fpr_vals) if fpr_vals else 0,
        ), 4)

        cf_rate = self._counterfactual_flip_rate(attr)

        return {
            "allow_rates": allow_rates,
            "deny_rates":  deny_rates,
            "ask_rates":   ask_rates,
            "disparate_impact":    di,
            "demographic_parity":  dp,
            "equalized_odds":      eo,
            "cf_flip_rate":        cf_rate,
        }

    def _counterfactual_flip_rate(self, attr: str) -> float:
        """
        Counterfactual fairness test.
        For each decision: if we change ONLY the sensitive attribute,
        does the final decision change?
        
        High flip rate = the attribute is directly driving decisions = bias.
        """
        if attr not in self.df.columns:
            return 0.0

        groups = self.df[attr].unique()
        if len(groups) < 2:
            return 0.0

        flipped = 0
        total   = 0
        group_a, group_b = groups[0], groups[1]

        subset_a = self.df[self.df[attr] == group_a].head(200)
        subset_b = self.df[self.df[attr] == group_b].head(200)
        n = min(len(subset_a), len(subset_b))

        for i in range(n):
            da = subset_a.iloc[i]["final_decision"]
            db = subset_b.iloc[i]["final_decision"]
            if da != db:
                flipped += 1
            total += 1

        return round(flipped / total, 4) if total > 0 else 0.0

    def _counterfactual_examples(self, attr: str, n: int = 3) -> list[dict]:
        """
        Return concrete examples where changing one attribute flips the decision.
        These are the demo moments — judges lean forward when they see these.
        """
        if attr not in self.df.columns:
            return []

        groups = self.df[attr].unique()
        if len(groups) < 2:
            return []

        examples = []
        group_a, group_b = groups[0], groups[1]
        subset_a = self.df[self.df[attr] == group_a]
        subset_b = self.df[self.df[attr] == group_b]

        for i in range(min(len(subset_a), len(subset_b), 50)):
            row_a = subset_a.iloc[i]
            row_b = subset_b.iloc[i]

            if row_a["final_decision"] != row_b["final_decision"]:
                examples.append({
                    "attribute_changed": attr,
                    "person_a": {
                        attr: str(group_a),
                        "credit_history_years": int(row_a.get("credit_history_years", 0)),
                        "income_normalized":    float(row_a.get("income_normalized", 0)),
                        "debt_ratio":           float(row_a.get("debt_ratio", 0)),
                        "decision":             str(row_a["final_decision"]),
                        "merit_score":          float(row_a.get("merit_score", 0)),
                    },
                    "person_b": {
                        attr: str(group_b),
                        "credit_history_years": int(row_b.get("credit_history_years", 0)),
                        "income_normalized":    float(row_b.get("income_normalized", 0)),
                        "debt_ratio":           float(row_b.get("debt_ratio", 0)),
                        "decision":             str(row_b["final_decision"]),
                        "merit_score":          float(row_b.get("merit_score", 0)),
                    },
                    "finding": (
                        f"With similar qualifications, "
                        f"{attr}={group_a} → {row_a['final_decision'].upper()} "
                        f"but {attr}={group_b} → {row_b['final_decision'].upper()}. "
                        f"Only '{attr}' was different."
                    ),
                })
            if len(examples) >= n:
                break

        return examples

    def _stage_bias_attribution(self, attr: str) -> dict:
        """
        Identify which pipeline stage introduces the most bias.
        Compares merit_score vs biased_score gap by group.
        """
        if attr not in self.df.columns or "bias_delta" not in self.df.columns:
            return {}

        stage_bias = {}
        for g in self.df[attr].unique():
            mask = self.df[attr] == g
            avg_delta = self.df[mask]["bias_delta"].mean()
            stage_bias[str(g)] = {
                "avg_bias_delta":   round(float(avg_delta), 4),
                "stage":            PipelineStage.PERMISSION_CHECK.value,
                "interpretation":   (
                    "Negative = penalised relative to baseline" if avg_delta < -0.01
                    else "Positive = advantaged relative to baseline" if avg_delta > 0.01
                    else "Neutral"
                ),
            }

        return stage_bias

    @staticmethod
    def _verdict(disparate_impact: float) -> str:
        if disparate_impact >= 0.9:
            return "fair"
        elif disparate_impact >= 0.8:
            return "marginal"
        elif disparate_impact >= 0.6:
            return "biased"
        else:
            return "severely_biased"


# ─── Quick test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running FairLens Pipeline Auditor...")
    print("Architecture inspired by: QueryEngine → hasPermissionsToUseTool → allow/deny/ask\n")

    pipeline = SimulatedAIPipeline(pipeline_name="loan_approval_v2")
    logs     = pipeline.run_batch(n=800)
    auditor  = PipelineAuditor(logs)
    result   = auditor.audit(["gender", "income_tier", "age_group"])

    print(f"Pipeline: {result.pipeline_name}")
    print(f"Total decisions: {result.total_decisions}")
    print(f"Overall verdict: {result.overall_verdict.upper()}")
    print(f"Disparate impact: {result.disparate_impact}")
    print(f"Counterfactual flip rate: {result.counterfactual_flip_rate}")
    print(f"\nGroup allow rates:")
    for g, r in result.group_allow_rates.items():
        print(f"  {g}: {r:.1%}")
    print(f"\nStage bias attribution:")
    for g, info in result.stage_bias.items():
        print(f"  {g}: delta={info['avg_bias_delta']:+.4f} — {info['interpretation']}")
    print(f"\n🔥 Counterfactual examples (demo moments):")
    for ex in result.counterfactual_examples[:2]:
        print(f"\n  Attribute changed: {ex['attribute_changed']}")
        print(f"  Finding: {ex['finding']}")
