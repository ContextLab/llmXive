# Research: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

## Overview
This research plan details how we will (1) acquire and harmonize publicly available fatigue datasets, (2) construct three feature sets, (3) train and evaluate regression models, and (4) perform bootstrap mediation analysis **only when measured residual stress is present in an open dataset**. Synthetic data is generated **solely** to verify that the pipeline runs end‑to‑end; any scientific conclusions derived from synthetic data are explicitly labeled as proof‑of‑concept and are not generalized to real materials.

## Dataset Strategy
| Requirement | Verified Source | Availability | Action |
|-------------|----------------|--------------|--------|
| Fatigue life + process parameters + measured residual stress | **None** (no verified open URL contains all required fields) | Unavailable | The primary analysis will proceed with the available process‑only and material‑property variables. Mediation analysis will be **skipped** unless a future open dataset with measured stress becomes available. |
| Supplementary process‑only data | UCI CSV/Parquet URLs (e.g., `) | Contains generic numeric features, not fatigue‑related | Retained for pipeline validation only; not used in the main scientific analysis. |
| Additional open‑source fatigue data | NIST JSONL URLs (conversation datasets) | Irrelevant to fatigue | Not used. |
| Synthetic validation dataset | `data/raw/synthetic_fatigue.csv` (generated from documented empirical formulas) | Included in repo | Used **only** to confirm that ingestion, preprocessing, modeling, and mediation scripts execute without error. Results from this dataset are reported as methodological sanity checks, not as scientific findings.

> **Note**: Because no open dataset currently provides measured residual stress together with fatigue life and process parameters, the mediation analysis will be omitted. Predictive modeling will still be performed using the proxy‑derived stress (Feature C) and the process‑only features (Feature A). All reported scientific metrics will be based on real open data where available; synthetic‑data results will be clearly marked.

## Methodology

### 1. Data Ingestion & Preprocessing (FR‑001, FR‑002, FR‑003, FR‑012, FR‑010)
- **Ingestion** (`src/ingest/ingest.py`): download each open dataset, compute a SHA‑256 checksum for the raw file, store under `data/raw/`, and propagate the checksum into the `checksum` column of the unified CSV (see `data-model.md`).
- **Unit Standardization**: Convert any stress values to MPa (`1 psi = 0.00689476 MPa`).
- **Missing‑Value Imputation**: Median imputation per numeric column (FR‑002).
- **Proxy Calculation**: When `residual_stress_measured` is missing, compute `σ_res = k·heat_input·cooling_rate` (`k=0.8` for steel, `k=0.6` for aluminum), set `is_proxy = True`, store in `residual_stress_proxy`, and clamp negatives to `0.01 MPa`. Rows with `is_proxy=True` are flagged for downstream handling.
- **Contract Validation**: After preprocessing, validate the processed CSV against `contracts/dataset_schema.yaml`. Failure aborts the pipeline.

### 2. Feature Set Construction
| Feature Set | Columns |
|-------------|---------|
| **A (Process‑only)** | `heat_input`, `cooling_rate`, `other_process_params…` |
| **B (Process + Measured Stress)** | All of A **plus** `residual_stress_measured` (rows where `is_proxy=False`) |
| **C (Process + Material Props)** | All of A **plus** `material_class`, `elastic_modulus`, `yield_strength` (no stress column) |

### 3. Model Training & Evaluation (FR‑004, FR‑005, FR‑008, FR‑009, FR‑011, SC‑002, SC‑004, SC‑005)
- **Algorithms**: `RandomForestRegressor`, `GradientBoostingRegressor` (scikit‑learn), shallow feed‑forward NN (`torch.nn.Sequential` with one hidden layer ≤ 128 units, early stopping ≤ 500 epochs).
- **Hyper‑parameter Grid**: 10 combos per algorithm; grid search inside a 5‑fold CV loop (FR‑005). CV folds are stratified by `material_class`.
- **Metrics**: MAPE and R² on each fold; final model selected by lowest mean CV‑MAPE.
- **Held‑out Test Set**: Stratified by `material_class`; random seed fixed (`SEED=42`).
- **Paired t‑test** (FR‑008): Compare absolute errors of Model A vs. Model B on the **full** test set (including imputed stress). Additionally, run a **sensitivity t‑test** on the measured‑stress subset and report both results. Apply **Bonferroni correction** for the three algorithm families (α = 0.05/3).
- **Cross‑Material Transfer** (FR‑011): Train on steel, test on aluminum and vice‑versa; report ΔMAPE (SC‑004).
- **Runtime Summary** (SC‑005): Log wall‑clock time and peak memory for each stage; generate `runtime_summary.csv` and assert limits (≤ 6 h, ≤ 7 GB RAM).

### 4. Mediation Analysis (FR‑006, FR‑007, SC‑001, SC‑003)
- **Eligibility**: Performed only on rows where `is_proxy=False`. If fewer than 50 such rows exist, a warning is logged and mediation is **skipped**.
- **Covariate Adjustment**: Include all other process parameters, material properties, and any available confounders (e.g., temperature, surface_finish, loading_condition) as covariates.
- **Collinearity Diagnostic**: Compute VIF for each predictor; report any VIF > 5 and interpret results cautiously.
- **Bootstrap**: 10 000 resamples using `statsmodels.stats.mediation.Mediation`.
- **Multiple‑Comparison**: Holm‑Bonferroni correction across material classes (steel, aluminum).
- **Reporting** (FR‑007, SC‑001, SC‑003): Save `mediation_summary.csv` with indirect effect, direct effect, proportion mediated, and 95 % CI; generate accompanying figures.

### 5. Reporting
- Generate CSV tables (`results/reports/*.csv`) and Matplotlib figures (`results/reports/*.png`) for:
  - Model performance per feature set & algorithm.
  - Paired‑t‑test statistics (full set & measured‑only sensitivity).
  - Mediation effect estimates with confidence intervals (if run).
  - Cross‑material ΔMAPE.
  - Runtime summary.
- All results are traceable to a single row in `data/processed/unified_fatigue.csv` and a single script in `code/`.

## Compute Feasibility
All steps run comfortably on the GitHub Actions free‑tier runner (≈ 2.5 h total, < 7 GB RAM). No GPU resources are required.

## Statistical Rigor
- **Multiple‑Comparison**: Bonferroni for paired t‑tests; Holm‑Bonferroni for mediation across materials.
- **Power**: Minimum of 50 measured‑stress rows required for mediation; otherwise mediation is omitted with a logged warning.
- **Causal Assumptions**: Effects are treated as associational; mediation is statistical, not causal.
- **Measurement Validity**: Synthetic data is used only for pipeline validation; real‑data results are qualified accordingly.
- **Collinearity**: VIF computed for all predictors; VIF > 5 reported, and independent‑effect interpretation is limited.

## Edge Cases
- **No measured stress** → use proxy only (Feature C) and flag `proxy_dependent = True` in the final report; mediation is omitted.
- **Sample size < 50** → warning and skip mediation (`skip_mediation = True`).
- **Negative proxy values** → clamp to `0.01 MPa` and log adjustment.

--- 
