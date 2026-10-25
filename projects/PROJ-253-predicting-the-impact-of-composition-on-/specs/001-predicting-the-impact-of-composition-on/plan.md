# Implementation Plan: Predicting the Impact of Composition on the Band Gap of Perovskite Materials

**Branch**: `001-predicting-composition-band-gap` | **Date**: 2026-10-25 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-predicting-composition-band-gap/spec.md`

## Summary
The pipeline must (1) acquire an open perovskite dataset via the Materials Project API (or a Zenodo mirror) and verify that it contains ≥ 500 ABX₃ entries, (2) generate ≥ 5 composition‑only descriptors (mean/variance of electronegativity, atomic radius, ionization energy, oxidation‑state variance, Goldschmidt tolerance factor, octahedral factor) using `matminer`, (3) enforce strict physical band‑gap bounds (0 < gap < 6 eV) and log/exclude invalid entries, (4) split the cleaned data into stratified train/val/test sets, (5) train Random Forest and Gradient Boosting regressors with k‑fold cross‑validation hyper‑parameter tuning (including learning‑rate for GB), (6) evaluate RMSE, MAE, R² on a held‑out test set and compare against a mean‑baseline using a bootstrap paired test with Bonferroni correction, (7) interpret the best model with SHAP (global summary and top‑few descriptor ranking), (8) validate ranking ability on an external experimental NREL dataset via Spearman correlation (annotating p‑value when N < 10) **and compute observed power for the Spearman test**, (9) sweep prediction‑error thresholds {0.30, 0.35, 0.40 eV} to compute false‑negative rates for lead‑free identification, and (10) refit a model using only the top‑5 descriptors to verify that its R² ≥ 0.8 × full‑model R². All steps are fully reproducible, CPU‑first, and respect the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matminer`, `shap`, `datasets`, `huggingface_hub`, `scipy`, `tqdm`, `statsmodels`  
- **Storage**: Files under `data/` (raw parquet or CSV, processed CSV, model artefacts) and `results/` (JSON metrics, figures).  
- **Testing**: `pytest` + JSON‑Schema contract validation (`contracts/processed_dataset.schema.yaml`).  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, ≤6 h).  
- **Constraints**: CPU‑first; no GPU‑only components. All external datasets are open and directly downloadable via the verified URLs listed in the spec.  
- **Scale/Scope**: Minimum 500 perovskite entries after filtering; ≥ 20 experimental entries for external validation.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed random seeds (`np.random.seed(42)`, `random_state=42`); deterministic data download URLs; single `run_all` script orchestrates the pipeline; no manual steps. |
| II. Verified Accuracy | All citations limited to the verified dataset URLs (see `research.md`). No unverified sources introduced. |
| III. Data Hygiene | Raw files are checksum‑verified; each transformation writes a new file with a provenance suffix; no in‑place mutation. |
| IV. Single Source of Truth | Every figure/table in the eventual paper will be generated directly from artefacts produced by this pipeline (CSV, JSON, PNG). |
| V. Versioning Discipline | Artefacts are named with SHA‑256 hash suffixes; `state/projects/.../artifact_hashes` will be updated automatically. |
| VI. Composition‑Only Descriptor Fidelity | Only elemental properties from `matminer` and stoichiometry‑derived tolerance/octahedral factors are used; no crystal‑structure inputs. |
| VII. Physical Validity & DFT‑Experimental Decoupling | Band‑gap filtering enforces `0 < gap < 6 eV`; external validation uses the NREL experimental set exclusively. |

## Project Structure
```text
specs/001-predicting-composition-band-gap/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── processed_dataset.schema.yaml
└── tasks.md               # generated later by /speckit-tasks

src/
├── pipeline/
│   ├── __init__.py
│   ├── download.py          # FR‑001, FR‑009
│   ├── preprocess.py        # FR‑003, FR‑010
│   ├── featurize.py         # FR‑002, FR‑012 (standardization added)
│   ├── split_scale.py       # FR‑013, FR‑012
│   ├── train.py             # FR‑004, FR‑014
│   ├── evaluate.py          # FR‑005 (bootstrap, correction)
│   ├── interpret.py         # FR‑006
│   ├── external_validate.py # FR‑007, FR‑011, power analysis
│   ├── sensitivity.py       # FR‑008
│   └── top5_refit.py        # FR‑016
└── utils/
    └── logging.py

tests/
├── contract/
│   └── test_processed_dataset.py   # schema validation
└── unit/
    └── test_*.py
```
**Structure Decision**: A single‑project layout (`src/`) suffices because the feature is a self‑contained data‑science pipeline; no web, mobile, or service components are required.

## Complexity Tracking
No constitution violations identified; all required principles are satisfied with the chosen design.

## Planned Phases & Tasks (FR/SC Mapping)

| Phase | Tasks (FR IDs) | Output | SC IDs addressed |
|-------|----------------|--------|-------------------|
| **0 – Data Acquisition** | FR‑001 (download via Materials Project API or Zenodo mirror), FR‑009 (log missing‑element warnings), **verify ≥ 500 ABX₃ entries after filtering** | `data/raw/*.parquet` or `data/raw/zenodo_perovskite.csv` | — |
| **1 – Preprocessing & Filtering** | FR‑003 (band‑gap bounds), FR‑010 (metallic warnings) | `data/processed/pre_filtered.parquet` | — |
| **2 – Feature Engineering & Standardization** | FR‑002 (matminer descriptors), **Standardize descriptors using the training‑set scaler before model training** (FR‑012) | `data/processed/perovskite_features.csv` | — |
| **3 – Train/Val/Test Split** | FR‑013 (stratified split) | `data/splits/train.csv`, `val.csv`, `test.csv` | — |
| **4 – Model Training & Hyper‑parameter Tuning** | FR‑004, FR‑014 (learning‑rate grid) | `models/rf_best.pkl`, `models/gb_best.pkl` | — |
| **5 – Baseline & Significance Testing** | FR‑005 (bootstrap paired test, Bonferroni correction) | `results/evaluation.json` | SC‑001, SC‑002 |
| **6 – Model Evaluation** | FR‑005 (metrics: RMSE, MAE, R²) | `results/summary.json` (contains RMSE, MAE, R²) | SC‑001 |
| **7 – Interpretation** | FR‑006 (SHAP summary, top‑5 ranking) | `figures/shap_summary.png`, `results/top5_importance.json` | — |
| **8 – External Validation & Power Analysis** | FR‑007, FR‑011 (Spearman ρ, annotate p‑value), **compute observed power for the Spearman test** | `results/external_validation.json` | SC‑003 |
| **9 – Sensitivity Analysis** | FR‑008 (error‑threshold sweep) | `results/sensitivity.csv` | SC‑004 |
| **10 – Top‑5 Descriptor Refitting** | FR‑016 (refit R² ≥ 0.8 × full) | `results/top5_refit.json` | SC‑005 |

All phases execute sequentially on the CI runner; each step writes its artefacts to disk, enabling downstream tasks to read without recomputation.