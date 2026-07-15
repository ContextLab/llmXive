# Tasks: Predicting Corrosion Potential from Composition and Environment

**Input**: Design documents from `/specs/001-predict-corrosion-potential/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 Initialize project directory structure: `code/`, `data/`, `data/raw/`, `data/processed/`, `data/logs/`, `state/`, `contracts/`, `config/`, `code/data/`, `code/models/`, `code/utils/`, `code/tests/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create schema contracts: `contracts/ingest.schema.yaml` and `contracts/dataset.schema.yaml`
- [ ] T005 [P] Implement custom exceptions in `code/utils/exceptions.py` (DataInsufficientError, SchemaMismatchError)
- [ ] T006 [P] Setup reproducible logging infrastructure in `code/utils/logging.py` (FR-010)
- [ ] T007 Create base data model classes for AlloyRecord, EnvironmentRecord, CorrosionMeasurement
- [ ] T008 Setup environment configuration management for random seeds and file paths
- [X] T009 Define schema validation utility in `code/utils/validation.py` to enforce non-null constraints (Dependency: T004)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download and preprocess NIST Corrosion Database records into a unified, clean dataset with strict schema validation and leakage prevention.

**Independent Test**: Execute `code/data/download_nist.py` and `code/data/preprocess.py`; verify output `data/processed/corrosion_dataset.parquet` exists, contains ≥500 records, has no nulls in critical fields, and passes GroupKFold (k=5) validation (≥10 alloy designations).

### Tests for User Story 1 (SEQUENTIAL - Write First) ⚠️

> **NOTE**: Write these tests FIRST. Run them to ensure they FAIL before implementation. These are NOT parallel with implementation. They must be written and run to fail before T012-T017 can be implemented.

- [X] T010 [US1] Write unit test for schema validation logic in `tests/unit/test_data_validation.py`. **Constraint**: Must fail before T012-T017 implementation.
- [X] T011 [US1] Write integration test for data ingestion pipeline in `tests/integration/test_data_ingestion.py`. **Constraint**: Must fail before T012-T017 implementation.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data/download_nist.py` to fetch from NIST-IR-8200. **Pre-fetch**: Check verified-datasets registry/config for URL. **Halt**: If URL is missing, raise `DataInsufficientError` immediately and halt (Plan Data Acquisition Strategy). **Fetch**: Implement retry logic (exponential backoff, limited retries) and halt on /404 (FR-001, FR-002)
- [X] T013 [P] [US1] Implement `code/data/preprocess.py` to encode weight fractions, filter missing pH/temp, and exclude outliers (FR-003, FR-013)
- [~] T014 [US1] Implement schema validation step in `code/data/preprocess.py` to enforce non-nulls and count records. **Halt Condition**: If <500 records, write exact record count to `data/logs/pipeline.log` AND `data/logs/diagnostics/count_report.txt`, then raise `DataInsufficientError` (FR-014, Plan Data Acquisition Strategy). **Note**: This task enforces Spec FR-014's `DataInsufficientError` requirement.
- [X] T015 [US1] Implement `code/data/split.py` with **GroupKFold (k=5)** logic to ensure statistical power while preventing alloy leakage. **Pre-check**: Verify dataset contains ≥10 specific alloy designations; if not, raise `DataInsufficientError`. **Output**: Generate train/test indices for multiple folds ensuring no alloy overlap between folds (FR-004, FR-012, Plan Complexity Tracking). **Note**: This task implements the Plan's GroupKFold (k=5) strategy which supersedes the Spec's single-split LOSO requirement to ensure sufficient test set size for statistical power.
- [ ] T016 [US1] Add diagnostic logging for excluded records (missing pH, extreme pH) to `data/logs/pipeline.log`
- [ ] T017 [US1] Verify split integrity: ensure strict GroupKFold constraint is met (zero overlap of specific_alloy_designation_id between folds). **Deliverable**: Write `data/logs/split_validation.json` containing fold statistics and overlap verification (SC-004).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Evaluation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting regressors on the preprocessed dataset to predict corrosion potential and evaluate performance against null baselines.

**Independent Test**: Run `code/models/train.py` and `code/models/evaluate.py`; verify `data/processed/model_results.json` contains R² and RMSE for both models, and that the best model is classified as "learnable" if R² > 0.0 (p < 0.05).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for model training timing (must complete <30 mins) in `tests/unit/test_model_timing.py`
- [ ] T019 [P] [US2] Integration test for end-to-end training and evaluation in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/models/train.py` to train Random Forest and Gradient Boosting (CPU-only, scikit-learn) with `random_state=42` using GroupKFold (k=5) indices (FR-005)
- [ ] T021 [US2] Implement `code/models/evaluate.py` to calculate R² and RMSE on held-out test sets from GroupKFold (k=5) and aggregate metrics (FR-006)
- [ ] T022 [US2] Implement null baseline comparison (mean prediction) and "learnable" classification logic (R² > 0.0, p < 0.05 via permutation test on aggregated predictions) (SC-001, SC-007)
- [ ] T023a [US2] Create `config/astm_g59_tolerance.yaml` and parse ASTM G59 standard to extract prediction error tolerance. If standard does not define a specific value, set a literature-derived default and log the source. (SC-002). **Note**: This task ensures a tolerance value is always defined for comparison.
- [ ] T023b [US2] Implement RMSE calculation in millivolts (mV) and compare against the tolerance defined in `config/astm_g59_tolerance.yaml`. **Verification**: Report comparison result; do not allow 'N/A' path (SC-002). **Note**: This task enforces SC-002 by requiring a comparison against a defined tolerance.
- [ ] T024 [US2] Save model artifacts and metrics to `data/processed/model_results.json` conforming to `contracts/model_results.schema.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Feature Importance Analysis (Priority: P3)

**Goal**: Generate permutation importance scores and partial dependence plots to identify key alloying elements and environmental interactions.

**Independent Test**: Run `code/models/interpret.py`; verify output includes top 5 features with p-values < 0.05 (Bonferroni/FDR corrected) and at least one partial dependence plot visualizing non-linear interaction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for permutation significance logic (sufficient permutations for stable estimation, FDR correction) in `tests/unit/test_importance_stats.py`
- [ ] T026 [P] [US3] Integration test for plot generation in `tests/integration/test_interpretability.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/models/interpret.py` to calculate permutation importance (FR-007)
- [ ] T028 [US3] Implement statistical significance testing for feature importance using **Permutation Test on Aggregated Predictions** (GroupKFold loop, a sufficient number of permutations, Bonferroni/FDR correction) to ensure continuous null distribution (FR-008, SC-003, Plan Complexity Tracking). **Note**: This task implements the Plan's 'Permutation Test on Aggregated Predictions' strategy which supersedes the Spec's 'one-sample permutation test' requirement to ensure statistical validity.
- [ ] T029 [US3] Generate partial dependence plots for top element-environment pairs (e.g., Chromium vs pH) (FR-009)
- [ ] T030 [US3] Compile summary report stating whether specific elements consistently reduce corrosion potential
- [ ] T031 [US3] Save all plots and reports to `data/processed/interpretability/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a Update README.md: Add usage instructions, installation steps, and data prerequisites
- [ ] T032b Update README.md: Add API reference for key scripts and configuration options
- [ ] T032c Update README.md: Add contribution guidelines and development setup instructions
- [ ] T033 Code cleanup and refactoring for memory efficiency
- [ ] T034 Performance optimization for data loading on GitHub Actions (CPU, limited RAM)
- [ ] T035 [P] Additional unit tests for edge cases (pH > 14, pH < 0) in `tests/unit/`
- [ ] T036 Run `quickstart.md` validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Depends on US1 completion (requires processed data)
- **User Story 3 (P3)**: Depends on US2 completion (requires trained model)

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
# Launch all models for User Story 1 together:
Task: "Implement download_nist.py with retry logic"
Task: "Implement preprocess.py for encoding and filtering"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify ≥500 records, no leakage, ≥10 alloys)
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Modeling) - *Can start only after US1 data is ready*
 - Developer C: User Story 3 (Interpretability) - *Can start only after US2 model is ready*
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
- **Critical Constraint**: Do not use synthetic data. If NIST-IR-8200 yields <500 records, the pipeline MUST halt.
- **Critical Constraint**: All models must run on CPU-only GitHub Actions runners (no CUDA, no low-bit quantization).
- **Critical Constraint**: Split strategy MUST be GroupKFold (k=5) with ≥10 specific alloy designations as per Plan and Spec constraints.
- **Critical Constraint**: ASTM G59 tolerance comparison is mandatory; if standard is ambiguous, use literature default (config file) and report result.
- **Critical Constraint**: Statistical significance testing must use "Permutation Test on Aggregated Predictions" as per Plan Complexity Tracking.
- **Note on Spec/Plan Conflicts**: Where Plan.md explicitly deviates from Spec.md (e.g., GroupKFold vs LOSO, DataInsufficientError vs SchemaMismatchError, Aggregated Predictions vs one-sample test), the Plan's strategy takes precedence for implementation tasks. These deviations are documented in the task descriptions.