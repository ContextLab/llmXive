# Tasks: Evaluating the Calibration of Predictive Uncertainty Intervals in Public Regression Benchmarks

**Input**: Design documents from `/specs/001-evaluating-the-calibration-of-predictive/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `specs/`)
- [ ] T001b [P] Create `__init__.py` files for `code/`, `code/data/`, `code/models/`, `code/analysis/`, `code/utils/`, `tests/`
- [X] T002 Initialize Python project with `requirements.txt` (scikit-learn, statsmodels, pandas, numpy, scipy, datasets, openml, pyyaml)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` with hyperparameters, seeds, and paths (ensure `data/` and `artifacts/` directories exist)
- [X] T005 [P] Implement `code/utils/logging.py` for structured logging and `code/utils/checksum.py` for artifact hashing
- [X] T006 [P] Implement `code/data/__init__.py` and base `code/data/loader.py` with strict "fail loud" logic (no synthetic fallbacks)
- [X] T007 Implement `code/data/preprocessor.py` to handle missing values, a standard train-test split with fixed seeds, and target validation
- [X] T008 Implement `code/models/base.py` defining the abstract `UncertaintyMethod` interface (fit, predict_interval)
- [ ] T009 Setup `tests/` structure with `pytest` configuration and `conftest.py` for fixtures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Benchmarking Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download public regression datasets, fit four UQ methods, and generate prediction intervals with empirical coverage metrics.

**Independent Test**: The pipeline runs on a single small dataset (e.g., Boston Housing via OpenML) and outputs a CSV with true targets, bounds, and coverage flags without runtime errors.

### Implementation for User Story 1 (Interface First)

- [ ] T018a [US1] Implement `code/main.py` CLI skeleton: Define the argument parser, directory structure, and the high-level orchestration flow (Load -> Split -> Fit -> Predict -> Metrics) without implementing the model logic yet
- [ ] T013 [P] [US1] Implement `code/models/quantile_gbt.py`: Quantile Regression using `sklearn.ensemble.GradientBoostingRegressor` for selected extreme percentiles (sub-component of Quantile Regression method)
- [ ] T013b [P] [US1] Implement `code/models/quantile_linear.py`: Quantile Regression using `sklearn.linear_model.QuantileRegressor` for extreme tail percentiles (sub-component of Quantile Regression method)
- [ ] T013c [US1] Implement `code/models/quantile_aggregator.py`: Logic to aggregate the results from T013 and T013b into a single "Quantile Regression" result set as required by FR-002, handling any conflicts or averaging strategies defined in `config.py`
- [ ] T014 [P] [US1] Implement `code/models/bayesian.py`: Bayesian Linear Regression using `sklearn.linear_model.BayesianRidge`
- [ ] T015 [P] [US1] Implement `code/models/gaussian.py`: Gaussian Process Regression using `sklearn.gaussian_process.GaussianProcessRegressor` (RBF kernel) with memory error handling
- [ ] T016 [P] [US1] Implement `code/models/conformal.py`: Split Conformal Prediction using quantile calibration on a holdout split
- [ ] T017 [US1] Implement `code/analysis/metrics.py`: Functions to calculate empirical coverage, average interval width, and Interval Score (Gneiting & Raftery)
- [ ] T018b [US1] Implement `code/main.py` Integration: Complete the CLI entry point by wiring T013-T017 models and T017 metrics into the orchestration flow defined in T018a
- [ ] T019 [US1] Implement `code/output/reporter.py` to generate the final CSV artifact (true, lower, upper, covered) for each method-dataset pair

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for `code/data/loader.py` ensuring it raises on invalid URLs and refuses synthetic fallback in `tests/test_loader.py`
- [ ] T011 [P] [US1] Unit test for `code/data/preprocessor.py` verifying train-test split sizes and seed reproducibility in `tests/test_preprocessor.py`
- [ ] T012 [P] [US1] Unit test for interval generation ensuring lower <= upper bounds and non-negative width in `tests/test_metrics.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Calibration Assessment (Priority: P2)

**Goal**: Perform rigorous statistical testing (Beta-Binomial, Permutation) to assess significance of calibration deviations and compute Interval Scores.

**Independent Test**: The analysis module accepts P output, returns p-values for Beta-Binomial tests against 0.90 (with FWER correction), and calculates interval scores correctly.

### Tests for User Story 2 (TDD First)

- [ ] T020 [P] [US2] Write failing test for `code/analysis/tests.py`: Verify Beta-Binomial test logic with method-of-moments over-dispersion and **Family-Wise Error Rate (FWER) correction** (e.g., Holm-Bonferroni) in `tests/test_tests.py`
- [ ] T021 [P] [US2] Write failing test for `code/analysis/tests.py`: Verify Permutation test logic with a **sufficiently large number of iterations** and correct handling of pairwise coverage deviations in `tests/test_tests.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/analysis/tests.py`: **Global** Beta-Binomial test for global coverage against a null hypothesis of a specified threshold using **method-of-moments estimator** for over-dispersion (alpha/beta parameters)
- [ ] T022b [US2] Implement `code/analysis/tests.py`: **FWER Correction** logic (e.g., Holm-Bonferroni) to adjust the p-values from T022 across all methods and datasets, returning corrected significance flags
- [ ] T023 [US2] Implement `code/analysis/tests.py`: Permutation test (Monte Carlo, with a sufficient number of iterations) for pairwise method comparison on coverage deviations
- [ ] T023b [US2] Implement `code/analysis/tests.py`: **Pairwise Integration** logic to apply the permutation test (T023) specifically to the pairwise coverage deviations between methods and aggregate the results
- [ ] T024 [US2] Update `code/main.py` to integrate global statistical tests (T022, T022b) and pairwise tests (T023b) into the reporting pipeline, flagging "mis-calibrated" results where **FWER-corrected** p < 0.05
- [ ] T025 [US2] Update `code/output/reporter.py` to include global p-values, **FWER-corrected** significance flags, and pairwise comparison results in the final output artifacts

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Global and Pairwise tests included)

---

## Phase 5: User Story 3 - Heteroscedasticity and Sensitivity Analysis (Priority: P3)

**Goal**: Investigate calibration in high-variance regions and test robustness to threshold definitions (±1% to ±3%).

**Independent Test**: Analysis on a heteroscedastic dataset shows distinct coverage rates across low/medium/high variance bins.

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/models/variance.py`: **Squared-Residual Regression** using `sklearn` (e.g., `GradientBoostingRegressor` on squared residuals) to predict residual variance for test points (replaces GAMLSS to satisfy dependency constraints while meeting FR-006)
- [ ] T029 [US3] Implement `code/analysis/heteroscedasticity.py`: Logic to stratify test points into low/medium/high variance bins and calculate per-bin coverage
- [ ] T030 [US3] Implement `code/analysis/tests.py`: **Conditional** Beta-Binomial test function that accepts pre-computed variance bins and performs over-dispersion adjusted tests for each bin
- [ ] T030b [US3] Implement `code/analysis/tests.py`: **Conditional Aggregation** logic to orchestrate the execution of the conditional test (T030) for *each* variance bin and aggregate the results for the final report (FR-006/SC-006 compliance)
- [ ] T031 [US3] Implement `code/analysis/tests.py`: Sensitivity analysis sweep for mis-calibration thresholds (**±1%, ±2%, ±3%**) and report variation in rates; output must be written to `artifacts/sensitivity_sweep.csv`
- [ ] T032 [US3] Update `code/main.py` to execute variance modeling (T028), conditional tests (T030, T030b), and sensitivity analysis (T031) as part of the full pipeline
- [ ] T033 [US3] Update `code/output/reporter.py` to include per-bin coverage rates and conditional test p-values in final artifacts
- [ ] T034 [US3] Update `code/output/reporter.py` to generate `artifacts/sensitivity_sweep.csv` containing the variation in mis-calibration rates across thresholds

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for variance stratification logic ensuring correct bin assignment in `tests/test_heteroscedasticity.py`
- [ ] T027 [P] [US3] Unit test for sensitivity sweep ensuring thresholds ±1%, ±2%, ±3% produce distinct mis-calibration counts in `tests/test_tests.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T036 [P] Implement memory error handling in `code/models/gaussian.py`: Add try/except block to catch `MemoryError`, log a warning via `code/utils/logging.py`, and skip the method for that dataset
- [ ] T037 [P] Performance optimization: Ensure streaming logic for large datasets (if any) and memory management for GP
- [ ] T038 [P] Run `pytest` on the full suite to verify all acceptance criteria
- [ ] T039 Run quickstart.md validation to ensure the pipeline runs end-to-end on a sample dataset

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable (requires US1 metrics)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable (requires US1 data, US2 stats)

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
Task: "Unit test for loader in tests/test_loader.py"
Task: "Unit test for preprocessor in tests/test_preprocessor.py"
Task: "Unit test for interval logic in tests/test_metrics.py"

# Launch all models for User Story 1 together:
Task: "Implement Quantile Regression (GBT) in code/models/quantile_gbt.py"
Task: "Implement Quantile Regression (Linear) in code/models/quantile_linear.py"
Task: "Implement Bayesian Linear Regression in code/models/bayesian.py"
Task: "Implement Gaussian Process Regression in code/models/gaussian.py"
Task: "Implement Split Conformal Prediction in code/models/conformal.py"
Task: "Implement Quantile Aggregation in code/models/quantile_aggregator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T018a -> Models -> T018b)
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