# Tasks: Predicting Material Degradation Under Cyclic Loading from Public Datasets

**Input**: Design documents from `/specs/001-predict-material-degradation/`
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

- [ ] T001a [P] Create root project directory `projects/PROJ-378-predicting-material-degradation-under-cy/`
- [ ] T001b [P] Create `code/`, `data/`, `tests/`, `state/`, `docs/` directories
- [ ] T001c [P] Create `data/raw/` and `data/processed/` directories
- [ ] T001d [P] Create `code/ingestion/`, `code/validation/`, `code/reporting/`, `code/stats/`, `code/utils/` directories
- [ ] T001e [P] Create `tests/unit/` and `tests/integration/` directories

- [ ] T002 Initialize Python 3.11 project with dependencies (`code/requirements.txt`)
- [ ] T003 [P] Configure linting and formatting tools (`.pre-commit-config.yaml`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw/`, `data/processed/`)
- [ ] T005 [P] Implement base logging configuration (`code/__init__.py`, `code/logging_config.py`)
- [ ] T006 [P] Setup artifact hashing and state management (`state/projects/PROJ-378-.../artifact_hashes.yaml`)
- [ ] T007 Create base data models/entities and schema (`code/ingestion/__init__.py`, `contracts/dataset.schema.yaml`)
- [ ] T007b [P] Create `config/imputation_config.yaml` with frozen parameters (max_iter=10, tolerance) as required by Constitution Principle VI.
- [ ] T008 Configure error handling and exit codes for pipeline termination (`code/utils/exceptions.py`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Coverage Validation (Priority: P1) 🎯 MVP

**Goal**: Ingest verified public datasets (NIST, UCI, Materials Project), validate for material science columns, detect the "Coverage Gap", and generate a termination report.

**Independent Test**: The system can be tested by running the ingestion script against the verified dataset URLs and verifying the output is a `gap_report.json` detailing missing columns, with no model training attempted.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for ingestion logic in `tests/unit/ingestion/test_load_data.py`
- [ ] T011 [P] [US1] Integration test for gap detection in `tests/integration/test_gap_detection.py`

### Implementation for User Story 1

- [ ] T012a [P] [US1] Implement `load_data.py` to fetch from verified NIST/UCI URLs, apply schema validation using `contracts/dataset.schema.yaml`, and output to `data/raw/nist_uci_combined.csv`. (`code/ingestion/load_data.py`)
- [ ] T012b [P] [US1] Implement `load_data.py` extension to attempt ingestion from Materials Project (via verified URL/package), log specific failure/gap, and output to `data/raw/materials_project_attempt.csv`. (`code/ingestion/load_data.py`)
- [ ] T012c [P] [US1] Implement `load_data.py` extension to attempt ingestion from Materials Project (via verified URL/package), log specific failure/gap, and output to `data/raw/materials_project_attempt.csv`. (`code/ingestion/load_data.py`)
- [ ] T016 [US1] Implement logic in `load_data.py` to exclude rows lacking critical variables (stress_amplitude, etc.) BEFORE validation/imputation, as per FR-001. (`code/ingestion/load_data.py`)
- [ ] T013 [US1] Implement `check_columns.py` to validate `data/raw/nist_uci_combined.csv` and `data/raw/materials_project_attempt.csv` for required columns (`stress_amplitude`, `elemental_percent`, `degradation_metric`), raising ValueError on failure, and output `data/processed/validation_report.json` with keys: valid, missing_columns, row_count. (`code/validation/check_columns.py`)
- [ ] T014 [US1] Implement `gap_report.py` to generate `data/processed/gap_report.json` with specific keys: status, missing_columns, sources_checked, timestamp, exit_code. (`code/reporting/gap_report.py`)
- [ ] T015 [US1] Implement `main.py` to orchestrate Load -> Validate -> Terminate on gap, reading `data/processed/gap_report.json`. (`code/main.py`)
- [ ] T017 [US1] Add logging for "CRITICAL: COVERAGE GAP DETECTED" and exit code handling in `main.py`. (`code/main.py`)
- [ ] T023 [US1] Implement skip logic in `code/validation/impute.py` that reads `config/imputation_config.yaml` and `data/processed/gap_report.json`, logging "Imputation Skipped: Data Gap Detected" if gap exists. (`code/validation/impute.py`)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Pipeline terminates gracefully with gap report)

---

## Phase 4: User Story 2 - Feasibility Pipeline & Memory Constraints (Priority: P2)

**Goal**: Implement the logic to enforce memory/disk limits and prepare the pipeline to skip modeling if data is invalid, ensuring resource compliance.

**Independent Test**: The system can be tested by executing the script with simulated large data or memory pressure checks to verify subsampling logic or graceful exit without OOM errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for memory limit enforcement in `tests/unit/utils/test_memory_check.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement memory/disk limit check utility in `code/utils/resource_limits.py` that returns a boolean `limit_exceeded`. (`code/utils/resource_limits.py`)
- [ ] T020 [US2] Implement subsampling logic in `code/utils/subsample.py` using random sampling with random_state=42, targeting [deferred] rows or 5GB max, outputting `data/processed/sampled_data.csv`. (`code/utils/subsample.py`)
- [ ] T021 [US2] Update main.py to extend the orchestration logic in T015, invoking T020 automatically if T019 triggers `limit_exceeded`, and skip training/inference if gap detected (FR-003, FR-005, FR-006). (`code/main.py`)
- [ ] T022 [US2] Implement logging for "Training Skipped: Data Gap Detected" and "Subsampling Applied" in `main.py`. (`code/main.py`)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Data ingestion, validation, and resource safety)

---

## Phase 5: User Story 3 - Statistical Inference & Uncertainty (Priority: P3)

**Goal**: Implement the statistical inference and uncertainty modules, designed to run only if valid data were present, but currently configured to skip gracefully if the gap is detected.

**Independent Test**: The system can be tested by mocking valid data to ensure the statistical modules (t-tests, permutation tests, quantile forests) execute correctly, and by running with real data to ensure they skip with proper logging.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for statistical inference logic in `tests/unit/stats/test_inference.py`

### Implementation for User Story 3

- [ ] T025 [P] [US3] Implement `t_test.py` in `code/stats/t_test.py` to perform t-tests on ElasticNet coefficients using scipy.stats.ttest_ind, output `data/processed/t_test_report.json` with p-values and significance flags, and output status='skipped' with reason if gap detected. (`code/stats/t_test.py`)
- [ ] T026 [US3] Implement `permutation_test.py` in `code/stats/permutation_test.py` to perform permutation-based importance tests for RF/GB using sklearn.inspection.permutation_importance, output `data/processed/permutation_report.json` with adjusted p-values, and output status='skipped' with reason if gap detected. (`code/stats/permutation_test.py`)
- [ ] T027 [US3] Implement `quantile_forest.py` in `code/stats/quantile_forest.py` to generate prediction intervals (10th-90th percentiles) using sklearn.ensemble.QuantileRegressor, output `data/processed/interval_report.json` with width measurements, and output status='skipped' with reason if gap detected. (`code/stats/quantile_forest.py`)
- [ ] T028 [US3] Implement Bonferroni correction logic in `code/stats/corrections.py` to adjust p-values for multiple hypotheses. (`code/stats/corrections.py`)
- [ ] T029 [US3] Update `main.py` to conditionally call T025-T028 based on `data/processed/gap_report.json` (skip if gap detected), logging "Inference Skipped" if so. (`code/main.py`)
- [ ] T030 [US3] Create file `code/stats/interactions.py` implementing polynomial feature generation and interaction significance testing using statsmodels or sklearn PolynomialFeatures, output `data/processed/interaction_report.json`, returning status='skipped' if gap detected. (`code/stats/interactions.py`)

**Checkpoint**: All user stories should now be independently functional (Pipeline handles data gap, resource limits, and skips advanced stats gracefully)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` and `README.md`
- [ ] T032 Code cleanup and refactoring of `main.py`
- [ ] T033 Performance optimization for data loading (streaming if available)
- [ ] T034 [P] Additional unit tests for edge cases (empty datasets, missing URLs) in `tests/unit/`
- [ ] T035 Security hardening for file path handling
- [ ] T036 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for ingestion logic in tests/unit/ingestion/test_load_data.py"
Task: "Integration test for gap detection in tests/integration/test_gap_detection.py"

# Launch all models for User Story 1 together:
Task: "Implement load_data.py in code/ingestion/load_data.py"
Task: "Implement check_columns.py in code/validation/check_columns.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Verify gap detection and termination)
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
   - Developer A: User Story 1 (Ingestion & Gap Detection)
   - Developer B: User Story 2 (Resource Constraints & Skip Logic)
   - Developer C: User Story 3 (Statistical Modules & Skip Logic)
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
- **Critical Constraint**: Do NOT train models or perform inference if the "Coverage Gap" is detected. The pipeline MUST terminate gracefully.
- **Execution Order**: T012 (Load) -> T016 (Exclude) -> T013 (Validate) -> T014 (Report) -> T015 (Orchestrate).
- **Config Requirement**: T007b must be completed before T023 to ensure imputation parameters are frozen.
- **Dependencies**: T013 depends on T007 (schema); T021 depends on T019 and T020; T029 depends on T014 and T015; T025-T028 must be implemented before T029.
- **Data Flow**: T012 (Load) -> T016 (Exclude) -> T013 (Validate) -> T014 (Report).
- **Main.py Extension**: T021 and T022 extend the orchestration logic in main.py established in T015.