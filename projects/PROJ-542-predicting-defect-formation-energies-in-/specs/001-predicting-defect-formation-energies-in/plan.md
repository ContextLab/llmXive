# Implementation Plan: Predicting Defect Formation Energies in Perovskites with Machine Learning

**Branch**: `001-predicting-defect-formation-energies` | **Date**: 2026-10-18 | **Spec**: [spec.md]  
**Input**: Feature specification from `specs/001-predicting-defect-formation-energies/spec.md`

## Summary
The project must (1) acquire a dataset of perovskite oxygen‑vacancy defect formation energies, (2) compute twelve compositional descriptors (atomic radius, Pauling electronegativity, oxidation state, valence electron count for A, B, X sites) using `pymatgen`, (3) train baseline Random Forest and Gradient Boosting regressors with 5‑fold **GroupKFold** cross‑validation on a CPU‑only runner, (4) evaluate the best model on a held‑out test split, reporting RMSE, MAE, R², a bootstrapped 95 % CI for RMSE, and a paired two‑sided t‑test (α = 0.05) for bias, (5) generate a ranked list of feature importances and a prediction‑vs‑actual scatter plot, (6) document the entire workflow in a reproducible Jupyter notebook, and (7) fall back to augmenting the feature set with structural descriptors if baseline compositional models do not meet the performance thresholds.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pymatgen`, `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `pytest`, `jupyter`  
- **Storage**: Flat files under `data/` (CSV, JSON, PNG) and `models/` (pickle)  
- **Testing**: `pytest` with JSON‑schema contracts in `contracts/`  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, CPU‑only) – **CPU‑first** execution.  
- **Constraints**: No CUDA/GPU usage; random seeds pinned (`random_state=42`).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All steps are scripted, deterministic seeds are fixed, and the notebook can be re‑executed from a fresh runner. |
| II. Verified Accuracy | No external literature beyond the Materials Project API (a standard, publicly documented source). |
| III. Data Hygiene | Raw CSV is checksum‑verified; every transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | The state file `state/projects/PROJ-542-predicting-defect-formation-energies-in-.yaml` records hashes, timestamps, and provenance for every generated artifact. |
| V. Versioning Discipline | Updated artifact hashes trigger state‑file updates per Constitution V. |
| VI. Computational Cost & Descriptor Parsimony | Only twelve compositional descriptors are used; models are lightweight tree‑based algorithms. |
| VII. Statistical Rigor | Evaluation includes RMSE, MAE, R², bootstrapped CI, and paired t‑test (α = 0.05). |

## Project Structure
```text
specs/001-predicting-defect-formation-energies/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── raw_dataset.schema.yaml
│   └── model_performance.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
src/
├── data/
│   ├── download.py          # Materials Project API fetch (API key via env) or abort
│   ├── featurize.py         # Descriptor computation with pymatgen
│   └── validate.py          # Size, missing‑value, power‑analysis checks
├── models/
│   ├── split.py             # GroupShuffleSplit → train.csv / test.csv
│   ├── train.py             # 5‑fold GroupKFold CV for RF & GB (n_jobs=1, random_state=42)
│   └── evaluate.py          # Held‑out evaluation, bootstrap CI, paired t‑test, feature importance
├── utils/
│   ├── logger.py
│   └── checksum.py          # SHA‑256 checksum utility
└── pipeline.ipynb           # End‑to‑end orchestrator
```

## Implementation Phases (mapping FRs & SCs)

| Phase | Tasks (linked to FR / SC) | Output |
|-------|---------------------------|--------|
| **0 Data Strategy** | *FR‑001* – Attempt download from Materials Project API; if `MP_API_KEY` missing, abort with clear message and require a user‑provided CSV at `data/raw/materials_defects.csv`. <br>*FR‑006* – Validate presence of required columns; log and drop rows with missing descriptors. <br>*FR‑007* – Detect empty API result set → abort with `"No data found for specified filters."` <br>*Contract* – Validate `data/raw/materials_defects.csv` against `contracts/raw_dataset.schema.yaml`. | `data/raw/materials_defects.csv` (checksum recorded in `data/checksums/raw_defects.sha256`) |
| **1 Feature Engineering** | *FR‑002* – `featurize.py` extracts atomic radius, Pauling electronegativity, oxidation state, valence electron count for A, B, X sites → a set of feature columns plus the target. <br>*FR‑008* – Rows where oxidation states cannot be determined are excluded; count logged. | `data/processed/features.csv` (checksum `data/checksums/features.sha256`) |
| **2 Dataset Validation & Power Analysis** | *FR‑009* – Verify `features.csv` contains **≥ 50** rows; raise `ValueError` otherwise (SC‑005). <br>*SC‑005* – Compute **achieved statistical power** to detect a **0.1 eV RMSE improvement** with **σ ≈ 0.3 eV**, α = 0.05, target power = 0.8 (required N ≈ a few hundred participants.). Log power and flag if N < 210. <br>*SC‑001* – Ensure **≥ 500** valid rows; if fewer, note limitation but continue. | `data/processed/validation.log` |
| **3 Train‑Test Split** | *FR‑011* – Deterministic `GroupShuffleSplit` (seed = 42) creates an 80/20 stratified (by composition) split with no overlap between groups. | `data/processed/train.csv`, `data/processed/test.csv` |
| **4 Model Training (Cross‑Validation)** | *FR‑003* – `train.py` runs **5‑fold GroupKFold** CV **only on `train.csv`**. <br>*Check* – Verify number of unique composition groups ≥ 5; abort with informative error if not. <br>*SC‑001* – Capture mean RMSE, MAE, R² per model. | `models/rf_cv.pkl`, `models/gb_cv.pkl`, `data/processed/cv_metrics.json` |
| **5 Model Selection & Evaluation** | *FR‑004* – Select model with lowest mean CV RMSE. <br>*FR‑004* – `evaluate.py` predicts on held‑out `test.csv`, computes RMSE, MAE, R². <br>*FR‑004* – Bootstrap a large number of resamples for 95 % CI of RMSE. <br>*FR‑004* – Paired two‑sided t‑test (α = 0.05) to assess bias (p‑value reported **only** for bias detection). <br>*Decision rule* – **Accept** model if **RMSE ≤ 0.5 eV** **and** **R² ≥ 70 %** (covers SC‑001 and SC‑002). If either fails, trigger Phase 8 fallback. | `data/processed/performance.json` |
| **6 Feature Importance & Visualisation** | *FR‑005* – Extract `feature_importances_` from the accepted model, rank, and save bar chart (`figures/feature_importance.png`). <br>*FR‑005* – Generate scatter plot of predicted vs. actual energies with 1:1 line (`figures/pred_vs_actual.png`). | PNG files in `figures/` |
| **7 Documentation & Contract Validation** | *FR‑010* – All steps captured in `pipeline.ipynb`; notebook executes end‑to‑end and produces the artefacts above. <br>*Contract mapping* – `raw_dataset.schema.yaml` ↔ `data/raw/materials_defects.csv`; `model_performance.schema.yaml` ↔ `data/processed/performance.json`; `cv_metrics.json` ↔ `model_performance.schema.yaml`; `features.csv` ↔ `raw_dataset.schema.yaml` (validation of descriptor columns). <br>*Contract validation* – Each artifact is validated against its schema inside the notebook and via `pytest`. | Executable notebook, passing contract tests |
| **8 Fallback Augmentation** | *FR‑012* – If Phase 5 decision rule fails, **augment** `features.csv` with structural descriptors (coordination numbers, average bond lengths, crystal symmetry class) computed via `pymatgen`. Overwrite file (new checksum recorded) and repeat Phases 4‑6 automatically. | Updated `data/processed/features.csv`, refreshed `performance.json`, new figures |

## Edge‑Case Handling (explicitly addressed)
- **Empty API result** → abort with “No data found for specified filters.” (FR‑007).  
- **Missing oxidation states** → rows dropped, count logged (FR‑008).  
- **Insufficient samples for 5‑fold CV** → raise `ValueError` with guidance (FR‑009).  
- **Fewer than five composition groups** → abort before CV with informative error (methodology‑f3cb4f4c).  
- **Baseline performance failure** → automatic fallback to structural descriptors (FR‑012).  

## Timeline (approximate)

| Week | Milestone |
|------|-----------|
| 1 | Implement data‑download fallback, checksum, raw‑schema validation (Phase 0). |
| 2 | Feature‑engineering pipeline, unit tests for descriptor extraction (Phase 1). |
| 3 | GroupKFold training scripts, CPU‑only benchmarking (Phase 4). |
| 4 | Held‑out evaluation, statistical analysis, visualisation (Phase 5). |
| 5 | Notebook integration, contract schemas, quickstart doc (Phase 7). |
| 6 | Full CI run, bug‑fixes, final reproducibility check; implement fallback augmentation if needed (Phase 8). |

---


