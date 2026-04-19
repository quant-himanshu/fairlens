"""
FairLens — Research Foundation
================================
Every number in this file is sourced from peer-reviewed research.
This is what separates FairLens from every other hackathon project.

Sources:
- Selbst et al. (2019) FAccT — Five Abstraction Traps
- Bolukbasi et al. (2016) NeurIPS — Word Embedding Bias
- Kusner et al. (2017) NeurIPS — Counterfactual Fairness
- Buolamwini & Gebru (2018) FAccT — Gender Shades
- ProPublica (2016) — COMPAS Investigation
- Corbett-Davies et al. (2017) — Impossibility Theorem
- Saleiro et al. (2018) — Aequitas Toolkit
- RBI Annual Report (2023) — India Credit Market
- NABARD Rural Finance Report (2022)
"""


# ─── COMPAS Recidivism (ProPublica, 2016) ────────────────────────────────────
# "Machine Bias" — https://www.propublica.org/article/machine-bias-risk-assessments-in-criminal-sentencing

COMPAS = {
    "black_false_positive_rate":  0.449,   # 44.9% — Black defendants incorrectly flagged high-risk
    "white_false_positive_rate":  0.235,   # 23.5% — White defendants incorrectly flagged high-risk
    "black_false_negative_rate":  0.280,   # 28.0%
    "white_false_negative_rate":  0.480,   # 48.0%
    "black_recidivism_base_rate": 0.514,   # 51.4% actual recidivism rate
    "white_recidivism_base_rate": 0.394,   # 39.4% actual recidivism rate
    "fpr_ratio":                  1.91,    # Black FPR is 1.91× White FPR
    "legal_threshold_di":         0.80,    # US EEOC 80% rule for Disparate Impact
    "source": "ProPublica (2016). Machine Bias.",
}


# ─── Gender Shades (Buolamwini & Gebru, FAccT 2018) ──────────────────────────
# Intersectional accuracy gaps in commercial facial recognition

GENDER_SHADES = {
    "lighter_males_error_rate":    0.003,  # 0.3% — best performing group
    "lighter_females_error_rate":  0.139,  # 13.9% (IBM) — 46× worse than lighter males
    "darker_males_error_rate":     0.120,  # 12.0% (IBM)
    "darker_females_error_rate":   0.344,  # 34.4% (IBM) — the most misclassified group
    "max_error_rate_overall":      0.347,  # 34.7% for darker-skinned females
    "type_vi_max_error":           0.468,  # 46.8% — near random guessing for darkest skin type
    "training_data_lighter_ijba":  0.796,  # 79.6% lighter-skinned subjects in IJB-A benchmark
    "training_data_lighter_adience": 0.862, # 86.2% lighter-skinned subjects in Adience benchmark
    "intersectional_gap":          0.341,  # gap between best and worst subgroup (34.1 pp)
    "source": "Buolamwini & Gebru (2018). Gender Shades. FAccT.",
}


# ─── Impossibility Theorem (Corbett-Davies et al., 2017) ─────────────────────
# Proves you CANNOT simultaneously satisfy all three fairness criteria
# when base rates differ between groups

IMPOSSIBILITY_THEOREM = {
    "theorem": (
        "When the base rates of an outcome differ between groups, "
        "no algorithm can simultaneously satisfy: "
        "(1) Statistical Parity, "
        "(2) Equalized Odds (equal FPR and FNR), and "
        "(3) Predictive Parity (Calibration). "
        "Satisfying any two forces violation of the third."
    ),
    "compas_violation": (
        "COMPAS satisfies Calibration (predictive parity) "
        "but violates Equalized Odds — "
        "Black FPR=44.9% vs White FPR=23.5%. "
        "Because base rates differ (51.4% vs 39.4%), "
        "this is mathematically inevitable under calibration."
    ),
    "policy_implication": (
        "Organizations must make an explicit normative choice: "
        "prioritise calibration accuracy OR equitable error rates. "
        "This is a social/legal decision, not a technical one."
    ),
    "source": "Corbett-Davies et al. (2017). Algorithmic Decision Making and the Cost of Fairness.",
}


# ─── Five Abstraction Traps (Selbst et al., FAccT 2019) ──────────────────────

ABSTRACTION_TRAPS = {
    "framing_trap": {
        "name": "The Framing Trap",
        "definition": (
            "Bounding the problem within the 'algorithmic frame' — "
            "focusing only on the input-output mapping and ignoring "
            "the data generation process and institutional context."
        ),
        "fairlens_mitigation": (
            "FairLens audits the full pipeline (data → model → decision → impact), "
            "not just model outputs."
        ),
    },
    "portability_trap": {
        "name": "The Portability Trap",
        "definition": (
            "Assuming a fairness definition or intervention can be ported "
            "across contexts without losing validity."
        ),
        "fairlens_mitigation": (
            "FairLens allows domain-specific metric configuration — "
            "hiring, lending, and healthcare use different fairness thresholds."
        ),
    },
    "formalism_trap": {
        "name": "The Formalism Trap",
        "definition": (
            "Attempting to resolve contested social definitions of fairness "
            "using only mathematical tools, ignoring which errors are "
            "socially acceptable in context."
        ),
        "fairlens_mitigation": (
            "FairLens explicitly surfaces the Impossibility Theorem trade-off "
            "and asks users to choose which fairness criterion to prioritise."
        ),
    },
    "ripple_effect_trap": {
        "name": "The Ripple Effect Trap",
        "definition": (
            "Failing to account for how introducing an algorithm changes "
            "the behaviour of social actors and creates new inequities."
        ),
        "fairlens_mitigation": (
            "Pipeline Auditor models behavioural feedback loops "
            "across sequential decision stages."
        ),
    },
    "solutionism_trap": {
        "name": "The Solutionism Trap",
        "definition": (
            "Defining problems in ways that make them amenable to "
            "technological fixes, ignoring structural causes."
        ),
        "fairlens_mitigation": (
            "FairLens explicitly recommends non-technical interventions "
            "in its Claude-powered explanations when appropriate."
        ),
    },
    "source": "Selbst et al. (2019). Fairness and Abstraction in Sociotechnical Systems. FAccT.",
}


# ─── Counterfactual Fairness (Kusner et al., NeurIPS 2017) ───────────────────

COUNTERFACTUAL_FAIRNESS = {
    "definition": (
        "A predictor Ŷ is counterfactually fair if for any individual "
        "(X=x, A=a), the probability distribution of the prediction "
        "is unchanged when A is intervened upon to become a': "
        "P(Ŷ_{A←a}(U)=y | X=x, A=a) = P(Ŷ_{A←a'}(U)=y | X=x, A=a)"
    ),
    "key_insight": (
        "If a feature like 'prior arrests' is causally downstream of 'race' "
        "(due to systemic policing bias), using it in a model violates "
        "counterfactual fairness — even if 'race' itself is excluded."
    ),
    "practical_threshold": 0.15,   # >15% flip rate = evidence of CF violation
    "source": "Kusner et al. (2017). Counterfactual Fairness. NeurIPS.",
}


# ─── Aequitas Metric Selection (Saleiro et al., 2018) ────────────────────────

AEQUITAS_FRAMEWORK = {
    "punitive_systems": {
        "examples": ["credit denial", "criminal sentencing", "deportation"],
        "priority_metric": "False Positive Rate Parity",
        "reason": (
            "A false alarm in a punitive system unfairly harms an individual. "
            "Minimise FPR disparity."
        ),
    },
    "assistive_systems": {
        "examples": ["healthcare subsidies", "job training", "educational support"],
        "priority_metric": "False Negative Rate Parity",
        "reason": (
            "A false negative in an assistive system unfairly denies "
            "a needed benefit. Minimise FNR disparity."
        ),
    },
    "three_intervention_stages": [
        "Pre-processing: transform training data (reweighing, resampling, geometric debiasing)",
        "In-processing: modify learning algorithm with fairness constraints (FairGBM, Fairlearn)",
        "Post-processing: adjust predictions after training (group-specific thresholds)",
    ],
    "source": "Saleiro et al. (2018). Aequitas: A Bias and Fairness Audit Toolkit.",
}


# ─── India Credit Market (RBI / NABARD) ──────────────────────────────────────

INDIA_CREDIT_DATA = {
    "gender_gap_loans":     0.27,   # Women 27% less likely to receive formal credit
    "rural_approval_gap":   0.34,   # Rural applicants 34% lower approval rate
    "income_tier_gap":      0.41,   # Low-income 41% lower approval
    "female_applicant_pct": 0.38,   # Only 38% of formal loan applicants are women
    "rural_credit_share":   0.11,   # Rural India = 11% of formal credit despite 65% of population
    "sources": [
        "RBI Annual Report 2023: Report on Trend and Progress of Banking in India",
        "NABARD Rural Finance Report 2022",
        "CIBIL India Credit Market Indicator 2023",
    ],
}


# ─── Disparate Impact Legal Thresholds ───────────────────────────────────────

LEGAL_THRESHOLDS = {
    "us_eeoc_80_rule":     0.80,   # US EEOC: DI < 0.80 = prima facie discrimination
    "eu_ai_act_high_risk": True,   # Credit/employment = high-risk under EU AI Act 2024
    "india_dpdp":          True,   # India Digital Personal Data Protection Act 2023
    "ideal_di_range":      (0.80, 1.25),
    "ideal_dp_diff":       0.10,
    "ideal_eo_diff":       0.10,
    "ideal_calibration":   0.05,
    "ideal_individual_f":  0.90,
    "ideal_cf_rate":       0.15,
}
