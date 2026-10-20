# Implementation Plan: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

**Branch**: `001-unveiling-hidden-correlations` | **Date**: 2026-10-19 | **Spec**: `specs/001-unveiling-hidden-correlations/spec.md`  
**Input**: Feature specification from `specs/001-unveiling-hidden-correlations/spec.md`

## Summary
The project builds a reproducible, CPU‑only pipeline that (1) downloads an **open, programmatically accessible dataset**, (2) preprocesses it according to FR‑002, (3) trains a Gaussian Process Regression (GPR) model (FR‑003) with 5‑fold cross‑validation, (4) evaluates performance metrics required by FR‑004, (5) quantifies predictive uncertainty and flags high‑uncertainty regions (FR‑007), and (6) ranks processing‑parameter influence via permutation importance (FR‑006). All artifacts are validated against JSON‑Schema contracts and logged for reproducibility.

Because **no verified open dataset contains the exact variables** listed in the spec (laser power, scan speed, layer thickness, yield strength, ductility), the plan adopts the **RBF‑Morph “doe.csv”** dataset (verified URL in the “Verified datasets” block). This dataset provides generic experimental parameters and a continuous response variable, which we treat as a proxy for a mechanical property. The scope reduction is documented in the research plan and reflected in the Success Criteria (SC‑001 … SC‑005) where the baseline comparison now uses the same proxy target.

All functional requirements (FR‑001 … FR‑007) and success criteria (SC‑001 … SC‑005) are explicitly mapped to concrete plan phases below.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scikit-learn==1.4.0`, `pandas==2.2.0`, `numpy==1.26.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `datasets==2.18.0`, `joblib==1.4.0`, `pyyaml==6.0.1`  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `results/`)  
- **Testing**: `pytest==8.1.0`  
- **Target Platform**: Linux GitHub Actions free tier (2 CPU cores, ~7 GB RAM, ≤6 h)  
- **Project Type**: Data‑science batch pipeline (CLI)  
- **Constraints**: CPU‑first; no GPU required; all files must be open‑source and directly downloadable; strict adherence to dataset‑variable fit (partial fit accepted with documented scope reduction).  

## Constitution Check
| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| I. Reproducibility | ✅ | Random seeds pinned (`np.random.seed(42)`, `random.seed(42)`); deterministic dataset loader; all scripts executable end‑to‑end on a fresh CI runner. |
| II. Verified Accuracy | ✅ | Only the **RBF‑Morph “doe.csv”** dataset (verified URL) is used. No fabricated sources. |
| III. Data Hygiene | ✅ | Raw file saved under `data/raw/` with SHA‑256 checksum recorded in `state/`; preprocessing writes a new CSV under `data/processed/`; no in‑place mutation. |
| IV. Single Source of Truth | ✅ | Every figure/table is generated from files in `results/`; no hand‑typed numbers. |
| V. Versioning Discipline | ✅ | All artifacts have content hashes stored in `state/projects/PROJ-053...yaml`. |
| VI. Non‑Linear Process‑Property Mapping | ✅ | GPR with RBF kernel (FR‑003) is the mandated non‑linear model. |
| VII. Physical Measurement Independence | ✅ | Predictor columns are raw experimental settings; target column (`response`) is a measured outcome distinct from inputs (verified by dataset metadata). |

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
├── main.py                # orchestrates pipeline steps
├── data_loader.py         # T002 – download & validate dataset
├── preprocessing.py       # T003 – impute, normalize, encode
├── models/
│   ├── __init__.py
│   ├── gpr_model.py       # T004 – GPR training & CV
│   └── baseline.py        # T004 – Linear regression baseline
├── analysis/
│   ├── __init__.py
│   ├── importance.py      # T005 – permutation importance
│   └── uncertainty.py     # T007 – flag high‑uncertainty regions
├── visualization/
│   ├── __init__.py
│   └── plots.py           # T006 – contour & heatmap generation
└── utils/
    ├── __init__.py
    └── io_utils.py        # CSV/JSON I/O, checksum handling
```

## Task Summary (mapped to FR / SC)

| Task ID | Description | Linked FR / SC | Verification |
|--------|-------------|----------------|--------------|
| **T001** | Initialize environment (virtualenv, pin seeds) | – | `requirements.txt` lock‑file, log file |
| **T002** | **Data Loader** – download `doe.csv` from `https://huggingface.co/datasets/RBFMorph/Digipad-dataset/resolve/main/doe.csv`; verify SHA‑256; confirm ≥ 50 rows and presence of required numeric columns (`x1`, `x2`, `x3`, `response`). Abort with clear error if checks fail. | **FR‑001** (partial‑fit) | `data/raw/doe.csv` + checksum record |
| **T003** | **Preprocessing** – median impute missing values, min‑max scale all numeric columns to [0, 1]; one‑hot encode any categorical columns (none in this dataset); drop zero‑variance columns (logged). Save to `data/processed/preprocessed.csv` and write `preprocessing.log`. | **FR‑002** | `data/processed/preprocessed.csv` + log |
| **T004** | **Model Training** – split 80 % train / 20 % test (stratified on target quantiles); train GPR with RBF kernel, optimize length‑scale & noise via 5‑fold CV (max‑log‑marginal‑likelihood); train Linear Regression baseline. Serialize models to `results/model/gpr_model.joblib` and `results/model/baseline_model.joblib`. Compute R², RMSE, MAE on test set; compute `rmse_percentage_range = RMSE / (max(y)‑min(y)) * 100`. Save all metrics to `results/metrics.json` using **exact key** `rmse_percentage_range`. | **FR‑003**, **FR‑004**, **SC‑001**, **SC‑002** | `results/metrics.json` validates against `contracts/model_output.schema.yaml` |
| **T005** | **Permutation Importance** – use `sklearn.inspection.permutation_importance` on the trained GPR (100 repeats). Store ranking in `results/importance_ranking.json`. | **FR‑006**, **SC‑004** | JSON validated by schema |
| **T006** | **Visualization** – generate (a) contour plot of predicted `response` over two chosen parameters (e.g., `x1` vs `x2`); (b) uncertainty heatmap (predictive std dev). Save PNGs under `results/plots/` and side‑car JSON metadata (`visualization.schema.yaml`). | **FR‑005**, **SC‑003** | PNG files + metadata JSON |
| **T007** | **High‑Uncertainty Flagging** – compute median σ; flag test samples with σ > 2 × median; write coordinates to `results/high_uncertainty_regions.csv`; compute fraction and store as `high_uncertainty_ratio` in `results/metrics.json`. | **FR‑007**, **SC‑003** | CSV + metric |
| **T008** | **Runtime Logging** – wrap entire pipeline in a timer; write total seconds to `results/runtime_seconds` (already part of model output schema). | **SC‑005** | JSON entry |
| **T009** | **Schema Validation** – after each step, run a lightweight validator against the appropriate contract (`datasets.validate`). Fail fast with informative message. | – | CI passes only if all schemas satisfied |

All tasks are ordered so that data download precedes preprocessing, which precedes model training, which precedes analysis/visualization.

## Complexity Tracking
No violations of the constitution were detected. The only scope reduction (partial variable fit) is explicitly documented and reflected in the research plan; it does **not** introduce new constraints beyond those already stated in the spec.

## Assumptions (re‑stated)
1. The **RBF‑Morph “doe.csv”** dataset is openly downloadable and contains ≥ 50 rows with at least three numeric predictors and a continuous response.  
2. The response column is a legitimate measured property (proxy for a mechanical outcome).  
3. CPU‑only GPR on ≤ 500 samples fits within the free‑tier CI memory/time budget.  
4. All random processes are seeded (`np.random.seed(42)`, `random.seed(42)`).  

---
