# Tasks: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

**Input**: Design documents from `/specs/001-statistical-analysis-urban-heat/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/raw`, `data/processed`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` pinning (`rasterio`, `geopandas`, `overpy`, `xarray`, `netCDF4`, `scikit-learn`, `pysal`, `mgwr`, `statsmodels`, `pyproj`, `earthaccess`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `utils/config.py` for city boundaries, CRS (EPSG:3857), and 30m grid parameters
- [ ] T005 [P] Implement `utils/io_helpers.py` for NetCDF/GeoTIFF reading/writing and checksumming
- [ ] T006 [P] Create `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`
- [ ] T007 Setup `pytest` configuration and contract test framework (`tests/contract/test_schemas.py`)
- [ ] T008 Implement random seed setting utility (`utils/random_seed.py`) for reproducibility

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Rasterization (Priority: P1) 🎯 MVP

**Goal**: Download vector OSM data and satellite thermal data for NYC, Chicago, LA, and align them into a unified 30m raster grid.

**Independent Test**: Verify output directory contains a single NetCDF/GeoTIFF per city where spatial intersection of valid temp and OSM covariate pixels is >99% of union, and CRS matches.

### Tests for User Story 1

- [ ] T009 [P] [US1] Contract test for aligned raster schema in `tests/contract/test_aligned_raster.py`
- [ ] T010 [P] [US1] Integration test for data alignment pipeline in `tests/integration/test_ingest_pipeline.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `code/01_ingest/fetch_osm.py` using Overpass API to download buildings, roads, and trees for NYC, Chicago, LA
- [ ] T012 [P] [US1] Implement `code/01_ingest/fetch_thermal.py` to download MODIS (MODIS thermal) and Landsat 8 thermal data from AWS Open Data for summer 2018-2022
- [ ] T012b [US1] Implement `code/01_ingest/fetch_albedo.py` to download NASA NLCD land-cover data (https://www.mrlc.gov/data) and derive `albedo.tif` (30m) for NYC, Chicago, LA. **Output**: Save the derived albedo raster specifically to `data/processed/aligned_grid/albedo.tif` to support downstream sensitivity analysis. **Depends on T011**.
- [ ] T013 [US1] Implement `code/01_ingest/align_rasters.py` as a SINGLE atomic script:
  - **Reproject**: Align OSM vectors and thermal rasters to common CRS (EPSG:3857).
  - **Aggregate**: Convert OSM building/road nodes to 30m density rasters.
  - **Aggregate**: Convert OSM tree nodes to 30m 'count per pixel' (proxy for tree presence).
  - **Compute**: Generate daytime LST composites from thermal data.
  - **Mask**: Exclude pixels with >50% cloud cover and handle missing OSM categories (impute zero/flag).
  - **Save**: Output final aligned NetCDF/GeoTIFF per city. **Depends on T011, T012, T012b**.
- [ ] T014 [US1] Add error handling for Overpass timeouts and missing satellite tiles
- [ ] T015 [US1] Add logging for data ingestion steps and checksum verification

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Exploratory Analysis and Spatial Autocorrelation (Priority: P2)

**Goal**: Generate statistical summaries and spatial diagnostics (Moran's I, variograms) to assess data-variable fit.

**Independent Test**: Verify script outputs correlation summary table and variogram plots confirming spatial autocorrelation.

### Tests for User Story 2

- [ ] T016 [P] [US2] Contract test for spatial diagnostic schema in `tests/contract/test_spatial_diag.py`
- [ ] T017 [P] [US2] Integration test for EDA pipeline in `tests/integration/test_eda_pipeline.py`

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `code/02_eda/spatial_stats.py`:
  - Calculate Pearson/Spearman correlations between OSM covariates and temperature
  - Compute Moran's I on temperature residuals
  - Calculate Variance Inflation Factor (VIF) and flag collinear variables (VIF > 5)
- [ ] T019 [US2] Implement `code/02_eda/plots.py` to generate variogram plots and correlation heatmaps
- [ ] T020 [US2] Implement logic to handle negligible spatial autocorrelation (Spec Edge Cases):
  - **Trigger**: If Moran's I p-value > 0.05.
  - **Action**: Log "Spatial autocorrelation negligible" to `results/diagnostics.json`. **DO NOT SKIP** GWR/SAR fitting. The stratified sample (N ≤ 50,000) ensures tractability regardless of autocorrelation strength. Proceed to fit GWR/SAR models as required by FR-004.
  - **Output**: Write `results/diagnostics.json` with message "Spatial autocorrelation negligible; proceeding with OLS, GWR, and SAR models". **Depends on T018**.
- [ ] T021 [US2] Add output generation for summary tables and diagnostic reports

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Spatial Modeling and Validation (Priority: P3)

**Goal**: Fit OLS, GWR, and SAR models on a stratified random sample (N ≤ 50,000) with spatial cross-validation and permutation testing.

**Independent Test**: Verify JSON output contains RMSE/R² for each model, with GWR showing significant improvement over OLS if hypothesis holds.

### Tests for User Story 3

- [ ] T022 [P] [US3] Contract test for model output schema in `tests/contract/test_model_output.py`
- [ ] T023 [P] [US3] Integration test for model training and validation in `tests/integration/test_modeling_pipeline.py`

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement `code/03_modeling/sample_data.py` to perform stratified random sampling (N ≤ 50,000) from the aligned grid
- [ ] T025a [US3] Implement `code/03_modeling/fit_models.py` (Part 1): Fit OLS baseline using `statsmodels` and save coefficients/metrics. **Depends on T024**.
- [ ] T025b [US3] Implement `code/03_modeling/fit_models.py` (Part 2): Fit GWR using `mgwr` with a **fixed default bandwidth** (e.g., 500m) for baseline comparison. **Depends on T024**.
- [ ] T025c [US3] Implement `code/03_modeling/fit_models.py` (Part 3): Fit SAR (Lag/Error) using `pysal.spreg`. **Depends on T024**.
- [ ] T026 [US3] Implement `code/03_modeling/cross_val.py` for spatial k-fold cross-validation (spatial blocks) to prevent leakage. **Depends on T025a, T025b, T025c**.
- [ ] T027 [US3] Implement `code/04_validation/perm_test.py` for toroidal shift permutation test:
  - Apply toroidal shift to **spatial block indices** to preserve block structure and prevent leakage (FR-005).
  - Generate null distribution by permuting OSM features within shifted blocks.
  - Report p-value of observed R² against null distribution. **Depends on T025a, T025b, T025c**.
- [ ] T028 [US3] Implement `code/04_validation/report_metrics.py`:
  - Report RMSE and R² for all models.
  - Apply Benjamini-Hochberg procedure (α ≤ 0.05) for FDR control on p-values.
  - **Hypothesis Test**: Implement a **Bootstrap percentile test (1000 iterations) on residuals** to test H0: R² ≤ 0.30. Write `results/r2_threshold_test.json` with pass/fail.
  - Frame all results as associational (no causal claims).
  - Compare GWR/SAR performance against OLS baseline (SC-001, SC-002).
  - Write `results/fdr_corrected_significance.csv` with adjusted p-values. **Depends on T025a, T025b, T025c, T026, T027**.
- [ ] T029a [US3] Implement `code/03_modeling/sensitivity.py` (Part 1): Calculate 'effective search radius' (median nearest-neighbor distance) from the sample data. **Define the sweep range** for FR-007 as [0.5x, 2.0x] of this calculated radius, explicitly recording these multipliers as the determined bounds for the '[deferred]' requirement. **Depends on T024**.
- [ ] T029b [US3] Implement `code/03_modeling/sensitivity.py` (Part 2): Execute GWR bandwidth sweep using the range from T029a and select optimal bandwidth via AICc minimization. Write `results/gwr_sensitivity.json` and `results/gwr_sensitivity.png`. **Depends on T025b, T029a**.
- [ ] T030 [US3] Implement `code/03_modeling/sensitivity.py` (Part 3): Sensitivity analysis on 'material albedo' (Plan Constitution Check item 7).
  - **Input**: Use land-cover derived albedo estimates from `data/processed/aligned_grid/albedo.tif` (from T012b).
  - **Action**: Re-run model sensitivity with albedo as a covariate.
  - **Output**: Write `results/albedo_sensitivity.json` quantifying variance explained by missing factors. **Depends on T025a, T025b, T025c, T012b**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` and `README.md`
- [ ] T032 Code cleanup and refactoring for CPU efficiency (tiling for raster aggregation)
- [ ] T033 Performance optimization to ensure ≤6h runtime on GitHub Actions free-tier
- [ ] T034 [P] Additional unit tests in `tests/unit/`
- [ ] T035 Run `quickstart.md` validation and verify all artifacts are reproducible

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires aligned raster data)
- **User Story 3 (P3)**: Depends on US1 and US2 completion (requires data and diagnostics)

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
- Models within a story marked [P] can run in parallel (e.g., T025a, T025c)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for aligned raster schema in tests/contract/test_aligned_raster.py"
Task: "Integration test for data alignment pipeline in tests/integration/test_ingest_pipeline.py"

# Launch all ingestion scripts together:
Task: "Implement code/01_ingest/fetch_osm.py"
Task: "Implement code/01_ingest/fetch_thermal.py"
Task: "Implement code/01_ingest/fetch_albedo.py"
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
   - Developer A: User Story 1 (Data Ingestion)
   - Developer B: User Story 2 (EDA) - *Note: Can start only after US1 data is available or with mocks*
   - Developer C: User Story 3 (Modeling) - *Note: Can start only after US1/US2 data is available or with mocks*
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
- **Critical Constraint**: All modeling tasks (US3) MUST use the stratified random sample (N ≤ 50,000) to ensure CPU tractability on cores/GB RAM. Do NOT attempt full grid GWR/SAR.
- **Data Integrity**: Do NOT fabricate data. Use real URLs from AWS/Overpass/NASA. If a dataset is missing, task obtaining a real alternative or flag the gap.
- **Dependency Note**: Tasks marked [P] can run in parallel ONLY if they do not consume the output of another task in the same phase. Explicit dependencies (e.g., "Depends on T024") override the [P] tag for execution order.