# Implementation Plan: Predicting the Impact of Composition on the Band Gap of Perovskite Materials

**Branch**: `001-predicting-composition-band-gap` | **Date**: 2026-10-21 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-predicting-composition-band-gap/spec.md`

## Summary
The project must (1) acquire a curated set of perovskite formulas with DFT‑calculated band gaps, (2) transform each formula into ≥ 5 composition‑only descriptors using **matminer**, (3) filter out non‑physical band‑gap values, (4) train composition‑only Random Forest and Gradient Boosting regressors with 5‑fold CV hyper‑parameter tuning, (5) evaluate against a mean‑baseline using bootstrap paired tests with multiple‑comparison correction, (6) interpret models via SHAP and feature‑importance, (7) validate ranking ability on an external experimental NREL dataset, (8) conduct a sensitivity sweep on error‑thresholds for lead‑free identification, and (9) confirm that a model using only the top‑5 descriptors retains ≥ 80 % of full‑model R². All steps are reproducible, CPU‑first, and respect the constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matminer`, `shap`, `huggingface_hub`, `datasets`, `scipy`, `tqdm`, `statsmodels`  
- **Storage**: Files under `data/` (raw parquet/JSON, intermediate CSVs, model artefacts)  
- **Testing**: `pytest` + contract validation (`jsonschema`/`yamale`)  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Project Type**: Research library / CLI pipeline  
- **Performance Goals**: Entire pipeline ≤ 5 h on 2‑core CPU, ≤ 6 GB RAM (streaming/parquet reads)  
- **Constraints**: Must run on CPU; no GPU‑only methods. All external datasets are open and directly downloadable via URLs listed in the “Verified datasets” block.  
- **Scale/Scope**: Minimum 500 perovskite entries; external validation ≥ 20 experimental entries.

## Constitution Check
| Principle | How the plan complies |
|-----------|-----------------------|
| I. Reproducibility | Fixed random seeds (`np.random.seed(42)`, `random_state=42`); full pipeline scripted; data fetched from immutable URLs; no manual steps. |
| II. Verified Accuracy | All citations (datasets, literature) are limited to the verified URLs provided; no unverified sources introduced. |
| III. Data Hygiene | Raw files are checksum‑verified; every transformation writes a new file with a documented provenance field in the filename. |
| IV. Single Source of Truth | Each figure/table in the eventual paper will be generated directly from the CSV/JSON artefacts produced by this pipeline. |
| V. Versioning Discipline | All artefacts are named with SHA‑256 hash suffixes; `state/projects/.../artifact_hashes` will be updated automatically. |
| VI. Composition‑Only Descriptor Fidelity | Only elemental properties from `matminer` and stoichiometry‑derived tolerance/octahedral factors are used; no crystal‑structure inputs. |
| VII. Physical Validity & DFT‑Experimental Decoupling | Band‑gap filtering enforces `0 < gap < 6 eV`; external validation uses the NREL experimental set, never mixed with DFT data. |

## Project Structure
```text
specs/001-predicting-composition-band-gap/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── processed_dataset.schema.yaml
└── tasks.md   # generated later by /speckit-tasks

src/
├── pipeline/
│   ├── __init__.py
│   ├── download.py          # data acquisition
│   ├── preprocess.py        # filtering, cleaning
│   ├── featurize.py         # matminer descriptor generation
│   ├── split_scale.py       # stratified split + standardization
│   ├── train.py             # RF & GB training + CV tuning
│   ├── evaluate.py          # baseline, bootstrap test, metrics
│   ├── interpret.py         # SHAP, feature importance
│   ├── external_validate.py # NREL ranking & Spearman
│   └── sensitivity.py       # threshold sweep for lead‑free FN rate
└── utils/
    └── logging.py

tests/
├── contract/
│   └── test_processed_dataset.py   # schema validation
└── unit/
    └── test_*.py
```
**Structure Decision**: A single‑project layout (`src/`) is sufficient because the feature is a self‑contained data‑science pipeline; no web or mobile components are required.

## Complexity Tracking
*No constitution violations identified; all required principles are satisfied with the chosen design.*

## Planned Phases & Tasks
| Phase | Tasks (maps to FR/SC) | Output |
|-------|-----------------------|--------|
| **0 – Data Acquisition** | FR‑001 (download DFT parquet datasets; filter perovskite formulas), FR‑009 (log missing‑element warnings) | `data/raw/dft.parquet` |
| **1 – Preprocessing & Feature Engineering** | FR‑002 (matminer descriptors), FR‑003 (band‑gap bounds), FR‑010 (metallic warnings), FR‑012 (standardization) | `data/processed/perovskite_features.csv` |
| **2 – Dataset Splitting** | FR‑013 (stratified train/val/test) | `data/splits/*.csv` |
| **3 – Model Training & Hyper‑parameter Tuning** | FR‑004, FR‑014 (learning‑rate tuning) | `models/rf_best.pkl`, `models/gb_best.pkl` |
| **4 – Baseline & Significance Testing** | FR‑005 (bootstrap paired test, multiple‑comparison correction) | `results/evaluation.json` |
| **5 – Model Interpretation** | FR‑006 (SHAP summary, top‑5 importance) | `figures/shap_summary.png` |
| **6 – External Validation** | FR‑007 (Spearman ρ), FR‑011 (annotate p‑value when N < 10) | `results/external_validation.json` |
| **7 – Sensitivity Analysis** | FR‑008 (error‑threshold sweep) | `results/sensitivity.csv` |
| **8 – Top‑5 Descriptor Refitting** | FR‑016 (refit R² ≥ 0.8 × full‑model R²) | `results/top5_refit.json` |
| **9 – Reporting** | SC‑001–SC‑005 (collect all metrics) | `reports/summary.md`, figures, tables |

All phases will be executed sequentially in the CI job; each step writes its artefacts to disk, enabling downstream tasks to read without recomputation.

---
