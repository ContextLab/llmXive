# Tasks: Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas

**Input**: Design documents from `/specs/001-ecotourism-regeneration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001 Create `code/__init__.py` and `tests/__init__.py`. **Verification**: Confirm `specs/001-ecotourism-regeneration/spec.md` SC-001 explicitly states "30" (passive check).
- [ ] T001b [P] [Spec-Check] Verify `specs/001-ecotourism-regeneration/spec.md` SC-001 contains "up to 30 valid sites". **Action**: If text is missing or differs, log an error to `state/spec_validation.log` and halt. Do NOT edit spec.md.
- [ ] T001c [P] [Spec-Check] Verify `specs/001-ecotourism-regeneration/spec.md` FR-002 contains the non-linear fallback note ("If non-linear asymptotic fitting fails..."). **Action**: If text is missing, log an error to `state/spec_validation.log` and halt. Do NOT edit spec.md.
- [X] T002 Initialize `requirements.txt` with `landsatxplore>=1.0.0`, `rasterio>=1.3.0`, `xarray>=2023.1.0`, `scikit-learn>=1.2.0`, `statsmodels>=0.13.0`, `pandas>=2.0.0`, `pyyaml>=6.0`, `pydantic>=2.0.0`, `requests>=2.28.0`.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T004 Create base configuration module `code/config.py` (constants, thresholds, paths)
- [X] T005 [P] Setup logging infrastructure in `code/logging_config.py`
- [X] T006a [P] [Data-Model] Create `site.schema.yaml` schema definition in `specs/001-ecotourism-regeneration/contracts/` using Pydantic models
- [X] T006b [P] [Data-Model] Create `timeseries.schema.yaml` schema definition in `specs/001-ecotourism-regeneration/contracts/` using Pydantic models
- [ ] T006c [P] [Data-Model] Create `output.schema.yaml` in `specs/001-ecotourism-regeneration/contracts/`. Define TWO distinct structures using Pydantic models: 1) `FinalReport` (per FR-006) containing `regression_coefficients` (dict), `sensitivity_analysis` (list of objects with fields: `threshold` (float), `proxy_variable` (str), `effect_size` (float), `p_value` (float), `corrected_p_value` (float)), and `data_quality_flags` (list of strings). 2) `SensitivityArtifact` (per FR-004) for raw sensitivity sweep data containing `threshold`, `proxy_variable`, `model_params`, `metrics`. Ensure schema matches Plan.md `contracts` section exactly.
- [X] T007 Implement memory-safe chunking utility in `code/utils/chunking.py` to ensure peak RAM <7GB. Define specific strategy: process Landsat scenes in batches, and climate data in 1-year chunks. Enforce memory limit by monitoring `psutil` and raising `MemoryError` if exceeded.
- [ ] T008 Create data directory structure and `.gitkeep` files for `data/raw/landsat`, `data/processed`, `data/ecotourism`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. **Includes Climate Data Fetch (T009) to resolve blocking dependencies.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 [P] [US1/US3] Fetch CHIRPS precipitation and MODIS temperature data for the study period. **Endpoints**:
 1. CHIRPS: ` (pattern: `chirps-{version}.{year}.csv`).
 2. MODIS: ` (params: `lat`, `lon`, `start=2000-01-01`, `end=2023-12-31`, `api_key`).
 **Logic**: Stream data in time-based chunks to stay within RAM limits. Calculate monthly averages per site.
 **Reproducibility**: Log exact API query parameters, versions, and timestamps to `data/raw/query_log.json` (Constitution Principle I).
 **Output**: `data/processed/climate_covariates.parquet` with columns: `site_id`, `year`, `month`, `precip_mm`, `temp_c`.
 **This task is now in Phase 2 to ensure data availability for US1 site pairing and US3 modeling.**

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

- [ ] T012b [US1] Fetch `data/raw/site_coordinates.csv` from the World Database of Protected Areas (WDPA). **Source**: ` Name or service not known)"))]. Filter for a balanced set of sites (ecotourism and control) with biome and protection status metadata. **Failure Mode**: If the source is unavailable, the task MUST fail loudly by raising a `RuntimeError`, writing a detailed error log to `data/raw/fetch_error.log` with exit code 1, and halting execution. Do NOT generate mock data. <!-- FAILED: unspecified -->
- [ ] T012c [US1] Fetch `data/ecotourism/revenue_data.csv` from **verified conservation NGO or tourism authority reports**. **Source Strategy**: Use a pre-defined list of verified URLs:
 1. ` Name or service not known)"))] (if available)
 2. ` (if available)
 3. ` (proxy for economic activity if direct revenue is missing).
 If the specific URL fails, raise a `RuntimeError` listing all attempted URLs. **Schema**: `site_id`, `year`, `revenue_usd`, `visitor_count`, `source`.

The research question investigates the relationship between annual visitor metrics and revenue over the defined study period. The method involves a longitudinal analysis of site data across multiple years. References remain as cited. **Logic**: If real revenue data is missing **ENTIRELY** for a site (all years), substitute the 'visitor count' metric for that site as the proxy variable. **DO NOT** use linear interpolation for missing revenue data; mark as null and exclude from revenue-specific metrics. Create `data/ecotourism/metadata.json` documenting the `source_name`, `retrieval_date`, and `preprocessing_steps` (including substitution flags) for each site. **Dependency**: Must complete before T017 and T018.
- [ ] T013 [US1] Implement `code/data_acquisition.py`: Download Landsat Level surface reflectance data via USGS API for a set of paired sites spanning multiple decades. Load site coordinates from `data/raw/site_coordinates.csv`. Implement explicit sensor selection logic: Landsat (-2011), Landsat 7 (2000-2023), Landsat 8 (2013-2023), Landsat 9 (2021-2023). Use `landsatxplore` with chunked streaming to respect RAM limits.
- [ ] T014 [US1] Implement `code/data_acquisition.py`: Log all API query parameters and versions to `data/raw/query_log.json`
- [X] T015 [US1] Implement `code/preprocessing.py`: Calculate NDVI from surface reflectance bands
- [X] T016a [US1] [P] Implement `code/preprocessing.py`: Implement cloud masking using USGS QA band
- [X] T016b [US1] [P] Implement `code/preprocessing.py`: Implement Fmask algorithm integration
- [ ] T017 [US1] Implement `code/preprocessing.py`: Pair sites logic. **Dependency**: Requires site metadata from T012c (to identify ecotourism vs control) and T012b. Calculate 'initial deforestation severity' as the absolute NDVI drop in the early period of the time series. Pair each ecotourism site with a control site in the same biome with an initial severity difference of ≤10%. **Missing Data Handling**: If a site has >50% data gaps, attempt substitution with visitor count (per FR-007 via T018); exclude only if substitution is impossible. Output `data/processed/site_pairs.csv` (intermediate) and `data/processed/ndvi_timeseries.parquet` (final).
- [ ] T018 [US1] Implement `code/preprocessing.py`: Validate ecotourism revenue/visitor data from `data/ecotourism/revenue_data.csv` (produced by T012c). Validate schema and handle missing values per FR-007 (substitution logic: if revenue missing entirely, use visitor count; no interpolation). **Output**: `data/processed/ecotourism_data.csv` with metadata in `data/ecotourism/metadata.json`. **Dependency**: Requires T012c. **Note**: This task now consolidates the logic previously split between T012c and T029.

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
- [ ] T030b [US3] Run T030 convergence test on the *actual* processed dataset (or a representative subset of 10 pairs) to verify SC-002 (≥90% convergence) before proceeding to final pipeline execution. **Dependency**: Requires climate data from T009 (Phase 2).

### Implementation for User Story 3

- [X] T009 [US3] [FR-003] **Note**: This task was moved to Phase 2 (Foundational) to ensure data availability. See T009 in Phase 2.
- [ ] T032 [US3] [FR-003] Load climate covariates from `data/processed/climate_covariates.parquet` (produced by T009) for use in mixed-effects model; control for precipitation (CHIRPS) and temperature (MODIS).
- [ ] T033 [US3] Implement `code/modeling.py`: Fit Linear Mixed-Effects Model (LMM) with 'pair' as random effect, controlling for climate and initial severity; apply Bonferroni/Holm correction per [FR-005].
- [ ] T034 [US3] Implement `code/modeling.py`: Sensitivity analysis sweeping revenue thresholds over a representative range of USD values and proxy variables (revenue vs. visitor count); perform sensitivity comparison between revenue-based and visitor-count-based models as required by [FR-007] and Edge Cases.
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
- [ ] T041 [P] [SC-002] [FR-001] Performance optimization: Verify peak memory usage ≤7GB during full pipeline run
- [ ] T042 [P] Additional unit tests for edge cases (cloudy data, missing revenue) in `tests/unit/`
- [ ] T043 Run `quickstart.md` validation to ensure reproducibility on CPU-only runner

---

## Revision Tasks: Addressing Spec/Plan Clarifications

**Purpose**: Explicitly address reviewer concerns regarding Landsat operational dates, site counts, and model convergence strategies.

- [ ] T048 [Data Strategy] Refine T012b and T013 to explicitly handle the Landsat 7 SLC-off gap. Implement a gap-filling step in `code/preprocessing.py` for Landsat scenes from the post-2005 era, using neighboring pixel interpolation or masking, to prevent data gaps from triggering false deforestation events.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T009 (Climate Data) is now in Phase 2, ensuring data is available for US1/US2/US3.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User Story 1 (P1): Can start after Foundational. T013 depends on T012b. T018 depends on T012c. T017 depends on T012c (for site metadata).
 - User Story 2 (P2): Depends on US1 completion (requires `data/processed/ndvi_timeseries.parquet` and `data/processed/ecotourism_data.csv`).
 - User Story 3 (P3): Depends on US2 completion (requires `data/processed/recovery_trajectories.parquet`). T009 (Climate) is now in Phase 2, so T032/T033 can proceed immediately after US2.
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision Tasks**: Can be executed in parallel with Phase 1/2 or immediately after spec review.

### User Story Dependencies

- **User Story 1 (P1)**: T012b -> T013 -> T015/T016 -> T012c -> T017 -> T018. **Note**: T012c must complete before T017 and T018. T029 removed (logic merged into T018).
- **User Story 2 (P2)**: Depends on US1 completion
- **User Story 3 (P3)**: Depends on US2 completion; includes T030b (Convergence Check). T009 is now in Phase 2.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] (T005, T006a-c, T007, T009) can run in parallel.
- Once Foundational phase completes, User Story 1 can start.
- Within US1: T012b must complete before T013. T012c must complete before T017 and T018. T013 and T012c can run in parallel (after T012b). T015/T016 can run in parallel. T017 depends on T015/T016 and T012c. T018 depends on T012c.
- Once US1 completes, User Story 2 can start.
- Once US2 completes, User Story 3 can start.
- All tests for a user story marked [P] can run in parallel.
- Revision tasks (T048) can be executed in parallel with development tasks as they only modify documentation.
- **Parallel Note**: T009 (Climate Data) can now run in parallel with US1/US2 site processing since it is in Phase 2.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes T009 Climate Data)
3. Complete Phase 3: User Story 1 (T012b -> T013 -> T015 -> T012c -> T017 -> T018)
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

1. Team completes Setup + Foundational (T006a-c, T005, T007, T009) together.
2. Once Foundational is done:
 - Developer A: User Story 1 (T012b -> T013 -> T015 -> T012c -> T017 -> T018)
 - Developer B: Revision Tasks (T048)
3. Once US1 completes:
 - Developer A: User Story 2
4. Once US2 completes:
 - Developer A: User Story 3 (including T030b)
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
- **Critical Fix**: T012c now implements FR-007 substitution logic (visitor count) instead of exclusion.
- **Critical Fix**: T009 moved to Phase 2 to resolve blocking dependency for US1/US3.
- **Critical Fix**: T012c now includes explicit failure mode for WDPA API and specific URLs for revenue data.
- **Critical Fix**: T006c now includes specific Pydantic field definitions.
- **Critical Fix**: T029 removed; logic consolidated into T018.
- **Critical Fix**: T017 now prioritizes substitution over exclusion and outputs `site_pairs.csv`.
- **Critical Fix**: Task list order corrected to T012b -> T013 -> T015/T016 -> T012c -> T017 -> T018.
- **Critical Fix**: T009 now includes specific API endpoints and logging requirements.
- **Critical Fix**: T045 and T046 removed as they were stale tasks based on outdated spec versions.
- **Critical Fix**: T034 now includes specific threshold values [1000, 5000, 10000, 50000].
- **Critical Fix**: T012c and T018 now strictly forbid linear interpolation for missing revenue data.