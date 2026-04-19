"""
FairLens — Impossibility Theorem Detector
==========================================
Based on Corbett-Davies et al. (2017).

When base rates differ between groups, no algorithm can simultaneously satisfy:
1. Statistical Parity
2. Equalized Odds
3. Predictive Parity (Calibration)

This module detects when an audit is hitting this theorem,
and explains what it means in plain language.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass


@dataclass
class ImpossibilityAnalysis:
    base_rates: dict                  # actual outcome rate per group
    base_rate_gap: float              # max - min base rate
    theorem_triggered: bool           # True if gap > 5% (meaningful difference)
    conflicting_metrics: list[str]    # which metrics are in conflict
    forced_tradeoff: str              # plain language explanation
    recommended_choice: str           # which metric to prioritise for this use case
    reference: str


def detect_impossibility(
    df: pd.DataFrame,
    label_col: str,
    ground_truth_col: str,
    sensitive_attr: str,
    domain: str = "lending"           # "lending", "hiring", "healthcare", "criminal_justice"
) -> ImpossibilityAnalysis:
    """
    Detect whether the Corbett-Davies Impossibility Theorem is active
    for this dataset and sensitive attribute.
    """
    groups = df[sensitive_attr].unique()
    base_rates = {}
    for g in groups:
        mask = df[sensitive_attr] == g
        base_rates[str(g)] = round(float(df[mask][ground_truth_col].mean()), 4)

    rates = list(base_rates.values())
    gap = round(max(rates) - min(rates), 4)
    triggered = gap > 0.05   # Meaningful difference in base rates

    # Domain-specific metric recommendations (Aequitas framework)
    domain_guidance = {
        "lending": {
            "system_type": "punitive",
            "priority": "False Positive Rate Parity",
            "reason": (
                "Credit denial is a punitive outcome. A false positive "
                "(denied despite being creditworthy) directly harms the individual. "
                "Prioritise equal FPR across groups over calibration accuracy."
            ),
        },
        "hiring": {
            "system_type": "punitive",
            "priority": "False Positive Rate Parity",
            "reason": (
                "Rejection is a punitive outcome. False positives "
                "(qualified candidates rejected) cause direct harm. "
                "Prioritise equal FPR. COMPAS-style calibration would be wrong here."
            ),
        },
        "healthcare": {
            "system_type": "assistive",
            "priority": "False Negative Rate Parity",
            "reason": (
                "Treatment recommendation is assistive. False negatives "
                "(patients denied needed care) cause direct harm. "
                "Prioritise equal FNR across demographic groups."
            ),
        },
        "criminal_justice": {
            "system_type": "punitive",
            "priority": "False Positive Rate Parity",
            "reason": (
                "False positives in criminal sentencing cause unjust incarceration. "
                "ProPublica found Black defendants had 44.9% FPR vs 23.5% for White "
                "defendants under COMPAS. This is the canonical example of the theorem."
            ),
        },
    }

    guidance = domain_guidance.get(domain, domain_guidance["lending"])

    if triggered:
        tradeoff = (
            f"The Impossibility Theorem (Corbett-Davies et al., 2017) is active. "
            f"Base rates differ by {gap:.1%} between groups ({', '.join(f'{g}: {r:.1%}' for g, r in base_rates.items())}). "
            f"This mathematically guarantees that satisfying Calibration will produce "
            f"unequal error rates, and vice versa. "
            f"This is not a bug — it is a fundamental property of the data. "
            f"Your organisation must make an explicit policy choice about which to prioritise."
        )
        conflicting = ["Calibration (Predictive Parity)", "Equalized Odds", "Statistical Parity"]
    else:
        tradeoff = (
            f"Base rates are similar across groups (gap: {gap:.1%}). "
            f"The Impossibility Theorem is not a significant constraint here — "
            f"multiple fairness criteria can likely be satisfied simultaneously."
        )
        conflicting = []

    return ImpossibilityAnalysis(
        base_rates=base_rates,
        base_rate_gap=gap,
        theorem_triggered=triggered,
        conflicting_metrics=conflicting,
        forced_tradeoff=tradeoff,
        recommended_choice=guidance["reason"],
        reference="Corbett-Davies et al. (2017). Algorithmic Decision Making and the Cost of Fairness.",
    )


if __name__ == "__main__":
    from core.india_dataset import generate_india_loan_dataset

    df = generate_india_loan_dataset(1000)
    result = detect_impossibility(
        df,
        label_col="approved",
        ground_truth_col="financially_eligible",
        sensitive_attr="gender",
        domain="lending",
    )

    print("Impossibility Theorem Analysis")
    print("=" * 50)
    print(f"Base rates: {result.base_rates}")
    print(f"Gap: {result.base_rate_gap:.1%}")
    print(f"Theorem triggered: {result.theorem_triggered}")
    print(f"\nForced trade-off:\n{result.forced_tradeoff}")
    print(f"\nRecommendation:\n{result.recommended_choice}")
