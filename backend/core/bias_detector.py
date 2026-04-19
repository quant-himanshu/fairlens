"""
FairLens Core Bias Detector
Computes 6 fairness metrics across all sensitive attribute groups.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional

from models.schemas import (
    MetricResult, GroupStats, FairnessVerdict, AuditConfig
)


@dataclass
class DetectorOutput:
    metrics: list[MetricResult]
    group_stats: list[GroupStats]
    overall_verdict: FairnessVerdict
    top_biased_feature: Optional[str]


def _verdict(value: float, lo: float, hi: float) -> FairnessVerdict:
    """Map a metric value against its ideal range to a verdict."""
    in_range = lo <= value <= hi
    distance = min(abs(value - lo), abs(value - hi))
    if in_range:
        return FairnessVerdict.FAIR
    if distance < 0.05:
        return FairnessVerdict.MARGINAL
    if distance < 0.15:
        return FairnessVerdict.BIASED
    return FairnessVerdict.SEVERELY_BIASED


def _overall_verdict(metrics: list[MetricResult]) -> FairnessVerdict:
    """Roll individual metric verdicts into one overall verdict."""
    severity_order = [
        FairnessVerdict.FAIR,
        FairnessVerdict.MARGINAL,
        FairnessVerdict.BIASED,
        FairnessVerdict.SEVERELY_BIASED,
    ]
    worst = max(metrics, key=lambda m: severity_order.index(m.verdict))
    return worst.verdict


class BiasDetector:
    def __init__(self, df: pd.DataFrame, config: AuditConfig):
        self.df = df.copy()
        self.config = config
        self.y_pred = df[config.label_column].values.astype(int)
        self.y_true = df[config.ground_truth_column].values.astype(int)
        self.scores = (
            df[config.score_column].values
            if config.score_column and config.score_column in df.columns
            else None
        )

    def run(self) -> DetectorOutput:
        all_metrics: list[MetricResult] = []
        all_group_stats: list[GroupStats] = []
        worst_feature = None
        worst_score = 0.0

        for attr in self.config.sensitive_attributes:
            if attr not in self.df.columns:
                continue

            sensitive = self.df[attr]
            metrics = self._compute_metrics_for_attribute(attr, sensitive)
            group_stats = self._compute_group_stats(attr, sensitive)

            all_metrics.extend(metrics)
            all_group_stats.extend(group_stats)

            # Track which attribute is the biggest offender
            attr_bias_score = sum(
                1 for m in metrics
                if m.verdict in (FairnessVerdict.BIASED, FairnessVerdict.SEVERELY_BIASED)
            )
            if attr_bias_score > worst_score:
                worst_score = attr_bias_score
                worst_feature = attr

        overall = _overall_verdict(all_metrics) if all_metrics else FairnessVerdict.FAIR

        return DetectorOutput(
            metrics=all_metrics,
            group_stats=all_group_stats,
            overall_verdict=overall,
            top_biased_feature=worst_feature,
        )

    def _compute_metrics_for_attribute(
        self, attr: str, sensitive: pd.Series
    ) -> list[MetricResult]:
        metrics: list[MetricResult] = []
        groups = sensitive.unique()

        if len(groups) < 2:
            return metrics

        # --- 1. Disparate Impact ---
        rates = {g: self.y_pred[sensitive == g].mean() for g in groups}
        max_rate = max(rates.values())
        min_rate = min(rates.values())
        di = min_rate / max_rate if max_rate > 0 else 1.0
        disadvantaged = min(rates, key=rates.get)
        metrics.append(MetricResult(
            name=f"Disparate Impact ({attr})",
            value=round(di, 4),
            ideal_range=(0.8, 1.25),
            verdict=_verdict(di, 0.8, 1.25),
            description=(
                "Ratio of positive outcome rates between the least and most favoured group. "
                "Below 0.8 indicates the '80% rule' legal threshold is violated."
            ),
            affected_group=str(disadvantaged),
        ))

        # --- 2. Demographic Parity Difference ---
        dp_diff = max_rate - min_rate
        metrics.append(MetricResult(
            name=f"Demographic Parity ({attr})",
            value=round(dp_diff, 4),
            ideal_range=(0.0, 0.1),
            verdict=_verdict(dp_diff, 0.0, 0.1),
            description=(
                "Absolute difference in positive prediction rates between groups. "
                "Values above 0.1 suggest the model treats groups systematically differently."
            ),
            affected_group=str(disadvantaged),
        ))

        # --- 3. Equalized Odds ---
        tpr_by_group, fpr_by_group = {}, {}
        for g in groups:
            mask = sensitive == g
            yt, yp = self.y_true[mask], self.y_pred[mask]
            tp = ((yt == 1) & (yp == 1)).sum()
            fn = ((yt == 1) & (yp == 0)).sum()
            fp = ((yt == 0) & (yp == 1)).sum()
            tn = ((yt == 0) & (yp == 0)).sum()
            tpr_by_group[g] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            fpr_by_group[g] = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        tpr_vals = list(tpr_by_group.values())
        fpr_vals = list(fpr_by_group.values())
        eo_diff = max(
            max(tpr_vals) - min(tpr_vals),
            max(fpr_vals) - min(fpr_vals),
        )
        metrics.append(MetricResult(
            name=f"Equalized Odds ({attr})",
            value=round(eo_diff, 4),
            ideal_range=(0.0, 0.1),
            verdict=_verdict(eo_diff, 0.0, 0.1),
            description=(
                "Max gap in True Positive Rate and False Positive Rate across groups. "
                "High values mean the model makes different types of errors for different groups."
            ),
        ))

        # --- 4. Calibration Gap (if scores available) ---
        if self.scores is not None:
            cal_gaps = []
            for g in groups:
                mask = sensitive == g
                predicted_probs = self.scores[mask]
                actual_outcomes = self.y_true[mask]
                bins = np.linspace(0, 1, 6)
                for i in range(len(bins) - 1):
                    in_bin = (predicted_probs >= bins[i]) & (predicted_probs < bins[i + 1])
                    if in_bin.sum() > 5:
                        predicted_mean = predicted_probs[in_bin].mean()
                        actual_mean = actual_outcomes[in_bin].mean()
                        cal_gaps.append(abs(predicted_mean - actual_mean))
            cal_gap = np.mean(cal_gaps) if cal_gaps else 0.0
            metrics.append(MetricResult(
                name=f"Calibration Gap ({attr})",
                value=round(float(cal_gap), 4),
                ideal_range=(0.0, 0.05),
                verdict=_verdict(float(cal_gap), 0.0, 0.05),
                description=(
                    "Average difference between predicted probability and actual outcome rate "
                    "within score buckets. Miscalibration means confidence scores lie."
                ),
            ))

        # --- 5. Individual Fairness (approximate) ---
        # Measures whether similar individuals get similar predictions.
        # Approximated by checking prediction consistency within tight feature neighbourhoods.
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [
            c for c in numeric_cols
            if c not in [self.config.label_column, self.config.ground_truth_column]
            and c != attr
        ]
        if len(feature_cols) >= 2:
            from sklearn.preprocessing import StandardScaler
            from sklearn.neighbors import NearestNeighbors

            X = self.df[feature_cols].fillna(0).values
            X_scaled = StandardScaler().fit_transform(X)
            nn = NearestNeighbors(n_neighbors=5, metric="euclidean")
            nn.fit(X_scaled)
            _, indices = nn.kneighbors(X_scaled)

            consistent = 0
            total = len(X)
            for i, neighbours in enumerate(indices):
                pred_i = self.y_pred[i]
                neighbour_preds = self.y_pred[neighbours[1:]]
                if (neighbour_preds == pred_i).mean() >= 0.6:
                    consistent += 1

            ind_fairness = consistent / total if total > 0 else 1.0
            metrics.append(MetricResult(
                name=f"Individual Fairness ({attr})",
                value=round(ind_fairness, 4),
                ideal_range=(0.9, 1.0),
                verdict=_verdict(ind_fairness, 0.9, 1.0),
                description=(
                    "Fraction of individuals who receive the same prediction as their "
                    "nearest neighbours (by non-sensitive features). Low = similar people treated differently."
                ),
            ))

        # --- 6. Counterfactual Fairness ---
        # How many predictions flip when we change only the sensitive attribute?
        flipped = 0
        total_checked = 0
        for g_a, g_b in zip(groups, groups[1:]):
            mask_a = sensitive == g_a
            mask_b = sensitive == g_b
            n = min(mask_a.sum(), mask_b.sum(), 200)  # cap for speed
            if n < 10:
                continue
            preds_a = self.y_pred[mask_a][:n]
            preds_b = self.y_pred[mask_b][:n]
            flipped += (preds_a != preds_b).sum()
            total_checked += n

        cf_rate = flipped / total_checked if total_checked > 0 else 0.0
        metrics.append(MetricResult(
            name=f"Counterfactual Fairness ({attr})",
            value=round(cf_rate, 4),
            ideal_range=(0.0, 0.15),
            verdict=_verdict(cf_rate, 0.0, 0.15),
            description=(
                "Fraction of predictions that flip when only the sensitive attribute changes "
                "(Kusner et al., NeurIPS 2017). Above 15% = counterfactual fairness violation. "
                "Reference: COMPAS showed 44.9% FPR for Black vs 23.5% for White defendants "
                "(ProPublica, 2016) — a 1.91x disparity ratio."
            ),
        ))

        return metrics

    def _compute_group_stats(
        self, attr: str, sensitive: pd.Series
    ) -> list[GroupStats]:
        stats = []
        for g in sensitive.unique():
            mask = sensitive == g
            yt = self.y_true[mask]
            yp = self.y_pred[mask]
            tp = ((yt == 1) & (yp == 1)).sum()
            fn = ((yt == 1) & (yp == 0)).sum()
            fp = ((yt == 0) & (yp == 1)).sum()
            tn = ((yt == 0) & (yp == 0)).sum()
            stats.append(GroupStats(
                group_name=str(g),
                attribute=attr,
                count=int(mask.sum()),
                positive_rate=round(float(yp.mean()), 4),
                true_positive_rate=round(tp / (tp + fn), 4) if (tp + fn) > 0 else None,
                false_positive_rate=round(fp / (fp + tn), 4) if (fp + tn) > 0 else None,
            ))
        return stats
