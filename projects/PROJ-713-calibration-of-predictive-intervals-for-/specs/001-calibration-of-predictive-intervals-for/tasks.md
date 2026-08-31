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

- [ ] T001 Create project directory structure: `code/`, `tests/`, `data/raw/`, `data/processed/`, `results/`. Implement a retry loop with exponential backoff for the `os.path.isdir` verification step to handle filesystem latency, ensuring idempotency before proceeding.

- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `statsmodels`, `prophet`, `torch`, `properscoring`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `matplotlib`)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for hyperparams, random seeds, and path constants
- [X] T005 Implement `code/utils/logger.py` for structured logging and `code/utils/exceptions.py` for custom error handling
- [X] T006a [P] Implement `code/data_loader.py`: Streaming loaders for M4/UCI.
- [X] T006b [P] Implement `code/data/sampler.py::stratified_sampler`: Implements stratified random sampling to select a balanced subset of M4 and UCI series, ensuring representation across frequencies/load profiles.
- [X] T006c [P] Implement variable validation in `code/data_loader.py`. Raise a `SystemExit` with a descriptive error code and message if required variables (timestamp, value) are missing, ensuring the *entire pipeline* halts immediately.
- [X] T007 Create `code/models/__init__.py` and base model interface definitions
- [X] T008 Create `code/metrics/__init__.py` and base metric interface definitions
- [X] T010 Implement `tests/unit/test_edge_cases.py` to verify edge case handling (constant variance, NaN handling).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Empirical Coverage Assessment (Priority: P1) 🎯 MVP

**Goal**: Load M4/UCI data, fit ARIMA/Prophet/LSTM, and compute empirical coverage for 0.80/0.95 intervals.

**Independent Test**: Run pipeline on a single M4 series; verify `results/coverage.csv` contains correct nominal vs. empirical deviations.

- [X] T009 [P] Implement `code/utils/checksum.py` with function `verify_checksums(data_dir: str) -> bool` that returns True if all files match recorded hashes, else raises ValueError. **Depends on**: T006c and T006b completion (must run after data processing).

- [X] T011 [P] Contract test for `data_loader` output schema in `tests/contract/test_data_schema.py`
- [X] T012 [P] Integration test for end-to-end ARIMA coverage calculation in `tests/integration/test_coverage_arima.py`

### Implementation for User Story 1

- [X] T013 [P] Implement `code/models/arima_model.py`: Statsmodels wrapper, conditional variance interval generation, error handling for non-convergence.
- [X] T014 [P] Implement `code/models/prophet_model.py`: Prophet wrapper, `uncertainty_samples` + residual simulation for intervals, error handling.
- [ ] T015 [P] Implement `code/models/lstm_model.py`: Single hidden layer (32 units), max 50 epochs, early stopping (patience=5). If the LSTM fails to produce valid intervals after 2 retry attempts with reduced learning rate, mark the series as 'failed' and log the series ID to `results/skipped_series.log`. Do NOT implement fallback mechanisms.
- [X] T016 [US1] Implement `code/metrics/coverage.py`: Compute empirical coverage rates for standard confidence levels against test set.
- [X] T017 [P] Implement `code/evaluation/runner_single.py`: Single-series runner for debugging. Input arguments: `series_id` (str), `model_type` (str), `config_path` (str). Output: JSON dict with keys `coverage_0.80`, `coverage_0.95`, `pit_p_value`, `crps`.
- [ ] T018 [US1] Implement `code/evaluation/runner.py` (Full Pipeline): Implement the full pipeline loop to process pre-sampled series (M, UCI). Include streaming logic, aggregation, and write results to `results/coverage.csv`, `results/distributional_metrics.csv`. Input arguments: `config_path`. Output: CSVs with columns: `series_id`, `model`, `nominal_level`, `empirical_coverage`, `deviation`, `pit_p_value`, `crps`. **Error Handling**: Catch and log *per-series model execution failures* (e.g., LSTM non-convergence) without crashing the pipeline, but allow *global data validation errors* (from T006c) to propagate and halt execution.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Distributional Calibration (PIT & CRPS) (Priority: P2)

**Goal**: Generate PIT histograms, perform Ljung-Box tests for uniformity, and calculate CRPS scores.

**Independent Test**: Generate PIT histogram for one model/series; verify Ljung-Box p-value logic and CRPS scalar output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] Contract test for metric output schema in `tests/contract/test_metrics_schema.py`
- [X] T020 [P] Integration test for PIT uniformity test in `tests/integration/test_pit_ljung_box_test.py`

### Implementation for User Story 2

- [X] T021 [P] Implement `code/metrics/pit.py`: Calculate Probability Integral Transform for forecast errors, generate histogram data, perform Ljung-Box test for uniformity, and return p-value and histogram bins.
- [X] T022 [P] Implement `code/metrics/crps.py`: Calculate Continuous Ranked Probability Score using `properscoring.crps_ensemble`.
- [ ] T022b [P] Implement `code/metrics/distributional_shape.py`: Calculate kurtosis and tail-weight metrics for the PIT values. Flag series as having 'heavy tails' if kurtosis > 3.5.
- [X] T023 [US2] Update `code/evaluation/runner.py` to integrate PIT and CRPS calculations into the main loop (logic merged into T018).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Conformal Baseline (Priority: P3)

**Goal**: Perform paired bootstrap tests for significance and implement Self-Calibrating Conformal Prediction wrapper.

**Independent Test**: Compare ARIMA vs. Prophet coverage; verify bootstrap p-value < 0.05 logic.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] Contract test for bootstrap output in `tests/contract/test_bootstrap_schema.py`
- [X] T026 [P] Integration test for conformal wrapper improvement in `tests/integration/test_conformal_improvement.py`

### Implementation for User Story 3

- [ ] T031a [US3] Implement `code/evaluation/bootstrap_test.py`: Paired bootstrap test with 1000 resamples at the time-series level, compare coverage deviations between models, and return p-values for significance at α=0.05.
- [ ] T031b [US3] Implement `code/calibration/conformal_orchestrator.py`: Self-Calibrating Conformal Prediction wrapper. Write results to `results/conformal_results.csv` with columns: `series_id`, `model`, `calibration_metric`, `baseline_value`, `conformal_value`.
- [ ] T031 [US3] Implement `code/evaluation/significance_orchestrator.py`: Read completed `results/coverage.csv` and `results/distributional_metrics.csv`, execute `bootstrap_test.py` and `conformal_orchestrator.py`, and write final results to `results/significance_test.csv` and `results/conformal_results.csv`. **Note**: This is a separate script, not a modification of `runner.py`.
- [ ] T032 [US3] Implement `code/evaluation/runner.py::write_significance_results` to serialize the bootstrap p-values to `results/significance_test.csv`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 Code cleanup and refactoring (remove hardcoded paths, ensure seed reproducibility)
- [ ] T035a [P] Run full pipeline on M/UCI subset and record runtime in `results/benchmark_timing.csv` to verify a time limit constraint
- [X] T035b [P] Add unit test in `tests/unit/test_conformal_constraints.py` verifying fixed sample size and no nested CV parameters
- [ ] T036 [P] Additional unit tests for edge cases (constant variance, NaN handling) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T038 Verify `state/` hashes and `updated_at` timestamps are correctly tracked
- [ ] T039 [P] Update `plan.md` Constitution Check table (Principle VI) to mandate 'Ljung-Box test' instead of 'Kolmogorov–Smirnov (KS) test' to align with Spec FR-004.
- [ ] T033a [P] Generate API documentation: Run `pdoc -o docs/api code/` to generate HTML documentation for `code/models/` and `code/metrics/` in `docs/api/`.

---

## Dependencies & Execution Order

(Same as previous revision)

### Parallel Opportunities

(Same as previous revision)

---

## Implementation Strategy

(Same as previous revision)

---

## Notes

(Same as previous revision)