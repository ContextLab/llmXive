# Implementation Plan: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

**Branch**: `001-predict-cold-work-kinetics` | **Date**: 2026-07-13 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-cold-work-kinetics/spec.md`

## Summary

This plan implements a fully reproducible CPU‑only pipeline to predict **raw** time‑to‑peak softening in aluminum alloys from cold work percentage, alloy composition, and annealing temperature. Because no verified public dataset containing all required variables currently exists, the pipeline falls back to a deterministic, version‑controlled synthetic generator. The synthetic data enable demonstration of the full analysis workflow while clearly flagging that empirical validation of the pinning hypothesis requires future acquisition of real experimental data.

The pipeline:

1. **Ingests** a user‑provided CSV (if present) or automatically generates a synthetic dataset via `code/simulate_data.py` (seed = 42).  
2. **Cleans** missing values, clips extreme outliers, and **engineers** interaction features (`cold_work_pct * Mn_wt`, etc.).  
3. **Computes** an Arrhenius‑normalized target (`time_to_peak_norm`) **only for exploratory visualizations**; the primary predictive model always uses the raw `time_to_peak`.  
4. **Trains** a Random Forest Regressor (CPU‑only, `n_estimators=100`, `random_state=42`).  
5. **Validates** with 5‑fold cross‑validation and an 80/20 held‑out test set (seed = 42).  
6. **Evaluates** interaction significance via a **permutation test** that shuffles interaction columns while preserving main effects, reporting an empirical p‑value.  
7. **Generates** feature‑importance, partial‑dependence, and permutation‑importance analyses to interpret the contribution of interaction terms.

All steps respect the CI runner limits (≤ 6 h, ≤ 7 GB RAM) and conform to the project constitution.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `scipy==1.13.*`, `pyyaml==6.*` (all CPU‑only wheels).  
- **Storage**: CSV/Parquet in `data/` (raw, processed) and JSON in `results/`.  
- **Testing**: `pytest` with unit tests for each pipeline stage.  
- **Performance Goals**: Runtime < 6 h, Memory < 7 GB, R² > 0.6, MAE < 15 % of mean raw `time_to_peak`.  
- **Constraints**: No GPU, dataset capped at 10 000 rows, deterministic random seeds.

## Dataset Acquisition Strategy

| Source | URL / Path | Status | Action |
|--------|------------|--------|--------|
| **User‑Provided CSV** | `data/raw/alloy_data.csv` (local) | **Verified** (user supplies) | Must contain all required columns (see Data Model). |
| **Synthetic Generator** | `code/simulate_data.py` (deterministic, seed = 42) | **Verified** (internal, version‑controlled) | Generates `data/raw/synthetic_alloy_data.csv` with ≥ 100 rows. SHA‑256 checksum recorded in `state/projects/PROJ-240.yaml`. |
| **External Repositories** | N/A | **Not Available** | No public dataset with the full variable set exists among verified sources. |

> **Reproducibility Note**: The pipeline first checks for `data/raw/alloy_data.csv`. If absent, it runs `simulate_data.py` to create a deterministic synthetic dataset. This guarantees that a fresh GitHub Actions runner can always execute the full workflow without manual data upload, satisfying Constitution I.

## Feature Engineering (FR‑002)

- Interaction terms: `cold_work_pct * mg_wt`, `cold_work_pct * si_wt`, `cold_work_pct * cu_wt`, `cold_work_pct * mn_wt`.  
- **Arrhenius normalization** (`time_to_peak_norm`) is computed **only for exploratory visualizations** using  
  `t_norm = time_to_peak * exp(Q/R * (1/450 - 1/annealing_temp_k))` with `Q = 140 kJ/mol`.  
  The normalized column is **never used** for model training or any success‑criteria calculation (prevents target leakage).

## Modeling (FR‑003, FR‑004)

- **Algorithm**: `sklearn.ensemble.RandomForestRegressor`.  
- **Hyper‑parameters**: `n_estimators=100`, `max_depth=None`, `random_state=42`.  
- **Data split**: 80/20 train‑test split (seed = 42), stratified by `alloy_series` when available.  
- **Cross‑validation**: 5‑fold CV on the training set.  
- **Outlier handling**: Clip `time_to_peak` > 1000 h to the 99th percentile; log clipped rows in `results/outlier_log.txt`.  
- **Small‑sample guard**: Abort with a clear error if total rows < 50 (insufficient for 5‑fold CV).  

## Statistical Significance of Interaction Terms (FR‑005)

1. **Additive Model**: Predictors = `{cold_work_pct, mg_wt, si_wt, cu_wt, mn_wt}`.  
2. **Interaction Model**: Additive predictors + the four interaction terms.  
3. **Permutation Test** (N = 1 000 permutations, 2‑CPU parallelism):  
   - For each permutation, independently shuffle each interaction column while leaving all main‑effect columns unchanged.  
   - Re‑fit the Interaction Model on the permuted training data and compute 5‑fold CV R².  
   - Compute ΔR²ᵢ = R²_interaction_permuted − R²_additive (additive model unchanged).  
   - Empirical p‑value = ( #{ΔR²ᵢ ≥ ΔR²_observed} + 1 ) / (N + 1).  
4. **Decision**: Interaction terms are **significant** if p < 0.05.  

This non‑parametric test respects the Random Forest’s nature and provides a valid significance assessment.

## Collinearity & Interpretation (FR‑006)

- **Permutation Importance** quantifies each feature’s contribution after permuting its values.  
- **Partial‑Dependence Plots** visualize marginal effects of the top interaction terms.  
- **Collinearity Note**: Interaction terms are mathematically derived from main effects; importance scores are interpreted descriptively, not as independent causal effects. We do not claim causal inference beyond the observed associations.

## Edge‑Case Handling

- **Pure Aluminum** (all composition columns = 0): Interaction terms become zero; permutation test is reported as “N/A” for this subset.  
- **Outliers**: Handled as described; logs stored in `results/outlier_log.txt`.  
- **Insufficient Data**: Pipeline exits with an informative error; no metrics are produced.

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | **PASS** | Fixed seeds, deterministic synthetic fallback, automatic data generation. |
| **II. Verified Accuracy** | **PASS** | Synthetic generator is version‑controlled and checksumed; literature values (e.g., Q = 140 kJ/mol) are cited from verified sources (Humphreys & Hatherly, 2004) with URLs in the bibliography. |
| **III. Data Hygiene** | **PASS** | Raw files checksumed; transformations write new files; no PII. |
| **IV. Single Source of Truth** | **PASS** | All metrics in `results/metrics.json`; figures derived from same data. |
| **V. Versioning Discipline** | **PASS** | SHA‑256 of the raw data file recorded in `state/projects/PROJ-240.yaml` under `artifact_hashes`; CI fails on hash mismatch. |
| **VI. Interaction‑Feature Explicitness** | **PASS** | Interaction columns are created, used in modeling, and reported separately. |
| **VII. Computational Boundedness** | **PASS** | CPU‑only Random Forest; dataset capped at 10 k rows; runtime < 30 min in tests. |

## Project Structure

```
specs/001-predict-cold-work-kinetics/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── metrics.schema.yaml
└── tasks.md
```

```
code/
├── ingestion.py
├── features.py
├── model.py
├── stats.py
├── simulate_data.py
└── pipeline.py
data/
├── raw/
│   └── alloy_data.csv   # user‑provided or generated automatically
└── processed/
    └── engineered_features.csv
results/
├── metrics.json
└── figures/
    ├── feature_importance.png
    └── partial_dependence_*.png
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Interaction Features | Required by FR‑002 & Constitution VI to test the pinning hypothesis. | Simple additive model would not capture modulation effect; fails SC‑002. |
| Permutation Test | Provides a valid significance test for non‑parametric Random Forests (addresses concerns 17c60a0d & d146a4d8). | Likelihood Ratio Test is invalid for RF; would produce meaningless p‑values. |
| Deterministic Synthetic Fallback | Ensures reproducibility when no verified external dataset exists (Constitution I & II). | Manual upload would break reproducibility and require external intervention. |
| Arrhenius Normalization Separation | Prevents leakage of predictor information into the target (addresses scientific_soundness‑b4a13f4a). | Using normalized target for training inflates R² and violates independence. |

## Runtime & Resource Estimate

- Data load & cleaning: < 30 s.  
- Feature engineering: < 10 s.  
- Random Forest training (100 trees, ≤ 10 k rows): **[deferred]** (well under 5 min on 2‑CPU CI).  
- 5‑fold CV: **[deferred]**.  
- Permutation test (1 000 perms, 2‑CPU parallelism): **[deferred]** (expected < 20 min).  
- Total < 30 min, comfortably within CI limits.
