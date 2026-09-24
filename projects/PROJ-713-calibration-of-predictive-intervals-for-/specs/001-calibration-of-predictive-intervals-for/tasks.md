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

- **Research Project**: `code/` (source), `tests/` (tests), `data/raw/`, `data/processed/`, `results/` at repository root.
- Paths shown below assume this research project structure - adjust based on plan.md structure.

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

- [ ] T001a [P] Create project directory: `code/`. Ensure idempotency (create if not exists). **Verification**: Verify `code/` directory exists and is writable.
- [ ] T001b [P] Create project directory: `tests/`. Ensure idempotency (create if not exists). **Verification**: Verify `tests/` directory exists and is writable.
- [ ] T001c [P] Create project directory: `data/raw/`. Ensure idempotency (create if not exists). **Verification**: Verify `data/raw/` directory exists and is writable.
- [ ] T001d [P] Create project directory: `data/processed/`. Ensure idempotency (create if not exists). **Verification**: Verify `data/processed/` directory exists and is writable.
- [ ] T001e [P] Create project directory: `results/`. Ensure idempotency (create if not exists). **Verification**: Verify `results/` directory exists and is writable.
- [X] T001f [P] Define directory paths in `code/config.yaml`. Set keys `paths.code`, `paths.tests`, `paths.data_raw`, `paths.data_processed`, `paths.results` to their respective relative paths (e.g., `code`, `tests`, `data/raw`). **Dependency**: Must run after T001a-T001e to ensure directories exist. **Verification**: Verify `code/config.yaml` contains valid path strings for all keys and matches the created directory structure.

- [ ] T002a [P] Create `code/requirements.txt` file. Ensure idempotency. **Verification**: Verify file exists and is empty initially.
- [ ] T002b [P] Pin dependencies in `code/requirements.txt` to specific versions: `statsmodels==0.14.1`, `prophet==1.1.5`, `torch==2.1.0`, `properscoring==0.1`, `scikit-learn==1.3.2`, `scipy==1.11.4`, `pandas==2.1.4`, `numpy==1.26.2`, `matplotlib==3.8.2`, `datasets==2.15.0`, `ucimlrepo==0.0.7`. **Verification**: Verify all versions are pinned and match the plan.
- [ ] T003a [P] Create `.flake8` configuration file in project root. Set `max-line-length = 88`, `ignore = E203, E266, W503`. **Verification**: Verify file exists and contains correct configuration.
- [ ] T003b [P] Create `pyproject.toml` for Black configuration. Set `line-length = 88`, `target-version = ['py311']`. **Verification**: Verify file exists and contains correct configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T000 [P] Implement `code/data/fetcher.py`: Script to download M4 and UCI Electricity datasets from verified sources (Hugging Face or direct URLs). 
    *   **M4**: Download archive from `https://github.com/monash-university-forecasting/m4-competition/raw/master/M4-Competition.zip` (or verified mirror). Verify SHA-256 checksum of the archive. Extract to `data/raw/m4/` using `unzip`. Verify that the extracted directory contains `m4-train.csv` and `m4-test.csv`.
    *   **UCI**: Download archive from `https://archive.ics.uci.edu/static/public/321/electricity.zip` (or verified mirror). Verify SHA-256 checksum of the archive. Extract to `data/raw/uci/` using `unzip`. Verify that the extracted directory contains `electricity.csv`.
    *   **Verification**: Verify archives exist, checksums match, and extracted directories contain the expected series files. **Failure**: Abort immediately with a descriptive error code if checksums do not match or extraction fails.
- [ ] T009 [P] Implement `code/utils/checksum.py` with function `verify_checksums(data_dir: str) -> bool` that returns True if all files match recorded hashes, else raises ValueError. **Depends on**: T000 (Data Fetch) completion. **Note**: This task is NOT parallel-safe and must run after T000. **Verification**: Verify that `verify_checksums` correctly identifies valid and invalid files.
- [X] T004 [P] Implement `code/config.py` for hyperparams, random seeds, and path constants
- [X] T005 [P] Implement `code/utils/logger.py` for structured logging and `code/utils/exceptions.py` for custom error handling
- [X] T006a [P] Implement `code/data_loader.py`: Streaming loaders for M4/UCI.
- [X] T006b [P] Implement `code/data/sampler.py::stratified_sampler`: Implements stratified random sampling to select a balanced subset of M4 and UCI series, ensuring representation across frequencies/load profiles.
- [X] T006c [P] Implement variable validation in `code/data_loader.py`. Raise a `SystemExit` with exit code `1` and a standardized error message format (e.g., `ERR_DATA_001: Missing required variable 'timestamp'`) if required variables (timestamp, value) are missing, ensuring the *entire pipeline* halts immediately. **Verification**: Verify that missing variables trigger `SystemExit(1)` with the correct error code and message format.
- [X] T007 [P] Create `code/models/__init__.py` and base model interface definitions
- [X] T008 [P] Create `code/metrics/__init__.py` and base metric interface definitions
- [X] T010 [P] Implement `tests/unit/test_edge_cases.py` to verify edge case handling (constant variance, NaN handling).

**Governance Gate**: 
> **Constitutional Deviation (Principle VI)**: The Spec mandates the Ljung-Box test (FR-004), while the Constitution mandates the KS test (Principle VI). This is a **blocking deviation**. 
> **Action**: Implementation of T018 (Full Pipeline) is **BLOCKED** until an external amendment to `constitution.md` Principle VI is ratified following the procedure in Principle V (PR, version update). 
> **Note**: Do not attempt to override the Constitution within this task list. Wait for external approval.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Empirical Coverage Assessment (Priority: P1) 🎯 MVP

**Goal**: Load M4/UCI data, fit ARIMA/Prophet/LSTM, and compute empirical coverage for 0.80/0.95 intervals.

**Independent Test**: Run pipeline on a single M4 series; verify `results/coverage.csv` contains correct nominal vs. empirical deviations.

- [X] T011 [P] Contract test for `data_loader` output schema in `tests/contract/test_data_schema.py`
- [X] T012 [P] Integration test for end-to-end ARIMA coverage calculation in `tests/integration/test_coverage_arima.py`

### Implementation for User Story 1

- [X] T013 [P] Implement `code/models/arima_model.py`: Statsmodels wrapper, conditional variance interval generation, error handling for non-convergence.
- [X] T014 [P] Implement `code/models/prophet_model.py`: Prophet wrapper, `uncertainty_samples` + residual simulation for intervals, error handling.
- [ ] T015 [P] Implement `code/models/lstm_model.py`: Single hidden layer (32 units), max 50 epochs, early stopping (patience=5). 
    *   **Fallback Logic**: If the LSTM fails to produce valid intervals after 2 retry attempts with reduced learning rate, **DO NOT substitute a Gaussian model**. Instead, log the series ID, model type, failure reason, and mark the series as "failed" in `results/skipped_series.log`. The series MUST be excluded from the LSTM benchmark results.
    *   **Logging**: Must log the series ID, model type, failure reason, and fallback application (skip only) to `results/skipped_series.log` in JSON format (e.g., `{"series_id": "X", "model": "LSTM", "failure_reason": "...", "fallback_applied": false, "status": "skipped"}`). 
    *   **Verification**: Verify that `results/skipped_series.log` is created with the correct JSON format for any series that triggers the fallback, and that the series is marked as "skipped" (not "failed" due to substitution).
- [X] T016 [US1] Implement `code/metrics/coverage.py`: Compute empirical coverage rates for standard confidence levels against test set.
- [ ] T017a [P] Implement `code/evaluation/runner_coverage_debug.py`: Single-series runner for US1 debugging. Input arguments: `series_id` (str), `model_type` (str), `config_path` (str). Output: JSON dict with keys `coverage_0.80` (float), `coverage_0.95` (float). 
    *   **Requirement**: The JSON output MUST contain ONLY the keys `coverage_0.80` and `coverage_0.95` as floats. It MUST NOT include `pit_p_value` or `crps` (US2 metrics). 
    *   **Verification**: Verify that the JSON output schema aligns with `results/coverage.csv` coverage columns only and contains no US2 metrics.
- [ ] T017b [P] Implement `code/evaluation/runner_pit_debug.py`: Single-series runner for US2 debugging. Input arguments: `series_id` (str), `model_type` (str), `config_path` (str). Output: JSON dict with keys `pit_p_value` (float), `crps` (float). 
    *   **Requirement**: The JSON output MUST contain ONLY the keys `pit_p_value` and `crps` as floats. It MUST NOT include `coverage_0.80` or `coverage_0.95` (US1 metrics). 
    *   **Verification**: Verify that the JSON output schema aligns with `results/distributional_metrics.csv` columns only and contains no US1 metrics.
- [ ] T018 [US1, US2] Implement `code/evaluation/runner.py` (Full Pipeline): Implement the full pipeline loop to process pre-sampled series (M, UCI). Include streaming logic, aggregation, and write results to `results/coverage.csv` and `results/distributional_metrics.csv`. 
    *   **Dependencies**: Must depend on T013, T014, T015 (model implementations), T021 (PIT), T022 (CRPS), and T023a (US2 Integration). 
    *   **Validation**: Must explicitly call `code/data_loader.py` validation (T006c) at start and halt immediately on global data errors. 
    *   **Aggregation**: Must integrate results from T013, T014, T015, T021, T022, and T023a. 
    *   **Input arguments**: `config_path`. 
    *   **Output**:
        1. `results/coverage.csv` with columns: `series_id`, `model`, `nominal_level`, `empirical_coverage`, `deviation`.
        2. `results/distributional_metrics.csv` with columns: `series_id`, `model`, `pit_p_value`, `crps`.
    *   **Verification**: Must verify that `results/coverage.csv` exists, contains >0 rows with non-null values in all columns, and that content matches SC-001 measurement definition (nominal vs empirical deviation). 
    *   **Error Handling**: Catch and log *per-series model execution failures* (e.g., LSTM non-convergence) without crashing the pipeline, but allow *global data validation errors* to propagate and halt execution.
    *   **Governance Block**: **This task is blocked** until the external amendment to Constitution Principle VI (Ljung-Box vs KS) is ratified. Do not execute until external approval is received.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Distributional Calibration (PIT & CRPS) (Priority: P2)

**Goal**: Generate PIT histograms, perform Ljung-Box tests for uniformity, and calculate CRPS scores.

**Independent Test**: Generate PIT histogram for one model/series; verify Ljung-Box p-value logic and CRPS scalar output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] Contract test for metric output schema in `tests/contract/test_metrics_schema.py`
- [X] T020 [P] Integration test for PIT uniformity test in `tests/integration/test_pit_ljung_box_test.py`

### Implementation for User Story 2

- [X] T021 [P] Implement `code/metrics/pit.py`: Calculate Probability Integral Transform for forecast errors, generate histogram data, perform Ljung-Box test for uniformity (accounting for autocorrelation as per Spec FR-004), and return p-value and histogram bins.
- [X] T022 [P] Implement `code/metrics/crps.py`: Calculate Continuous Ranked Probability Score using `properscoring.crps_ensemble`.
- [ ] T023a [US2] Implement `code/evaluation/runner_dist_integration.py`: Integrate PIT and CRPS calculations into the main loop. 
    *   **Dependency**: Must depend on T021 and T022.
    *   **Verification**: Verify that `results/distributional_metrics.csv` is updated with PIT p-values and CRPS scores.
    *   **Note**: This task is a prerequisite for T018 and ensures US2 metrics are correctly integrated.
- [ ] T023b [US2] Implement `tests/integration/test_pit_crps_integration.py`: Integration test for the full US2 pipeline (PIT + CRPS) on a single series. 
    *   **Verification**: Verify that the test passes and outputs the correct JSON schema for US2 metrics.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Conformal Baseline (Priority: P3)

**Goal**: Perform paired bootstrap tests for significance and implement Self-Calibrating Conformal Prediction wrapper.

**Independent Test**: Compare ARIMA vs. Prophet coverage; verify bootstrap p-value < 0.05 logic.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] Contract test for bootstrap output in `tests/contract/test_bootstrap_schema.py`
- [X] T026 [P] Integration test for conformal wrapper improvement in `tests/integration/test_conformal_improvement.py`

### Implementation for User Story 3

- [X] T031a [US3] Implement `code/evaluation/bootstrap_test.py`: Paired bootstrap test with 1000 resamples at the time-series level, compare coverage deviations between models, and return p-values for significance at α=0.05.
- [ ] T031c [US3] Implement `tests/unit/test_conformal_sccp.py`: Unit test to verify the "Self-Calibrating Conformal Prediction" mechanism. 
    *   **Requirement**: Must test the specific internal logic of the SCCP method (e.g., self-calibration step) against a known reference or mathematical property, ensuring it is not a generic conformal wrapper.
    *   **Verification**: Verify that the test passes only if the SCCP logic is correctly implemented.
- [ ] T031b [US3] Implement `code/calibration/conformal_orchestrator.py`: Self-Calibrating Conformal Prediction wrapper. 
    *   **Dependency**: Must run after T018 completes. 
    *   **Verification**: Must depend on T031c (Unit Test for SCCP) to ensure algorithm correctness. 
    *   **Output**: Write results to `results/conformal_results.csv` with columns: `series_id`, `model`, `calibration_metric`, `baseline_value`, `conformal_value`, `improvement_delta`. 
    *   **Verification**: 
        1. Verify that `results/conformal_results.csv` exists with all columns populated and `improvement_delta` calculated correctly.
        2. **Run T031c and assert pass**.
        3. Verify that the implementation updates the calibration parameter `alpha` based on the empirical coverage of the calibration set, as defined in the SCCP method (Self-Calibrating).
        4. Verify that the internal logic explicitly implements the "Self-Calibrating" step (adjusting alpha based on empirical coverage) rather than using a standard fixed-alpha conformal wrapper.
- [ ] T031 [US3] Implement `code/evaluation/significance_orchestrator.py`: Read completed `results/coverage.csv`, `results/distributional_metrics.csv`, and `results/conformal_results.csv`, execute `bootstrap_test.py` (T031a) and `conformal_orchestrator.py` (T031b), and write final results to `results/significance_test.csv` and `results/conformal_results.csv`. 
    *   **Dependency**: Must run after T031a and T031b. 
    *   **Output**: `results/significance_test.csv` with columns: `model_a`, `model_b`, `metric`, `p_value`, `significant`. 
    *   **Verification**: Verify that `results/significance_test.csv` exists with all columns populated and `p_value` calculated correctly.
- [ ] T032 [US3] Implement `code/evaluation/runner.py::write_significance_results` (or separate script as per T031) to serialize the bootstrap p-values to `results/significance_test.csv` with columns: `model_a`, `model_b`, `metric`, `p_value`, `significant`. 
    *   **Input**: Aggregated coverage deviations from `results/coverage.csv`. 
    *   **Verification**: Verify that `results/significance_test.csv` exists with columns `model_a`, `model_b`, `metric`, `p_value`, `significant` populated and matches SC-004 measurement definition.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034a [P] Implement seed pinning in `code/config.py` and all models (T013, T014, T015) to ensure reproducibility.
- [ ] T034b [P] Run `code/utils/verify_hashes.py` with `--code_dir code` and `--results_dir results` to confirm identical outputs on re-run and output a JSON hash comparison report to `results/hash_report.json`. **Verification**: Verify report exists and shows all hashes match.
- [X] T034c [P] Remove hardcoded paths: Audit `code/` for hardcoded paths and ensure all paths are derived from `code/config.py`. **Dependency**: Must run after T001f (path configuration). **Verification**: Verify no hardcoded paths remain in `code/` scripts.
- [ ] T035a [P] Execute pipeline on M/UCI subset (10 series) to verify runtime constraints. Command: `python code/evaluation/runner.py --subset 10`. Threshold: Must complete within 10 minutes. **Verification**: Verify completion time and success.
- [ ] T035b [P] Record runtime to `results/benchmark_timing.csv` with columns: `series_id`, `start_time`, `end_time`, `duration_ms`. Method: `code/evaluation/runner.py` must log timestamps. **Verification**: Verify file exists and columns are populated.
- [ ] T036 [P] Implement `tests/unit/test_edge_cases.py` with specific functions: `test_constant_variance` (verify ARIMA/LSTM skip), `test_nan_handling` (verify NaN detection and logging). **Verification**: Verify all tests pass.
- [ ] T037 [P] Run `python -m pytest tests/integration/test_quickstart.py` to ensure end-to-end reproducibility. **Verification**: Verify all tests pass and output matches expected results.
- [ ] T038 [P] Implement `code/utils/hash_tracker.py` with function `track_artifacts(code_dir: str, results_dir: str) -> dict` that generates SHA-256 hashes for all files in `code/` and `results/`, and updates `state/` YAML with the hashes. **Verification**: Verify `state/` YAML is updated with correct hashes.
- [ ] T033a [P] Generate API documentation using `pdoc --output-dir docs/api --exclude code/utils/checksum.py code/`. **Verification**: Verify `docs/api` directory exists and contains documentation for `code/` modules.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T000 (Data Fetch) must complete before T009 (Checksum Verification).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T018 (US1) output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) except T009 which has dependencies
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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