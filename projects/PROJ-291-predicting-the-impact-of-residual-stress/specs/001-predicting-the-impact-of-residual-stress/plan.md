# Implementation Plan: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

**Branch**: `001-predict-residual-stress-fatigue` | **Date**: 2026-10-10 | **Spec**: [spec.md](../specs/001-predict-residual-stress-fatigue/spec.md)  
**Input**: Feature specification from `/specs/001-predict-residual-stress-fatigue/spec.md`

## Summary
The project will (1) ingest publicly available fatigue datasets, (2) construct three feature sets (process‑only, process + measured stress, process + material properties), (3) train baseline and stress‑mediated regression models, (4) evaluate predictive gains, and (5) perform bootstrap mediation analysis **only when measured residual stress is present in an open dataset**. Synthetic data is generated **solely** for pipeline validation; it is never used for scientific inference.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `torch==2.3.*` (CPU‑only), `statsmodels==0.14.*`, `datasets==2.20.*`, `pyyaml==6.0.*`, `pytest==8.2.*`
- **Storage**: File‑based CSV/Parquet under `data/` (raw) and `data/processed/` (derived)
- **Testing**: `pytest` with contract validation (see `contracts/`)
- **Target Platform**: Linux (Ubuntu‑latest) GitHub Actions runner
- **Compute Feasibility**: All steps are CPU‑friendly and expected to run within the free‑tier limits (≈ 2.5 h, < 7 GB RAM, < 14 GB disk). No GPU resources are required.

## Constitution Check
| Principle | Mapping to FR/SC |
|-----------|------------------|
| I. Reproducibility | Fixed seeds (FR‑010); deterministic scripts; data fetched from canonical URLs |
| II. Verified Accuracy | No new external citations beyond verified dataset URLs |
| III. Data Hygiene | Raw files immutable; checksum recorded during ingestion (FR‑001, FR‑010) |
| IV. Single Source of Truth | All figures/tables generated from files under `results/` |
| V. Versioning Discipline | Content hashes drive state updates (FR‑010) |
| VI. Residual‑Stress Proxy Integrity | Proxy calculation & flagging (FR‑003, FR‑012) |
| VII. Cross‑Material Mediation Validation | Stratified analysis (FR‑009); improvement thresholds (SC‑002, SC‑004) |

## Detailed Phases

### 1. Data Ingestion & Preprocessing (FR‑001, FR‑002, FR‑003, FR‑012, FR‑010)
- **Ingestion** (`src/ingest/ingest.py`): programmatically download each open dataset, compute a SHA‑256 checksum for every raw file, store under `data/raw/`, and **write the checksum into a new `checksum` column** of the unified CSV (see `data-model.md`). Checksums are also recorded in the project state file.
- **Checksum Propagation**: the per‑row checksum is carried forward unchanged through all downstream transformations.
- **Unit Standardization**: Convert any stress values to MPa (`1 psi = 0.00689476 MPa`).
- **Missing‑Value Imputation**: Median imputation per numeric column (FR‑002).
- **Proxy Calculation** (FR‑003): When `residual_stress_measured` is missing, compute `σ_res = k·heat_input·cooling_rate` (`k=0.8` for steel, `k=0.6` for aluminum), set `is_proxy = True`, store in `residual_stress_proxy`, and **clamp negative results to 0.01 MPa**. Rows with `is_proxy=True` are flagged for downstream handling.
- **Contract Validation**: After preprocessing, validate the processed CSV against `contracts/dataset_schema.yaml` using `jsonschema`. Failure aborts the pipeline (addresses plan_consistency‑8a8a09a4).

### 2. Feature Set Construction
| Feature Set | Columns |
|-------------|---------|
| **A (Process‑only)** | `heat_input`, `cooling_rate`, `other_process_params…` |
| **B (Process + Measured Stress)** | All of A **plus** `residual_stress_measured` (rows where `is_proxy=False`) |
| **C (Process + Material Props)** | All of A **plus** `material_class`, `elastic_modulus`, `yield_strength` (no stress column) |

### 3. Model Training & Evaluation (FR‑004, FR‑005, FR‑008, FR‑009, FR‑011, SC‑002, SC‑004, SC‑005)
- **Algorithms**: `RandomForestRegressor`, `GradientBoostingRegressor` (scikit‑learn), shallow feed‑forward NN (`torch.nn.Sequential` with one hidden layer ≤ 128 units, early stopping ≤ 500 epochs).
- **Hyper‑parameter Grid**: 10 combos per algorithm; grid search performed inside a **5‑fold CV** loop (FR‑005). CV folds are stratified by `material_class`.
- **Metrics**: MAPE and R² on each fold; final model selected by lowest mean CV‑MAPE.
- **Held‑out Test Set**: Stratified by `material_class`; random seed fixed (`SEED=42`) (FR‑010).  
- **Paired t‑test** (FR‑008): Compare absolute errors of Model A vs. Model B on the **full** test set (including imputed stress). Additionally, run a **sensitivity t‑test** on the measured‑stress subset and report both results. Apply **Bonferroni correction** for the three algorithm families (α = 0.05/3).  
- **Cross‑Material Transfer** (FR‑011): Train on steel, test on aluminum and vice‑versa; report ΔMAPE (SC‑004).  
- **Runtime Summary** (SC‑005): Log wall‑clock time and peak memory for each stage; at pipeline end generate `runtime_summary.csv` and assert limits (≤ 6 h, ≤ 7 GB RAM).

### 4. Mediation Analysis (FR‑006, FR‑007, SC‑001, SC‑003)
- **Eligibility**: Performed **only** on rows where `is_proxy=False`. If fewer than 50 such rows exist, emit a warning and **skip mediation** (edge‑case handling).  
- **Covariate Adjustment**: Include all other process parameters, material properties, and any available confounders (e.g., temperature, surface_finish, loading_condition) as covariates in the mediation model.  
- **Collinearity Diagnostic**: Compute VIF for each predictor; if any VIF > 5, report the issue and interpret mediation results with caution (supplementing the earlier VIF check).  
- **Bootstrap**: 10 000 resamples using `statsmodels.stats.mediation.Mediation` with the specified covariates.  
- **Multiple‑Comparison**: Apply **Holm‑Bonferroni** correction across material classes (steel, aluminum).  
- **Reporting** (FR‑007, SC‑001, SC‑003): Save `mediation_summary.csv` containing indirect effect, direct effect, proportion mediated, and 95 % CI; generate accompanying figures.

### 5. Reporting
- CSV tables (`results/reports/*.csv`) and Matplotlib figures (`results/reports/*.png`) for:
  - Model performance per feature set & algorithm.
  - Paired‑t‑test statistics (full set & measured‑only sensitivity).
  - Mediation effect estimates with confidence intervals (if run).
  - Cross‑material ΔMAPE.
  - Runtime summary.

### 6. Edge‑Case Handling (per spec)
- **No measured stress** → use proxy only (Feature C) and set `proxy_dependent = True` in the final report; mediation is omitted.
- **Sample size < 50** → warning and skip mediation (`skip_mediation = True`).
- **Negative proxy values** → clamp to `0.01 MPa` and log adjustment.
