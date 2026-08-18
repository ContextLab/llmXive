# Tasks: Assessing the Stability of Statistical Model Performance Across Data Subsets

**Input**: Design documents from `/specs/001-assessing-the-stability-of-statistical-m/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project - adjusted based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` by creating files: `code/__init__.py`, `code/main.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `tests/__init__.py`, `tests/contract/.gitkeep`, `tests/unit/.gitkeep`, `tests/integration/.gitkeep`
- [X] T002 Initialize Python project with `requirements.txt` containing pinned versions: `scikit-learn>=1.3.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `scipy>=1.11.0`, `openml>=0.13.0`
- [X] T003 [P] Implement PII scan script `code/scripts/pii_scan.py` to run `ruff check --select=PII001,PII002.` and fail the build if PII is detected, satisfying Constitution Principle III (Data Hygiene).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils.py` for seed pinning, logging setup, and error handling wrappers
- [X] T005 [P] Implement `code/data_loader.py` with OpenML fetch logic, binary-class validation, and SHA-256 checksum caching to `data/raw/`. **MUST** support direct URL fetch for UCI datasets if not available on OpenML. **MUST** dynamically select 15 binary classification datasets based on diversity criteria (Constitution Principle VII) rather than using a hardcoded list. **Logic**:
 1. Fetch a candidate pool of binary classification datasets (e.g., top 50 by size or random sample) from OpenML.
 2. Validate each dataset: if `n_samples < 100`, log a warning and **skip only that specific dataset**.
 3. Perform **programmatic spectrum validation**: verify the candidate pool spans a broad sample size range (N<1k, 1k-10k, N>10k).
 4. **Dynamic Selection**: From the valid pool, select exactly 15 datasets that best cover the required spectrum (N<1k, 1k-10k, N>10k) by sorting by n_samples and taking the top 5 from each of the three bins. If the pool is insufficient to cover all bins, expand the search or log a CRITICAL error: "CRITICAL: Insufficient valid datasets to cover required spectrum. Exiting." and exit with code 1.
 5. **Robust Network Error Handling**: if a download fails, log the error, skip that dataset, and continue with the rest.
 6. **Checksum Verification**: Integrate checksum verification logic to ensure data integrity before use.
 7. Generate `data/spectrum_report.json` documenting the final selection and its diversity coverage.
 8. **Reproducibility Cache**: Save the final list of 15 dataset IDs to `data/spectrum_report.json`. Subsequent runs MUST use this cached list to ensure reproducibility (Constitution Principle I).
- [X] T006 Implement `code/preprocessor.py` with leakage-safe imputation (median/mode) and scaling wrappers
- [X] T007 [P] Create contract tests in `tests/contract/test_dataset_schema.py` and `tests/contract/test_evaluation_run_schema.py` to validate schemas defined in `specs/001-assessing-the-stability-of-statistical-m/contracts/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Repeated Cross-Validation Execution (Priority: P1) 🎯 MVP

**Goal**: Execute repeated k-fold evaluations for LR, RF, Linear SVM on multiple datasets, recording raw metrics.

**Independent Test**: Run on a single small dataset (e.g., Iris) and verify that a sufficient number of records are generated with non-zero variance across all models.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These are "Write Test" tasks (TDD). They must be written *before* T011 is implemented, but they *execute* after T011 is complete.

- [X] T009 [P] [US1] Contract test for `EvaluationRun` schema in `tests/contract/test_evaluation_run.py` (Depends on Phase 2 schema definitions)
- [X] T010a [US1] **Write Test Fixture** `test_fixture_iris_binary` in `tests/integration/test_cv_engine.py` to create a binary subset of Iris from OpenML.
- [X] T010b [US1] **Write Test** `test_repeated_cv_iris_row_count` in `tests/integration/test_cv_engine.py` asserting the expected number of rows are generated (multiple repeats × 3 models).
- [X] T010c [US1] **Write Test** `test_repeated_cv_iris_variance` in `tests/integration/test_cv_engine.py` asserting non-zero variance in accuracy scores across multiple repeats for at least one model.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/evaluator.py` with `RepeatedStratifiedKFold` logic.
 - **Logic**:
 - If `n_samples < 100`: log warning and **skip** dataset (Spec Edge Case: "Skip if insufficient samples").
 - If `100 <= n_samples < 200`: log warning and **proceed with caution** (Spec Edge Case: "10-fold may be unstable for N<200, but do not skip unless N<100").
 - If `n_samples >= 200`: use `RepeatedStratifiedKFold(n_splits=10, n_repeats=10)`.
 - **Constraint**: It MUST NOT reduce the fold count for valid datasets (N>=100).
- [X] T012 [US1] Implement training loop for Logistic Regression, Random Forest (n_estimators=100), and Linear SVM in `code/evaluator.py` (Depends on T011 structure)
- [X] T013 [US1] Implement metric calculation (Accuracy, F1) inside the CV loop to prevent leakage.
 - **Function Name**: `calculate_metrics(y_true, y_pred)`
 - **Return Type**: `pandas.DataFrame` with columns `['accuracy', 'f1_score']`.
 - **Output**: Must be consumed by T014.
- [X] T014 [US1] Write raw evaluation results to `results/raw_evaluations.csv` with exact columns and types:
 - **Schema**: `dataset_id` (int), `model_name` (str), `fold_id` (int), `repeat_id` (int), `accuracy` (float), `f1_score` (float).
 - **Dependency**: Must wait for T013 to produce the metrics dataframe.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Variance Quantification and Correlation Analysis (Priority: P2)

**Goal**: Calculate CV (std/mean) for each (dataset, model) pair and compute Pearson correlations with dataset properties.

**Independent Test**: Feed synthetic data with zero variance and verify CV is 0; verify correlation matrix matches expected synthetic relationships.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for `calculate_cv` function handling zero-variance cases in `tests/unit/test_analyser.py`
- [X] T017 [P] [US2] Unit test for Pearson correlation calculation in `tests/unit/test_analyser.py`
- [X] T042 [P] [US2] **Write Unit Test** for `calculate_log_log_correlation` function in `tests/unit/test_analyser.py`.
 - **Target Function**: `calculate_log_log_correlation` (defined in T019b).
 - **Test Case**: Create synthetic data with known power-law relationship and verify the linearized correlation.

### Implementation for User Story 2

- [X] T018a [US2] Implement aggregation logic in `code/analyser.py` to compute `mean_accuracy`, `std_accuracy`, `cv_accuracy`, `mean_f1`, `std_f1`, `cv_f1` per (dataset, model).
 - **Input**: Must consume `results/raw_evaluations.csv` (validated against schema from T007).
 - **Output**: Intermediate DataFrame with CV metrics.
 - **Constraint**: Must handle `std=0` cases by setting CV to 0 and flagging for exclusion in correlation analysis.
- [X] T018b [US2] Implement aggregation logic in `code/analyser.py` to compute `log_variance_accuracy` (log(std^2)) and `log_variance_f1` per (dataset, model).
 - **Input**: Must consume `results/raw_evaluations.csv`.
 - **Output**: Intermediate DataFrame with Log-Variance metrics.
 - **Constraint**: Must handle `std=0` cases by setting log_variance to -999 (or similar sentinel) and flagging for exclusion.
- [X] T019a [US2] **PRIMARY**: Implement **Pearson correlation** calculation in `code/analyser.py` to compute correlation coefficients between **CV** (as required by FR-004/SC-001) and dataset properties (log(n_samples), log(n_features)).
 - **Data Source**: Must source dataset properties (n_samples, n_features) from `data/spectrum_report.json` generated by T005.
 - **Primary Output**: Pearson r and p-value on CV vs log(N).
 - **Secondary**: Compute Spearman rho for robustness check.
 - **Output**: Append results to `results/correlation_results.csv` with `metric_type='CV'`.
 - **Constraint**: This is the **primary** analysis for SC-001 and SC-002.
- [X] T019b [US2] **SECONDARY**: Implement **Pearson correlation** calculation in `code/analyser.py` to compute correlation coefficients between **log(CV)** (log(CV)) and dataset properties (log(n_samples), log(n_features)) as a secondary/transformative analysis (Plan 'Log-Transformed Variance' decision).
 - **Input**: Must consume aggregated data. **Must filter out rows where CV=0** before calculating log(CV) to prevent undefined operations.
 - **Primary Output**: Pearson r and p-value on log(CV) vs log(N).
 - **Secondary**: Compute Spearman rho for robustness check.
 - **Output**: Append results to `results/correlation_results.csv` with `metric_type='LogCV'`.
 - **Constraint**: This is a **secondary** analysis to support the primary CV analysis.
 - **Additional Output**: Must also calculate and output regression coefficients (slope, intercept) for the log-log fit to `results/regression_coefficients.csv`.
- [X] T020 [US2] **SECONDARY**: Compute **Theoretical Deviation** and residuals from log-log linear regression of **log(CV)** against log(n_samples) and log(n_features).
 - **Input**: Must consume regression coefficients (slope, intercept) from T019b output (`results/regression_coefficients.csv`).
 - **Formula**: Calculate deviation as `log(CV) - (slope * log(N) + intercept)`. Uses the fitted slope from T019b, not a hardcoded -0.5.
 - **Output Artifact**: Write residuals and deviation metrics to `results/theoretical_deviation.csv`.
 - **Dependency**: Must wait for T019b.
- [X] T021 [US2] **Finalize and Write** summary tables to `results/stability_metrics.csv` and `results/correlation_results.csv`.
 - **Schema `stability_metrics.csv`**: `dataset_id` (int), `model_name` (str), `mean_accuracy` (float), `cv_accuracy` (float), `mean_f1` (float), `cv_f1` (float), `log_cv_accuracy` (float).
 - **Schema `correlation_results.csv`**: `dataset_id` (int), `model_name` (str), `metric_type` (str: 'CV', 'LogCV'), `pearson_r` (float), `pearson_p_value` (float), `spearman_rho` (float), `spearman_p_value` (float), `feature_count` (int), `sample_size` (int), `adj_p_value_holm` (float), `significant_holm` (bool).
 - **Primary Constraint**: `pearson_r` and `pearson_p_value` for `metric_type='CV'` must be the primary columns used for decision making.
 - **Implementation Logic**:
 1. Read `results/raw_evaluations.csv` and aggregate to compute stability metrics (mean, std, cv, log(CV)) per (dataset, model).
 2. Write aggregated metrics to `results/stability_metrics.csv`.
 3. Read `results/correlation_results.csv` (populated by T019a, T019b, and **updated by T026 to include adjusted p-values**) and write final summary to `results/correlation_results.csv`.
 4. Ensure all required columns are populated from upstream tasks, preserving the adjusted p-values added by T026.
 - **Dependency**: Must wait for T018a, T018b, T019a, T019b, T020, and **T026**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance of Variance Differences (Priority: P3)

**Goal**: Apply Block Permutation Test on the absolute differences of squared deviations to compare variance distributions and correct for multiple comparisons using **Holm-Bonferroni**.

**Independent Test**: Generate synthetic groups with known different variances and verify the test correctly rejects the null hypothesis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for permutation test logic in `tests/unit/test_analyser.py`
- [X] T024 [P] [US3] Unit test for Holm-Bonferroni correction implementation in `tests/unit/test_analyser.py`

### Implementation for User Story 3

- [X] T025 [US3] Implement **Block Permutation Test** in `code/analyser.py` to compare variance distributions across LR, RF, and SVM.
 - **Test Statistic**: Calculate the absolute difference of the variances (|Var_A - Var_B|) derived from the squared deviations of accuracy scores for each model pair.
 - **Input**: Must consume variance values from T018a/T018b output.
 - **Algorithm**: **Block Permutation**: Permute entire repeat indices (0-9) as blocks, keeping fold indices within repeats intact. This preserves the dependence structure of repeated CV scores.
 - **Logic**: Generate results for **all three pairwise combinations** (LR vs RF, RF vs SVM, LR vs SVM) for each dataset.
 - **Output**: Write raw p-values for each model pair per dataset to `results/permutation_results.csv` (raw).
- [X] T026 [US3] Implement **Multiple Comparison Correction** and **Final Write** globally across the set of ALL hypothesis tests (correlations and Permutation Tests) performed across the full collection of datasets.
 - **Input**: Must consume p-values from `results/correlation_results.csv` (from T019a/T019b) and `results/permutation_results.csv` (raw, from T025). **Must wait for T025 completion**.
 - **Scope**: 'ALL' tests = Union of all p-values from correlation results and permutation test results (225 total tests: 15 datasets * 3 models * 2 metrics for correlations + 15 datasets * 3 pairs for permutations). This single family is used for strict FWER control as required by FR-007 and SC-005.
 - **Method (FWER)**: Implement **Holm-Bonferroni** procedure (step-down) as explicitly required by Plan for strict FWER control.
 - **Action**: Apply correction to the union of all p-values.
 - **Output**:
 1. Append/Update `results/correlation_results.csv` with columns `adj_p_value_holm` and `significant_holm`.
 2. Append/Update `results/permutation_results.csv` with columns `adj_p_value_holm` and `significant_holm`.
 3. **Finalize and Write** the final `results/permutation_results.csv` with the complete schema including adjusted p-values.
 - **Constraint**: Must explicitly report Holm-Bonferroni adjusted p-values and ensure the final files contain the corrected values.
- [X] T028a [US3] Implement report generator aggregation logic in `code/report_generator.py` to aggregate `results/stability_metrics.csv`, `results/correlation_results.csv` (final, from T021/T026), and `results/permutation_results.csv` (final, from T026).
 - **Input Columns**: Specify exact columns from each CSV to be used (e.g., `dataset_id`, `model_name`, `pearson_r`, `adj_p_value_holm`, etc.).
 - **Aggregation Logic**: Define grouping, filtering, and summarization steps (e.g., group by dataset, filter by significance).
 - **Output Format**: Specify the intermediate data structure (e.g., DataFrame) to be passed to the templating engine.
- [X] T028b [US3] Implement markdown templating logic in `code/report_generator.py` using `docs/report_template.md`.
 - **Template Variables**: List all variables to be bound (e.g., `summary_stats`, `significant_datasets`, `correlation_table`).
 - **Data Binding Logic**: Specify how data from T028a is mapped to template variables.
 - **Library**: Use Jinja2 for templating.
- [X] T028c [US3] Generate a final summary report in `results/final_report.md` by executing the aggregation and templating logic.
 - **Content**: Must include the following sections:
 1. 'Significant Variance Differences' (list datasets where adj_p < 0.05 for Holm-Bonferroni).
 2. 'Model Comparison' (rank by mean CV).
 3. 'Correction Methodology' (confirm Holm-Bonferroni application for FWER).
 4. 'Achieved FWER' (report the calculated FWER as per SC-005).
 - **Dependency**: Must wait for T028a and T028b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029a [P] Update `README.md` with usage instructions.
 - **Content**: Include installation steps, usage examples, and expected outputs.
- [X] T029b [P] Update `specs/001-assessing-the-stability-of-statistical-m/quickstart.md` with dataset list.
 - **Content**: List all A set of datasets with their OpenML/UCI IDs and brief descriptions.
- [X] T029c [P] Add contribution guidelines to `CONTRIBUTING.md`.
 - **Content**: Include guidelines for code style, testing, and submitting PRs.
- [X] T031 Performance optimization: Ensure memory usage stays <7GB by processing datasets sequentially and clearing caches.
 - **Concrete Actions**: Implement chunked reading in `code/data_loader.py` for large datasets; add explicit `gc.collect()` calls after each dataset processing; use `del` to remove large objects from memory.
- [X] T032 [P] Run end-to-end validation on a small subset of datasets to verify total runtime < 6h.
 - **Script**: Create `scripts/run_e2e_validation.py` to execute the pipeline on a subset of datasets.
 - **Execution**: Run the script and record runtime in `results/e2e_validation_log.txt`.
- [X] T033 [P] Run `quickstart.md` validation to ensure reproducibility.
 - **Script**: Create `scripts/validate_quickstart.py` to execute the steps in `quickstart.md`.
 - **Validation**: Check for expected exit codes and output files; record results in `results/quickstart_validation_log.txt`.

---

## Phase X: Review Resolution & Hardening

**Purpose**: Address specific reviewer concerns regarding dataset diversity, statistical rigor, and CI reliability.

- [X] T036a [P] **CI Timeout Configuration**: Update `.github/workflows/ci.yml` to include a `timeout-minutes` directive with a sufficiently large value to accommodate the full evaluation job. (Addresses Plan T008 & Edge Case: Network/Timeout failure).
 - **YAML Path**: `.github/workflows/ci.yml` -> `jobs.evaluation.timeout-minutes`
 - **Value**: 360
- [X] T036b [P] **Signal Handler**: Implement `signal_handler` in `code/main.py` to gracefully shut down and save partial results if the runner is terminated early, ensuring no silent data loss. (Addresses Plan T008 & Edge Case: Network/Timeout failure).
 - **Signals**: Catch `SIGINT` and `SIGTERM`.
 - **Logic**: On signal, save partial results (e.g., `results/partial_evaluations.csv`) and exit gracefully.
 - **Function Signature**: `def signal_handler(signum, frame):`
- [X] T037a [P] **Zero-Variance Edge Case Handling**: Add explicit logic in `code/analyser.py` to detect datasets/models where `std=0` (perfect stability). (Addresses Spec Edge Case: Zero Variance).
 - **Location**: `code/analyser.py` -> `calculate_cv` function.
 - **Condition**: `if std == 0:`
 - **Action**: Log warning, set CV to 0, flag for exclusion.
- [X] T037b [P] **Zero-Variance Exclusion**: Update correlation calculation in `code/analyser.py` to exclude zero-variance cases to prevent division-by-zero errors. (Addresses Spec Edge Case: Zero Variance).
 - **Location**: `code/analyser.py` -> `calculate_correlation` function.
 - **Modification**: Add a filter step to exclude rows where `std == 0` before calling the correlation function.
- [X] T038a [P] **Multiple Comparison Correction Verification**: Add unit test in `tests/unit/test_analyser.py` specifically for the Holm-Bonferroni ordering logic. (Addresses FR-007 & SC-005).
 - **Test Case**: Provide a set of p-values (e.g., [0.01, 0.02, 0.03, 0.04]).
 - **Expected Output**: Verify the adjusted p-values follow the Holm-Bonferroni ordering.
 - **Target Function**: `apply_holm_bonferroni`
- [X] T038b [P] **Multiple Comparison Correction Verification**: Add unit test in `tests/unit/test_analyser.py` specifically for the Holm-Bonferroni monotonicity logic. (Addresses FR-007 & SC-005).
 - **Test Case**: Provide a set of p-values and verify that adjusted p-values are monotonically non-decreasing.
 - **Target Function**: `apply_holm_bonferroni`
- [X] T039a [P] **Dataset Diversity Verification**: Add unit test in `tests/unit/test_data_loader.py` that asserts the presence of datasets with N<1k. (Addresses Plan T005 & Constitution Principle VII).
 - **Mock Data**: Create a mock dataset with N=500.
 - **Assertion**: Verify that the dataset is included in the valid set.
 - **Target Function**: `validate_dataset_spectrum`
- [X] T039b [P] **Dataset Diversity Verification**: Add unit test in `tests/unit/test_data_loader.py` that asserts the presence of datasets with 1k-10k. (Addresses Plan T005 & Constitution Principle VII).
 - **Mock Data**: Create a mock dataset with N=5000.
 - **Assertion**: Verify that the dataset is included in the valid set.
 - **Target Function**: `validate_dataset_spectrum`
- [X] T039c [P] **Dataset Diversity Verification**: Add unit test in `tests/unit/test_data_loader.py` that asserts the presence of datasets with N>10k. (Addresses Plan T005 & Constitution Principle VII).
 - **Mock Data**: Create a mock dataset with N=50000.
 - **Assertion**: Verify that the dataset is included in the valid set.
 - **Target Function**: `validate_dataset_spectrum`
- [X] T040 [P] **Adaptive Fold Logic Validation**: Add unit tests in `tests/unit/test_evaluator.py` to verify that datasets with N < 100 are **skipped** and datasets with N >= 100 use K=10. (Addresses Plan T004 & Spec Edge Case: Dataset Size Limit).
 - **Mock Data**: Create mock datasets with N=50 and N=200.
 - **Expected Log Message (N=50)**: "Skipping dataset with n_samples=50 (< 100)."
 - **Expected Parameter Values (N=200)**: `n_splits=10`, `n_repeats=10`.
 - **Target Function**: `evaluate_model`

---

## Phase Y: Review Resolution & Hardening (Continued)

**Purpose**: Address remaining reviewer concerns regarding statistical validity, reproducibility, and edge cases.

- [X] T047 [P] **CI Integration for Data Download**: Update `.github/workflows/ci.yml` to include a step that runs `code/data_loader.py` (created in T005) as a one-time setup before the main evaluation job, ensuring datasets are cached correctly.
 - **Logic**: This step should only run on `main` branch or specific tags, not on every PR, to avoid unnecessary downloads.
 - **Constraint**: Ensure that the downloaded data is cached across CI runs to save time and bandwidth.
 - **Note**: This step must also run the checksum verification logic from T005 to ensure data integrity.
- [X] T048 [P] **Documentation Update for Statistical Methods**: Update `docs/report_template.md` (create if missing) and `specs/001-assessing-the-stability-of-statistical-m/research.md` to explicitly describe the statistical methods used (Log-Log transformation, Block Permutation Test, Holm-Bonferroni correction) and their justification.
 - **Content Requirements**:
 1. **Log-Log Transformation**: Add a section explaining that raw CV distributions are skewed and non-linear with respect to sample size. State that a log-log transformation is applied to linearize the power-law relationship (CV ~ 1/√N) and normalize residuals for Pearson correlation, citing standard statistical practice for variance stabilization.
 2. **Block Permutation Test**: Add a section justifying the use of Block Permutation over standard permutation. Explicitly state that repeated CV scores within a single repeat are not independent; therefore, permuting individual scores would inflate Type I error. The task must describe permuting entire repeat blocks to preserve the dependence structure.
 3. **Holm-Bonferroni Correction**: Add a section explaining that for strict Family-Wise Error Rate (FWER) control required by SC-005 and the Plan's Complexity Tracking, Holm-Bonferroni is preferred over Benjamini-Hochberg (which controls FDR) and standard Bonferroni (which is overly conservative). Justify Holm-Bonferroni as the optimal balance for this exploratory analysis.
 4. **Template Creation**: If `docs/report_template.md` does not exist, create it with the necessary sections (Methodology, Results, Discussion) and placeholders for the statistical outputs.
 - **Action**: Edit `docs/report_template.md` (or create it) to include these specific explanatory blocks in the "Methodology" section. Edit `research.md` to include the same justifications and add formal citations to the relevant statistical literature (e.g., Holm 1979 for Holm-Bonferroni, standard texts for log-transformation).
 - **Constraint**: Ensure that the documentation is clear, accessible, and directly addresses the "Why" of each method choice.
- [X] T049 [P] **Verification of Integrated Logic**: Verify that the logic for Checksum Verification is fully present in T005 and T047, and that the logic for Memory Profiling and Signal Handling is fully present in T031 and T036b.
 - **Action**: Review `code/data_loader.py` (T005) and `.github/workflows/ci.yml` (T047) to confirm checksum verification is executed. Review `code/evaluator.py` (T031) and `code/main.py` (T036b) to confirm memory management and signal handling are implemented.
 - **Output**: A verification note in the PR description confirming these integrations are complete.

---

## Phase Z: Final Validation & Execution Readiness

**Purpose**: Ensure the pipeline is robust, reproducible, and ready for the full execution run.

- [ ] T050 [P] **Final End-to-End Smoke Test**: Execute a full pipeline run on exactly 3 datasets (one from each size bin: <1k, 1k-10k, >10k) to verify the entire flow from download to final report generation without errors.
 - **Script**: Create `scripts/run_smoke_test.py` to orchestrate this specific subset.
 - **Validation**: Verify that `results/raw_evaluations.csv`, `results/stability_metrics.csv`, `results/correlation_results.csv`, `results/permutation_results.csv`, and `results/final_report.md` are all generated and contain valid data.
 - **Constraint**: This task MUST pass before the full 15-dataset run is triggered in CI.
- [ ] T051 [P] **Resource Usage Audit**: Run the smoke test (T050) with memory profiling enabled and log peak RSS memory usage to `results/memory_profile.log`.
 - **Tool**: Use `memory_profiler` or `tracemalloc`.
 - **Action**: Insert profiling decorators around `code/evaluator.py` and `code/analyser.py` functions.
 - **Goal**: Confirm peak memory usage remains < 6GB with a safety margin for the 7GB limit.
- [ ] T052 [P] **Determinism Verification**: Run the smoke test (T050) twice with the same seed and verify that the checksums of all output CSVs and the final report are identical.
 - **Action**: Add a script `scripts/verify_determinism.py` that runs the pipeline twice, computes SHA-256 hashes of all result files, and asserts equality.
 - **Goal**: Confirm that random seed pinning in `code/utils.py` is effective across all components.
- [ ] T053 [P] **CI Workflow Finalization**: Update `.github/workflows/ci.yml` to trigger the full pipeline (15 datasets) only on manual dispatch or specific branch pushes, ensuring the 6-hour timeout and signal handling are active.
 - **Action**: Add a `workflow_dispatch` trigger and configure the `evaluation` job to use the `signal_handler` from T036b.
 - **Goal**: Ensure the CI environment is correctly configured for the long-running job.