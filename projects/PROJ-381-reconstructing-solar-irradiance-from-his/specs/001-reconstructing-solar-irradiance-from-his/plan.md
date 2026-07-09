# Implementation Plan: Reconstructing Solar Irradiance from Historical Sunspot Records

**Branch**: `001-reconstruct-solar-irradiance` | **Date**: 2024-05-22
**Spec**: `spec.md`

## Summary
This plan implements a CPU-tractable pipeline to reconstruct Total Solar Irradiance (TSI) from historical Group Sunspot Numbers (GSN). It addresses the core research question regarding cycle-to-cycle variability by training non-linear regression models (Random Forest and Gaussian Process) using 'Cycle Phase' features (sin/cos of day-of-year) instead of categorical Cycle IDs to avoid overfitting on the limited satellite-era data (N=2 cycles). The pipeline validates generalization via Time-Block Cross-Validation (Train: 2003-2015, Test: Subsequent Period), applies the model to pre-satellite data (1610–2002), and rigorously compares results against the 2007 baseline and CMIP6 datasets. All findings are framed as associational, with statistical corrections for multiple comparisons. A dedicated Sensitivity Analysis phase addresses the inconsistency tolerance threshold requirements.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `scipy`, `requests`, `pyyaml`
**Storage**: Local CSV/Parquet files in `data/` (no external DB)
**Testing**: `pytest` (unit tests for data ingestion, integration tests for pipeline phases)
**Target Platform**: Linux (GitHub Actions CPU-only runner: 2 vCPU, 7GB RAM)
**Project Type**: Data Science / Scientific Computing Pipeline
**Performance Goals**: Complete pipeline (ingest, preprocess, train, evaluate, reconstruct) within 6 hours; peak RAM < 7 GB.
**Constraints**: No GPU/CUDA; no large-LLM inference; strict adherence to FR-008 (CPU-only) and FR-009 (sensitivity analysis).
**Scale/Scope**: Time series data from the early instrumental period to present; models trained on satellite-era subset (modern era).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/`. Data fetched from canonical verified URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Compliant** | All citations in `research.md` and `plan.md` mapped to verified dataset URLs. No invented URLs. |
| **III. Data Hygiene** | **Compliant** | Raw data preserved in `data/raw/`. Derivations in `data/processed/`. Checksums recorded in state YAML. |
| **IV. Single Source of Truth** | **Compliant** | All figures/stats trace to `data/processed/` and `code/`. No hand-typed numbers in paper. |
| **V. Versioning Discipline** | **Compliant** | Artifacts hashed; state updated on changes. |
| **VI. Cycle-Specific Calibration** | **Compliant** | Plan explicitly uses 'Cycle Phase' features (sin/cos) to capture variability without overfitting on N=2 cycles. Time-Block CV ensures valid generalization. |
| **VII. Historical Gap Handling** | **Compliant** | Plan includes specific gap-filling logic (GSN=0 for gaps ≥ 1 year) and bootstrap resampling (sufficient iterations) for uncertainty (FR-005). |

## Project Structure

### Documentation (this feature)
```text
specs/001-reconstructing-solar-irradiance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── dataset_schema.schema.yaml
│   └── output_schema.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)
```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants
├── data/
│   ├── __init__.py
│   ├── ingestion.py     # Load GSN, TSI, CMIP6 from HF
│   └── preprocessing.py # Gap filling, cycle detection, feature engineering
├── models/
│   ├── __init__.py
│   ├── train.py         # RF/GP training, Time-Block CV
│   └── predict.py       # Reconstruction generation
├── analysis/
│   ├── __init__.py
│   ├── comparison.py    # Baseline vs. New, Variance tests
│   └── stats.py         # Bootstrap, FDR correction, Sensitivity Analysis
└── main.py              # Orchestration script

tests/
├── __init__.py
├── test_ingestion.py
├── test_preprocessing.py
└── test_model_training.py

data/
├── raw/                 # Downloaded datasets (checksummed)
└── processed/           # Derived datasets
```

**Structure Decision**: Single Python package structure (`code/`) selected for simplicity and ease of CPU-bound execution. No microservices or heavy infrastructure required.

## Phase Execution Order

1.  **Phase 0: Research & Data Verification**
    *   Verify dataset URLs (GSN, TSI, CMIP6) against `research.md`.
    *   Confirm variable availability (GSN, TSI, Cycle Phase).
    *   Define dataset schemas (`contracts/`).

2.  **Phase 1: Data Ingestion & Preprocessing**
    *   Download raw data to `data/raw/`.
    *   Implement gap filling (GSN=0 for gaps ≥ 1 year) per FR-002 (corrected unit).
    *   Detect cycle boundaries (SILSO method) and compute 'Cycle Phase' (sin/cos).
    *   Output `data/processed/preprocessed_data.parquet`.

3.  **Phase 2: Model Training & Validation (User Story 1)**
    *   Train RF and GP models using 'Cycle Phase' features (NOT categorical Cycle ID).
    *   Execute Time-Block Cross-Validation (Train: 2003-2015, Test: Post-2015 period).
    *   Calculate RMSE, R² for the held-out block.
    *   Select best model based on generalization metrics.

4.  **Phase 2.5: Sensitivity Analysis (FR-009, SC-005)**
    *   Sweep 'inconsistency tolerance threshold' over a range of small values.
    *   Measure reconstruction stability and error reduction for each threshold.
    *   Output `sensitivity_report.json`.

5.  **Phase 3: Pre-Satellite Reconstruction (User Story 2)**
    *   Apply trained model to 1610–2002 GSN.
    *   Generate uncertainty bands via prediction intervals.
    *   Perform bootstrap resampling for variance comparison (Maunder/Dalton/Modern).

6.  **Phase 4: Baseline Comparison & Reporting (User Story 3)**
    *   Compare new reconstruction vs. 2007 baseline/CMIP6.
    *   Calculate error reduction (SC-001).
    *   Apply multiple-comparison correction (FR-007).
    *   Generate final report with associational framing (FR-006).

## Compute Feasibility Strategy

*   **Memory**: Data subset to satellite era (present-day) for training (a substantial number of rows). Pre-satellite data processed in chunks or as a single small CSV. Total RAM usage < 2 GB.
*   **CPU**: Random Forest (max_depth=10, n_estimators=100) and Gaussian Process (RBF kernel) are CPU-tractable on 2 cores for <10k rows.
*   **Runtime**: Estimated training time < 30 mins; reconstruction < 10 mins; bootstrap (1000 iters) < 2 hours. Total < 6 hours.
*   **Libraries**: Pin `scikit-learn`, `pandas`, `numpy` to versions with stable CPU wheels. No `torch` or CUDA dependencies.