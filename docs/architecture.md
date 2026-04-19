# FairLens Architecture

## Overview

FairLens is a two-service application:
- **Backend**: Python FastAPI serving the bias detection API
- **Frontend**: Next.js 14 React dashboard

```
Browser → Next.js (port 3000) → FastAPI (port 8000) → Claude API
                                        ↓
                               BiasDetector (6 metrics)
                               BiasMitigator (3 strategies)
                               AIExplainer (Claude)
                               ReportGenerator (PDF)
```

---

## Request lifecycle: Upload & Audit

```
POST /api/audit/upload  (multipart/form-data: CSV + config)
  → validate_dataframe()          # check columns exist, binary labels, min rows
  → BiasDetector.run()
      → _compute_metrics_for_attribute()  ×  n_sensitive_attrs
          → Disparate Impact
          → Demographic Parity Difference
          → Equalized Odds
          → Calibration Gap         (if score column provided)
          → Individual Fairness     (k-NN approximation)
          → Counterfactual Fairness (group swap approximation)
      → _compute_group_stats()
  → _overall_verdict()            # worst metric wins
  → store in _audit_store[uuid]
  → return AuditResult (JSON)
```

---

## Request lifecycle: Explain

```
POST /api/explain/  { audit_id }
  → load AuditResult from store
  → check _explain_cache (avoid re-billing Claude)
  → build prompt (metrics + group stats as JSON)
  → anthropic.messages.create(model="claude-sonnet-4-20250514")
  → parse JSON response → ExplainResponse
  → cache + return
```

---

## Request lifecycle: Mitigate

```
POST /api/audit/mitigate  { audit_id, strategy, sensitive_attribute }
  → BiasMitigator.apply(strategy)
      → reweighing:           Kamiran & Calders sample weights + LR retrain
      → threshold_optimizer:  per-group threshold search for equalized balanced accuracy
      → resampling:           oversample minority (group, label) cells + LR retrain
  → BiasDetector.run() on mitigated DataFrame (after metrics)
  → compute fairness_improvement + accuracy_delta
  → return MitigationResult
```

---

## Fairness Metrics — Mathematical Definitions

### 1. Disparate Impact (DI)
```
DI = min_g P(Ŷ=1 | G=g) / max_g P(Ŷ=1 | G=g)

Ideal: 0.8 ≤ DI ≤ 1.25
Legal threshold (US EEOC 80% rule): DI < 0.8 is prima facie evidence of discrimination
```

### 2. Demographic Parity Difference (DPD)
```
DPD = max_g P(Ŷ=1 | G=g) - min_g P(Ŷ=1 | G=g)

Ideal: DPD < 0.1
```

### 3. Equalized Odds (EO)
```
EO = max(
  max_g TPR_g - min_g TPR_g,
  max_g FPR_g - min_g FPR_g
)

Where TPR_g = P(Ŷ=1 | Y=1, G=g),  FPR_g = P(Ŷ=1 | Y=0, G=g)

Ideal: EO < 0.1
```

### 4. Calibration Gap
```
For each group g and score bin b:
  gap_b = |mean(scores in b for group g) - mean(outcomes in b for group g)|

CalibrationGap = mean(gap_b) across all groups and bins

Ideal: < 0.05
```

### 5. Individual Fairness (k-NN approximation)
```
For each individual i, find k=5 nearest neighbours by non-sensitive features.
IndividualFairness = fraction of individuals where ≥60% of neighbours share prediction.

Ideal: > 0.9
```

### 6. Counterfactual Fairness
```
For groups A and B (each sensitive attribute pair):
  Sample n individuals from each group
  CounterfactualRate = fraction where pred(A_i) ≠ pred(B_i)

Ideal: < 0.15
```

---

## Mitigation Algorithms

### Reweighing (Kamiran & Calders, 2012)
Pre-processing. Assigns sample weights:
```
w(x_i) = P(G=g) × P(Y=y) / P(G=g, Y=y)
```
Upweights underrepresented (group, outcome) pairs before training.

### Threshold Optimizer (post-processing)
For each group independently, finds the decision threshold that maximises balanced accuracy:
```
balanced_accuracy = (TPR + TNR) / 2
threshold* = argmax_{t ∈ [0.1, 0.9]} balanced_accuracy(predictions_g ≥ t)
```

### Resampling (pre-processing)
Oversamples minority (group × label) cells to equal size, retrains classifier on balanced data.

---

## Data Flow Diagram

```
CSV Upload
    │
    ▼
validate_dataframe()
    │
    ▼
pandas.DataFrame
    │
    ├──────────────────────────────────┐
    ▼                                  ▼
BiasDetector                    Store in memory
    │                            _audit_store[uuid]
    ├── DisparateImpact                │
    ├── DemographicParity             │
    ├── EqualizedOdds        ◄────────┘
    ├── CalibrationGap           (on explain/mitigate request)
    ├── IndividualFairness
    └── CounterfactualFairness
          │
          ▼
    AuditResult (JSON)
          │
          ├──── /api/explain/ ──► Claude API ──► ExplainResponse
          │
          ├──── /api/audit/mitigate ──► BiasMitigator ──► MitigationResult
          │
          └──── /api/audit/{id}/report.pdf ──► ReportLab ──► PDF bytes
```
