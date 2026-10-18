# Implementation Plan: Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors

**Branch**: `001-hydrogen-diffusion-prediction` | **Date**: 2026-10-18 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-hydrogen-diffusion-prediction/spec.md`

## Summary
The project must build a reproducible pipeline that (1) ingests hydrogen‑diffusion measurements together with compositional and processing descriptors, (2) trains XGBoost and Random‑Forest regressors with nested cross‑validation and Bayesian hyper‑parameter search, (3) compares them to a linear baseline, (4) quantifies pairwise descriptor interactions with SHAP, (5) validates interaction importance via multiple bootstrap refits, (6) **adds an independent external validation using a separately generated synthetic test set** to substantiate the constitutional claim about variance explained, and (7) **performs a formal post‑hoc power analysis** to assess the ability of the sample size to detect interaction effects.

**Crucial Note on Scope**: A synthetic benchmark dataset is generated because no verified open‑source diffusion dataset with the required descriptors is available. The pipeline is ready to consume a real dataset when it becomes available.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `xgboost==2.0.*`, `shap==0.45.*`, `optuna==3.6.*`, `datasets==2.19.*`, `mlflow==2.14.*`
- **Storage**: File‑based CSV/Parquet in `data/` (raw, derived, and results)  
- **Testing**: `pytest==8.2.*` (unit & contract tests)  
- **Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ~7 GB RAM)  
- **Constraints**: CPU‑first; no GPU required. All heavy loops are bounded by explicit time/iteration caps.  
- **Scale/Scope**: Pipeline benchmark using a synthetic dataset of 200 rows (seeded `SEED=42`). An additional external synthetic test set (seeded `SEED=999`) of 80 rows is generated for out‑of‑sample validation.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts are deterministic; external datasets are fetched via canonical URLs. Random seeds are pinned (`SEED=42` for training data, `SEED=999` for external test). |
| II. Verified Accuracy | No external citations are introduced beyond verified sources. |
| III. Data Hygiene | Raw files are checksummed; every transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | Every figure/table references a single row in `data/processed/*.parquet` and a single entry in the experiment log. |
| V. Versioning Discipline | All artifacts are content‑hashed; `state/projects/PROJ-233-...yaml` is updated on change. |
| VI. Numerical Stability & Interaction Validation | Bayesian optimization is time‑capped; 1,000 bootstraps provide CIs. External validation assesses whether >70 % variance claim holds on unseen data. |
| VII. Independent Validation & Descriptor Provenance | Descriptor calculations and proxies use literature formulas independent of the diffusion target. k‑NN imputation is trained only on predictor columns. |

## Project Structure
```text
specs/001-hydrogen-diffusion-prediction/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── model_performance.schema.yaml
└── tasks.md
```

```text
src/
├── pipeline/
│   ├── ingest.py          # FR‑001, FR‑008
│   ├── preprocess.py      # scaling, k‑NN imputation
│   ├── train.py           # FR‑002, FR‑003, FR‑008
│   ├── evaluate.py        # performance metrics
│   ├── shap_interaction.py# FR‑004
│   └── bootstrap.py       # FR‑005
├── utils/
│   ├── logger.py
│   └── seeds.py
└── cli/
    └── run_pipeline.py    # entry point
tests/
├── contract/
│   └── test_contracts.py
└── unit/
    ├── test_ingest.py
    ├── test_train.py
    └── test_bootstrap.py
```

## Phase Mapping (covers all FR & SC)

| Phase | Tasks (linked to FR/SC) |
|-------|--------------------------|
| **0 – Dataset Strategy & Verification** | Verify NIST URL. Since variables are missing, generate a non‑trivial synthetic benchmark dataset matching the schema (FR‑001, SC‑005). Also generate a separate synthetic external test set (different seed) for validation. |
| **1 – Data Ingestion & Descriptor Engineering** | Implement `ingest.py` to load raw/synthetic data; fetch compositional properties; compute `mean_electronegativity`, `atomic_radius_variance`; derive `free_volume_proxy` & `grain_boundary_density`; **ensure `temperature` is retained as a primary predictor (FR‑001, FR‑008, SC‑005)**. Apply k‑NN imputation (k=5) on predictor columns only; StandardScaler on all numeric features. |
| **2 – Nested Model Training** | `train.py` runs outer k‑fold CV; inside each outer training fold, an Optuna Bayesian search (max 2 h) tunes XGBoost and RF; **train models on `log10_D` target using the full descriptor set including `temperature` (FR‑002, FR‑008)**. Fit imputer & scaler inside inner folds only. |
| **3 – Baseline Linear Model & Comparison** | Train ordinary least‑squares on the same inner‑fold pipelines; compute RMSE & R² on log‑scale for each outer test fold; aggregate to produce `ModelPerformance` records (FR‑003, SC‑001). |
| **4 – SHAP Interaction Analysis** | After selecting the best non‑linear model, compute SHAP interaction values (`shap.TreeExplainer`) and produce a ranked interaction table (FR‑004). |
| **4b – External Validation** | Evaluate the best‑performing non‑linear model (with tuned hyper‑parameters) on the **separate synthetic external test set** (80 samples). Record RMSE, R², and variance explained. Compare the variance explained to the constitutional >70 % target, and log whether the claim is met (addresses concern methodology‑97e5e7c6). |
| **5 – Bootstrap Robustness Validation** | `bootstrap.py` performs 1,000 resamples. For each: (a) refit the full nested pipeline **using the best fixed hyper‑parameters** (to ensure CI feasibility); (b) **re‑calculate SHAP interaction values on the bootstrap model**; (c) perform ablation on a held‑out slice of the bootstrap sample to calculate ΔR². Compute 95 % CIs for top‑5 importances (FR‑005, SC‑002, SC‑003). |
| **6 – Resource‑Guard & Fallback Logic** | Wrap pipeline in a monitor tracking RAM (via `psutil`) and wall‑clock time. If RAM > 6 GB → switch to 150‑sample subset; if time > 5 h 55 m → abort optimization/bootstraps, log best‑so‑far, exit with code 0 (FR‑006, SC‑004). |
| **7 – Results Packaging** | Write `ModelPerformance`, `InteractionTerm`, and `BootstrapResult` tables to `data/results/` as Parquet; generate summary figures (RMSE, SHAP heatmap, CI violin plots). |
| **8 – Power Analysis** *(new phase)* | After the full nested‑CV run, compute the effect size (Cohen’s f²) for the interaction terms using the variance explained by the best non‑linear model versus the linear baseline. Run a post‑hoc power analysis (e.g., `statsmodels.stats.power.FTestPower`) with α = 0.05, the observed effect size, and the sample size (N ≈ 200). Record achieved power and, if power < 0.8, flag the limitation in the final report. This directly satisfies concern methodology‑acb4dfc8. |
| **9 – Documentation & Contract Validation** | Validate all result files against the YAML contracts in `contracts/`; generate summary report. |

## Timeline (≈ 8 – 15 substantive tasks)
1. Generate non‑trivial synthetic benchmark dataset (training) and external synthetic test set.  
2. Implement ingestion & descriptor calculations (including temperature).  
3. Write preprocessing utilities (imputation, scaling).  
4. Build nested CV training loop with Optuna.  
5. Add linear baseline pipeline.  
6. Integrate SHAP interaction extraction.  
7. Implement external validation evaluation on the separate test set and explicit >70 % variance check.  
8. Implement bootstrap refit loop (fixed‑params, re‑calculated interactions).  
9. Add resource‑guard wrapper.  
10. **Add Power Analysis step** to compute effect size, perform post‑hoc power calculation, and record results.  
11. Write contract schemas & validation tests.  
12. Produce figures & summary report.  
13. Assemble quick‑start script & README.  

## Power Analysis Note (addressing methodology‑acb4dfc8)
A post‑hoc power analysis will be performed after the synthetic data generation step. Using the observed effect size (Cohen’s f²) from the full‑dataset nested‑CV results, we will compute the achieved statistical power for detecting interaction effects at α = 0.05. The analysis will be reported in the final results; if power is below 0.8, the CI widths will be highlighted as a limitation.
