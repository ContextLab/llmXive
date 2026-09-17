# Tasks: Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas

**Input**: Design documents from `/specs/001-ecotourism-regeneration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

## Phase 1: Setup & Spec Validation (Shared Infrastructure)

**Purpose**: Project initialization, spec validation, and basic structure

- [X] T001 Create `code/__init__.py` and `tests/__init__.py`
- [X] T002 Initialize `requirements.txt` with landsatxplore, rasterio, xarray, scikit-learn, statsmodels, pandas, pyyaml, pydantic, requests
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T045 [Spec Update] Update `specs/001-ecotourism-regeneration/spec.md` Success Criterion SC-001 to replace "[deferred]" with the explicit number "30" (e.g., "processes up to 30 valid sites "). This task MUST complete before T012b and T013.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create base configuration module `code/config.py` (constants, thresholds, paths)
- [X] T005 [P] Setup logging infrastructure in `code/logging_config.py`
- [X] T006a [P] [Data-Model] Create `site.schema.yaml` schema definition in `specs/001-ecotourism-regeneration/contracts/` using Pydantic models
- [X] T006b [P] [Data-Model] Create `timeseries.schema.yaml` schema definition in `specs/001-ecotourism-regeneration/contracts/` using Pydantic models
- [ ] T006c [P] [Data-Model] Create `output.schema.yaml` in `specs/001-ecotourism-regeneration/contracts/`. Define TWO distinct structures: 1) `FinalReport` (per FR-006) containing `regression_coefficients`, `sensitivity_analysis` (list of objects with `threshold`, `proxy_variable`, `effect_size`, `p_value`), and `data_quality_flags`. 2) `SensitivityArtifact` (per FR-004/SC-004) for the raw sensitivity sweep data. Use Pydantic models for validation.
- [X] T007 Implement memory-safe chunking utility in `code/utils/chunking.py` to ensure peak RAM <7GB. Define specific strategy: process Landsat scenes in batches, and climate data in 1-year chunks. Enforce memory limit by monitoring `psutil` and raising `MemoryError` if exceeded.
- [ ] T008 Create data directory structure and `.gitkeep` files for `data/raw/landsat`, `data/processed`, `data/ecotourism`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest, clean, and align Landsat satellite imagery time series with ecotourism site metadata for the defined study period (2000-2023).

**Independent Test**: Verify that the system outputs a consolidated CSV/Parquet file containing a representative set of paired sites with valid NDVI time series, and that data volume fits within 7GB RAM without crashing.

### Tests for User Story 1 (OPTIONAL) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Unit test for chunked download logic in `tests/unit/test_data_acquisition.py`
- [X] T011 [P] [US1] Unit test for cloud masking logic in `tests/unit/test_preprocessing.py`
- [X] T012 [US1] Integration test for full pipeline run on a subset of 2 sites in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T012b [US1] Fetch `data/raw/site_coordinates.csv` from the World Database of Protected Areas (WDPA) or a verified public source. Filter for a balanced set of sites (ecotourism and control) with biome and protection status metadata. Do NOT generate mock data. If the source is unavailable, the task MUST fail loudly.
- [ ] T012c [US1] Fetch `data/ecotourism/revenue_data.csv` from verified public conservation organization reports or tourism authority databases (e., Open Data Network, specific national park portals). Schema: `site_id`, `year` (2000-2023), `revenue_usd`, `visitor_count`, `source`. If real data is missing for a site, log a warning and exclude the site from the analysis (do NOT substitute mock data). Create `data/ecotourism/metadata.json` documenting the `source_name`, `retrieval_date`, and `preprocessing_steps` for each site.
- [ ] T013 [US1] Implement `code/data_acquisition.py`: Download Landsat Level surface reflectance data via USGS API for 30 paired sites (2000-2023) [UNRESOLVED-CLAIM: c_a271073c — status=not_enough_info] Load site coordinates from `data/raw/site_coordinates.csv`. Implement explicit sensor selection logic: Landsat 5 (2000-2011), Landsat 7 (2000-2023), Landsat 8 (2013-2023), Landsat 9 (2021-2023).
- [ ] T014 [US1] Implement `code/data_acquisition.py`: Log all API query parameters and versions to `data/raw/query_log.json`
- [X] T015 [US1] Implement `code/preprocessing.py`: Calculate NDVI from surface reflectance bands
- [X] T016a [US1] [P] Implement `code/preprocessing.py`: Implement cloud masking using USGS QA band
- [X] T016b [US1] [P] Implement `code/preprocessing.py`: Implement Fmask algorithm integration
- [ ] T017 [US1] Implement `code/preprocessing.py`: Pair sites logic. Calculate 'initial deforestation severity' as the absolute NDVI drop in the early period of the time series. Pair each ecotourism site with a control site in the same biome with an initial severity difference of ≤10%. Exclude sites with >50% data gaps. Output consolidated `data/processed/ndvi_timeseries.parquet` and `data/processed/site_metadata.csv`.
- [ ] T018 [US1] Implement `code/preprocessing.py`: Fetch and validate ecotourism revenue/visitor data from `data/ecotourism/revenue_data.csv` (produced by T012c). Validate schema and handle missing values. Output to `data/processed/ecotourism_data.csv` with metadata in `data/ecotourism/metadata.json`.
- [ ] T029 [US1] [FR-007] [Edge-Cases] Implement `code/preprocessing.py`: Handle missing revenue data: if revenue data is missing ENTIRELY for a site (all years), substitute the 'visitor count' metric for the entire site as the proxy variable. If revenue is missing for >50% of years but not entirely, use linear interpolation for single-year gaps. Log all substitutions in metadata.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Deforestation Detection and Recovery Trajectory Modeling (Priority: P2)

**Goal**: Automatically detect deforestation events (NDVI drop ≥0.30 sustained over 2 years) and calculate recovery trajectories using non-linear asymptotic models.

**Independent Test**: Run detection on synthetic data with known events; verify break-point identification and model fit (R² ≥ 0.95).

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T021 [P] [US2] Unit test for break-point detection algorithm in `tests/unit/test_detection.py`
- [X] T022 [P] [US2] Unit test for asymptotic model fitting in `tests/unit/test_detection.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `code/detection.py`: Deforestation event detection logic (NDVI drop ≥0.30, sustained ≥2 years)
- [X] T024 [US2] Implement `code/detection.py`: Filter sites with no clear deforestation event (NDVI drop <0.30)
- [X] T025 [US2] Implement `code/detection.py`: Fit non-linear asymptotic model (logistic/Gompertz) to recovery phase (mid-to-long term); verify R² ≥ 0.95
 *Note: If non-linear fit fails (R² < 0.95), linear slope is the ACCEPTED metric. *
- [X] T026 [US2] Implement `code/detection.py`: Fallback to linear slope calculation for an initial short-term window if asymptotic fit fails (R² < 0.95); mark as ACCEPTED metric per spec FR-002
- [X] T027 [US2] Implement `code/detection.py`: Handle "incomplete recovery" cases (recovery period <5 years) - flag and exclude from primary slope analysis
- [ ] T028 [US2] Output `data/processed/recovery_trajectories.parquet` containing event start/end, severity, and trajectory parameters. Columns: `site_id`, `event_start`, `event_end`, `severity`, `trajectory_params` (dict), `model_type` (asymptotic/linear), `r_squared`. Ensure this runs after T027.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Inference and Sensitivity Analysis (Priority: P3)

**Goal**: Fit linear mixed-effects models to test ecotourism association with regeneration, control for covariates, and perform sensitivity analysis on thresholds.

**Independent Test**: Run model on processed dataset; verify output includes coefficients, p-values, and sensitivity report across thresholds.

### Tests for User Story 3 (REQUIRED) ⚠️

- [ ] T030 [US3] Unit test for mixed-effects model convergence in `tests/unit/test_modeling.py`. Assert that the model converges for ≥90% of synthetic test cases with known parameters.
- [ ] T031 [US3] Unit test for sensitivity analysis logic in `tests/unit/test_modeling.py`.
- [ ] T030b [US3] Run T030 convergence test on the *actual* processed dataset (or a representative subset of 10 pairs) to verify SC-003 (≥90% convergence) before proceeding to final pipeline execution.

### Implementation for User Story 3

- [ ] T009 [US3] [FR-003] Fetch CHIRPS precipitation and MODIS temperature data for the study period (early 21st century to present). Use `xarray` and `requests` to fetch CHIRPS from NOAA/CDR public API and MODIS from NASA POWER API. Stream data in 1-year chunks to stay within RAM limits. Calculate monthly averages per site. Output to `data/processed/climate_covariates.parquet` with columns: `site_id`, `year`, `month`, `precip_mm`, `temp_c`.
- [ ] T032 [US3] [FR-003] Load climate covariates from `data/processed/climate_covariates.parquet` (produced by T009) for use in mixed-effects model; control for precipitation (CHIRPS) and temperature (MODIS).
- [ ] T033 [US3] Implement `code/modeling.py`: Fit Linear Mixed-Effects Model (LMM) with 'pair' as random effect, controlling for climate and initial severity; apply Bonferroni/Holm correction per [FR-005].
- [ ] T034 [US3] Implement `code/modeling.py`: Sensitivity analysis sweeping revenue thresholds over a concrete set of representative USD values and proxy variables (revenue vs. visitor count); perform sensitivity comparison between revenue-based and visitor-count-based models as required by [FR-007] and Edge Cases.
- [ ] T035 [US3] Implement `code/report.py`: Generate final report with regression coefficients, CIs, sensitivity tables, and data quality pass/fail flags; output to `data/processed/final_report.json` per [FR-006].
- [ ] T036 [US3] Implement `code/report.py`: Output `data/processed/sensitivity_analysis.csv` per [FR-004].

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates: Create `README.md` with setup instructions
- [ ] T038 [P] Documentation updates: Create `specs/001-ecotourism-regeneration/data-model.md` with entity descriptions
- [ ] T039 [P] Documentation updates: Create `specs/001-ecotourism-regeneration/methodology.md` with data source citations and traceability to metadata entries
- [ ] T040 Code cleanup and refactoring
- [ ] T041 [P] [SC-005] [FR-001] Performance optimization: Verify peak memory usage ≤7GB during full pipeline run
- [ ] T042 [P] Additional unit tests for edge cases (cloudy data, missing revenue) in `tests/unit/`
- [ ] T043 Run `quickstart.md` validation to ensure reproducibility on CPU-only runner

---

## Revision Tasks: Addressing Spec/Plan Clarifications

**Purpose**: Explicitly address reviewer concerns regarding Landsat operational dates, site counts, and model convergence strategies.

- [ ] T046 [Spec Update] Update `specs/001-ecotourism-regeneration/spec.md` FR-002 to explicitly state that if non-linear asymptotic fitting fails (R² < 0.95), the linear slope fallback is the primary accepted metric for that site.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately. **T045 MUST complete before T012b and T013.**
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T009 (now in Phase 5) depends on T006 (schema) for output structure, but is no longer blocking US1/US2.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User Story 1 (P1): Can start after Foundational. T013 depends on T012b. T018 depends on T012c. T029 depends on T018.
 - User Story 2 (P2): Depends on US1 completion (requires `data/processed/ndvi_timeseries.parquet` and `data/processed/ecotourism_data.csv`).
 - User Story 3 (P3): Depends on US2 completion (requires `data/processed/recovery_trajectories.parquet`). T009 (Climate) is now part of this phase.
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision Tasks**: Can be executed in parallel with Phase 1/2 or immediately after spec review.

### User Story Dependencies

- **User Story 1 (P1)**: T045 (Spec Update) -> T012b -> T013 -> T015/T016 -> T017 -> T012c -> T018 -> T029
- **User Story 2 (P2)**: Depends on US1 completion
- **User Story 3 (P3)**: Depends on US2 completion; includes T009 (Climate) and T030b (Convergence Check)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] (T005, T006a-c, T007) can run in parallel.
- Once Foundational phase completes, User Story 1 can start.
- Within US1: T012b must complete before T013. T012c must complete before T018. T013 and T012c can run in parallel. T015/T016 can run in parallel. T017 depends on T015/T016. T018 depends on T012c. T029 depends on T018.
- Once US1 completes, User Story 2 can start.
- Once US2 completes, User Story 3 can start.
- All tests for a user story marked [P] can run in parallel.
- Revision tasks (T046) can be executed in parallel with development tasks as they only modify documentation.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (including T045 Spec Update)
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T012b -> T013 -> T015 -> T017 -> T012c -> T018 -> T029)
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

1. Team completes Setup + Foundational (T006a-c, T005, T007) together. T045 runs in parallel.
2. Once Foundational is done:
 - Developer A: User Story 1 (T012b -> T013 -> T015 -> T017 -> T012c -> T018 -> T029)
 - Developer B: Revision Tasks (T046)
3. Once US1 completes:
 - Developer A: User Story 2
4. Once US2 completes:
 - Developer A: User Story 3 (including T009, T030b)
5. Stories complete and integrate sequentially

---

## Notes

- [P] tasks = different files, no dependencies (within same phase/story)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Spec.md Update Required: SC-001 '[deferred]' site count needs explicit number '30' (T045).
- Spec.md Update Required: FR-002 '2-year sustained drop' definition may need clarification to align with 'break-point' logic.
- Spec.md Update Required: FR-002 non-linear model requirement for short windows risks non-convergence; linear fallback is ACCEPTED metric if R² < 0.95 (T046).
- Real Data Only: T012c and T012b MUST fetch real data; mock generation is forbidden.
- Authentication: T009 uses public APIs (NOAA/NASA) requiring no auth.
- Sensor Logic: T013 uses explicit year ranges for Landsat 5/7/8/9.