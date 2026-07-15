# Tasks: Statistical Analysis of Urban Noise Pollution

**Input**: Design documents from `/specs/001-statistical-analysis-urban-noise/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create directory structure: `data/raw`, `data/processed`, `code`, `tests/unit`, `tests/integration`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing: `pandas`, `geopandas`, `pysal`, `libpysal`, `scikit-learn`, `numpy`, `statsmodels`, `requests`, `pyarrow`, `linearmodels`, `dask`, `distributed`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes memory-safe design for FR-010.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. T005 must complete before T011.

- [X] T006 [P] Create base `SpatialGridCell` entity schema in `code/schemas/grid_cell.py` with fields: `grid_id`, `geometry`, `noise_metrics` (dict), `covariates` (dict), `date`
- [X] T007 [P] Create `code/logger.py` with `RotatingFileHandler`, specific format string `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`, and a test function `test_log_format` verifying output
- [X] T004b [P] Implement `code/hygiene.py` with `compute_and_record_checksums()` function to update `state/projects/PROJ-304-statistical-analysis-of-publicly-availab.yaml`
- [X] T005 [P] Implement synthetic data generator `code/synthetic_data.py` to create 50k grid cells with stochastic spatial parameters; **MUST pin random seed AND record generated parameters in `state/projects/PROJ-304-statistical-analysis-of-publicly-availab.yaml`**
- [ ] T005b [P] Implement memory-safe chunking in `code/synthetic_data.py` (using Dask or pandas chunking) to Implement memory-safe chunking in code/synthetic_data.py (using Dask or pandas chunking) to ensure generation of 50k cells stays <7GB RAM [UNRESOLVED-CLAIM: c_071d3c39 — status=not_enough_info], satisfying FR-010 by design

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Aggregation and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Ingest raw noise measurements and covariates, harmonize them into a unified spatial grid in WGS84.

**Independent Test**: The pipeline can be tested by running the data ingestion script on the synthetic data and verifying the output is a single GeoDataFrame with no missing coordinates and aligned coordinate reference systems.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for IQR outlier filter in `tests/unit/test_preprocessing.py`
- [ ] T010 [P] [US1] Integration test for data harmonization flow in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/ingestion.py` to load synthetic noise and covariate data (traffic, land use, population) <!-- ATOMIZE: requested -->
- [ ] T015 [US1] Implement `code/preprocessing.py::clean_traffic_data` to ensure `df['traffic_volume']` retains 0.0 values and only applies imputation/exclusion to `NaN` values, logging the count of excluded rows to `data/processed/exclusion_log.csv`
- [X] T012 [US1] Implement `code/preprocessing.py` to apply IQR filter (1.5x IQR) for decibel outlier removal [UNRESOLVED-CLAIM: c_78c7f411 — status=not_enough_info]
- [X] T013 [US1] Implement daily aggregation logic in `code/preprocessing.py` (mean, median, 95th percentile **per day** per grid cell); **Unit of analysis is (grid_id, date)**; Output is a DataFrame retaining daily granularity
- [X] T014 [US1] Implement spatial harmonization in `code/ingestion.py` to merge covariates into 200m grid cells using output from T013, handling missing covariates via exclusion and **logging a WARNING level message indicating the number of excluded cells**
- [ ] T016 [US1] Write harmonized dataset to `data/processed/harmonized.parquet` and update checksums

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline and Spatial Model Fitting (Priority: P2)

**Goal**: Fit OLS, Spatial Lag, and Spatial Error models, calculating coefficients, diagnostics, and robust standard errors.

**Independent Test**: The modeling step can be tested by running the fitting script on a static subset of the data and verifying that models converge, producing coefficients and diagnostic statistics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for Moran's I calculation in `tests/unit/test_models.py`
- [X] T018 [P] [US2] Unit test for Benjamini-Hochberg FDR correction in `tests/unit/test_models.py`

### Implementation for User Story 2

- [X] T019 [US2] Implement spatial weight matrix construction in `code/models.py`: Queen Contiguity first, fallback to K-Nearest Neighbor (K=8)
- [X] T020 [US2] Implement OLS regression fitting in `code/models.py` using `statsmodels`
- [X] T021 [US2] Implement Spatial Lag and Spatial Error model fitting in `code/models.py` using `PySAL`
- [~] T022 [US2] Implement robust standard error calculation: **Conley SEs for OLS**, **HAC/Model-specific robust SEs for Spatial Lag/Error** using `linearmodels`; output p-values
- [ ] T023 [US2] Apply Benjamini-Hochberg FDR correction (α=0.05) to the p-values [UNRESOLVED-CLAIM: c_edb5a251 — status=not_enough_info] **derived from the robust SEs in T022** for primary covariates
- [ ] T024 [US2] Implement convergence fallback: if Spatial models fail, fall back to OLS but still calculate/report OLS Moran's I
- [ ] T025 [US2] Implement weight matrix failure handling: if both Queen and KNN fail, raise `SpatialWeightMatrixError("Both Queen and KNN failed")` and log CRITICAL error to halt execution
- [ ] T026 [US2] Save model outputs (coefficients, p-values, AIC, R², Moran's I) to `data/processed/model_results.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Spatial Cross-Validation and Performance Comparison (Priority: P3)

**Goal**: Perform spatial cross-validation and compare models using RMSE, R², AIC, and permutation tests.

**Independent Test**: The validation step can be tested by executing the cross-validation loop and verifying that training and test folds are spatially disjoint and metrics are aggregated correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for spatial block generation in `tests/unit/test_validation.py`
- [ ] T028 [P] [US3] Integration test for permutation test logic in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement 5-fold spatial cross-validation in `code/validation.py` ensuring spatially disjoint train/test sets
- [ ] T030 [US3] Implement performance metric calculation (RMSE, R², AIC) for each fold and model type
- [ ] T031 [US3] Implement spatial block permutation test with a sufficient number of permutations to determine statistical significance of RMSE differences
- [ ] T032 [US3] Implement logic to identify best model based on lowest AIC and significant RMSE reduction
- [ ] T033 [US3] Implement `code/validation.py::check_success_criteria(results)` which records whether Success Criteria (SC-001 to SC-005) are met and writes results to `data/processed/sc_validation_report.json`
- [ ] T034 [US3] Generate final comparison report in `data/processed/validation_report.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 Refactor `code/ingestion.py` and `code/models.py` to use `pandas` chunking or `dask` if memory usage exceeds 5GB during processing of 50k cells (ensure FR-010 compliance)
- [ ] T037 [P] Documentation updates in `docs/` (README, quickstart)
- [ ] T038 Run quickstart.md validation: `pytest tests/integration/test_quickstart.py -v --tb=short`; expect exit code 0 and [deferred] pass rate
- [ ] T039 Ensure all artifacts are checksummed and state file is updated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. T005 must complete before T011.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on models from US2

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
Task: "Unit test for IQR outlier filter in tests/unit/test_preprocessing.py"
Task: "Integration test for data harmonization flow in tests/integration/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingestion.py to load synthetic noise and covariate data"
Task: "Implement code/preprocessing.py to apply IQR filter"
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
- **CRITICAL**: All data must be synthetic (per plan.md) to validate pipeline logic; do not fabricate real-world results.
- **CRITICAL**: Ensure CPU-only constraints are met (no CUDA, 8-bit models, or heavy transformers).
- **CRITICAL**: Performance constraints (FR-010) are enforced by design in Phase 2 (T005b), not optimized later.