# Tasks: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [ ] T001a [P] Create `code/` directory
- [ ] T001b [P] Create `data/raw/` directory
- [ ] T001c [P] Create `data/processed/` directory
- [ ] T001d [P] Create `artifacts/models/` directory
- [ ] T001e [P] Create `artifacts/reports/` directory
- [ ] T001f [P] Create `tests/unit/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [~] T004 Create `contracts/dataset.schema.yaml` defining required fields: `rolling_temperature` (float), `grain_size` (float), `composition` (dict of element:float), `process_type` (string)
- [~] T005 [P] Create `contracts/model_output.schema.yaml` defining output structure for models and reports
- [~] T006 [P] Implement `code/config.py` with paths, random seeds, timeout constants (extended training limit), and runner constraints
- [~] T007 Create `code/__init__.py` and `code/data/__init__.py` / `code/models/__init__.py` package structures
- [~] T008 Implement `code/main.py` orchestrator with global timeout handling and versioning hooks
- [~] T009 Setup `state/` directory and `hash_artifacts.py` script for SHA-256 hashing of data artifacts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and Variable Verification (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and validate public datasets to ensure presence of temperature, composition, and grain size, or halt with a clear error.

**Independent Test**: Execute `code/data/download.py` and verify it either produces a valid CSV with all required columns or exits with code 1 and a JSON error object `{"code": "E_DATA_MISSING",...}`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Note: These tests depend on T012+ being implemented to pass.**

- [~] T010 [P] [US1] Unit test `tests/unit/test_download.py::test_schema_precheck_skips_invalid_sources` (verifies skipping of invalid sources like Materials Project)
- [~] T011 [P] [US1] Unit test `tests/unit/test_download.py::test_filters_non_rolling_processes` (verifies exclusion of non-rolling processes)

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/data/download.py`: Schema pre-check logic to verify `rolling_temperature`, `grain_size`, `composition` in source metadata before download
- [~] T013 [US1] Implement `code/data/download.py`: Download logic for valid sources (NOMAD, OpenML) with checksum verification
- [~] T014 [US1] Implement `code/data/download.py`: Filtering logic to exclude `process_type` != 'Rolling' (Casting, SPD)
- [~] T015 [US1] Implement `code/data/download.py`: Validation logic to detect pure aluminum entries (no alloying elements); if found, output JSON error `{"code": "E_INSUFFICIENT_VARIANCE", "message": "Dataset contains only pure aluminum"}` and halt (do not use E_DATA_MISSING)
- [~] T016 [US1] Implement `code/data/download.py`: Error handling to output structured JSON error `{"code": "E_DATA_MISSING",...}` if all sources fail or variables missing
- [~] T017 [US1] Implement `code/data/download.py`: Integration with `hash_artifacts.py` to hash raw downloaded files
- [~] T018 [US1] Create `data/raw/` directory structure and ensure raw files are saved with checksums

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Interaction Feature Engineering and Baseline Modeling (Priority: P2)

**Goal**: Generate interaction features, normalize data, and train a baseline linear regression model.

**Independent Test**: Run `code/data/preprocess.py` and `code/models/baseline.py` on a sample dataset; verify output includes interaction columns and a trained linear model with coefficients.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Unit test `tests/unit/test_preprocess.py::test_interaction_feature_generation` <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 4, column 19:
 1. **Test Logic**: The test constructs a `pandas`...
 ^) -->
- [~] T020 [P] [US2] Unit test `tests/unit/test_validate.py::test_collinearity_detection` (verifies detection of |r| > 0.8)

### Implementation for User Story 2

- [~] T022 [US2] Implement `code/data/preprocess.py`: Generation of interaction features (`Temperature × %Mg`, `Temperature × %Si`, etc.) and appending to dataset (MUST precede normalization)
- [~] T021 [US2] Implement `code/data/preprocess.py`: Normalization of all numeric features (StandardScaler) - MUST follow interaction generation
- [~] T023 [US2] Implement `code/data/validate.py`: Collinearity detection logic (correlation matrix); flag pairs with |r| > 0.8
- [~] T024 [US2] Implement `code/data/validate.py`: Logic to identify chemical couplings (e.g., Mg/Si) vs. non-chemical collinearity; prepare descriptive framing
- [~] T025 [P] [US2] Implement `code/models/baseline.py`: Stratified train/val/test split by `source_study` (or random with warning)
- [~] T026 [US2] Implement `code/models/baseline.py`: Train OLS Linear Regression with interaction terms; log R², MAE, coefficients
- [~] T027 [US2] Implement `code/models/baseline.py`: Save baseline model artifact to `artifacts/models/` and log R² to `artifacts/reports/baseline_metrics.json`
- [~] T028 [US2] Update `code/main.py` to conditionally skip full grid search if $N < 100$ (disable `non_linear.py` execution)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Non-Linear Interaction Modeling and Sensitivity Analysis (Priority: P3)

**Goal**: Train a Random Forest model with grid search, perform sensitivity analysis on thresholds, and conduct confounder analysis.

**Independent Test**: Run `code/models/non_linear.py` and `code/models/sensitivity.py`; verify R² delta calculation, threshold sweep stability report, and confounder status report.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T029 [P] [US3] Unit test `tests/unit/test_non_linear.py::test_timeout_fallback_mechanism`
- [ ] T030 [P] [US3] Unit test `tests/unit/test_sensitivity.py::test_threshold_sweep_logic`

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/models/non_linear.py`: Timeout mechanism (4h limit) that wraps the training process; fallback to default params (n_estimators=100, max_depth=10) if exceeded
- [ ] T031 [US3] Implement `code/models/non_linear.py`: Random Forest training with grid search (n_estimators: 50-100, max_depth: -10) wrapped by T032
- [ ] T033 [US3] Implement `code/models/non_linear.py`: Stratified split by `source_study` for training; ensure no data leakage
- [ ] T034 [US3] Implement `code/models/non_linear.py`: Calculate and log R², MAE, RMSE; compute $\Delta R^2 = R^2_{RF} - R^2_{Linear}$
- [ ] T035 [P] [US3] Implement `code/models/sensitivity.py`: Threshold sweep logic for feature importance (0.01, 0.05, 0.1)
- [ ] T036 [US3] Implement `code/models/sensitivity.py`: Calculate stability score of top-5 significant interaction terms across thresholds; report stability value; log a warning if stability <80% (do NOT halt pipeline)
- [ ] T037 [P] [US3] Implement `code/models/confounder.py`: Confounder analysis logic; check for proxy variables (strain rate, cooling rate)
- [ ] T038 [US3] Implement `code/models/confounder.py`: If proxies exist, compare R²; if missing, report "N/A" and skip comparative R² calculation (generate JSON report with N/A status); DO NOT calculate E-values
- [ ] T039 [US3] Implement `code/models/confounder.py`: Generate JSON report for collinearity framing (chemical vs. non-chemical) and confounder status
- [ ] T040 [US3] Update `code/main.py` to orchestrate Phase 3 tasks and ensure total pipeline execution ≤ 5 hours
- [ ] T041 [US3] Run `hash_artifacts.py` on final artifacts and update `state/...yaml` with final hashes

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Update `README.md` with CLI usage examples for `download.py` and `main.py`
- [ ] T043 [P] Update `docs/api.md` with function signatures for `preprocess.py` and `non_linear.py`
- [ ] T044 Code cleanup and refactoring (remove debug prints, ensure type hints)
- [ ] T045 Generate memory profile report and verify peak usage < 6.5 GB on full dataset
- [ ] T046 [P] Additional unit tests for edge cases (pure aluminum, collinear data) in `tests/unit/`
- [ ] T047 Security hardening (ensure no hardcoded secrets, validate external URLs)
- [ ] T048 Run `quickstart.md` validation (if created) to ensure local reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data validation (US1) output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on baseline model (US2) output for R² delta calculation

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
Task: "Unit test tests/unit/test_download.py::test_schema_precheck_skips_invalid_sources"
Task: "Unit test tests/unit/test_download.py::test_filters_non_rolling_processes"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py: Schema pre-check logic"
Task: "Implement code/data/download.py: Download logic for valid sources"
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