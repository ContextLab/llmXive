# Implementation Plan: Predicting Defect Formation Energies in Perovskites with Machine Learning

**Branch**: `001-predicting-defect-energies` | **Date**: 2026-10-16 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `specs/001-predicting-defect-formation-energies/spec.md`

## Summary
The project must (1) acquire a dataset of perovskite oxygen‑vacancy defect formation energies, (2) compute twelve compositional descriptors (atomic radius, Pauling electronegativity, oxidation state, valence electron count for A, B, X sites) using `pymatgen` (plus an optional Goldschmidt tolerance factor when lattice data exist), (3) train baseline Random Forest and Gradient Boosting regressors with **5‑fold GroupKFold** cross‑validation on a CPU‑only runner, (4) evaluate the best model on a held‑out test split, reporting RMSE, MAE, R², a bootstrapped 95 % CI for RMSE, and a paired two‑sided t‑test (α = 0.05), (5) generate a ranked list of feature importances and a prediction‑vs‑actual scatter plot, and (6) document the entire workflow in a reproducible Jupyter notebook.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pymatgen`, `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `pytest`  
- **Storage**: Flat files under `data/` (CSV, JSON, PNG)  
- **Testing**: `pytest` with JSON‑schema contracts in `contracts/`  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, no GPU) – **CPU‑first** execution.  
- **Project Type**: Research notebook / library‑style code under `src/`  
- **Performance Goals**: End‑to‑end run ≤ 6 h on the free‑tier CI runner; memory ≤ 6 GB.  
- **Constraints**: No CUDA/GPU usage; random seeds pinned (`random_state=42`).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All steps are scripted, deterministic seeds are fixed, and the notebook can be re‑executed from a fresh runner. |
| II. Verified Accuracy | No external literature citations beyond the Materials Project API (a standard, publicly documented source). |
| III. Data Hygiene | Raw CSV is checksum‑verified; every transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | Figures and tables are generated directly from pipeline artefacts; no manual transcription. |
| V. Versioning Discipline | Updated artefacts (e.g., `features.csv` after fallback) are re‑checksummed and their hashes recorded in the project‑state YAML. |
| VI. Computational Cost & Descriptor Parsimony | Only twelve compositional descriptors (plus optional tolerance factor) are used; models are lightweight tree‑based algorithms. |
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
│   ├── download.py          # optional Materials Project API fetch (API key via env)
│   ├── featurize.py         # descriptor computation with pymatgen (+ optional tolerance factor)
│   └── pipeline.ipynb       # end‑to‑end notebook orchestrating all phases
├── models/
│   ├── train.py             # GroupKFold CV for RF & GB (n_jobs=1, random_state=42)
│   └── evaluate.py          # held‑out evaluation, stats, plots
└── utils/
    ├── logger.py
    └── contracts.py         # validation helpers
```

## Implementation Phases (mapping FRs & SCs)

| Phase | Tasks (linked to FR / SC) | Output |
|-------|---------------------------|--------|
| **0 Data Strategy** | *FR‑001* – Attempt automatic download from Materials Project API; if `MP_API_KEY` missing, abort with clear message and require user‑provided CSV at `data/raw/materials_defects.csv`. <br>*FR‑006* – Validate presence of all required columns; log and drop rows with missing descriptors. <br>*FR‑007* – Detect empty API result set and abort with `"No data found for specified filters."` | `data/raw/materials_defects.csv` (checksum recorded) |
| **1 Feature Engineering** | *FR‑002* – `featurize.py` extracts atomic radius, Pauling electronegativity, oxidation state, valence electron count for A, B, X sites → 12 columns. <br>*FR‑008* – Rows where oxidation states cannot be determined are excluded; count logged. <br>*Optional* – If lattice parameters are present, compute Goldschmidt tolerance factor (single extra column). | `data/processed/features.csv` (12 or 13 descriptor columns + target) |
| **2 Dataset Validation & Power Analysis** | *FR‑009* – Verify `features.csv` contains ≥ 50 rows; raise `ValueError` otherwise. <br>*SC‑005* – Ensure ≥ 500 valid rows; if fewer, log a warning and report reduced statistical power. <br>**Power analysis** – Using `statsmodels.stats.power.tt_ind_solve_power`, assume an effect size corresponding to a 0.1 eV RMSE improvement with σ estimated from a pilot subset; compute required N for 80 % power at α = 0.05 and compare to actual N, logging the achieved power. | Validation log (`data/processed/validation.log`) |
| **3 Model Training (Cross‑Validation)** | *FR‑003* – `train.py` runs **5‑fold GroupKFold** (`GroupKFold` with groups = full composition string) for Random Forest and Gradient Boosting (scikit‑learn, `n_jobs=1`, `random_state=42`). <br>*SC‑004* – All training runs on CPU‑only runner; total runtime recorded (must stay ≤ 30 min per run). | `models/rf_cv.pkl`, `models/gb_cv.pkl`, `data/processed/cv_metrics.json` |
| **4 Model Selection & Test Split** | *FR‑011* – Create an 80/20 stratified (by composition) train‑test split (seeded, no overlap with CV groups). <br>*FR‑003* (re‑used) – Select model with lowest mean CV RMSE. | `data/processed/train.csv`, `data/processed/test.csv`, `models/best_model.pkl` |
| **5 Performance Evaluation** | *FR‑004* – `evaluate.py` predicts on held‑out test set, computes RMSE, MAE, R². <br>*FR‑004* – Bootstrap 10 000 resamples for 95 % CI of RMSE. <br>*FR‑004* – Paired two‑sided t‑test (α = 0.05) between predictions and DFT values. <br>*Decision rule* – If **both** RMSE ≤ 0.5 eV **and** R² ≥ 70 % **and** p‑value > 0.05, accept model; otherwise trigger Phase 8 fallback. | `data/processed/performance.json` |
| **6 Feature Importance & Visualisation** | *FR‑005* – Extract `feature_importances_` from the best model, rank, and save bar chart (`figures/feature_importance.png`). <br>*FR‑005* – Generate scatter plot of predicted vs. actual energies with 1:1 line (`figures/pred_vs_actual.png`). | PNG figures in `figures/` |
| **7 Documentation & Contract Validation** | *FR‑010* – All steps captured in `pipeline.ipynb`; notebook executes end‑to‑end and produces the artefacts above. <br>*FR‑010* – Contract validation against `contracts/*.schema.yaml` performed inside the notebook (and via `pytest`). | Executable notebook, passing contract tests |
| **8 Fallback Augmentation** | If Phase 5 decision rule fails, **augment** the existing `features.csv` with structural descriptors (coordination numbers, average bond lengths, crystal symmetry class) computed via `pymatgen`. The file is **overwritten** (new checksum recorded) and the training/evaluation steps (Phases 3‑5) are repeated automatically. No new artefact name is introduced, preserving the data‑model consistency. | Updated `data/processed/features.csv` (checksum refreshed), refreshed `performance.json`, updated figures. |

## Edge‑Case Handling (explicitly addressed)
- **Empty API result** → abort with “No data found for specified filters.” (FR‑007).  
- **Missing oxidation states** → rows dropped, count logged (FR‑008).  
- **Insufficient samples for 5‑fold CV** → raise `ValueError` with guidance (FR‑009).  
- **Imbalanced composition classes** → GroupKFold ensures whole compositions stay within a single fold; additional class‑weighting removed (corrected API misuse).  
- **Baseline performance failure** → automatic fallback to structural descriptors (FR‑012).  

## Timeline (approximate)

| Week | Milestone |
|------|-----------|
| 1 | Implement data‑download fallback, checksum, validation (Phase 0). |
| 2 | Feature‑engineering pipeline, unit tests for descriptor extraction (Phase 1). |
| 3 | GroupKFold training scripts, CPU‑only benchmarking (Phase 3). |
| 4 | Held‑out evaluation, statistical analysis, visualisation (Phase 5). |
| 5 | Notebook integration, contract schemas, quickstart doc (Phase 7). |
| 6 | Full CI run, bug‑fixes, final reproducibility check; implement fallback augmentation if needed (Phase 8). |

---

