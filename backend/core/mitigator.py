"""
FairLens Mitigator
Applies bias mitigation strategies and returns before/after metric comparison.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from models.schemas import (
    MetricResult, MitigationResult, MitigationStrategy, AuditConfig
)
from core.bias_detector import BiasDetector


class BiasMitigator:
    def __init__(self, df: pd.DataFrame, config: AuditConfig, sensitive_attribute: str):
        self.df = df.copy()
        self.config = config
        self.sensitive_attribute = sensitive_attribute

    def _get_feature_cols(self) -> list[str]:
        exclude = {
            self.config.label_column,
            self.config.ground_truth_column,
            self.sensitive_attribute,
        }
        if self.config.score_column:
            exclude.add(self.config.score_column)
        return [
            c for c in self.df.select_dtypes(include=[np.number]).columns
            if c not in exclude
        ]

    def apply(self, strategy: MitigationStrategy) -> MitigationResult:
        # Get before metrics
        before_detector = BiasDetector(self.df, self.config)
        before_output = before_detector.run()
        before_metrics = before_output.metrics

        if strategy == MitigationStrategy.REWEIGHING:
            mitigated_df = self._reweighing()
        elif strategy == MitigationStrategy.THRESHOLD_OPTIMIZER:
            mitigated_df = self._threshold_optimizer()
        elif strategy == MitigationStrategy.RESAMPLING:
            mitigated_df = self._resampling()
        else:
            mitigated_df = self._reweighing()  # fallback

        after_detector = BiasDetector(mitigated_df, self.config)
        after_output = after_detector.run()
        after_metrics = after_output.metrics

        # Compute fairness improvement (fraction of metrics improved)
        improved = 0
        for bm, am in zip(before_metrics, after_metrics):
            if am.verdict.value <= bm.verdict.value:  # enum ordering: fair < marginal < biased
                improved += 1
        fairness_improvement = improved / len(before_metrics) if before_metrics else 0.0

        # Compute accuracy delta
        y_true = self.df[self.config.ground_truth_column].values
        before_acc = (self.df[self.config.label_column].values == y_true).mean()
        after_acc = (mitigated_df[self.config.label_column].values == y_true).mean()
        accuracy_delta = round(float(after_acc - before_acc), 4)

        return MitigationResult(
            strategy=strategy,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            accuracy_delta=accuracy_delta,
            fairness_improvement=round(fairness_improvement, 4),
        )

    def _reweighing(self) -> pd.DataFrame:
        """
        Reweighing (Kamiran & Calders, 2012).
        Assigns sample weights inversely proportional to the joint probability
        of (sensitive_attribute, label) so that each group*outcome cell
        is represented proportionally.
        """
        df = self.df.copy()
        sensitive = df[self.sensitive_attribute]
        labels = df[self.config.ground_truth_column]
        n = len(df)

        weights = np.ones(n)
        for g in sensitive.unique():
            for y in [0, 1]:
                mask = (sensitive == g) & (labels == y)
                p_g = (sensitive == g).mean()
                p_y = (labels == y).mean()
                p_gy = mask.mean()
                if p_gy > 0:
                    w = (p_g * p_y) / p_gy
                    weights[mask] = w

        # Re-train a logistic regression with the new weights, replace predictions
        feature_cols = self._get_feature_cols()
        if len(feature_cols) < 1:
            return df

        X = df[feature_cols].fillna(0).values
        y = labels.values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        clf = LogisticRegression(max_iter=500, random_state=42)
        clf.fit(X_scaled, y, sample_weight=weights)
        df[self.config.label_column] = clf.predict(X_scaled)
        return df

    def _threshold_optimizer(self) -> pd.DataFrame:
        """
        Post-processing threshold optimizer.
        Finds the per-group classification threshold that equalises TPR
        across groups while maximising overall accuracy.
        """
        df = self.df.copy()
        sensitive = df[self.sensitive_attribute]
        y_true = df[self.config.ground_truth_column].values

        score_col = self.config.score_column
        if not score_col or score_col not in df.columns:
            # Estimate scores from logistic regression if not provided
            feature_cols = self._get_feature_cols()
            if not feature_cols:
                return df
            X = df[feature_cols].fillna(0).values
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            clf = LogisticRegression(max_iter=500, random_state=42)
            clf.fit(X_scaled, y_true)
            scores = clf.predict_proba(X_scaled)[:, 1]
        else:
            scores = df[score_col].values

        new_preds = np.zeros(len(df), dtype=int)
        for g in sensitive.unique():
            mask = (sensitive == g).values
            group_scores = scores[mask]
            group_truth = y_true[mask]

            # Find threshold that maximises balanced accuracy for this group
            best_thresh, best_ba = 0.5, 0.0
            for thresh in np.linspace(0.1, 0.9, 17):
                preds = (group_scores >= thresh).astype(int)
                tp = ((group_truth == 1) & (preds == 1)).sum()
                tn = ((group_truth == 0) & (preds == 0)).sum()
                fn = ((group_truth == 1) & (preds == 0)).sum()
                fp = ((group_truth == 0) & (preds == 1)).sum()
                tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
                tnr = tn / (tn + fp) if (tn + fp) > 0 else 0
                ba = (tpr + tnr) / 2
                if ba > best_ba:
                    best_ba = ba
                    best_thresh = thresh

            new_preds[mask] = (group_scores >= best_thresh).astype(int)

        df[self.config.label_column] = new_preds
        return df

    def _resampling(self) -> pd.DataFrame:
        """
        Uniform resampling.
        Oversamples underrepresented (group, label) combinations
        so all cells have equal representation before retraining.
        """
        df = self.df.copy()
        sensitive = df[self.sensitive_attribute]
        labels = df[self.config.ground_truth_column]

        # Find target size: max(group * label cell counts)
        cell_counts = {}
        for g in sensitive.unique():
            for y in [0, 1]:
                mask = (sensitive == g) & (labels == y)
                cell_counts[(g, y)] = mask.sum()

        if not cell_counts:
            return df

        target = max(cell_counts.values())
        frames = [df]
        for (g, y), count in cell_counts.items():
            if count < target:
                subset = df[(sensitive == g) & (labels == y)]
                extra = subset.sample(n=target - count, replace=True, random_state=42)
                frames.append(extra)

        balanced_df = pd.concat(frames, ignore_index=True)

        feature_cols = self._get_feature_cols()
        if not feature_cols:
            return df

        X = balanced_df[feature_cols].fillna(0).values
        y = balanced_df[self.config.ground_truth_column].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        clf = LogisticRegression(max_iter=500, random_state=42)
        clf.fit(X_scaled, y)

        # Predict on original (unbalanced) df
        X_orig = df[feature_cols].fillna(0).values
        X_orig_scaled = scaler.transform(X_orig)
        df[self.config.label_column] = clf.predict(X_orig_scaled)
        return df
