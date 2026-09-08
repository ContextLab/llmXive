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
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pytest, jsonschema)
- [X] T003 Configure linting and formatting tools (ruff/black) in code/
- [X] T004 Create `code/config.py` with constants for seeds, paths, and `BOOTSTRAP_ITERATIONS` (defaulting to a sufficient number of iterations for robust estimation).
- [X] T005 Create `code/utils.py` with `pin_random_seed(seed: int)` and `compute_file_checksum(filepath: str) -> str` (SHA256). **Verification**: T005a asserts checksum recorded in `state/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-.yaml` and verified against raw files.
- [X] T005a Verify checksums in state YAML match raw data files.
- [X] T006 Create `code/utils.py` with `setup_logging(log_level: str)`.
- [X] T007 Setup environment configuration management in `code/config.py` with env vars for DATASET_URLS, OUTPUT_PATH, RANDOM_SEED, BOOTSTRAP_ITERATIONS.
- [X] T1225 [P] Create `.gitignore` with required patterns (`__pycache__/`, `*.pyc`, `data/raw/`, `data/processed/*.tmp`, `t*.py`, `scratch*.py`, `debug*.py`, `*.egg-info/`, `.env`). **Verification**: T1225‑V asserts required patterns are present.
- [X] T1225‑V Verify that `.gitignore` contains all required patterns.

## Phase 0.5: Pre‑Acquisition Power Analysis

- [ ] T1235 [P] Perform a priori power analysis (two-sample t-test, d=0.5, α=0.05, power≥0.8, allocation ratio 1:1) BEFORE any dataset acquisition. Record justification in `power_analysis.txt`. **Verification**: T1235‑V checks file existence and that calculated power ≥ 0.8.
- [ ] T1235‑V Verify `power_analysis.txt` exists and reports power ≥ 0.8 prior to any dataset download.
- [X] T1236 [P] Validate that the acquired datasets (from T011) meet the power requirement calculated in T1235. **Verification**: T1236‑V asserts power ≥ 0.8 for the final dataset pool.

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, bug fixes, configuration, and unit tests that MUST be complete before ANY user story can be implemented.

- [X] T1201 Audit `code/` directory to identify all files matching `t0*.py` pattern. **Verification**: Generates `audit/t0_files.txt`; asserts file exists.
- [X] T1202 [US2] Migrate logic from identified `code/t0*.py` scripts into `code/cleaning.py`, `code/analysis.py`, `code/reporting.py`. **Dependency**: T1201 must complete first. **Verification**: Unit tests confirm logic integrity in new modules.
- [X] T1203 [US3] Migrate reporting logic from `code/t0*.py` scripts into `code/reporting.py` and `code/main.py`. **Dependency**: T1201 must complete first. **Verification**: Verifies all functions are callable from `main.py` and produce identical artifacts.
- [X] T1204 Delete all standalone `code/t0*.py` scripts after successful migration. **Verification**: Script `scripts/verify_no_t0_scripts.py` asserts no files matching `t0*.py` remain.
- [X] T056 [P] Ensure `code/config.py` is the sole source of paths/parameters; add verification task T056‑V that greps for hard‑coded path strings. **Verification**: T056a asserts no hardcoded paths remain in codebase.
- [X] T1205 Audit all Python modules in `code/` for hardcoded path strings. **Verification**: Generates `audit/hardcoded_paths.txt`.
- [X] T1206 [BUG] Refactor all identified hardcoded paths to import constants from `code/config.py`. **Dependency**: T007 (file creation), T056 (config population), T1205 (audit). **Verification**: Static analysis confirms no hardcoded paths remain.
- [X] T1207 Update `code/main.py` to load configuration from `code/config.py` and pass paths explicitly. **Verification**: Executes `main.py` with a clean environment to confirm correct path resolution.
- [X] T1213 Audit `code/cleanup_utils.py`, `code/profiler.py` for duplicate functions. **Verification**: Generates diff report of overlapping functions.
- [X] T1214 Consolidate unique logic from `code/cleanup_utils.py` and `code/profiler.py` into `code/utils.py`. Delete originals. **Verification**: Asserts deletion and successful import.
- [X] T1215 Move maintenance scripts `code/run_lint.py` and `code/run_quickstart_validation.py` to `scripts/`. **Verification**: Confirms scripts are moved and executable.
- [X] T1216 Fix `code/analysis.py`: Remove hardcoded `p_value = 0.05`. Replace with `scipy.stats.ttest_ind` (equal_var=False for Welch's) and pass `assumptions_met` flag. **Verification**: Runs analysis on a known dataset and verifies p-values are dynamic.
- [X] T1217 Fix Cohen's d calculation in `code/analysis.py`: Ensure pooled standard deviation is computed from the two specific groups defined by the outcome variable. **Verification**: Unit test compares computed Cohen's d against manual calculation.
- [X] T1218 Update `code/cleaning.py`: Ensure all cleaning functions return `(cleaned_df, metadata_dict)` including `rows_removed`, `missing_before`, `missing_after`, and `variance_reduction`. **Verification**: Unit tests confirm metadata return.
- [ ] T1219 Fix `code/reporting.py`: Ensure it correctly consumes metadata from cleaning functions and populates `cleaned_metrics.json` with exactly these fields: `rows_removed` (numeric), `missing_before` (numeric), `missing_after` (numeric), `variance_reduction` (numeric). **Dependency**: `contracts/cleaned_metrics.schema.yaml`. **Verification**: Validates `cleaned_metrics.json` schema compliance.
- [ ] T1220 Correct Bootstrap Configuration: Update all bootstrap calls to use `config.BOOTSTRAP_ITERATIONS` with a standard, non‑default iteration count and **NO** fallback. **Verification**: Audits code for absence of fallback logic.
- [X] T1220b Add unit test `tests/unit/test_bootstrap.py::test_iteration_count` to ensure bootstrap receives the correct iteration count. **Verification**: Asserts test passes.
- [X] T1208 Create `tests/` directory structure with subdirectories `unit/`, `integration/`, `contract/`.
- [X] T1209 Create `tests/fixtures/sample_data.csv` with known values.
- [X] T1210 Implement unit tests in `tests/unit/test_cleaning.py` for IQR, imputation, recoding. **Verification**: Asserts pass rate.
- [X] T1211 Implement unit tests in `tests/unit/test_analysis.py` for t-test and regression. **Verification**: Asserts pass rate.
- [X] T1212 Implement integration test `tests/integration/test_full_pipeline.py`. **Verification**: Asserts all artifacts exist.
- [X] T1213a Implement contract‑validation tests in `tests/contract/` for all JSON artifacts. **Verification**: Asserts pass rate.
- [X] T1221 Create `data/raw/README.md` documenting URLs, DOIs, and cryptographic checksums. **Verification**: Validates README completeness.
- [ ] T1223 Update `code/data_loader.py` to fail (non‑zero exit) if download fails. Remove silent fallback. **Verification**: Simulates failed download and asserts error exit.
- [ ] T1236 [P] Verify that all stochastic functions respect `config.RANDOM_SEED`. **Verification**: T1236‑V runs a deterministic seed test across modules.
- [X] T1237 [P] Verify robust alternatives are executed when `assumptions_met` is false. **Verification**: T1237‑V forces a violation and checks that Welch’s test or rank‑based regression results are recorded.
- [ ] T1238 [P] Verify that cleaning‑metadata fields (`rows_removed`, `missing_before`, `missing_after`, `variance_reduction`) are written for **every** cleaning variant in `cleaned_metrics.json`. **Verification**: T1238‑V scans the JSON for completeness.
- [X] T1239 [P] Verify README references generated figures (`output/figures/`) per Principle IV. **Verification**: T1239‑V parses README and checks figure links.
- [X] T1247 [P] Verify that all numeric metrics have ≥3‑decimal precision across JSON artefacts. **Verification**: T1247‑V asserts precision for p‑values, CIs, effect sizes, etc.

## Phase 2: User Story 1 – Dataset Acquisition and Baseline Analysis (Priority: P1) 🎯 MVP

**Goal**: Download public datasets from UCI/OpenML and run baseline statistical analyses (t‑tests, linear regressions) on raw, uncleaned data to establish reference metrics (p‑values, 95 % CI, effect sizes)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test in `tests/unit/test_acquisition.py`: Verify `download_dataset` returns a successful HTTP status and non-empty content.
- [ ] T010 [P] [US1] Integration test in `tests/integration/test_baseline.py`: Verify baseline analysis script produces `baseline_metrics.json` with valid p‑values.

### Implementation for User Story 1

- [ ] T011 [US1] Implement acquisition logic in `code/data_loader.py`. Downloads verified UCI URLs, validates checksums, writes raw files to `data/raw/`, **records the verified outcome column name, sample size, and missingness proportion** in `data/processed/dataset_metadata.json`. **Verification**: T011a checks HTTP status; T011b validates SHA256 checksum; T011c confirms outcome column recorded.
- [X] T011‑acquire‑bin‑coverage [US1] Ensure at least one dataset per size bin (n < 50, 50‑200, >200) and per missingness level by dynamically acquiring additional public datasets if needed. **Source**: UCI Repository. **Selection**: Alphabetical order. **Verification**: T011‑V confirms bin coverage before pipeline proceeds.
- [ ] T012 [US1] Implement baseline statistical analysis in `code/analysis.py` using `scipy.stats` and `statsmodels`. Writes per‑dataset metrics (p‑value, 95% CI, effect size, `ci_overlap`, `effect_size_change`) to `data/processed/baseline_metrics.json` with ≥3‑decimal precision. **Verification**: T012a runs the analysis; T012b asserts file existence, schema compliance, and precision.
- [ ] T012a Verify `baseline_metrics.json` contains required fields and numeric precision (≥3‑decimal).
- [ ] T012b Verify `baseline_metrics.json` schema compliance.
- [X] T012c‑V Verify that outcome column name is recorded in `dataset_metadata.json` for each dataset (ties to FR‑005/FR‑017).
- [ ] T013 [US1] Add orchestration in `code/main.py` to invoke data acquisition and baseline analysis. **Verification**: T013a runs `python -m code.main --stage baseline` and checks exit code 0.

## Phase 2.5: Missingness Mechanism Generation (After Dataset Acquisition)

- [ ] T074a [US2] Generate MCAR and MAR missingness mechanisms for each dataset. **Implementation**: Use `sklearn.utils.shuffle` for MCAR and a logistic model for MAR. Store in `data/processed/missingness_mechanisms/`. **Dependency**: T011 must complete first. **Verification**: T074a‑V asserts files exist, correct shape, and reproducible randomness.
- [X] T074a‑V Verify missingness mechanism files exist, have expected dimensions, and were generated with the fixed random seed.

## Phase 3: User Story 2 – Systematic Cleaning Strategy Application (Priority: P1)

**Goal**: Apply three cleaning strategies systematically (IQR outlier removal, mean/median/KNN imputation, categorical recoding) and re‑run identical statistical tests on each cleaned variant

### Implementation for User Story 2

- [X] T017 [US2] Implement function `apply_iqr_outlier_removal(df, k=1.5)` in `code/cleaning.py`. Logs rows removed; flags if ≥50% rows removed. **Verification**: T017a unit‑tests correct removal and metadata.
- [X] T018 [US2] Implement function `apply_mean_imputation(df, columns)` in `code/cleaning.py`. Validates zero missing values; flags variance reduction ≥20%. **Verification**: T018a unit‑test.
- [X] T019 [US2] Implement function `apply_median_imputation(df, columns)` in `code/cleaning.py`. **Verification**: T019a unit‑test.
- [X] T020 [US2] Implement function `apply_knn_imputation(df, columns, k=5)` in `code/cleaning.py`. **Verification**: T020a unit‑test.
- [X] T021 [US2] Implement categorical recoding: nominal (≤10 categories) → one‑hot; ordinal/large (>10) → integer label encoding. Return `(cleaned_df, metadata_dict)`. **Verification**: T021a unit‑test validates encoding and metadata.
- [X] T022 [US2] Write cleaned datasets to `data/processed/` with strategy‑specific filenames. **Verification**: T022a checks naming and checksums.
- [X] T023 [US2] Ensure cleaning functions return `(cleaned_df, metadata_dict)` with `rows_removed` and `missing_values_remaining`. **Verification**: T023a asserts metadata fields.
- [ ] T024 [US2] Re‑run t‑tests and linear regressions on each cleaned variant using `code/analysis.py`.
- [ ] T069 [US2] Generate `data/processed/cleaned_metrics.json` aggregating metrics per cleaning strategy per dataset, including `ci_overlap` and `effect_size_change`. **Verification**: T069a runs generation; T069b checks schema, precision, and metadata.
- [X] T1300 [US2] Verify outcome column documentation and recording (FR‑005). **Verification**: T1300‑V confirms outcome column captured in `dataset_metadata.json`.
- [X] T1301 [US2] Validate raw datasets against schema (FR‑009). **Verification**: T1301‑V.
- [X] T1302 [US2] Generate and validate `dataset_metadata.json` (FR‑017). **Verification**: T1302‑V.

## Phase 4: Permutation‑Based FPR Estimation (Priority: P1)

- [ ] T074b [US2] For each dataset, **permute the outcome variable BEFORE any cleaning step** (preserving covariate structure) under both MCAR and MAR missingness mechanisms. Then apply **all** cleaning variants to each permuted dataset and run the full analysis pipeline. Store intermediate results as needed.
- [ ] T074c Compute the proportion of permutations that yield a significant result (p < 0.05) after Holm‑Bonferroni correction for each cleaning variant. Record this proportion as the estimated False‑Positive‑Rate in `data/processed/null_fpr_metrics.json`. **Action**: If FPR > 0.05, log warning and mark variant as invalid. **Verification**: T074c‑V checks that `null_fpr_metrics.json` exists, values are ≥0 and ≤1, and that any variant exceeding 0.05 triggers a warning.
- [X] T074d Verify that the permutation of the outcome occurs **prior** to any cleaning operation for every variant. **Verification**: T074d‑V scans `logs/pipeline.log` for pattern 'PERMUTE_BEFORE_CLEANING=true' and asserts no cleaning step precedes the permutation step.

## Phase 5: Assumption Checks & Robust Fallback (New Sub‑Phase)

- [ ] T072 [P] Run Shapiro‑Wilk normality test (α = 0.05), Levene’s homoscedasticity test (α = 0.05), and a linearity check (R² ≥ 0.7) on the baseline and each cleaned variant. Record a boolean `assumptions_met` flag in `cleaned_metrics.json`.
- [ ] T073 [P] Verify that for every analysis where `assumptions_met` is false, a robust alternative (Welch’s t‑test or rank‑based regression) is executed, its results are stored, and the `assumptions_met` flag is correctly reflected. **Verification**: T073‑V.

## Phase 6: Multiple‑Comparison Correction

- [ ] T007a [US3] Apply Holm‑Bonferroni correction across **all** cleaning‑variant p‑values **within each dataset** to control the family‑wise error rate at **α = 0.05**. Record adjusted p‑values in `cleaned_metrics.json`. **Verification**: T007b asserts claim compliance.

## Phase 7: Bootstrap Variance Estimation

- [ ] T031 [US3] Perform bootstrap variance estimation for each cleaned variant with `config.BOOTSTRAP_ITERATIONS` (default set to a sufficient number of iterations). Store bootstrap confidence intervals in `data/processed/bootstrap_metrics.json`. **Verification**: T045a audits code for absence of fallback.
- [X] T045a Verify that bootstrap routines do not contain fallback iteration counts.
- [ ] T2062-Verify [US3] Verify that NO fallback logic exists for bootstrap iterations (strictly 1000 or more). **Verification**: Static analysis asserts no conditional reduction of `BOOTSTRAP_ITERATIONS`.

## Phase 8: Sensitivity Analysis (US‑002)

- [ ] T008a [US2] Perform stratified sensitivity analysis across size bins (n < 50, 50‑200, >200) and missingness levels ([deferred], ≤5%, ≤10%, >10%). **Input**: `data/processed/missingness_mechanisms/` from T074a. **Verification**: T008b checks that each bin contains ≥1 dataset.
- [ ] T008a-Link [US2] Verify that the sensitivity analysis explicitly consumes the generated missingness mechanism files from T074a. **Verification**: T008a-Link-V asserts file usage in logs.
- [X] T1305 [US3] Verify after automatic acquisition that every size‑bin and missingness‑level contains at least one dataset. **Verification**: T1305‑V aborts pipeline if any bin is empty.

## Phase 9: Metrics Comparison & Reporting (US‑003)

- [ ] T027 [US3] Implement metrics comparison in `code/reporting.py`. Computes `ci_overlap` (proportion of overlapping intervals) and `effect_size_change` (absolute change). Stores results in `baseline_metrics.json` and `cleaned_metrics.json` with ≥3‑decimal precision. **Dependency**: T012, T024.
- [X] T028 [US3] Add claim verification placeholder (no external reference required).
- [X] T029 [US3] Implement missingness‑rate binning with thresholds (0 %, ≤5 %, ≤10 %, >10 %). Logs warning for empty bins.
- [X] T030 [US3] Implement dataset‑size binning (n<50, 50‑200, >200). Logs warning for empty bins.
- [ ] T033a [US3] Perform outlier‑threshold sweep for k ∈ {1.5, 2.0}; store per‑threshold metrics in `data/processed/outlier_threshold_sweep_report.json`.
- [X] T033b [US3] Compute inconsistency rate per outlier threshold; append to sweep report.
- [ ] T033c [US3] Verify `outlier_threshold_sweep_report.json` exists and is well‑formed.
- [X] T034 [US3] Generate forest plot of p‑value shifts (`output/figures/pvalue_shifts_forest.png`). **Verification**: T034a checks file existence.
- [X] T034-Ref [US3] Update `final_report.md` (T041) to explicitly reference the forest plot path. **Verification**: T034-Ref-V checks report content.
- [X] T035 [US3] Generate heatmap of CI‑width changes (`output/figures/ci_width_heatmap.png`). **Verification**: T035a checks file existence.
- [X] T035-Ref [US3] Update `final_report.md` (T041) to explicitly reference the heatmap path. **Verification**: T035-Ref-V checks report content.
- [X] T036 [US3] Implement per‑dataset p‑value shift reporting.
- [X] T038 [US3] Implement per‑dataset effect‑size change reporting.
- [X] T039 [US3] Log excluded datasets (>80% missing outcome) with warning; record reason in `data_quality_report.md`.
- [ ] T040 [US3] Create `ComparisonReport` entity and write `data/processed/comparison_report.json`.
- [X] T041 [US3] Generate final report `output/reports/final_report.md`.
- [X] T041-Verify [US3] Verify that `final_report.md` contains references to `output/figures/pvalue_shifts_forest.png` and `output/figures/ci_width_heatmap.png`. **Verification**: T041-Verify-V asserts string presence.
- [X] T1303 [US3] Verify per‑dataset delta fields (`p_value_delta`, `direction`, `ci_overlap`, `effect_size_change`) exist and are correctly typed. **Verification**: T1303‑V.
- [X] T1304 [US3] Verify all numeric metrics have ≥3‑decimal precision across JSON artefacts. **Verification**: T1304‑V.

## Phase 10: Polish & Cross‑Cutting Concerns

- [X] T042 [P] Documentation updates in `docs/README.md` with pipeline overview. **Verification**: T042a diffs README against expected content.
- [X] T046 [P] Additional unit tests for edge cases (no outliers, variance reduction, row removal) in `tests/unit/`.
- [X] T047 Run quickstart.md validation and fix any pipeline execution issues. **Verification**: T047a confirms quickstart validation succeeded.
- [X] T048 Verify all artefacts are checksummed and `state.yaml` is updated. **Verification**: T048a checks entries in state YAML.
- [X] T049 [P] Add CI/CD workflow file for GitHub Actions with CPU‑only constraints.
- [ ] T066 [P] Unit test `tests/unit/test_analysis_fix.py`: Verify `analysis.run_t_test` uses `scipy.stats.ttest_ind`.
- [X] T067 [P] Unit test `tests/unit/test_cleaning_signature.py`: Verify cleaning functions return `(cleaned_df, metadata)`.
- [X] T060 Update `.gitignore` to exclude temporary script patterns, compiled files, Jupyter checkpoints, and data temp files. **Verification**: T060a checks `.gitignore` contains required patterns.
- [X] T1224 [TEST] Run full test suite (`pytest -q`) to confirm all new tests pass and no regressions exist. **Verification**: T1224‑V asserts exit code 0.
- [ ] T1226 [HYGIENE] Run `scripts/check_config.py` to ensure no hardcoded paths remain. **Verification**: T1226‑V asserts script exits with success.
- [X] T1107 [HYGIENE] Delete all remaining `code/t*.py` scripts after confirming logic migrated. **Verification**: T1107a asserts no such files exist.
- [ ] T1109 [HYGIENE] Merge unique helper functions from `cleanup_utils.py` and `profiler.py` into `code/utils.py`; then delete the now‑redundant files. **Verification**: T1109a confirms deletion and successful import.
- [X] T1110 [HYGIENE] Update `.gitignore` to exclude patterns `t*.py`, `scratch*.py`, `debug*.py`. **Verification**: T1110a checks `.gitignore`.
- [ ] T1123a [HYGIENE] Run `scripts/check_config.py` and fail if any hard‑coded path strings remain.
- [ ] T1124a [HYGIENE] Assert bootstrap routine uses `config.BOOTSTRAP_ITERATIONS` without fallback.

## Phase 11: Specification Amendments & Documentation Updates

- [X] T1111 [SPEC] Edit `spec.md` to remove unrelated paragraphs.
- [X] T1112 [SPEC] Revise Success Criteria `SC-001`, `SC-002`, `SC-003` in `spec.md`.
- [X] T1113 [SPEC] Refine the hypothesis section in `spec.md`.
- [X] T2058-Update [SPEC] Update `spec.md` to replace `[deferred]` placeholders in FR-008 and Assumptions with concrete values ([deferred], ≤5%, ≤10%, >10%) to align with Plan and Tasks. **Verification**: Diff check confirms replacement.

## Phase 12: Final Verification & Cleanup (Comprehensive)

- [X] T2019 [P] Run full pipeline smoke test: `python -m code.main` from a clean state. **Verification**: Exit code 0.
- [X] T2020a [P] {{claim:c_02073a94}} (Wikidata Q126592664, {{claim:c_60945306}} (Wikipedia: Ping (networking utility), https://en.wikipedia.org/wiki/Ping_(networking_utility))"))]) **Implementation**: Script checks existence and size > 0.
- [X] T2021 [P] Run unit test suite (`pytest -q`) to confirm no regressions. **Success**: Exit code 0.
- [X] T2022a [P] Run integrationtest`tests/integration/test_full_pipeline.py`. **Success**: Generates `integration_success_report.txt`.
- [X] T1120a [P] Ensure integration smoke test validates presence and non‑emptiness of all expected output artifacts.
- [X] T1227 [PIPELINE] Execute full pipeline from clean state: `python -m code.main`. Verify all artifacts are generated, valid, and match expected schema. **Verification**: T1227a runs smoke test and validates artifacts.

## Phase 13: Revision & Hygiene Fixes (Addressing Reviewer Concerns)

**Purpose**: Address specific structural, data quality, and implementation completeness issues raised in prior research-stage reviews.

- [ ] T2051 [HYGIENE] Centralize Configuration: Audit all Python modules to ensure `code/config.py` is the *only* source for paths and parameters. Remove any hardcoded strings like `"data/raw/"` or `"output/figures/"` found in legacy scripts or modules. **Verification**: `scripts/check_config.py` exits with failure if any hardcoded paths are detected.
- [ ] T2052 [TEST] Add Comprehensive Test Suite: Create `tests/` directory structure if missing. Implement unit tests for core logic: `tests/unit/test_cleaning.py` (verify outlier removal counts, imputation zero-missing), `tests/unit/test_analysis.py` (verify p-value calculation via `scipy`, Cohen's d via pooled std), and `tests/integration/test_full_pipeline.py` (run full pipeline from clean state). **Core Logic Scope**: Functions in `code/cleaning.py`, `code/analysis.py`, `code/reporting.py`. **Verification**: `pytest -q` passes with [deferred] coverage on core logic functions.
- [ ] T2053 [HYGIENE] Remove Redundant Files: Audit `code/cleanup_utils.py`, `code/utils.py`, and `code/profiler.py`. Merge unique logic into `code/utils.py` or `code/main.py` as appropriate. Delete `code/cleanup_utils.py`, `code/profiler.py`, and any other redundant utility files. **Verification**: `scripts/verify_no_redundant_utils.py` asserts the redundant files are deleted and imports succeed.
- [ ] T2054 [DATA] Document Data Provenance: Update `data/raw/README.md` to explicitly list the exact URLs, DOIs, and expected SHA-256 checksums for all datasets used (e.g., UCI Wine, UCI Breast Cancer). **Action**: Programmatically generate/lookup DOIs and checksums if not present. Include the executable command or script path (`code/data_loader.py`) to download them. **Verification**: `scripts/verify_data_readme.py` confirms all required fields are present.
- [X] T2055 [DATA] Create Data Quality Report: Generate `data/processed/data_quality_report.md`. Document the dataset selection process: total datasets attempted, number excluded (with reasons per spec edge cases), and the final sample size. Explicitly state that the sample size is a limitation and that aggregate statistics (median/IQR) are unstable for n < 5. **Verification**: `scripts/verify_data_quality_report.py` confirms file existence and required sections.
- [ ] T2056 [DATA] Enforce Strict Download Failure: Update `code/data_loader.py` to explicitly fail (non-zero exit) if the download from the verified URL fails. Remove any silent fallbacks to mock data or skipping logic. Add a log entry confirming the checksum of the downloaded file matches the expected value. **Verification**: Simulate a failed download (e.g., invalid URL) and assert the script exits with non-zero status and logs the failure.
- [ ] T1225 [HYGIENE] Consolidate Logic: Refactor all logic from `code/t022_save_cleaned_datasets.py`, `code/t023_reanalyze_cleaned_variants.py`, `code/t027_run_comparison.py`, `code/t030_dataset_size_sensitivity.py`, `code/t032_permutation_null_fpr.py`, `code/t033_outlier_threshold_sweep.py`, `code/t034_generate_forest_plot.py`, `code/t035_generate_ci_heatmap.py`, `code/t036_pvalue_shift_reporting.py`, `code/t037_ci_width_reporting.py`, `code/t038_effect_size_reporting.py`, `code/t039_log_excluded_datasets.py`, `code/t040_create_comparison_report.py`, `code/t041_generate_final_report.py`, `code/t044_runtime_profiling.py`, `code/t045_conditional_bootstrap_reduction.py`, and `code/t048_verify_checksums_and_state.py` into their designated canonical modules: `code/cleaning.py`, `code/analysis.py`, and `code/reporting.py`. **Verification**: Script `scripts/verify_logic_migration.py` asserts these functions are importable from the canonical modules and no `t0*.py` files remain. (Note: This task assumes these files exist; if not, it is a no-op or skipped).
- [ ] T1226 [HYGIENE] Run `scripts/check_config.py` and fail if any hard‑coded path strings remain.
- [X] T1107 [HYGIENE] Delete all remaining `code/t*.py` scripts after confirming logic migrated. **Verification**: T1107a asserts no such files exist.
- [ ] T1109 [HYGIENE] Merge unique helper functions from `cleanup_utils.py` and `profiler.py` into `code/utils.py`; then delete the now‑redundant files. **Verification**: T1109a confirms deletion and successful import.
- [X] T1110 [HYGIENE] Update `.gitignore` to exclude patterns `t*.py`, `scratch*.py`, `debug*.py`. **Verification**: T1110a checks `.gitignore`.
- [ ] T1123a [HYGIENE] Run `scripts/check_config.py` and fail if any hard‑coded path strings remain.
- [ ] T1124a [HYGIENE] Assert bootstrap routine uses `config.BOOTSTRAP_ITERATIONS` without fallback.
