# Implementation Plan: Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel

**Branch**: `001-predicting-impact-of-additive-manufacturing-parameters-on-porosity` | **Date**: 2026-06-24 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predicting-impact-of-additive-manufacturing-parameters-on-porosity/spec.md`

## Summary

This project implements a computational pipeline to predict porosity in 316L Stainless Steel parts produced via Laser Powder Bed Fusion (LPBF). The approach involves downloading a verified public LPBF 316L dataset, preprocessing numerical features (imputation, normalization), engineering a derived Volumetric Energy Density feature, and training two regression models (Gradient Boosting and MLP) using k-fold cross-validation. The pipeline concludes with SHAP-based explainability (via model bootstrapping) and statistical significance testing (via feature permutation tests) to identify key process parameters, all executed within CPU-only constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `shap`, `matplotlib`, `seaborn`, `pyyaml`, `jsonschema`  
**Storage**: Local CSV/Parquet files in `data/`, model artifacts (`.pkl`) in `models/`, plots in `results/`  
**Testing**: `pytest` for unit tests on preprocessing logic and contract validation  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, ~7GB RAM)  
**Project Type**: Data Science Pipeline / Research Script  
**Performance Goals**: Complete full pipeline (download to plot) within 6 hours; Memory usage < 7GB  
**Constraints**: No GPU; No 8-bit quantization; No large LLMs; Strict column mapping for datasets; No multicollinearity in model inputs (raw vs. derived).  
**Scale/Scope**: Single dataset analysis; Regression focus; 2 models; 5-fold CV.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Plan mandates pinned random seeds, explicit `requirements.txt`, and fetch from canonical URLs. |
| **II. Verified Accuracy** | **Compliant** | **Hard Gate**: The `Reference-Validator` agent must verify the dataset URL against the "Verified Datasets" block and confirm material type (316L) before any download. If the URL is not in the block or material mismatches, the pipeline halts. |
| **III. Data Hygiene** | **Compliant** | Raw data preserved; derived data saved as new files with checksums; no in-place modification. |
| **IV. Single Source of Truth** | **Compliant** | All figures/metrics traced to `data/` and `code/`; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | **Compliant** | **Explicit Step**: After every artifact generation (data, model, plot), the `state/` YAML file will be updated with the new content hash. |
| **VI. Model Validation & Numerical Stability** | **Compliant** | 5-fold CV, RMSE/R² reporting, normalization [0,1], and fixed seeds explicitly planned. |
| **VII. Dataset Provenance & Physical Feature Consistency** | **Compliant** | Derived $E_v$ formula strictly followed; provenance file created; source recorded. |

## Verified Accuracy Gate

Before any code execution (Phase 0), the following check is performed:
1.  Identify the target dataset URL from the "Verified Datasets" block in `research.md`.
2.  Verify the URL is reachable and the file format matches expectations.
3.  **Critical**: Confirm the dataset contains **316L Stainless Steel** porosity data. If the dataset is for a different material (e.g., IN625, Ti64), the project **MUST HALT** with a "Material Mismatch" error. No cross-material transfer learning is permitted.
4.  The `Reference-Validator` agent must verify the URL and material before the download step proceeds.

## Artifact Hashing (Versioning Discipline)

To satisfy Principle V:
1.  After `download_data.py` creates the raw file, compute its SHA-256 hash and record it in `state/...yaml`.
2.  After `preprocess.py` creates the cleaned CSV, compute its hash and update `state/...yaml`.
3.  After model training and plot generation, hash the artifacts and update `state/...yaml`.
4.  The `state/` YAML file is the single source of truth for artifact versions.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-impact-of-additive-manufacturing-parameters-on-porosity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── dataset.schema.yaml
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
projects/PROJ-363-predicting-the-impact-of-additive-manufa/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── download_data.py       # FR-001: Download & checksum
│   ├── preprocess.py          # FR-002, FR-003: Impute, Normalize, Ev calc, Contract Validation
│   ├── train_models.py        # FR-004, FR-005: GB & MLP, 5-fold CV
│   ├── analyze_explainability.py # FR-006, FR-007: SHAP (Bootstrapped), Permutation Test (Feature)
│   └── utils.py               # Helpers, logging, seed setting, state updater
├── data/
│   ├── raw/                   # Downloaded raw files (immutable)
│   └── processed/             # Cleaned CSVs, checksums
├── models/
│   └── artifacts/             # Saved .pkl files
├── results/
│   ├── plots/                 # SHAP, CV curves
│   └── reports/               # JSON metrics, statistical tables
└── tests/
    ├── unit/
    └── contract/
```

**Structure Decision**: Single project structure with clear separation of `code/`, `data/`, and `results/` to support reproducibility and the "Single Source of Truth" principle.

## Contract Enforcement

The `preprocess.py` script includes a validation step that loads `contracts/dataset.schema.yaml` and validates the preprocessed DataFrame against it. If validation fails (e.g., missing columns, wrong types, out-of-range values), the script exits with a clear error message, preventing invalid data from entering the training phase.

## Complexity Tracking

No violations detected. The complexity is managed by:
1.  Strict separation of data acquisition, preprocessing, and modeling.
2.  CPU-only constraints enforced by library selection (`scikit-learn` only).
3.  Explicit handling of collinearity (raw vs. derived features) to prevent model instability.
4.  Contract validation ensures data integrity before modeling.