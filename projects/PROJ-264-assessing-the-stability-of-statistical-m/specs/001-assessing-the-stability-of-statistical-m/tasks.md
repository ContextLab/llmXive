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
- [X] T002 Initialize Python project with `requirements.txt` containing pinned versions: `scikit-learn>=1.3.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `scipy>=1.11.0`, `openml>=0.13.0`, `requests>=2.31.0`. **Note**: The `requests` library is explicitly required for the UCI fallback logic described in T005.
- [X] T003 [P] Implement PII scan script `code/scripts/pii_scan.py` to run `ruff check --select=PII001,PII002.` and fail the build if PII is detected, satisfying Constitution Principle III (Data Hygiene). **Sub-task**: Ensure `ruff` is installed and `pyproject.toml` is configured with the necessary PII rules if not already present.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils.py` for seed pinning, logging setup, and error handling wrappers
- [X] T005 [P] Implement `code/data_loader.py` with OpenML fetch logic, binary-class validation, and SHA-256 checksum caching to `data/raw/`. **MUST** support direct URL fetch for UCI datasets if not available on OpenML (requires `requests` library from T002). **MUST** load a FIXED, pre-verified list of 15 binary classification dataset IDs from `research.md` (Constitution Principle I). **Logic**:
 1. Read the fixed list of 15 dataset IDs from `research.md`.
 2. For each ID, fetch the dataset from OpenML (or UCI URL if OpenML fails).
 3. **Do not skip** datasets with `n_samples < 100` here; log a warning but include them in the report for T005c to filter.
 4. Perform **static spectrum validation**: verify the final list of valid datasets spans a broad sample size range (N<1k, 1k-10k, N>10k) AND feature dimension range (F<10, 10-50, F>50). If the fixed list fails to cover the spectrum, log a CRITICAL error and exit.
 5. **UCI Fallback Logic**: If OpenML fetch fails for a candidate, **construct the standard UCI URL** using the pattern ` (or similar based on the dataset's metadata name field). **Parse** the downloaded archive (CSV/ARFF) using `pandas.read_csv` or `arff.loadarff`. If parsing fails, log error and skip. **Do not** fall back to synthetic data.
 6. **Robust Network Error Handling**: if a download fails, log the error, skip that dataset, and continue with the rest.
 7. **Checksum Verification**: Integrate checksum verification logic to ensure data integrity before use.
 8. Generate `data/spectrum_report.json` documenting the final selection and its diversity coverage. **MUST** include a `selected_ids` array containing the exact list of dataset IDs used for the run to ensure reproducibility (Constitution Principle I).
- [X] T005b [P] **Generate Static Spectrum Report**: Create `data/spectrum_report.json` based on the fixed list from T005. **Action**: Run the data loader to fetch and validate the fixed 15 IDs, then write the `selected_ids` and diversity metrics to `data/spectrum_report.json`. This ensures the dataset list is locked before evaluation. **Dependency**: T005 must complete first (sequential, not parallel).
- [X] T005c [P] **Dataset Filter**: Implement a filter step in `code/data_loader.py` (or a separate script) that reads `data/spectrum_report.json`, filters out any datasets with `n_samples < 100` (logging warnings), and produces a final `data/filtered_dataset_ids.json`. **Constraint**: This step MUST run after T005/T005b and before T011 to centralize the skip logic. **Centralized Logic**: T005 and T011 MUST NOT contain their own skip logic for n<100; T005c is the sole filter.
- [X] T006 Implement `code/preprocessor.py` with leakage-safe imputation (median/mode) and scaling wrappers
- [X] T007 [P] Create contract tests in `tests/contract/test_dataset_schema.py` and `tests/contract/test_evaluation_run_schema.py` to validate schemas defined in `specs/001-assessing-the-stability-of-statistical-m/contracts/`
- [X] T009 [US1] Contract test for `EvaluationRun` schema in `tests/contract/test_evaluation_run.py` (Depends on T007). **Moved to Phase 2 to enforce Producer-Consumer order.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Repeated Cross-Validation Execution (Priority: P1) 🎯 MVP

**Goal**: Execute repeated k-fold evaluations for LR, RF, Linear SVM on multiple datasets, recording raw metrics.

**Independent Test**: Run on a single small dataset (e.g., Iris) and verify that a sufficient number of records are generated with non-zero variance across all models.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These are "Write Test" tasks (TDD). They must be written *before* T011 is implemented, but they *execute* after T011 is complete.

- [X] T010a [US1] **Write Test Fixture** `test_fixture_iris_binary` in `tests/integration/test_cv_engine.py` to create a binary subset of Iris from OpenML.
- [X] T010b [US1] **Write Test** `test_repeated_cv_iris_row_count` in `tests/integration/test_cv_engine.py` asserting the expected number of rows are generated (multiple repeats × 3 models).
- [X] T010c [US1] **Write Test** `test_repeated_cv_iris_variance` in `tests/integration/test_cv_engine.py` asserting non-zero variance in accuracy scores across multiple repeats for at least one model.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/evaluator.py` with `RepeatedStratifiedKFold` logic.
 - **Logic**:
 - **Do not skip** datasets with `n_samples < 100` here; rely on T005c to filter the input list.
 - If `100 <= n_samples < 200`: log warning and **proceed with caution** (Spec Edge Case: "10-fold may be unstable for N<200, but do not skip unless N<100").
 - If `n_samples >= 200`: use `RepeatedStratifiedKFold(n_splits=10, n_repeats=10)`.
 - **Constraint**: It MUST NOT reduce the fold count for valid datasets (N>=100).
 - **Dependency**: Must use the filtered list from T005c.
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
- [X] T019b [US2] **PRIMARY**: Implement **Pearson correlation** calculation in `code/analyser.py` to compute correlation coefficients between **log(CV)** and dataset properties (log(n_samples), log(n_features)) as the primary analysis.
 - **Input**: Must consume aggregated data. **Must filter out rows where CV=0** before calculating log(CV) to prevent undefined operations.
 - **Primary Output**: Pearson r and p-value on log(CV) vs log(N).
 - **Secondary**: Compute Spearman rho for robustness check.
 - **Output**: Append results to `results/correlation_results.csv` with `metric_type='LogCV'`.
 - **Constraint**: This is the **primary** analysis for SC-001 and SC-002. **Note**: Direct Pearson on raw CV (T019a) is rejected by the Plan as tautological and is not implemented.
 - **Additional Output**: Must also calculate and output regression coefficients (slope, intercept) for the log-log fit to `results/regression_coefficients.csv`.
- [X] T020 [US2] **SECONDARY**: Compute **Theoretical Deviation** and residuals from log-log linear regression of **log(CV)** against log(n_samples) and log(n_features).
 - **Input**: Must consume regression coefficients (slope, intercept) from T019b output (`results/regression_coefficients.csv`).
 - **Formula**: Calculate deviation as `log(CV) - (slope * log(N) + intercept)`. Uses the fitted slope from T019b, not a hardcoded -0.5.
 - **Output Artifact**: Write residuals and deviation metrics to `results/theoretical_deviation.csv`.
 - **Dependency**: Must wait for T019b.
- [X] T021 [US2] **Write Raw Tables**: Write raw, uncorrected summary tables to `results/stability_metrics.csv` and `results/correlation_results_raw.csv`.
 - **Schema `stability_metrics.csv`**: `dataset_id` (int), `model_name` (str), `mean_accuracy` (float), `cv_accuracy` (float), `mean_f1` (float), `cv_f1` (float), `log_cv_accuracy` (float).
 - **Schema `correlation_results_raw.csv`**: `dataset_id` (int), `model_name` (str), `metric_type` (str: 'CV', 'LogCV'), `pearson_r` (float), `pearson_p_value` (float), `spearman_rho` (float), `spearman_p_value` (float), `feature_count` (int), `sample_size` (int), `adj_p_value_holm` (float, **must be null** for this raw output), `significant_holm` (bool, **must be false** for this raw output).
 - **Primary Constraint**: `pearson_r` and `pearson_p_value` for `metric_type='CV'` and `metric_type='LogCV'` must be populated.
 - **Implementation Logic**:
 1. Read `results/raw_evaluations.csv` and aggregate to compute stability metrics (mean, std, cv, log(CV)) per (dataset, model).
 2. Write aggregated metrics to `results/stability_metrics.csv`.
 3. Read `results/correlation_results.csv` (populated by T019b) and write **raw, uncorrected** results to `results/correlation_results_raw.csv` with adjusted p-values set to `null`.
 4. Ensure all required columns are populated from upstream tasks.
 - **Dependency**: Must wait for T018a, T018b, T019b. **Note**: This writes to a RAW file to avoid overwriting T019b's output. **Correction**: T021 does NOT depend on T020.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Raw Output)

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
 - **Algorithm**: **Block Permutation**: Permute entire repeat indices as blocks

The research question, method, and references remain unchanged as required., keeping fold indices within repeats intact. This preserves the dependence structure of repeated CV scores.
 - **Logic**: Generate results for **all three pairwise combinations** (LR vs RF, RF vs SVM, LR vs SVM) for each dataset.
 - **Output**: Write raw p-values for each model pair per dataset to `results/permutation_results_raw.csv` (raw).
- [X] T026a [US2/US3] **Define Correction Families**: Explicitly define and document the two distinct statistical families for multiple comparison correction.
 - **Input**: Must consume `results/correlation_results_raw.csv` (raw, from T021) and `results/permutation_results_raw.csv` (raw, from T025).
 - **Logic**:
 1. **Family 1 (Correlation)**: All p-values from `results/correlation_results_raw.csv` (metric_type='CV' and 'LogCV').
 2. **Family 2 (Permutation)**: All p-values from `results/permutation_results_raw.csv`.
 - **Output**: Write `results/correction_families.json` containing the list of p-values for each family and their metadata (source file, metric type). **Schema**: `{"family_correlation": {"p_values": [...], "metadata": {...}}, "family_permutation": {"p_values": [...], "metadata": {...}}}`.
 - **Constraint**: This task **defines** the families before correction is applied.
- [X] T026b [US2/US3] **Apply Multiple Comparison Correction** and **Finalize** globally across the set of ALL hypothesis tests, respecting the families defined in T026a.
 - **Input**: Must consume `results/correction_families.json` (from T026a).
 - **Scope**: Apply Holm-Bonferroni correction **separately** to Family 1 (Correlation) and Family 2 (Permutation) to avoid over-correction across distinct statistical questions (FR-007).
 - **Method (FWER)**: Implement **Holm-Bonferroni** procedure (step-down) for each family.
 - **Action**: Apply correction to each family independently.
 - **Output**:
 1. Append/Update `results/correlation_results.csv` with columns `adj_p_value_holm` and `significant_holm` (overwriting nulls from T021).
 2. Append/Update `results/permutation_results.csv` with columns `adj_p_value_holm` and `significant_holm`.
 3. **Finalize and Write** the final `results/permutation_results.csv` and `results/correlation_results.csv` with the complete schema including adjusted p-values.
 - **Constraint**: Must explicitly report Holm-Bonferroni adjusted p-values and ensure the final files contain the corrected values. **This is the final writer** for corrected artifacts.
- [X] T026c [US2/US3] **Validate Correction Strategy**: Document and verify that the two-family correction strategy satisfies FR-007 and the Plan's "ALL tests" requirement.
 - **Action**: Write a section in `docs/report_template.md` or `research.md` explaining that the union of the two corrected sets controls the global Family-Wise Error Rate (FWER) at the target alpha level, satisfying the requirement to correct "the set of ALL hypothesis tests".
 - **Output**: Updated documentation in `docs/report_template.md`.
- [X] T028a [US3] Implement report generator aggregation logic in `code/report_generator.py` to aggregate `results/stability_metrics.csv`, `results/correlation_results.csv` (final, from T026b), and `results/permutation_results.csv` (final, from T026b).
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
- [X] T029b Update `specs/001-assessing-the-stability-of-statistical-m/quickstart.md` with dataset list.
 - **Content**: List all A set of datasets with their OpenML/UCI IDs and brief descriptions. **Dependency**: Must wait for T005/T005b to produce the final dataset list.
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

- [X] T036a [P] **CI Timeout Configuration**: Update `.github/workflows/ci.yml` to include a `timeout-minutes` directive with a sufficiently large value to accommodate the full evaluation job. (Addresses Plan T008 & Edge Case: Network/Timeout failure). **Traceability**: Required by FR-006 ("execute on GitHub Actions runner").
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

- [X] T050a **Create Smoke Test Script**: Create `scripts/run_smoke_test.py` to orchestrate a full pipeline run on exactly 3 datasets (one from each size bin: <1k, 1k-10k, >10k). **Hardcoded IDs**: Use OpenML ID (iris), ID 14 (heart-statlog), and ID 1461 (credit-a) as the specific fixtures.
 - **Action**: Write script that downloads, evaluates, analyzes, and reports.
 - **Dependency**: T005, T005c, T011, T019b, T025.
- [X] T050b [P] **Execute Smoke Test**: Run `scripts/run_smoke_test.py` and verify it completes without errors.
 - **Action**: Execute the script and capture logs.
 - **Dependency**: T050a.
- [X] T050c [P] **Validate Smoke Test Results**: Verify that `results/raw_evaluations.csv`, `results/stability_metrics.csv`, `results/correlation_results.csv`, `results/permutation_results.csv`, and `results/final_report.md` are all generated and contain valid data.
 - **Validation Logic**:
 1. Verify no NaN values in critical columns.
 2. Verify row count in `results/raw_evaluations.csv` matches `num_selected_datasets * 3 models * 100 repeats`. **Explicitly allow count < 4500 if datasets were skipped** (e.g., due to network errors or <100 samples).
 3. Verify all selected dataset IDs are present.
 - **Dependency**: T050b.
- [X] T051a [P] **Instrument Pipeline for Profiling**: Add memory profiling decorators around `code/evaluator.py` and `code/analyser.py` functions.
 - **Tool**: Use `memory_profiler` or `tracemalloc`.
 - **Action**: Insert decorators to log peak RSS.
 - **Dependency**: T050a.
- [ ] T051b [P] **Run Resource Usage Audit**: Execute the smoke test (T050b) with profiling enabled and log peak RSS memory usage to `results/memory_profile.log`.
 - **Goal**: Confirm peak memory usage remains < 6GB with a safety margin for the 7GB limit.
 - **Dependency**: T051a, T050b.
- [ ] T052a [P] **Create Determinism Script**: Create `scripts/verify_determinism.py` that runs the pipeline twice, computes SHA-256 hashes of all result files, and asserts equality. **Constraint**: Must use `SEED=42` for both runs.
 - **Action**: Write script to orchestrate two runs and compare hashes.
 - **Dependency**: T050a.
- [ ] T052b [P] **Execute Determinism Verification**: Run the smoke test (T050b) twice with the same seed (`SEED=42` passed as environment variable) and verify that the checksums of all output CSVs and the final report are identical.
 - **Goal**: Confirm that random seed pinning in `code/utils.py` is effective across all components.
 - **Dependency**: T052a, T050b.
- [ ] T053 [P] **CI Workflow Finalization**: Update `.github/workflows/ci.yml` to trigger the full pipeline (15 datasets) only on manual dispatch or specific branch pushes, ensuring the 6-hour timeout and signal handling are active. **Traceability**: Required by FR-006 ("execute on GitHub Actions runner").
 - **Action**: Add a `workflow_dispatch` trigger and configure the `evaluation` job to use the `signal_handler` from T036b.
 - **Goal**: Ensure the CI environment is correctly configured for the long-running job.

---

## Phase AA: Execution Readiness & Safety Hardening

**Purpose**: Final checks to ensure the pipeline is robust against network failures, dataset unavailability, and resource exhaustion before the full 15-dataset run.

- [ ] T054 [P] **Robust Data Fetch Retry Logic**: Update `code/data_loader.py` to implement exponential backoff retry logic for network failures during dataset download.
 - **Location**: `code/data_loader.py` -> `fetch_dataset` function.
 - **Logic**: On `requests.exceptions.RequestException`, retry up to 3 times with delays of 1s, 2s, 4s. If all retries fail, log error and skip dataset (do not crash).
 - **Constraint**: Must NOT fall back to synthetic data. Must fail loudly if the real source is unreachable after retries.
- [ ] T055 [P] **Dataset Availability Pre-Check**: Implement a pre-flight check script `scripts/check_dataset_availability.py` that attempts to fetch headers/metadata for all 15 selected datasets before the main run.
 - **Action**: Run this script in CI before triggering the full evaluation job.
 - **Goal**: Identify and skip unavailable datasets early to prevent long-running jobs from failing halfway.
 - **Output**: Generate `data/available_datasets.json` with a list of verified dataset IDs.
- [ ] T056 [P] **Memory Safety Guardrails**: Add explicit memory usage checks in `code/evaluator.py` before loading each dataset.
 - **Location**: `code/evaluator.py` -> `evaluate_model` function.
 - **Logic**: Use `psutil` to check available memory. If available memory < 1GB, log a warning and skip the dataset to prevent OOM crashes.
 - **Constraint**: Must log the specific dataset ID and available memory before skipping.
- [ ] T057 [P] **Partial Results Recovery**: Enhance `code/main.py` signal handler (T036b) to support resuming from the last completed dataset if the run is interrupted.
 - **Logic**: Check for a `results/last_completed_dataset.txt` file. If present, skip already processed datasets and resume from the next one.
 - **Goal**: Maximize progress in case of CI timeouts or interruptions.
- [ ] T058 [P] **Final Sanity Check**: Run a quick sanity check on the `results/raw_evaluations.csv` schema and content after T050.
 - **Script**: Create `scripts/sanity_check_results.py`.
 - **Checks**: Verify no NaN values in critical columns, verify row counts match expectations (dynamic formula: num_selected * 3 * 100), verify all dataset IDs are present.
 - **Goal**: Catch data corruption or logic errors before the final report generation.

---

## Phase BB: Final Execution Validation & Reporting

**Purpose**: Execute the full pipeline on the selected 15 datasets and generate the final research report.

- [ ] T059 [P] **Execute Full Pipeline**: Trigger the full evaluation job on GitHub Actions using the `workflow_dispatch` trigger configured in T053.
 - **Action**: Manually trigger the workflow with the `selected_ids` from `data/spectrum_report.json`.
 - **Goal**: Complete the full 15-dataset evaluation within the 6-hour timeout.
 - **Dependency**: T053, T054, T055.
- [ ] T060 [P] **Validate Full Pipeline Outputs**: Verify that all expected output files are generated and contain valid data after the full run.
 - **Validation Logic**:
 1. Verify `results/raw_evaluations.csv` has the expected number of rows (15 datasets * 3 models * 100 repeats = 4500, minus any skipped datasets).
 2. Verify `results/stability_metrics.csv` has entries for all processed (dataset, model) pairs.
 3. Verify `results/correlation_results.csv` and `results/permutation_results.csv` contain adjusted p-values.
 4. Verify `results/final_report.md` is generated and contains all required sections.
 - **Dependency**: T059.
- [ ] T061 [P] **Generate Final Research Report**: Execute `code/report_generator.py` to produce the final `results/final_report.md` if not already generated by T028c.
 - **Action**: Run the report generator with the final results.
 - **Goal**: Produce a comprehensive report summarizing the stability analysis.
 - **Dependency**: T060.
- [ ] T062 [P] **Archive Results**: Archive all result files (`results/` directory) and `data/spectrum_report.json` as a release artifact.
 - **Action**: Create a GitHub release or archive the results directory.
 - **Goal**: Ensure reproducibility and long-term storage of the research findings.
 - **Dependency**: T061.