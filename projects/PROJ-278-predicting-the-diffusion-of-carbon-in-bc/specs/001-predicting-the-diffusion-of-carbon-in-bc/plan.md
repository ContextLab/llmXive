# Implementation Plan: Predicting the Diffusion of Carbon in BCC Metals from Compositional Data

**Branch**: `001-predict-carbon-diffusion-bcc` | **Date**: 2026-07-13 | **Spec**: `/specs/001-predicting-carbon-diffusion-bcc/spec.md`
**Input**: Feature specification from `/specs/001-predicting-carbon-diffusion-bcc/spec.md`

## Summary

This project implements a computational pipeline to predict carbon diffusion coefficients in Body-Centered Cubic (BCC) metals using **only** compositional data (atomic fractions, derived descriptors) and temperature. The primary requirement is to isolate the predictive power of bulk composition by strictly filtering out microstructural variables. The technical approach involves ingesting raw data from NIST and Materials Project (via verified HuggingFace mirrors), filtering for BCC structure, engineering descriptors (atomic radius variance, VEC, electronegativity spread, `1/T`), training ensemble and linear models (Random Forest, XGBoost, Elastic Net) under strict CPU constraints, and quantifying the "microstructural gap" via adjusted $R^2$ and SHAP analysis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `xgboost`, `shap`, `pymatgen`, `requests`, `pyarrow`  
**Storage**: Local CSV/JSON artifacts (`data/`, `code/outputs/`)  
**Testing**: `pytest` with contract validation against `contracts/` schemas  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 CPU, ~7 GB RAM, no GPU)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Total runtime ≤ 6 hours; Memory usage < 6 GB; Model training < 2 hours  
**Constraints**: No GPU usage; No heavy LLM inference; Data must be log-transformed before modeling (FR-003, Constitution Principle VI); Strict exclusion of non-BCC phases and entries lacking provenance flags.  
**Scale/Scope**: Dataset size unknown a priori (assumed < 10k rows based on niche domain); Model complexity limited to hyperparameter combinations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds in `code/`, and deterministic data fetching from verified HuggingFace URLs. |
| **II. Verified Accuracy** | **PASS** | All dataset references in `research.md` are restricted to the "Verified datasets" block. Phase 0 includes a `Reference-Validator` step to verify the URL against the primary source. |
| **III. Data Hygiene** | **PASS** | Plan requires checksums for all raw data in `state/` and immutable raw data storage in `data/raw/`. |
| **IV. Single Source of Truth** | **PASS** | All metrics in the final report will be generated programmatically from `data/processed/` and `code/`. |
| **V. Versioning Discipline** | **PASS** | Artifacts will be versioned via content hashes in `state/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc.yaml`. The Advancement-Evaluator will invalidate stale records when this file is updated. |
| **VI. Numerical-Stability** | **PASS** | Plan explicitly mandates $\log_{10} D$ transformation prior to any model fitting (FR-003, Constitution Principle VI). |
| **VII. Composition-Isolation** | **PASS** | Pipeline includes a strict filter for `structure == "BCC"`, exclusion of entries missing provenance flags, and exclusion of microstructural descriptors from feature sets. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-carbon-diffusion-bcc/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/
├── data/
│   ├── raw/               # Downloaded parquet/jsonl files (immutable)
│   ├── processed/         # Cleaned CSVs, feature-engineered data
│   └── checksums.txt      # SHA256 hashes of raw files
├── code/
│   ├── 01_download.py     # Fetches data from verified HuggingFace URLs
│   ├── 02_preprocess.py   # Filters BCC, validates provenance, computes descriptors, log-transforms
│   ├── 03_train.py        # Trains RF, XGBoost, Elastic Net with grid search
│   ├── 04_evaluate.py     # SHAP analysis, permutation tests, variance partitioning
│   ├── utils.py           # Helper functions for descriptor calculation
│   └── requirements.txt   # Pinned dependencies
├── tests/
│   ├── test_preprocess.py
│   └── test_contracts.py  # Validates outputs against schema files in contracts/
└── docs/                  # Paper drafts and reports
```

**Structure Decision**: Single project structure with a linear pipeline (download → preprocess → train → evaluate). This minimizes I/O overhead and ensures the entire workflow fits within the available CI window..

## Phase Breakdown

### Phase 0: Data Acquisition & Validation
1.  **Download**: Fetch `MeLiDC` parquet from the verified URL.
2.  **Verify**: Run `Reference-Validator` to confirm the URL matches the primary NIST/Materials Project source (Constitution Principle II).
3.  **Checksum**: Generate SHA256 hash and store in `data/checksums.txt`.
4.  **Schema Check**: Verify the downloaded file contains required columns: `composition`, `structure`, `diffusion_coefficient`, `temperature`, and `microstructure_controlled` (or equivalent provenance flag). If missing, raise `DataInsufficientError`.

### Phase 1: Preprocessing & Feature Engineering
1.  **Filter**: Select rows where `structure == "BCC"` and `solute == "C"`.
2.  **Provenance Validation (FR-008)**: Exclude any entry where `microstructure_controlled` or `single_crystal` flag is missing or false. Log excluded entries.
3.  **Transform**: Apply $\log_{10}$ to `diffusion_coefficient` (FR-003, Constitution Principle VI).
4.  **Feature Engineering**: Compute `atomic_radius_variance`, `VEC`, `electronegativity_spread`, `mixing_entropy`, and `inv_temperature` (1/T).
5.  **Normalize**: Ensure atomic fractions sum to 1.0.
6.  **Output**: Save `dataset_cleaned.csv` and validate against `contracts/dataset.schema.yaml`.

### Phase 2: Model Training & Evaluation
1.  **Split**: If $N \ge 30$, use 80/20 split. If $N < 30$, switch to Leave-One-Out Cross-Validation (LOOCV) and emit `PowerWarning`.
2.  **Train**: Train Random Forest, XGBoost, and Elastic Net models with a constrained grid search (a limited set of combinations).
3.  **Evaluate**: Calculate $R^2$, RMSE, MAE on the test set (or LOOCV average).
4.  **Permutation Test (FR-005)**: Perform a permutation test with a sufficient number of iterations to ensure robust statistical inference. comparing the best ML model against a linear baseline (Elastic Net) to generate a p-value.
5.  **Output**: Save `model_results.json` and validate against `contracts/model_output.schema.yaml`.

### Phase 3: Interpretation & Reporting
1.  **SHAP Analysis**: Generate SHAP values to rank descriptors.
2.  **Variance Partitioning**: Calculate adjusted $R^2$ as the upper bound of composition-explainable variance. Explicitly note that residual variance includes measurement error, missing descriptors, and microstructural effects (not just microstructure).
3.  **Output**: Save `feature_importance.json` and `variance_partition.csv`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The scope is constrained to a single scientific question with a limited dataset. | N/A |