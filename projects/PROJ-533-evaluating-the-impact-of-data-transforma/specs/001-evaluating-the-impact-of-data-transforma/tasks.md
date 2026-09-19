# Tasks: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

**Input**: Design documents from `/specs/001-data-transformation-sensitivity/`
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

- [ ] T001a [P] Create `code/` directory using `mkdir -p code` and verify existence with `test -d code`.
- [ ] T001b [P] Create `data/` directory using `mkdir -p data` and verify existence with `test -d data`.
- [ ] T001c [P] Create `results/` directory using `mkdir -p results` and verify existence with `test -d results`.
- [ ] T001d [P] Create `tests/` directory using `mkdir -p tests` and verify existence with `test -d tests`.
- [X] T002 Initialize a Python project with dependencies (`scikit-learn`, `scipy`, `pandas`, `numpy`, `seaborn`, `matplotlib`, `requests`, `pyyaml`, `statsmodels`) in `requirements.txt`.
- [ ] T003a [P] Create `.flake8` configuration file with max-line-length=100 and ignore codes: E501, W503, W504 for `code/` linting. Verify file exists and contains expected content using `test -f .flake8 && grep -q "max-line-length=100" .flake8`.
- [X] T003b [P] Create `pyproject.toml` with `[tool.black]` configuration for formatting `code/` (line-length=100, target-version=py311).

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 [P] Create `code/utils/logging_config.py` that configures a logger writing to `results/pipeline.log`. The log format MUST be JSON: `{"timestamp": "...", "level": "...", "message": "...", "data": {"key": "value"}}`. Must handle file locking using `fcntl.flock` and atomic writes (write to temp file then rename). **Dependency**: No dependencies (runs first).
- [ ] T004 [P] Implement `utils/checkpointing.py` with functions: `save_state(run_id, step, data)` (persisting `current_dataset_id` (str), `last_seed` (int), `error_counts` (dict) to `results/checkpoints/`), `load_state(run_id)` (returning state dict or None), and `delete_checkpoint(run_id)`. Must handle file locking using `fcntl.flock` and atomic writes (write to temp file then rename). **Dependency**: T009 (logging_config).
- [ ] T004b [P] Verify `code/utils/checkpointing.py` works by creating a checkpoint file in `results/checkpoints/` and verifying it contains valid JSON with keys `current_dataset_id`, `last_seed`, `error_counts`. **Dependency**: T004.
- [ ] T005a [P] Implement `t_test` function in `utils/statistical_tests.py`. **Dependency**: T009.
- [ ] T005b [P] Implement `anova` function in `utils/statistical_tests.py`. **Dependency**: T009.
- [ ] T005c [P] Implement `shapiro_wilk` function in `utils/statistical_tests.py`. **Dependency**: T009.
- [ ] T005d [P] Implement `friedman` function in `utils/statistical_tests.py`. **Dependency**: T009.
- [X] T006a [P] Create `code/data_model.py` skeleton file. **Dependency**: T009.
- [X] T006b [P] Implement `code/utils/data_model.py` defining classes for Dataset, Transformation, and TestResult based on the spec in T006a. Attributes must include `checksum` and `source_url` for Dataset. **Dependency**: T006a.
- [ ] T008 [P] Create `results/simulation_seeds.txt` as a file with header `RUN_ID=<id> SEED=<val>` and write a sample seed entry `RUN_ID=init SEED=42` to verify format. **Dependency**: T009.
- [ ] T008b [P] Verify `results/simulation_seeds.txt` contains valid seed values (non-empty, correct format) before simulation tasks run. **Dependency**: T008.

## Phase 3: User Story 1 - Download and Filter Real-World Datasets (Priority: P1) 🎯 MVP

**Goal**: Download at least 50 public datasets from UCI/OpenML, filter for non-normality (Shapiro-Wilk p < 0.05) and sample size (N ≥ 30), and preserve metadata.

**Independent Test**: Execute `code/download_datasets.py` and `code/filter_datasets.py` and verify `data/datasets.csv` contains ≥50 valid entries with SHA-256 checksums in `data/checksums.csv`.

### Tests for User Story 1 (TDD First - Write these BEFORE implementation)

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. These are atomic tasks, one per test function.

- [X] T010a [US1] Unit test for valid URL validation: Implement `tests/unit/test_download.py::test_valid_url_returns_true_for_valid_url` asserting `is_valid_url("...")` returns True
- [X] T010b [US1] Unit test for invalid URL validation: Implement `tests/unit/test_download.py::test_invalid_url_returns_false` asserting `is_valid_url("not_a_url")` returns False
- [X] T011a [US1] Unit test for Shapiro-Wilk p-value calculation: Implement `tests/unit/test_filter.py::test_shapiro_wilk_p_value_calculation` asserting `shapiro_test([1,2,3,4,5])` returns a p-value object
- [X] T011b [US1] Unit test for Shapiro-Wilk filtering logic (p < 0.05): Implement `tests/unit/test_filter.py::test_filter_keeps_non_normal` asserting a dataset with p=0.01 is kept and p=0.10 is excluded
- [X] T012a [US1] Integration test for full download-and-filter pipeline: Implement `tests/integration/test_pipeline.py::test_full_download_filter_pipeline` asserting that running both scripts produces a valid `data/datasets.csv` with ≥1 entry

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/download_datasets.py` to fetch the INITIAL batch of datasets from UCI/OpenML with explicit URL logging. **CRITICAL**: Must use `openml.datasets.get_datasets()` or explicit UCI raw URLs; MUST NOT include any `try/except` fallback to synthetic/mock data generation. If the fetch fails or yields <50 datasets, the script MUST raise a `ConnectionError` with message "Dataset fetch failed or count < 50" and exit with code 1. **Dependency**: T009.
- [ ] T014 [US1] Implement `code/download_datasets.py` to compute SHA-256 checksums for all downloaded datasets and write to `data/checksums.csv`. **Dependency**: Must run immediately AFTER T013 (Download) to checksum the raw downloaded data before any filtering or exclusion logic is applied.
- [ ] T014b [US1] Create `state/projects/PROJ-533-evaluating-the-impact-of-data-transforma.yaml` if missing, define schema (`artifact_hashes` map), and update it with checksums from T014. **Dependency**: T006b (data_model schema), T013 (Download), T014 (checksums).
- [ ] T015a [US1] Define schema for `data/imputation_log.csv` (headers: `dataset_id, variable, imputation_method, rate`, comma-delimited, string types) and `data/exclusions.csv` (headers: `dataset_id, reason, details`, comma-delimited, string types). **Dependency**: T009.
- [ ] T015 [US1] Implement missing value imputation (mean/median) and exclusion logic (>10% missing) in `code/filter_datasets.py`. Must write results to `data/imputation_log.csv` and `data/exclusions.csv`. **CRITICAL**: Must explicitly check if imputation rate > 10% and exclude the dataset, logging the reason in `data/exclusions.csv` with columns `dataset_id`, `reason` (e.g., "missing_rate"), `details` (e.g., "[deferred]"). **Dependency**: T015a (schema).
- [ ] T016a [US1] Define schema for `data/filter_results.csv` (headers: `dataset_id, shapiro_p, sample_size, included`, comma-delimited, mixed types: string, float, int, boolean). **Dependency**: T009.
- [ ] T016 [US1] Implement Shapiro-Wilk normality test and sample size filtering (N ≥ 30) in `code/filter_datasets.py` (FR-002). Must write results to `data/filter_results.csv`. **CRITICAL**: Must verify that `data/exclusions.csv` and `data/filter_results.csv` are created and contain at least one row (or are empty if no exclusions/filters applied, but file must exist). **Dependency**: T015 (Imputation), T016a (schema).
- [ ] T051 [US1] Implement dataset filtering logic in `code/download_datasets.py` to enforce the requirement of having at least one continuous variable AND one categorical group label with ≥2 levels. Exclude datasets lacking these criteria with explicit logging to `data/exclusions.csv`. **Dependency**: T013 (Download).
- [ ] T052 [US1] Implement a robust dataset selection strategy in `code/download_datasets.py` that explicitly queries for and downloads a minimum of 50 datasets from UCI/OpenML. If the initial query (T013) yields fewer than 50, the script must expand the search criteria (e.g., broader keywords, different time ranges) until the threshold is met, logging the expansion steps. **Dependency**: T013 (Download).
- [ ] T017 [US1] Implement metadata extraction (sample size, continuous variables, group labels, source_url) and write to `data/datasets.csv` (FR-001). **Dependency**: Must run AFTER T051 and T052 (Filtering) to record only retained datasets.

## Phase 4: User Story 2 - Apply Transformations and Run Type I Error Tests (Priority: P2)

**Goal**: Apply Box-Cox, Yeo-Johnson, and rank-based transformations to filtered datasets and estimate Type I error via label shuffling.

**Independent Test**: Run `code/apply_transformations.py` and `code/simulate_null.py` on a single dataset and verify Type I error is estimated via a sufficient number of shuffles with a fixed seed.

### Tests for User Story 2 (TDD First - Write these BEFORE implementation)

- [ ] T019a [US2] Unit test for transformation success/failure handling (log-shift intervention): Implement `tests/unit/test_transformations.py::test_log_shift_applied_on_negative_values` asserting a log-shift is applied and logged when Box-Cox fails on negative data
- [ ] T019b [US2] Unit test for transformation failure logging: Implement `tests/unit/test_transformations.py::test_transformation_failure_logs_reason` asserting a specific error message is written to the log when a transformation fails
- [ ] T020a [US2] Unit test for null simulation label shuffling logic: Implement `tests/unit/test_simulate_null.py::test_label_shuffling_preserves_distribution` asserting that shuffled labels maintain the original group size distribution
- [ ] T020b [US2] Unit test for fixed seed reproducibility: Implement `tests/unit/test_simulate_null.py::test_seed_reproducibility` asserting that two runs with seed=42 produce identical p-value sequences
- [ ] T021a [US2] Integration test for transformation + null simulation on one dataset: Implement `tests/integration/test_type1_error.py::test_type1_error_estimation_single_dataset` asserting the pipeline produces a valid JSON result file

### Implementation for User Story 2

- [ ] T022a [US2] Implement `code/apply_transformations.py` for Box-Cox transformation. **CRITICAL**: Must explicitly implement log-shift intervention (apply log-shift to make values positive) if Box-Cox fails on negative data, and log the intervention. **Dependency**: T009 (logging_config), T006b (data_model).
- [ ] T022b [US2] Implement `code/apply_transformations.py` for Yeo-Johnson transformation. **Dependency**: T009, T006b.
- [ ] T022c [US2] Implement `code/apply_transformations.py` for rank-based inverse normal transformation. **Dependency**: T009, T006b.
- [ ] T024 [US2] Implement `code/simulate_null.py` to shuffle group labels 1000 times with a fixed seed (seed=42), compute t-test/ANOVA p-values (FR-004), append the seed value to `results/simulation_seeds.txt` (creating file if missing with header `RUN_ID=<id> SEED=42`), and record proportion of p < 0.05 as Type I error estimate. **Dependency**: T022a, T022b, T022c, T008.
- [ ] T025 [P] [US2] Implement checkpointing in `code/simulate_null.py` to save progress per dataset. **Dependency**: T024.
- [ ] T026 [US2] Write per-dataset Type I error results to `results/type1_error/[dataset_id].json`

## Phase 5: User Story 4 - Simulate Data with Known Ground Truth for Power Analysis (Priority: P4)

**Goal**: Generate simulated datasets with known effect sizes (Cohen's d) and measure statistical power.

**Independent Test**: Run `code/simulate_power.py` with fixed effect sizes and verify power estimates match expected values within 95% CI half-width ±0.02.

### Tests for User Story 4 (TDD First - Write these BEFORE implementation)

- [ ] T028a [US4] Unit test for simulated data generation (non-normal distributions): Implement `tests/unit/test_simulate_power.py::test_non_normal_data_generation` asserting Generated data has skewness > 0.5
- [ ] T028b [US4] Unit test for ground truth label assignment: Implement `tests/unit/test_simulate_power.py::test_ground_truth_labels_assigned` asserting labels match the known effect size group
- [ ] T029a [US4] Unit test for power calculation logic: Implement `tests/unit/test_simulate_power.py::test_power_calculation_proportion` asserting power = count(significant) / total_runs
- [ ] T030a [US4] Integration test for full power simulation pipeline: Implement `tests/integration/test_power_analysis.py::test_full_power_simulation_pipeline` asserting the pipeline produces valid JSON results for all effect sizes

### Implementation for User Story 4

- [ ] T031 [US4] Implement `code/simulate_power.py` to generate at least 1000 simulated datasets per effect size (small, medium, large) with ground truth labels (FR-005, US-4 Acceptance Scenario 1). **CRITICAL**: Must explicitly generate and record ground truth labels for each simulated dataset. **Dependency**: T006b (data_model).
- [ ] T033 [US4] Implement `code/simulate_power.py` to run t-test/ANOVA on transformed simulated data (using T022 logic) and record proportion of p < 0.05 as power (FR-006). **Dependency**: T031, T022a, T022b, T022c.
- [ ] T034 [US4] Implement `code/simulate_power.py` to compute bootstrap confidence intervals for power estimates to satisfy US-4 Acceptance Scenario 3 requirement for CI validation (FR-006, US-4). **Dependency**: T033.
- [ ] T035 [US4] Write per-simulation power results to `results/power/[effect_size]_[transform]_[test].json`

## Phase 6: User Story 3 - Aggregate Results and Generate Reports (Priority: P3)

**Goal**: Aggregate results across all datasets, compute mean Type I error and power with bootstrap CIs, perform Friedman test, and generate visualizations.

**Independent Test**: Execute `code/aggregate_results.py` on pre-computed results and verify summary tables contain mean metrics with CIs and bar plots are generated.

### Tests for User Story 3 (TDD First - Write these BEFORE implementation)

- [ ] T036a [US3] Unit test for aggregation logic (mean/CI calculation): Implement `tests/unit/test_aggregate.py::test_bootstrap_ci_calculation` asserting the function returns a tuple (mean, ci_lower, ci_upper)
- [ ] T036b [US3] Unit test for aggregation logic (mean calculation): Implement `tests/unit/test_aggregate.py::test_mean_calculation` asserting the function returns the correct arithmetic mean
- [ ] T037a [US3] Unit test for Friedman test and post-hoc Bonferroni correction: Implement `tests/unit/test_aggregate.py::test_friedman_test_and_bonferroni` asserting the function returns a p-value and adjusted p-values
- [ ] T038a [US3] Integration test for full aggregation and visualization pipeline: Implement `tests/integration/test_aggregation.py::test_full_aggregation_pipeline` asserting the script produces summary tables and plots

### Implementation for User Story 3

- [ ] T039 [US3] Implement `code/aggregate_results.py` to load all Type I error and power results and compute means per transformation-test combination (FR-007)
- [ ] T040 [P] [US3] Implement `code/aggregate_results.py` to compute bootstrap confidence intervals for aggregated metrics (FR-007)
- [ ] T041 [US3] Implement `code/aggregate_results.py` to perform Friedman test (non-parametric repeated measures ANOVA) on error rates (FR-008)
- [ ] T042 [P] [US3] Implement `code/aggregate_results.py` to perform post-hoc pairwise comparisons with Bonferroni correction (FR-008)
- [ ] T043 [US3] Implement `code/aggregate_results.py` to perform sensitivity analysis sweeping α across a range with a fine-grained step size and generate a JSON report in `results/aggregated/sensitivity_analysis.json` containing both the alpha sweep data and the summary tables. **CRITICAL**: The JSON structure must include keys: `alpha_sweep`, `summary_tables`, `friedman_p_value`. (FR-008, FR-009). **Dependency**: T039, T041.
- [ ] T044 [P] [US3] Implement `code/aggregate_results.py` to generate bar plots (matplotlib/seaborn) showing error rates and power by transformation and test type (FR-009). **Dependency**: T043.

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 Update README.md to include installation instructions, usage examples for code/download_datasets.py, and a description of the results/ directory structure
- [ ] T048 Profile `code/aggregate_results.py` and optimize loop X; record runtime in `results/benchmark.log` to ensure < 6h total runtime
- [ ] T049 Additional unit tests (if requested) in `tests/unit/`
- [ ] T050 Execute all code blocks in quickstart.md and verify they complete without error, logging output to `results/quickstart_validation.log`

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P4 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for input data
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Independent of real data, but depends on Foundational utils
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 and US4 completion for aggregation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (except T009) can run in parallel
- Once Foundational phase completes, US1, US2, US4 can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

## Parallel Example: User Story 1

```bash
# Launch all implementation tasks for User Story 1 together (after tests are written):
Task: "Implement missing value imputation in code/filter_datasets.py"
Task: "Implement Shapiro-Wilk normality test in code/filter_datasets.py"
```

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
4. Add User Story 4 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Acquisition)
 - Developer B: User Story 2 (Type I Error)
 - Developer C: User Story 4 (Power Analysis)
3. All stories complete, then Developer D/E handles User Story 3 (Aggregation)

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Feasibility Check**: All tasks are CPU-only, no GPU/CUDA required, Memory usage < 6GB, Runtime < 6h. No 8-bit/4-bit quantization or large model training.
- **Data Integrity**: All data loading tasks MUST fail loudly on fetch errors. No synthetic fallbacks allowed.