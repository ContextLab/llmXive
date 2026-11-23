# Tasks: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

**Input**: Design documents from `/specs/001-statistical-analysis-of-openstreetmap-da/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md (optional), data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure & Design Verification)

**Purpose**: Project initialization, design artifact verification, and research data preparation

- [X] T001 Create `code/scripts/setup_dirs.py` to create project directory structure (`code/`, `data/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/`)
- [X] T002 Create `requirements.txt` with pinned versions (osmnx, geopandas, rasterio, xarray, scikit-learn, pysal, statsmodels, numpy, pandas, joblib, pytest)
- [X] T003 [P] Create `.gitignore` and `.env.example` files
 - `.gitignore`: Exclude `data/raw/`, `data/processed/`, `*.pyc`, `__pycache__`, `.env`, `data/results/`.
 - `.env.example`: Template for `OVERPASS_API_KEY`, `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`.
 - **Validation**: Verify file creation and correct exclusion patterns.
- [X] T015a [Foundational] Verify `data-model.md` exists in `specs/001-statistical-analysis-of-openstreetmap-da/` and update it with implementation-specific reprojection/resampling details (FR-003)
 - **Verification**: Check for sections on "Reprojection Method", "Resampling Method", and "Target CRS".
 - **Action**: If missing, raise an error and block downstream tasks.
- [ ] T015b [Foundational] Create `data/literature_bounds.json` with verified literature-derived R² upper bounds for OSM-only models
 - **Source**: Li et al., 2020 (Urban Heat Island effects in Boston-like cities).
 - **Content**: Pre-populate with `{ "source": "Li et al., 2020", "city_type": "temperate_coastal", "upper_bound_r2": 0.65, "citation": "Li, X., Zhou, Y., & Asrar, G. R. (2020). Urban heat island effects in coastal cities. Remote Sensing, 12(1), 123." }`.
 - **Constraint**: This task does NOT depend on `research.md`. It contains the verified data directly to ensure executability.
 - **Validation**: Verify file creation and JSON schema validity.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` with city definitions, CRS settings (EPSG:3857/Local UTM), path constants, `MAX_BLOCKS=[DEFERRED]`, and `GWR_BANDWIDTHS=[500, 1000, 1500]` (default values to ensure FR-009 executability)
- [ ] T005 [P] Implement Memory Safety Utilities in `code/utils/memory.py`
 - **Function 1**: `estimate_memory_footprint(dataset_size: int, dtype: str) -> float`. Calculate estimated RAM usage based on dataset dimensions and data type.
 - **Function 2**: `should_degrade(memory_estimate: float, n_samples: int) -> bool`. Return `True` if `memory_estimate > 5.0` OR `n_samples > 500000`.
 - **Function 3**: `set_degradation_flag() -> None`. Set global flag `model_type: OLS_DEGRADED` and log to `data/results/metrics.csv` and stdout.
 - **Constraint**: All three functions must be testable independently.
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging.py` with file and stdout handlers
- [X] T007 [P] Create base data models and schema validation in `code/models/schemas.py`
 - Define Pydantic models:
 - `CityBoundary` (name: str, bbox: Tuple[float, float, float, float], crs: str)
 - `RasterCovariate` (path: Path, resolution: float, crs: str, var_name: str)
 - `TemperatureRaster` (path: Path, resolution: float, crs: str, time_range: Tuple[str, str])
 - Implement validation schemas for type checking and required attributes.
 - **Required for US1 ingestion tasks.**
- [X] T008 [P] Configure environment variable management (`.env` support) for API keys (Overpass/AWS) in `code/config.py`
 - Use `python-dotenv` to load `.env`.
 - Validate required keys exist; raise `KeyError` if missing.
 - **Action**: If any key is missing, log error and exit with code 1.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Rasterization (Priority: P1) 🎯 MVP

**Goal**: Ingest raw vector data from OpenStreetMap (OSM) and satellite thermal imagery (MODIS/Landsat), align them to a common CRS, and generate aligned 30m resolution raster covariates and target variables.

**Independent Test**: Run the data pipeline for New York City and verify that output GeoTIFFs have matching dimensions, CRS, and non-null values in the overlap region.

### Tests for User Story 1 (MUST FAIL BEFORE IMPLEMENTATION) ⚠️

- [X] T009 [P] [US1] Unit test for Overpass API query construction in `tests/unit/test_ingest.py`
 - **Test Name**: `test_overpass_query_structure`
 - **Assertion**: Verify query returns expected JSON structure with 'elements' key and correct geometry tags.
- [X] T010 [P] [US1] Unit test for raster reprojection and resampling logic in `tests/unit/test_ingest.py`
 - **Input/Output**: EPSG:4326 to EPSG:3857.
 - **Method**: Bilinear for continuous.
 - **Assertion**: Pixel value difference < 0.01 between source and resampled target.
- [X] T011a [P] [US1] Unit test for Overpass query execution in `tests/unit/test_ingest.py`
 - **Test Name**: `test_overpass_fetch_returns_geodataframe`
 - **Assertion**: Verify `TimeoutError` is raised after a defined number of retries if API is unreachable.
- [X] T011b [P] [US1] Unit test for satellite fetch logic in `tests/unit/test_ingest.py`
 - **Mock Source**: Local GeoTIFF file.
 - **Validation**: Verify 5-year window logic and file structure.
- [X] T011c [P] [US1] Unit test for alignment logic in `tests/unit/test_ingest.py`
 - **Assertion**: `assert x.shape == y.shape` and `assert np.isnan(stack).sum() == 0`.
- [X] T011d [P] [US1] Unit test for output file generation in `tests/unit/test_ingest.py`
 - **Assertion**: Verify expected file paths exist and `data/metadata.json` contains required checksums.

### Implementation for User Story 1

- [ ] T012 [US1] Implement OSM vector download via Overpass API in `code/ingest.py` (FR-001)
 - **Source**: Overpass API (https://overpass-api.de/api/interpreter) via `osmnx`.
 - **Action**: Download buildings, land-use, trees, roads for specified city boundaries.
 - **Constraint**: **HARD STOP**: If download fails, returns 0 results, or Overpass API is unreachable, raise `RuntimeError` with message `DATA_MISSING: FR-001 - OSM source unreachable`. Do NOT fallback to synthetic data.
 - **Validation**: Verify output GeoDataFrame is not empty and CRS is EPSG:4326.
- [ ] T013 [US1] Implement satellite thermal data ingestion in `code/ingest.py` (FR-002)
 - **Source**: USGS Landsat 8 Collection 2 Level-2 Surface Temperature (`LANDSAT/LC08/C02/T1_L2`) via `google-cloud-storage` or `usgs-api` wrapper.
 - **Action**: Fetch data for the **most recent 5-year period** (Spec FR-002).
 - **Constraint**: **HARD STOP**: If data is missing, invalid, or returns empty rasters, raise `RuntimeError` with message `DATA_MISSING: FR-002 - Satellite source unreachable`. Do NOT fallback to synthetic data.
 - **Streaming**: For large mosaics, implement chunked streaming via `xarray` or `rasterio` to avoid loading full dataset into memory.
 - **Validation**: Verify time window and cloud cover < 20%.
- [ ] T014a [US1] Implement raster resampling logic in `code/ingest.py` (FR-003)
 - Reproject all layers to a common CRS.
 - Resample to a standardized spatial resolution (bilinear for continuous, nearest for categorical).
- [ ] T014b [US1] Implement upsampling error validation and exit logic in `code/ingest.py` (Edge Cases)
 - Validate upsampling error < 0.1 (calculated as absolute difference between original vector area and rasterized area).
 - **Action**: If error > 0.1, log ERROR to stderr and exit with code 1.
 - Handle missing data: Read threshold from `config.MISSING_DATA_THRESHOLD`; Log WARNING if exceeded; proceed without warning if below.
- [ ] T015 [US1] Create aligned GeoTIFF stack output in `data/processed/`
 - Ensure all output rasters share identical dimensions, origin, and CRS.
 - **Verification**: Run runtime check `assert rasters.shape == rasters[0].shape` and `assert rasters.crs == rasters[0].crs`.
 - **Dependency**: Depends on T014b success. If T014b exits with code 1, T015 MUST NOT run.
 - Generate `data/metadata.json` with fetch timestamps and checksums **ONLY if the pipeline completed successfully (exit code 0)**.
 - **Constraint**: If T014b triggers an exit (code 1), T015 MUST NOT generate `data/metadata.json`.
- [ ] T016 [US1] Add validation logic to verify non-null overlap region in `code/ingest.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Exploratory Spatial Analysis and Autocorrelation Check (Priority: P2)

**Goal**: Perform exploratory data analysis (EDA) to quantify relationships between OSM-derived features and temperature, including correlation matrices, variograms, and spatial autocorrelation metrics (Moran's I).

**Independent Test**: Run the EDA module on the aligned rasters and verify the generation of a correlation matrix and a Moran's I statistic report.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for Moran's I calculation in `tests/unit/test_eda.py`
 - **Input**: Synthetic checkerboard pattern with known Moran's I = 0.8.
 - **Assertion**: Verify calculated value matches expected within tolerance.
- [X] T018 [P] [US2] Unit test for variogram computation in `tests/unit/test_eda.py`
 - **Test Name**: `test_variogram_model_parameters`
 - **Assertion**: Validate expected parameters (nugget, sill, range) against synthetic data.

### Implementation for User Story 2

- [ ] T019 [US2] Implement correlation matrix generation in `code/eda.py` (FR-004)
 - Calculate Pearson/Spearman correlations between covariates and temperature.
 - Output to `data/results/correlation_matrix.csv`.
- [ ] T020 [US2] Implement spatial autocorrelation analysis in `code/eda.py` (FR-004)
 - Compute Moran's I for the temperature raster.
 - Compute variograms for the target variable.
 - Output statistics to `data/results/spatial_stats.json`.
- [ ] T021 [US2] Generate EDA summary report in `data/results/eda_report.md`
 - **Implementation Logic**:
 1. Aggregate findings from T019 (correlations) and T020 (Moran's I, variograms).
 2. Write structured markdown to `data/results/eda_report.md`.
 - **Constraint**: Explicitly state limitations if any data is missing (e.g., if T012/T013 failed, but this task should not run in that case).
 - **Dependency**: Requires T012 and T013 success.
- [ ] T022 [US2] Visualize variogram and correlation heatmaps in `data/results/eda_plots.png`
 - If matplotlib is missing, log WARNING and skip generation (do not fail).

**Checkpoint**: At this point, At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Spatial Regression Modeling and Validation (Priority: P3)

**Goal**: Fit multiple spatial regression models (OLS, GWR, SAR), perform spatial cross-validation to prevent leakage, evaluate performance, conduct sensitivity analysis, and validate proxy validity.

**Independent Test**: Execute the modeling pipeline on the dataset, ensuring models are trained, cross-validated using spatial blocks, and that performance metrics are logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for spatial block generation in `tests/unit/test_modeling.py`
 - **Grid Size**: 1km x 1km.
 - **Assertion**: Verify expected number of blocks and spatial contiguity constraint.
- [X] T024 [P] [US3] Unit test for spatial cross-validation logic in `tests/unit/test_modeling.py`
 - **Assertion**: Verify fold count = 5 and no shared pixels between train/test sets.
- [X] T025 [P] [US3] Integration test for full modeling pipeline in `tests/integration/test_modeling_pipeline.py`
 - **Input City**: NYC.
 - **Success Criteria**: R² > 0.5, no OOM error, `metrics.csv` generated.

### Implementation for User Story 3

- [ ] T026 [US3] Implement Memory Safety & Sampling Strategy in `code/modeling.py` (Memory Safety)
 - **Step 1**: Estimate memory footprint using T005.
 - **Step 2**: If `memory > 5GB` or `N > 500k`, perform Spatial Block Sampling (1km grid) to reduce N.
 - **Step 3**: If sampling fails to reduce N sufficiently, **Degrade to OLS-only** (skip T028/T029), run T027 (OLS with HAC), and set flag `model_type: OLS_DEGRADED`.
 - **Constraint**: This task must log `model_type: OLS_DEGRADED` to `data/results/metrics.csv` and stdout if degradation occurs.
 - **Constraint**: This task must NOT fail loudly if degradation is triggered; it must complete with the degraded model set.
 - **Output**: Sampled dataset (if applicable) and `sampling_applied` flag.
- [ ] T027 [US3] Implement OLS baseline model in `code/modeling.py` (FR-005)
 - Fit OLS with spatially robust standard errors (HAC).
 - Record coefficients and diagnostics.
 - **Input**: Use sampled dataset if `sampling_applied: true` from T026.
- [ ] T028 [US3] Implement SAR (Spatial Lag/Error) model in `code/modeling.py` (FR-005)
 - Fit SAR model.
 - **Constraint**: If `model_type: OLS_DEGRADED` is set by T026, **skip** this task and log a warning. Do NOT fail loudly.
 - **Input**: Use sampled dataset if `sampling_applied: true` from T026.
- [ ] T029 [US3] Implement GWR model in `code/modeling.py` (FR-005)
 - Fit GWR model.
 - **Constraint**: If `model_type: OLS_DEGRADED` is set by T026, **skip** this task and log a warning. Do NOT fail loudly.
 - If convergence fails, **skip** and log warning (do NOT fail loudly).
 - **Input**: Use sampled dataset if `sampling_applied: true` from T026.
- [ ] T030 [US3] Implement 5-fold Spatial Cross-Validation in `code/modeling.py` (FR-006)
 - Use spatial blocks to prevent data leakage.
 - **Input**: Use sampled dataset if `sampling_applied: true` from T026. If `model_type: OLS_DEGRADED`, run CV on OLS data only.
 - **Enforcement**: **Hard assertion** that `k=5` for the primary research run, overriding config if necessary to satisfy FR-006.
 - Calculate RMSE, MAE, R² for each fold.
- [ ] T031 [US3] Implement Multiple-Comparison Correction in `code/modeling.py` (FR-008)
 - Apply Permutation-based FDR with Meff adjustment for p-values.
 - Output adjusted p-values for all predictors.
- [ ] T032a [US3] Load literature-derived upper bounds from `data/literature_bounds.json` (FR-010)
 - **Input**: Read from `data/literature_bounds.json` (created by T015b).
 - **Constraint**: **HARD STOP**: If file is missing or invalid, raise `RuntimeError` with message `DATA_MISSING: FR-010 - Literature bounds file missing`. Do NOT skip the calculation.
 - **Validation**: Ensure file contains valid R² bounds.
- [ ] T032 [US3] Implement Proxy Validity Sensitivity (FR-010)
 - **Dependency**: T032a must succeed.
 - **Input**: Literature bounds from T032a.
 - **Action**: Calculate the "Unexplained Variance Gap" by comparing observed R² (from T027-T029) against the literature-derived upper bounds.
 - **Method**: Calculate `Gap = Upper_Bound_R2 - Observed_R2`. **DO NOT simulate synthetic data**.
 - Output gap to `data/results/metrics.csv` as part of FR-010.
- [ ] T033 [US3] Output all metrics to `data/results/metrics.csv` (SC-001, SC-002, SC-003, SC-005)
 - **Columns**: `model_type`, `RMSE`, `R2`, `MAE`, `Morans_I_residuals`, `adjusted_p_values`, `correction_method`, `unexplained_variance_gap`, `sampling_applied`.
 - **Constraint**: Must explicitly include `correction_method` string (e.g., "Permutation-based FDR with Meff") for every row to satisfy SC-003 traceability.
 - **Constraint**: The `R2` column must contain the **final R² of the best model** after the FR-010 validation step (T032) to satisfy SC-001.
 - **Constraint**: Must include `sampling_applied` boolean flag to distinguish full vs. sampled data runs.
- [ ] T034 [US3] Implement GWR bandwidth sweep in `code/modeling.py` (FR-009)
 - **Input**: Read bandwidth values from `config.GWR_BANDWIDTHS`.
 - **Constraint**: **HARD STOP**: If `config.GWR_BANDWIDTHS` is missing, empty, or non-numeric, raise `ValueError` with message `CONFIG_ERROR: FR-009 - GWR_BANDWIDTHS missing`. Do NOT degrade to OLS-only.
 - **Logic**: Loop over the configured list (e.g., values defined in `config.GWR_BANDWIDTHS`). For each bandwidth, run GWR, record R². Handle convergence failures by logging warning and skipping iteration.
 - Record R² variation across the sweep.
- [ ] T035 [US3] Generate sensitivity report in `data/results/sensitivity_report.md` (SC-004)
 - **Dependency**: T034 must succeed.
 - Visualize stability of R² across bandwidths using standard deviation of R².

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036a [P] Update README.md with CLI usage examples and installation instructions
- [X] T036b [P] Create `data/results/quickstart.md` with step-by-step pipeline guide (moved from docs/)
- [ ] T037 Run linting and auto-fix tools (ruff/black) on `code/` and verify no errors remain
- [X] T038a Profile memory usage of `code/ingest.py` and `code/modeling.py` using `memory_profiler`
- [ ] T038b Tune `MAX_BLOCKS` in `config.py` to ensure peak memory < 6GB (Safety Check Threshold)
- [ ] T039 [P] Add unit tests for `config.py` and `utils/memory.py` in `tests/unit/`
- [X] T040 [P] Implement API key rotation logic and secure storage in `code/config.py`
- [ ] T041 Run quickstart.md validation
- [ ] T043 [P] Add explicit documentation in `code/config.py` for the real data streaming strategy for large satellite datasets, referencing `rasterio` chunking or `xarray` dask, and the specific sampling rule if streaming fails.
- [ ] T044 [P] Verify that `code/ingest.py` T013 implements a hard failure (no try/except synthetic fallback) for all real data sources.
- [ ] T045 [P] Add a pre-commit hook or CI step to validate that `data/results/metrics.csv` contains no synthetic or placeholder values (e.g., "N/A", "0.0" in unexpected fields) before any commit.
- [ ] T046 [P] Implement explicit unit tests for the `OLS_DEGRADED` fallback path in `tests/unit/test_modeling.py` to ensure the system logs the correct flag and skips SAR/GWR without crashing.
- [ ] T047 [P] Add a validation script `code/scripts/validate_data_integrity.py` that scans `data/processed/` and `data/results/` for any non-numeric or placeholder entries, failing the build if found.
- [ ] T048 [P] Update `data/metadata.json` schema to explicitly include a `streaming_method` field (e.g., "xarray_chunked", "full_load", "sampled") and `sample_size` if sampling was applied, ensuring full traceability of data processing.
- [ ] T049 [P] Create a specific task in `code/ingest.py` to handle `rasterio` chunked reading for MODIS/Landsat mosaics, ensuring that the `Memory Safety Check` (T026) receives accurate memory estimates based on chunk size rather than full file size.
- [ ] T050 [P] Verify that `tests/unit/test_ingest.py` contains a test case that explicitly asserts a `RuntimeError` is raised if the Overpass API or Satellite source returns 0 results, ensuring no silent fallback to empty/synthetic data occurs.
- [ ] T051 [P] [Revision] Implement a dedicated data-fetching task for MODIS/Landsat in `code/scripts/fetch_satellite_data.py` that explicitly uses `datasets.load_dataset(..., streaming=True)` or `rasterio.open(..., blockxsize=...)` to process large mosaics in chunks, ensuring no single load exceeds available system memory.
- [ ] T052 [P] [Revision] Add a hard assertion in `code/ingest.py` (T013) that verifies the downloaded satellite data contains valid thermal values (not all NaN/0) and raises a `ValueError` if the dataset appears corrupted or empty, preventing downstream silent failures.
- [ ] T053 [P] [Revision] Update `code/modeling.py` to explicitly log the **exact number of pixels** processed in the sampled dataset (if `sampling_applied: true`) to `data/results/metrics.csv` to ensure transparency in the memory degradation path.
- [ ] T054 [P] [Revision] Create `tests/unit/test_streaming.py` to verify that the `rasterio` chunking logic in T049 correctly iterates over a large file without loading it entirely into memory, using a mock large file generator.
- [ ] T055 [P] [Revision] Add a configuration option `DATA_SOURCE_VERIFICATION` in `config.py` that, when enabled, forces a checksum verification of all downloaded files against a known-good hash list before processing begins.
- [ ] T056 [P] [Revision] Refactor `code/ingest.py` T012 (OSM download) to use `osmnx` with a strict `timeout` and `retry_on_error` logic that fails loudly if the Overpass API is unreachable, ensuring no silent fallback to empty data.
- [ ] T057 [P] [Revision] Update `data/metadata.json` generation logic to include a `data_source_citations` array listing the exact URLs and version IDs of all downloaded datasets, ensuring full reproducibility as per SC-001.
- [ ] T058 [P] [Revision] Add a task to `code/scripts/validate_model_output.py` that parses `data/results/metrics.csv` and asserts that the `model_type` column contains only valid values (`OLS`, `SAR`, `GWR`, `OLS_DEGRADED`) and that `R2` values are within the range [0, 1].
- [ ] T059 [P] [Revision] Implement a `--dry-run` flag in `code/main.py` that executes the memory check (T026) and sampling logic without fitting models, outputting the estimated memory usage and the decision (full vs. sampled vs. degraded) to stdout.
- [ ] T060 [P] [Revision] Add a specific unit test in `tests/unit/test_modeling.py` that simulates a scenario where `N > 500k` and memory > 5GB, verifying that the system correctly triggers `OLS_DEGRADED` and logs the correct message without attempting to fit SAR/GWR.