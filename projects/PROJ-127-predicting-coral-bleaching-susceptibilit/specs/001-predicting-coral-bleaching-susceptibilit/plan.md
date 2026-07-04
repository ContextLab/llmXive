# Implementation Plan: Predicting Coral Bleaching Susceptibility from Environmental Data

**Branch**: `001-predict-coral-bleaching` | **Date**: 2026-06-25 | **Spec**: `specs/001-predict-coral-bleaching/spec.md`
**Input**: Feature specification from `/specs/001-predict-coral-bleaching/spec.md`

## Summary

This project implements a machine learning pipeline to predict coral bleaching susceptibility by integrating heterogeneous oceanographic data (NOAA SST/DHW) with species-level trait data (Coral Trait Database) and bleaching events (ReefBase). The core technical approach involves a spatial hold-out strategy (train on Western Pacific, test on Eastern Pacific) using an XGBoost Gradient Boosting Machine. 

**Critical Constraint**: The pipeline **requires** verified, real-world data for the target variable (bleached) and key predictors (thermal tolerance). If verified sources for the Coral Trait Database or ReefBase are not available in the "Verified datasets" block, the pipeline **will not** generate synthetic data. Instead, it will halt and generate a "Data Gap Report" detailing the missing variables. The project scope is strictly limited to **real data analysis** or an explicit, opt-in "Simulation Mode" (disabled by default) that is clearly labeled as not predicting real-world phenomena.

All components are designed to run on a CPU-only GitHub Actions runner (2 cores, ~7 GB RAM) within 6 hours.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `xgboost`, `scikit-learn`, `pandas`, `geopandas`, `rasterio`, `numpy`, `requests`, `pyyaml`  
**Storage**: Local CSV/Parquet files and GeoTIFFs under `data/`  
**Testing**: `pytest` (unit tests for data ingestion, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Full pipeline execution ≤ 6 hours on CPU; RAM usage ≤ 7 GB via spatial sampling.  
**Constraints**: No GPU; no CUDA; no deep learning frameworks (PyTorch/TensorFlow) for training; all datasets must be fetched from verified sources. **Synthetic data is strictly prohibited for the default scientific run.**  
**Scale/Scope**: Analysis of reef-species units across the Indo-Pacific and Eastern Pacific, limited to available verified dataset rows.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Principle I (Reproducibility)**: **PASS**. The plan mandates pinned random seeds in `code/`, version-locked dataset URLs (from the verified list), and a `requirements.txt` for dependency isolation.
2.  **Principle II (Verified Accuracy)**: **PASS** (Conditional). All dataset references in `research.md` are restricted to the provided "Verified datasets" block. If a required dataset (Coral Trait DB, ReefBase) is missing from the verified list, the plan **FAILS** this check and halts, requiring a scope amendment or data acquisition.
3.  **Principle III (Data Hygiene)**: **PASS**. The plan includes a `checksums.json` generation step in the ingestion phase. Raw data is preserved; derived features are written to new files.
4.  **Principle IV (Single Source of Truth)**: **PASS**. All metrics (ROC-AUC, AUPRC) are generated programmatically and logged; no hand-typed values in the final report.
5.  **Principle V (Versioning Discipline)**: **PASS**. Artifacts (datasets, models, maps) will be hashed and recorded in `state/`.
6.  **Principle VI (Ecological Data Provenance)**: **FAIL** (Current State). The required datasets (Coral Trait Database, ReefBase) are currently listed as "NO VERIFIED SOURCE" in the research plan. The plan **cannot pass** this principle until real, version-locked URLs are provided. **Remediation**: Acquire verified sources for Coral Trait Database and ReefBase. If unavailable, the project scope must be formally amended to "Simulation Study" (opt-in only).
7.  **Principle VII (Model Generalization & Performance)**: **PASS** (Conditional). The plan enforces a spatial hold-out (West vs. East Pacific) and mandates ROC-AUC, Precision-Recall, and calibration reporting **only if real data is available**. If real data is missing, this principle is **N/A** for the current run.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-coral-bleaching/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py                # Paths, seeds, thresholds, DATA_GAP_HALT flag
├── ingest.py                # Data download, merging, imputation, Data Gap Check
├── features.py              # VIF calculation, lagged features, interactions, Definitional Check
├── train.py                 # XGBoost training, CV, spatial split (conditional on real data)
├── evaluate.py              # Permutation importance, FDR, ROC-AUC, AUPRC, Bootstrap Stability
├── map.py                   # GeoTIFF generation, threshold sensitivity, Variation Metric
├── main.py                  # Pipeline orchestrator
└── data_gap_report.py       # Generates report if data is missing

data/
├── raw/                     # Downloaded parquet/csv (checksummed)
├── processed/               # Unified reef-species dataset
└── models/                  # Trained XGBoost artifacts

tests/
├── unit/
│   ├── test_ingest.py
│   └── test_features.py
└── integration/
    └── test_pipeline.py

requirements.txt
```

**Structure Decision**: Single project structure (`code/`) is selected to minimize overhead and ensure all data processing and modeling steps are tightly coupled within a single execution context, fitting the 6-hour runtime constraint.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Spatial Hold-Out (West vs. East) | Essential for generalization testing (US-2) and Constitution Principle VII. | Random split would fail to test geographic transferability, a core research question. |
| VIF Analysis (FR-009) | Required to handle collinearity between SST and DHW (Assumption: Collinearity). | Standard feature importance can be biased by correlated predictors; VIF ensures robust selection. |
| Permutation FDR (FR-007) | Required to prevent false positives in high-dimensional feature space (US-2). | Standard p-values without correction would inflate Type I errors across multiple predictors. |
| **Data Gap Halt** | Required to prevent scientific invalidity of training on synthetic data. | Proceeding with synthetic data would render the research question unanswerable and violate Constitution Principle VI. |

## Implementation Phases

### Phase 0: Data Verification & Ingestion
- **Task 0.1**: Verify availability of all required datasets (NOAA, UNEP, Coral Trait DB, ReefBase) against the "Verified datasets" block.
- **Task 0.2**: If any required dataset (Coral Trait DB, ReefBase) is missing, generate `data_gap_report.md` and **HALT**.
- **Task 0.3**: If all data is present, download and checksum raw files.
- **Task 0.4**: Merge data into unified `reef-species` table.

### Phase 1: Feature Engineering & Validation
- **Task 1.1**: Compute lagged environmental variables (30-day rolling mean SST).
- **Task 1.2**: Create interaction terms (DHW * Thermal Tolerance).
- **Task 1.3**: **Definitional Circularity Check**: Verify if DHW is derived from SST. If so, flag and recommend dropping one or using residuals.
- **Task 1.4**: Calculate VIF for all predictors. Drop features with VIF > 5.

### Phase 2: Model Training & Evaluation
- **Task 2.1**: Split data spatially (Train: West Pacific, Test: East Pacific).
- **Task 2.2**: Train XGBoost model with k-fold cross-validation (max_depth, learning_rate, n_estimators).
- **Task 2.3**: Compute ROC-AUC on test set (SC-001).
- **Task 2.4**: **Bootstrap Stability**: Perform 100 bootstrap resamples to measure ranking stability of top-3 predictors (SC-002).
- **Task 2.5**: **Permutation Importance**: Run a sufficient number of permutations to calculate empirical p-values. Apply Benjamini-Hochberg FDR correction (FR-007). **Justification**: Essential to prevent false-positive feature identification in high-dimensional data.
- **Task 2.6**: **Threshold Sensitivity**: Sweep cutoffs {low, 0.5, 0.7}. Calculate FP/FN rates and **report the variation (delta/range)** of these rates (SC-005, FR-008).

### Phase 3: Mapping & Reporting
- **Task 3.1**: Generate GeoTIFF risk map (FR-005).
- **Task 3.2**: Validate map against independent historical bleaching reports (SC-003). If no independent reports exist, mark as "Not Applicable".
- **Task 3.3**: Generate final report with all metrics and data gap status.
