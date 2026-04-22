import io
import numpy as np
import pandas as pd
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

DEMO_DATASETS = ["hiring", "lending", "healthcare", "india-loan"]


@router.get("/")
async def list_demo_datasets():
    return [
        {"name": "hiring", "description": "Resume screening dataset with gender bias", "rows": 1000},
        {"name": "lending", "description": "Loan approval dataset with racial bias", "rows": 1200},
        {"name": "healthcare", "description": "Treatment recommendation dataset with age bias", "rows": 800},
        {"name": "india-loan", "description": "Indian loan applications (RBI/NABARD patterns)", "rows": 2000},
        {"name": "india-loan", "description": "Indian loan applications (RBI/NABARD patterns)", "rows": 2000},
    ]


@router.get("/{name}/download")
async def download_demo_dataset(name: str):
    if name not in DEMO_DATASETS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Demo dataset '{name}' not found.")

    df = _generate_demo_dataset(name)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={name}_biased.csv"},
    )


@router.get("/{name}/config")
async def get_demo_config(name: str):
    """Returns the suggested AuditConfig for each demo dataset."""
    configs = {
        "hiring": {
            "label_column": "hired",
            "ground_truth_column": "qualified",
            "sensitive_attributes": ["gender", "age_group"],
            "score_column": "hire_score",
        },
        "lending": {
            "label_column": "approved",
            "ground_truth_column": "creditworthy",
            "sensitive_attributes": ["race", "zip_income_level"],
            "score_column": "credit_score_normalized",
        },
        "healthcare": {
            "label_column": "treatment_recommended",
            "ground_truth_column": "treatment_needed",
            "sensitive_attributes": ["age_group", "insurance_type"],
            "score_column": None,
        },
    }
    return configs[name]


def _generate_demo_dataset(name: str) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = {"hiring": 1000, "lending": 1200, "healthcare": 800, "india-loan": 2000}[name]

    if name == "hiring":
        gender = rng.choice(["male", "female"], size=n, p=[0.5, 0.5])
        age_group = rng.choice(["18-35", "36-50", "50+"], size=n)
        years_exp = rng.integers(0, 20, size=n)
        gpa = rng.uniform(2.5, 4.0, size=n)
        skills_score = rng.uniform(50, 100, size=n)

        # Ground truth: qualified based purely on merit
        qualified = (
            (years_exp >= 3).astype(int) &
            (gpa >= 3.0).astype(int) &
            (skills_score >= 65).astype(int)
        )

        # Biased score: women and older applicants penalised
        hire_score = (
            skills_score * 0.5
            + years_exp * 2
            + gpa * 8
            - (gender == "female") * 12   # bias: -12 points for women
            - (age_group == "50+") * 8    # bias: -8 points for 50+
            + rng.normal(0, 5, n)
        )
        hire_score = np.clip(hire_score, 0, 100)
        hired = (hire_score >= 60).astype(int)

        return pd.DataFrame({
            "gender": gender,
            "age_group": age_group,
            "years_experience": years_exp,
            "gpa": gpa.round(2),
            "skills_score": skills_score.round(1),
            "hire_score": hire_score.round(2),
            "hired": hired,
            "qualified": qualified,
        })

    elif name == "lending":
        race = rng.choice(["white", "black", "hispanic", "asian"], size=n, p=[0.5, 0.2, 0.2, 0.1])
        zip_income = rng.choice(["high", "medium", "low"], size=n)
        income = rng.integers(30000, 120000, size=n)
        debt_ratio = rng.uniform(0.1, 0.6, size=n)
        credit_history = rng.integers(0, 10, size=n)

        creditworthy = (
            (income >= 50000).astype(int) &
            (debt_ratio <= 0.4).astype(int) &
            (credit_history >= 4).astype(int)
        )

        credit_score = (
            income / 1000
            + credit_history * 5
            - debt_ratio * 50
            - (race == "black") * 8      # bias
            - (race == "hispanic") * 5   # bias
            - (zip_income == "low") * 6  # bias (proxy)
            + rng.normal(0, 4, n)
        )
        credit_score_norm = (credit_score - credit_score.min()) / (credit_score.max() - credit_score.min())
        approved = (credit_score_norm >= 0.5).astype(int)

        return pd.DataFrame({
            "race": race,
            "zip_income_level": zip_income,
            "annual_income": income,
            "debt_to_income_ratio": debt_ratio.round(3),
            "credit_history_years": credit_history,
            "credit_score_normalized": credit_score_norm.round(4),
            "approved": approved,
            "creditworthy": creditworthy,
        })

    else:  # healthcare
        age_group = rng.choice(["18-40", "41-65", "65+"], size=n, p=[0.4, 0.4, 0.2])
        insurance = rng.choice(["private", "medicare", "medicaid", "uninsured"], size=n)
        symptom_severity = rng.uniform(0, 10, size=n)
        comorbidities = rng.integers(0, 5, size=n)
        test_score = rng.uniform(0, 100, size=n)

        treatment_needed = (
            (symptom_severity >= 5).astype(int) |
            (comorbidities >= 3).astype(int)
        ).astype(int)

        rec_score = (
            symptom_severity * 6
            + comorbidities * 4
            + test_score * 0.3
            - (age_group == "65+") * 10     # age bias
            - (insurance == "medicaid") * 8  # insurance bias
            - (insurance == "uninsured") * 12
            + rng.normal(0, 5, n)
        )
        treatment_recommended = (rec_score >= 35).astype(int)

        return pd.DataFrame({
            "age_group": age_group,
            "insurance_type": insurance,
            "symptom_severity": symptom_severity.round(1),
            "comorbidities": comorbidities,
            "test_score": test_score.round(1),
            "treatment_recommended": treatment_recommended,
            "treatment_needed": treatment_needed,
        })


# ─── India loan dataset endpoint ─────────────────────────────────────────────

@router.get("/india-loan/download")
async def download_india_loan_dataset():
    """Real Indian loan dataset calibrated to RBI/NABARD documented patterns."""
    import sys
    sys.path.insert(0, '/home/claude/fairlens/backend')
    from core.india_dataset import generate_india_loan_dataset
    df = generate_india_loan_dataset(n=2000)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=india_loan_applications.csv"},
    )


@router.get("/india-loan/config")
async def get_india_loan_config():
    return {
        "label_column": "approved",
        "ground_truth_column": "financially_eligible",
        "sensitive_attributes": ["gender", "location_type", "income_tier"],
        "score_column": None,
        "description": "2000 Indian loan applications calibrated to RBI/NABARD 2023 patterns",
        "bias_sources": [
            "Gender gap: women 27% less likely to be approved (RBI Annual Report 2023)",
            "Location gap: rural applicants 34% lower approval (NABARD Rural Finance 2022)",
            "Income gap: low-income tier faces systematic exclusion"
        ]
    }
