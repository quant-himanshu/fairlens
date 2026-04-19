# FairLens — AI Bias Detection & Fairness Auditing Platform

> Built for Google Solution Challenge 2026 · Problem 4: Unbiased AI Decision

FairLens detects, explains, and fixes bias in AI decision-making pipelines — for hiring, lending, healthcare, and beyond. It gives organizations a clear, actionable dashboard to measure fairness before their systems impact real people.

---

## What It Does

- **Audit any dataset or model** for hidden bias and discrimination
- **6 fairness metrics** computed in real-time: Disparate Impact, Demographic Parity, Equalized Odds, Calibration, Individual Fairness, Counterfactual Fairness
- **Claude AI explanations** — plain-language reasoning for every bias finding
- **Fix suggestions** — automated reweighing, resampling, and threshold tuning
- **Before/after comparison** — see exactly how much bias was removed
- **PDF audit report** — exportable for compliance and governance

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Recharts |
| Backend | FastAPI, Python 3.11 |
| ML / Fairness | scikit-learn, fairlearn, aif360, SHAP |
| AI Explanations | Anthropic Claude API |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | NextAuth.js |

---

## Project Structure

```
fairlens/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── requirements.txt
│   ├── api/
│   │   ├── audit.py             # /audit endpoints
│   │   ├── explain.py           # /explain endpoints (Claude)
│   │   └── datasets.py          # /datasets endpoints
│   ├── core/
│   │   ├── bias_detector.py     # Core fairness metrics engine
│   │   ├── mitigator.py         # Bias mitigation algorithms
│   │   ├── explainer.py         # SHAP + Claude explanations
│   │   └── report_gen.py        # PDF report generator
│   ├── models/
│   │   └── schemas.py           # Pydantic models
│   └── utils/
│       ├── data_loader.py       # CSV/JSON ingestion
│       └── validators.py
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # Landing / upload
│   │   ├── audit/
│   │   │   └── [id]/page.tsx    # Audit results dashboard
│   │   └── api/
│   │       └── proxy/route.ts   # API proxy
│   ├── components/
│   │   ├── MetricCard.tsx       # Single fairness metric display
│   │   ├── BiasRadar.tsx        # Radar chart of all metrics
│   │   ├── FeatureImportance.tsx # SHAP waterfall chart
│   │   ├── MitigationPanel.tsx  # Fix suggestions + apply
│   │   ├── DataUploader.tsx     # Drag-drop CSV uploader
│   │   └── AuditReport.tsx      # Full audit summary
│   └── lib/
│       ├── api.ts               # Backend API client
│       └── types.ts             # Shared TypeScript types
├── data/
│   └── samples/
│       ├── hiring_biased.csv    # Demo: biased hiring dataset
│       ├── lending_biased.csv   # Demo: biased loan approvals
│       └── healthcare_biased.csv
├── docs/
│   ├── architecture.md
│   └── fairness_metrics.md
└── docker-compose.yml
```

---

## Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+
- Anthropic API key

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Mac/Linux
pip install -r requirements.txt
cp ../.env.example .env           # add your ANTHROPIC_API_KEY
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
cp ../.env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## How It Works

1. **Upload** a CSV dataset (predictions, ground truth, sensitive attributes)
2. **Configure** which columns are sensitive (gender, race, age) and what the outcome is
3. **Audit** — FairLens computes all 6 fairness metrics in seconds
4. **Explain** — Claude reads the metrics and explains bias in plain English
5. **Mitigate** — Apply one-click fixes and see the before/after delta
6. **Export** — Download a full PDF audit report for compliance

---

## Fairness Metrics

| Metric | What It Measures | Ideal Value |
|---|---|---|
| Disparate Impact | Ratio of positive outcomes across groups | 0.8 – 1.25 |
| Demographic Parity | Difference in positive prediction rates | < 0.1 |
| Equalized Odds | TPR and FPR gap across groups | < 0.1 |
| Calibration | Confidence score accuracy per group | < 0.05 |
| Individual Fairness | Similar people get similar outcomes | > 0.9 |
| Counterfactual Fairness | Outcome change if sensitive attr flipped | < 0.15 |

---

## Demo

The `/data/samples/` directory contains three pre-built biased datasets for instant demo:
- **Hiring**: Resume screening with gender bias
- **Lending**: Loan approval with racial bias  
- **Healthcare**: Treatment recommendation with age bias

---

## Evaluation Criteria Alignment

| Criterion | Weight | Our Advantage |
|---|---|---|
| Technical Merit | 40% | 6 metrics, SHAP, mitigation algorithms, real Claude Code internals audit |
| Innovation | 25% | First tool to audit Claude Code's own decision pipeline |
| Cause Alignment | 25% | Directly prevents AI discrimination in hiring/lending/healthcare |
| UX | 10% | One-page upload → results in < 5 seconds |

---

## Team
Built with ❤️ for Google Solution Challenge 2026 India
