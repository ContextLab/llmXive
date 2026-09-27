# Implementation Plan: Predicting Avian Migration Patterns from eBird Data

**Branch**: `001-predicting-avian-migration` | **Date**: 2026-09-08 | **Spec**: `specs/001-predicting-avian-migration-patterns-from/spec.md`

## Summary

This project implements a data-driven pipeline to predict the "first arrival" dates of *Setophaga ruticilla* (American Redstart) across North America. The approach ingests the eBird Basic Dataset (EBD) and real environmental data from NASA Earthdata (MODIS), aligns them to a 0.5° spatiotemporal grid, and derives a robust migration onset metric via a cumulative observation threshold. A Gradient Boosting Regressor (XGBoost) is trained on lagged environmental predictors (Temperature, EVI/NDVI) to forecast arrival dates. Rigorous statistical validation (Diebold-Mariano tests, permutation importance) and sensitivity analysis (threshold sweeps) ensure the results are not artifacts of data bias or collinearity. **All data used is real; no synthetic or proxy data is generated.** If continental-scale data exceeds compute limits, the study scope is reduced to a verified regional subset (e.g., Pacific Northwest) using the same real data source.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `xgboost`, `shap`, `scikit-learn`, `pandas`, `dask` (for out-of-core processing), `geopandas`, `rasterio`, `requests`, `datasets` (Hugging Face), `earthaccess` (NASA Earthdata), `psutil` (memory monitoring)  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/outputs`); No database required.  
**Testing**: `pytest` (unit/integration), `pytest-timeout` (enforcing 6h limit).  
**Target Platform**: Linux (GitHub Actions Runner: 2 vCPU, ~7GB RAM).  
**Project Type**: Computational Research Pipeline.  
**Performance Goals**: Full pipeline (download, process, train, test, visualize) completes in ≤6 hours with peak RSS ≤7GB.  
**Constraints**: No local GPU; CPU-first execution.  
**Scale/Scope**: Continental North America (–2023), 0.5° grid resolution. **Fallback**: If full data exceeds RAM, scope reduces to verified regional subset (Pacific Northwest).

> **Compute Strategy**: The XGBoost model and statistical tests are designed to run on the CPU-only GitHub Actions runner. If the dataset size exceeds memory during aggregation, the pipeline will use Dask for streaming aggregation OR automatically reduce the study scope to a verified regional subset (e.g., Pacific Northwest) with a documented power limitation, as per the "Compute Feasibility" guidelines. **No synthetic data is used.**

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification Method |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `code/` will include `requirements.txt` and `random.seed(42)` in all scripts. Data fetches use verified URLs/APIs only. |
| **II. Verified Accuracy** | **PASS** | All dataset citations in `research.md` map strictly to the `# Verified datasets` block in the prompt or NASA Earthdata. No invented URLs. Data is REAL, not synthetic. |
| **III. Data Hygiene** | **PASS** | Pipeline will generate MD5 checksums for `data/raw` files and store them in `state/...yaml`. No in-place edits. |
| **IV. Single Source of Truth** | **PASS** | `metrics.json` and `first_arrival_sweep.csv` will be the sole sources for paper figures. All data is derived from real sources (EBD, MODIS). |
| **V. Versioning Discipline** | **PASS** | Artifacts will be named with content hashes or explicit version tags (e.g., `v1.0-ebd-2015-2023`). |
| **VI. Citizen Science Bias** | **PASS** | Code will enforce "complete checklist" filters (duration ≥1m, observers ≥1, distance ≤10km) and 0.5° grid aggregation. Low-effort cells are flagged. |
| **VII. Temporal Integrity** | **PASS** | Feature engineering will strictly use lagged variables (t-1 to t-4 weeks) for prediction of time `t`. A temporal split (early years for training, subsequent years for validation, and the most recent year for testing) will be enforced. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-avian-migration-patterns-from/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── grid_cell_observation.schema.yaml  # Canonical Schema (SSoT)
│   └── metrics.schema.yaml                # Metrics Schema
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-126-predicting-avian-migration-patterns-from/code/
├── __init__.py
├── config.py            # Paths, seeds, bounding box, hyperparams, API tokens
├── data_loader.py       # Fetches EBD/MODIS (Earthdata), validates checksums
├── preprocessing.py     # Grid aggregation, first-arrival derivation, threshold sweep
├── model_training.py    # XGBoost training, SHAP, Diebold-Mariano, Permutation Importance
├── visualization.py     # Map generation
└── run_pipeline.sh      # Entry point script

projects/PROJ-126-predicting-avian-migration-patterns-from/data/
├── raw/                 # Downloaded CSVs/Rasters (checksummed)
├── processed/           # Aggregated grids, first-arrival CSVs, metrics.json
└── outputs/             # SHAP plots, final maps

projects/PROJ-126-predicting-avian-migration-patterns-from/tests/
├── test_data_loader.py
├── test_preprocessing.py
└── test_model_training.py
```

**Structure Decision**: Selected a linear pipeline structure (Loader -> Preprocess -> Train -> Viz) to match the sequential dependencies of the spec (Data must be ready before modeling). `config.py` centralizes all magic numbers to ensure reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Streaming/Chunking** | EBD is large; loading full 2015-2023 into RAM may exceed 7GB. | Loading full CSV into Pandas DataFrame is not feasible on the 7GB RAM constraint without OOM crashes. |
| **Threshold Sweep** | Spec requires sensitivity analysis (3, 5, 10 obs). | A single threshold (e.g., 5) cannot satisfy FR-003 and SC-003 (robustness check). |
| **Diebold-Mariano Test** | Required for SC-002 to compare models statistically. | Simple RMSE comparison is insufficient for scientific rigor; p-values are mandatory. |
| **MODIS Ingestion** | FR-002 requires MODIS data; NASA POWER is insufficient. | Using weather data (POWER) as a proxy for vegetation (MODIS) violates the spec's data requirements. |

## Implementation Phases

### Phase 0: Configuration & Setup
- **Task T004**: Create `code/config.py` defining:
  - `RANDOM_SEED = 42`
  - `DATA_PATHS` (raw, processed, outputs)
  - `NASA_EARTHDATA_TOKEN` (from env var `NASA_EARTHDATA_TOKEN`)
  - `BOUNDING_BOX` (North America: lat 25-50, lon -130 to -60)
  - `REGIONAL_SUBSET_BOX` (Pacific Northwest: lat 45-50, lon -125 to -115)
  - `HYPERPARAMS` (XGBoost max_depth, n_estimators, etc.)
- **Output**: `code/config.py` with verified defaults.

### Phase 1: Data Ingestion & Preprocessing
- **Phase 1.1: Data Ingestion (FR-001, FR-002)**
  - **Task T011**: Implement `code/data_loader.py`:
    - Download EBD subset for *Setophaga ruticilla* (2015-2023) from verified Hugging Face source.
    - Fetch MODIS MOD11A2 (Temp) and MOD13Q1 (EVI/NDVI) from NASA Earthdata using `earthaccess`.
    - Verify checksums for EBD; store API response hashes.
    - Raise `ConnectionError` if API fails or data is missing.
    - **Fallback Logic**: If full continental MODIS data cannot be downloaded or processed due to size, automatically switch to `REGIONAL_SUBSET_BOX` (Pacific Northwest) and log the scope reduction.
  - **Output**: `data/raw/ebd_subset.csv`, `data/raw/modis_temp.nc`, `data/raw/modis_evi.nc`.

- **Phase 1.2: Environmental Data Resampling (FR-002)**
  - **Task T016**: Implement grid alignment in `code/data_loader.py`:
    - Resample MODIS data (0.5°) to match eBird grid cells.
    - **Algorithm**: Nearest-neighbor interpolation. If a grid cell has no MODIS data within 10km, set `data_quality_flag` = "missing_env".
    - Handle missing values by flagging, not imputing, to preserve data integrity.
    - Rows with "missing_env" are excluded from training but logged for diagnostics.
  - **Output**: Updated `data/raw/modis_*.nc` with grid alignment.

- **Phase 1.3: Feature Engineering (FR-003)**
  - **Task T014, T015**: Implement `code/preprocessing.py`:
    - Filter EBD for complete checklists.
    - Aggregate to 0.5° grid cells.
    - Calculate `first_arrival_date` for thresholds {3, 5, 10}.
    - Implement `calculate_first_arrival_sweep` and `save_first_arrival_results`.
    - Validate output CSV structure against `grid_cell_observation.schema.yaml`.
    - Ensure `data/processed/first_arrival_sweep.csv` is generated.
  - **Output**: `data/processed/first_arrival_sweep.csv`.

### Phase 2: Modeling & Validation
- **Phase 2.1: Model Training (FR-004, FR-005)**
  - **Task**: Train XGBoost models (Temp-only, NDVI-only, Combined) with temporal split.
  - **Output**: Trained model artifacts.

- **Phase 2.2: Model Evaluation (FR-005)**
  - **Task T024**: Implement permutation importance test in `code/model_training.py`.
    - Shuffle features and measure performance drop.
    - Save results to `data/outputs/permutation_importance.csv`.
  - **Output**: `data/outputs/permutation_importance.csv`.

- **Phase 2.3: Statistical Validation (FR-006)**
  - **Task T029**: Implement Diebold-Mariano test and bootstrap-based RMSE differences in `code/model_training.py`.
    - Compare Combined vs. Temp-only vs. NDVI-only.
    - Save results to `data/processed/metrics.json`.
  - **Output**: `data/processed/metrics.json` with p-values and confidence intervals.

- **Phase 2.4: Sensitivity Analysis (FR-003, SC-003)**
  - **Task T030**: Read `data/processed/first_arrival_sweep.csv` and flag variations in arrival dates across thresholds.
    - Compare median first-arrival dates for thresholds 3, 5, 10.
    - Flag if variation > 7 days.
  - **Output**: Updated `metrics.json` with sensitivity flags.

### Phase 3: Visualization & Mapping (FR-007)
- **Phase 3.1: Map Generation (FR-007)**
  - **Task T040**: Implement `code/visualization.py`:
    - Generate continental-scale (or regional subset) maps of predicted arrival dates.
    - Generate SHAP summary plots.
    - Save maps to `data/outputs/migration_map.png` and `data/outputs/shap_summary.png`.
  - **Output**: `data/outputs/migration_map.png`, `data/outputs/shap_summary.png`.

### Phase 4: Feasibility Verification (SC-004)
- **Phase 4.1: Compute Measurement (SC-004)**
  - **Task T050**: Run pipeline with timing instrumentation.
    - Execute `time ./run_pipeline.sh` and capture `free -m` logs.
    - **Implementation Detail**: Use `psutil` in Python to monitor peak RSS of the main process and log it to `metrics.json`.
    - Log peak RSS and elapsed time to `metrics.json`.
    - Ensure no hardcoded values; all metrics are measured.
  - **Output**: Verified feasibility metrics in `metrics.json`.

## Contracts

- **Canonical Schema**: `contracts/grid_cell_observation.schema.yaml` (defines all data structures for the pipeline). **This is the single source of truth.**
- **Metrics Schema**: `contracts/metrics.schema.yaml` (defines output metrics structure).
- **Note**: All other schema files have been removed to avoid conflicts. The `grid_cell_observation.schema.yaml` is the single source of truth for data structures.
