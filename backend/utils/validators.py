import pandas as pd
from models.schemas import AuditConfig


def validate_dataframe(df: pd.DataFrame, config: AuditConfig) -> list[str]:
    errors = []

    if config.label_column not in df.columns:
        errors.append(f"Label column '{config.label_column}' not found in CSV.")
    if config.ground_truth_column not in df.columns:
        errors.append(f"Ground truth column '{config.ground_truth_column}' not found in CSV.")
    for attr in config.sensitive_attributes:
        if attr not in df.columns:
            errors.append(f"Sensitive attribute column '{attr}' not found in CSV.")
    if len(df) < 50:
        errors.append("Dataset too small. Need at least 50 rows for meaningful fairness analysis.")

    if not errors:
        label_vals = df[config.label_column].dropna().unique()
        if not all(v in [0, 1] for v in label_vals):
            errors.append(
                f"Label column '{config.label_column}' must contain binary values (0/1). "
                f"Found: {list(label_vals[:5])}"
            )

    return errors
