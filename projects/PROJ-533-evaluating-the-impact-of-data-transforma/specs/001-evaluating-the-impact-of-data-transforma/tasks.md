---
description: "Task list for evaluating data transformation impact on statistical test sensitivity"
---

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
- [X] T002 [P] Initialize a Python project with dependencies (`scikit-learn`, `scipy`, `pandas`, `numpy`, `seaborn`, `matplotlib`, `requests`, `pyyaml`, `statsmodels`, `portalocker`) in `requirements.txt`. **CRITICAL**: This file is the primary source for environment setup (`pip install -r requirements.txt`).
- [ ] T003a [P] Create `.flake8` configuration file with max-line-length=100 and ignore codes: E501, W503, W504 for `code/` linting. Verify file exists and contains expected content using `test -f .flake8 && grep -q "max-line-length=100" .flake8`.
- [X] T003b [P] Create `pyproject.toml` with `[tool.black]` configuration for formatting `code/` (line-length=100, target-version=py311). **Note**: This file is for tool configuration only; environment setup uses `requirements.txt`.

## Phase 2: Foundational (Blocking Prerequisites & Spec Alignment)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T009 [P] Create `code/utils/logging_config.py` that configures a logger writing to `results/pipeline.log`. The log format MUST be JSON: `{"timestamp": "...", "level": "...", "message": "...", "data": {"key": "value"}}`. Must handle file locking using the `portalocker` library for cross-platform compatibility. Atomic writes (write to temp file then rename) are required. **Dependency**: No dependencies (runs first).
- [ ] T004 [P] Implement `utils/checkpointing.py` with functions: `save_state(run_id, step, data)` (persisting `current_dataset_id` (str), `last_seed` (int), `error_counts` (dict) to `results/checkpoints/`), `load_state(run_id)` (returning state dict or None), and `delete_checkpoint(run_id)`. Must handle file locking using `portalocker` and atomic writes. **Dependency**: T009 (logging_config).
- [ ] T004b [Foundational] Verify `code/utils/checkpointing.py` works by creating a checkpoint file in `results/checkpoints/` and verifying it contains valid JSON with keys `current_dataset_id`, `last_seed`, `error_counts`. **Dependency**: T004 (sequential).
- [ ] T005 [P] Implement statistical test wrappers in `code/utils/statistical_tests.py` including `t_test`, `anova`, `shapiro_wilk`, and `glmm` functions using `statsmodels` for GLMM. **Dependency**: T009.
- [X] T006a [P] Create `code/data_model.py` skeleton file. **Dependency**: T009.
- [X] T006b [P] Implement `code/utils/data_model.py` defining classes for Dataset, Transformation, and TestResult based on the spec in T006a. Attributes must include `checksum` and `source_url` for Dataset. **Dependency**: T006a.
- [ ] T015a [P] Define schema for `data/imputation_log.csv` (headers: `dataset_id, variable, imputation_method, rate`, comma-delimited, string types) and `data/exclusions.csv` (headers: `dataset_id, reason, details`, comma-delimited, string types). **Dependency**: T009, T006b.
- [ ] T016a [P] Define schema for `data/filter_results.csv` (headers: `dataset_id, shapiro_p, sample_size, included`, comma-delimited, mixed types: string, float, int, boolean). **Dependency**: T009, T006b.

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

- [ ] T013 [US1] Implement `code/download_datasets.py` to fetch datasets from OpenML. **CRITICAL**: Must strictly adhere to FR-001. If the initial query for datasets with >30 rows and continuous variables returns < 50 datasets, the script MUST raise a `ConnectionError` with message "Dataset fetch failed: fewer than 50 public datasets found" and exit with code 1. NO fallback to hardcoded lists or synthetic data is permitted. **Dependency**: T009.
- [ ] T013b [US1] Implement verification logic in `code/download_datasets.py` to ensure all fetched datasets are from public sources (UCI/OpenML) by validating source URLs against canonical domain patterns. Log verified datasets to `data/datasets.csv`. **Dependency**: T013.
- [ ] T014 [US1] Implement `code/checksum_datasets.py` to compute SHA-256 checksums for all **retained** datasets in `data/filtered/` and write to `data/checksums.csv`. **CRITICAL**: Must run immediately AFTER T016 (Filtering) to checksum only the retained data. **Dependency**: T016.
- [ ] T015a [US1] Define schema for `data/imputation_log.csv` and `data/exclusions.csv`. **Dependency**: T009, T006b. (Note: This task is duplicated from Phase 2 for clarity; ensure schema is defined before T015).
- [ ] T015 [US1] Implement missing value imputation (mean/median) and exclusion logic (>10% missing) in `code/filter_datasets.py`. Must write results to `data/imputation_log.csv` and `data/exclusions.csv`. **CRITICAL**: Must explicitly check if imputation rate > 10% and exclude the dataset, logging the reason in `data/exclusions.csv` with columns `dataset_id`, `reason` (e.g., "missing_rate"), `details` (e.g., "missing_rate: 12.5" where 12.5 is the actual calculated float percentage). **Dependency**: T015a (schema).
- [ ] T016a [US1] Define schema for `data/filter_results.csv`. **Dependency**: T009, T006b.
- [ ] T016 [US1] Implement Shapiro-Wilk normality test and sample size filtering (N ≥ 30) in `code/filter_datasets.py` (FR-002). Must write results to `data/filter_results.csv`. **CRITICAL**: Must verify that `data/exclusions.csv` and `data/filter_results.csv` are created and contain at least one row (or are empty if no exclusions/filters applied, but file must exist). **Dependency**: T015 (Imputation), T016a (schema).
- [ ] T017 [US1] Implement metadata extraction (sample size, continuous variables, group labels, source_url) and write to `data/datasets.csv` (FR-001). **CRITICAL**: For distribution shape estimation (skew/kurtosis), this task MUST load the full dataset (or a representative sample via `streaming=True` + `islice`) into memory to compute global statistics required for downstream simulation (T024a). **Dependency**: Must run AFTER T016 (Filtering) and T014 (Checksums) to record only retained datasets.
- [ ] T053 [US1] Implement streaming logic in `code/download_datasets.py` and `code/filter_datasets.py` for processing datasets that exceed RAM limits during analysis steps that do not require global statistics (e.g., per-row transformations). **CRITICAL**: This logic MUST NOT prevent T017 from loading the full dataset (or a sample) for skew/kurtosis calculation. T017 is explicitly responsible for global statistics; T053 applies only to downstream per-row operations and explicitly excludes T017. **Dependency**: T013, T017.

## Phase 4: User Story 2 - Apply Transformations and Run Type I Error Tests (Priority: P2)

**Goal**: Generate simulated null data (independence guaranteed) to estimate Type I error via transformations and statistical tests, avoiding latent confounds in real data.

**Independent Test**: Run `code/generate_null_data.py` and `code/analyze_null_data.py` on a single dataset and verify Type I error is estimated via a sufficient number of simulations with a fixed seed.

### Tests for User Story 2 (TDD First - Write these BEFORE implementation)

- [ ] T019a [US2] Unit test for transformation success/failure handling (log-shift intervention): Implement `tests/unit/test_transformations.py::test_log_shift_applied_on_negative_values` asserting a log-shift is applied and logged when Box-Cox fails on negative data
- [ ] T019b [US2] Unit test for transformation failure logging: Implement `tests/unit/test_transformations.py::test_transformation_failure_logs_reason` asserting a specific error message is written to the log when a transformation fails
- [ ] T020a [US2] Unit test for null simulation data generation: Implement `tests/unit/test_simulate_null.py::test_null_data_independence` asserting that generated null data has no true group differences
- [ ] T020b [US2] Unit test for fixed seed reproducibility: Implement `tests/unit/test_simulate_null.py::test_seed_reproducibility` asserting that two runs with seed=42 produce identical data sequences
- [ ] T021a [US2] Integration test for null data generation + analysis on one dataset: Implement `tests/integration/test_type1_error.py::test_type1_error_estimation_single_dataset` asserting the pipeline produces a valid JSON result file

### Implementation for User Story 2

- [ ] T022 [US2] Implement transformation functions in `code/data/transformations.py` for Box-Cox, Yeo-Johnson, and rank-based inverse normal transformations. **CRITICAL**: Box-Cox must implement log-shift intervention (apply log-shift to make values positive) if Box-Cox fails on negative data, and log the intervention. **Dependency**: T009 (logging_config), T006b (data_model).
- [ ] T024a [US2] Implement `code/generate_null_data.py` to generate simulated datasets where the null hypothesis (independence of X and Y) is guaranteed by construction. **CORRECTION**: Do NOT use label shuffling on real data. The data must match the distribution shapes (skew, kurtosis) of the real-world filtered datasets (from T017) by computing mean skewness and kurtosis of continuous variables in filtered datasets and using these as parameters for the simulation distribution. Generate at least 1000 datasets per effect size (small, medium, large) with fixed random seeds. **Dependency**: T006b, T017.
- [ ] T024b [US2] Implement `code/analyze_null_data.py` to apply transformations (T022) to the simulated null data (T024a) and compute t-test/ANOVA p-values. **Dependency**: T024a, T022.
- [ ] T024c [US2] Implement `code/analyze_null_data.py` to estimate Type I error by computing the proportion of p-values < 0.05 across the 1000+ simulations for each transformation-test combination. Record the seed value used for each simulation run in `results/simulation_seeds.txt` using the format `RUN_ID=<simulated_null_run_id> SEED=<seed>`. **Dependency**: T024b.
- [ ] T025 [US2] Implement aggregation in `code/analyze_null_data.py` to compute the final Type I error rate metric (proportion of p < 0.05) and compare it against the α = 0.05 threshold for the report (SC-002). **Dependency**: T024c.
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

- [ ] T031a [US4] Implement `code/simulate_power.py` to generate simulated alternative datasets with known effect sizes (Cohen's d ∈ {small, medium, large}) and ground truth labels (FR-005, US-4 Acceptance Scenario 1). The data must match the distribution shapes (skew, kurtosis) of the real-world filtered datasets (from T017). Generate at least 1000 simulated datasets per effect size. **CRITICAL**: Must explicitly generate and record ground truth labels for each simulated dataset. Record the seed value in `results/simulation_seeds.txt` using the format `RUN_ID=<simulated_alt_run_id> SEED=<seed>`. **Dependency**: T006b (data_model), T017.
- [ ] T031b [US4] Implement `code/simulate_power.py` to apply transformations (T022) to the simulated alternative data (T031a). **Dependency**: T031a, T022.
- [ ] T033 [US4] Implement `code/simulate_power.py` to run t-test/ANOVA on transformed simulated data and record proportion of p < 0.05 as power (FR-006). **Dependency**: T031b.
- [ ] T034 [US4] Implement `code/simulate_power.py` to compute bootstrap confidence intervals for power estimates to satisfy US-4 Acceptance Scenario 3 requirement for CI validation (FR-006, US-4). **Dependency**: T033.
- [ ] T035 [US4] Write per-simulation power results to `results/power/[effect_size]_[transform]_[test].json`

## Phase 6: User Story 3 - Aggregate Results and Generate Reports (Priority: P3)

**Goal**: Aggregate results across all datasets, compute mean Type I error and power with bootstrap CIs, perform GLMM, and generate visualizations.

**Independent Test**: Execute `code/aggregate_results.py` on pre-computed results and verify summary tables contain mean metrics with CIs and plots are generated.

### Tests for User Story 3 (TDD First - Write these BEFORE implementation)

- [ ] T036a [US3] Unit test for aggregation logic (mean/CI calculation): Implement `tests/unit/test_aggregate.py::test_bootstrap_ci_calculation` asserting the function returns a tuple (mean, ci_lower, ci_upper)
- [ ] T036b [US3] Unit test for aggregation logic (mean calculation): Implement `tests/unit/test_aggregate.py::test_mean_calculation` asserting the function returns the correct arithmetic mean
- [ ] T037a [US3] Unit test for GLMM and post-hoc Bonferroni correction: Implement `tests/unit/test_aggregate.py::test_glmm_and_bonferroni` asserting the function returns a p-value and adjusted p-values
- [ ] T038a [US3] Integration test for full aggregation and visualization pipeline: Implement `tests/integration/test_aggregation.py::test_full_aggregation_pipeline` asserting the script produces summary tables and plots

### Implementation for User Story 3

- [ ] T039 [US3] Implement `code/aggregate_results.py` to load all Type I error and power results and compute means per transformation-test combination (FR-007)
- [ ] T040 [P] [US3] Implement `code/aggregate_results.py` to compute bootstrap confidence intervals for aggregated metrics (FR-007)
- [ ] T041a [US3] Implement `code/aggregate_results.py` to perform GLMM (Generalized Linear Mixed Model) on error rates to assess whether transformation type significantly affects error rates, using `statsmodels` (FR-008, Plan's Complexity Tracking). **Dependency**: T039.
- [ ] T041b [US3] Implement `code/aggregate_results.py` to perform post-hoc pairwise comparisons with Bonferroni correction on GLMM results (FR-008, Plan's Complexity Tracking). **Dependency**: T041a.
- [ ] T043 [US3] Implement `code/aggregate_results.py` to perform sensitivity analysis sweeping α across a range of 0.01 to 0.10 with a step size of 0.01 and generate a JSON report in `results/aggregated/sensitivity_analysis.json` containing both the alpha sweep data and the summary tables. **CRITICAL**: The JSON structure must include keys: `alpha_sweep`, `summary_tables`, `glmm_p_value`. (FR-008, FR-009). **Dependency**: T039, T041a.
- [ ] T044 [P] [US3] Implement `code/aggregate_results.py` to generate bar plots (matplotlib/seaborn) showing error rates and power by transformation and test type (FR-009). **Dependency**: T043.
- [ ] T045 [US3] Implement `code/aggregate_results.py` to validate aggregated results using GLMM as required by the Plan's Summary and Technical Context. **Dependency**: T041a, T041b.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for distribution shape estimation
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Independent of real data, but depends on Foundational utils and US1 for distribution shape estimation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 and US4 completion for aggregation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (except T009, T004b) can run in parallel
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
 - Developer B: User Story 2 (Type I Error via Simulated Null Data)
 - Developer C: User Story 4 (Power Analysis via Simulated Alternative Data)
3. All stories complete, then Developer D/E handles User Story 3 (Aggregation)

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Feasibility Check**: All tasks are CPU-only, no GPU/CUDA required, No 8-bit/4-bit quantization or large model training.
- **Data Integrity**: All data loading tasks MUST fail loudly on fetch errors. No synthetic fallbacks allowed.
- **Methodological Correction**: Type I error estimation is performed exclusively on simulated null data (independence guaranteed), not on real-world data via label shuffling. This is reflected in T024a and authorized by the updated FR-004 in spec.md.
- **Statistical Method**: GLMM is used for robust error estimation; Friedman test is not used. This is reflected in T041a and authorized by the updated FR-008 in spec.md.
- **Spec Alignment**: The spec has been updated to reflect the corrected methodology (Simulated Null, GLMM) BEFORE the project advances.
