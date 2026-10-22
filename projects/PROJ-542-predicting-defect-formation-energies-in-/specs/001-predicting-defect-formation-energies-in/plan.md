# Implementation Plan: Predicting Defect Formation Energies in Perovskites

**Branch**: `001-predicting-defect-formation-energies` | **Date**: 2026-10-22 | **Spec**: [spec.md]  
**Input**: Feature specification from `specs/001-predicting-defect-formation-energies/spec.md`

## Summary
The project must (1) obtain a perovskite oxygen‑vacancy defect formation‑energy dataset (via Materials Project API *or* a user‑provided CSV), (2) compute twelve compositional descriptors for the A, B, X sites using `pymatgen`, (3) verify dataset completeness and size (≥ 500 rows for primary analysis, with a hard minimum of 50 rows for any 5‑fold CV), (4) create a non‑overlapping train‑test‑validation split, (5) train baseline Random Forest and Gradient Boosting regressors with 5‑fold GroupKFold cross‑validation, (6) evaluate the best‑performing model on a held‑out test set, (7) optionally integrate captured confounder metadata as covariates, (8) generate a ranked list of feature importances and visualisations, (9) document the entire workflow in a reproducible Jupyter notebook, (10) enforce a total wall‑clock budget ≤ 30 minutes on a free‑tier GitHub Actions runner, (11) automatically fall back to structural descriptors if baseline compositional models do not meet **RMSE ≤ 0.5 eV** *and* **R² ≥ 70 %**, and (12) record SHA‑256 hashes of all artifacts in the project state file.

### Power‑analysis justification
A two‑sample t‑test with α = 0.05, an expected effect size corresponding to an RMSE of 0.5 eV, and a target variance‑explained of [deferred] requires roughly **500 independent compositions** to achieve > 80 % power. This calculation informs both the **≥ 500‑sample** primary‑analysis requirement (SC‑005) and the **RMSE ≤ 0.5 eV / R² ≥ 70 %** success thresholds (SC‑001, SC‑002). If the dataset contains fewer than 500 samples but at least 50, the pipeline will still run, but a power‑size warning will be logged and the results will be flagged as under‑powered.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pymatgen`, `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `statsmodels`, `tqdm`, `jupyter`, `pytest`, `jsonschema`  
- **Storage**: Flat files under `data/` (CSV, JSON) and `models/` (pickle)  
- **Testing**: `pytest` with JSON‑Schema contracts in `contracts/`  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, CPU‑only) – **CPU‑first** execution.  
- **Constraints**: No CUDA/GPU usage; random seeds pinned (`random_state=42`).  
- **Scale/Scope**: Aim for ≥ 500 valid compositions; if fewer are available, the pipeline runs with a warning and a power‑size disclaimer (the results are flagged as under‑powered but still produced).

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Deterministic seeds, end‑to‑end notebook (`pipeline.ipynb`), and checksum verification after each artifact. |
| II. Verified Accuracy | Only the Materials Project API (public) and `pymatgen` internal tables are used. No uncited literature. |
| III. Data Hygiene | Raw CSV and every derived file receive a SHA‑256 checksum; transformations write new files; no in‑place mutation. |
| IV. Single Source of Truth | All figures and metrics are generated from the files recorded in `state/projects/PROJ‑542‑…yaml`. |
| V. Versioning Discipline | After each artifact is written, its SHA‑256 hash is appended to `state/projects/PROJ‑542‑…yaml`, triggering version updates. |
| VI. Computational Cost & Descriptor Parsimony | Baseline uses only twelve compositional descriptors and lightweight tree models; structural descriptors are added **only** if baseline fails to meet the RMSE ≤ 0.5 eV and R² ≥ 70 % thresholds (FR‑012). |
| VII. Statistical Rigor | Evaluation includes RMSE, MAE, R², bootstrap CI for RMSE, and a paired two‑sided t‑test (α = 0.05). The t‑test is reported for bias inspection only; primary success criteria are RMSE ≤ 0.5 eV and R² ≥ 70 % (justified by the power analysis above). |
| VIII. Confounder Awareness | Metadata (DFT functional, calculation settings, temperature, pressure) is captured from the Materials Project response (`metadata.json`) and **optionally** added as extra covariates during model training (Phase 7). This satisfies the methodological concern about uncontrolled confounders. |

## Project Structure
```text
specs/001-predicting-defect-formation-energies/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── raw_dataset.schema.yaml
│   ├── features.schema.yaml
│   └── model_performance.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
src/
├── data/
│   ├── download.py          # Materials Project API fetch or CSV fallback; aborts with FR‑007 if no data.
│   ├── checksum.py          # SHA‑256 utility; creates checksum files after each artifact.
│   ├── featurize.py         # Descriptor computation + gap logging (FR‑006) + oxidation‑state filtering (FR‑008).
│   ├── validate.py          # Size & completeness checks (≥ 500 rows for primary analysis; ≥ 50 rows for any CV). Logs power‑size warnings.
│   ├── split.py             # Stratified GroupShuffleSplit (group = composition) → train.csv, test.csv, validation.csv; guarantees no overlap (FR‑011). |
│   ├── metadata.py          # Extracts DFT functional, calculation settings, temperature, pressure from MP metadata; writes `metadata.json`. |
│   └── logger.py            # Consistent logging.
├── models/
│   ├── train.py             # 5‑fold GroupKFold CV for RF & GB (CPU‑only). Writes cv_metrics.json and model pickles.
│   ├── evaluate.py          # Held‑out test, bootstrap CI, paired t‑test, feature importance; writes performance.json & figures.
│   ├── fallback.py          # Augments features with structural descriptors (if needed) and retrains using the **validation.csv** as held‑out set.
│   └── confounder_integration.py # OPTIONAL: merges `metadata.json` fields as additional numeric/categorical features for model training when present.
└── pipeline.ipynb           # Orchestrator notebook.
```

## Implementation Phases (mapping FRs & SCs)

| Phase | Tasks (FR / SC) | Output |
|-------|-----------------|--------|
| **0 Data Acquisition** | *FR‑001* – `download.py` attempts Materials Project API using `MP_API_KEY`. If the key is missing **or** the API returns an empty result **and** a user‑provided CSV exists at `data/raw/materials_defects.csv`, the script proceeds with the CSV; otherwise it aborts with `"No data found for specified filters."` (FR‑007). <br>*FR‑006* – Verify required columns (`composition`, `defect_type`, `formation_energy`). Missing columns cause abort. <br>*FR‑007* – Empty result handling as above. <br>*Confounder capture* – `metadata.py` extracts any available DFT functional, calculation settings, temperature, and pressure from the MP response and writes them to `data/raw/metadata.json`. <br>*Contract* – Validate raw CSV against `contracts/raw_dataset.schema.yaml`. | `data/raw/materials_defects.csv`, `data/raw/metadata.json`, `data/checksums/raw_defects.sha256` |
| **1 Feature Engineering** | *FR‑002* – `featurize.py` parses each composition with `pymatgen` to compute atomic radius, Pauling electronegativity, oxidation state, and valence electron count for A, B, X → 12 descriptor columns + `formation_energy`. <br>*FR‑006* – Any descriptor that cannot be retrieved is recorded in `descriptor_gaps.log`; the script aborts if gaps exist. <br>*FR‑008* – Rows where oxidation states are indeterminate are dropped; count logged. <br>*Checksum* – `checksum.py` creates `data/checksums/features.sha256`. | `data/processed/features.csv`, `data/processed/featurize.log`, `data/processed/descriptor_gaps.log`, `data/checksums/features.sha256` |
| **2 Dataset Validation** | *FR‑009* – `validate.py` enforces a **hard minimum of 50 samples** for any 5‑fold CV (raises `ValueError` if not met). It then checks whether **≥ 500 samples** are present; if not, a **power‑size warning** is logged (but the pipeline continues). The warning references the power‑analysis justification above. <br>*SC‑005* – Logs whether the dataset meets the ≥ 500‑sample target. | `data/processed/validation.log` |
| **3 Train‑Test‑Validation Split** | *FR‑011* – `split.py` performs an 80/20 train‑test split **and** creates a [deferred] validation subset (used only for fallback) **by composition group** using `GroupShuffleSplit` (seed = 42). No composition appears in more than one split. <br>*Checksum* – SHA‑256 for `train.csv`, `test.csv`, `validation.csv`. | `data/processed/train.csv`, `data/processed/test.csv`, `data/processed/validation.csv`, `data/processed/split.log`, `data/checksums/train.sha256`, `data/checksums/test.sha256`, `data/checksums/validation.sha256` |
| **4 Model Training (Cross‑Validation)** | *FR‑003* – `train.py` runs **5‑fold GroupKFold** CV on `train.csv` for Random Forest (`n_estimators=200`) and Gradient Boosting (`n_estimators=200`). <br>*SC‑001* – Writes mean ± std RMSE, MAE, R² per model to `cv_metrics.json`. <br>*Edge* – Abort with clear error if fewer than 5 composition groups exist. | `models/rf_cv.pkl`, `models/gb_cv.pkl`, `data/processed/cv_metrics.json`, `data/checksums/cv_metrics.sha256` |
| **5 Model Selection & Held‑Out Evaluation** | *FR‑004* – Select model with lowest mean CV RMSE. <br>*FR‑004* – `evaluate.py` predicts on `test.csv`, computes RMSE, MAE, R². <br>*FR‑004* – Bootstrap a large number of resamples (e.g., 10 000) for a 95 % confidence interval on RMSE. <br>*FR‑004* – Paired two‑sided t‑test (α = 0.05) comparing predictions vs. DFT values; the p‑value is reported for bias inspection only. <br>*SC‑004* – Record total wall‑clock time; abort if > 30 min. <br>*Decision* – If **RMSE ≤ 0.5 eV** **and** **R² ≥ 70 %**, accept; otherwise trigger Phase 6 fallback. | `data/processed/performance.json`, `figures/pred_vs_actual.png`, `figures/feature_importance.png`, `data/checksums/performance.sha256` |
| **6 Fallback Augmentation** | *FR‑012* – If Phase 5 decision rule fails, `fallback.py` recomputes `features.csv` adding structural descriptors (coordination number, average bond length, crystal symmetry) **using the optional `structure_cif` column** from the raw dataset (if present). New checksum recorded (`features_augmented.sha256`). Then Phases 4‑5 are re‑executed **using `validation.csv` as the held‑out set** to avoid re‑using the original test set. | `data/processed/features_augmented.csv`, `data/checksums/features_augmented.sha256`, refreshed `performance.json`, updated figures, updated checksums |
| **7 Confounder Integration (optional)** | If `metadata.json` contains numeric or categorical fields (e.g., DFT functional encoded as one‑hot, temperature, pressure), `confounder_integration.py` merges them into the training matrix. The same optional feature set is used in both baseline and fallback training runs, enabling assessment of whether controlling for these confounders improves RMSE/R². Logging records which confounders were added. | Updated training matrices (same filenames, new checksum entries), `data/checksums/confounders_integration.sha256` |
| **8 Documentation & Contract Validation** | *FR‑010* – All steps are orchestrated in `pipeline.ipynb`; the notebook can be executed end‑to‑end on a fresh runner. <br>*Contract validation* – After each artifact is written, `jsonschema.validate` is called against the appropriate contract (`raw_dataset.schema.yaml`, `features.schema.yaml`, `model_performance.schema.yaml`). <br>*Testing* – `pytest -q` runs a suite that checks checksums and schema compliance. | Executable notebook, passing test suite |
| **9 Runtime & Logging** | *SC‑004* – `utils/logger.py` timestamps each stage; the total runtime is written to `runtime.log`. If the budget is exceeded, the pipeline aborts with a clear error message. | `runtime.log` |

## Edge‑Case Handling (explicitly addressed)
- **Empty API result** → abort with “No data found for specified filters.” (FR‑007) **unless** a user CSV is present, in which case the pipeline proceeds with the CSV.  
- **Missing oxidation states** → rows dropped, count logged (FR‑008).  
- **Insufficient samples for 5‑fold CV** → raise `ValueError` with guidance (FR‑009).  
- **Baseline performance failure** → automatic fallback to structural descriptors (FR‑012); fallback evaluation uses the independent `validation.csv` to avoid optimistic bias.  
- **Descriptor gaps** → `descriptor_gaps.log` records any missing descriptor; pipeline aborts if gaps exist (FR‑006).  
- **Runtime budget breach** → pipeline aborts with a runtime‑exceeded error (SC‑004).  
- **Potential confounders** → DFT functional, calculation settings, temperature, and pressure are captured in `metadata.json` (via `metadata.py`). When present, they are optionally merged as covariates in Phase 7. This satisfies the methodological concern about uncontrolled confounders.  
- **Collinearity** → A Pearson correlation matrix of the twelve descriptors is logged; feature importance is interpreted descriptively, not as independent causal effects.  

## Statistical Rigor Checklist
- **Multiple comparisons**: Only two models are compared; family‑wise error correction is unnecessary (SC‑002).  
- **Power justification**: See **Power‑analysis justification** above; ≥ 500 samples give > 80 % power for the target effect size.  
- **Causal inference**: Work is purely predictive/associational; no causal statements are made (causal‑inference disclaimer).  
- **Measurement validity**: Targets are DFT‑computed defect formation energies from the Materials Project, a widely accepted computational source.  
- **Collinearity**: Descriptors may be correlated; a Pearson correlation matrix will be logged; feature importance is interpreted descriptively, not as independent effects.  

## Causal‑Inference Disclaimer
The analyses performed in this project are **strictly predictive and associational**. No causal statements about how compositional or structural changes *cause* variations in defect formation energy are made. All conclusions are limited to the observed correlations within the DFT‑derived dataset.

## Timeline (approximate)

| Week | Milestone |
|------|-----------|
| 1 | Implement `download.py`, `checksum.py`, and raw‑dataset contract; generate raw CSV or abort. |
| 2 | Build `featurize.py` with gap reporting; produce `features.csv`. |
| 3 | Write `validate.py` (dual‑threshold logic), `split.py`, and generate checksums. |
| 4 | Implement `train.py` (GroupKFold CV) and `evaluate.py` (bootstrap CI, t‑test, feature importance). |
| 5 | Assemble `pipeline.ipynb`, add contract validation calls, and create `checksum_all.py`. |
| 6 | Full CI run, debugging, and verification of all contracts; implement fallback augmentation and optional confounder integration. |
| 7 | Polish documentation, quickstart guide, and final reproducibility audit. |

---


