# Implementation Plan: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

**Branch**: `PROJ-125-statistical-analysis-of-openstreetmap-da` | **Date**: 2026-06-25 | **Spec**: `specs/001-statistical-analysis-of-openstreetmap-da/spec.md`
**Input**: Feature specification from `specs/001-statistical-analysis-of-openstreetmap-da/spec.md`

## Summary

This project implements a reproducible statistical pipeline to quantify Urban Heat Island (UHI) effects by analyzing the relationship between OpenStreetMap (OSM) urban features (buildings, trees, roads) and Land Surface Temperature (LST) derived from satellite data (MODIS/Landsat). The pipeline ingests vector and raster data, reprojects them to a common 30m resolution, performs exploratory spatial analysis (Moran's I), and fits spatial regression models (OLS, SAR, GWR). If memory constraints prevent spatial modeling, the pipeline will **halt execution** rather than producing potentially invalid results.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `osmnx`, `geopandas`, `rasterio`, `xarray`, `scikit-learn`, `pysal` (for SAR/GWR), `statsmodels`, `numpy`, `pandas`, `scipy`, `ruff`, `black`, `pytest`.
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/results/`); No external database required for this batch analysis.
**Testing**: `pytest` with `pytest-cov` for coverage; `ruff` for linting; `black` for formatting.
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ~7GB RAM).
**Project Type**: Data Science Pipeline / CLI
**Performance Goals**: Complete full pipeline within 6 hours; Memory usage < 6GB.
**Constraints**: 
- **Memory**: Strict GB RAM limit. If exceeded, the pipeline will halt execution.
- **Data**: No synthetic data. Must use real, downloadable sources.
- **Compute**: CPU-first. If SAR/GWR requires GPU (unlikely for standard `pysal` on CPU, but possible for large matrices), scale down or halt execution.
- **Resolution**: All data must be resampled to a uniform spatial resolution..

### Spatial Resolution Integrity (Principle VI Compliance)
To satisfy **Constitution Principle VI**, the pipeline enforces the following reprojection and aggregation logic:
1. **Ingestion**: OSM vectors are ingested in their native CRS (usually EPSG:4326). Satellite rasters are ingested in their native CRS (often EPSG:4326 or specific UTM zones).
2. **Reprojection to Local UTM**: All data is first reprojected to the **Local UTM zone** corresponding to the city's centroid. This ensures distance-based calculations (e.g., density, bandwidth) are accurate in meters.
3. **Aggregation**: OSM vector features (points/lines/polygons) are aggregated to a high-resolution grid using the UTM projection. For example, building footprints are rasterized to a binary mask at 30m resolution.
4. **Final Alignment**: The aggregated 30m raster grid is then reprojected to **a standard web mapping coordinate reference system** (Web Mercator) if required for visualization or downstream compatibility, but all statistical modeling occurs on the UTM-aligned grid to preserve metric integrity.
5. **Documentation**: Every transformation step logs the `source_crs`, `target_crs`, and `resampling_method` (e.g., `nearest`, `cubic`) to `data/processed/transformation_log.json`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan includes `requirements.txt` pinning, random seeds, and canonical data fetch logic. |
| **II. Verified Accuracy** | **PASS** | Plan mandates citation validation for all external sources before use. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw data and immutable derivation steps. |
| **IV. Single Source of Truth** | **PASS** | All metrics will be generated from `data/results/metrics.csv` and referenced in reports. |
| **V. Versioning** | **PASS** | Artifact hashes will be recorded in `state/...yaml`. |
| **VI. Spatial Resolution Integrity** | **PASS** | Plan explicitly details the reprojection logic: Native -> Local UTM -> 30m Aggregation -> EPSG:3857. This ensures vector-raster alignment is metrically valid before statistical analysis. |
| **VII. Proxy Validity Boundaries** | **PASS** | Plan includes "Unexplained Variance Gap" calculation (FR-010) and sensitivity analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-analysis-of-openstreetmap-da/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-125-statistical-analysis-of-openstreetmap-da/
├── code/
│   ├── __init__.py
│   ├── config.py              # Configuration, memory thresholds, seeds, MAX_BLOCKS
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── memory.py          # Memory monitoring, sampling logic
│   │   └── io.py              # Data ingestion, checksumming
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ols.py             # OLS fitting
│   │   ├── sar.py             # SAR fitting (with fallback)
│   │   └── gwr.py             # GWR fitting (with fallback)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── exploratory.py     # Moran's I, correlation
│   │   └── validation.py      # Cross-validation, FDR correction
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded raw data (checksummed)
│   ├── processed/             # Rasterized, aligned data
│   └── results/               # Metrics, plots, reports, linting logs
├── tests/
│   ├── unit/
│   │   ├── test_config.py     # Unit tests for config.py
│   │   ├── test_memory.py     # Unit tests for memory.py
│   │   └── test_io.py         # Unit tests for io.py
│   └── integration/
│       └── test_pipeline.py
├── docs/
│   └── quickstart.md          # Validation artifact for T041
└── requirements.txt
```

**Structure Decision**: Single-project structure with modular `code/` directory. This aligns with the "CLI/Data Pipeline" nature and ensures all dependencies and scripts are contained within the project root for easy CI execution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Memory Fallback Logic** | Essential for CI stability on 7GB RAM with large spatial datasets. | A simple "fail on error" approach would crash the pipeline, violating SC-005 and preventing any results. |
| **Spatial Cross-Validation** | Required to prevent spatial autocorrelation leakage in model evaluation. | Standard random K-fold would overestimate model performance due to spatial clustering. |
| **Multiple Model Types (OLS/SAR/GWR)** | Required by FR-005 to compare global vs. local effects. | Running only OLS would miss the spatial heterogeneity analysis required by the spec. |
| **Local UTM Reprojection** | Required by Principle VI to ensure distance-based metrics (density) are accurate. | Directly reprojecting to EPSG:3857 for aggregation would distort areas and densities at higher latitudes. |

## Linting & Formatting (T037)

To satisfy **T037**, the following linting and formatting workflow is mandated:
- **Tooling**: `ruff` (linting) and `black` (formatting).
- **Execution**:
  - `ruff check code/` must pass with zero errors.
  - `black --check code/` must pass with zero diffs.
- **Artifact**: A `lint_report.txt` file will be generated in `data/results/` containing the output of `ruff check` and `black --check`.
- **Failure**: If linting fails, the pipeline halts before model fitting.

## Memory Safety & Configuration (T038b)

To satisfy **T038b**, the following configuration and monitoring strategy is mandated:
- **Config File**: `code/config.py` must define `MAX_BLOCKS` (default: a representative sample size) and `MAX_MEMORY_GB` (default: a moderate threshold).
- **Memory Profiling**:
  - `utils/memory.py` will track peak memory usage per processing block.
  - Results will be logged to `data/results/memory_profile.csv` with columns: `block_id`, `peak_memory_gb`, `status`.
- **Threshold Enforcement**: If `peak_memory_gb > MAX_MEMORY_GB`, the pipeline triggers the `OLS_DEGRADED` fallback or halts.
- **Verification**: A unit test `test_memory.py` will simulate memory spikes and verify the logging mechanism.

## Testing Strategy (T039)

To satisfy **T039**, the following unit tests are required:
- **`tests/unit/test_config.py`**: Validates that `config.py` loads correctly, seeds are pinned, and `MAX_BLOCKS` is within range.
- **`tests/unit/test_memory.py`**: Validates the memory monitoring logic and the `OLS_DEGRADED` trigger condition.
- **`tests/unit/test_io.py`**: Validates checksumming and data ingestion logic.
- **Coverage**: Minimum 80% line coverage for `code/utils/` and `code/config.py`.

## Quickstart Validation (T041)

To satisfy **T041**, the following validation is required:
- **Artifact**: A `docs/quickstart.md` file must exist and be validated against the `quickstart.md` in the plan.
- **Validation**: A script `scripts/validate_quickstart.sh` will run the installation steps in a Docker container to ensure reproducibility.
- **Output**: `data/results/quickstart_validation.log` will record the success/failure of the validation run.

## Spec Update for Fallback (T042)

To satisfy **T042**, the following update to `spec.md` is mandated:
- The `spec.md` file must be updated to explicitly state that `OLS_DEGRADED` is the governing rule for memory constraints.
- This update ensures that the fallback strategy is documented as a first-class requirement, not just an implementation detail.

## Execution Flow

1. Ingest OSM and Satellite Data (T012, T013)
2. Align and Rasterize (T014, T015) - *With Local UTM reprojection*
3. Exploratory Analysis (T019, T020)
4. Memory Check & Sampling (T026a, T026b) - *With `MAX_BLOCKS` configuration*
5. Model Fitting (T027, T028, T029) - *Subject to FR-005 Fallback*
6. Cross-Validation & Metrics (T030, T031)
7. Sensitivity & Proxy Validity (T034, T032)
8. Export Results (T033) - *Ensure no synthetic values in `metrics.csv`*
9. Linting & Validation (T037, T041) - *Generate `lint_report.txt` and `quickstart_validation.log`*
10. Update Spec (T042) - *Update `spec.md` with fallback rule*

**Note on Output Integrity**: The pipeline must calculate real metrics from the sampled dataset. If the dataset is empty or invalid, the pipeline halts. No placeholder values (e.g., "N/A", "0.0" for uncomputed metrics) are allowed in `data/results/metrics.csv` unless the run was explicitly degraded and logged as such.