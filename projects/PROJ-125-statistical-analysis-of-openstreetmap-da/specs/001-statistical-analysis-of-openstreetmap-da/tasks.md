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

- [X] T001 Create `code/scripts/setup_dirs.py` to create project directory structure (`code/`, `data/`, `tests/`, `docs/`, `data/raw/`, `data/processed/`, `data/results/`)
- [X] T002 Create `requirements.txt` with pinned versions (osmnx, geopandas, rasterio, xarray, scikit-learn, pysal, statsmodels, numpy, pandas, joblib, pytest)
- [ ] T003 Create `.gitignore` and `.env.example` files
- [ ] T015a [Foundational] Verify `data-model.md` exists in `specs/001-urban-heat-osm/` and update it with implementation-specific reprojection/resampling details (FR-003)
- [X] T015b [Foundational] Create `data/literature_bounds.json` with literature-derived R² upper bounds for OSM-only models (Source: verified research in `research.md`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` with city definitions, CRS settings (EPSG:3857/Local UTM), path constants, and `MAX_BLOCKS=[DEFERRED]` (placeholder referencing plan.md)
- [X] T005 [P] Implement memory safety utilities (`code/utils/memory.py`) for matrix size estimation and **safety checks** (NOT sampling) to ensure data fits within RAM; if data exceeds limits, the utility must raise a fatal error to satisfy spec assumptions.
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging.py` with file and stdout handlers
- [ ] T007 [P] Create base data models and schema validation in `code/models/` (CityBoundary, RasterCovariate, TemperatureRaster) - **Required for US1 ingestion tasks.**
- [ ] T008 Configure environment variable management (`.env` support) for API keys (Overpass/AWS)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Rasterization (Priority: P1) 🎯 MVP

**Goal**: Ingest raw vector data from OpenStreetMap (OSM) and satellite thermal imagery (MODIS/Landsat), align them to a common CRS, and generate aligned 30m resolution raster covariates and target variables.

**Independent Test**: Run the data pipeline for New York City and verify that output GeoTIFFs have matching dimensions, CRS, and non-null values in the overlap region.

### Tests for User Story 1 (MUST FAIL BEFORE IMPLEMENTATION) ⚠️

- [X] T009 [P] [US1] Unit test for Overpass API query construction in `tests/unit/test_ingest.py`
- [X] T010 [P] [US1] Unit test for raster reprojection and resampling logic in `tests/unit/test_ingest.py`
- [X] T011 [P] [US1] Integration test for end-to-end ingestion of a single city in `tests/integration/test_ingest_pipeline.py` <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [X] T012 [US1] Implement OSM vector download via Overpass API in `code/ingest.py` (FR-001)
 - Download buildings, land-use, trees, roads for specified city boundaries.
 - Handle rate limits with exponential backoff and local caching.
 - **Constraint**: Do NOT implement synthetic fallback; raise error on download failure.
- [X] T013 [US1] Implement satellite thermal data ingestion in `code/ingest.py` (FR-002) <!-- FAILED: unspecified -->
 - Fetch MODIS/Landsat data for the **most recent 5-year period** (spec requirement).
 - Validate the time window explicitly before processing (e.g., `end_date - start_date >= 5 years`).
 - Compute daytime land-surface temperature composites.
 - Implement cloud masking and multi-date composite generation if cloud cover > 20%.
 - **Constraint**: Use real data sources only; do not fallback to synthetic temperature data.
- [X] T014a [US1] Implement raster resampling logic in `code/ingest.py` (FR-003)
 - Reproject all layers to a common CRS.
 - Resample to a standardized spatial resolution (bilinear for continuous, nearest for categorical).
- [X] T014b [US1] Implement upsampling error validation and exit logic in `code/ingest.py` (Edge Cases)
 - Validate upsampling error < 0.1 (calculated as absolute difference between original vector area and rasterized area).
 - **Action**: If error > 0.1, log ERROR to stderr and exit with code 1.
 - Handle missing data: Read threshold from `config.MISSING_DATA_THRESHOLD`; Log WARNING if exceeded; proceed without warning if below.
- [ ] T015 [US1] Create aligned GeoTIFF stack output in `data/processed/`
 - Ensure all output rasters share identical dimensions, origin, and CRS.
 - Generate `data/metadata.json` with fetch timestamps and checksums **ONLY if the pipeline completed successfully (exit code 0)**.
 - **Constraint**: If T014b triggers an exit (code 1), T015 MUST NOT generate `data/metadata.json`.
- [X] T016 [US1] Add validation logic to verify non-null overlap region in `code/ingest.py`
- [X] T021a [US1] Implement ingestion of socioeconomic proxies (WorldPop/OSM height) in `code/ingest.py`
 - Attempt to fetch data; if unavailable, **log WARNING and continue** (do NOT raise error).
 - Output to `data/processed/socioeconomic_proxies.tif` if successful.
 - **Constraint**: If fetch fails, log limitation and proceed; do NOT generate synthetic proxies.
 - **Note**: Moved from Phase 4 to Phase 3 to respect 'Ingestion before Analysis' flow.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Exploratory Spatial Analysis and Autocorrelation Check (Priority: P2)

**Goal**: Perform exploratory data analysis (EDA) to quantify relationships between OSM-derived features and temperature, including correlation matrices, variograms, and spatial autocorrelation metrics (Moran's I).

**Independent Test**: Run the EDA module on the aligned rasters and verify the generation of a correlation matrix and a Moran's I statistic report.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for Moran's I calculation in `tests/unit/test_eda.py`
- [X] T018 [P] [US2] Unit test for variogram computation in `tests/unit/test_eda.py`

### Implementation for User Story 2

- [X] T019 [US2] Implement correlation matrix generation in `code/eda.py` (FR-004)
 - Calculate Pearson/Spearman correlations between covariates and temperature.
 - Output to `data/results/correlation_matrix.csv`.
- [X] T020 [US2] Implement spatial autocorrelation analysis in `code/eda.py` (FR-004)
 - Compute Moran's I for the temperature raster.
 - Compute variograms for the target variable.
 - Output statistics to `data/results/spatial_stats.json`.
- [ ] T021 [US2] Generate EDA summary report in `data/results/eda_report.md`
 - Include summary of strength and direction of linear relationships.
 - Incorporate findings from T021a (socioeconomic proxies) **if available**; handle missing file gracefully.
- [ ] T022 [US2] Visualize variogram and correlation heatmaps in `data/results/eda_plots.png`
 - If matplotlib is missing, log WARNING and skip generation (do not fail).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Spatial Regression Modeling and Validation (Priority: P3)

**Goal**: Fit multiple spatial regression models (OLS, GWR, SAR), perform spatial cross-validation to prevent leakage, evaluate performance, conduct sensitivity analysis, and validate proxy validity.

**Independent Test**: Execute the modeling pipeline on the dataset, ensuring models are trained, cross-validated using spatial blocks, and that performance metrics are logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for spatial block generation in `tests/unit/test_modeling.py`
- [ ] T024 [P] [US3] Unit test for spatial cross-validation logic in `tests/unit/test_modeling.py`
- [ ] T025 [P] [US3] Integration test for full modeling pipeline in `tests/integration/test_modeling_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement Spatial Block Sampling in `code/modeling.py` (Memory Safety)
 - **Constraint**: This task implements a **safety check** to ensure the full dataset fits in RAM. If the dataset exceeds memory limits, the pipeline must **FAIL LOUDLY** rather than subsampling, as per spec assumptions. Random pixel sampling is forbidden to preserve autocorrelation structure.
- [ ] T027 [US3] Implement OLS baseline model in `code/modeling.py` (FR-005)
 - Fit OLS with spatially robust standard errors (HAC).
 - Record coefficients and diagnostics.
- [ ] T028 [US3] Implement SAR (Spatial Lag/Error) model in `code/modeling.py` (FR-005)
 - Fit SAR model.
 - **Constraint**: If memory footprint > 5GB or N > 500k, **FAIL LOUDLY** with a specific error message indicating FR-005 cannot be satisfied. Do NOT degrade to OLS.
- [ ] T029 [US3] Implement GWR model in `code/modeling.py` (FR-005)
 - Fit GWR model.
 - **Constraint**: If convergence fails or memory constraints are hit, **FAIL LOUDLY** with a specific error message indicating FR-005 cannot be satisfied. Do NOT fallback to OLS.
- [ ] T030 [US3] Implement configurable k-fold Spatial Cross-Validation in `code/modeling.py` (FR-006)
 - Use spatial blocks to prevent data leakage.
 - Default k=5 (as per Spec FR-006), but configurable to match Plan's k-fold requirement.
 - Calculate RMSE, MAE, R² for each fold.
- [ ] T031 [US3] Implement Multiple-Comparison Correction in `code/modeling.py` (FR-008)
 - Apply Permutation-based FDR with Meff adjustment for p-values.
 - Output adjusted p-values for all predictors.
- [ ] T032a [US3] Load literature-derived upper bounds from `data/literature_bounds.json` (FR-010)
 - Ensure the file exists and contains valid R² bounds (Source: T015b).
- [ ] T032 [US3] Implement Proxy Validity Sensitivity (FR-010)
 - **Input**: Literature bounds from T032a.
 - **Action**: Conduct a sensitivity analysis by varying missing confounds (e.g., albedo, anthropogenic heat) to quantify the "Unexplained Variance Gap".
 - **Method**: Simulate the addition of missing confounds (e.g., synthetic albedo layers with realistic variance) to the model and measure the change in R² to estimate the gap.
 - Output gap to `data/results/metrics.csv` as part of FR-010 (does not map to SC-001).
- [ ] T033 [US3] Output all metrics to `data/results/metrics.csv` (SC-001, SC-002, SC-003, SC-005)
 - **Columns**: `model_type`, `RMSE`, `R2`, `MAE`, `Morans_I_residuals`, `adjusted_p_values`, `correction_method`.
 - **Constraint**: Must explicitly include `correction_method` string (e.g., "Permutation-based FDR with Meff") for every row to satisfy SC-003 traceability.
- [ ] T034 [US3] Implement GWR bandwidth sweep in `code/modeling.py` (FR-009)
 - **Default**: Sweep over `[100, 200, 500, 1000, 2000]` meters (or `config.GWR_BANDWIDTHS` if defined).
 - Record R² variation across the sweep.
- [ ] T035 [US3] Generate sensitivity report in `data/results/sensitivity_report.md` (SC-004)
 - Visualize stability of R² across bandwidths using standard deviation of R².

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036a [P] Update README.md with CLI usage examples and installation instructions
- [ ] T036b [P] Create `docs/quickstart.md` with step-by-step pipeline guide
- [ ] T037 Run linting and auto-fix tools (ruff/black) on `code/` and verify no errors remain
- [ ] T038a Profile memory usage of `code/ingest.py` and `code/modeling.py` using `memory_profiler`
- [ ] T038b Tune `MAX_BLOCKS` in `config.py` to ensure peak memory < 6GB (Safety Check Threshold)
- [ ] T039 [P] Add unit tests for `config.py` and `utils/memory.py` in `tests/unit/`
- [ ] T040 [P] Implement API key rotation logic and secure storage in `code/config.py`
- [ ] T041 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **CRITICAL**: T007 (Create base data models) and T015a (Verify/Update data-model.md) MUST complete before any US1 task (T012-T016) can start.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **Phase 4 Tasks (T021a)**: Must complete before T021 (EDA Report) - **Note**: T021a is now in Phase 3, so it runs before Phase 4 tasks.
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
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

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
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Critical Constraint**: All modeling tasks must respect the available RAM limit. via **Safety Check** (T026). If data exceeds RAM, the system must **FAIL LOUDLY** rather than degrade to a subset or subsample. No GPU usage allowed.
- **Deferred Values**: `MAX_BLOCKS`, `MISSING_DATA_THRESHOLD`, and `PROXY_VALIDITY_THRESHOLD` are defined in `config.py` as placeholders; implementers must ensure code reads these from config, not hardcodes values.
- **FR-005 Integrity**: If memory constraints prevent fitting three models, the system must **FAIL LOUDLY** rather than claiming a "degraded satisfaction". The spec requires three models; if the hardware cannot support it, the run must fail to alert the user to the constraint violation.
- **Data Integrity**: All data loading tasks (T012, T013, T021a) MUST fail loudly if real data sources are unreachable, except for T021a which logs a warning and continues if socioeconomic proxies are missing. Synthetic fallbacks are strictly prohibited to prevent fabrication.
- **Ingestion Order**: T021a (Socioeconomic Proxies) has been moved to Phase 3 to ensure all ingestion occurs before Analysis (Phase 4).