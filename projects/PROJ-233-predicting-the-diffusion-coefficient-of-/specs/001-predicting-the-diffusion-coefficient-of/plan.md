# Implementation Plan: Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors

**Branch**: `001-hydrogen-diffusion-prediction` | **Date**: 2026-10-18 | **Spec**: [spec.md]
**Input**: Feature specification from `/specs/001-hydrogen-diffusion-prediction/spec.md`

## Summary

Build a reproducible, CPU‑only pipeline that (1) ingests hydrogen‑diffusion measurements with compositional, microstructural, and temperature descriptors, (2) trains XGBoost and Random‑Forest regressors under nested 5‑fold cross‑validation with an inner Optuna Bayesian search (≤ 2 h), (3) compares them to a linear baseline on log₁₀(D), (4) quantifies pairwise interactions via SHAP interaction values (descriptive only), (5) validates interaction importance with an **ablation‑based ΔR² share** on an independent hold‑out set (primary metric for SC‑006) and bootstrap‑derived confidence intervals, (6) enforces resource guards (6 h / ~7 GB), (7) performs **both** an **a‑priori simulation‑based power analysis** confirming the ≥ 200‑sample requirement **and** a post‑hoc analysis reporting observed effect size f², minimum detectable f², and CI width for the top‑ranked descriptor, and (8) reports results with full provenance. The plan also contains a **Scope‑Correction** section because the spec’s assumed data sources are not openly downloadable.

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `xgboost==2.0.*`, `shap==0.45.*`, `optuna==3.6.*`, `statsmodels==0.14.*`, `psutil==5.9.*`, `pyyaml==6.0.*`
- **Storage**: file‑based CSV/Parquet under `data/` (raw, processed, results)
- **Testing**: `pytest==8.2.*`
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU, ~7 GB RAM, no GPU)
- **Performance Goals**: full pipeline within 6 h wall‑clock and ~7 GB RAM (FR-006, SC-004)
- **Constraints**: CPU‑only (per spec assumption "No GPU Requirement"); all loops time‑bounded; no synthetic stand‑ins for real measurements.

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All seeds pinned (`SEED=42`); deterministic pipeline; raw data fetched/loaded from a single canonical file path and checksummed. |
| II. Verified Accuracy | No citations beyond verified sources; the unverified NIST/JMS data sources are explicitly flagged, not cited as reachable. |
| III. Data Hygiene | Raw file checksummed into `data/checksums.sha256`; every transformation writes a new derived file with documented provenance; no PII. |
| IV. Single Source of Truth | Every figure/statistic traces to one row in `data/processed/*.parquet` and one code block; no hand‑typed numbers. |
| V. Versioning Discipline | All artifacts content‑hashed; project state `updated_at` maintained by the platform. |
| VI. Numerical Stability & Interaction Validation | Bayesian optimization time‑capped with graceful exit; a substantial number of bootstrap refits (fixed hyperparameters) yield CIs for importance rankings; interaction claims validated on an independent hold‑out via ablation ΔR² (not solely SHAP). |
| VII. Independent Validation & Descriptor Provenance | Target `log10_D` never used as predictor or in imputation/scaling; k‑NN imputation (k=5) fit on predictor columns only inside training folds; proxy derivations documented as independent of diffusion measurements. |

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
│   ├── ingest.py           # FR-001, FR-008: load real data, compute descriptors, unit harmonization, 1/T feature
│   ├── preprocess.py       # FR-001: k‑NN imputation (k=5, predictors only), StandardScaler
│   ├── train.py            # FR-002, FR-003: nested CV + Optuna, linear baseline
│   ├── evaluate.py         # FR-003, FR-010: metrics, external hold‑out evaluation (ablation ΔR² share)
│   ├── shap_interaction.py # FR-004: SHAP interaction values (descriptive only)
│   ├── bootstrap.py        # FR-005, limitation note (fixed hyperparameters)
│   ├── power.py            # FR-009: a‑priori simulation power analysis + post‑hoc effect‑size & min‑detectable‑f²
│   └── guard.py            # FR-006: RAM/wall‑clock monitor, fallback sampling
├── utils/
│   └── seeds.py
└── cli/
    └── run_pipeline.py

tests/
├── contract/
│   └── test_contracts.py
├── unit/
│   ├── test_ingest.py      # uses small hard‑coded fixture rows (spec US‑1 independent test)
│   ├── test_train.py
│   └── test_bootstrap.py
└── data/
    └── fixture_rows.csv    # tiny labeled test fixture — NOT used to produce results; satisfies independent tests
```

**Structure Decision**: single‑project layout (`src/` + `tests/`); a `requirements.txt` lives at the repository root (see quickstart). No frontend, packaging, or infrastructure scaffolding.

## Phase Mapping (covers every FR and SC)

| Phase | Work (FR/SC covered) |
|-------|----------------------|
| **0 – Data acquisition gate & provenance** | Define the real‑input contract (`data/raw/diffusion_measurements.csv` per `contracts/dataset.schema.yaml`). Document that **no verified open source** for the NIST/JMS sources exists; the pipeline **exits non‑zero** with an explicit “no verified data source” message if the file is missing. Checksum raw data (Constitution III). **FR‑001 (data side), SC‑005; scope flag recorded.** |
| **1 – Ingestion & descriptor engineering** | `ingest.py`: harmonize units to m²/s (US‑1 scenario 3); compute `mean_electronegativity`, `atomic_radius_variance` from element‑property tables bundled in‑repo with cited provenance; derive `free_volume_proxy`, `grain_boundary_density` via documented literature formulas independent of D (FR‑007); retain `temperature` **and** create `inv_temperature = 1 / temperature` (physically motivated Arrhenius feature) (FR‑008). `preprocess.py`: k‑NN imputation (k=5) on predictor columns only, StandardScaler on all numeric features including `inv_temperature`, fitted inside training folds (FR‑001). |
| **2 – Nested model training** | `train.py`: outer 5‑fold CV; inner Optuna TPE search (≤ 2 h, 5‑min grace exit with code 0 and “Optimization terminated due to time budget” log; grid‑fallback (`max_depth=6, learning_rate=0.1, n_estimators=200`) on non‑convergence) for XGBoost and RF; target `log10_D`; imputer/scaler fit inside inner folds only (FR‑002). |
| **3 – Linear baseline & comparison** | OLS baseline in the same nested pipeline; RMSE and R² on log₁₀(D) per outer fold; Holm‑adjusted pairwise model comparison; explicit best‑model statement (FR‑003, SC‑001). |
| **4 – SHAP interaction analysis** | `shap.TreeExplainer.shap_interaction_values` on the best non‑linear model; ranked pairwise interaction table with mean |SHAP| magnitudes (descriptive). **Note**: this SHAP‑ratio is *not* used for SC‑006; it is reported only for interpretability. |
| **4b – Independent hold‑out evaluation** | Pre‑CV stratified hold‑out test set (a representative proportion of samples) disjoint from all CV folds. Evaluate the tuned best model; **compute interaction‑variance share via ablation ΔR²**: (R²_full − R²_without_interactions) / R²_full. Also compute a bootstrap‑derived 95 % CI for this share (≤ 40 hold‑out samples, CI reported). Report against the ≥ 70 % criterion (FR‑010, SC‑006). |
| **5 – Bootstrap robustness** | `bootstrap.py`: b = 1…1000 resamples; **refit full pipeline (imputation, scaling, model) with the **best hyperparameters fixed** for feasibility (limitation noted in SC‑002 interpretation). SHAP interactions recomputed per resample; ablation ΔR² for top interactions on held‑out slices; 95 % percentile CIs for top‑5 importances (FR‑005, SC‑002, SC‑003). |
| **6 – Resource guard** | `guard.py`: `psutil` RAM polling (threshold 6 GB → log “Memory limit approached – switching to sampled subset”, 150‑sample subset, fixed seed = 42); wall‑clock abort after a prolonged runtime., exit code 0 with best‑so‑far results (FR‑006, SC‑004). |
| **7a – A‑priori power analysis** | `power.py`: **simulation‑based power analysis** (Monte‑Carlo) that confirms the **n ≥ 200** requirement for detecting interaction effect size *f*² ≥ 0.15 with α = 0.05 and that bootstrap 95 % CI widths for top‑feature importance are ≤ 0.1. This satisfies FR‑009’s design‑time requirement. |
| **7b – Post‑hoc power analysis** | After data are loaded, compute observed effect size `f² = (R²_nl − R²_lin)/(1 − R²_nl)` using `statsmodels.stats.power.FTestPower`; report the **minimum detectable f²** at 0.80 power given the realized sample size; also report the 95 % CI width for the top‑ranked descriptor. Flag if power < 0.80 or CI > 0.1. |
| **8 – Results packaging & contracts** | Write `model_performance`, `interaction_terms`, `bootstrap_ci`, `external_validation`, `power_analysis` tables to `data/results/`; figures (RMSE comparison, SHAP heatmap, CI violins, hold‑out plot, power plot); validate all outputs against `contracts/`; summary report mapping each SC to its measurement. |

## Timeline (≈ 12 substantive tasks)

1. Data acquisition gate: input contract, refusal‑on‑missing‑real‑data, checksumming, provenance docs (Phase 0).
2. Ingestion: unit harmonization, descriptor computation, proxy derivation, **1/T feature** (Phase 1).
3. Preprocessing: fold‑internal k‑NN imputation and scaling (Phase 1).
4. Nested CV training loop with Optuna, time budget, grid fallback (Phase 2).
5. Linear baseline and model‑comparison report with Holm adjustment (Phase 3).
6. SHAP interaction extraction and ranked table (Phase 4).
7. External hold‑out evaluation with **ablation ΔR² share** and bootstrap CI (Phase 4b).
8. Bootstrap refit loop with fixed hyperparameters, limitation note (Phase 5).
9. Resource guard with sampling fallback and graceful timeout (Phase 6).
10. **A‑priori simulation power analysis** + post‑hoc effect‑size & min‑detectable‑f² reporting (Phases 7a & 7b).
11. Contract schemas and validation tests (Phase 8).
12. Figures, summary report, quickstart (Phase 8).

## Scope Correction Requested

The spec must be amended to resolve the data‑availability mismatch: either (a) name a concrete, verified, openly downloadable dataset containing hydrogen diffusion coefficients plus composition/processing/temperature fields, or (b) authorize a documented manual data‑entry effort from open publications with per‑row provenance (still requiring ≥ 95 % non‑null descriptors per SC‑005). Until such a source is provided, the pipeline is fully implemented and tested **but produces no result tables**, and no synthetic data will be substituted.

--- 
