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
- [X] T003a [P] Configure linting tool by creating `.ruff.toml` with explicit rules: `[lint]` section enabling `E`, `F`, `W`, `I` rules, setting `line-length = 88`, and enabling `D` (Pydocstyle) and `PI` (PII) rules to satisfy Constitution Principle III (Data Hygiene).
- [X] T003b [P] Configure formatting tool by creating `pyproject.toml` with Black settings (e.g., `line-length = 88`, `target-version = ['py311']`)
- [X] T003c [P] Implement PII scan script skeleton `code/scripts/pii_scan.py` (create file, imports, main function stub).
- [X] T003d [P] Implement PII scan logic in `code/scripts/pii_scan.py` to run `ruff check --select=PII001,PII002 .` and fail the build if PII is detected, satisfying Constitution Principle III.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils.py` for seed pinning, logging setup, and error handling wrappers
- [X] T005 [P] Implement `code/data_loader.py` with OpenML fetch logic, binary-class validation, and SHA-256 checksum caching to `data/raw/`. **MUST** support direct URL fetch for UCI datasets if not available on OpenML. **MUST** explicitly select 15 binary classification datasets (OpenML IDs: 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 - or a verified equivalent list of 15 binary datasets) defined in `code/config.py` (Constitution Principle VII). **Logic**:
 1. Validate each dataset: if `n_samples < 100`, log a warning and **skip only that specific dataset** (do not fail the whole run).
 2. Perform **programmatic spectrum validation**: verify the remaining valid datasets collectively span a broad sample size range (N<1k, 1k-10k, N>10k) and generate `data/spectrum_report.json` with this verification.
 3. If the count of valid datasets is insufficient (< 15), log the exact message: "CRITICAL: Insufficient valid datasets (< 15). Exiting." and exit with code 1.
 4. Implement **robust network error handling**: if a download fails, log the error, skip that dataset, and continue with the rest.
 5. **Checksum Verification**: Integrate checksum verification logic to ensure data integrity before use.
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
- [X] T019a [US2] Implement **Pearson correlation** calculation in `code/analyser.py` to compute correlation coefficients between **CV** (as required by FR-004/SC-001) and dataset properties (log(n_samples), log(n_features)).
 - **Data Source**: Must source dataset properties (n_samples, n_features) from `data/spectrum_report.json` generated by T005.
 - **Primary Output**: Pearson r and p-value on CV vs log(N).
 - **Secondary**: Compute Spearman rho for robustness check.
 - **Output**: Append results to `results/correlation_results.csv` with `metric_type='CV'`.
 - **Constraint**: Must explicitly state in the output that these correlations are computed on the **Coefficient of Variation** metric as per SC-001.
- [X] T019b [US2] Implement **Pearson correlation** calculation in `code/analyser.py` to compute correlation coefficients between **log(CV)** (log(CV)) and dataset properties (log(n_samples), log(n_features)) as required by Plan 'Log-Transformed Variance' decision.
 - **Primary Output**: Pearson r and p-value on log(CV) vs log(N).
 - **Secondary**: Compute Spearman rho for robustness check.
 - **Output**: Append results to `results/correlation_results.csv` with `metric_type='LogCV'`.
 - **Constraint**: Must explicitly state in the output that these correlations are computed on the **Log-Transformed CV** metric as per Plan.
 - **Additional Output**: Must also calculate and output regression coefficients (slope, intercept) for the log-log fit to `results/regression_coefficients.csv`.
- [X] T020 [US2] Compute **Theoretical Deviation** and residuals from log-log linear regression of **log(CV)** against log(n_samples) and log(n_features).
 - **Input**: Must consume regression coefficients (slope, intercept) from T019b output (`results/regression_coefficients.csv`).
 - **Formula**: Calculate deviation as `log(CV) - log(1/sqrt(N))`.
 - **Output Artifact**: Write residuals and deviation metrics to `results/theoretical_deviation.csv`.
 - **Dependency**: Must wait for T019b.
- [X] T021 [US2] Write summary tables to `results/stability_metrics.csv` and `results/correlation_results.csv`.
 - **Schema `stability_metrics.csv`**: `dataset_id` (int), `model_name` (str), `mean_accuracy` (float), `cv_accuracy` (float), `mean_f1` (float), `cv_f1` (float), `log_cv_accuracy` (float).
 - **Schema `correlation_results.csv`**: `dataset_id` (int), `model_name` (str), `metric_type` (str: 'CV', 'LogCV'), `pearson_r` (float), `pearson_p_value` (float), `spearman_rho` (float), `spearman_p_value` (float), `feature_count` (int), `sample_size` (int).
 - **Primary Constraint**: `pearson_r` and `pearson_p_value` must be the primary columns used for decision making.
 - **Explicit Requirement**: The `metric_type` column MUST distinguish between 'CV' (SC-001 requirement) and 'LogCV' (Plan requirement) to ensure both analyses are present and traceable.
 - **Implementation Logic**:
  1. Read `results/raw_evaluations.csv` and aggregate to compute stability metrics (mean, std, cv, log(CV)) per (dataset, model).
  2. Write aggregated metrics to `results/stability_metrics.csv`.
  3. Read `results/correlation_results.csv` (populated by T019a and T019b) and write final summary to `results/correlation_results.csv` (overwriting or appending as needed to ensure all rows are present).
  4. Ensure all required columns are populated from upstream tasks.
 - **Dependency**: Must wait for T018a, T018b, T019a, T019b, and T020.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance of Variance Differences (Priority: P3)

**Goal**: Apply Block Permutation Test on the absolute differences of squared deviations to compare variance distributions and correct for multiple comparisons.

**Independent Test**: Generate synthetic groups with known different variances and verify the test correctly rejects the null hypothesis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for permutation test logic in `tests/unit/test_analyser.py`
- [X] T024 [P] [US3] Unit test for Benjamini-Hochberg correction implementation in `tests/unit/test_analyser.py`

### Implementation for User Story 3

- [X] T025 [US3] Implement **Block Permutation Test** in `code/analyser.py` to compare variance distributions across LR, RF, and SVM.
 - **Test Statistic**: Calculate the absolute difference of the variances (|Var_A - Var_B|) derived from the squared deviations of accuracy scores for each model pair.
 - **Input**: Must consume variance values from T018a/T018b output.
 - **Algorithm**: **Block Permutation**: Permute entire repeat indices (0-9) as blocks, keeping fold indices within repeats intact. This preserves the dependence structure of repeated CV scores.
 - **Logic**: Generate results for **all three pairwise combinations** (LR vs RF, RF vs SVM, LR vs SVM) for each dataset.
 - **Output**: Raw p-values for each model pair per dataset to `results/permutation_results.csv` (raw).
- [X] T026 [US3] Implement **Multiple Comparison Correction** globally across the set of ALL hypothesis tests (correlations and Permutation Tests) performed across the full collection of datasets.
 - **Input**: Must consume p-values from `results/correlation_results.csv` (from T019a/T019b) and `results/permutation_results.csv` (from T025). **Must wait for T025 completion**.
 - **Scope**: 'ALL' tests = Union of all p-values from correlation results and permutation test results.
 - **Method 1 (FDR)**: Implement Benjamini-Hochberg procedure (FDR control) as explicitly required by Plan for exploratory analysis.
 - **Method 2 (FWER)**: Implement Bonferroni correction to calculate the achieved Family-Wise Error Rate (FWER) to satisfy FR-007 and SC-005.
 - **Output**: Adjusted p-values for both methods.
 - **Constraint**: Must explicitly report both FDR-adjusted p-values (BH) and FWER-adjusted p-values (Bonferroni).
- [X] T027 [US3] Write permutation test results to `results/permutation_results.csv`.
 - **Schema**: `dataset_id` (int), `model_a` (str), `model_b` (str), `statistic` (float), `raw_p_value` (float), `adj_p_value_bh` (float), `adj_p_value_bonf` (float), `significant_bh` (bool), `significant_bonf` (bool).
 - **Dependency**: Must wait for T026 to produce adjusted p-values.
 - **Coverage Constraint**: Must ensure all three pairwise combinations (LR vs RF, RF vs SVM, LR vs SVM) are generated for every dataset.
- [X] T028a [US3] Implement report generator aggregation logic in `code/report_generator.py` to aggregate `results/stability_metrics.csv`, `results/correlation_results.csv`, and `results/permutation_results.csv`.
 - **Input Columns**: Specify exact columns from each CSV to be used (e.g., `dataset_id`, `model_name`, `pearson_r`, `adj_p_value_bh`, `adj_p_value_bonf`, etc.).
 - **Aggregation Logic**: Define grouping, filtering, and summarization steps (e.g., group by dataset, filter by significance).
 - **Output Format**: Specify the intermediate data structure (e.g., DataFrame) to be passed to the templating engine.
- [X] T028b [US3] Implement markdown templating logic in `code/report_generator.py` using `docs/report_template.md`.
 - **Template Variables**: List all variables to be bound (e.g., `summary_stats`, `significant_datasets`, `correlation_table`).
 - **Data Binding Logic**: Specify how data from T028a is mapped to template variables.
 - **Library**: Use Jinja2 for templating.
- [X] T028c [US3] Generate a final summary report in `results/final_report.md` by executing the aggregation and templating logic.
 - **Content**: Must include the following sections:
 1. 'Significant Variance Differences' (list datasets where adj_p < 0.05 for either BH or Bonferroni).
 2. 'Model Comparison' (rank by mean CV).
 3. 'Correction Methodology' (confirm Benjamini-Hochberg application for FDR and Bonferroni for FWER).
 4. 'Achieved FDR' (calculate and report the effective alpha level).
 5. 'Achieved FWER' (report the calculated FWER as per SC-005).
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
 - **Concrete Actions**: Implement chunked reading in `data_loader.py` for large datasets; add explicit `gc.collect()` calls after each dataset processing; use `del` to remove large objects from memory.
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
- [X] T038a [P] **Multiple Comparison Correction Verification**: Add unit test in `tests/unit/test_analyser.py` specifically for the Benjamini-Hochberg ordering logic. (Addresses FR-007 & SC-005).
 - **Test Case**: Provide a set of p-values (e.g., [0.01, 0.02, 0.03, 0.04]).
 - **Expected Output**: Verify the adjusted p-values follow the BH ordering.
 - **Target Function**: `apply_benjamini_hochberg`
- [X] T038b [P] **Multiple Comparison Correction Verification**: Add unit test in `tests/unit/test_analyser.py` specifically for the Benjamini-Hochberg monotonicity logic. (Addresses FR-007 & SC-005).
 - **Test Case**: Provide a set of p-values and verify that adjusted p-values are monotonically non-decreasing.
 - **Target Function**: `apply_benjamini_hochberg`
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
- [X] T040a [P] **Adaptive Fold Logic Validation**: Add unit test in `tests/unit/test_evaluator.py` to verify that datasets with N < 100 are **skipped**. (Addresses Plan T004 & Spec Edge Case: Dataset Size Limit).
 - **Mock Data**: Create a mock dataset with N=50.
 - **Expected Log Message**: "Skipping dataset with n_samples=50 (< 100)."
 - **Target Function**: `evaluate_model`
- [X] T040b [P] **Adaptive Fold Logic Validation**: Add unit test in `tests/unit/test_evaluator.py` to verify that datasets with N >= 100 use K=10. (Addresses Plan T004 & Spec Edge Case: Dataset Size Limit).
 - **Mock Data**: Create a mock dataset with N=200.
 - **Expected Parameter Values**: `n_splits=10`, `n_repeats=10`.
 - **Target Function**: `evaluate_model`

---

## Phase Y: Review Resolution & Hardening (Continued)

**Purpose**: Address remaining reviewer concerns regarding statistical validity, reproducibility, and edge cases.

- [ ] T047 [P] **CI Integration for Data Download**: Update `.github/workflows/ci.yml` to include a step that runs `code/download_data.py` as a one-time setup before the main evaluation job, ensuring datasets are cached correctly.
 - **Logic**: This step should only run on `main` branch or specific tags, not on every PR, to avoid unnecessary downloads.
 - **Constraint**: Ensure that the downloaded data is cached across CI runs to save time and bandwidth.
 - **Note**: This step must also run the checksum verification logic from T005 to ensure data integrity.
- [ ] T048 [P] **Documentation Update for Statistical Methods**: Update `docs/report_template.md` and `specs/001-assessing-the-stability-of-statistical-m/research.md` to explicitly describe the statistical methods used (Log-Log transformation, Block Permutation Test, BH correction, Bonferroni correction) and their justification.
 - **Content Requirements**:
  1. **Log-Log Transformation**: Add a section explaining that raw CV distributions are skewed and non-linear with respect to sample size. State that a log-log transformation is applied to linearize the power-law relationship (CV ~ 1/√N) and normalize residuals for Pearson correlation, citing standard statistical practice for variance stabilization.
  2. **Block Permutation Test**: Add a section justifying the use of Block Permutation over standard permutation. Explicitly state that repeated CV scores within a single repeat are not independent; therefore, permuting individual scores would inflate Type I error. The task must describe permuting entire repeat blocks to preserve the dependence structure.
  3. **Benjamini-Hochberg (BH) Correction**: Add a section explaining that for exploratory analysis of 15 datasets × 3 models, Bonferroni correction is too conservative (low power). Justify BH as the standard method for controlling the False Discovery Rate (FDR) in large-scale hypothesis testing.
  4. **Bonferroni Correction**: Add a section stating that Bonferroni is implemented alongside BH to explicitly calculate and report the achieved Family-Wise Error Rate (FWER) as required by SC-005, serving as a conservative bound.
 - **Action**: Edit `docs/report_template.md` to include these specific explanatory blocks in the "Methodology" section. Edit `research.md` to include the same justifications and add formal citations to the relevant statistical literature (e.g., Benjamini & Hochberg 1995 for BH, standard texts for log-transformation).
 - **Constraint**: Ensure that the documentation is clear, accessible, and directly addresses the "Why" of each method choice.
- [ ] T049 [P] **Verification of Integrated Logic**: Verify that the logic previously assigned to T045 (Checksum Verification) is fully present in T005 and T047, and that the logic for T046 (Memory Profiling) is fully present in T031 and T036b.
 - **Action**: Review `code/data_loader.py` (T005) and `.github/workflows/ci.yml` (T047) to confirm checksum verification is executed. Review `code/evaluator.py` (T031) and `code/main.py` (T036b) to confirm memory management and signal handling are implemented.
 - **Output**: A verification note in the PR description confirming these integrations are complete, allowing T045 and T046 to be permanently removed.

---