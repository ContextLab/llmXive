# Tasks: The Role of Temporal Discounting in Procrastination on Cognitive Tasks

**Input**: Design documents from `/specs/001-temporal-discounting-procrastination/`
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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn` dependencies
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/raw/` and `data/processed/` directory structure
- [X] T005 [P] Implement `requirements.txt` with pinned versions for reproducibility
- [ ] T006 [P] Configure `pytest` framework and directory structure
- [X] T007 Create `code/__init__.py` and base configuration loader
- [X] T008 [P] Setup seed management: Create `code/config.py` to load `RANDOM_SEED` and provide `get_random_state()` helper; explicitly pass `random_state` to all stochastic functions in `numpy`, `pandas`, `scipy` (including `stats`), and `sklearn` to ensure reproducibility per Constitution I.
- [ ] T009 [P] Implement data checksum verification utility in `code/utils/checksum.py` AND integrate it to write/update the `artifact_hashes` map in `state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml` for every raw/processed artifact, ensuring Single Source of Truth traceability per Constitution Principle III and V.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest, harmonize, and process raw data (or DGP) into a unified analysis-ready dataset with calculated discount rates.

**Independent Test**: The pipeline can be fully tested by executing the data ingestion script and verifying the output DataFrame contains the required columns (`discount_rate_k`, `procrastination_score`, `wm_accuracy`, `wm_rt`, `age`, `gender`, `education`) with zero null values in key predictor/outcome columns after imputation or filtering.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests are written first (TDD) but listed here to reflect dependency on code structure created by T013-T018.

- [X] T010 [P] [US1] Unit test for DGP parameter generation in `tests/test_ingestion.py`
- [X] T011 [P] [US1] Unit test for hyperbolic model fitting edge cases (failure cases) in `tests/test_modeling.py`
- [X] T012 [P] [US1] Integration test for full data harmonization pipeline in `tests/test_integration.py`

### Implementation for User Story 1

- [X] T013 [US1] **PRE-CHECK**: Implement DGP Configuration Validator in `code/ingestion.py`. This task validates the DGP parameters (schema definition, expected columns, reliability targets) *before* data generation. It must verify that the configuration matches the spec's requirements (e.g., Cronbach's alpha targets) and raise `SystemExit(1)` if the DGP config is invalid.
- [~] T014 [US1] **DATA GENERATION**: Implement Data Generating Process (DGP) generator in `code/ingestion.py`. This task MUST generate **three distinct CSV files** (`data/raw/delay_discounting.csv`, `data/raw/procrastination.csv`, `data/raw/nback.csv`) simulating N=500 participants based on literature parameters. Each file must contain distinct experimental paradigm data (e.g., indifference points for discounting, scale responses for procrastination, accuracy/RT for n-back). Use `get_random_state()` from T008. <!-- FAILED: unspecified -->
- [X] T014b [US1] **RELIABILITY CHECK**: Implement Reliability Verification in `code/ingestion.py`. This task MUST calculate Cronbach's alpha for each of the three generated synthetic datasets. If any alpha < 0.7, it MUST raise `SystemExit(1)` with message "CRITICAL: Synthetic data reliability below threshold (alpha < 0.7)". This task runs after T014 and before T015a.
- [X] T015a [US1] **HARMONIZATION**: Implement data harmonization and merging logic in `code/ingestion.py`. This task reads the three distinct source files generated by T014, merges them using `participant_id`, and handles ID matching. It must check for >10% drop due to ID mismatch and flag/halt if exceeded. [UNRESOLVED-CLAIM: c_849523a5 — status=not_enough_info]
- [~] T015b [US1] **CRITICAL HALT (Data)**: Implement validation logic to check for missing core constructs (`discount_rate_k`, `procrastination_score`, `wm_accuracy`) in the *generated and harmonized* data. If any are missing, **Raise SystemExit(1)** with message "CRITICAL: Missing core construct: {col}". This task MUST execute after T015a (to ensure data exists) and before T015c (model fitting).
- [X] T015c [US1] **MODEL FITTING**: Implement hyperbolic model fitting function `fit_hyperbolic_model` in `code/modeling.py` using `scipy.optimize.curve_fit` (uses `get_random_state()`). This task calculates `discount_rate_k` for each participant in the harmonized dataset.
- [ ] T016 [US1] **MISSING DATA HANDLING**: Implement missing data handling logic in `code/ingestion.py`. If missing covariates (age, gender) >10%, **flag for reduced model** by writing `data/processed/model_config.json` with `reduced_model: true` and excluding those covariates; otherwise perform listwise deletion or mean imputation. This task MUST run *before* T018 and write the config file so downstream tasks can read it.
- [ ] T018 [US1] **WRITE DATASET**: Write the final harmonized dataset to `data/processed/harmonized_dataset.parquet` (only if T015b passed and T016 completed).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Moderation Regression Analysis (Priority: P2)

**Goal**: Execute OLS regression to test the primary hypothesis (moderation effect) and calculate VIF.

**Independent Test**: The analysis can be fully tested by running the regression script and verifying that the output includes a coefficient and p-value for the interaction term (`log(k) * wm_metric`), and that model assumptions (VIF) are reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for interaction term creation and mean-centering in `tests/test_modeling.py`
- [ ] T020 [P] [US2] Unit test for VIF calculation and threshold flagging in `tests/test_modeling.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement log-transformation of discount rate (`log(k)`) and mean-centering of predictors in `code/modeling.py`
- [ ] T022 [US2] Implement OLS regression model construction with interaction term in `code/modeling.py` (FR-004). **Read `data/processed/model_config.json` from T016**: if `reduced_model` is true, exclude flagged covariates from the model.
- [ ] T023 [US2] Implement VIF calculation and reporting logic (flag if > 5) [UNRESOLVED-CLAIM: c_39b28774 — status=not_enough_info] in `code/modeling.py` (FR-005)
- [ ] T024 [US2] Implement extraction of coefficients, p-values, and confidence intervals for the interaction term
- [ ] T032b [US2] **Intermediate Monitoring**: Wrap T021-T024 execution in `memory_profiler` and `time` module. If `max_memory_mb > 7168` or `elapsed_time` exceeds 50% of 6h limit, **Raise SystemExit(1)**.
- [ ] T025 [US2] Save regression results summary to `data/processed/regression_results.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform bootstrapping and sensitivity analysis to verify stability of the interaction effect.

**Independent Test**: The robustness check can be independently tested by running the bootstrapping script and verifying that the confidence intervals for the interaction coefficient do not include zero (if the primary effect was significant) or that the stability metric is calculated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for bootstrap resampling logic (1000 resamples) in `tests/test_robustness.py`
- [ ] T027 [P] [US3] Unit test for sensitivity analysis threshold sweeps in `tests/test_robustness.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement bootstrapping routine (1000 resamples) to generate 95% CI for interaction coefficient [UNRESOLVED-CLAIM: c_c23041a2 — status=not_enough_info] in `code/robustness.py` (FR-006)
- [ ] T029 [US3] Implement sensitivity analysis for WM load threshold (median, ±0.05*SD, ±0.10*SD) and discount rate in `code/robustness.py` (FR-007)
- [ ] T030 [US3] Implement logic to calculate `instability_ratio` = (count of thresholds where 95% CI crosses zero) / (total thresholds). **Flag instability if `instability_ratio > 0.5`** (SC-004).
- [ ] T031 [US3] Aggregate all results (primary, bootstrap, sensitivity, instability_ratio) into a final `data/processed/final_analysis_report.json`. **Explicitly mandate writing the `instability_ratio` flag, the raw threshold sweep data (threshold values and corresponding p-values), and the variation report required by FR-007 to this JSON file.**
- [ ] T032 [US3] **Final Verification**: Verify total runtime and memory usage stay within 6h/7GB limits on CPU (FR-010). Use `memory_profiler` and `time` module; assert `max_memory_mb < 7168` and `elapsed_time < 21600`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Update `README.md` with execution instructions and DGP explanation
- [ ] T034 Code cleanup and refactoring for readability: Refactor `code/ingestion.py` and `code/modeling.py` to reduce cyclomatic complexity < 10 as measured by `radon` **AND** remove all `TODO` comments.
- [ ] T035 [P] Add docstrings to all public functions in `code/`
- [ ] T036 Run full pipeline end-to-end to generate final artifacts
- [ ] T037 Update `state.yaml` with execution hashes and completion status

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US2

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
Task: "Unit test for DGP parameter generation in tests/test_ingestion.py"
Task: "Unit test for hyperbolic model fitting edge cases in tests/test_modeling.py"

# Launch all models for User Story 1 together:
Task: "Implement Data Generating Process (DGP) generator in code/ingestion.py"
Task: "Implement hyperbolic model fitting function in code/modeling.py"
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Regression)
 - Developer C: User Story 3 (Robustness)
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
- **CRITICAL**: T015b MUST raise SystemExit(1) on missing core constructs.
- **CRITICAL**: T016 MUST write `data/processed/model_config.json` to signal reduced model path.
- **CRITICAL**: T008 MUST ensure seeds are passed to ALL stochastic functions.
- **CRITICAL**: T032a/T032b MUST raise SystemExit(1) on resource limit breach.
- **CRITICAL**: T014 MUST generate three distinct CSV files.
- **CRITICAL**: T014b MUST halt if Cronbach's alpha < 0.7.