---
description: "Task list for feature: Quantifying the Impact of Data Cleaning on Statistical Inference"
---

# Tasks: Quantifying the Impact of Data Cleaning on Statistical Inference

**Input**: Design documents from `/specs/001-quantify-data-cleaning-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 0: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (code/, data/raw/, data/processed/, tests/)
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pytest)
- [X] T003 [P] Configure linting and formatting tools (ruff/black) in code/

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Create base data models/entities per data-model.md (Dataset, CleaningStrategy, AnalysisResult, ComparisonReport schemas) in `code/models.py`.
- [X] T004 Create `code/utils.py` with function `pin_random_seed(seed: int)` for numpy and scipy, ensuring reproducibility.
- [X] T005 Create `code/utils.py` with function `compute_file_checksum(filepath: str) -> str` for SHA256 validation of data files.
- [X] T006 Create `code/utils.py` with function `setup_logging(log_level: str)` to initialize the logging infrastructure.
- [X] T007 Setup environment configuration management in `code/config.py` with env vars for DATASET_URLS, OUTPUT_PATH, RANDOM_SEED, BOOTSTRAP_ITERATIONS.
- [X] T044 Code cleanup and refactoring (remove dead code, optimize imports). **Verification**: T044a runs lint and ensures no style errors.
- [X] T044a [P] Run lint (`ruff` and `black --check`) on the codebase and assert exit code 0; fail if any style violations are found. **Verification**: Lint passes without errors.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Dataset Acquisition and Baseline Analysis (Priority: P1) 🎯 MVP

**Goal**: Download public datasets from UCI/OpenML and run baseline statistical analyses (t‑tests, linear regressions) on raw, uncleaned data to establish reference metrics (p‑values, 95 % CI, effect sizes)

**Independent Test**: Can be fully tested by executing the dataset download and baseline analysis script against a single dataset, producing a report with p‑values, confidence intervals, and effect sizes for that dataset

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test in `tests/unit/test_acquisition.py`: Verify `download_dataset` returns a successful HTTP status and non-empty content for UCI HAR URL.
- [X] T010 [P] [US1] Integration test in `tests/integration/test_baseline.py`: Verify baseline analysis script produces `baseline_metrics.json` with valid p-values (0 < p < 1) and finite CIs.

### Implementation for User Story 1

- [X] T011 [US1] Implement acquisition logic in `code/data_loader.py`. Downloads verified UCI URLs, validates checksums, logs fallback to OpenML if unavailable, and writes raw files to `data/raw/`. **Verification**: T011a checks HTTP status; T011b validates SHA256 checksum. <!-- UPDATED -->
- [X] [X] T012 [US1] Implement baseline statistical analysis in `code/analysis.py` using `scipy.stats` (t‑tests) and `statsmodels` (linear regression). Writes per‑dataset metrics (p‑value, 95 % CI, effect size) to `data/processed/baseline_metrics.json` with ≥3‑decimal precision. **Deliverable**: `code/analysis.py` baseline functions. **Verification**: T012a runs the analysis; T012b asserts file existence, schema compliance, and ≥3‑decimal precision.
- [X] T012a [US1] Run baseline analysis script on all raw datasets. Produces `baseline_metrics.json`. **Success**: File created with correct schema.
- [X] [X] T012b [US1] Verify `baseline_metrics.json` contains all required fields with ≥3‑decimal precision. **Success**: Automated test passes.
- [X] [X] T012c [US1] Verify numeric fields in `baseline_metrics.json` are rounded to at least three decimal places. **Verification**: Parses JSON and asserts precision.
- [X] [X] T013 [US1] Add orchestration in `code/main.py` to invoke data acquisition and baseline analysis, ensuring `data/processed/baseline_metrics.json` is produced. **Deliverable**: Updated `code/main.py`. **Verification**: T013a runs `python -m code.main --stage baseline` and checks exit code 0 and file presence.
- [X] T013a [US1] Integration test: execute `code/main.py` for baseline stage; verify exit code 0 and artifact generation.

**Checkpoint**: User Story 1 will be fully functional once pending tasks are completed.

---

## Phase 3: User Story 2 - Systematic Cleaning Strategy Application (Priority: P1)

**Goal**: Apply three cleaning strategies systematically (IQR outlier removal, mean/median/KNN imputation, categorical recoding) and re‑run identical statistical tests on each cleaned variant

**Independent Test**: Can be fully tested by applying one cleaning strategy (e.g., IQR outlier removal with k=1.5) to a single dataset and comparing before/after p‑values, which delivers the primary research outcome for that strategy

### Implementation for User Story 2

- [X] T017 [US2] Implement function `apply_iqr_outlier_removal(df, k=1.5)` in `code/cleaning.py`. Logs rows removed; flags if ≥50 % rows removed.
- [X] T018 [US2] Implement function `apply_mean_imputation(df, columns)` in `code/cleaning.py`. Validates zero missing values; flags variance reduction ≥20 %.
- [X] T019 [US2] Implement function `apply_median_imputation(df, columns)` in `code/cleaning.py`. Same validation as T018.
- [X] T020 [US2] Implement function `apply_knn_imputation(df, columns, k=5)` in `code/cleaning.py` using scikit‑learn. Same validation as T018.
- [X] T021 [US2] Implement function `apply_categorical_recoding(df)` in `code/cleaning.py` with factor encoding.
- [X] T022 [US2] Write cleaned datasets to `data/processed/` with strategy‑specific filenames (e.g., `dataset_outlier_removed.csv`).
- [X] T023 [US2] Ensure cleaning functions return `(cleaned_df, metadata_dict)` where metadata includes `rows_removed` and `missing_values_remaining`.
- [X] T024 [US2] Re‑run t‑tests and linear regressions on each cleaned variant using `code/analysis.py`. **Deliverable**: Updated analysis pipeline.
- [X] [X] T069 [US2] Generate `data/processed/cleaned_metrics.json` aggregating metrics per cleaning strategy per dataset. **Dependency**: T024. **Verification**: T069a runs the generation; T069b checks schema, precision, and inclusion of cleaning metadata.
- [X] T069a [US2] Execute cleaned‑metrics generation step via `code/main.py --stage cleaned`.
- [X] T069b [US2] Verify `cleaned_metrics.json` contains required fields, ≥3‑decimal precision, and cleaning metadata.
- [X] [X] T069c [US2] Verify numeric fields in `cleaned_metrics.json` are rounded to at least three decimal places.

### Tests for User Story 2 (OPTIONAL ⚠️)

- [X] T014 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_iqr_outlier_removal` removes rows where |z-score| > k and logs count.
- [X] T015 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_mean_imputation` results in zero missing values in target columns.
- [X] T016 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_categorical_recoding` produces factor‑encoded columns and validates against FR‑002 and FR‑003 requirements.

**Checkpoint**: User Story 2 tasks are now complete and ready for execution.

---

## Phase 4: User Story 3 - Metrics Comparison and Sensitivity Analysis (Priority: P2)

**Goal**: Compute absolute and relative differences between baseline and cleaned results, perform sensitivity analysis across dataset sizes and missingness rate bins, and generate summary visualizations

**Independent Test**: Can be fully tested by running the comparison script on 2 datasets (one cleaned, one baseline) and verifying the difference report contains p‑value shifts, CI width changes, and effect‑size variations with valid numeric values

### Shared Preparatory Tasks

- [X] T099a [P] Prepare baseline and cleaned metric artifacts for downstream comparison. Runs validation script `code/validation.py` **after** T012b and T069b. **Verification**: T099b confirms artifacts exist and pass schema checks.
- [X] T099b [P] Validation of artifacts: ensure `baseline_metrics.json` and `cleaned_metrics.json` are present, well‑formed, and meet precision requirements.

### Tests for User Story 3 (OPTIONAL)

- [X] T090 [P] [US3] Unit test in `tests/unit/test_reporting.py`: Verify `calculate_p_value_shift` returns absolute difference with ≥3‑decimal precision.
- [X] T025 [P] [US3] Unit test in `tests/unit/test_reporting.py`: Verify Benjamini‑Hochberg correction is applied correctly.
- [X] T026 [P] [US3] Integration test in `tests/integration/test_sensitivity.py`: Verify stratification logic logs warnings for empty bins and proceeds.

### Implementation for User Story 3

- [X] T027 [US3] Implement metrics comparison in `code/reporting.py`. Computes |p_cleaned − p_baseline| (≥3‑decimal), CI width change (≥2‑decimal), effect‑size delta, and inconsistency rate (proportion of datasets where significance status changes). **Dependency**: T012, T024.
- [X] [X] T027a [US3] Generate per‑dataset delta report `output/reports/delta_report.json` meeting SC‑001 wording (qualitative directionality, per‑dataset).
- [X] [X] T027c [US3] Verify `delta_report.json` contains per‑dataset entries with required fields and proper precision.
- [X] T028 [US3] Add claim verification placeholder (no external reference required). **Deliverable**: `code/reporting.py`.
- [X] T029 [US3] Implement missingness‑rate binning with thresholds (0 %, ≤5 %, ≤10 %, >10 %). Logs warning `"Missingness bin empty: bin <X> has no datasets"`.
- [X] T030 [US3] Implement dataset‑size binning (n<50, 50‑200, >200). Logs warning for empty bins.
- [X] T031 [US3] Implement bootstrap variance estimation with **≥1000** resamples per dataset (default 1000). **Verification**: T045a audits code for absence of fallback.
- [X] [X] T033a [US3] Perform outlier‑threshold sweep for k ∈ {1.5, 2.0}; for each threshold run full analysis on real data and store per‑threshold metrics in `data/processed/outlier_threshold_sweep_report.json`.
- [X] [X] T033b [US3] Compute inconsistency rate per outlier threshold; append to sweep report.
- [X] [X] T033c [US3] Verify `outlier_threshold_sweep_report.json` exists, is well‑formed, and contains required fields with ≥3‑decimal precision.
- [X] [X] T039a [US3] Implement false‑positive‑rate (FPR) estimation: generate permutation null datasets, run full pipeline for each outlier‑threshold, compute proportion of p < 0.05, store results in `data/processed/null_fpr_metrics.json`.
- [X] [X] T039b [US3] Verify `null_fpr_metrics.json` exists, schema‑valid, and numeric fields meet ≥3‑decimal precision.
- [X] [X] T034 [US3] Generate forest plot of p‑value shifts (`output/figures/pvalue_shifts_forest.png`). **Verification**: T034a checks file existence.
- [X] [X] T034c [US3] Verify forest plot file is non‑empty and saved to the correct path.
- [X] [X] T035 [US3] Generate heatmap of CI‑width changes (`output/figures/ci_width_heatmap.png`). **Verification**: T035a checks file existence.
- [X] [X] T035c [US3] Verify heatmap file is non‑empty and saved to the correct path.
- [X] T036 [US3] Implement per‑dataset p‑value shift reporting (no median/IQR). **Aligns with methodological pivot**.
- [X] T037 [US3] Implement per‑dataset CI width change reporting. **Enforced minimum 1000 bootstrap iterations; no fallback**.
- [X] T038 [US3] Implement per‑dataset effect‑size change reporting.
- [X] T039 [US3] Log excluded datasets (>80 % missing outcome) with warning; record reason in `data_quality_report.md`.
- [X] T040 [US3] Create `ComparisonReport` entity and write `data/processed/comparison_report.json` aggregating all results.
- [X] T041 [US3] Generate final report `output/reports/final_report.md` referencing visualizations and noting methodological limitations.

**Checkpoint**: All US3 tasks now have explicit dependencies on T012/T024, making the story correctly dependent on US1/US2 completion.

---

## Phase 5: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042 [P] Documentation updates in `docs/README.md` with pipeline overview.
- [X] T045 Enforce minimum 1000 bootstrap iterations (fallback removed). **Verification**: T045a audits code for any fallback logic.
- [X] T046 [P] Additional unit tests for edge cases (no outliers, variance reduction, row removal) in `tests/unit/`.
- [X] T047 Run quickstart.md validation and fix any pipeline execution issues. **New tasks**: T070 (execute quickstart) and T071 (validate quickstart output) added in Phase 6.
- [X] T048 Verify all artifacts are checksummed and `state.yaml` is updated.
- [X] T049 [P] Add CI/CD workflow file for GitHub Actions with CPU‑only constraints.
- [X] T066 [P] Unit test `tests/unit/test_analysis_fix.py`: Verify `analysis.run_t_test` uses `scipy.stats.ttest_ind` and `statsmodels` OLS.
- [X] T067 [P] Unit test `tests/unit/test_cleaning_signature.py`: Verify cleaning functions return `(cleaned_df, metadata)`.

---

## Phase 6: Quickstart Execution and Validation

**Purpose**: Ensure the Quickstart documentation steps are executable and produce expected artifacts.

- [X] T070 [P] Execute the Quickstart script (`scripts/quickstart.sh`) from a clean checkout. **Verification**: Checks that the script runs without error and exits with code 0.
- [X] T071 [P] Validate Quickstart output: confirm that `baseline_metrics.json`, `cleaned_metrics.json`, and `output/figures/pvalue_shifts_forest.png` are generated and non‑empty after Quickstart execution.

---

## Phase 7: Specification & Documentation Refinement

**Purpose**: Align spec, data provenance, and documentation with reviewer feedback.

- [X] T050 [P] Remove extraneous text blocks titled **"LLM data quality reports"** and **"glioblastoma biomarkers"** from `specs/001-quantify-data-cleaning-impact/spec.md`. Verified by diff test.
- [X] T050b [P] Remove corrupted FR‑006 text from `spec.md`. Verified by diff test.
- [X] T051 [P] Revise Success Criteria `SC-001`, `SC-002`, `SC-03` in `spec.md` to replace "Median and IQR" with "Per‑dataset delta reporting with qualitative directionality assessment". Verified by diff test.
- [X] T052 [P] Refine hypothesis statement in `spec.md` as required. Verified by diff test.
- [X] T053 [P] Create `data/raw/README.md` documenting URLs, SHA‑256 checksums, and descriptions. Test parses table and validates checksums.
- [X] T054 [P] Implement robust download script `scripts/download_data.sh` that fails on error, validates checksum, and logs success. Test asserts behavior.
- [X] T055 [P] Create `data/processed/data_quality_report.md` with dataset statistics and limitation note. Test checks sections.
- [X] T056 [P] Add comprehensive test suite covering data loading, cleaning, analysis, and full pipeline integration.
- [X] T057 [P] Ensure `code/config.py` is the sole source of paths/parameters; add verification task `T057‑V` that greps for hard‑coded paths.
- [X] T058 [P] Merge unique helpers from `code/cleanup_utils.py` and `code/profiler.py` into `code/utils.py`; delete originals. Verify deletion with test.
- [X] T059 [P] Move maintenance scripts to `scripts/` and verify original locations are empty.
- [X] T060 Update `.gitignore` to exclude temporary task scripts, compiled files, Jupyter checkpoints, and data temp files.
- [X] T061 [P] Consolidate fragmented `t0*.py` scripts into their designated modules (cleaning, analysis, reporting, sensitivity). Verify removal with test.
- [X] T062 [P] Ensure `code/main.py` orchestrates the full pipeline and returns exit code 0 on success. Add integration test.
- [X] T063 [BUG] Fixed hard‑coded p‑value computation in `code/analysis.py`.
- [X] T064 [BUG] Updated cleaning functions to return `(cleaned_df, metadata_dict)`.
- [X] T065 [BUG] Enforced `config.BOOTSTRAP_ITERATIONS` in bootstrap routine; removed the iteration fallback after a sufficient number of iterations.

---

## Phase 8: Refactoring – Fine‑Grained Tasks (formerly Phase 9)

**Purpose**: Replace coarse, multi‑action tasks with atomic, verifiable units.

- [X] T094 Delete all `code/t0*.py` scripts after confirming logic migrated. **Verification**: T094a asserts no such files remain.
- [X] T095a Audit `code/cleanup_utils.py` for unique functions and produce a report.
- [X] T095b Produce audit artifact `audit_cleanup_utils.txt` listing unique functions.
- [X] T096a Audit `code/profiler.py` for unique functions and produce a report.
- [X] T096b Produce audit artifact `audit_profiler.txt` listing unique functions.
- [X] T097 Merge unique functions from `cleanup_utils.py` and `profiler.py` into `code/utils.py`.
- [X] T098 Delete `code/cleanup_utils.py`. **Verification**: T2018a ensures file absent.
- [X] T099 Delete `code/profiler.py`. **Verification**: T2018a ensures file absent.
- [X] T100 Move `code/run_lint.py` to `scripts/run_lint.py`. **Verification**: T2016a confirms relocation.
- [X] T101 Move `code/run_quickstart_validation.py` to `scripts/run_quickstart_validation.py`. **Verification**: T2016a confirms relocation.
- [X] T102 Create linting script `scripts/check_config.py` that scans for hard‑coded path strings outside `code/config.py`. **Verification**: T102a asserts it flags violations.
- [X] T103 Execute `scripts/check_config.py` and fix any violations. **Verification**: T103a produces a CI pass report.
- [X] T104 Refactor `code/main.py` to import core pipeline functions only.
- [X] T105 Ensure `code/main.py` is the sole entry point; add test `tests/unit/test_main_entrypoint.py`.

---

## Phase 9: Structural Consolidation & Logic Correction (Reviewer Fixes)

**Purpose**: Address critical reviewer findings regarding code fragmentation, hardcoded values, and missing logic.

- [X] T2001 [REVIEWER-COMPLETENESS] Implement FR‑006 (FPR Estimation) logic directly in `code/analysis.py` and `code/reporting.py`. Includes permutation null dataset generation, full pipeline execution per outlier threshold, and FPR computation. **Verification**: T2001a runs FPR module and checks `null_fpr_metrics.json`.
- [X] T2002 [REVIEWER-COMPLETENESS] Ensure `code/main.py` imports and calls these functions directly to form a single, runnable pipeline. **Verification**: T2002a runs full pipeline and confirms all stages execute.
- [X] T2003 [REVIEWER-COMPLETENESS] Verify `code/cleaning.py` contains full implementations of T017‑T021 (no imports from deleted modules). **Verification**: T2003a runs static analysis.
- [X] T2004 [REVIEWER-CORRECTNESS] Fix `code/analysis.py`: Remove hardcoded `p_value = 0.05`. Replace with `scipy.stats.ttest_ind` and `statsmodels` OLS calls.
- [X] T2005 [REVIEWER-CORRECTNESS] Correct Cohen's d calculation in `code/analysis.py` to use the pooled standard deviation of the two specific groups being compared.
- [X] [X] T2006 [REVIEWER-CORRECTNESS] Re‑run the pipeline to regenerate `data/processed/baseline_metrics.json` and `data/processed/cleaned_metrics.json` with real computed values. **Verification**: T2006a validates regenerated files against schema and precision.
- [X] T2007 [REVIEWER-CORRECTNESS] Update `code/cleaning.py` so all cleaning functions return `(cleaned_df, metadata)` including `rows_removed` and `missing_values_remaining`.
- [X] [X] T2008 [REVIEWER-CORRECTNESS] Update `code/reporting.py` to consume the metadata from cleaning functions and ensure `data/processed/cleaned_metrics.json` includes these fields. **Verification**: T2008a checks JSON content.
- [X] [X] T2009 [REVIEWER-CORRECTNESS] Ensure `config.BOOTSTRAP_ITERATIONS` (default 1000) is explicitly passed to the bootstrap function with no fallback. **Verification**: T2009a confirms no fallback logic exists.
- [X] T2011 [REVIEWER-DATA-QUALITY] Update `data/raw/README.md` with exact URLs, DOIs, and SHA‑256 checksums for UCI HAR and UCI Shopper. **Verification**: T2011a runs schema validation on the README.
- [X] T2012 [REVIEWER-DATA-QUALITY] Make `code/data_loader.py` fail (non‑zero exit) if download from verified URL fails; add log entry confirming checksum match. **Verification**: T2012a simulates failure and expects exit ≠ 0.
- [X] T2013 [REVIEWER-DATA-QUALITY] Create `data/processed/data_quality_report.md` recording dataset selection process, excluded datasets, and final n = 2 limitation. **Verification**: T2013a checks file existence and content sections.
- [X] T2014 [REVIEWER-DATA-QUALITY] Add test `tests/unit/test_data_provenance.py` that verifies the existence and validity of `data/raw/README.md` and `data/processed/data_quality_report.md`.

---

## Phase 10: Final Validation & Smoke Testing

**Purpose**: Ensure the consolidated pipeline runs end‑to‑end without errors.

- [X] T2019 [P] Run full pipeline smoke test: `python -m code.main` from a clean state. **Verification**: Exit code 0.
- [X] T2020a [P] Verify all output artifacts (`baseline_metrics.json`, `cleaned_metrics.json`, `null_fpr_metrics.json`, visualizations) are generated and non‑empty. **Implementation**: Script checks existence and size > 0.
- [X] T2021 [P] Run unit test suite (`pytest -q`) to confirm no regressions in cleaning, analysis, or reporting modules. **Success**: Exit code 0.
- [X] T2022a [P] Run integration test `tests/integration/test_full_pipeline.py` that runs the full pipeline and checks that all expected output files are present and non‑empty. **Success**: Generates `integration_success_report.txt`.

---

## Phase 11: Additional Hygiene, Consolidation & Reviewer‑Driven Tasks

**Purpose**: Close remaining reviewer‑identified gaps and enforce project hygiene.

- [X] T1107 [HYGIENE] Delete all remaining `t0*.py` scripts after confirming their logic has been fully migrated into `code/cleaning.py`, `code/analysis.py`, and `code/reporting.py`. **Verification**: T1107a asserts no such files exist.
- [X] T1108 [HYGIENE] Move `code/run_lint.py` and `code/run_quickstart_validation.py` to `scripts/` directory and update any references. **Verification**: T1108a checks file locations.
- [X] T1109 [HYGIENE] Merge any unique helper functions from `code/cleanup_utils.py` and `code/profiler.py` into `code/utils.py`; then delete the now‑redundant files. **Verification**: T1109a confirms deletion.
- [X] T1110 [HYGIENE] Update `.gitignore` to exclude patterns `t*.py`, `scratch*.py`, `debug*.py` to prevent future accidental commits of temporary scripts.

---

## Phase 12: Specification Amendments & Documentation Updates

**Purpose**: Align the specification with the actual implementation and reviewer feedback.

- [X] T1111 [SPEC] Edit `specs/001-quantify-data-cleaning-impact/spec.md` to **remove** the unrelated “LLM data quality reports” and “glioblastoma biomarkers” paragraphs.
- [X] T1112 [SPEC] Revise Success Criteria `SC-001`, `SC-002`, and `SC-03` in `spec.md` to replace “Median and IQR” with **“Per‑dataset delta reporting with qualitative directionality assessment”** for cases where n < 5.
- [X] T1113 [SPEC] Refine the hypothesis section in `spec.md` to focus on the *direction* of p‑value shifts (e.g., “outlier removal reduces p‑values when outliers are present”) and remove the untestable “datasets with n < 50” clause.

---

## Phase 13: Data Provenance & Robust Loading

**Purpose**: Ensure all data sources are real, verifiable, and loading failures are explicit.

- [X] T1114 [DATA] Create `data/raw/README.md` documenting exact URLs, DOIs, and SHA‑256 checksums for the UCI HAR and UCI Shopper datasets.
- [X] T1115 [DATA] Implement (or update) `code/data_loader.py` so that any download failure raises an exception (non‑zero exit) and logs a checksum verification message upon success.
- [X] T1116 [DATA] Generate `data/processed/data_quality_report.md` describing the dataset selection process, numbers attempted vs. excluded, reasons for exclusion, and the final n = 2 limitation.

---

## Phase 14: Comprehensive Test Suite

**Purpose**: Provide automated verification of core functionality and full‑pipeline execution.

- [X] T1117 [TEST] Add unit tests in `tests/unit/test_cleaning.py` covering IQR outlier removal, mean/median/KNN imputation, and categorical recoding, asserting correct metadata (`rows_removed`, `missing_values_remaining`).
- [X] T1118 [TEST] Add unit tests in `tests/unit/test_analysis.py` verifying that `run_t_test` uses `scipy.stats.ttest_ind` and that regression uses `statsmodels` OLS, and that Cohen’s d is correctly computed.
- [X] T1119 [TEST] Add unit tests in `tests/unit/test_bootstrap.py` confirming that the bootstrap routine respects `config.BOOTSTRAP_ITERATIONS` (≥1000) and does not fallback silently.
- [X] T1120 [TEST] Add an integration smoke test `tests/integration/test_full_pipeline.py` that runs `python -m code.main` from a clean checkout and checks that all expected output files are present and non‑empty.

---

## Phase 15: Core Logic Corrections & Configuration Centralization

**Purpose**: Fix statistical computation bugs and enforce a single source of configuration.

- [X] T1121 [CORE] Refactor `code/analysis.py` to remove the placeholder `p_value = 0.05` and replace it with actual calls to `scipy.stats.ttest_ind` (for t‑tests) and `statsmodels` OLS (for linear regression). Also correct the Cohen’s d calculation to use the pooled standard deviation of the two groups being compared.
- [X] T1122 [CORE] Update all cleaning functions in `code/cleaning.py` (`apply_iqr_outlier_removal`, `apply_mean_imputation`, `apply_median_imputation`, `apply_knn_imputation`, `apply_categorical_recoding`) so they return a tuple `(cleaned_df, metadata_dict)` where `metadata_dict` includes `rows_removed` and `missing_values_remaining`. Ensure `code/reporting.py` consumes this metadata and writes it into `data/processed/cleaned_metrics.json`.
- [X] T1123 [CONFIG] Audit the entire codebase to guarantee that **only** `code/config.py` defines paths and parameters (e.g., `DATASET_URLS`, `OUTPUT_PATH`). Replace any hard‑coded strings like `"data/raw/"` or `"output/figures/"` with references to `config`. Add a verification task `T057‑V` that greps for disallowed literals.

---

## Phase 16: Bootstrap & Sensitivity Configuration

**Purpose**: Enforce Constitution Principle VI regarding bootstrap iterations.

- [X] T1124 [BOOTSTRAP] Ensure that the bootstrap routine receives `config.BOOTSTRAP_ITERATIONS` (default 1000) explicitly; remove any fallback to 500 iterations unless the dataset size exceeds 5 000 rows, in which case a warning is logged and the iteration count is capped at 1000.
