# Implementation Plan: Predicting Defect Formation Energies in Perovskites

**Branch**: `001-predicting-defect-formation-energies` | **Date**: 2026-10-22 | **Spec**: [spec.md]  
**Input**: Feature specification from `specs/001-predicting-defect-formation-energies/spec.md`

## Summary
The project must (1) acquire a perovskite oxygen‑vacancy defect formation‑energy dataset (or accept a user‑provided CSV), (2) compute twelve compositional descriptors for the A, B, X sites using `pymatgen`, (3) validate the dataset and guarantee statistical power, (4) split data into a non‑overlapping train‑test set, (5) train baseline Random Forest and Gradient Boosting regressors with 5‑fold cross‑validation, (6) evaluate the best model on the held‑out test set, reporting RMSE, MAE, R², a bootstrapped 95 % CI for RMSE, and a paired two‑sided t‑test, (7) generate feature‑importance rankings and prediction‑vs‑actual visualisations, (8) document the entire workflow in a reproducible Jupyter notebook, and (9) **ensure total runtime ≤ 30 minutes on a CPU‑only GitHub Actions runner**. If the baseline models do not meet **RMSE ≤ 0.5 eV** and **R² ≥ 70 %**, the pipeline will augment the feature set with structural descriptors and retrain.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pymatgen`, `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `statsmodels`, `pytest`, `jupyter`, `tqdm`  
- **Storage**: Flat files under `data/` (CSV, JSON, TXT) and `models/` (pickle)  
- **Testing**: `pytest` with JSON‑Schema contracts in `contracts/`  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, CPU‑only) – **CPU‑first** execution.  
- **Constraints**: No CUDA/GPU usage; all random seeds fixed (`random_state=42`).  
- **Scale/Scope**: Aim for ≥ 500 valid compositions; if fewer, the pipeline logs a power‑analysis warning but continues (SC‑005).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All steps are scripted, deterministic seeds are pinned, and the notebook (`pipeline.ipynb`) can be re‑executed from a fresh runner. |
| II. Verified Accuracy | Only the Materials Project API (a publicly documented source) and built‑in `pymatgen` tables are used. No external literature is cited without verification. |
| III. Data Hygiene | Raw CSV is checksum‑verified (`sha256sum`), every transformation writes a new file with its own checksum, and no in‑place mutation occurs. |
| IV. Single Source of Truth | Each figure, metric, and table is generated from a single artifact path recorded in `state/projects/PROJ-542‑...yaml`. |
| V. Versioning Discipline | Artifact hashes are written to the state file after each step; any change triggers a hash update. |
| VI. Computational Cost & Descriptor Parsimony | Only twelve compositional descriptors are used for baseline models; models are lightweight tree‑based algorithms. |
| VII. Statistical Rigor | Evaluation includes RMSE, MAE, R², a bootstrap 95 % CI for RMSE, and a paired two‑sided t‑test (α = 0.05). Runtime is measured and must stay ≤ 30 min (SC‑004). |

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
│   ├── download.py          # Materials Project API fetch (fallback to local CSV)
│   ├── featurize.py         # Descriptor computation, writes features.csv + featurize.log + descriptor_gaps.log
│   ├── validate.py          # Size check, logs row count, warns if <500, no power‑analysis step
│   └── checksum.py          # SHA‑256 utility, writes checksums/*.sha256
├── models/
│   ├── split.py             # GroupShuffleSplit → train.csv, test.csv + split.log
│   ├── train.py             # 5‑fold GroupKFold CV, writes cv_metrics.json + model pickles
│   └── evaluate.py          # Held‑out evaluation, bootstrap CI, t‑test, feature importance, figures
├── utils/
│   └── logger.py            # Consistent logging format
└── pipeline.ipynb           # End‑to‑end orchestrator
```

## Implementation Phases (mapping FRs & SCs)

| Phase | Tasks (linked to FR / SC) | Output |
|-------|---------------------------|--------|
| **0 Data Acquisition** | *FR‑001* – `download.py` attempts Materials Project API fetch using `MP_API_KEY`. If the key is missing or the API returns empty, abort with `"No data found for specified filters."` (FR‑007) and require a user‑provided CSV at `data/raw/materials_defects.csv`. <br>*FR‑006* – Verify required columns (`composition`, `defect_type`, `formation_energy`) exist; log any gaps. <br>*Contract* – Validate raw CSV against `contracts/raw_dataset.schema.yaml`. | `data/raw/materials_defects.csv` + `data/checksums/raw_defects.sha256` |
| **1 Feature Engineering** | *FR‑002* – `featurize.py` uses `pymatgen` to compute atomic radius, Pauling electronegativity, oxidation state, and valence electron count for A, B, X → 12 descriptor columns + `formation_energy`. <br>*FR‑006* – After computation, **descriptor_gaps.log** records any missing descriptor values (e.g., missing radius for a site). If any gaps are present, the script aborts with a clear error. <br>*FR‑008* – Rows where oxidation states cannot be determined are dropped; count logged in `featurize.log`. <br>*Checksum* – `checksum.py` creates `data/checksums/features.sha256`. | `data/processed/features.csv`, `data/processed/featurize.log`, `data/processed/descriptor_gaps.log`, `data/checksums/features.sha256` |
| **2 Dataset Validation** | *FR‑009* – `validate.py` checks that `features.csv` contains **≥ 50** rows; raises `ValueError` with guidance if not (FR‑009). <br>*SC‑005* – Logs whether the dataset meets the **≥ 500** rows target; if short, a warning is emitted (power‑analysis removed). | `data/processed/validation.log` |
| **3 Train‑Test Split** | *FR‑011* – `split.py` performs an 80/20 stratified split **by composition group** using `GroupShuffleSplit` (seed = 42). No composition appears in both splits. <br>*Checksum* – Checksums for `train.csv` and `test.csv`. | `data/processed/train.csv`, `data/processed/test.csv`, `data/processed/split.log`, `data/checksums/train.sha256`, `data/checksums/test.sha256` |
| **4 Model Training (Cross‑Validation)** | *FR‑003* – `train.py` runs **5‑fold GroupKFold** CV on `train.csv` for both Random Forest and Gradient Boosting (n_jobs=1, `random_state=42`). <br>*SC‑001* – Captures mean ± std RMSE, MAE, R² per model, writes `cv_metrics.json`. <br>*Edge* – Abort with informative error if fewer than 5 composition groups exist. | `models/rf_cv.pkl`, `models/gb_cv.pkl`, `data/processed/cv_metrics.json`, `data/checksums/cv_metrics.sha256` |
| **5 Model Selection & Held‑Out Evaluation** | *FR‑004* – Select model with lowest mean CV RMSE. <br>*FR‑004* – `evaluate.py` predicts on `test.csv`, computes RMSE, MAE, R². <br>*FR‑004* – Bootstrap 10 000 resamples for a 95 % CI on RMSE. <br>*FR‑004* – Paired two‑sided t‑test (α = 0.05) comparing predictions vs. DFT values; reports p‑value. <br>*SC‑004* – Record total wall‑clock time for the entire pipeline (from start of `download.py` to end of `evaluate.py`). If runtime > 30 minutes, the pipeline aborts with an error indicating the feasibility breach. <br>*Decision rule* – If **RMSE ≤ 0.5 eV** **and** **R² ≥ 70 %**, accept; otherwise trigger Phase 6 fallback. | `data/processed/performance.json`, `figures/pred_vs_actual.png`, `figures/feature_importance.png`, `data/checksums/performance.sha256` |
| **6 Feature Importance & Visualisation** | *FR‑005* – Extract `feature_importances_` from the accepted model, rank, and save bar chart (`feature_importance.png`). <br>*FR‑005* – Generate scatter plot with 1:1 line (`pred_vs_actual.png`). | PNGs in `figures/` |
| **7 Documentation & Contract Validation** | *FR‑010* – All steps orchestrated in `pipeline.ipynb`; notebook executes the full pipeline end‑to‑end. <br>*Contract validation* – After each artifact is written, `pipeline.ipynb` calls `jsonschema.validate` against the appropriate contract (`raw_dataset.schema.yaml` for raw CSV, `model_performance.schema.yaml` for performance JSON). <br>*Testing* – `pytest -q` runs a suite that re‑executes the checksum utility and validates all schemas. | Executable notebook, passing `pytest` suite |
| **8 Fallback Augmentation** | *FR‑012* – If Phase 5 decision rule fails, `featurize.py` is re‑run with additional structural descriptors (coordination numbers, average bond lengths, crystal symmetry class) computed via `pymatgen`. The new `features.csv` overwrites the previous version (new checksum recorded) and Phases 4‑6 are automatically re‑executed. | Updated `features.csv`, refreshed `performance.json`, new figures, updated checksums |

## Edge‑Case Handling (explicitly addressed)
- **Empty API result** → abort with “No data found for specified filters.” (FR‑007).  
- **Missing oxidation states** → rows dropped, count logged (FR‑008).  
- **Insufficient samples for 5‑fold CV** → raise `ValueError` with guidance (FR‑009).  
- **Fewer than five composition groups** → abort before CV with clear message.  
- **Baseline performance failure** → automatic fallback to structural descriptors (FR‑012).  
- **Descriptor gaps** → `descriptor_gaps.log` records any missing descriptor; pipeline aborts if gaps exist (FR‑006).  
- **Runtime budget breach** → pipeline aborts with a runtime‑exceeded error (SC‑004).  

## Timeline (approximate)

| Week | Milestone |
|------|-----------|
| 1 | Implement `download.py`, `checksum.py`, and raw‑dataset contract; generate raw CSV or abort. |
| 2 | Build `featurize.py` with full descriptor‑gap reporting; produce `features.csv` + logs. |
| 3 | Write `validate.py` (size check, warning for <500 rows), `split.py`, and corresponding logs. |
| 4 | Implement `train.py` (GroupKFold CV) and `evaluate.py` (bootstrap CI, t‑test, feature importance). |
| 5 | Assemble `pipeline.ipynb`, add contract validation calls, and write `checksum_all.py` (per‑artifact checksums). |
| 6 | Full CI run, debugging, and verification of all contracts; implement fallback augmentation. |
| 7 | Documentation polishing, quickstart guide, and final reproducibility audit. |

---

