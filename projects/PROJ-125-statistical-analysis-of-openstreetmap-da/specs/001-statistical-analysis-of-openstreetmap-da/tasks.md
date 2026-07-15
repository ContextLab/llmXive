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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create project directory structure (`code/`, `data/`, `tests/`, `docs/`, `data/raw/`, `data/processed/`, `data/results/`)
- [X] T001b Create `requirements.txt` with pinned versions (osmnx, geopandas, rasterio, xarray, scikit-learn, pysal, statsmodels, numpy, pandas, joblib, pytest)
- [X] T001c Create `.gitignore` and `.env.example` files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` with city definitions, CRS settings (EPSG:3857/Local UTM), path constants, and MAX_BLOCKS=100
- [X] T005 [P] Implement memory safety utilities (`code/utils/memory.py`) for matrix size estimation and spatial block sampling logic
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging.py` with file and stdout handlers
- [ ] T007 Create base data models and schema validation in `code/models/` (CityBoundary, RasterCovariate, TemperatureRaster)
- [ ] T008 Configure environment variable management (`.env` support) for API keys (Overpass/AWS)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Rasterization (Priority: P1) 🎯 MVP

**Goal**: Ingest raw vector data from OpenStreetMap (OSM) and satellite thermal imagery (MODIS/Landsat), align them to a common CRS, and generate aligned 30m resolution raster covariates and target variables.

**Independent Test**: Run the data pipeline for New York City and verify that output GeoTIFFs have matching dimensions, CRS, and non-null values in the overlap region.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for Overpass API query construction in `tests/unit/test_ingest.py`
- [X] T010 [P] [US1] Unit test for raster reprojection and resampling logic in `tests/unit/test_ingest.py`
- [X] T011 [P] [US1] Integration test for end-to-end ingestion of a single city in `tests/integration/test_ingest_pipeline.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement OSM vector download via Overpass API in `code/ingest.py` (FR-001)
 - Download buildings, land-use, trees, roads for specified city boundaries.
 - Handle rate limits with exponential backoff and local caching.
- [X] T013 [US1] Implement satellite thermal data ingestion in `code/ingest.py` (FR-002)
 - Fetch MODIS/Landsat data for a recent multi-year period.
 - Compute daytime land-surface temperature composites.
 - Implement cloud masking and multi-date composite generation if cloud cover > 20%.
- [X] T014 [US1] Implement raster alignment and resampling in `code/ingest.py` (FR-003)
 - Reproject all layers to a common CRS.
 - Resample to a standardized coarse resolution (bilinear for continuous, nearest for categorical).
 - Validate upsampling error < 0.1; exit with code 1 if exceeded.
 - Handle missing data: Proceed without warning if ≤10%; Log WARNING if > 10%.
- [~] T015 [US1] Create aligned GeoTIFF stack output in `data/processed/`
 - Ensure all output rasters share identical dimensions, origin, and CRS.
 - Generate `data/metadata.json` with fetch timestamps and checksums.
- [~] T015a [US1] Write `data-model.md` documenting reprojection and resampling methods (SC-007)
- [X] T016 [US1] Add validation logic to verify non-null overlap region in `code/ingest.py`

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
 - Attempt to ingest socioeconomic proxies (WorldPop/OSM height) as described in Plan Phase 2.
 - If ingestion fails or data is missing, flag as a limitation in the report.
 - Include summary of strength and direction of linear relationships.
- [~] T022 [US2] Visualize variogram and correlation heatmaps (optional, if matplotlib available)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Spatial Regression Modeling and Validation (Priority: P3)

**Goal**: Fit multiple spatial regression models (OLS, GWR, SAR), perform spatial cross-validation to prevent leakage, evaluate performance, conduct sensitivity analysis, and validate proxy validity.

**Independent Test**: Execute the modeling pipeline on the dataset, ensuring models are trained, cross-validated using spatial blocks, and that performance metrics are logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for spatial block generation in `tests/unit/test_modeling.py`
- [X] T024 [P] [US3] Unit test for spatial cross-validation logic in `tests/unit/test_modeling.py`
- [X] T025 [P] [US3] Integration test for full modeling pipeline in `tests/integration/test_modeling_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement Spatial Block Sampling in `code/modeling.py` (Memory Safety)
 - Reduce data to a maximum of MAX_BLOCKS (default 100) spatial blocks (1km x 1km) by default, configurable in `code/config.py`.
 - Enforce strict random seed for reproducibility.
- [ ] T027 [US3] Implement OLS baseline model in `code/modeling.py` (FR-005)
 - Fit OLS with spatially robust standard errors (HAC).
 - Record coefficients and diagnostics.
- [ ] T028 [US3] Implement SAR (Spatial Lag/Error) model in `code/modeling.py` (FR-005)
 - Fit SAR model if memory footprint < 5GB and N < 500k.
 - If memory constraints exceeded, degrade to OLS with HAC and log `model_type: "OLS_DEGRADED"`.
- [ ] T029 [US3] Implement GWR model in `code/modeling.py` (FR-005)
 - Fit GWR if memory constraints allow.
 - If convergence fails, fallback to global OLS.
- [ ] T030 [US3] Implement configurable k-fold Spatial Cross-Validation in `code/modeling.py` (FR-006)
 - Use spatial blocks to prevent data leakage.
 - Default k=5 (as per Spec FR-006), but configurable to match Plan's k-fold requirement.
 - Calculate RMSE, MAE, R² for each fold.
- [ ] T031 [US3] Implement Multiple-Comparison Correction in `code/modeling.py` (FR-008)
 - Apply Permutation-based FDR with Meff adjustment for p-values.
 - Output adjusted p-values for all predictors.
- [ ] T032a [US3] Fetch literature-derived upper bounds for OSM-only models (e.g., EPA UHI Review 2023) and store in `data/literature_bounds.json`
- [ ] T032 [US3] Implement Proxy Validity Sensitivity (FR-010)
 - Calculate "Unexplained Variance Gap" = Literature_Max_R2 (from T032a) - Observed_R2 (from T030/T031).
 - Output gap to `data/results/metrics.csv` as SC-006.
- [ ] T034 [US3] Implement GWR bandwidth sweep in `code/modeling.py` (FR-009)
 - Sweep over a configurable set of bandwidth values immediately after GWR fitting.
 - Record R² variation across the sweep.
- [ ] T035 [US3] Generate sensitivity report in `data/results/sensitivity_report.md` (SC-004)
 - Visualize stability of R² across bandwidths using standard deviation of R².
- [ ] T033 [US3] Output all metrics to `data/results/metrics.csv` (SC-001, SC-002, SC-003, SC-005, SC-006)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T036a [P] Update README.md with CLI usage examples and installation instructions
- [X] T036b [P] Create `docs/quickstart.md` with step-by-step pipeline guide
- [~] T037a Run `ruff` and `black` to fix linting and formatting issues across `code/` <!-- FAILED: unspecified -->
- [~] T037b Remove unused imports and dead code identified by linters in `code/`
- [ ] T038a Profile memory usage of `code/ingest.py` and `code/modeling.py` using `memory_profiler`
- [ ] T038b Tune MAX_BLOCKS in `config.py` to ensure peak memory < 6GB
- [ ] T039 [P] Add unit tests for `config.py` and `utils/memory.py` in `tests/unit/`
- [ ] T040 [P] Implement API key rotation logic and secure storage in `code/config.py`
- [ ] T041 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **CRITICAL**: T007 (Create base data models) MUST complete before any US1 task (T012-T016) can start.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **Phase 5 Tasks (T032a)**: Must complete before T032 (Proxy Validity)
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
- **Critical Constraint**: All modeling tasks must respect the 7GB RAM limit via Spatial Block Sampling (MAX_BLOCKS=100) and automatic degradation to OLS if N > 500k. No GPU usage allowed.