# Implementation Plan: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

**Branch**: `001-unveiling-hidden-correlations` | **Date**: 2026-10-23 | **Spec**: `specs/001-unveiling-hidden-correlations/spec.md`  
**Input**: Feature specification from `specs/001-unveiling-hidden-correlations/spec.md`

## Summary
The project delivers a reproducible, CPU‑only pipeline that (1) downloads a **verified open proxy dataset** (RBF‑Morph “doe.csv”), (2) preprocesses it (median imputation, min‑max scaling, one‑hot encoding where needed), (3) splits the data into train/test, (4) trains a Gaussian Process Regression model with an RBF kernel using 5‑fold cross‑validation, (5) trains a Linear Regression baseline, (6) evaluates R², RMSE, MAE and RMSE expressed as a percentage of the target range, (7) computes permutation importance **merged into `results/metrics.json`**, (8) extracts predictive uncertainty, (9) flags high‑uncertainty regions (σ > 2 × median σ), (10) performs a lightweight confounder assessment, (11) runs a simple power‑analysis estimate, (12) generates contour and uncertainty heatmap visualizations. All artifacts are validated against JSON‑Schema contracts and logged for reproducibility.

> **Scope Limitation** – No open dataset provides the exact AM‑alloy variables required by FR‑001 (laser power, scan speed, layer thickness, yield strength, ductility). The RBF‑Morph “doe.csv” dataset is therefore used **solely as a methodological illustration**; its three numeric predictors (`x1`, `x2`, `x3`) stand in for the processing parameters, and its `response` column stands in for a mechanical property. This limitation is documented in the final report and all FR/SC references are interpreted with respect to these proxy variables. FR‑001 cannot be fully satisfied with publicly available data; the unmet requirement is flagged for possible scope revision.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.0`, `numpy==1.26.0`, `scikit-learn==1.4.0`, `joblib==1.4.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `datasets==2.18.0`, `pyyaml==6.0.1`  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `results/`)  
- **Testing**: `pytest==8.1.0` (tests under `tests/`)  
- **Target Platform**: GitHub Actions free tier (2 CPU cores, ~7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑first; no GPU required; all files must be open‑source and directly downloadable; strict dataset‑variable fit (proxy acknowledged).  

## Constitution Check
| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| I. Reproducibility | ✅ | Random seeds pinned (`np.random.seed(42)`, `random.seed(42)`). All scripts are deterministic and runnable on a fresh CI runner. |
| II. Verified Accuracy | ✅ | Only the verified RBF‑Morph “doe.csv” dataset (URL below) is used. No fabricated sources. |
| III. Data Hygiene | ✅ | Raw file saved under `data/raw/` with a SHA checksum recorded in `state/dataset_checksum.txt`. Preprocessing writes new CSVs under `data/processed/`; no in‑place mutation. |
| IV. Single Source of Truth | ✅ | Every figure/table is generated from files in `results/`; no hand‑typed numbers. |
| V. Versioning Discipline | ✅ | All artifacts have content hashes stored in `state/projects/PROJ-053...yaml`. |
| VI. Non‑Linear Process‑Property Mapping | ✅ | GPR with RBF kernel (FR‑003) satisfies the principle. |
| VII. Physical Measurement Independence | ✅ | Predictors (`x1`, `x2`, `x3`) are raw experimental settings; target (`response`) is a measured outcome distinct from inputs (metadata in the dataset). |

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
│   ├── importance.py      # T005 – permutation importance (merged into metrics)
│   ├── uncertainty.py     # T007 – high‑uncertainty flagging
│   ├── confounder.py      # T010 – simple confounder assessment
│   └── power_analysis.py  # T011 – power‑analysis estimate
├── visualization/
│   ├── __init__.py
│   └── plots.py           # T006 – contour & heatmap generation
└── utils/
    ├── __init__.py
    └── io_utils.py        # CSV/JSON I/O, checksum handling, logging
```

## Task Summary (mapped to FR / SC)

| Task ID | Script / File | Description | Linked FR / SC | Verification Artifact |
|--------|----------------|-------------|----------------|-----------------------|
| **T002** | `code/data_loader.py` | Download `doe.csv` from `https://huggingface.co/datasets/RBFMorph/Digipad-dataset/resolve/main/doe.csv`; verify SHA‑256 (recorded in `state/dataset_checksum.txt`); confirm ≥ 50 rows and presence of columns `x1`, `x2`, `x3`, `response`. Abort with clear error if checks fail. Implements retry logic with exponential back‑off (max 3 attempts). | **FR‑001**, **FR‑002** (imputation/normalization later) | `data/raw/doe.csv`, `state/dataset_checksum.txt`, `results/data_loader.log` |
| **T003** | `code/preprocessing.py` | (a) Median‑impute missing values.<br>(b) Min‑max scale numeric columns to `[0,1]` (producing `*_norm` columns).<br>(c) Detect zero‑variance columns → log warning & drop.<br>(d) One‑hot encode any categorical columns (none in this dataset).<br>(e) Split into `train.csv` and `test.csv` using `random_state=42`. Save under `data/processed/`. Write `preprocessing.log`. | **FR‑002**, edge‑case handling | `data/processed/train.csv`, `data/processed/test.csv`, `data/processed/preprocessing.log` |
| **T004** | `code/models/gpr_model.py` & `code/models/baseline.py` | Train GPR with RBF kernel on training set; hyper‑parameters (`length_scale`, `alpha`) optimized via 5‑fold CV maximizing log‑marginal‑likelihood. Train Linear Regression baseline on same split. Serialize models with `joblib.dump` to `results/model/gpr_model.joblib` and `results/model/baseline_model.joblib`. Compute R², RMSE, MAE on test set; compute `rmse_percentage_range = RMSE / (max(y_test)-min(y_test)) * 100`. Save all metrics to `results/metrics.json` (validated against `contracts/model_output.schema.yaml`). | **FR‑003**, **FR‑004**, **SC‑001**, **SC‑002** | Model artifacts + `results/metrics.json` |
| **T005** | `code/analysis/importance.py` | Compute permutation importance on the trained GPR (30 repeats, `random_state=42`). **Merge** the resulting list of `{feature_name, importance_score}` into the `feature_importance` field of `results/metrics.json`. | **FR‑006**, **SC‑004** | Updated `results/metrics.json` |
| **T006** | `code/visualization/plots.py` | (a) Generate contour plot of predicted `response` over `x1_norm` vs `x2_norm` (grid 100 × 100).<br>(b) Generate uncertainty heatmap (predictive std dev) over same grid. Save PNGs to `results/plots/contour_response.png` and `results/plots/uncertainty_heatmap.png`. Write side‑car JSON metadata (`contour_response.json`, `uncertainty_heatmap.json`) conforming to `contracts/visualization.schema.yaml`. | **FR‑005**, **SC‑003** | PNGs + JSON metadata |
| **T007** | `code/analysis/uncertainty.py` | Compute median σ on the test set; flag any test sample with σ > 2 × median. Write coordinates to `results/high_uncertainty_regions.csv`. Compute fraction `high_uncertainty_ratio` and insert into `results/metrics.json`. | **FR‑007**, **SC‑003** | CSV file + updated `results/metrics.json` |
| **T008** | `code/main.py` (runtime logging) | Wrap entire pipeline in a timer; write total seconds to `results/metrics.json` under key `runtime_seconds`. | **SC‑005** | Updated `results/metrics.json` |
| **T009** | `code/utils/io_utils.py` (schema validation) | After each major step, load the produced artifact (CSV or JSON) and **convert CSV rows to JSON objects** before validating against the appropriate contract via `jsonschema.validate`. Fail fast with informative message. This satisfies **FR‑001** data‑hygiene validation. | **FR‑001** | CI passes only if all schema validations succeed |
| **T010** | `code/analysis/confounder.py` | Compute Pearson correlation matrix among all predictors and the response. Any absolute correlation > 0.8 is recorded as a potential confounder in `results/confounders.json`. | **FR‑003** (model‑related validation) | `results/confounders.json` |
| **T011** | `code/analysis/power_analysis.py` | Using a two‑sided α = 0.05, estimate the minimum detectable R² with N = 50 samples and 5‑fold CV (approx. 0.10). Record the estimate and limitation note in `results/power_analysis.json`. | **SC‑001**, **SC‑002** (power‑analysis extension) | `results/power_analysis.json` |

All tasks are ordered so that data download precedes preprocessing, which precedes train/test split, which precedes model training, which precedes analysis, which precedes visualization. Each step writes a deterministic log file that the verifier can inspect.

## Complexity Tracking
No violations of the constitution were detected. The only deviation from the original specification is the **proxy dataset** usage, which is explicitly documented, does not introduce new constraints, and is reflected in all downstream artifacts and success criteria.

## Assumptions (re‑stated)
1. The **RBF‑Morph “doe.csv”** dataset is openly downloadable and contains ≥ 50 rows with three numeric predictors and a continuous response.  
2. The response column is a legitimate measured outcome (proxy for a mechanical property).  
3. CPU‑only GPR on ≤ 500 samples fits within the free‑tier CI memory/time budget.  
4. All random processes are seeded (`np.random.seed(42)`, `random.seed(42)`).  
5. No open dataset provides the exact AM‑specific variables; the proxy is used solely to illustrate the methodology.  

---



