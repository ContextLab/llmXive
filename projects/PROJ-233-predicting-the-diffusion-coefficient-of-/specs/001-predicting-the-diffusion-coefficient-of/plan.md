# Implementation Plan: Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors

**Branch**: `001-hydrogen-diffusion-prediction` | **Date**: 2026-10-26 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-hydrogen-diffusion-prediction/spec.md`

## Summary

Build a reproducible, CPU‑only pipeline that (1) ingests hydrogen‑diffusion measurements with compositional, microstructural, and temperature descriptors, (2) trains XGBoost and Random‑Forest regressors under nested 5‑fold cross‑validation with an inner Bayesian‑optimization loop (≤ 2 h CPU budget), (3) compares them to a linear baseline on log₁₀(D), (4) quantifies pairwise interactions via SHAP interaction values (descriptive only), (5) validates interaction importance with an **independent hold‑out evaluation** that computes the **ablation ΔR² share** by refitting a depth‑1 (main‑effects‑only) model, (6) performs both a **simulation‑based a‑priori power analysis** (conditional) and a **post‑hoc power analysis** (observed effect size, minimum detectable f², CI width), (7) records all results with strict provenance, and (8) enforces resource guards (6 h / ~7 GB RAM). The plan also contains a **Scope‑Correction** section because the spec’s assumed data sources are not openly downloadable.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `xgboost==2.0.*`, `shap==0.45.*`, `optuna==3.6.*`, `statsmodels==0.14.*`, `psutil==5.9.*`, `pyyaml==6.0.*`  
- **Storage**: file‑based CSV/Parquet under `data/` (raw, processed, results)  
- **Testing**: `pytest==8.2.*`  
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU, ~7 GB RAM, no GPU)  
- **Performance Goals**: full pipeline within 6 h wall‑clock and ~7 GB RAM (FR‑006)  

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All seeds pinned (`SEED=42`); deterministic pipeline; raw data fetched/loaded from a single canonical file path and checksummed. |
| II. Verified Accuracy | No citations beyond verified sources; the unverified NIST/JMS sources are explicitly flagged, not cited. |
| III. Data Hygiene | Raw file checksummed (`data/checksums.sha256`); every transformation writes a new derived file with documented provenance; no PII. |
| IV. Single Source of Truth | Every figure/statistic traces to one row in `data/processed/*.parquet` and one code block; no hand‑typed numbers. |
| V. Versioning Discipline | All artifacts content‑hashed; project state `updated_at` maintained by the platform. |
| VI. Numerical Stability & Interaction Validation | Bayesian optimization time‑capped with graceful exit; bootstrap refits (fixed hyperparameters) yield CIs; interaction claims validated via independent hold‑out ablation ΔR² share (not solely SHAP). |
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
│   ├── ingest.py           # FR-001, FR-008: load data, compute descriptors, unit harmonization, 1/T feature, temperature collinearity check
│   ├── preprocess.py       # FR-001: k‑NN imputation (k=5, predictors only), StandardScaler (fit inside inner folds)
│   ├── train.py            # FR-002, FR-003: nested CV + Optuna, time‑budgeted, fallback grid, linear baseline
│   ├── evaluate.py         # FR-003, FR-010: metrics, external hold‑out, ablation ΔR² share
│   ├── shap_interaction.py # FR-004: SHAP interaction values (descriptive ranking)
│   ├── bootstrap.py        # FR-005, limitation note (fixed hyperparameters)
│   ├── power.py            # FR-009: a‑priori simulation power analysis + post‑hoc effect‑size & min‑detectable‑f²
│   └── guard.py            # FR-006: RAM/wall‑clock monitor, fallback sampling, graceful timeout
├── utils/
│   └── seeds.py
└── cli/
    └── run_pipeline.py

tests/
├── contract/
│   └── test_contracts.py
├── unit/
│   ├── test_ingest.py      # uses tiny fixture rows (spec US‑1 independent test)
│   ├── test_train.py
│   └── test_bootstrap.py
└── data/
    └── fixture_rows.csv    # tiny labeled test fixture — NOT used to produce results; satisfies independent tests
```

**Structure Decision**: single‑project layout (`src/` + `tests/`); a `requirements.txt` lives at the repository root (see quickstart). No frontend, packaging, or dashboard scaffolding.

## Phase Mapping (covers every FR and SC)

| Phase | Work (FR/SC covered) |
|-------|----------------------|
| **0 – Data acquisition gate & provenance** | Define the real‑input contract (`data/raw/diffusion_measurements.csv` per `contracts/dataset.schema.yaml`). Document that **no verified open source** for the NIST/JMS data exists; the pipeline **exits non‑zero** with an explicit “no verified data source” message if the file is missing. Checksum raw data (Constitution III). **FR‑001 (data side), SC‑005; scope flag recorded.** |
| **1 – Ingestion & descriptor engineering** | `ingest.py`: harmonize units to m²/s (US‑1 scenario 3); compute `mean_electronegativity`, `atomic_radius_variance` from bundled element‑property table; derive `free_volume_proxy`, `grain_boundary_density` via literature formulas independent of D (FR‑007). **Retain the raw `temperature` column for record‑keeping *and* include it as a predictor for the non‑linear models**; compute `inv_temperature = 1 / temperature` for use by all models. Perform a correlation matrix and VIF check; if any VIF > 5, log a warning (addresses concern c2aa6e4f). |
| **2 – Preprocessing** | `preprocess.py`: k‑NN imputation (k=5) on predictor columns only, StandardScaler on **all numeric predictors including raw temperature and its reciprocal** – fitted **inside each inner training fold** (FR‑001). Collinearity between temperature and its inverse is noted; the linear baseline will later drop raw temperature to avoid perfect collinearity. |
| **3 – Nested model training** | `train.py`: outer 5‑fold CV; inner Optuna TPE search (≤ 2 h, 5‑min grace exit). If time budget exceeded, log “Optimization terminated due to time budget”, record best‑so‑far hyperparameters, and fall back to default grid (`max_depth=6, learning_rate=0.1, n_estimators=200`). All preprocessing (imputation, scaling) fitted **inside inner folds only**. Train XGBoost, Random Forest, and a linear OLS baseline (using only `inv_temperature`). |
| **4 – Linear baseline & comparison** | Compute outer‑fold RMSE and R² on log₁₀(D); Holm‑adjusted pairwise comparisons among the three models (FR‑003, SC‑001). |
| **5 – SHAP interaction analysis** | `shap_interaction.py`: compute `TreeExplainer.shap_interaction_values` on the best non‑linear model; rank pairwise interactions by mean absolute magnitude (descriptive only) (FR‑004). No inference about variance contribution is drawn from SHAP alone. |
| **5b – Independent hold‑out evaluation** | Reserve a stratified **external hold‑out set** (disjoint from all CV folds). Evaluate the tuned best model to obtain `R²_full`. **Then refit a depth‑1 XGBoost model** (max_depth=1, same hyperparameters where applicable) on the **same training data** (excluding the hold‑out) to capture only main effects. Compute the **interaction‑variance share** as `(R²_full − R²_main) / R²_full`. Bootstrap this share with 1,000 resamples to obtain a 95 % CI (addresses concerns 2e1790c5 and 343e23c7). |
| **6 – Bootstrap robustness** | `bootstrap.py`: b = 1…1000 resamples; **refit the full pipeline** (imputation, scaling, model) **with the best hyperparameters fixed** for feasibility (FR‑005, SC‑002, SC‑003). Re‑compute SHAP interactions and the ΔR² ablation for top interactions on the hold‑out slice; generate 95 % percentile CIs for the top‑5 feature‑importance scores. |
| **7 – Resource guard** | `guard.py`: monitor RAM via `psutil` (threshold 6 GB → log “Memory limit approached – switching to sampled subset” and continue on a reproducible 150‑sample random subset, seed = 42). Wall‑clock abort at 5 h 55 min; if triggered, log “Time limit reached – terminating gracefully”, output best‑so‑far results, exit code 0 (FR‑006). |
| **8a – A‑priori power analysis** | `power.py`: **simulation‑based power analysis** (Monte‑Carlo) that confirms the **n ≥ 200** requirement for detecting interaction effect size *f*² ≥ 0.15 with α = 0.05 and that bootstrap 95 % CI widths for the top‑feature importance are ≤ 0.1. The analysis is explicitly labeled **conditional** on the assumed effect‑size distribution (addresses concern 9c4c3191). |
| **8b – Post‑hoc power analysis** | After data are loaded, compute observed `f² = (R²_nl − R²_lin)/(1 − R²_nl)` using `statsmodels.stats.power.FTestPower`; report **minimum detectable f²** at 0.80 power given the realized `n`; also report the observed 95 % CI width for the top‑ranked descriptor. Flag if power < 0.80 or CI > 0.1. |
| **9 – Results packaging & contracts** | Write `model_performance`, `interaction_terms`, `bootstrap_ci`, `external_validation`, `power_analysis` tables to `data/results/`; generate figures (`rmse_comparison.png`, `shap_interaction_heatmap.png`, `bootstrap_feature_importance_violin.png`, `external_validation_plot.png`, `power_analysis_plot.png`); validate all outputs against `contracts/`; produce a summary report mapping each SC to its measurement. |

## Timeline (≈ 12 substantive tasks)

1. Data acquisition gate: input contract, refusal‑on‑missing‑real‑data, checksumming, provenance docs (Phase 0).  
2. Ingestion: unit harmonization, descriptor computation, proxy derivation, **1/T feature**, temperature collinearity check (Phase 1).  
3. Preprocessing: fold‑internal k‑NN imputation and scaling (Phase 2).  
4. Nested CV training with Optuna, time budget, grid fallback (Phase 3).  
5. Linear baseline and Holm‑adjusted comparison (Phase 4).  
6. SHAP interaction extraction and ranking (Phase 5).  
7. Independent hold‑out evaluation with depth‑1 ablation ΔR² share and bootstrap CI (Phase 5b).  
8. Bootstrap refit loop with fixed hyperparameters (Phase 6).  
9. Resource guard with sampling fallback and graceful timeout (Phase 7).  
10. **A‑priori simulation power analysis** + post‑hoc effect‑size & min‑detectable‑f² reporting (Phases 8a & 8b).  
11. Contract schemas and validation tests (Phase 9).  
12. Figures, summary report, quickstart (Phase 9).

## Scope Correction Updated

The spec references the NIST Standard Reference Database and the *Journal of Materials Science* as data sources, but **no verified open, programmatically downloadable dataset** containing hydrogen diffusion coefficients together with composition, processing history, and temperature exists. To proceed, the pipeline adopts a **documented manual‑entry process**:

1. **Template provision** – a CSV template `data/raw/hydrogen_diffusion_template.csv` (included in the repository) lists the required columns (`sample_id`, `composition`, `composition_fractions` (optional), `processing_params` (JSON‑encoded), `temperature`, `diffusion_coefficient`). Example rows and a brief guide are provided in the file header.

2. **Manual data entry** – researchers must populate the template by extracting data from the literature (e.g., individual journal articles, conference proceedings). For each row, a **provenance manifest** must be added as a comment line in the CSV (starting with `#`) indicating the source reference (DOI, URL, or citation) for that sample.

3. **Placement** – the completed file must be saved as `data/raw/diffusion_measurements.csv`. The ingestion pipeline validates the file against `contracts/dataset.schema.yaml`, checks the SHA‑256 checksum recorded in `data/checksums.sha256`, and aborts with an explicit error if the file is missing or malformed.

4. **Future open data** – if an openly downloadable dataset satisfying FR‑001 becomes available, its URL can be added to the configuration (`config/open_dataset_url`) and the pipeline will automatically download and use it, bypassing the manual‑entry requirement.

This concrete manual‑entry procedure satisfies FR‑001 while respecting the Constitution’s data‑hygiene and reproducibility principles. Until a verified open dataset is provided, the pipeline will **not fabricate data** and will exit gracefully with a clear message.

## Edge Cases

- **Dataset Variable Mismatch**: If the manually entered file lacks specific microstructural parameters (e.g., `free_volume_proxy`) for a significant portion of entries, the pipeline relies on the literature‑derived proxy formulas (independent of D) to fill those fields; rows with missing required fields trigger a warning and are excluded from model training if the missingness exceeds 5 % for that column (maintains the ≥ 95 % non‑null requirement).  
- **Computational Out‑of‑Memory**: If the full dataset + bootstrapping exceeds available memory, the guard switches to a reproducible 150‑sample subset (seed = 42) and logs the limitation.  
- **Convergence Failure**: If Bayesian optimization fails to converge within the 2‑hour limit, the search loop terminates early, logs “Optimization terminated due to time budget”, records the best‑so‑far hyperparameters, and falls back to the default grid (max_depth = 6, learning_rate = 0.1, n_estimators = 200).

## Expected Deliverables

- Tables (produced only once real data is supplied): `model_performance.parquet`, `interaction_terms.parquet`, `bootstrap_ci.parquet`, `external_validation.parquet`, `power_analysis.parquet`.  
- Figures: `rmse_comparison.png`, `shap_interaction_heatmap.png`, `bootstrap_feature_importance_violin.png`, `external_validation_plot.png`, `power_analysis_plot.png`.  
- Summary report mapping each SC to its concrete measurement, plus the explicit data‑availability limitation statement.  
