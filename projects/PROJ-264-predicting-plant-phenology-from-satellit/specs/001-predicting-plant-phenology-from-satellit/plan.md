# Implementation Plan: Predicting Plant Phenology from Satellite Imagery and Climate Data

**Branch**: `001-predict-plant-phenology` | **Date**: 2024-05-21 | **Spec**: `specs/001-predict-plant-phenology/spec.md`
**Input**: Feature specification from `specs/001-predict-plant-phenology/spec.md`

## Summary

This feature implements a machine learning pipeline to predict plant phenological events (budburst, flowering, senescence) using satellite imagery (Sentinel-2) and climate data (NOAA/NASA). The system ingests multi-source data, aligns it temporally to consistent intervals, handles missing data via interpolation or exclusion, trains XGBoost/LightGBM models, and performs sensitivity analysis on regularization parameters. The solution is designed to run entirely on CPU-only CI resources (GitHub Actions free tier).

**Critical Methodological Updates**:
- **Validation Strategy**: Replaced single-site holdout with **Spatial Block Cross-Validation** (K=5 geographic clusters) and **Temporal Holdout** (train 2018-2021, test 2022-2023) to prevent spatial confounding.
- **Feature Independence**: Implemented **Lagged Feature Windows** (e.g., Jan-Mar data to predict April event) to prevent data leakage. Removed `gdd_cumulative` from raw inputs to avoid multicollinearity with temperature.
- **Exploratory Framing**: Explicitly acknowledged the small sample size as a limitation; results are framed as exploratory hypothesis generation.
- **Data Hygiene**: Removed invalid historical datasets (2000, Landsat) from primary validation; reliance is strictly on GEE API and ground truth.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `xarray`, `geopandas`, `xgboost`, `lightgbm`, `scikit-learn`, `requests`, `huggingface_hub`, `earthengine-api`  
**Storage**: Local CSV/Parquet files in `data/` (checksummed), model artifacts in `artifacts/`  
**Testing**: `pytest` (unit, integration, contract tests)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM)  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: Complete data ingestion and model training for 10-15 sites within 6 hours; RMSE/R² metrics computed on held-out test sets.  
**Constraints**: 
- **No GPU usage**; no large LLM inference.
- **Data subset** to fit ~7 GB RAM.
- **Authentication**: Standard Google Earth Engine authentication (`earthengine authenticate`) is **required** for all API access, even for public data.
- **Sample Size**: 10-15 sites (Exploratory study; wide confidence intervals expected).
- **Feature Selection**: GDD is derived at training time, not a raw input.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Notes |
|-----------|--------|--------------|
| **I. Reproducibility** | PASS | Plan includes pinning `random_seed` in `code/` and using canonical API sources. `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | PASS | Plan mandates citing only verified dataset URLs. **New**: Pipeline generates `provenance.yaml` with GEE endpoints/checksums for Reference-Validator verification before `research_accepted`. |
| **III. Data Hygiene** | PASS | Plan requires checksumming all files in `data/` and preserving raw data unchanged. Derivations written to new files. |
| **IV. Single Source of Truth** | PASS | Plan ensures all metrics (RMSE, R²) are computed by code and traced to `data/` rows. No hand-typed stats. |
| **V. Versioning Discipline** | PASS | Plan includes content hashes for artifacts and updates `state/projects/...yaml` on changes. |
| **VI. Satellite & Climate Data Provenance** | PASS | **Schema Defined**: `data/provenance.yaml` MUST include `api_endpoint`, `date_range`, `processing_params`, `software_version`, `checksum`. |
| **VII. Ground-Truth Phenology Validation** | PASS | Plan includes mapping predictions to Nature's Notebook observation IDs and reporting site-specific metrics. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-plant-phenology/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── ingestion.py          # Downloads and aligns satellite, climate, phenology data
│   ├── preprocessing.py      # Interpolation, masking, feature engineering (Lagged windows)
│   └── provenance.yaml       # Records API endpoints, parameters, checksums
├── models/
│   ├── train.py              # XGBoost/LightGBM training with Spatial Block CV
│   ├── evaluate.py           # RMSE, MAE, R² calculation
│   └── sensitivity.py        # Hyperparameter sweep and importance analysis
├── cli/
│   └── run_pipeline.py       # Orchestration script
├── lib/
│   └── utils.py              # Common helpers (logging, seeding, file I/O)
└── config.py                 # Global config (paths, seeds, API keys)
    # Note: config.py must adhere to a Config Contract (JSON Schema) to prevent hardcoded secrets.

tests/
├── contract/
│   ├── test_dataset_schema.py
│   ├── test_config_schema.py  # Validates config.py against schema
│   └── test_output_schema.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_ingestion.py
    ├── test_preprocessing.py
    └── test_models.py

data/
├── raw/                      # Raw downloads (checksummed)
├── processed/                # Cleaned, aligned datasets
└── artifacts/                # Model files, plots, reports

artifacts/
└── models/                   # Trained model binaries
```

**Structure Decision**: Single-project structure (`src/`, `tests/`, `data/`) selected for simplicity and alignment with data science workflow. No separate backend/frontend required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Multiple Model Fallback (XGBoost → LightGBM)** | FR-004 requires fallback if XGBoost fails to converge. | Single model would violate spec requirement for robustness. |
| **Sensitivity Analysis Module** | FR-006 requires sweeping regularization parameters. | Hardcoded parameters would fail robustness checks (SC-003). |
| **Interpolation Logic** | FR-008 requires handling missing satellite data with specific rules. | Simple exclusion would lose too much data; naive imputation violates data hygiene. |
| **Provenance Tracking** | Constitution Principle VI requires recording API details. | Hardcoded paths would break reproducibility and validation. |
| **Spatial Block CV** | Methodology concern (a82b16b8): Single-site holdout causes spatial confounding. | Random split fails to test generalization to new locations. |
| **Lagged Features** | Scientific Soundness (d6a1cf94): Current NDVI predicts past event (tautology). | Using current data for prediction leaks target information. |
| **GDD Removal from Raw** | Scientific Soundness (ec009187): GDD is collinear with Temp. | Keeping both invalidates permutation importance. |
