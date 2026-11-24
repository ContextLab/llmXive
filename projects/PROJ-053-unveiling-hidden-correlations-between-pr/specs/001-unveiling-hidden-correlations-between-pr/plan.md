# Implementation Plan: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

**Branch**: `001-unveiling-hidden-correlations` | **Date**: 2026-10-23 | **Spec**: `specs/001-unveiling-hidden-correlations/spec.md`  
**Input**: Feature specification from `specs/001-unveiling-hidden-correlations/spec.md`

## Summary
The project delivers a reproducible, CPU‑only pipeline that (1) **attempts** to download a public AM‑alloy dataset that *should* contain the exact required columns (`laser_power`, `scan_speed`, `layer_thickness`, `alloy_composition`, `yield_strength`, and `ductility`) and validates its integrity; (2) preprocesses it (median imputation, min‑max scaling, one‑hot encoding of `alloy_composition`), handling missing values, zero‑variance features, and enforcing a minimum of 50 samples; (3) splits into train/test; (4) trains a Gaussian Process Regression (GPR) model with an RBF kernel, optimizing `length_scale` and noise `sigma` via 5‑fold cross‑validation maximizing log‑marginal‑likelihood; (5) trains a Linear Regression baseline; (6) evaluates R², RMSE, MAE on the test set; (7) computes RMSE as a percentage of the observed target range; (8) performs permutation importance; (9) **conditionally** computes the correlation between permutation importance and an external reference ranking **if such a ranking is provided**; (10) conducts a bootstrap‑based power analysis; (11) extracts predictive uncertainty, flags high‑uncertainty regions (σ > 2 × median σ); (12) **adds** per‑alloy R² scores when `alloy_composition` is present; (13) **adds** a comparative analysis of model performance with and without alloy composition covariates; (14) generates contour and uncertainty‑heatmap visualizations; (15) writes a **manifest file** `state/manifest.yaml` that enumerates all primary artifacts (raw data, processed splits, model files, metrics, visualizations) to satisfy the Single Source of Truth principle; and (16) validates every major artifact against the JSON‑Schema contracts.

> **Scope Limitation** – No open dataset currently provides the exact AM‑alloy variables required by the relevant functional requirement. The pipeline therefore **will abort** with a clear error if the downloaded dataset does not contain the required columns. Acquisition of a suitable dataset is a prerequisite for completing the scientific objectives; this limitation is documented and flagged for a spec amendment.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.0`, `numpy==1.26.0`, `scikit-learn==1.4.0`, `joblib==1.4.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `datasets==2.18.0`, `jsonschema==4.22.0`, `pyyaml==6.0.1`, `statsmodels==0.14.0`  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `results/`, `state/`)  
- **Testing**: `pytest==8.1.0` (tests under `tests/`)  
- **Target Platform**: GitHub Actions free tier (2 CPU, ~7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑first; all methods run on the free runner; no GPU required.

## Constitution Check
| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| I. Reproducibility | ✅ | Random seeds pinned (`np.random.seed(42)`, `random.seed(42)`). All scripts are deterministic and runnable on a fresh CI runner. |
| II. Verified Accuracy | ✅ | Only verified open datasets are accepted; the download step validates SHA‑256 and required columns. |
| III. Data Hygiene | ✅ | Raw file saved under `data/raw/` with a SHA‑256 checksum recorded in `state/dataset_checksum.txt`. Preprocessing writes new CSVs under `data/processed/`; no in‑place mutation. |
| IV. Single Source of Truth | ✅ | Generated `state/manifest.yaml` lists every primary artifact; all figures/tables trace back to this manifest. |
| V. Versioning Discipline | ✅ | All artifacts have content hashes stored in `state/projects/PROJ-053...yaml`. |
| VI. Non‑Linear Process‑Property Mapping | ✅ | GPR with RBF kernel (FR‑003) satisfies the principle. |
| VII. Physical Measurement Independence | ✅ | Predictors and outcomes are sourced from separate columns; no leakage. |

## Project Structure
```text
specs/001-unveiling-hidden-correlations/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── visualization.schema.yaml
└── tasks.md               # generated later by /speckit-tasks
```

```text
code/
├── __init__.py
├── main.py                # orchestrates pipeline steps via CLI flags
├── data_loader.py         # T002 – download & validate dataset
├── preprocessing.py       # T003 – impute, normalize, encode, split
├── models/
│   ├── __init__.py
│   ├── gpr_model.py       # T004 – GPR training & CV
│   └── baseline.py        # T004 – Linear regression baseline
├── analysis/
│   ├── __init__.py
│   ├── importance.py      # T005 – permutation importance (and optional correlation)
│   ├── uncertainty.py     # T007 – high‑uncertainty flagging
│   ├── confounder.py      # T010 – confounder diagnostics (limited to available covariates)
│   ├── residuals.py       # T004 – heteroscedasticity test
│   ├── power_analysis.py  # T011 – bootstrap‑based power analysis (merged into metrics)
│   ├── per_alloy_r2.py    # T013 – subgroup R² per alloy type (conditional)
│   └── composition_control.py # T014 – performance with/without alloy composition
├── visualization/
│   ├── __init__.py
│   └── plots.py           # T006 – contour & heatmap generation
└── utils/
    ├── __init__.py
    └── io_utils.py        # CSV/JSON I/O, checksum handling, logging, manifest generation
```

## Task Summary (mapped to FR / SC)

| Task ID | Script / File | Description | Linked FR / SC | Verification Artifact |
|--------|----------------|-------------|----------------|-----------------------|
| **T002** | `code/data_loader.py` | Download a **verified open AM‑alloy dataset** that contains the exact columns `laser_power`, `scan_speed`, `layer_thickness`, `alloy_composition`, `yield_strength`, `ductility`. Verify SHA‑256 checksum (recorded in `state/dataset_checksum.txt`). Abort with a clear error if any required column is missing or if the row count is < 50. Implements exponential‑backoff retry (max 3 attempts). | **FR‑001**, **FR‑002** | `data/raw/<dataset>.csv`, `state/dataset_checksum.txt`, `results/data_loader.log` |
| **T003** | `code/preprocessing.py` | (a) Median‑impute missing values.<br>(b) Min‑max scale numeric columns to `[0,1]` (producing `*_norm` columns).<br>(c) Detect zero‑variance columns → log warning & drop.<br>(d) One‑hot encode `alloy_composition` (creates `alloy_<type>` binary columns).<br>(e) Split into `train.csv` and `test.csv` using `random_state=42`. Save under `data/processed/`. Write `preprocessing.log`. | **FR‑002**, **FR‑008**, edge‑case handling | `data/processed/train.csv`, `data/processed/test.csv`, `data/processed/preprocessing.log` |
| **T004** | `code/models/gpr_model.py` & `code/models/baseline.py` | Train GPR with RBF kernel; hyper‑parameters `length_scale` and noise `sigma` optimized via 5‑fold CV maximizing log‑marginal‑likelihood. Train Linear Regression baseline on same split. Serialize models with `joblib.dump` to `results/model/gpr_model.joblib` and `results/model/baseline_model.joblib`. Compute R², RMSE, MAE on test set; compute `rmse_percentage_range = RMSE / (max(y_test)-min(y_test)) * 100`. Run Breusch‑Pagan test for heteroscedasticity; populate `residual_analysis` object. Save all metrics to `results/metrics.json` (validated against `contracts/model_output.schema.yaml`). | **FR‑003**, **FR‑004**, **SC‑001**, **SC‑002**, **plan_consistency-56884050** | Model artifacts + `results/metrics.json` |
| **T005** | `code/analysis/importance.py` | Compute permutation importance on the trained GPR (30 repeats, `random_state=42`). If a file `reference_importance.csv` is present, load the external ranking and compute Spearman correlation; store the value as `importance_correlation` in `results/metrics.json`. Merge the GPR importance list into the `feature_importance` field of `results/metrics.json`. | **FR‑006**, **SC‑004** (conditional on external reference) | Updated `results/metrics.json` |
| **T006** | `code/visualization/plots.py` | (a) Generate contour plot of predicted `yield_strength` over `laser_power_norm` vs `scan_speed_norm` (grid 100 × 100).<br>(b) Generate uncertainty heatmap (predictive std dev) over same grid. Save PNGs to `results/plots/contour_yield_strength.png` and `results/plots/uncertainty_heatmap.png`. Write side‑car JSON metadata (`contour_yield_strength.json`, `uncertainty_heatmap.json`) conforming to `contracts/visualization.schema.yaml`. | **FR‑005**, **SC‑003** | PNGs + JSON metadata |
| **T007** | `code/analysis/uncertainty.py` | Compute median σ on the test set; flag any test sample with σ > 2 × median. Write coordinates to `results/high_uncertainty_regions.csv`. Compute fraction `high_uncertainty_ratio` and insert into `results/metrics.json`. | **FR‑007**, **SC‑003** | CSV file + updated `results/metrics.json` |
| **T008** | `code/main.py` (runtime logging) | Wrap entire pipeline in a timer; write total seconds to `results/metrics.json` under key `runtime_seconds`. | **SC‑005** | Updated `results/metrics.json` |
| **T009** | `code/utils/io_utils.py` (schema validation) | After each major step, load the produced artifact (CSV or JSON) and **convert CSV rows to JSON objects** before validating against the appropriate contract via `jsonschema.validate`. Fail fast with informative message. | **FR‑001** | CI passes only if all schema validations succeed |
| **T010** | `code/analysis/confounder.py` | Compute Pearson correlation matrix among all numeric predictors and the response. Record any absolute correlation > 0.8 as a potential confounder in `results/confounders.json`. Compute Variance Inflation Factors (VIF); VIF > 5 logged as a warning. If `alloy_composition` is present, also compute per‑alloy R² (see T013) and note limitation if absent. | **FR‑009** | `results/confounders.json` |
| **T011** | `code/analysis/power_analysis.py` | Perform a bootstrap simulation (1 000 resamples) using the **effective post‑preprocessing sample size** to estimate the distribution of R² under the null. Report the 80 % confidence interval lower bound as the **minimum detectable R²** and store under `power_analysis` in `results/metrics.json`. | **SC‑001**, **SC‑002** (enhanced power analysis) | Updated `results/metrics.json` |
| **T012** | `code/utils/io_utils.py` (manifest) | After successful pipeline run, generate `state/manifest.yaml` listing all primary artifacts (raw data checksum, processed splits, model files, metrics, plots). | **IV. Single Source of Truth** | `state/manifest.yaml` |
| **T013** | `code/analysis/per_alloy_r2.py` | If `alloy_composition` one‑hot columns exist, compute R² on the test set **separately for each alloy type** (filter test rows by alloy flag). Store results in `results/metrics.json` under `per_alloy_r2` (mapping alloy name → R²). | **SC‑007**, **SC‑008** (subgroup assessment) | Updated `results/metrics.json` |
| **T014** | `code/analysis/composition_control.py` | Train a second GPR model **excluding** all alloy‑composition one‑hot columns. Evaluate on the same test set and record `r2_score` and `rmse`. Compare to the full‑model metrics; compute ΔR² and ΔRMSE and store under `performance_without_composition` in `results/metrics.json`. This directly satisfies SC‑008. | **SC‑008**, **FR‑009** | Updated `results/metrics.json` |

All tasks are ordered so that data download precedes preprocessing, which precedes train/test split, which precedes model training, which precedes analysis, which precedes visualization, and finally manifest generation. Each step writes a deterministic log file that the verifier can inspect.

## Complexity Tracking
No violations of the constitution were detected beyond the acknowledged lack of an open dataset satisfying FR‑001. The plan now **fails fast** if the required columns are absent, preserving methodological integrity while awaiting a suitable dataset.

## Assumptions
1. An open dataset containing the exact AM‑alloy variables will become available or be supplied by the researcher.  
2. The dataset size (≥ 50 samples) is sufficient for GPR training on the free‑tier CI runner.  
3. Predictors are numeric; `alloy_composition` is categorical and will be one‑hot encoded.  
4. All random processes are seeded (`np.random.seed(42)`, `random.seed(42)`).  
5. No open dataset currently fulfills FR‑001; the pipeline is prepared to process such a dataset when provided.  

---


