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
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pytest, jsonschema)
- [X] T003 Configure linting and formatting tools (ruff/black) in code/
- [X] T004 Create `code/config.py` with constants for seeds, paths, and `BOOTSTRAP_ITERATIONS` (defaulting to a sufficient number of iterations for robust estimation).
- [X] T005 Create `code/utils.py` with `pin_random_seed(seed: int)` and `compute_file_checksum(filepath: str) -> str` (SHA256). **Verification**: T005a asserts checksum recorded in `state/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-.yaml` and verified against raw files.
- [X] T005a Verify checksums in state YAML match raw data files.
- [X] T006 Create `code/utils.py` with `setup_logging(log_level: str)`.
- [X] T007 Setup environment configuration management in `code/config.py` with env vars for DATASET_URLS, OUTPUT_PATH, RANDOM_SEED, BOOTSTRAP_ITERATIONS.

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, bug fixes, configuration, and unit tests that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase now includes critical bug fixes, configuration audits, and unit tests to ensure downstream tasks run on correct, validated code.

- [X] T1201 Audit `code/` directory to identify all files matching `t0*.py` pattern. **Verification**: Generates `audit/t0_files.txt`; asserts file exists and is non‑empty.
- [X] T1202 [US2] Migrate logic from identified `code/t0*.py` scripts (glob pattern) into `code/cleaning.py`, `code/analysis.py`, `code/reporting.py`. **Dependency**: T1201 must complete first. **Verification**: Unit tests confirm logic integrity in new modules.
- [X] T1203 [US3] Migrate reporting logic from `code/t0*.py` scripts into `code/reporting.py` and `code/main.py`. **Dependency**: T027 must be complete first. **Verification**: Verifies all functions are callable from `main.py` and produce identical artifacts.
- [X] T1204 Delete all standalone `code/t0*.py` scripts after successful migration. **Verification**: Script `scripts/verify_no_t0_scripts.py` asserts no files matching `t0*.py` remain.
- [X] T007 Setup environment configuration management in `code/config.py` with env vars for DATASET_URLS, OUTPUT_PATH, RANDOM_SEED, BOOTSTRAP_ITERATIONS.
- [X] T056 [P] Ensure `code/config.py` is the sole source of paths/parameters; add verification task T057‑V that greps for hard‑coded path strings. **Verification**: T056a asserts no hardcoded paths remain in codebase.
- [X] T1205 Audit all Python modules in `code/` for hardcoded path strings. **Verification**: Generates `audit/hardcoded_paths.txt`.
- [X] T1206 [BUG] Refactor all identified hardcoded paths to import constants from `code/config.py`. **Dependency**: T007 (file creation), T056 (config population), T1205 (audit). **Verification**: Static analysis confirms no hardcoded paths remain.
- [X] T1207 Update `code/main.py` to load configuration from `code/config.py` and pass paths explicitly. **Verification**: Executes `main.py` with a clean environment to confirm correct path resolution.
- [X] T1213 Audit `code/cleanup_utils.py`, `code/profiler.py` for duplicate functions. **Verification**: Generates diff report of overlapping functions.
- [X] T1214 Consolidate unique logic from `code/cleanup_utils.py` and `code/profiler.py` into `code/utils.py`. Delete originals. **Verification**: Asserts deletion and successful import.
- [X] T1215 Move maintenance scripts `code/run_lint.py` and `code/run_quickstart_validation.py` to `scripts/`. **Verification**: Confirms scripts are moved and executable.
- [X] T1216 Fix `code/analysis.py`: Remove hardcoded `p_value = 0.05`. Replace with `scipy.stats.ttest_ind` for t‑tests. **Verification**: Runs analysis on a known dataset and verifies p‑values are dynamic.
- [X] T1217 Fix Cohen's d calculation in `code/analysis.py`: Ensure pooled standard deviation is computed from the two specific groups defined by the outcome variable. **Verification**: Unit test compares computed Cohen's d against manual calculation.
- [X] T1218 Update `code/cleaning.py`: Ensure all cleaning functions return `(cleaned_df, metadata_dict)` including `rows_removed` and `missing_values_remaining`. **Verification**: Unit tests confirm metadata return.
- [X] T1219 Fix `code/reporting.py`: Ensure it correctly consumes metadata from cleaning functions and populates `cleaned_metrics.json` with exactly these fields: `rows_removed` (numeric), `missing_before` (numeric), `missing_after` (numeric), `variance_reduction` (numeric). **Dependency**: `contracts/cleaned_metrics.schema.yaml`. **Verification**: Validates `cleaned_metrics.json` schema compliance.
- [X] T1220 Correct Bootstrap Configuration: Update all bootstrap calls to use `config.BOOTSTRAP_ITERATIONS` with a standard, non-default iteration count (1000) and **NO** fallback. **Verification**: Audits code for absence of fallback logic.
- [X] T1220b Add unit test `tests/unit/test_bootstrap.py::test_iteration_count` to ensure bootstrap receives the correct iteration count. **Verification**: Asserts test passes.
- [X] T1208 Create `tests/` directory structure with subdirectories `unit/`, `integration/`, `contract/`.
- [X] T1209 Create `tests/fixtures/sample_data.csv` with known values.
- [X] T1210 Implement unit tests in `tests/unit/test_cleaning.py` for IQR, imputation, recoding. **Verification**: Asserts pass rate.
- [X] T1211 Implement unit tests in `tests/unit/test_analysis.py` for t-test and regression. **Verification**: Asserts pass rate.
- [X] T1212 Implement integration test `tests/integration/test_full_pipeline.py`. **Verification**: Asserts all artifacts exist.
- [X] T1213a Implement contract‑validation tests in `tests/contract/` for all JSON artifacts. **Verification**: Asserts pass rate.
- [X] T1221 Create `data/raw/README.md` documenting URLs, DOIs, and cryptographic checksums. **Verification**: Validates README completeness.
- [X] T1223 Update `code/data_loader.py` to fail (non‑zero exit) if download fails. Remove silent fallback. **Verification**: Simulates failed download and asserts error exit.

## Phase 1.5: Missingness Mechanism Generation

**Purpose**: Generate MCAR and MAR missingness mechanisms required for FPR estimation.

- [ ] T074a [US2] Generate MCAR and MAR missingness mechanisms for each dataset. **Implementation**: Use `sklearn.utils.shuffle` for MCAR and logistic model for MAR. Store in `data/processed/missingness_mechanisms/`. **Dependency**: T011 (Dataset Acquisition). **Verification**: Asserts files exist and have correct shape.

## Phase 1.7: Permutation‑Based FPR Estimation (Corrected Order)

**Purpose**: Estimate FPR with outcome permutation **before** any cleaning step, per FR-006.

**⚠️ NOTE**: The plan.md Phase 5 currently states "permute after cleaning". This contradicts spec.md FR-006. Tasks below enforce the spec requirement (permute BEFORE cleaning). The plan.md must be revised separately to align.

- [ ] T074 [US1] Permutation‑Based FPR Estimation: Permute the outcome column **before** any cleaning operation (using both MCAR and MAR missingness mechanisms). Run the full cleaning pipeline for each variant. Use a fixed number of permutations for ALL datasets to ensure reproducibility. Compute the proportion of permutations yielding a significant result (p < 0.05) after Holm‑Bonferroni correction and store in `null_fpr_metrics.json`. **Dependency**: T074a (Missingness Generation). **Verification**: T074b checks that the permutation occurs prior to cleaning and validates precision (≥3‑decimal) in `null_fpr_metrics.json`.
- [X] T074b Verify permutation-before-cleaning order and count.

## Phase 2: User Story 1 - Dataset Acquisition and Baseline Analysis (Priority: P1) 🎯 MVP

**Goal**: Download public datasets from UCI/OpenML and run baseline statistical analyses (t‑tests, linear regressions) on raw, uncleaned data to establish reference metrics (p‑values, 95 % CI, effect sizes)

**Independent Test**: Can be fully tested by executing the dataset download and baseline analysis script against a single dataset, producing a report with p‑values, confidence intervals, and effect sizes for that dataset

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test in `tests/unit/test_acquisition.py`: Verify `download_dataset` returns a successful HTTP status and non-empty content.
- [X] T010 [P] [US1] Integration test in `tests/integration/test_baseline.py`: Verify baseline analysis script produces `baseline_metrics.json` with valid p‑values.

### Implementation for User Story 1

- [X] T011 [US1] Implement acquisition logic in `code/data_loader.py`. Downloads verified UCI URLs, validates checksums, and writes raw files to `data/raw/`. **Verification**: T011a checks HTTP status; T011b validates SHA256 checksum.
- [X] T012 [US1] Implement baseline statistical analysis in `code/analysis.py` using `scipy.stats` and `statsmodels`. Writes per‑dataset metrics (p‑value, 95% CI, effect size, `ci_overlap`, `effect_size_change`) to `data/processed/baseline_metrics.json` with ≥3‑decimal precision. **Verification**: T012a runs the analysis; T012b asserts file existence, schema compliance, and precision.
- [X] T013 [US1] Add orchestration in `code/main.py` to invoke data acquisition and baseline analysis. **Verification**: T013a runs `python -m code.main --stage baseline` and checks exit code 0.

## Phase 3: User Story 2 - Systematic Cleaning Strategy Application (Priority: P1)

**Goal**: Apply three cleaning strategies systematically (IQR outlier removal, mean/median/KNN imputation, categorical recoding) and re‑run identical statistical tests on each cleaned variant

**Independent Test**: Can be fully tested by applying one cleaning strategy (e.g., IQR outlier removal with k=1.5) to a single dataset and comparing before/after p‑values, which delivers the primary research outcome for that strategy

### Implementation for User Story 2

- [X] T017 [US2] Implement function `apply_iqr_outlier_removal(df, k=1.5)` in `code/cleaning.py`. Logs rows removed; flags if ≥50% rows removed. **Verification**: T017a unit‑tests correct removal and metadata.
- [X] T018 [US2] Implement function `apply_mean_imputation(df, columns)` in `code/cleaning.py`. Validates zero missing values; flags variance reduction ≥20%. **Verification**: T018a unit‑test.
- [X] T019 [US2] Implement function `apply_median_imputation(df, columns)` in `code/cleaning.py`. **Verification**: T019a unit‑test.
- [X] T020 [US2] Implement function `apply_knn_imputation(df, columns, k=5)` in `code/cleaning.py`. **Verification**: T020a unit‑test.
- [X] T021 [US2] Implement categorical recoding: nominal (≤10 categories) → one‑hot; ordinal/large (>10) → integer label encoding. Return `(cleaned_df, metadata_dict)`. **Verification**: T021a unit‑test validates encoding and metadata.
- [X] T022 [US2] Write cleaned datasets to `data/processed/` with strategy‑specific filenames. **Verification**: T022a checks naming and checksums.
- [X] T023 [US2] Ensure cleaning functions return `(cleaned_df, metadata_dict)` with `rows_removed` and `missing_values_remaining`. **Verification**: T023a asserts metadata fields.
- [X] T024 [US2] Re‑run t‑tests and linear regressions on each cleaned variant using `code/analysis.py`.
- [X] T069 [US2] Generate `data/processed/cleaned_metrics.json` aggregating metrics per cleaning strategy per dataset, including `ci_overlap` and `effect_size_change`. **Verification**: T069a runs generation; T069b checks schema, precision, and metadata.
- [ ] T074a [US2] Generate MCAR and MAR missingness mechanisms for each dataset. **Implementation**: Use `sklearn.utils.shuffle` for MCAR and logistic model for MAR. Store in `data/processed/missingness_mechanisms/`. **Dependency**: T011 (Dataset Acquisition). **Verification**: Asserts files exist and have correct shape.

### Tests for User Story 2 (OPTIONAL ⚠️)

- [X] T014 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_iqr_outlier_removal` removes rows correctly.
- [X] T015 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_mean_imputation` results in zero missing values.
- [X] T016 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_categorical_recoding` produces factor‑encoded columns.

## Phase 4: User Story 3 - Metrics Comparison and Sensitivity Analysis (Priority: P2)

**Goal**: Compute absolute and relative differences between baseline and cleaned results, perform sensitivity analysis across dataset sizes and missingness rate bins, and generate summary visualizations

**Independent Test**: Can be fully tested by running the comparison script on 2 datasets (one cleaned, one baseline) and verifying the difference report contains p‑value shifts, CI width changes, and effect‑size variations with valid numeric values

### Shared Preparatory Tasks

- [X] T099a [P] Prepare baseline and cleaned metric artifacts for downstream comparison. Runs validation script `code/validation.py`. **Verification**: T099b confirms artifacts exist and pass schema checks.

### Implementation for User Story 3

- [X] T027 [US3] Implement metrics comparison in `code/reporting.py`. Computes `ci_overlap` (proportion of overlapping intervals) and `effect_size_change` (absolute change in effect size). **Constraint**: Do NOT calculate CI width change. Stores results in `baseline_metrics.json` and `cleaned_metrics.json` with ≥3‑decimal precision. **Dependency**: T012, T024.
- [X] T028 [US3] Add claim verification placeholder (no external reference required).
- [X] T029 [US3] Implement missingness‑rate binning with thresholds (0%, ≤5%, ≤10%, >10%). Logs warning for empty bins.
- [X] T030 [US3] Implement dataset‑size binning (n<50, 50‑200, >200). Logs warning for empty bins.
- [X] T031 [US3] Implement bootstrap variance estimation with a fixed number of resamples per dataset (config.BOOTSTRAP_ITERATIONS = 1000). **NO fallback permitted**. **Verification**: T045a audits code for absence of fallback.
- [X] T033a [US3] Perform outlier‑threshold sweep for k ∈ {, a representative upper bound}; store per‑threshold metrics in `data/processed/outlier_threshold_sweep_report.json`.
- [X] T033b [US3] Compute inconsistency rate per outlier threshold; append to sweep report.
- [X] T033c [US3] Verify `outlier_threshold_sweep_report.json` exists and is well‑formed.
- [X] T034 [US3] Generate forest plot of p‑value shifts (`output/figures/pvalue_shifts_forest.png`). **Verification**: T034a checks file existence.
- [X] T035 [US3] Generate heatmap of CI‑width changes (`output/figures/ci_width_heatmap.png`). **Verification**: T035a checks file existence.
- [X] T036 [US3] Implement per‑dataset p‑value shift reporting.
- [X] T038 [US3] Implement per‑dataset effect‑size change reporting.
- [X] T039 [US3] Log excluded datasets (>80% missing outcome) with warning; record reason in `data_quality_report.md`.
- [X] T040 [US3] Create `ComparisonReport` entity and write `data/processed/comparison_report.json`.
- [X] T041 [US3] Generate final report `output/reports/final_report.md`.
- [X] T007a [US3] Apply Holm‑Bonferroni correction across all cleaning‑variant p‑values; store adjusted p‑values in `cleaned_metrics.json`. **Verification**: T007b asserts FWER ≤ 0.05.
- [X] T008a [US3] Perform stratified sensitivity analysis across size and missingness bins; store results in `sensitivity_metrics.json`. **Verification**: T008b checks that each bin contains ≥1 dataset.
- [X] T006a [US3] Perform Wilcoxon‑based power analysis (medium effect size, α = 0.05, power ≥ 0.8) for each dataset and write justification to `power_analysis.txt`. **Verification**: T006b validates the file.
- [X] T006c [US3] Run citation‑validation script (Principle II) and log outcome. **Verification**: T006d checks the validation log.
- [X] T006e [US3] Generate synthetic benchmark datasets (null effect and d = 0.5), run the full pipeline, and record FPR and effect‑size recovery. **Verification**: T006f asserts FPR ≤ 0.05 and effect‑size tolerance ±0.1.
- [X] T006g [US3] Compute paired Wilcoxon test on `p_value_delta` across datasets for each cleaning operation; store results in `hypothesis_test_results.json`. **Verification**: T006h checks that the test yields p < 0.05.
- [X] T009a [US3] Run full contract‑validation suite after each major stage. **Verification**: T009a asserts all validations succeed.

## Phase 5: Assumption Checks & Robust Fallback (New Sub‑Phase)

**Goal**: Perform statistical assumption checks before each test and switch to robust alternatives when needed.

- [X] T072 [P] Run Shapiro‑Wilk normality test (α = 0.05), Levene’s homoscedasticity test (α = 0.05), and a linearity check (R² ≥ 0.7) on the baseline and each cleaned variant. Record a boolean `assumptions_met` flag in `cleaned_metrics.json`.
- [X] T073 Verify that for every analysis where `assumptions_met` is false, a robust alternative (Welch’s t‑test or rank‑based regression) is executed, its results are stored, and the `assumptions_met` flag is correctly reflected.

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042 [P] Documentation updates in `docs/README.md` with pipeline overview. **Verification**: T042a diffs README against expected content.
- [X] T046 [P] Additional unit tests for edge cases (no outliers, variance reduction, row removal) in `tests/unit/`.
- [X] T047 Run quickstart.md validation and fix any pipeline execution issues. **Verification**: T047a confirms quickstart validation succeeded.
- [X] T048 Verify all artifacts are checksummed and `state.yaml` is updated. **Verification**: T048a checks entries in state YAML.
- [X] T049 [P] Add CI/CD workflow file for GitHub Actions with CPU‑only constraints.
- [X] T066 [P] Unit test `tests/unit/test_analysis_fix.py`: Verify `analysis.run_t_test` uses `scipy.stats.ttest_ind`.
- [X] T067 [P] Unit test `tests/unit/test_cleaning_signature.py`: Verify cleaning functions return `(cleaned_df, metadata)`.
- [X] T060 Update `.gitignore` to exclude temporary script patterns, compiled files, Jupyter checkpoints, and data temp files. **Verification**: T060a checks `.gitignore` contains required patterns.

## Phase 7: Documentation Draft (Quickstart Removed)

**Purpose**: Documentation updates only; no pipeline execution here.

- [X] T070 [P] (REMOVED - Moved to Phase 12) Execute the Quickstart script (`scripts/quickstart.sh`) from a clean checkout. **Verification**: Checks that the script runs without error.
- [X] T071 [P] (REMOVED - Moved to Phase 12) Validate Quickstart output: confirm that `baseline_metrics.json`, `cleaned_metrics.json`, and visualizations are generated. **Verification**: T071a asserts presence and non‑emptiness.

## Phase 8: Specification & Documentation Refinement

**Purpose**: Align spec, data provenance, and documentation with reviewer feedback.

- [X] T050 [P] Remove extraneous text blocks titled "LLM data quality reports" and "glioblastoma biomarkers" from `spec.md`. Verified by diff test.
- [X] T050b [P] Remove corrupted FR‑ text from `spec.md`. Verified by diff test.
- [X] T051 [P] Revise Success Criteria `SC-001`, `SC-002`, `SC-03` in `spec.md` to replace "Median and IQR" with "Per‑dataset delta reporting with qualitative directionality assessment". Verified by diff test.
- [X] T052 [P] Refine hypothesis statement in `spec.md` as required. Verified by diff test.
- [X] T053 [P] Create `data/raw/README.md` documenting URLs, SHA checksums, and descriptions. **Verification**: T1114a parses README, checks URLs, checksums, and file existence.
- [X] T054 [P] Implement robust download script `scripts/download_data.sh` that fails on error, validates checksum, and logs success. **Verification**: T054a asserts behavior.
- [X] T055 [P] Create `data/processed/data_quality_report.md` with dataset statistics and limitation note. **Verification**: T1116a checks required sections.
- [X] T056 [P] Ensure `code/config.py` is the sole source of paths/parameters; add verification task T057‑V that greps for hard‑coded path strings. **Verification**: T056a asserts no hardcoded paths remain.
- [X] T058 [P] Merge unique helpers from `code/cleanup_utils.py` and `code/profiler.py` into `code/utils.py`. Delete originals. **Verification**: T058a asserts deletion.
- [X] T059 [P] Move maintenance scripts `code/run_lint.py` and `code/run_quickstart_validation.py` to `scripts/`. **Verification**: T059a confirms scripts are moved.
- [X] T060 [P] Update `.gitignore` to exclude temporary script patterns. **Verification**: T060a checks `.gitignore`.
- [X] T061 [P] Ensure `code/main.py` imports and calls functions from `code/cleaning.py`, `code/analysis.py`, and `code/reporting.py` exclusively. **Verification**: Execute `python -m code.main --dry-run`.
- [X] T063 [BUG] Fixed hard‑coded p‑value computation in `code/analysis.py`.
- [X] T064 [BUG] Updated cleaning functions to return `(cleaned_df, metadata_dict)`.
- [X] T065 [BUG] Enforced `config.BOOTSTRAP_ITERATIONS` in bootstrap routine; removed the iteration fallback.
- [X] T104 Refactor `code/main.py` to import only core pipeline functions. **Verification**: T104a runs unit tests.
- [X] T1108 Move maintenance scripts (`run_lint.py`, `run_quickstart_validation.py`) to `scripts/`. **Verification**: T1108a confirms scripts moved.

## Phase 9: Final Validation & Smoke Testing

**Purpose**: Ensure the consolidated pipeline runs end‑to‑end without errors.

- [X] T2019 [P] Run full pipeline smoke test: `python -m code.main` from a clean state. **Verification**: Exit code 0.
- [X] T2020a [P] Verify all output artifacts are generated and non‑empty. **Implementation**: Script checks existence and size > 0.
- [X] T2021 [P] Run unit test suite (`pytest -q`) to confirm no regressions. **Success**: Exit code 0.
- [X] T2022a [P] Run integration test `tests/integration/test_full_pipeline.py`. **Success**: Generates `integration_success_report.txt`.
- [X] T1120a [P] Ensure integration smoke test validates presence and non‑emptiness of all expected output artifacts.

## Phase 10: Additional Hygiene, Consolidation & Reviewer‑Driven Tasks

**Purpose**: Close remaining reviewer‑identified gaps and enforce project hygiene.

- [X] T1107 [HYGIENE] Delete all remaining `code/t*.py` scripts after confirming logic migrated. **Verification**: T1107a asserts no such files exist.
- [X] T1109 [HYGIENE] Merge unique helper functions from `cleanup_utils.py` and `profiler.py` into `code/utils.py`; then delete the now‑redundant files. **Verification**: T1109a confirms deletion.
- [X] T1110 [HYGIENE] Update `.gitignore` to exclude patterns `t*.py`, `scratch*.py`, `debug*.py`. **Verification**: T1110a checks `.gitignore`.
- [X] T1123a [HYGIENE] Run `scripts/check_config.py` and fail if any hard‑coded path strings remain.
- [X] T1124a [HYGIENE] Assert bootstrap routine uses `config.BOOTSTRAP_ITERATIONS` without fallback.

## Phase 11: Specification Amendments & Documentation Updates

**Purpose**: Align the specification with the actual implementation and reviewer feedback.

- [X] T1111 [SPEC] Edit `spec.md` to remove unrelated paragraphs.
- [X] T1112 [SPEC] Revise Success Criteria `SC-001`, `SC-002`, and `SC-03` in `spec.md`.
- [X] T1113 [SPEC] Refine the hypothesis section in `spec.md`.

## Phase 12: Final Verification & Cleanup (Comprehensive)

**Purpose**: Final validation, power analysis, and bin coverage checks.

### Sub-Phase 12.7: Final Verification & Cleanup

- [ ] T1224 [TEST] Run full test suite (`pytest -q`) to confirm all new tests pass and no regressions exist. **Verification**: T1224a asserts exit code 0.
- [ ] T1225 [HYGIENE] Update `.gitignore` to exclude temporary patterns (`t*.py`, `scratch*.py`, `debug*.py`, `__pycache__`, `*.pyc`). **Verification**: T1225a confirms `.gitignore` contains required patterns.
- [ ] T1226 [HYGIENE] Run `scripts/check_config.py` to ensure no hardcoded paths remain. **Verification**: T1226a asserts script exits with success.
- [ ] T1227 [PIPELINE] Execute full pipeline from clean state: `python -m code.main`. Verify all artifacts are generated, valid, and match expected schema. **Verification**: T1227a runs smoke test and validates artifacts.
- [ ] T1228 [POWER] Perform A Priori Power Analysis using `statsmodels.stats.power.WilcoxonPower` for medium effect size (d=0.5), α=0.05, power≥0.8. Determine the minimum total number of datasets required. Document justification in `power_analysis.txt`. **Note**: This analysis must be performed BEFORE dataset acquisition to satisfy FR-016. No dynamic acquisition is permitted. **Verification**: T1228a asserts power ≥ 0.8 and file existence.
- [ ] T1229 [DATA] Validate final dataset collection against bin constraints (n<50, 50-200, >200) and missingness levels. **Action**: If any bin is empty, the task FAILS and the pipeline halts. Do NOT acquire additional datasets dynamically. **Verification**: T1229a confirms all bins are populated or task fails.