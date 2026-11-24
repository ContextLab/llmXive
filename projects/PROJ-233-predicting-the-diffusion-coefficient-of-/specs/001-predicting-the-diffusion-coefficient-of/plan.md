# Implementation Plan: Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors

**Branch**: `001-hydrogen-diffusion-prediction` | **Date**: 2026-10-26 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-hydrogen-diffusion-prediction/spec.md`

## Summary

Build a reproducible, CPU‑only pipeline that (1) ingests hydrogen‑diffusion measurements with compositional, microstructural, and temperature descriptors, (2) trains XGBoost and Random‑Forest regressors under nested 5‑fold cross‑validation with an inner Bayesian‑optimization loop (≤ 2 h CPU budget), (3) compares them to a linear baseline on log₁₀(D), (4) quantifies pairwise interactions via permutation‑based SHAP interaction analysis (descriptive only), (5) validates interaction importance with an independent hold‑out evaluation that computes the **ablation ΔR² share** using permutation of interaction pairs, (6) performs both a simulation‑based a‑priori power analysis and a post‑hoc interaction‑specific power analysis, (7) records all results with strict provenance, and (8) enforces resource guards (6 GB RAM, 6 h wall‑clock). The plan also contains a **Scope‑Correction** section because the spec’s assumed data sources are not openly downloadable.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `xgboost==2.0.*`, `shap==0.45.*`, `optuna==3.6.*`, `statsmodels==0.14.*`, `psutil==5.9.*`, `pyyaml==6.0.*`, `joblib==1.4.*`  
- **Storage**: file‑based CSV/Parquet under `data/` (raw, processed, results)  
- **Testing**: `pytest==8.2.*`  
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU, ~7 GB RAM, no GPU)  
- **Performance Goals**: full pipeline within 6 h wall‑clock and ~7 GB RAM  

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All seeds pinned (`SEED=42`); deterministic pipeline; raw data fetched/loaded from a single canonical file path and checksummed. |
| II. Verified Accuracy | No citations beyond verified sources; the unverified NIST/JMS sources are explicitly flagged, not cited. |
| III. Data Hygiene | Raw file checksummed (`data/checksums.sha256`); every transformation writes a new derived file with documented provenance; no PII. |
| IV. Single Source of Truth | Every figure/statistic traces to one row in `data/processed/*.parquet` and one code block; the project state YAML `state/projects/PROJ-233-predicting-the-diffusion-coefficient-of-.yaml` is the SSoT. |
| V. Versioning Discipline | All artifacts content‑hashed; project state `updated_at` maintained by the platform. |
| VI. Numerical Stability & Interaction Validation | Bayesian optimization time‑capped with graceful exit; bootstrap refits (fixed hyperparameters) yield CIs; interaction claims validated via permutation‑based ΔR² share (not solely SHAP). |
| VII. Independent Validation & Descriptor Provenance | Target `log10_D` never used as predictor or in imputation/scaling; k‑NN imputation (k=5) fit on predictor columns only; proxy formulas documented as independent of diffusion measurements. |

## Project Structure

```text
specs/001-hydrogen-diffusion-prediction/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── model_performance.schema.yaml
│   └── power_analysis.schema.yaml
└── tasks.md

src/
├── pipeline/
│   ├── ingest.py
│   ├── preprocess.py
│   ├── train.py
│   ├── evaluate.py
│   ├── shap_interaction.py
│   ├── bootstrap.py
│   ├── power.py
│   └── guard.py
├── utils/
│   └── seeds.py
└── cli/
    └── run_pipeline.py

tests/
├── contract/
│   └── test_contracts.py
├── unit/
│   ├── test_ingest.py
│   ├── test_train.py
│   └── test_bootstrap.py
└── data/
    └── fixture_rows.csv
```

**Structure Decision**: single‑project layout (`src/` + `tests/`) with a root‑level `requirements.txt`. No frontend, packaging, or dashboard scaffolding.

## Phase Mapping (covers every FR and SC)

| Phase | Work (FR/SC covered) |
|-------|----------------------|
| **0 – Data acquisition gate & provenance** | Define the real‑input contract (`data/raw/diffusion_measurements.csv`). Verify presence and SHA‑256 checksum; abort with clear error if missing. **FR‑001, SC‑005** |
| **1 – Ingestion & descriptor engineering** | Harmonize units, compute compositional descriptors, derive microstructural proxies, create `inv_temperature` (1/K) **for the linear baseline only**, retain raw `temperature` as predictor for XGBoost/RF. **FR‑001, FR‑007, FR‑008** |
| **2 – Preprocessing** | k‑NN imputation (k=5) on predictor columns only; StandardScaler on all numeric predictors (fit inside inner folds). **FR‑001** |
| **3 – Nested model training** | Outer 5‑fold CV; inner Optuna TPE search (≤ 2 h). Graceful fallback to default grid if time budget exceeded. **FR‑002, FR‑003** |
| **4 – Linear baseline & comparison** | Compute outer‑fold RMSE & R² on log₁₀(D) using only `inv_temperature` as temperature predictor; Holm‑adjusted pairwise comparisons among XGBoost, RF, and linear. **FR‑003, SC‑001** |
| **5 – SHAP interaction analysis** | Compute `TreeExplainer.shap_interaction_values` on the best non‑linear model; rank interactions by mean absolute magnitude (descriptive). **FR‑004** |
| **5b – Independent hold‑out evaluation** | Because no verified DOE hold‑out exists, reserve **[deferred]** of the manually supplied dataset as an internal stratified hold‑out (seed = 42). Evaluate the tuned full model on this set, then **for each descriptor pair** permute the two columns jointly (leaving all else unchanged), recompute R², and calculate ΔR². Aggregate over all pairs to obtain the **interaction‑variance share** = ΣΔR² / (R²_full − R²_linear). Compute 95 % CI via 1,000 bootstrap resamples of the hold‑out. **FR‑010, SC‑006** |
| **6 – Bootstrap robustness** | 1,000 resamples; refit full pipeline (imputation, scaling, model) **with fixed best hyperparameters**; recompute SHAP interactions and ΔR² for top interactions; generate 95 % CIs for top‑5 feature importances. Parallelised with `joblib.Parallel(n_jobs=2)` to stay within CPU limits. **FR‑005, SC‑002, SC‑003** |
| **7 – Resource guard** | Monitor RAM via `psutil` (threshold 6 GB → switch to reproducible 150‑sample subset, seed = 42). Wall‑clock abort at 5 h 55 min; log graceful termination, record best‑so‑far results, exit code 0. |
| **8a – A‑priori power analysis** | Monte‑Carlo simulation confirming n ≥ 200 yields ≥ 0.80 power for detecting interaction effect size *f*² ≥ 0.15 (α = 0.05) and bootstrap CI widths ≤ 0.1. **FR‑009** |
| **8b – Post‑hoc interaction‑specific power analysis** | Compute interaction‑specific effect size `f²_interaction = (ΔR²_interaction_share) / (1 − ΔR²_interaction_share)`. Using `statsmodels.stats.power.FTestPower`, report observed power for detecting that effect at α = 0.05 and the 95 % CI width for the top descriptor. **FR‑009** |
| **9 – Results packaging & contracts** | Write all tables to `data/results/`; generate figures; validate against `contracts/`; produce summary mapping each SC to its measurement. |

## Timeline (≈ 12 substantive tasks)

1. Data acquisition gate & checksum.  
2. Ingestion & descriptor creation (including `inv_temperature` for linear baseline).  
3. Preprocessing (k‑NN, scaling).  
4. Nested CV with Bayesian optimization & fallback.  
5. Linear baseline & Holm‑adjusted comparison.  
6. SHAP interaction extraction.  
7. Independent hold‑out permutation‑based interaction variance share & bootstrap CI.  
8. Full‑pipeline bootstrap refits (fixed hyperparameters, parallelised).  
9. Resource guard (RAM & wall‑clock).  
10. A‑priori simulation power analysis.  
11. Post‑hoc interaction‑specific power analysis.  
12. Contracts, figures, summary report, quickstart.

## Scope Correction Updated

The spec references the NIST Standard Reference Database and the *Journal of Materials Science* as data sources, but **no verified open, programmatically downloadable dataset** containing the required columns exists. To proceed, the pipeline adopts a **manual‑entry process**:

1. **Template** – `data/raw/hydrogen_diffusion_template.csv` lists required columns with example rows and a header comment explaining the format.  
2. **Manual entry** – researchers populate the template from literature, adding a comment line (`# Source: DOI:…`) above each row to record provenance.  
3. Save the completed file as `data/raw/diffusion_measurements.csv`. The ingestion pipeline validates it against `contracts/dataset.schema.yaml`, checks the SHA‑256 checksum (recorded in `data/checksums.sha256`), and aborts with a clear error if missing or malformed.  
4. **Future open data** – if an openly downloadable dataset later becomes available, its URL can be added to `config/open_dataset_url` and the pipeline will automatically download it, bypassing manual entry.

This satisfies FR‑001 while respecting the Constitution’s data‑hygiene and reproducibility principles. No synthetic data are fabricated.

## Edge Cases

- **Dataset Variable Mismatch** – If `free_volume_proxy` or other microstructural fields are missing for >5 % of rows, the pipeline fills them using literature‑derived proxy formulas (independent of D) and logs a warning; rows exceeding the missingness threshold are excluded.  
- **Out‑of‑Memory** – Guard switches to a reproducible 150‑sample subset (seed = 42) and logs the limitation.  
- **Optimization Convergence Failure** – Early termination logs “Optimization terminated due to time budget”, records best‑so‑far hyperparameters, and falls back to the default grid (`max_depth=6, learning_rate=0.1, n_estimators=200`).  

## Expected Deliverables

- Tables: `model_performance.parquet`, `interaction_terms.parquet`, `bootstrap_ci.parquet`, `external_validation.parquet`, `power_analysis.parquet`.  
- Figures: `rmse_comparison.png`, `shap_interaction_heatmap.png`, `bootstrap_feature_importance_violin.png`, `external_validation_plot.png`, `power_analysis_plot.png`.  
- Summary report mapping each SC to its concrete measurement and stating the data‑availability limitation.
