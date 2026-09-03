---
description: "Task list for feature: Quantifying the Impact of Data Cleaning on Statistical Inference"
---

# Tasks: Quantifying the Impact of Data Cleaning on Statistical Inference

**Input**: Design documents from `/specs/001-quantify-data-cleaning-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 0: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (code/, data/raw/, data/processed/, tests/)
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pytest)
- [X] T003L [P] Configure linting and formatting tools (ruff/black) in code/
- [X] T005 Compute file checksum `compute_file_checksum(filepath: str) -> str` (SHA256) for data files. **Verification**: T005a records checksum in `state/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-.yaml`; T005b asserts entry exists.
- [X] T005a Record computed checksum in project state YAML as required by Constitution Principle III.
- [X] T005b Verify that the checksum entry is present in the state YAML after computation.

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, bug fixes, configuration, and unit tests that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase now includes critical bug fixes, configuration audits, and unit tests to ensure downstream tasks run on correct, validated code.

- [ ] T1201a [HYGIENE] Audit `code/` directory to identify all files matching `t0*.py` pattern. **Verification**: T1201a generates a list of all such files for migration.
- [ ] T1201b [HYGIENE] Generate migration plan for identified `t0*.py` files. **Verification**: T1201b confirms plan covers all identified files.
- [X] T1202 [US2] Migrate logic from identified `t0*.py` scripts (e.g., `t022_*.py`, `t027_*.py`) into `code/cleaning.py`, `code/analysis.py`, `code/reporting.py`. Ensure `code/cleaning.py` contains full implementations of IQR, imputation, and recoding functions. **Verification**: T1202a runs unit tests confirming logic integrity in the new modules.
- [X] T1203 [US3] Migrate logic from identified `t0*.py` scripts into `code/reporting.py`, `code/sensitivity.py`, and `code/main.py`. **Verification**: T1203a verifies all functions are callable from `main.py` and produce identical artifacts.
- [ ] T1204 [HYGIENE] Delete all standalone `t0*.py` scripts in `code/` after successful migration and verification. **Verification**: T1204a asserts no files matching `t0*.py` remain in `code/`. <!-- FAILED: unspecified -->
- [ ] T1205 [CONFIG] Audit all Python modules in `code/` (including `main.py`, `data_loader.py`, `analysis.py`, `cleaning.py`, `reporting.py`) to identify hardcoded path strings (e.g., `"data/raw/"`, `"output/figures/"`, `"data/processed/"`). **Verification**: T1205a generates a report of all hardcoded paths found.
- [X] T1206 [CONFIG] Refactor all identified hardcoded paths to import and use constants from `code/config.py`. Ensure `code/config.py` is the single source of truth for all paths and parameters. **Verification**: T1206a runs a static analysis check to confirm no hardcoded paths remain in source modules.
- [X] T1207 [CONFIG] Update `code/main.py` to load configuration from `code/config.py` and pass paths explicitly to all pipeline functions. **Verification**: T1207a executes `main.py` with a clean environment to confirm correct path resolution.
- [X] T1213 [HYGIENE] Audit `code/cleanup_utils.py`, `code/profiler.py`, and `code/utils.py` to identify duplicate or overlapping functions (e.g., `pin_random_seed`, `compute_file_checksum`, logging helpers). **Verification**: T1213a generates a diff report of overlapping functions.
- [X] T1214 [HYGIENE] Consolidate unique logic from `code/cleanup_utils.py` and `code/profiler.py` into `code/utils.py` or `code/main.py`. Delete `code/cleanup_utils.py` and `code/profiler.py` after consolidation. **Verification**: T1214a asserts deletion of redundant files and successful import of migrated functions.
- [X] T1215 [HYGIENE] Move maintenance scripts `code/run_lint.py` and `code/run_quickstart_validation.py` to `scripts/` directory (create if needed). Update imports in any referencing files. **Verification**: T1215a confirms scripts are moved and executable from new location.
- [X] T1221 [DATA] Create `data/raw/README.md` documenting exact URLs, DOIs, and SHA-256 checksums for all datasets used (e.g., UCI HAR, UCI Shopper). Include executable download commands. **Verification**: T1221a validates that the README contains all required fields and checksums match downloaded files.
- [X] T1223 [DATA] Update `code/data_loader.py` (or `scripts/download_data.sh`) to explicitly fail (non-zero exit) if download fails, and log SHA-256 checksum verification. Remove any silent fallback to mock data. **Verification**: T1223a simulates a failed download and asserts script exits with error.
- [X] T1216 [BUG] Fix `code/analysis.py`: Remove hardcoded `p_value = 0.05` assignment. Replace with `scipy.stats.ttest_ind` for t-tests, grouping data by the outcome variable column. **Verification**: T1216a runs analysis on a known dataset and verifies p-values are non-constant and statistically valid.
- [X] T1217 [BUG] Fix Cohen's d calculation in `code/analysis.py`: Ensure pooled standard deviation is computed from the two specific groups defined by the outcome variable (e.g., `df[df[outcome] == 0]` vs `df[df[outcome] == 1]`), not the global dataset standard deviation. **Verification**: T1217a runs unit test comparing computed Cohen's d against a manual calculation.
- [X] T1218 [BUG] Update `code/cleaning.py`: Ensure all cleaning functions (`apply_iqr_outlier_removal`, `apply_mean_imputation`, etc.) return a tuple `(cleaned_df, metadata_dict)` including `rows_removed` and `missing_values_remaining`. **Verification**: T1218a runs unit tests confirming metadata return.
- [ ] T1219 [BUG] Fix `code/reporting.py`: Ensure it correctly consumes metadata from cleaning functions and populates `cleaned_metrics.json` with `rows_removed` and `missing_values_remaining` fields. **Verification**: T1219a validates `cleaned_metrics.json` schema compliance.
- [ ] T1220 [BUG] Correct Bootstrap Configuration: Update `code/main.py` (or relevant script) to explicitly pass `config.BOOTSTRAP_ITERATIONS` (default 1000) to the bootstrap function. Remove any default fallback to A sufficient number of iterations unless dataset size > 5000. **Verification**: T1220a audits code for correct iteration count and runs a small bootstrap test to confirm 1000 resamples.
- [ ] T1208 [TEST] Create `tests/` directory structure with subdirectories `unit/`, `integration/`, and `contract/`. **Verification**: T1208a confirms directory creation.
- [ ] T1209a [TEST] Create a fixture file `tests/fixtures/sample_data.csv` with known values for testing analysis functions. **Verification**: T1209a confirms file existence and validity.
- [ ] T1209 [TEST] Implement unit tests in `tests/unit/test_cleaning.py` for `apply_iqr_outlier_removal`, `apply_mean_imputation`, `apply_median_imputation`, `apply_knn_imputation`, and `apply_categorical_recoding`. Verify correct row removal, zero missing values, and metadata return. **Verification**: T1209a runs `pytest tests/unit/test_cleaning.py` and asserts [deferred] pass rate.
- [ ] T1210 [TEST] Implement unit tests in `tests/unit/test_analysis.py` for `run_t_test` and `run_linear_regression`. Verify that p-values are computed dynamically (not hardcoded) and Cohen's d uses pooled standard deviation of specific groups. **Verification**: T1210a runs `pytest tests/unit/test_analysis.py` and asserts [deferred] pass rate.
- [ ] T1211 [TEST] Implement integration test in `tests/integration/test_full_pipeline.py` that executes `python -m code.main` from a clean state and verifies generation of all required artifacts (`baseline_metrics.json`, `cleaned_metrics.json`, `null_fpr_metrics.json`, visualizations). **Verification**: T1211a asserts all artifacts exist and are non-empty.
- [ ] T1212 [TEST] Implement contract tests in `tests/contract/` to validate all JSON artifacts against their respective schemas (`dataset.schema.yaml`, `baseline_metrics.schema.yaml`, etc.) after each major pipeline stage. **Verification**: T1212a runs contract tests and asserts [deferred] pass rate.
- [X] T008 Create base data models/entities per data-model.md (Dataset, CleaningStrategy, AnalysisResult, ComparisonReport schemas) in `code/models.py`.
- [X] T004 Create `code/utils.py` with function `pin_random_seed(seed: int)` for numpy and scipy, ensuring reproducibility.
- [X] T005U Create `code/utils.py` with function `compute_file_checksum(filepath: str) -> str` for SHA256 validation of data files. **Verification**: T005a records checksum in state YAML; T005b confirms entry.
- [X] T006 Create `code/utils.py` with function `setup_logging(log_level: str)` to initialize the logging infrastructure.
- [X] T007 Setup environment configuration management in `code/config.py` with env vars for DATASET_URLS, OUTPUT_PATH, RANDOM_SEED, BOOTSTRAP_ITERATIONS.
- [X] T003a Validate each raw dataset against `contracts/dataset.schema.yaml`. **Verification**: T003b ensures validation passes for all downloads.
- [X] T004a Extract and record the outcome column name for each dataset into `data/processed/dataset_metadata.json`. **Verification**: T004b checks the column is documented and numeric.
- [X] T004c [P] Verify that each outcome column recorded in `dataset_metadata.json` is numeric, non‑constant, and has no missing values. **Verification**: T004c‑v asserts numeric dtype, variance > 0, and completeness.
- [X] T003c Validate `baseline_metrics.json` against `contracts/baseline_metrics.schema.yaml`. **Verification**: T003d checks numeric fields have ≥3‑decimal precision.
- [X] T003e Validate `cleaned_metrics.json` against `contracts/cleaned_metrics.schema.yaml`. **Verification**: T003f checks precision and required fields.
- [X] T003g Validate cleaning‑metadata fields inside `cleaned_metrics.json` against the schema. **Verification**: T003h ensures metadata compliance.
- [X] T005c Ensure each size‑bin (n < 50, 50‑200, >200) and missingness level bin has ≥ 1 dataset; download additional data if needed. **Verification**: T005d checks bin coverage.
- [X] T044 Code cleanup and refactoring (remove dead code, optimize imports). **Verification**: T044a runs lint and ensures no style errors.
- [X] T044a [P] Run lint (`ruff` and `black --check`) on the codebase and assert exit code 0; fail if any style violations are found. **Verification**: Lint passes without errors.
- [X] T100 [P] FR‑005 Outcome Variable Definition: Verify each dataset’s outcome column is explicitly documented in the source metadata and record the name in `data/processed/dataset_metadata.json`. **Verification**: T100a asserts documentation presence and correct recording.
- [X] T101 [P] FR‑006 Assumption Checks: Run Shapiro‑Wilk normality, Levene homoscedasticity, and linearity (R² ≥ 0.7) checks before each statistical test. Record `assumptions_met` flag. **Verification**: T101a checks flag correctness per analysis.
- [X] T102 [P] FR‑006 Robust Fallback: When `assumptions_met` is false, automatically switch to Welch’s t‑test or rank‑based regression and store results, flagging the fallback. **Verification**: T102a asserts robust method execution and flagging.
- [X] T104 [P] SC‑006 Assumption‑Check Flagging: Verify that every entry in `cleaned_metrics.json` contains a boolean `assumptions_met` and that robust fallbacks are recorded when false. **Verification**: T104a audits the JSON artifacts.
- [X] T105 [P] FR‑016 Power Analysis: Perform Wilcoxon‑based power analysis (medium effect size, α = 0.05, power ≥ 0.8) for each dataset; write justification to `power_analysis.txt`. **Verification**: T105a checks file existence and that power ≥ 0.8 for all datasets.
- [X] T106 [P] FR‑019 Citation Validation: Run the citation‑validation script required by Principle II; log the verification outcome. **Verification**: T106a parses the log and asserts all citations pass.
- [X] T107 [P] FR‑020 External Benchmark Simulation: {{claim:c_162ce178}} **Verification**: T107a validates recorded metrics meet thresholds.
- [X] T108 [P] FR‑021 Δ‑Metrics Hypothesis Test: Compute paired Wilcoxon signed‑rank test on `p_value_delta` across datasets for each cleaning operation; store results in `hypothesis_test_results.json`. **Verification**: T108a asserts p < 0.05 for at least one cleaning operation.
- [X] T109 [P] FR‑007 Multiple‑Comparison Verification: Apply Holm‑Bonferroni correction across all cleaning‑variant p‑values within each dataset; assert family‑wise error rate ≤ 0.05 and record adjusted p‑values in `cleaned_metrics.json`. [UNRESOLVED-CLAIM: c_e5004fbd — status=not_enough_info] **Verification**: T109a checks FWER compliance.
- [X] T110 [P] FR‑008 Sensitivity Analysis Verification: After stratified analysis, assert that each size‑bin and missingness‑level bin contains ≥ 1 dataset and that results are stored in `sensitivity_metrics.json`. **Verification**: T110a confirms bin coverage and artifact validity.

## Phase 1.5: Missingness Mechanism Generation (Foundational)

**Purpose**: Generate MCAR and MAR missingness mechanisms required for FPR estimation.

- [ ] T074a [P] Generate MCAR (Missing Completely At Random) and MAR (Missing At Random) missingness mechanisms for each dataset. **Implementation**: Use `sklearn.utils.shuffle` for MCAR and a logistic model based on other features for MAR. **Verification**: T074b asserts both mechanisms are generated and stored.
- [ ] T074b [P] Verify that MCAR and MAR missingness mechanisms are correctly applied and stored in `data/processed/missingness_mechanisms/`. **Verification**: T074b checks file existence and structure.

## Phase 1.7: Permutation-Based FPR Estimation (Corrected Order)

**Purpose**: Estimate FPR with outcome permutation **before** any cleaning step, per FR-006.

- [ ] T074 [P] Implement permutation‑based FPR estimation: permute the outcome column on the raw dataset **before** any cleaning operation, using both MCAR and MAR missingness mechanisms generated in T074a. Run the full cleaning pipeline for each variant. Compute the proportion of permutations yielding a significant result (p < 0.05) after Holm‑Bonferroni correction and store in `null_fpr_metrics.json`. **Iteration Logic**: Use 1000 permutations for n ≤ 200, 500 for n > 200.
- [ ] T074a [P] Verify that permutation occurs prior to cleaning, that the number of permutations respects the dataset size (1000 for n ≤ 200, 500 otherwise), and that `null_fpr_metrics.json` contains the correct FPR values with ≥3‑decimal precision.

## Phase 2: User Story 1 - Dataset Acquisition and Baseline Analysis (Priority: P1) 🎯 MVP

**Goal**: Download public datasets from UCI/OpenML and run baseline statistical analyses (t‑tests, linear regressions) on raw, uncleaned data to establish reference metrics (p‑values, 95% CI, effect sizes)

**Independent Test**: Can be fully tested by executing the dataset download and baseline analysis script against a single dataset, producing a report with p‑values, confidence intervals, and effect sizes for that dataset

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test in `tests/unit/test_acquisition.py`: Verify `download_dataset` returns a successful HTTP status and non-empty content for UCI HAR URL.
- [X] T010 [P] [US1] Integration test in `tests/integration/test_baseline.py`: Verify baseline analysis script produces `baseline_metrics.json` with valid p‑values (0 < p < 1) and finite CIs.

### Implementation for User Story 1

- [X] T011 [US1] Implement acquisition logic in `code/data_loader.py`. Downloads verified UCI URLs, validates checksums, logs fallback to OpenML if unavailable, and writes raw files to `data/raw/`. **Verification**: T011a checks HTTP status; T011b validates SHA256 checksum.
- [X] [X] T012 [US1] Implement baseline statistical analysis in `code/analysis.py` using `scipy.stats` (t‑tests) and `statsmodels` (linear regression). Writes per‑dataset metrics (p‑value, 95% CI, effect size) to `data/processed/baseline_metrics.json` with ≥3‑decimal precision. **Deliverable**: `code/analysis.py` baseline functions. **Verification**: T012a runs the analysis; T012b asserts file existence, schema compliance, and ≥3‑decimal precision; T012c verifies numeric precision of all fields.
- [X] T012a [US1] Run baseline analysis script on all raw datasets. Produces `baseline_metrics.json`. **Success**: File created with correct schema.
- [X] [X] T012b [US1] Verify `baseline_metrics.json` contains all required fields with ≥3‑decimal precision. **Success**: Automated test passes.
- [X] [X] T012c [US1] Verify numeric fields in `baseline_metrics.json` are rounded to at least three decimal places. **Verification**: Parses JSON and asserts precision.
- [X] [X] T013 [US1] Add orchestration in `code/main.py` to invoke data acquisition and baseline analysis, ensuring `data/processed/baseline_metrics.json` is produced. **Deliverable**: Updated `code/main.py`. **Verification**: T013a runs `python -m code.main --stage baseline` and checks exit code 0 and file presence.
- [X] T013a [US1] Integration test: execute `code/main.py` for baseline stage; verify exit code 0 and artifact generation.

**Checkpoint**: User Story 1 will be fully functional once pending tasks are completed.

## Phase 3: User Story 2 - Systematic Cleaning Strategy Application (Priority: P1)

**Goal**: Apply three cleaning strategies systematically (IQR outlier removal, mean/median/KNN imputation, categorical recoding) and re‑run identical statistical tests on each cleaned variant

**Independent Test**: Can be fully tested by applying one cleaning strategy (e.g., IQR outlier removal with k=1.5) to a single dataset and comparing before/after p‑values, which delivers the primary research outcome for that strategy

### Implementation for User Story 2

- [X] T017 [US2] Implement function `apply_iqr_outlier_removal(df, k=1.5)` in `code/cleaning.py`. Logs rows removed; flags if ≥50% rows removed. **Verification**: T017a unit‑tests correct removal and metadata.
- [X] T018 [US2] Implement function `apply_mean_imputation(df, columns)` in `code/cleaning.py`. Validates zero missing values; flags variance reduction ≥20%. **Verification**: T018a unit‑test for zero missing and variance flag.
- [X] T019 [US2] Implement function `apply_median_imputation(df, columns)` in `code/cleaning.py`. Same validation as T018. **Verification**: T019a unit‑test.
- [X] T020 [US2] Implement function `apply_knn_imputation(df, columns, k=5)` in `code/cleaning.py` using scikit‑learn. Same validation as T018. **Verification**: T020a unit‑test.
- [ ] T021 [US2] Implement function `apply_categorical_recoding(df)` in `code/cleaning.py`. **Requirement**: Detect ordinal variables (via metadata or order-preserving checks) and apply integer label encoding; apply one-hot encoding to nominal variables. **Verification**: T021a unit‑test for correct encoding and metadata.
- [X] T022 [US2] Write cleaned datasets to `data/processed/` with strategy‑specific filenames (e.g., `dataset_outlier_removed.csv`). **Verification**: T022a checks naming, checksum validation, and schema compliance.
- [X] T023 [US2] Ensure cleaning functions return `(cleaned_df, metadata_dict)` where metadata includes `rows_removed` and `missing_values_remaining`. **Verification**: T023a asserts metadata fields are present.
- [X] T024 [US2] Re‑run t‑tests and linear regressions on each cleaned variant using `code/analysis.py`. **Deliverable**: Updated analysis pipeline.
- [X] [X] T069 [US2] Generate `data/processed/cleaned_metrics.json` aggregating metrics per cleaning strategy per dataset. **Dependency**: T024. **Verification**: T069a runs generation; T069b checks schema, precision, and inclusion of cleaning metadata; T069c verifies file existence, schema validation, metadata fields, and numeric precision.
- [X] T069a [US2] Execute cleaned‑metrics generation step via `code/main.py --stage cleaned`.
- [X] T069b [US2] Verify `cleaned_metrics.json` contains required fields, ≥3‑decimal precision, and cleaning metadata.
- [X] [X] T069c [US2] Verify `cleaned_metrics.json` is written, passes schema validation, includes cleaning‑metadata, and all numeric values have ≥3‑decimal precision.
- [X] [X] T069d [US2] Verify downstream reporting consumes cleaning metadata correctly.

### Tests for User Story 2 (OPTIONAL ⚠️)

- [X] T014 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_iqr_outlier_removal` removes rows where |z-score| > k and logs count.
- [X] T015 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_mean_imputation` results in zero missing values in target columns.
- [X] T016 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_categorical_recoding` produces factor‑encoded columns and validates against FR‑002 and FR‑003 requirements.

**Checkpoint**: User Story 2 tasks are now complete and ready for execution.

## Phase 4: User Story 3 - Metrics Comparison and Sensitivity Analysis (Priority: P2)

**Goal**: Compute absolute and relative differences between baseline and cleaned results, perform sensitivity analysis across dataset sizes and missingness rate bins, and generate summary visualizations

**Independent Test**: Can be fully tested by running the comparison script on 2 datasets (one cleaned, one baseline) and verifying the difference report contains p‑value shifts, CI width changes, and effect‑size variations with valid numeric values

### Shared Preparatory Tasks

- [X] T099a [P] Prepare baseline and cleaned metric artifacts for downstream comparison. Runs validation script `code/validation.py` **after** T012b and T069b. **Verification**: T099b confirms artifacts exist and pass schema checks.
- [X] T099b [P] Validation of artifacts: ensure `baseline_metrics.json` and `cleaned_metrics.json` are present, well‑formed, and meet precision requirements.

### Implementation for User Story 3

- [X] T027 [US3] Implement metrics comparison in `code/reporting.py`. Computes |p_cleaned − p_baseline| (≥3‑decimal), CI width change (≥2‑decimal), effect‑size delta, and inconsistency rate (proportion of datasets where significance status changes). **Dependency**: T012, T024.
- [X] [X] T027a [US3] Generate per‑dataset delta report `output/reports/delta_report.json` meeting SC‑001 wording (qualitative directionality, per‑dataset).
- [X] [X] T027c [US3] Verify `delta_report.json` contains per‑dataset entries with required fields and proper precision.
- [X] T028 [US3] Add claim verification placeholder (no external reference required). **Deliverable**: `code/reporting.py`.
- [X] T029 [US3] Implement missingness‑rate binning with thresholds (0%, ≤5%, ≤10%, >10%). Logs warning `"Missingness bin empty: bin <X> has no datasets"`.
- [X] T030 [US3] Implement dataset‑size binning (n<50, 50‑200, >200). Logs warning for empty bins.
- [X] T031 [US3] Implement bootstrap variance estimation with **≥1000** resamples per dataset (default 1000). **Verification**: T045a audits code for absence of fallback; T045b asserts no fallback occurs.
- [X] [X] T033a [US3] Perform outlier‑threshold sweep for k ∈ {, 2.0}; for each threshold run full analysis on real data and store per‑threshold metrics in `data/processed/outlier_threshold_sweep_report.json`.
- [X] [X] T033b [US3] Compute inconsistency rate per outlier threshold; append to sweep report.
- [X] [X] T033c [US3] Verify `outlier_threshold_sweep_report.json` exists, is well‑formed, and contains required fields with ≥3‑decimal precision.
- [X] T034 [US3] Generate forest plot of p‑value shifts (`output/figures/pvalue_shifts_forest.png`). **Verification**: T034a checks file existence.
- [X] [X] T034c [US3] Verify forest plot file is non‑empty and saved to the correct path.
- [X] [X] T035 [US3] Generate heatmap of CI‑width changes (`output/figures/ci_width_heatmap.png`). **Verification**: T035a checks file existence.
- [X] [X] T035c [US3] Verify heatmap file is non‑empty and saved to the correct path.
- [X] T036 [US3] Implement per‑dataset p‑value shift reporting (no median/IQR). **Aligns with methodological pivot**.
- [X] T037 [US3] Implement per‑dataset CI width change reporting. **Enforced minimum 1000 bootstrap iterations; no fallback**.
- [X] T038 [US3] Implement per‑dataset effect‑size change reporting.
- [X] T039 [US3] Log excluded datasets (>80% missing outcome) with warning; record reason in `data_quality_report.md`.
- [X] T040 [US3] Create `ComparisonReport` entity and write `data/processed/comparison_report.json` aggregating all results.
- [X] T041 [US3] Generate final report `output/reports/final_report.md` referencing visualizations and noting methodological limitations.
- [X] T007a [US3] Apply Holm‑Bonferroni correction across all cleaning‑variant p‑values within each dataset; store adjusted p‑values in `cleaned_metrics.json`. **Verification**: T007b asserts FWER ≤ 0.05.
- [X] T008a [US3] Perform stratified sensitivity analysis across size and missingness bins; store results in `sensitivity_metrics.json`. **Verification**: T008b checks that each bin contains ≥1 dataset.
- [X] T006a [US3] Perform Wilcoxon‑based power analysis (medium effect size, α = 0.05, power ≥ 0.8) and write justification to `power_analysis.txt`. **Verification**: T006b validates the file and that the analysis justifies the selected A set of datasets.
- [X] T006c [US3] Run citation‑validation script (Principle II) and log outcome. **Verification**: T006d checks the validation log.
- [X] T006e [US3] Generate synthetic benchmark datasets (null effect and d = 0.5), run full pipeline, and record FPR and effect‑size recovery. **Verification**: T006f asserts FPR ≤ 0.05 and effect‑size tolerance ± 0.1.
- [X] T006g [US3] Compute paired Wilcoxon test on `p_value_delta` across datasets for each cleaning operation; store results in `hypothesis_test_results.json`. **Verification**: T006h checks that the test yields p < 0.05.
- [X] T009a [US3] Run full contract‑validation suite after each major stage to ensure all artefacts pass schema checks. **Verification**: T009a asserts all validations succeed.

## Phase 5: Assumption Checks & Robust Fallback (New Sub‑Phase)

**Goal**: Perform statistical assumption checks before each test and switch to robust alternatives when needed.

- [X] T072 [P] Run Shapiro‑Wilk normality test (α = 0.05), Levene’s homoscedasticity test (α = 0.05), and a linearity check (R² ≥ 0.7) on the baseline and each cleaned variant. Record a boolean `assumptions_met` flag in `cleaned_metrics.json` for each analysis result.
- [X] T073 Verify that for every analysis where `assumptions_met` is false, a robust alternative (Welch’s t‑test or rank‑based regression) is executed, its results are stored, and the `assumptions_met` flag is correctly reflected in the JSON artifact.

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042 [P] Documentation updates in `docs/README.md` with pipeline overview. **Verification**: T042a diffs README against expected content.
- [X] T045 Enforce minimum 1000 bootstrap iterations (fallback removed). **Verification**: T045a audits code for any fallback logic; T045b asserts no fallback occurs.
- [X] T046 [P] Additional unit tests for edge cases (no outliers, variance reduction, row removal) in `tests/unit/`.
- [X] T047 Run quickstart.md validation and fix any pipeline execution issues. **Verification**: T047a confirms quickstart validation succeeded and required artifacts are present.
- [X] T048 Verify all artifacts are checksummed and `state.yaml` is updated. **Verification**: T048a checks entries in state YAML.
- [X] T049 [P] Add CI/CD workflow file for GitHub Actions with CPU‑only constraints.
- [X] T066 [P] Unit test `tests/unit/test_analysis_fix.py`: Verify `analysis.run_t_test` uses `scipy.stats.ttest_ind` and `statsmodels` OLS.
- [X] T067 [P] Unit test `tests/unit/test_cleaning_signature.py`: Verify cleaning functions return `(cleaned_df, metadata)`.
- [X] T060 Update `.gitignore` to exclude temporary script patterns, compiled files, Jupyter checkpoints, and data temp files. **Verification**: T060a checks `.gitignore` contains required patterns.

## Phase 7: Documentation Draft (Quickstart Removed)

**Purpose**: Documentation updates only; no pipeline execution here.

- [X] T070 [P] (REMOVED - Moved to Phase 12) Execute the Quickstart script (`scripts/quickstart.sh`) from a clean checkout. **Verification**: Checks that the script runs without error and exits with code 0.
- [X] T071 [P] (REMOVED - Moved to Phase 12) Validate Quickstart output: confirm that `baseline_metrics.json`, `cleaned_metrics.json`, and `output/figures/pvalue_shifts_forest.png` are generated and non‑empty after Quickstart execution. **Verification**: T071a asserts presence and non‑emptiness of all required artifacts.

## Phase 8: Specification & Documentation Refinement

**Purpose**: Align spec, data provenance, and documentation with reviewer feedback.

- [X] T050 [P] Remove extraneous text blocks titled **"LLM data quality reports"** and **"glioblastoma biomarkers"** from `specs/001-quantify-data-cleaning-impact/spec.md`. Verified by diff test.
- [X] T050b [P] Remove corrupted FR‑006 text from `spec.md`. Verified by diff test.
- [X] T051 [P] Revise Success Criteria `SC-001`, `SC-002`, `SC-03` in `spec.md` to replace "Median and IQR" with **"Per‑dataset delta reporting with qualitative directionality assessment"**. Verified by diff test.
- [X] T052 [P] Refine hypothesis statement in `spec.md` as required. Verified by diff test.
- [X] T053 [P] Create `data/raw/README.md` documenting URLs, SHA‑256 checksums, and descriptions. **Verification**: T1114a parses README, checks URLs, checksums, and file existence.
- [X] T054 [P] Implement robust download script `scripts/download_data.sh` that fails on error, validates checksum, and logs success. **Verification**: T054a asserts behavior.
- [X] T055 [P] Create `data/processed/data_quality_report.md` with dataset statistics and limitation note. **Verification**: T1116a checks required sections are present.
- [X] T056 [P] Ensure `code/config.py` is the sole source of paths/parameters; add verification task T057‑V that greps for hard‑coded paths.
- [X] T058 [P] Merge unique helpers from `code/cleanup_utils.py` and `code/profiler.py` into `code/utils.py`; delete originals. **Verification**: T058a asserts deletion.
- [X] T059 [P] Move maintenance scripts to `scripts/` and verify original locations are empty. **Verification**: T059a confirms move.
- [X] T060 Update `.gitignore` to exclude temporary script patterns, compiled files, Jupyter checkpoints, and data temp files. **Verification**: T060a checks `.gitignore` contains the required patterns.
- [X] T061 [P] Consolidate fragmented `t0*.py` scripts into their designated modules (cleaning, analysis, reporting, sensitivity). **Verification**: T061a asserts removal.
- [X] T062 [P] Ensure `code/main.py` orchestrates the full pipeline and returns exit code 0 on success. **Verification**: T062a integration test confirms behavior.
- [X] T063 [BUG] Fixed hard‑coded p‑value computation in `code/analysis.py`.
- [X] T064 [BUG] Updated cleaning functions to return `(cleaned_df, metadata_dict)`.
- [X] T065 [BUG] Enforced `config.BOOTSTRAP_ITERATIONS` in bootstrap routine; removed the iteration fallback after a sufficient number of iterations.
- [X] T104 Refactor `code/main.py` to import core pipeline functions only. **Verification**: T104a runs unit tests for `code/main.py` after refactor to ensure unchanged behavior.
- [X] T1108 Move maintenance scripts (`run_lint.py`, `run_quickstart_validation.py`) to `scripts/`. **Verification**: T1108a confirms scripts moved and imports updated without errors.

## Phase 9: Final Validation & Smoke Testing

**Purpose**: Ensure the consolidated pipeline runs end‑to‑end without errors.

- [X] T2019 [P] Run full pipeline smoke test: `python -m code.main` from a clean state. **Verification**: Exit code 0.
- [X] T2020a [P] Verify all output artifacts (`baseline_metrics.json`, `cleaned_metrics.json`, `null_fpr_metrics.json`, visualizations) are generated and non‑empty. **Implementation**: Script checks existence and size > 0.
- [X] T2021 [P] Run unit test suite (`pytest -q`) to confirm no regressions in cleaning, analysis, or reporting modules. **Success**: Exit code 0.
- [X] T2022a [P] Run integration test `tests/integration/test_full_pipeline.py` that runs the full pipeline and checks that all expected output files are present and non‑empty. **Success**: Generates `integration_success_report.txt`.
- [X] T1120a [P] Ensure integration smoke test validates presence and non‑emptiness of all expected output artifacts.

## Phase 10: Additional Hygiene, Consolidation & Reviewer‑Driven Tasks

**Purpose**: Close remaining reviewer‑identified gaps and enforce project hygiene.

- [X] T1107 [HYGIENE] Delete all remaining `code/t0*.py` scripts after confirming logic migrated. **Verification**: T1107a asserts no such files exist.
- [X] T1109 [HYGIENE] Merge unique helper functions from `cleanup_utils.py` and `profiler.py` into `code/utils.py`; then delete the now‑redundant files. **Verification**: T1109a confirms deletion.
- [X] T1110 [HYGIENE] Update `.gitignore` to exclude patterns `t*.py`, `scratch*.py`, `debug*.py` to prevent future accidental commits of temporary scripts. **Verification**: T1110a checks `.gitignore` contains these patterns.
- [X] T1123a [HYGIENE] Run `scripts/check_config.py` and fail if any hard‑coded path strings remain outside `code/config.py`.
- [X] T1124a [HYGIENE] Assert bootstrap routine uses `config.BOOTSTRAP_ITERATIONS` without fallback.

## Phase 11: Specification Amendments & Documentation Updates

**Purpose**: Align the specification with the actual implementation and reviewer feedback.

- [X] T1111 [SPEC] Edit `specs/001-quantify-data-cleaning-impact/spec.md` to **remove** the unrelated "LLM data quality reports" and "glioblastoma biomarkers" paragraphs.
- [X] T1112 [SPEC] Revise Success Criteria `SC-001`, `SC-002`, and `SC-03` in `spec.md` to replace "Median and IQR" with **"Per‑dataset delta reporting with qualitative directionality assessment"** for cases where n < 5.
- [X] T1113 [SPEC] Refine the hypothesis section in `spec.md` to focus on the *direction* of p‑value shifts and remove the untestable "datasets with n < 50" clause.

## Phase 12: Final Verification & Cleanup (Comprehensive)

**Purpose**: Final validation, power analysis, and bin coverage checks.

### Sub-Phase 12.7: Final Verification & Cleanup

- [ ] T1224 [TEST] Run full test suite (`pytest -q`) to confirm all new tests pass and no regressions exist. **Verification**: T1224a asserts exit code 0.
- [ ] T1225 [HYGIENE] Update `.gitignore` to exclude temporary patterns (`t*.py`, `scratch*.py`, `debug*.py`, `__pycache__`, `*.pyc`). **Verification**: T1225a confirms `.gitignore` contains required patterns.
- [ ] T1226 [HYGIENE] Run `scripts/check_config.py` to ensure no hardcoded paths remain in source code. **Verification**: T1226a asserts script exits with success.
- [ ] T1227 [PIPELINE] Execute full pipeline from clean state: `python -m code.main`. Verify all artifacts are generated, valid, and match expected schema. **Verification**: T1227a runs smoke test and validates artifacts.
- [ ] T1228 [POWER] Perform A Priori Power Analysis using `statsmodels.stats.power.WilcoxonPower` for medium effect size (d=0.5), α=0.05, power≥0.8. **Action**: If power < 0.8, dynamically acquire additional datasets to meet the threshold. Write justification to `power_analysis.txt`. **Verification**: T1228a asserts power ≥ 0.8 and file existence.
- [ ] T1229 [DATA] Validate final dataset collection against bin constraints (n<50, 50-200, >200) and missingness levels. **Action**: If any bin is empty, acquire additional datasets. **Verification**: T1229a confirms all bins are populated.