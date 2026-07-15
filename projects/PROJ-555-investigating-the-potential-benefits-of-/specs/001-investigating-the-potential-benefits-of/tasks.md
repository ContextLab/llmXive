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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create `code/__init__.py` and `tests/__init__.py`
- [X] T002 Initialize `requirements.txt` with landsatxplore, rasterio, xarray, scikit-learn, statsmodels, pandas, pyyaml, pydantic
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create base configuration module `code/config.py` (constants, thresholds, paths)
- [X] T005 [P] Setup logging infrastructure in `code/logging_config.py`
- [X] T006a [P] [Data-Model] Create `site.schema.yaml` schema definition in `specs/001-ecotourism-regeneration/contracts/` using Pydantic models
- [X] T006b [P] [Data-Model] Create `timeseries.schema.yaml` schema definition in `specs/001-ecotourism-regeneration/contracts/` using Pydantic models
- [ ] T006c [P] [Data-Model] Create `output.schema.yaml` schema definition in `specs/001-ecotourism-regeneration/contracts/` using Pydantic models
- [ ] T007 Implement memory-safe chunking utility in `code/utils/chunking.py` to ensure peak RAM <7GB
- [ ] T008 Create data directory structure and `.gitkeep` files for `data/raw/landsat`, `data/processed`, `data/ecotourism`
- [ ] T009 [FR-003] Fetch CHIRPS precipitation and MODIS temperature data for a multi-decadal period spanning the early 21st century.; output to `data/processed/climate_covariates.parquet` with monthly resolution; use CHIRPS API and NASA POWER API

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest, clean, and align Landsat satellite imagery time series with ecotourism site metadata for the defined study period (2000-2023).

**Independent Test**: Verify that the system outputs a consolidated CSV/Parquet file containing a representative set of paired sites with valid NDVI time series, and that data volume fits within 7GB RAM without crashing.

### Tests for User Story 1 (OPTIONAL) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T010 [P] [US1] Unit test for chunked download logic in `tests/unit/test_data_acquisition.py`
- [~] T011 [P] [US1] Unit test for cloud masking logic in `tests/unit/test_preprocessing.py` <!-- SKIPPED: YAML+regex parse failed (while scanning a simple key
 in "<unicode string>", line 8, column 1:
 The test includes a fallback imp...
 ^
could not find expected ':'
 in "<unicode string>", line 10, column 1:
 The tests are designed to fail i...
 ^) -->
- [X] T012 [US1] Integration test for full pipeline run on a subset of 2 sites in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T012b [US1] Generate `data/raw/site_coordinates.csv` containing paired site coordinates (ecotourism and control) with biome and protection status metadata
- [ ] T012c [US1] Generate `data/ecotourism/revenue_data.csv` containing placeholder or real visitor/revenue data for multiple sites.; create `data/ecotourism/metadata.json` with source info <!-- FAILED: unspecified -->
- [~] T013 [US1] Implement `code/data_acquisition.py`: Download Landsat Level-2 data via USGS API for 30 paired sites using chunked streaming; load site coordinates from `data/raw/site_coordinates.csv`
 *Note: Implements Landsat 8/9 only (Landsat ceased operation in 2011.). Requires T044 to update spec.md FR-001.*
- [~] T014 [US1] Implement `code/data_acquisition.py`: Log all API query parameters and versions to `data/raw/query_log.json`
- [X] T015 [US1] Implement `code/preprocessing.py`: Calculate NDVI from surface reflectance bands
- [X] T016 [US1] Implement `code/preprocessing.py`: Apply cloud masking using USGS QA band or Fmask algorithm <!-- ATOMIZE: requested -->
- [~] T017 [US1] Implement `code/preprocessing.py`: Pair sites logic (same biome, similar initial NDVI drop ±10%); exclude sites with >50% data gaps; output consolidated `data/processed/ndvi_timeseries.parquet` and `data/processed/site_metadata.csv`
- [~] T018 [US1] Implement `code/preprocessing.py`: Fetch and validate ecotourism revenue/visitor data from `data/ecotourism/revenue_data.csv`; output to `data/processed/ecotourism_data.csv` with metadata in `data/ecotourism/metadata.json`
- [X] T029 [US1] [FR-007] [Edge-Cases] Implement `code/preprocessing.py`: Handle missing revenue data: if revenue column is null, use visitor count; if both null, exclude site. Log substitution in metadata.

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
 *Note: Spec.md FR-002 defines deforestation as '2-year sustained drop' which may contradict 'break-point' logic. Task implements spec as written but flags for review.*
- [X] T024 [US2] Implement `code/detection.py`: Filter sites with no clear deforestation event (NDVI drop <0.30)
- [X] T025 [US2] Implement `code/detection.py`: Fit non-linear asymptotic model (logistic/Gompertz) to recovery phase (mid-to-long term); verify R² ≥ 0.95
 *Note: If non-linear fit fails (R² < 0.95), linear slope is the ACCEPTED metric.*
- [X] T026 [US2] Implement `code/detection.py`: Fallback to linear slope calculation for an initial short-term window if asymptotic fit fails (R² < 0.95); mark as ACCEPTED metric per spec FR-002
- [X] T027 [US2] Implement `code/detection.py`: Handle "incomplete recovery" cases (recovery period <5 years) - flag and exclude from primary slope analysis
- [ ] T028 [US2] Generate `data/processed/recovery_trajectories.parquet` containing event start/end, severity, and trajectory parameters

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Inference and Sensitivity Analysis (Priority: P3)

**Goal**: Fit linear mixed-effects models to test ecotourism association with regeneration, control for covariates, and perform sensitivity analysis on thresholds.

**Independent Test**: Run model on processed dataset; verify output includes coefficients, p-values, and sensitivity report across thresholds.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T030 [P] [US3] Unit test for mixed-effects model convergence in `tests/unit/test_modeling.py`
- [ ] T031 [P] [US3] Unit test for sensitivity analysis logic in `tests/unit/test_modeling.py`

### Implementation for User Story 3

- [ ] T032 [US3] [FR-003] Load climate covariates from `data/processed/climate_covariates.parquet` (produced by T009) for use in mixed-effects model; control for precipitation (CHIRPS) and temperature (MODIS)
- [ ] T033 [US3] Implement `code/modeling.py`: Fit Linear Mixed-Effects Model (LMM) with 'pair' as random effect, controlling for climate and initial severity; apply Bonferroni/Holm correction per [FR-005]
- [ ] T034 [US3] Implement `code/modeling.py`: Sensitivity analysis sweeping revenue thresholds (low, medium, and high tiers) and proxy variables (revenue vs. visitor count); perform sensitivity comparison between revenue-based and visitor-count-based models as required by [FR-007] and Edge Cases
- [ ] T035 [US3] Implement `code/report.py`: Generate final report with regression coefficients, CIs, sensitivity tables, and data quality pass/fail flags; output to `data/processed/final_report.json` per [FR-006]
- [ ] T036 [US3] Implement `code/report.py`: Output `data/processed/sensitivity_analysis.csv` per [FR-004]

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

- [ ] T044 [P] [FR-001] [US-1] Update `specs/001-ecotourism-regeneration/spec.md` to replace "Landsat 5/8/9 " with "Landsat 8/9" in FR-001 and US-1 to reflect operational reality (Landsat missions ceased operation in 2011. [UNRESOLVED-CLAIM: c_b7c434d6 — status=not_enough_info]).
- [ ] T045 [P] [SC-001] Update `specs/001-ecotourism-regeneration/spec.md` to replace "[deferred]" in SC-001 with the explicit number "30".
- [ ] T046 [P] [FR-002] Update `specs/001-ecotourism-regeneration/spec.md` FR-002 to explicitly state that if non-linear asymptotic fitting fails (R² < 0.95), the linear slope fallback is the primary accepted metric for that site.
- [ ] T047 [P] [Plan] Update `specs/001-ecotourism-regeneration/plan.md` to confirm the 30-site target and document the specific revenue thresholds used in the sensitivity analysis.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T009 depends on T006 (schema) to write valid parquet files.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User Story 1 (P1): Can start after Foundational. T013 depends on T012b. T018 depends on T013. T029 depends on T018.
 - User Story 2 (P2): Depends on US1 completion (requires `data/processed/ndvi_timeseries.parquet` and `data/processed/ecotourism_data.csv`).
 - User Story 3 (P3): Depends on US2 completion (requires `data/processed/recovery_trajectories.parquet`).
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision Tasks**: Can be executed in parallel with Phase 1/2 or immediately after spec review.

### User Story Dependencies

- **User Story 1 (P1)**: T012b -> T013 -> T015/T016 -> T017 -> T018 -> T029
- **User Story 2 (P2)**: Depends on US1 completion
- **User Story 3 (P3)**: Depends on US2 completion

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005, T006a-c, T007) can run in parallel. T009 is NOT [P] as it depends on T006.
- Once Foundational phase completes, User Story 1 can start.
- Within US1: T012b must complete before T013. T013 must complete before T015/T016. T015/T016 can run in parallel. T017 depends on T015/T016. T018 depends on T013 (and T012c). T029 depends on T018.
- Once US1 completes, User Story 2 can start.
- Once US2 completes, User Story 3 can start.
- All tests for a user story marked [P] can run in parallel.
- Revision tasks (T044-T047) can be executed in parallel with development tasks as they only modify documentation.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T012b -> T013 -> T015 -> T017 -> T018 -> T029)
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

1. Team completes Setup + Foundational (T006a-c, T005, T007) together. T009 waits for T006.
2. Once Foundational is done:
 - Developer A: User Story 1 (T012b -> T013 -> T015 -> T017 -> T018 -> T029)
 - Developer B: Revision Tasks (T044-T047)
3. Once US1 completes:
 - Developer A: User Story 2
4. Once US2 completes:
 - Developer A: User Story 3
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
- Spec.md Update Required: Landsat 5 reference in FR-001/US1 Acceptance Scenarios contradicts operational reality; update to Landsat 8/9 only (T044).
- Spec.md Update Required: SC-001 '[deferred]' site count needs explicit number (30) (T045).
- Spec.md Update Required: FR-002 '2-year sustained drop' definition may need clarification to align with 'break-point' logic.
- Spec.md Update Required: FR-002 non-linear model requirement for short windows risks non-convergence; linear fallback is ACCEPTED metric if R² < 0.95 (T046).