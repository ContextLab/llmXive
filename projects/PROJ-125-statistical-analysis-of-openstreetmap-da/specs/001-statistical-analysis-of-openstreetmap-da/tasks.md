# Tasks: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

**Input**: Design documents from `/specs/001-urban-heat-osm/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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
- [X] T015a [Foundational] Verify `data-model.md` exists in `specs/001-urban-heat-osm/` and update it with implementation-specific reprojection/resampling details (FR-003)
 - **Verification**: Check for sections on "Reprojection Method", "Resampling Method", and "Target CRS".
 - **Action**: If missing, raise an error and block downstream tasks.
- [X] T015b [Foundational] Create `data/literature_bounds.json` with literature-derived R² upper bounds for OSM-only models (Source: verified research in `research.md`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` with city definitions, CRS settings (EPSG:3857/Local UTM), path constants, and `MAX_BLOCKS=[DEFERRED]` (placeholder referencing plan.md)
- [X] T005 [P] Implement memory safety utilities (`code/utils/memory.py`) for matrix size estimation and **graceful degradation logic** to ensure data fits within RAM; if data exceeds limits (memory >5GB or N > 500k), the utility must **trigger the OLS-only fallback path** as per Spec FR-005, setting the flag `model_type: OLS_DEGRADED` and logging the event. It must **NOT** raise a fatal error.
 - **Action**: Check memory footprint. If >5GB or N > 500k, trigger fallback logic (set flag `model_type: OLS_DEGRADED`) rather than raising an error.
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
- [X] T021a [Foundational] Implement ingestion of socioeconomic proxies (WorldPop/OSM height) in `code/ingest.py`
 - Attempt to fetch data; if unavailable, **log WARNING and continue** (do NOT raise error).
 - **Threshold Logic**: If missing data > 10%, log WARNING. If ≤10%, proceed without warning.
 - Output to `data/processed/socioeconomic_proxies.tif` if successful.
 - **Constraint**: If fetch fails, log limitation and proceed; do NOT generate synthetic proxies.
 - **Note**: Moved to Phase 2 to ensure availability before EDA (Phase 4).

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
 - **Assertion**: Verify `TimeoutError` is raised after 3 retries if API is unreachable.
- [X] T011b [P] [US1] Unit test for satellite fetch logic in `tests/unit/test_ingest.py`
 - **Mock Source**: Local GeoTIFF file.
 - **Validation**: Verify 5-year window logic and file structure.
- [X] T011c [P] [US1] Unit test for alignment logic in `tests/unit/test_ingest.py`
 - **Assertion**: `assert x.shape == y.shape` and `assert np.isnan(stack).sum() == 0`.
- [X] T011d [P] [US1] Unit test for output file generation in `tests/unit/test_ingest.py`
 - **Assertion**: Verify expected file paths exist and `data/metadata.json` contains required checksums.

### Implementation for User Story 1

- [X] T012 [US1] Implement OSM vector download via Overpass API in `code/ingest.py` (FR-001)
 - Download buildings, land-use, trees, roads for specified city boundaries.
 - Handle rate limits with exponential backoff and local caching.
 - **Constraint**: Do NOT implement synthetic fallback; raise error on download failure.
- [X] T013 [US1] Implement satellite thermal data ingestion in `code/ingest.py` (FR-002)
 - Fetch MODIS/Landsat data for the **most recent 5-year period** (Spec FR-002).
 - Validate the time window explicitly using `config.TIME_WINDOW_THRESHOLD`.
 - **Constraint**: If `config.TIME_WINDOW_THRESHOLD` is missing or invalid, fail loudly with a specific error message.
 - Compute daytime land-surface temperature composites.
 - Implement cloud masking and multi-date composite generation if cloud cover > 20%.
 - **Constraint**: Use real data sources only; do not fallback to synthetic temperature data.
 - **Streaming**: For large mosaics, implement chunked streaming via `xarray` or `rasterio` to avoid loading full dataset into memory.
- [X] T014a [US1] Implement raster resampling logic in `code/ingest.py` (FR-003)
 - Reproject all layers to a common CRS.
 - Resample to a standardized spatial resolution (bilinear for continuous, nearest for categorical).
- [X] T014b [US1] Implement upsampling error validation and exit logic in `code/ingest.py` (Edge Cases)
 - Validate upsampling error < 0.1 (calculated as absolute difference between original vector area and rasterized area).
 - **Action**: If error > 0.1, log ERROR to stderr and exit with code 1.
 - Handle missing data: Read threshold from `config.MISSING_DATA_THRESHOLD`; Log WARNING if exceeded; proceed without warning if below.
- [X] T015 [US1] Create aligned GeoTIFF stack output in `data/processed/`
 - Ensure all output rasters share identical dimensions, origin, and CRS.
 - **Verification**: Run runtime check `assert rasters.shape == rasters[0].shape` and `assert rasters.crs == rasters[0].crs`.
 - Generate `data/metadata.json` with fetch timestamps and checksums **ONLY if the pipeline completed successfully (exit code 0)**.
 - **Constraint**: If T014b triggers an exit (code 1), T015 MUST NOT generate `data/metadata.json`.
- [X] T016 [US1] Add validation logic to verify non-null overlap region in `code/ingest.py`

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

- [X] T019 [US2] Implement correlation matrix generation in `code/eda.py` (FR-004)
 - Calculate Pearson/Spearman correlations between covariates and temperature.
 - Output to `data/results/correlation_matrix.csv`.
- [X] T020 [US2] Implement spatial autocorrelation analysis in `code/eda.py` (FR-004)
 - Compute Moran's I for the temperature raster.
 - Compute variograms for the target variable.
 - Output statistics to `data/results/spatial_stats.json`.
- [X] T021 [US2] Generate EDA summary report in `data/results/eda_report.md`
 - **Implementation Logic**:
 1. Aggregate findings from T019 (correlations) and T020 (Moran's I, variograms).
 2. Incorporate findings from **output file `data/processed/socioeconomic_proxies.tif`** and **log status** of **T021a** (socioeconomic proxies).
 3. **Missing Confounds Section**: If T021a failed or proxies were missing (indicated by log or missing file), explicitly list "Missing Confounds" with details from T021a log.
 4. Write structured markdown to `data/results/eda_report.md`.
 - **Constraint**: Explicitly incorporate findings from T021a. If T021a failed, the report MUST include a "Missing Confounds" section detailing the limitation rather than ignoring it.
- [X] T022 [US2] Visualize variogram and correlation heatmaps in `data/results/eda_plots.png`
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

- [X] T026a [US3] Implement Memory Safety Check in `code/modeling.py` (Memory Safety)
 - **Action**: Check memory footprint of full dataset.
 - **If memory > 5GB or N > 500k**: Trigger **Spatial Block Sampling** (T026b) to reduce N.
 - **If memory <= 5GB**: Proceed to T027-T029 with full dataset. Set flag `sampling_applied: false`.
- [X] T026b [US3] Implement Spatial Block Sampling (1km grid) algorithm in `code/modeling.py` (Plan Requirement)
 - **Input**: Full dataset from T026a check.
 - **Action**: Partition the raster grid into 1km x 1km blocks. **Stratified selection by UTM grid quadrant** to reduce N < 500k while preserving spatial autocorrelation structure.
 - **Output**: Sampled dataset and `sampling_applied` flag.
 - **Constraint**: Must preserve the spatial block structure required for Moran's I and variogram estimation. **DO NOT** use random pixel sampling.
- [X] T026c [US3] Implement Degradation Logic in `code/modeling.py` (Memory Safety) - **Conditional Branch of T026b**
 - **If sampling reduces data**: Proceed to T027-T029 with the sampled dataset. Set flag `sampling_applied: true`.
 - **If sampling fails to reduce data sufficiently**: **Degrade to OLS-only** (skip T028/T029), run T027 (OLS with HAC), and set flag `model_type: OLS_DEGRADED`. **Do NOT fail loudly**; this is the Plan's required fallback.
 - **Logging**: Log the reason for degradation to `data/results/metrics.csv` and stdout. **MUST explicitly log the exact string `model_type: OLS_DEGRADED`** to satisfy Spec FR-005 traceability.
- [X] T027 [US3] Implement OLS baseline model in `code/modeling.py` (FR-005)
 - Fit OLS with spatially robust standard errors (HAC).
 - Record coefficients and diagnostics.
 - **Input**: Use sampled dataset if `sampling_applied: true` from T026.
- [X] T028 [US3] Implement SAR (Spatial Lag/Error) model in `code/modeling.py` (FR-005)
 - Fit SAR model.
 - **Constraint**: If `model_type: OLS_DEGRADED` is set by T026c (due to sampling failure), **skip** this task and log a warning. Do NOT fail loudly.
 - If memory constraints are hit (and sampling was not attempted or failed), degrade to OLS (already handled by T026c).
 - **Input**: Use sampled dataset if `sampling_applied: true` from T026.
- [X] T029 [US3] Implement GWR model in `code/modeling.py` (FR-005)
 - Fit GWR model.
 - **Constraint**: If `model_type: OLS_DEGRADED` is set by T026c, **skip** this task and log a warning. Do NOT fail loudly.
 - If convergence fails, **skip** and log warning (do NOT fail loudly).
 - **Input**: Use sampled dataset if `sampling_applied: true` from T026.
- [X] T030 [US3] Implement 5-fold Spatial Cross-Validation in `code/modeling.py` (FR-006)
 - Use spatial blocks to prevent data leakage.
 - **Input**: Use sampled dataset if `sampling_applied: true` from T026. If `model_type: OLS_DEGRADED`, run CV on OLS data only.
 - **Enforcement**: **Hard assertion** that `k=5` for the primary research run, overriding config if necessary to satisfy FR-006.
 - Calculate RMSE, MAE, R² for each fold.
- [X] T031 [US3] Implement Multiple-Comparison Correction in `code/modeling.py` (FR-008)
 - Apply Permutation-based FDR with Meff adjustment for p-values.
 - Output adjusted p-values for all predictors.
- [X] T032a [US3] Load literature-derived upper bounds from `data/literature_bounds.json` (FR-010)
 - Ensure the file exists and contains valid R² bounds (Source: T015b).
 - **Input**: Read from `data/literature_bounds.json`.
 - **Constraint**: If file is missing or invalid, **log a limitation and skip the gap calculation** (do NOT raise a fatal error).
- [X] T032 [US3] Implement Proxy Validity Sensitivity (FR-010)
 - **Input**: Literature bounds from T032a.
 - **Action**: Calculate the "Unexplained Variance Gap" by comparing observed R² (from T027-T029) against the literature-derived upper bounds.
 - **Method**: Calculate `Gap = Upper_Bound_R2 - Observed_R2`. **DO NOT simulate synthetic data**.
 - Output gap to `data/results/metrics.csv` as part of FR-010.
- [X] T033 [US3] Output all metrics to `data/results/metrics.csv` (SC-001, SC-002, SC-003, SC-005)
 - **Columns**: `model_type`, `RMSE`, `R2`, `MAE`, `Morans_I_residuals`, `adjusted_p_values`, `correction_method`, `unexplained_variance_gap`, **`sampling_applied`**.
 - **Constraint**: Must explicitly include `correction_method` string (e.g., "Permutation-based FDR with Meff") for every row to satisfy SC-003 traceability.
 - **Constraint**: The `R2` column must contain the **final R² of the best model** after the FR-010 validation step (T032) to satisfy SC-001.
 - **Constraint**: Must include `sampling_applied` boolean flag to distinguish full vs. sampled data runs.
- [X] T034 [US3] Implement GWR bandwidth sweep in `code/modeling.py` (FR-009)
 - **Input**: Read bandwidth values from `config.GWR_BANDWIDTHS`.
 - **Constraint**: If `config.GWR_BANDWIDTHS` is missing, empty, or non-numeric, **log a warning and degrade to OLS-only execution** (do NOT fail loudly).
 - **Logic**: Loop over the configured list (e.g., values defined in `config.GWR_BANDWIDTHS`). For each bandwidth, run GWR, record R². Handle convergence failures by logging warning and skipping iteration.
 - Record R² variation across the sweep.
- [X] T035 [US3] Generate sensitivity report in `data/results/sensitivity_report.md` (SC-004)
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
- [ ] T042 [P] Update `spec.md` to document the Plan's fallback strategy (OLS_DEGRADED) as the governing rule for memory constraints, resolving the semantic gap with FR-005.
- [ ] T043 [P] Add explicit documentation in `code/config.py` for the real data streaming strategy for large satellite datasets, referencing `rasterio` chunking or `xarray` dask, and the specific sampling rule if streaming fails.
- [ ] T044 [P] Verify that `code/ingest.py` T013 implements a hard failure (no try/except synthetic fallback) for all real data sources, and that T021a is the ONLY exception with a documented warning path.
- [ ] T045 [P] Add a pre-commit hook or CI step to validate that `data/results/metrics.csv` contains no synthetic or placeholder values (e.g., "N/A", "0.0" in unexpected fields) before any commit.
- [ ] T046 [P] Implement explicit unit tests for the `OLS_DEGRADED` fallback path in `tests/unit/test_modeling.py` to ensure the system logs the correct flag and skips SAR/GWR without crashing.
- [ ] T047 [P] Add a validation script `code/scripts/validate_data_integrity.py` that scans `data/processed/` and `data/results/` for any non-numeric or placeholder entries, failing the build if found.
- [ ] T048 [P] Update `data/metadata.json` schema to explicitly include a `streaming_method` field (e.g., "xarray_chunked", "full_load", "sampled") and `sample_size` if sampling was applied, ensuring full traceability of data processing.
- [ ] T049 [P] Create a specific task in `code/ingest.py` to handle `rasterio` chunked reading for MODIS/Landsat mosaics, ensuring that the `Memory Safety Check` (T026a) receives accurate memory estimates based on chunk size rather than full file size.
- [ ] T050 [P] Verify that `tests/unit/test_ingest.py` contains a test case that explicitly asserts a `RuntimeError` is raised if the Overpass API or Satellite source returns 0 results, ensuring no silent fallback to empty/synthetic data occurs.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **CRITICAL**: T007 (Create base data models), T015a (Verify/Update data-model.md), and T021a (Socioeconomic Proxies) MUST complete before any US1/US2 task can start.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (Phase 3)**: No dependencies on other stories.
 - **US2 (Phase 4)**: Depends on **US1 data output** (T015) and **T021a** completion.
 - **US3 (Phase 5)**: Depends on **US1 data output** (T015) and **T021a** completion.
 - **Note**: While Setup/Foundational tasks can be parallel, US2 and US3 cannot start until US1 data is ready.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **Phase 4 Tasks (T021)**: Must complete after T021a (Socioeconomic Proxies) - T021a is now in Phase 2, so it runs before Phase 4 tasks.
- **Phase 5 Tasks (T030/T031)**: Must complete before T034/T035 (Sensitivity)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes:
 - US1 can start immediately.
 - US2 and US3 **must wait** for US1 data output.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel (if no data dependencies)
- Different user stories can be worked on in parallel by different team members **only after US1 data is ready**.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for Overpass API query construction in tests/unit/test_ingest.py"
Task: "Unit test for raster reprojection and resampling logic in tests/unit/test_ingest.py"

# Launch all models for User Story 1 together:
Task: "Implement OSM vector download via Overpass API in code/ingest.py"
Task: "Implement satellite thermal data ingestion in code/ingest.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (Wait for US1 data)
 - Developer C: User Story 3 (Wait for US1 data)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All modeling tasks must respect the available RAM limit. via **Spatial Block Sampling** (T026a/T026b/T026c). If data exceeds RAM, the system must **execute sampling** (T026b) to reduce N. If sampling fails to reduce N sufficiently, the system must **degrade to OLS** (T026c) rather than failing. No GPU usage allowed.
- **Deferred Values**: `MAX_BLOCKS`, `MISSING_DATA_THRESHOLD`, `TIME_WINDOW_THRESHOLD` are defined in `config.py` as placeholders; implementers must ensure code reads these from config, and fail loudly if missing/invalid **UNLESS** the Spec/Plan mandates a graceful fallback (e.g., T005, T032a, T034).
- **FR-005 Integrity**: If memory constraints prevent fitting three models, the system must **degrade to OLS** (as per Plan) rather than failing. The spec requires three models, but the Plan's fallback strategy is the governing rule for execution (see T042).
- **Data Integrity**: All data loading tasks (T012, T013, T021a) MUST fail loudly if real data sources are unreachable, except for T021a which logs a warning and continues if socioeconomic proxies are missing. Synthetic fallbacks are strictly prohibited to prevent fabrication.
- **Ingestion Order**: T021a (Socioeconomic Proxies) is now in Phase 2 to ensure all ingestion occurs before Analysis (Phase 4).
- **Data Streaming Requirement (FR-002)**: For large satellite datasets (MODIS/Landsat) that exceed RAM limits, tasks MUST implement **streaming** of the full dataset using `rasterio` or `xarray` chunking, rather than loading the entire mosaic into memory. If streaming is not feasible for a specific tile, the task MUST use a **real, documented sample** (e.g., first N pixels) and explicitly state the sampling limitation in `data/metadata.json`. **Synthetic data generation is strictly forbidden.**
- **Spatial Block Sampling Integrity**: T026b MUST ensure that the sampling process preserves the spatial autocorrelation structure. The implementation must verify that the sampled blocks are spatially contiguous or representative of the full grid, and MUST NOT use random pixel sampling as a fallback.
- **Model Fallback Logic**: The logic in T026c must be robust: if sampling is triggered but fails to reduce N below 500k, the system MUST degrade to OLS (T027) and log `model_type: OLS_DEGRADED`. It MUST NOT crash or attempt to fit SAR/GWR.
- **Revision Concerns**: Tasks T043, T044, and T045 address the critical need for explicit documentation of streaming strategies, strict enforcement of "fail loudly" data policies, and validation against synthetic data injection in final outputs.
- **Graceful Degradation Updates**: Tasks T005, T032a, and T034 have been updated to implement graceful degradation (logging limitations or falling back to OLS) instead of raising fatal errors, ensuring compliance with Spec FR-005 and FR-010.
- **New Revision Concerns**: Tasks T046-T050 address the specific need to validate the OLS fallback path, enforce data integrity checks on output metrics, and ensure streaming logic is explicitly tested and documented to prevent silent failures or data fabrication.
