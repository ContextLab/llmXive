# Tasks: Evaluating the Impact of Data Scaling on Robustness of Statistical Tests

**Input**: Design documents from `/specs/001-evaluating-data-scaling-on/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create root project directories: `code/`, `data/`, `results/`, `logs/`
- [X] T001b [P] Create `code/simulation/`, `code/preprocessing/`, `code/analysis/`, `code/visualization/` subdirectories. **Deliverable**: Verify directories exist: `code/simulation`, `code/preprocessing`, `code/analysis`, `code/visualization`.
- [X] T001c [P] Create `data/raw/`, `data/scaled/`, `data/config/` subdirectories
- [X] T001d [P] Create `results/figures/` and `data/scaled/{standardized,minmax,robust}/` subdirectories
- [X] T002 Initialize Python project with pinned dependencies in `code/requirements.txt` (numpy, scipy, pandas, scikit-learn, statsmodels, matplotlib, seaborn)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data hygiene, configuration, and streaming adaptations.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration management for `SimulationConfig` entity in `code/simulation/config.py`
- [X] T005a [P] Create `code/simulation/logger.py` with `setup_logger` function that returns a logger instance configured with `logging.INFO` and a specific format string `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`
- [X] T005b [P] Configure log levels for `code/simulation/logger.py` to handle `DEBUG`, `INFO`, `WARNING`, `ERROR` with file rotation to `logs/simulation.log` using `RotatingFileHandler` with `maxBytes=10MB` and `backupCount=5`. **Deliverable**: Ensure logger explicitly logs the random seed and simulation batch ID on every batch start as required by Constitution Principle VI. The `setup_logger` function must accept `batch_id` as an argument to ensure deterministic logging. **Format String**: Use `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`. **Persistence Requirement**: In addition to logging, the `setup_logger` function must write the `seed` and `batch_id` to a persistent file `code/simulation/seed_config.json` to satisfy Constitution Principle VI's requirement for recording seeds in `code/` for reproducibility. **Primary Source of Truth**: The `seed_config.json` file is the authoritative record for seeds; logging is secondary.
- [X] T005c [P] **Inject Batch ID into Log Context**: Create a function `inject_batch_context` in `code/simulation/logger.py` that wraps the logger to include `batch_id` and `seed` in every log record. **Requirement**: This function must be called at the start of every simulation batch. **Verification**: Unit test `code/tests/unit/simulation/test_logger.py` asserting the log output contains the batch ID. **Dependency**: Must be completed before T028a.
- [X] T006 [P] Create base test fixtures and seed management in `code/tests/conftest.py` (independent of T005, using standard library logging for fixtures)
- [X] T007 Setup environment configuration for CPU-only constraints (disable GPU, set parallelism limits) in `code/utils/env.py`
- [X] T024 [US4] **Implement Strict Streaming Loader**: Refactor `code/preprocessing/ingestion.py` to use `datasets.load_dataset(..., streaming=True)` for large public datasets. **Requirement**: Do not load the full dataset into memory. **Logic**: Iterate over the streaming object in chunks to compute necessary statistics (mean, variance) or to sample a fixed number of rows. **Constraint**: If a full dataset cannot be processed within the specified time limit, the code must explicitly sample a well-defined subset. (e.g., `itertools.islice` the first N rows) and log the sample size and limitation. **Prohibition**: Do NOT use `generate_synthetic_data` as a fallback if streaming fails. **CRITICAL PREREQUISITE**: This task MUST be completed before T035 and T038.
- [X] T025 [US4] **Enforce Fail-Loudly Data Fetch**: Remove any `try/except` blocks in `code/preprocessing/ingestion.py` that catch download errors and substitute synthetic data. **Action**: If `datasets.load_dataset` or a URL fetch fails, the function must raise a `RuntimeError` with a clear message identifying the missing source. **Rationale**: Prevents silent fabrication where real data fails and the pipeline continues with fake data. **CRITICAL PREREQUISITE**: This task MUST be completed before T035 and T038.
- [X] T026 [US4] Adapt `code/analysis/tests.py` to accept chunked/streamed data via a `data_stream` or `sample_size` argument. Implement a 'sample-and-test' strategy: stream N=5000 rows, then run the standard test.
- [X] T027a [US4] **Fetch Dataset Metadata**: Implement a script in `code/preprocessing/ingestion.py` to fetch metadata for all candidate datasets listed in `research.md`. **Requirement**: The script must verify which datasets are accessible (returning 200 OK or valid metadata). **Constraint**: Do not proceed to filtering or logging in this task. **Verification**: Unit test `code/tests/unit/preprocessing/test_datasets_config.py` with function `test_fetch_metadata_success` asserting the script fetches metadata correctly. **CRITICAL PREREQUISITE**: This task MUST be completed before T027b.
- [X] T027b [US4] **Filter Available Datasets**: Implement logic in `code/preprocessing/ingestion.py` to filter the fetched metadata to only include accessible datasets. **Requirement**: The script must produce a list of available dataset IDs. **Logic**: If the count of available datasets is < 10, log a `WARNING` stating "FR-008 Note: Only N datasets available" and proceed with the available count. **Do NOT raise a RuntimeError**. **Verification**: Unit test `code/tests/unit/preprocessing/test_datasets_config.py` with function `test_filter_available_datasets` asserting the script filters correctly and logs warning if <10. **CRITICAL PREREQUISITE**: This task MUST be completed before T027c.
- [X] T027c [US4] **Log Dataset Availability**: Implement logic in `code/preprocessing/ingestion.py` to log warnings for failed datasets and the count of available datasets. **Requirement**: The script must log a `WARNING` if <10 datasets are available (though T027b should have already logged). **Constraint**: Do not proceed to ingestion in this task. **Verification**: Unit test `code/tests/unit/preprocessing/test_datasets_config.py` with function `test_log_dataset_availability` asserting the script logs warnings correctly. **CRITICAL PREREQUISITE**: This task MUST be completed before T027d.
- [X] T027d [US4] **Create Verified Dataset Configuration**: Generate `data/config/datasets.yaml` containing the list of *successfully verified* datasets from T027b. **Deliverable**: `data/config/datasets.yaml` with unique IDs. **Schema**: Each entry MUST contain `dataset_id` (string), `source_url` (string), `checksum` (string, SHA256), and `status` (string: 'verified'). **Validation**: Programmatically verify that the generated YAML contains the available entries. **Constraint**: If T027b raised an error, this task is skipped. **Verification**: Unit test `code/tests/unit/preprocessing/test_datasets_config.py` with function `test_verify_yaml_generation` asserting the generated file contains the available entries. **CRITICAL PREREQUISITE**: This task MUST be completed before T051 and T056.
- [X] T027e [US4] **Ingest Available Datasets**: Implement logic in `code/preprocessing/ingestion.py` to ingest *only* the datasets listed in `data/config/datasets.yaml` (from T027d). **Requirement**: Process whatever is available (even if <10, though T027b should have blocked). **Deliverable**: `results/real_world_ingestion_log.csv` with schema: `dataset_id`, `source_url`, `status`, `row_count`, `checksum`. **Dependency**: Requires T024 and T025. **Verification**: Unit test `code/tests/unit/preprocessing/test_ingestion.py` asserting that the ingestion completes successfully for the available list. **CRITICAL PREREQUISITE**: This task MUST be completed before T038 and T056.
- [X] T028 [US4] **Add Verification Task for Real Data**: Create a task `code/tests/unit/preprocessing/test_real_data_integrity.py` that asserts the loaded data is not synthetic by checking for specific statistical properties or source ID verification.
- [X] T064 [US3] **Time-Limit Enforcement & Budget Verification**: Implement a 'hard stop' mechanism in `code/main.py` to handle the 6-hour time limit (FR-007). **Trigger**: Check elapsed time at regular intervals. **Action**: If the limit is exceeded, **SAVE partial results to `results/partial_checkpoint.csv` FIRST**, then log the number of completed iterations, and exit with code 1 if `completed_iterations < 10000` (Time Limit Reached) or code 99 if critical failure. **Fallback**: If time limit is hit, attempt to reduce config complexity (fewer distributions) to meet the [deferred] iteration target. **Verification Logic**: Explicitly check if `completed_iterations == target_iterations` before the time limit to verify the 'fixed time budget' in SC-003 was met. Log 'Budget Met' or 'Budget Exhausted'. **Exit Codes**: Code 0 = Success (>=10k iterations), Code 1 = Time Limit (Partial Success, CI should pass if partial results exist), Code 99 = Critical Failure. **Dependency**: Must be completed before T028a.
- [X] T065 [US3] **Define Configuration Matrix**: Explicitly define the configuration matrix in `code/simulation/config.py` as a list of dictionaries: `distribution_types` (Normal, Skewed, Heteroscedastic), `scaling_methods` (Standardization, Min-Max, Robust), `test_types` (t-test, ANOVA, Chi-squared). **Deliverable**: A constant `CONFIG_MATRIX` in `code/simulation/config.py`. **Verification**: Unit test `code/tests/unit/simulation/test_config.py` asserting the matrix contains all required combinations. **Dependency**: Must be completed before T028a.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Simulation Engine for Null and Alternative Hypotheses (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic datasets with controlled distributional properties where ground truth is known.

**Independent Test**: Generate a dataset with null hypothesis (mean diff = 0) and verify mean difference < 0.01; generate alternative (mean diff = 1.0) and verify |mean_diff - 1.0| < 0.05.

### Tests for User Story 1

- [X] T008 [P] [US1] Contract test for null hypothesis generation in `code/tests/unit/simulation/test_generator.py`
- [X] T009 [P] [US1] Contract test for alternative hypothesis generation in `code/tests/unit/simulation/test_generator.py`
- [X] T010 [P] [US1] Test for skewness/heteroscedasticity parameter accuracy in `code/tests/unit/simulation/test_generator.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `generate_synthetic_data` function in `code/simulation/generator.py` that accepts arbitrary distributional moments: `mean`, `variance`, `skewness`, `kurtosis` as explicit float arguments. Map variance to the scale parameter of scipy.stats.norm (for normal distributions). If skewness=0 and kurtosis=3, default to Normal distribution. **Deliverable**: Function signature `generate_synthetic_data(mean, var, skew, kurt, n, seed)`.
- [X] T012 [US1] Implement ground truth validation logic in `code/simulation/generator.py` that returns a boolean and logs assertion failures if `mean_diff >= 0.01` for null or `|mean_diff - 1.0| >= 0.05` for alternative. **Deliverable**: Function returns `(bool, str)` where bool indicates validity and str contains error message if invalid.
- [X] T013 [US1] Add logic to handle zero-variance edge cases in `code/simulation/generator.py`: Log `WARNING` with message "Skipping iteration: zero variance detected" if `std_dev < 1e-9 ` and skip the specific iteration. **Condition**: `if std_dev < 1e-9 `. **Log Level**: `WARNING`.
- [X] T014 [US1] Implement data persistence to `data/synthetic/` with metadata. **Deliverable**: Save each batch as `data/synthetic/batch_{batch_id}_{seed}.parquet`. Columns must include: `seed` (int), `config_json` (string, JSON serialized config), `ground_truth_label` (string: 'null' or 'alternative'), and the generated data columns.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Scaling Application and Statistical Testing Pipeline (Priority:P2)

**Goal**: Apply scaling methods (Standardization, Min-Max, Robust) and run parametric tests (t-test, ANOVA, Chi-squared).

**Independent Test**: Apply Standardization to a fixed dataset, verify (Wikipedia: Standard normal table), and confirm t-test p-value stability compared to unscaled data.

### Tests for User Story 2

- [X] T015 [P] [US2] Contract test for Standardization scaling properties (mean=0, std=1) in `code/tests/unit/preprocessing/test_scaling.py`
- [X] T016 [P] [US2] Contract test for Min-Max scaling properties (min=0, max=1) in `code/tests/unit/preprocessing/test_scaling.py`
- [X] T017 [P] [US2] Contract test for Robust scaling (median/IQR) and zero-IQR handling in `code/tests/unit/preprocessing/test_scaling.py`
- [X] T018 [P] [US2] Test for p-value invariance under linear scaling transformations in `code/tests/unit/analysis/test_tests.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `standardize_data` function in `code/preprocessing/scaling.py`
- [X] T020 [P] [US2] Implement `min_max_scale` function in `code/preprocessing/scaling.py`
- [X] T021 [P] [US2] Implement `robust_scale` function in `code/preprocessing/scaling.py` with explicit zero-IQR handling: Log `WARNING` and skip the iteration if IQR is zero. **Action**: Do not return a constant; skip iteration entirely. **Rationale**: Skipping is a necessary data hygiene step to prevent NaNs and division-by-zero errors, ensuring robust scaling handles edge cases as per Edge Case 2.
- [X] T022 [US2] Implement `run_t_test` and `run_anova` in `code/analysis/tests.py`
- [X] T023 [US2] Implement `run_chi_squared` in `code/analysis/tests.py` with binning logic based on theoretical quantiles derived from the config's ground-truth parameters (mean, variance). **Edge Case Handling**: Explicitly check for zero variance in the data. If zero variance is detected OR if bin merging fails (both neighbors fail), log `WARNING: Edge Case: Zero Variance / Bin Merge Failed` and skip the iteration. **Logic**: If a bin has an expected count < 5, merge with the left neighbor; if the left neighbor is empty or < 5, merge with the right neighbor. If both fail, log "Bin merge failed" and skip. **Traceability**: This skip condition must be explicitly linked to the spec's Edge Case requirement for handling zero variance. **Verification**: Unit test `code/tests/unit/analysis/test_tests.py` asserting the skip logic triggers correctly on zero variance and merge failure. **Dependency**: Requires T019, T020, T021.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregation and Visualization of Inferential Validity (Priority: P3)

**Goal**: Aggregate a sufficient number of iterations to calculate Type I error rates and Power., then visualize against nominal alpha.

**Independent Test**: Feed a set of pre-calculated p-values into aggregation logic and verify that the calculated empirical error rate matches the proportion of p-values < 0.05, and that the confidence interval calculation runs successfully.

### Tests for User Story 3

- [X] T060 [P] [US3] Contract test for empirical error rate calculation (count < alpha / total) in `code/tests/unit/analysis/test_metrics.py`
- [X] T061 [US3] **Production CI Implementation**: Implement `calculate_confidence_interval` in `code/analysis/metrics.py` using the Clopper-Pearson exact method.
- [X] T062 [US3] **Verification Test**: Implement a test in `code/tests/unit/analysis/test_metrics.py` that verifies the Clopper-Pearson implementation against known binomial values for n=100, p=0.05 (expected range: a low-order magnitude to a small threshold).

### Implementation for User Story 3

- **CRITICAL PATH BLOCKER**: The following tasks (T028a, T028b, T028c) MUST be completed before any downstream analysis (T029, T030, T039, T053) can proceed.
- [X] T028a [US3] **Implement Simulation Loop Orchestration**: In `code/main.py`, implement the iteration loop to iterate over all combinations defined in `code/simulation/config.py` (T065). **Algorithm**: For each config in `CONFIG_MATRIX`, loop `target_iterations` (**[deferred]** as per FR-004) times. In each iteration: 1. Generate data (T011). 2. Apply scaling (T019-T021). 3. Run tests (T022-T023). 4. Record `iteration_id`, `config_id`, `scaling_method`, `test_type`, `p_value`, `statistic`, `ground_truth`, `scaling_params`, `seed`. **Deliverable**: `results/simulation_results.csv` with schema: `iteration_id`, `config_id`, `scaling_method`, `test_type`, `p_value`, `statistic`, `ground_truth`, `scaling_params`, `seed`. **Logic**: The loop must run **at least 10,000 iterations per configuration** (FR-004). It must record the random seed for every iteration (Constitution Principle VI). **Time Check**: Check elapsed time at regular intervals. If time limit (6h) is exceeded, call `save_checkpoint` (T064) to save partial results to `results/partial_checkpoint.csv` and exit with code 99. **Dependency**: Requires T011, T019-T021, T022-T023, T065.
- [X] T028b [US3] **Implement Checkpoint & Time-Limit Logic**: In `code/main.py`, implement the checkpoint mechanism to save partial results to `results/partial_checkpoint.csv` at regular intervals or when the time limit (T064) is approached. **Verification**: Unit test `code/tests/unit/simulation/test_main.py` asserting that partial results are saved correctly. **Dependency**: Requires T064.
- [X] T028c [US3] **Implement Result Aggregation & CSV Writing**: In `code/main.py`, implement the logic to aggregate results and write to `results/simulation_results.csv` after each configuration or at the end. **Schema**: `iteration_id`, `config_id`, `scaling_method`, `test_type`, `p_value`, `statistic`, `ground_truth`, `scaling_params`, `seed`. **Verification**: Unit test `code/tests/unit/simulation/test_main.py` asserting file exists and contains valid schema. **Dependency**: Requires T028a.
- [X] T029 [US3] Implement `calculate_aggregate_metrics` in `code/analysis/metrics.py` to compute Type I error and Power. **Formula**: Type I error = count(p < 0.05) / total_iterations (for null hypothesis). Power = count(p < 0.05) / total_iterations (for alternative hypothesis). **CI Method**: Use Clopper-Pearson exact method for confidence intervals. **Deliverable**: `results/aggregate_metrics.csv` with schema: `config_id`, `scaling_method`, `test_type`, `error_rate`, `power`, `ci_lower`, `ci_upper`. **Dependency**: Requires T028c to produce `results/simulation_results.csv`.
- [X] T030 [US3] Implement `generate_error_rate_plot` in `code/visualization/plots.py` showing empirical rate vs with confidence intervals (using Clopper-Pearson). **Input**: Expects a DataFrame with columns `[scaling_method, error_rate, ci_lower, ci_upper]`. **Requirements**: Use `seaborn` to plot error bars for confidence intervals. and a horizontal reference line at the conventional significance threshold. **Dependency**: Requires T029 to produce aggregate metrics.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Real-World Dataset Validation (Priority: P4)

**Goal**: Ingest public datasets (UCI/OpenML) and validate simulation findings on real data.

**Independent Test**: Run pipeline on Iris dataset, verify scaling, testing, and report generation without crashing.

### Tests for User Story 4

- [X] T033 [P] [US4] Contract test for dataset ingestion (handle missing values, output clean DF) in `code/tests/unit/preprocessing/test_ingestion.py`
- [X] T034a [P] [US4] Integration test for full real-world pipeline on Iris dataset in `code/tests/integration/test_real_world.py`

### Implementation for User Story 4

- [X] T035 [US4] Implement `download_dataset` function in `code/preprocessing/ingestion.py` using specific verified URLs or `datasets.load_dataset`. **Requirement**: Must use the streaming loader from T024 and only download datasets listed in `data/config/datasets.yaml` (T027d). **Dependency**: Requires T024 and T027d.
- [X] T036 [US4] Implement data cleaning and preprocessing (imputation/removal) in `code/preprocessing/ingestion.py`
- [X] T037 [US4] Create `RealWorldDataset` entity and metadata storage in `code/preprocessing/ingestion.py`
- [X] T051 [US4] **Implement Explicit Dataset Sampling Logic**: In `code/preprocessing/ingestion.py`, add a dedicated function `sample_streamed_data` that takes a `stream` object and a `max_rows` integer (default a substantial number of samples). **Requirement**: Use `itertools.islice` to strictly limit rows. **Deliverable**: Function `sample_streamed_data` in `code/preprocessing/ingestion.py` returning a DataFrame and metadata dict. **Verification**: Unit test `code/tests/unit/preprocessing/test_ingestion.py` asserting correct sampling and metadata. **Dependency**: Must be completed before T038 and T056.
- [X] T056 [US4] **Ingest Full Dataset Set**: Implement ingestion and processing of all public datasets listed in `data/config/datasets.yaml`. **Deliverable**: `results/real_world_ingestion_log.csv` with schema: `dataset_id`, `source_url`, `status`, `row_count`, `checksum`. **Verification**: Script `code/tests/unit/preprocessing/test_ingestion.py` asserting all datasets are processed and the log file contains the correct schema. **Dependency**: Requires T027d and T051.
- [X] T038 [US4] **Reuse Scaling and Testing Pipeline on Real Data**: Apply the scaling and testing pipeline to real data using the sampling logic from T051. **Deliverable**: `results/real_world_results.csv` with p-values and effect sizes for each dataset. **Verification**: Script `code/tests/integration/test_real_world.py` asserting file exists and contains p-values for multiple datasets. **Dependency**: Requires T051 and T056.
- [X] T039 [US4] **Implement Comparison Report Generation**: Generate `results/comparison_report.md` comparing synthetic vs real-world results. **Schema**: Markdown table with columns: `Metric`, `Synthetic_Value`, `Real_Value`, `Mean_Absolute_Difference`, `Correlation_Coefficient`. **Metrics**: Calculate `Mean_Absolute_Difference` (mean of |synthetic_p - real_p|) and `Correlation_Coefficient` (Pearson correlation between synthetic and real p-values). **Content**: Must include a table comparing synthetic vs real-world error rates and effect sizes. **Verification**: Script `code/tests/unit/analysis/test_metrics.py` asserting the report is generated with the correct schema and metrics. **Dependency**: Requires T038 to produce real-world results, T029 to produce synthetic results, and T057 to produce sensitivity analysis.
- [X] T052 [US4] **Add Real-World Data Source Verification**: In `code/tests/unit/preprocessing/test_real_data_integrity.py`, add an assertion that checks the `source_id` in the loaded DataFrame metadata matches one of the IDs in `data/config/datasets.yaml`. **Rationale**: Ensures the data loader is not accidentally falling back to a default or cached synthetic dataset if the network fetch fails or times out.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Documentation updates in `docs/` and `quickstart.md`.
- [X] T041 Code cleanup and refactoring of `code/simulation/generator.py` for performance.
- [X] T042a [P] Vectorize `generate_synthetic_data` in `code/simulation/generator.py` using NumPy array operations instead of Python loops.
- [X] T042b [P] Parallelize simulation loop in `code/main.py` using `multiprocessing`.
- [X] T043 [P] Additional unit tests for edge cases.
- [X] T044 [P] Run quickstart.md validation.

---

## Phase 8: Review Resolution & Data Integrity (Revision Pass)

**Purpose**: Improvements to ensure data integrity and compliance with specific review concerns.

### Implementation for Review Resolution

- [X] T046 [US4] Implement Streaming Loaders (Consolidated into T024/T026)
- [X] T047 [US4] Enforce Fail-Loudly Data Fetch (Consolidated into T025)
- [X] T048 [US4] Update Dataset Configuration (using verified IDs from research.md) (Consolidated into T027d)
- [X] T034b [US4] Validate the configuration in `data/config/datasets.yaml` created by T027d.
- [X] T049 [US4] Add Verification Task for Real Data (Consolidated into T028)
- [X] T050 [US4] Refine Real-World Pipeline Logic (Consolidated into T038)

- [X] T053 [US3/US4] **Implement Mixed-Effects Model Analysis**: In `code/analysis/metrics.py`, implement a function `fit_mixed_effects_model` using `statsmodels`. **Requirement**:
 - **For Real-World Data**: Model `deviation ~ scaling_method + (1 | dataset_id)` where `dataset_id` is a random effect.
 - **For Synthetic Data**: Model `deviation ~ scaling_method + (1 | config_id)` where `config_id` is a **random effect**. **Rationale**: This implementation satisfies FR-010 and SC-007, which mandate fitting mixed-effects models for all data to test scaling impact. This requirement overrides the plan's Complexity Tracking note which rejected mixed-effects for synthetic data, as the Spec takes precedence.
 - **Deviation Definition**: `deviation = |p_value - alpha|`.
 - **Input Data**: Use `results/aggregate_metrics.csv` (from T029) with columns `error_rate`, `power`, `scaling_method`, `config_id`.
 - **Deliverable**: Function `fit_mixed_effects_model` in `code/analysis/metrics.py` returning a model summary object.
 - **Verification**: Test asserting p-value < 0.05 for scaling_method on real-world data and that synthetic data is included in the analysis with the correct random-effect structure for `config_id`.
 - **Dependency**: Requires T029 to produce aggregate metrics and T056 to produce real-world data. **Requires T002** (statsmodels).
- [X] T055 [US4] **Validate Real-World Pipeline on Non-Iris Datasets**: Extend the integration test in `code/tests/integration/test_real_world.py` to run the full pipeline on at least 3 additional datasets from `data/config/datasets.yaml` (excluding Iris). **Requirement**: Each dataset must be processed using the streaming/sampling logic defined in T051. **Deliverable**: `results/real_world_validation_report.md` generated upon success. **Verification**: Test report confirming successful execution and p-value output for each dataset. **Dependency**: Requires T056 to ingest all datasets.
- [X] T057 [US3] **Implement Sensitivity Analysis for Alpha Thresholds**: In `code/analysis/metrics.py`, add a function `run_sensitivity_analysis` that re-calculates Type I error rates and power for a range of alpha levels. **Requirement**: This addresses the assumption about threshold justification in the spec and satisfies SC-007. **Logic**: Read `results/simulation_results.csv` (raw data) and re-calculate error rates by counting p-values < alpha for each alpha level. The specific alpha levels to test (e.g., standard significance thresholds) are to be determined by the implementer based on the research design. **Deliverable**: A new CSV `results/sensitivity_analysis.csv` containing error rates and power for each alpha level and scaling method. **Verification**: Unit test asserting the function produces results for multiple alpha levels. **Dependency**: Requires T028c to produce base simulation results.
- [X] T058 [US3] **Implement Numerical Precision Stability Check**: In `code/analysis/tests.py`, add a function `check_numerical_stability` that compares the p-values of scaled vs unscaled data specifically for the t-test and ANOVA. **Requirement**: Log any p-value differences as warnings if they exceed a negligible threshold., as these indicate potential numerical instability rather than statistical change. **Deliverable**: A log file `logs/numerical_stability.log` capturing any deviations in the format `WARNING: Numerical deviation detected: {method} diff={diff}`. **Verification**: Unit test asserting the function correctly identifies a known numerical deviation. **Dependency**: Requires T022 and T023.
- [X] T059 [US4] **Implement Real-World Dataset Metadata Enrichment**: In `code/preprocessing/ingestion.py`, extend the `RealWorldDataset` entity to include a `source_verified` boolean flag that is set to `True` only if the dataset was successfully fetched from the verified URL in `data/config/datasets.yaml`. **Requirement**: This flag must be propagated to `results/real_world_results.csv`. **Deliverable**: Updated schema for `results/real_world_results.csv`: `dataset_id`, `source_url`, `p_value`, `effect_size`, `source_verified`. **Verification**: Unit test asserting the flag is set correctly for verified and unverified sources. **Dependency**: Requires T027d and T056.

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