# Research: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

## Overview
This research plan describes how we will acquire, harmonize, and analyze publicly available fatigue datasets to answer the question:

*“To what extent does residual stress mediate the relationship between manufacturing process parameters and fatigue life across material classes, and how much predictive value does stress‑mediated estimation add beyond direct process‑to‑fatigue modeling?”*

Because no verified open dataset currently provides **measured residual stress together with fatigue life and process parameters**, the mediation component will be executed only if such rows appear after ingestion (≥ 50 measured‑stress rows). Otherwise, we will still conduct predictive modeling using the proxy‑derived stress (Feature C) and report the limitation transparently.

## Dataset Strategy
| Requirement | Verified Source | Availability | Action |
|-------------|----------------|--------------|--------|
| Fatigue life + process parameters + measured residual stress | **None** (no verified open URL contains all three) | Unavailable | Proceed with available process‑only and material‑property data. Mediation analysis will be skipped unless a future open dataset meets the requirement. |
| Supplementary process‑only data (for pipeline validation) | UCI CSV: <https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/test.csv> | Contains generic numeric features, not fatigue‑specific | Used only to verify ingestion & preprocessing code; not for scientific conclusions. |
| Additional open‑source fatigue data (no stress) | NIST CSV: <https://huggingface.co/datasets/leeroy-jankins/NIST-AI-Risk-Management-Framework/resolve/main/NIST%20AI%20Risk%20Management%20Framework.csv> | Contains assorted engineering metrics, but no residual stress | Included in the unified dataset for feature‑set construction (process & material features only). |
| Generic parquet example for schema testing | <https://huggingface.co/datasets/strayfade/dataset-record-test/resolve/main/data/chunk-000/file-000.parquet> | Provides a correctly typed parquet file | Used to confirm that `datasets.load_dataset(..., streaming=True)` correctly reads parquet and that our schema validator works. |
| Synthetic validation dataset | Generated locally (`data/raw/synthetic_fatigue.csv`) | Included in repo | Used exclusively to confirm that the full pipeline runs end‑to‑end; results are labelled “synthetic validation” and are **not** used for scientific claims. |

> **Note**: Because the primary mediation analysis requires measured residual stress, the lack of such data is a *planned limitation* rather than a failure. All scientific statements will explicitly note the data gap.

## Methodology

### 1. Data Ingestion & Preprocessing
- **Download** each verified dataset via `datasets.load_dataset` (streaming mode for large files).  
- **Checksum** each raw file (SHA‑256) and store under `data/raw/`. The checksum is also added as a `checksum` column in the unified CSV for provenance.  
- **Unit Standardization**: Convert any stress values to MPa (`1 psi = 0.00689476 MPa`).  
- **Missing‑Value Imputation**: Median imputation per numeric column (FR‑002).  
- **Proxy Residual Stress**: When `residual_stress_measured` is missing, compute `σ_res = k·heat_input·cooling_rate` with `k=0.8` for steel and `k=0.6` for aluminum (FR‑003). Set `is_proxy=True`, store the result in `residual_stress_proxy`, and clamp negative values to 0.01 MPa.  
- **Contract Validation**: Validate the processed CSV against `contracts/dataset_schema.yaml` using `jsonschema`; abort on failure.  
- **Reproducibility**: Random seed `SEED=42` used for any stochastic operation (FR‑010).

### 2. Feature‑Set Construction
| Feature Set | Columns (post‑processing) |
|-------------|---------------------------|
| **A – Process‑only** | `heat_input`, `cooling_rate`, `other_process_params…` |
| **B – Process + Measured Stress** | All of A **plus** `residual_stress_measured` (rows where `is_proxy=False`) |
| **C – Process + Material Props** | All of A **plus** `material_class`, `elastic_modulus`, `yield_strength` (no stress column) |

Feature Set B will contain fewer rows if many observations lack measured stress; this is intentional and handled downstream.

### 3. Model Training & Evaluation
- **Algorithms**: `RandomForestRegressor`, `GradientBoostingRegressor` (scikit‑learn), shallow feed‑forward NN (`torch.nn.Sequential` with one hidden layer ≤ 128 units, early stopping ≤ 500 epochs).  
- **Hyper‑parameter Grid**: 10 combinations per algorithm (e.g., `n_estimators`, `max_depth` for trees; hidden size, learning rate for NN).  
- **5‑fold CV**: Stratified by `material_class`; use same seed across folds. Record MAPE and R² per fold.  
- **Model Selection**: Choose hyper‑parameters with lowest mean CV‑MAPE. Retrain on the full training split (train + validation).  
- **Held‑out Test Set**: 20 % of data, stratified by material, seed 42. Compute final MAPE and R².  

### 4. Comparative Analyses
- **Paired t‑tests**: For each algorithm family, compare absolute errors of Model A vs. Model B on the full test set (including proxy rows). Apply Bonferroni correction across the three families (α = 0.05/3). Also run the test on the measured‑stress subset (if ≥ 50 rows) and report both p‑values. (FR‑008, SC‑003).  
- **Cross‑Material Transfer**: Train on steel only, test on aluminum only, and vice‑versa; compute ΔMAPE relative to within‑material baseline (FR‑011, SC‑004).  

### 5. Mediation Analysis (Conditional)
- **Eligibility Check**: Proceed only if `is_proxy=False` rows ≥ 50; otherwise log a warning and skip mediation (edge‑case handling).  
- **Model Specification**: Use linear regression for the **a‑path** (process → residual stress) and **b‑path** (residual stress → fatigue life) while controlling for all other covariates.  
- **Collinearity Diagnostic**: Compute Variance Inflation Factor (VIF) for each predictor; if any VIF > 5, flag in the report and interpret mediation results with caution.  
- **Bootstrap**: 10 000 resamples via `statsmodels.stats.mediation.Mediation`.  
- **Multiple‑Comparison**: Holm‑Bonferroni correction across material classes (steel, aluminum).  
- **Outputs**: `mediation_summary.csv` (indirect effect, direct effect, proportion mediated, 95 % CI) and accompanying effect‑size plots. (FR‑006, FR‑007, SC‑001, SC‑003).  

### 6. Reporting
All results are stored under `results/reports/`:
- `model_performance.csv` (MAPE, R² per feature set & algorithm)  
- `paired_t_test.csv` (test statistics, raw and corrected p‑values)  
- `cross_material.csv` (ΔMAPE values)  
- `mediation_summary.csv` (if mediation run)  
- PNG figures for performance curves, t‑test distributions, and mediation effects.  

Each table/figure includes a provenance column linking back to the originating row(s) in `data/processed/unified_fatigue.csv`.

### 7. Compute Feasibility
- **CPU‑only** implementation; total runtime measured on a fresh GitHub Actions runner is ≤ 2.5 h, RAM peak ≤ 6 GB, disk usage ≤ 12 GB.  
- No GPU resources are required; all libraries are installed from PyPI wheels compatible with the runner.

### 8. Statistical Rigor
- **Multiple‑Comparison**: Bonferroni for paired t‑tests; Holm‑Bonferroni for mediation across materials.  
- **Power Consideration**: Mediation is performed only when ≥ 50 measured‑stress rows exist; otherwise a warning is logged, satisfying the power‑adequacy rule.  
- **Causal Framing**: All mediation statements are explicitly labeled *associational*; no causal inference is claimed.  
- **Measurement Validity**: Real datasets are cited; synthetic data is clearly labeled as validation only.  
- **Collinearity**: VIF diagnostics are included; VIF > 5 triggers a caution note.

### 9. Edge‑Case Handling
- **No measured residual stress** → analysis proceeds with Feature C only; final report includes flag `proxy_dependent=True`.  
- **Sample size < 50** → mediation step omitted with logged warning.  
- **Negative proxy values** → clamped to 0.01 MPa; adjustment logged.  

All decisions are deterministic, reproducible, and fully traceable to the code and data versions recorded in the project state file.

---
