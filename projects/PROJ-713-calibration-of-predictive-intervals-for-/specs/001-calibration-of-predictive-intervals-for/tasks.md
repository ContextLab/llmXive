# Tasks: Calibration of Predictive Intervals for Time‑Series Forecasts

**Input**: Design documents from `/specs/001-calibration-of-predictive-intervals/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001a [P] Create `projects/PROJ-713-calibration-of-predictive-intervals-for-/code/` directory structure
- [ ] T001b [P] Create `projects/PROJ-713-calibration-of-predictive-intervals-for-/tests/` directory structure
- [ ] T001c [P] Create `data/raw/` and `data/processed/` directories
- [ ] T001d [P] Create `results/` directory structure
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `statsmodels`, `prophet`, `torch`, `properscoring`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `matplotlib`)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for hyperparams, random seeds, and path constants
- [X] T005 Implement `code/utils/logger.py` for structured logging and `code/utils/exceptions.py` for custom error handling
- [X] T006 Implement `code/data_loader.py` with:
 - Verified URL fetchers for M4 (` fallback logic or specific M4 repo URL) and UCI Electricity (`)
 - **Hard-fail mechanism**: Raise `ValueError` immediately if checksums do not match or URLs are unreachable (per FR-007)
 - **Split Logic**: Implement 80/20 split ([deferred] training, [deferred] testing) as per Constitution Principle VII and Spec FR-001. Explicitly override the plan's previous mention of "72/8/20" split; the 80/20 split is the single source of truth.
 - Streaming/chunked loading logic to handle UCI multivariate data within 7GB RAM
 - Standardization (zero mean, unit variance)
- [X] T007 Create `code/models/__init__.py` and base model interface definitions
- [X] T008 Implement `code/metrics/__init__.py` and base metric interface definitions
- [~] T009 Setup `data/raw/` and `data/processed/` directory structures with checksum verification logic
- [X] T010 Implement `tests/unit/test_data_loader.py` to verify split logic (80/20) and streaming behavior on a small mock dataset

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Empirical Coverage Assessment (Priority: P1) 🎯 MVP

**Goal**: Load M4/UCI data, fit ARIMA/Prophet/LSTM, and compute empirical coverage for 0.80/0.95 intervals.

**Independent Test**: Run pipeline on a single M4 series; verify `results/coverage.csv` contains correct nominal vs. empirical deviations.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for `data_loader` output schema in `tests/contract/test_data_schema.py`
- [X] T012 [P] [US1] Integration test for end-to-end ARIMA coverage calculation in `tests/integration/test_coverage_arima.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/models/arima_model.py`: Statsmodels wrapper, conditional variance interval generation using `conf_int` with `method='conditional'` (or equivalent explicit parameter) to ensure compliance with FR-003, error handling for non-convergence (log/skip series)
- [X] T014 [P] [US1] Implement `code/models/prophet_model.py`: Prophet wrapper, `uncertainty_samples` + residual simulation for intervals, error handling
- [X] T015 [P] [US1] Implement `code/models/lstm_model.py`:
 - Single hidden layer (32 units), max 50 epochs, early stopping (patience=5)
 - CPU-only training (no CUDA, no `load_in_8bit`)
 - **Fallback**: If intervals are invalid (NaN/Inf) or residuals are non-Gaussian (detected via variance check), switch to Empirical CDF (quantile-based) intervals as per Spec fallback logic.
 - **Stability Check**: Detect NaN/Inf; retry with reduced learning rate (Initial: 0.01, Reduction: 0.1x, Max attempts: a limited number) as per Spec Edge Cases
- [X] T016 [US1] Implement `code/metrics/coverage.py`: Compute empirical coverage rates for standard confidence levels against test set
- [X] T017 [US1] Implement `code/evaluation/runner.py` (partial): Implement single series loop for data loading, model fitting, and coverage calculation
- [~] T018 [US1] Implement `code/evaluation/runner.py` (complete): Extend loop to process all series in M4/UCI (streaming for UCI), aggregate results to `results/coverage.csv`
- [~] T019 [US1] Add error handling in `runner.py` to catch and log specific series failures (e.g., constant variance) without crashing the pipeline

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Distributional Calibration (PIT & CRPS) (Priority: P2)

**Goal**: Generate PIT histograms, perform Ljung-Box tests for uniformity, and calculate CRPS scores.

**Independent Test**: Generate PIT histogram for one model/series; verify Ljung-Box p-value logic and CRPS scalar output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for metric output schema in `tests/contract/test_metrics_schema.py`
- [X] T021 [P] [US2] Integration test for PIT uniformity test in `tests/integration/test_pit_ljung_box_test.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `code/metrics/pit.py`:
 - Calculate Probability Integral Transform for forecast errors
 - Generate histogram data
 - Perform **Ljung-Box test** for uniformity (per Constitution Principle VI and Spec FR-004, SC-002) to account for autocorrelation. **Do NOT use Kolmogorov-Smirnov test.**
 - Return p-value and histogram bins
- [ ] T023 [P] [US2] Implement `code/metrics/crps.py`:
 - Calculate Continuous Ranked Probability Score using `properscoring.crps_ensemble`
 - Ensure compatibility with both Gaussian and Empirical CDF interval types
- [ ] T024 [US2] Update `code/evaluation/runner.py` to integrate PIT and CRPS calculations into the main loop (requires T018 and T022/T023 complete)
- [ ] T025 [US2] Aggregate PIT and CRPS results to `results/distributional_metrics.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Conformal Baseline (Priority: P3)

**Goal**: Perform paired bootstrap tests for significance and implement Self-Calibrating Conformal Prediction wrapper.

**Independent Test**: Compare ARIMA vs. Prophet coverage; verify bootstrap p-value < 0.05 logic.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for bootstrap output in `tests/contract/test_bootstrap_schema.py`
- [ ] T028 [P] [US3] Integration test for conformal wrapper improvement in `tests/integration/test_conformal_improvement.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/evaluation/bootstrap_test.py`:
 - Paired bootstrap test with a sufficient number of resamples at time-series level
 - Compare coverage deviations between models
 - Return p-values for significance at α=0.05
- [ ] T030 [P] [US3] Implement `code/calibration/conformal.py`:
 - Self-Calibrating Conformal Prediction wrapper
 - CPU-optimized implementation (fixed sample size, no nested CV)
 - Compare baseline vs. wrapped empirical coverage
- [ ] T031 [US3] Update `code/evaluation/runner.py` to execute bootstrap tests and conformal wrapper on aggregated results (requires T024 and T029/T030 complete)
- [ ] T032 [US3] Output significance results to `results/significance_test.csv` and conformal comparison to `results/conformal_results.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033a [P] Generate API documentation for `code/models/` and `code/metrics/`
- [ ] T033b [P] Update `README.md` with usage guide, installation steps, and data fetch instructions
- [ ] T033c [P] Document data schemas in `docs/data_schema.md`
- [ ] T034 Code cleanup and refactoring (remove hardcoded paths, ensure seed reproducibility)
- [ ] T035a [P] Run full pipeline on M/UCI subset and record runtime in `results/benchmark_timing.csv` to verify a time limit constraint
- [ ] T035b [P] Add unit test in `tests/unit/test_conformal_constraints.py` verifying fixed sample size and no nested CV parameters
- [ ] T036 [P] Additional unit tests for edge cases (constant variance, NaN handling) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T038 Verify `state/` hashes and `updated_at` timestamps are correctly tracked

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T016 (Coverage) for full metric suite, but PIT/CRPS logic is independent
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2 for significance testing

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
Task: "Contract test for data_loader in tests/contract/test_data_schema.py"
Task: "Integration test for ARIMA coverage in tests/integration/test_coverage_arima.py"

# Launch all models for User Story 1 together:
Task: "Implement ARIMA model in code/models/arima_model.py"
Task: "Implement Prophet model in code/models/prophet_model.py"
Task: "Implement LSTM model in code/models/lstm_model.py"
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