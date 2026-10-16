# Implementation Plan: Predicting Defect Formation Energies in Perovskites with Machine Learning

**Branch**: `001-predicting-defect-formation-energies` | **Date**: 2026-10-16 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `specs/001-predicting-defect-formation-energies/spec.md`

## Summary
The project must (1) obtain a dataset of perovskite oxygen‑vacancy defect formation energies, (2) compute twelve compositional descriptors (atomic radius, Pauling electronegativity, oxidation state, valence electron count for A, B, X sites) **plus an optional simple structural descriptor (Goldschmidt tolerance factor) when lattice data are available**, using `pymatgen`, (3) train baseline Random Forest and Gradient Boosting regressors with 5‑fold **stratified** cross‑validation on a CPU‑only runner, (4) evaluate the best model on a held‑out test split, reporting RMSE, MAE, R², a bootstrapped 95 % CI for RMSE, and a paired two‑sided t‑test p‑value > 0.05, (5) produce feature‑importance rankings and scatter‑plot visualisations, and (6) document everything in a reproducible Jupyter notebook.  

**Descriptor Limitation** – The twelve compositional descriptors capture bulk chemical trends but omit detailed local structural/electronic information (e.g., octahedral tilting, band‑edge states). The optional Goldschmidt tolerance factor is included when lattice parameters exist. If baseline performance does not meet the RMSE target, future work will explore richer structural features (e.g., crystal graph convolutions) **outside the current scope**.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pymatgen`, `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `pytest` (for contract tests)  
- **Storage**: Flat files under `data/` (raw CSV, engineered CSV, model artefacts)  
- **Testing**: `pytest` with contract schemas in `contracts/`  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM) – **CPU‑first** execution; no GPU required.  
- **Project Type**: Research notebook / library style code under `src/`  
- **Performance Goals**: Complete end‑to‑end run ≤ 6 h on the free‑tier CI runner; memory ≤ 6 GB.  
- **Constraints**: Must run without CUDA; random seeds pinned in `code/`.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All code, random seeds, and data‑download steps are scripted; the notebook can be re‑executed from a fresh runner. |
| II. Verified Accuracy | No external literature citations are introduced beyond the Materials Project API (a standard, publicly documented source). |
| III. Data Hygiene | Raw CSV is checksum‑verified; every transformation writes a new file with a provenance note. |
| IV. Single Source of Truth | Every figure/table is generated directly from the artefacts produced in the pipeline; no manual transcription. |
| V. Versioning Discipline | Artefacts are referenced by content hash in `state/projects/...yaml`. |
| VI. Computational Cost & Descriptor Parsimony | Only twelve compositional descriptors (plus optional tolerance factor) are required; the optional descriptor is lightweight and added only when available. |
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
│   ├── train.py             # CV training for RF & GB (StratifiedKFold, class_weight='balanced')
│   └── evaluate.py          # held‑out test evaluation, stats, plots
└── utils/
    ├── logger.py
    └── contracts.py         # validation helpers
```

## Implementation Phases (mapping FRs & SCs)

| Phase | Tasks (linked to FR / SC) | Output |
|-------|---------------------------|--------|
| **0 Data Strategy** | *FR‑001* – Verify availability of the Materials Project defect dataset. Since the API requires a key (non‑open), the pipeline will **require the user to supply a pre‑downloaded CSV** at `data/raw/materials_defects.csv`. If an API key is present (`MP_API_KEY` env var), `download.py` will attempt automatic retrieval; otherwise it aborts with a clear error. <br> *FR‑006* – Validate that each row contains all required descriptors; missing rows are logged and dropped. <br> *FR‑007* – Detect empty result set and abort with “No data found for specified filters.” | `data/raw/materials_defects.csv` (checksum recorded) |
| **1 Feature Engineering** | *FR‑002* – `featurize.py` iterates over each composition, uses `pymatgen` to extract atomic radii, Pauling electronegativity, oxidation state, and valence electron count for A, B, X sites → 12 columns. **Additionally**, if lattice parameters are present, compute the Goldschmidt tolerance factor as a single optional structural descriptor. <br> *FR‑008* – Rows where oxidation states cannot be determined are excluded; count logged. | `data/processed/features.csv` (12–13 descriptor columns + target) |
| **2 Dataset Validation & Power Analysis** | *FR‑009* – Verify that `features.csv` contains ≥ 50 rows; raise `ValueError` otherwise. <br> *SC‑005* – Ensure ≥ 500 valid rows; if not, log a warning and note reduced statistical power. <br> **Power analysis**: Assuming an expected RMSE improvement of 0.1 eV and a standard deviation of ~0.3 eV, a sample of 500 gives > 80 % power at α = 0.05 (computed via a two‑sample t‑test approximation). If fewer rows are available, the plan will report the power limitation. | Validation log |
| **3 Model Training** | *FR‑003* – `train.py` runs **5‑fold stratified cross‑validation** (`StratifiedKFold` by A‑site element) for Random Forest and Gradient Boosting (scikit‑learn, `n_jobs=1`, `class_weight='balanced'`). <br> *SC‑004* – Execution on CPU‑only runner; time measured. | `models/rf_cv.pkl`, `models/gb_cv.pkl`, `data/processed/cv_metrics.json` |
| **4 Model Selection & Test Split** | *FR‑011* – Randomly split the original dataset (seeded) into an 80/20 **stratified** train‑test split by A‑site element, ensuring no overlap with CV folds. <br> *FR‑004* – `evaluate.py` loads the best CV model (lowest mean RMSE) and predicts on the held‑out set. |
| **5 Performance Evaluation** | *FR‑004* – Compute RMSE, MAE, R²; bootstrap 10 000 resamples for 95 % CI of RMSE; paired two‑sided t‑test (α = 0.05) comparing predictions vs. DFT values. <br> *SC‑001* – RMSE compared to the < 0.5 eV target (deferred). <br> *SC‑002* – R² compared to ≥ 70 % target (deferred). <br> *SC‑003* – Report p‑value > 0.05 for “no bias”. |
| **6 Feature Importance & Visualisation** | *FR‑005* – Extract `feature_importances_` from the best model, rank, and plot bar chart. <br> *FR‑005* – Generate scatter plot of predicted vs. actual energies with a 1:1 reference line. |
| **7 Documentation & Contract Validation** | *FR‑010* – All steps are captured in `pipeline.ipynb`; the notebook is executable end‑to‑end and produces the CSVs, model artefacts, JSON report, and PNG figures. **Contract validation** (schema checks) is performed inside the notebook as part of the documentation workflow, satisfying reproducibility and data‑hygiene requirements without a separate phase. |
| **8 Quickstart Generation** | *FR‑010* – Provide concise CLI commands in `quickstart.md` to run the notebook or individual scripts. This is considered part of the documentation deliverable required by FR‑010. |

## Edge‑Case Handling (explicitly addressed)
- Empty API result → abort with “No data found for specified filters.” (FR‑007).  
- Missing oxidation states → rows dropped, count logged (FR‑008).  
- Insufficient samples for 5‑fold CV → raise `ValueError` with guidance to broaden filters (FR‑009).  
- Composition‑class imbalance → stratified CV, stratified train‑test split, and class‑weighting (addressed in Phase 3 and Phase 4).  

## Timeline (approximate)
| Week | Milestone |
|------|-----------|
| 1 | Implement data‑download fallback, checksum, and validation (Phase 0). |
| 2 | Feature engineering pipeline, unit tests for descriptor extraction (Phase 1). |
| 3 | CV training scripts, CPU‑only benchmarking (Phase 3). |
| 4 | Held‑out evaluation, statistical analysis, visualisation (Phase 5). |
| 5 | Notebook integration, contract schemas, quickstart doc (Phase 7). |
| 6 | Full CI run, bug‑fixes, final reproducibility check. |

---



