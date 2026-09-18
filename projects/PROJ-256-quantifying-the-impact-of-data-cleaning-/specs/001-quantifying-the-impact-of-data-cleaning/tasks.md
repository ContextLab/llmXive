---
description: "Task list template for feature implementation"
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

- [ ] T1235 Perform a priori power analysis (two‑sample t‑test, d=0.5, α=0.05, power≥0.8, allocation ratio 1:1) BEFORE any dataset acquisition. Record justification in `power_analysis.txt`. **Verification**: T1235‑V checks file existence and that calculated power ≥ 0.8. *(Removed [P] tag; must run before Phase 2)*
- [ ] T1235‑V Verify `power_analysis.txt` exists and reports power ≥ 0.8 prior to any dataset download.
- [ ] T1236 Validate that the acquired datasets (from T011) meet the power requirement calculated in T1235. **Verification**: T1236‑V asserts power ≥ 0.8 for the final dataset pool.

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, bug fixes, configuration, and unit tests that MUST be complete before ANY user story can be implemented.

- [X] T1201 Audit `code/` directory to identify all files matching `t0*.py` pattern. **Verification**: Generates `audit/t0_files.txt`; asserts file exists.
- [X] T1202 [US2] Migrate logic from identified `code/t0*.py` scripts into `code/cleaning.py`, `code/analysis.py`, `code/reporting.py`. **Dependency**: T1201 must complete first. **Verification**: Unit tests confirm logic integrity in new modules.
- [X] T1203 [US3] Migrate reporting logic from `code/t0*.py` scripts into `code/reporting.py` and `code/main.py`. **Dependency**: T1201 must complete first. **Verification**: Verifies all functions are callable from `main.py` and produce identical artifacts.
- [X] T1204 Delete all standalone `code/t0*.py` scripts after successful migration. **Verification**: Script `scripts/verify_no_t0_scripts.py` asserts no files matching `t0*.py` remain.
- [X] T056 [P] Ensure `code/config.py` is the sole source of paths/parameters; add verification task T056‑V that greps for hard‑coded path strings.
- [X] T056‑V Verify no hard‑coded path strings remain in the codebase.
- [X] T1205 Audit all Python modules in `code/` for hardcoded path strings. **Verification**: Generates `audit/hardcoded_paths.txt`.
- [X] T1206 [BUG] Refactor all identified hardcoded paths to import constants from `code/config.py`. **Dependency**: T007 (file creation), T056 (config population), T1205 (audit). **Verification**: Static analysis confirms no hardcoded paths remain.
- [X] T1207 Update `code/main.py` to load configuration from `code/config.py` and pass paths explicitly. **Verification**: Executes `main.py` with a clean environment to confirm correct path resolution.
- [X] T1213 Audit `code/cleanup_utils.py`, `code/profiler.py` for duplicate functions. **Verification**: Generates diff report of overlapping functions.
- [X] T1214 Consolidate unique logic from `code/cleanup_utils.py` and `code/profiler.py` into `code/utils.py`. Delete originals. **Verification**: Asserts deletion and successful import.
- [X] T1215 Move maintenance scripts `code/run_lint.py` and `code/run_quickstart_validation.py` to `scripts/`. **Verification**: Confirms scripts are moved and executable.
- [X] T1216 Fix `code/analysis.py`: Remove hardcoded `p_value = 0.05`. Replace with `scipy.stats.ttest_ind` (equal_var=False for Welch's) and pass `assumptions_met` flag. **Verification**: Runs analysis on a known dataset and verifies p-values are dynamic.
- [X] T1217 Fix Cohen's d calculation in `code/analysis.py`: Ensure pooled standard deviation is computed from the two specific groups defined by the outcome variable. **Verification**: Unit test compares computed Cohen's d against manual calculation.
- [X] T1218 Update `code/cleaning.py`: Ensure all cleaning functions return `(cleaned_df, metadata_dict)` including `rows_removed`, `missing_before`, `missing_after`, and `variance_reduction`. **Verification**: Unit tests confirm metadata return.
- [X] T1219 Fix `code/reporting.py`: Ensure it correctly consumes metadata from cleaning functions and populates `cleaned_metrics.json` with exactly the fields `rows_removed`, `missing_before`, `missing_after`, `variance_reduction`. **Verification**: Validates `cleaned_metrics.json` schema compliance. **Status**: Completed.
- [X] T1219‑V Verify `cleaned_metrics.json` contains required metadata fields and passes schema validation.
- [X] T1220 Create `contracts/cleaned_metrics.schema.yaml` defining required metadata fields and numeric precision constraints. **Verification**: T1220‑V validates `cleaned_metrics.json` against this schema.
- [X] T1220‑V Verify `cleaned_metrics.json` conforms to `contracts/cleaned_metrics.schema.yaml`.
- [X] T1221 Add verification that bootstrap routines use `config.BOOTSTRAP_ITERATIONS` without fallback. **Verification**: T1124a‑V (see below) ensures no fallback logic.
- [X] T1222 [P] Add validation step in pipeline to check `cleaned_metrics.json` against its schema after each generation. **Verification**: T1223‑V runs schema validator.
- [X] T1223‑V Verify schema validation of `cleaned_metrics.json` succeeds.
- [X] T1222b Add verification that bootstrap CI precision meets ≥3‑decimal requirement. **Verification**: T031‑V (see below).
- [X] T1208 Create `tests/` directory structure with subdirectories `unit/`, `integration/`, `contract/`.
- [X] T1209 Create `tests/fixtures/sample_data.csv` with known values.
- [X] T1210 Implement unit tests in `tests/unit/test_cleaning.py` for IQR, imputation, recoding. **Verification**: Asserts pass rate.
- [X] T1211 Implement unit tests in `tests/unit/test_analysis.py` for t-test and regression. **Verification**: Asserts pass rate.
- [X] T1212 Implement integration test `tests/integration/test_full_pipeline.py`. **Verification**: Asserts all artefacts exist.
- [X] T1213a Implement contract‑validation tests in `tests/contract/` for all JSON artefacts. **Verification**: Asserts pass rate.
- [X] T1221 Create `data/processed/dataset_metadata.json` documenting outcome column, sample size, missingness proportion. **Verification**: T1221‑V validates against `contracts/dataset.schema.yaml`.
- [X] T1221‑V Verify `dataset_metadata.json` complies with `contracts/dataset.schema.yaml`.
- [X] T1224 [TEST] Run full test suite (`pytest -q`) to confirm all new tests pass and no regressions exist. **Verification**: T1224‑V asserts exit code 0.
- [X] T1226 [HYGIENE] Run `scripts/check_config.py` to ensure no hard‑coded paths remain. **Verification**: T1226‑V asserts script exits with success.
- [X] T1107 [HYGIENE] Delete all remaining `code/t*.py` scripts after confirming logic migrated. **Verification**: T1107a asserts no such files exist.

## Phase 2: User Story 1 – Dataset Acquisition and Baseline Analysis (Priority: P1) 🎯 MVP

**Goal**: Download public datasets from UCI/OpenML and run baseline statistical analyses (t‑tests, linear regressions) on raw, uncleaned data to establish reference metrics (p‑values, 95 % CI, effect sizes)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test in `tests/unit/test_acquisition.py`: Verify `download_dataset` returns a successful HTTP status and non-empty content.
- [X] T010 [P] [US1] Integration test in `tests/integration/test_baseline.py`: Verify baseline analysis script produces `baseline_metrics.json` with valid p‑values.

### Implementation for User Story 1

- [X] T011 Implement acquisition logic in `code/data_loader.py`. Downloads verified UCI URLs, validates checksums, writes raw files to `data/raw/`, **records the verified outcome column name, sample size, and missingness proportion** in `data/processed/dataset_metadata.json`. **Verification**: T011a checks HTTP status; T011b validates SHA256 checksum; T011c confirms outcome column recorded.
- [X] T011‑acquire‑bin‑coverage Ensure at least one dataset per size bin (n < 50, 50‑200, >200) and per missingness level by dynamically acquiring additional public datasets if needed. **Verification**: T011‑V confirms bin coverage before pipeline proceeds.
- [X] T012 Implement baseline statistical analysis in `code/analysis.py` using `scipy.stats` and `statsmodels`. Writes per‑dataset metrics (p‑value, 95% CI, effect size, `ci_overlap`, `effect_size_change`) to `data/processed/baseline_metrics.json` with ≥3‑decimal precision. **Verification**: T012a runs the analysis; T012b asserts file existence, schema compliance, and precision.
- [X] T012a Verify `baseline_metrics.json` contains required fields and numeric precision (≥3‑decimal).
- [X] T012b Verify `baseline_metrics.json` schema compliance.
- [X] T012c‑V Verify that outcome column name is recorded in `dataset_metadata.json` for each dataset.
- [X] T013 Add orchestration in `code/main.py` to invoke data acquisition and baseline analysis. **Verification**: T013a runs `python -m code.main --stage baseline` and checks exit code 0.

## Phase 2.5: Missingness Mechanism Generation (After Dataset Acquisition)

- [X] T074a Generate MCAR and MAR missingness mechanisms for each dataset. **Implementation**: Use `sklearn.utils.shuffle` for MCAR and a logistic model for MAR. Store in `data/processed/missingness_mechanisms/`. **Verification**: T074a‑V asserts files exist, correct shape, and reproducible randomness.
- [X] T074a‑V Verify missingness mechanism files exist, have expected dimensions, and were generated with the fixed random seed.
- [ ] T074b [US2] Permute the outcome variable **before** any cleaning step for each dataset under both MCAR and MAR mechanisms. Store permuted raw files in `data/processed/permuted/`. **Verification**: T074b‑V checks existence and correct usage downstream.
- [ ] T074c [US2] Compute permutation‑based false‑positive‑rate (FPR) for each cleaning variant by running the full pipeline on permuted data and recording proportion of significant results after Holm‑Bonferroni. Store in `data/processed/null_fpr_metrics.json`. **Verification**: T074c‑V asserts FPR values between 0 and 1 and flags >0.05.

## Phase 3: User Story 2 – Systematic Cleaning Strategy Application (Priority: P1)

### Implementation for User Story 2

- [X] T017 Implement function `apply_iqr_outlier_removal(df, k=1.5)` in `code/cleaning.py`. Logs rows removed; flags if ≥50% rows removed. **Verification**: T017a unit‑tests correct removal and metadata.
- [X] T018 Implement function `apply_mean_imputation(df, columns)` in `code/cleaning.py`. Validates zero missing values; flags variance reduction ≥20%. **Verification**: T018a unit‑test.
- [X] T019 Implement function `apply_median_imputation(df, columns)` in `code/cleaning.py`. **Verification**: T019a unit‑test.
- [X] T020 Implement function `apply_knn_imputation(df, columns, k=5)` in `code/cleaning.py`. **Verification**: T020a unit‑test.
- [X] T021 Implement categorical recoding: nominal (≤10 categories) → one‑hot; ordinal/large (>10) → integer label encoding. Return `(cleaned_df, metadata_dict)`. **Verification**: T021a unit‑test validates encoding and metadata.
- [X] T022 Write cleaned datasets to `data/processed/` with strategy‑specific filenames. **Verification**: T022a checks naming and checksums.
- [X] T023 Ensure cleaning functions return `(cleaned_df, metadata_dict)` with `rows_removed` and `missing_values_remaining`. **Verification**: T023a asserts metadata fields.
- [X] T024 Re‑run t‑tests and linear regressions on each cleaned variant using `code/analysis.py`. **Verification**: T024‑V confirms analyses were executed and artefacts regenerated.
- [X] T024V Verify that cleaned‑variant analyses re‑run and produce updated `cleaned_metrics.json`.
- [X] T069 Generate `data/processed/cleaned_metrics.json` aggregating metrics per cleaning strategy per dataset, including `ci_overlap` and `effect_size_change`. **Verification**: T069a runs generation; T069b checks schema, precision, and metadata.
- [X] T1300 Verify outcome column documentation and recording (FR‑005). **Verification**: T1300‑V confirms outcome column captured in `dataset_metadata.json`.
- [X] T1301 Validate raw datasets against schema (FR‑009). **Verification**: T1301‑V.
- [X] T1302 Generate and validate `dataset_metadata.json` (FR‑017). **Verification**: T1302‑V.

## Phase 3.5: Outlier‑Threshold Sweep, Assumption Checks & Robust Fallback (FR‑006)

- [X] T3006 Generate permuted versions of each dataset by shuffling the outcome variable **before** any cleaning step, preserving covariate structure. Store in `data/processed/permuted/`. **Verification**: T3006‑V ensures files are created and correctly permuted.
- [X] [P] T074b For each dataset, **permute the outcome variable BEFORE any cleaning step** (preserving covariate structure) under both MCAR and MAR missingness mechanisms. Then apply **all** cleaning variants to each permuted dataset and run the full analysis pipeline. **Verification**: T074b‑V ensures permutation occurs prior to cleaning.
- [X] T074c Compute the proportion of permutations that yield a significant result (p < 0.05) after Holm‑Bonferroni correction for each cleaning variant. Record this proportion as the estimated False‑Positive‑Rate in `data/processed/null_fpr_metrics.json`. **Verification**: T074c‑V checks file exists, values 0‑1, and warnings for FPR > 0.05.
- [X] T074d Verify that the permutation of the outcome occurs **prior** to any cleaning step for every variant. **Verification**: T074d‑V scans logs for correct ordering.

## Phase 5: Assumption Checks & Robust Fallback

- [X] T072 Run Shapiro‑Wilk normality test (α = 0.05), Levene’s homoscedasticity test (α = 0.05), and a linearity check (R² ≥ 0.7) on the baseline and each cleaned variant. Record a boolean `assumptions_met` flag in `cleaned_metrics.json`. **Verification**: T072‑V asserts flags are recorded.
- [X] T072V Verify assumption checks are performed and results logged in `cleaned_metrics.json`.
- [X] [P] T073 Verify that for every analysis where `assumptions_met` is false, a robust alternative (Welch’s t‑test or rank‑based regression) is executed, its results are stored, and the `assumptions_met` flag is correctly reflected. **Verification**: T073‑V forces a violation and checks fallback execution.

## Phase 5: Bootstrap Variance Estimation (FR‑014)

- [X] T007a Apply Holm‑Bonferroni correction across **all** cleaning‑variant p‑values **within each dataset** to control the family‑wise error rate at **α = 0.05**. Record adjusted p‑values in `cleaned_metrics.json`. **Verification**: T007a‑V asserts claim compliance and that adjusted p‑values satisfy FWER ≤ 0.05.

## Phase 6: Sensitivity Analysis (FR‑008)

- [X] T031 Perform bootstrap variance estimation for each cleaned variant with `config.BOOTSTRAP_ITERATIONS` (default set to a sufficient number of iterations). Store bootstrap confidence intervals in `data/processed/bootstrap_metrics.json`. **Verification**: T031‑V asserts bootstrap CI precision ≥3‑decimal.
- [X] T045a Verify that bootstrap routines do not contain fallback iteration counts. **Verification**: T1124a‑V passes.
- [X] T1221V Verify bootstrap code uses `config.BOOTSTRAP_ITERATIONS` without fallback.

## Phase 7: Metrics Comparison & Reporting (US‑003)

- [X] T008a Perform stratified sensitivity analysis across size bins (n < 50, 50‑200, >200) and missingness levels ([deferred], ≤5 %, ≤10 %, >10 %). **Verification**: T008a‑V checks each bin contains ≥1 dataset.
- [X] T008a‑V Verify that the sensitivity analysis explicitly consumes the generated missingness mechanism files from T074a.
- [X] T1305 Verify after automatic acquisition that every size‑bin and missingness‑level contains at least one dataset. **Verification**: T1305‑V aborts pipeline if any bin is empty.

## Phase 9: Metrics Comparison & Reporting (US‑003)

- [X] T027 Implement metrics comparison in `code/reporting.py`. Computes `ci_overlap` (proportion of overlapping intervals) and `effect_size_change` (absolute change). Stores results in `baseline_metrics.json` and `cleaned_metrics.json` with ≥3‑decimal precision. **Verification**: T027‑V confirms calculations and precision.
- [X] [P] T028 Add claim verification placeholder (no external reference required). **Verification**: T028‑V checks placeholder exists and is logged.
- [X] T028V Verify claim‑verification placeholder is present and logged.
- [X] T029 Implement missingness‑rate binning with thresholds (0 %, ≤5 %, ≤10 %, >10 %). **Verification**: T029‑V asserts binning logic runs.
- [X] T029V Verify missingness‑rate binning executes correctly.
- [X] T030 Implement dataset‑size binning (n<50, 50‑200, >200). **Verification**: T030‑V asserts binning logic runs.
- [X] T030V Verify dataset‑size binning executes correctly.
- [X] T033a Perform outlier‑threshold sweep for k ∈ {1.5, 2.0}; store per‑threshold metrics in `data/processed/outlier_threshold_sweep_report.json`. **Verification**: T033a‑V checks sweep file generation.
- [X] T033aV Verify outlier‑threshold sweep files are produced.
- [X] T033b Compute inconsistency rate per outlier threshold; append to sweep report. **Verification**: T033b‑V validates inconsistency metrics.
- [X] T033bV Verify inconsistency‑rate calculations are written.
- [X] T034 Generate forest plot of p‑value shifts (`output/figures/pvalue_shifts_forest.png`). **Verification**: T034a checks file existence.
- [X] T034‑Ref Update `final_report.md` to explicitly reference the forest plot path. **Verification**: T034‑Ref‑V checks report content.
- [X] T035 Generate heatmap of CI‑width changes (`output/figures/ci_width_heatmap.png`). **Verification**: T035a checks file existence.
- [X] T035‑Ref Update `final_report.md` to explicitly reference the heatmap path. **Verification**: T035‑Ref‑V checks report content.
- [X] T036 Implement per‑dataset p‑value shift reporting. **Verification**: T036‑V ensures report generated and linked in final report.
- [X] T036V Verify per‑dataset p‑value shift report is generated and referenced.
- [X] T038 Implement per‑dataset effect‑size change reporting. **Verification**: T038‑V ensures report generated and linked.
- [X] T038V Verify per‑dataset effect‑size change report is generated and referenced.
- [X] T039 Log excluded datasets (>80% missing outcome) with warning; record reason in `data_quality_report.md`. **Verification**: T039‑V confirms logging and report update.
- [X] T039V Verify excluded‑dataset logging and `data_quality_report.md` update.
- [X] T040 Create `ComparisonReport` entity and write `data/processed/comparison_report.json`. **Verification**: T040‑V validates file creation and schema compliance.
- [X] T040V Verify `comparison_report.json` is created and passes schema validation.
- [X] T041 Generate final report `output/reports/final_report.md`. **Verification**: T041‑V checks that the report contains references to both figure files.
- [X] T1303 Verify per‑dataset delta fields (`p_value_delta`, `direction`, `ci_overlap`, `effect_size_change`) exist and are correctly typed. **Verification**: T1303‑V.
- [X] T1304 Verify all numeric metrics have ≥3‑decimal precision across JSON artefacts. **Verification**: T1304‑V.

## Phase 8: Contract Creation & Validation (Cross‑Cutting)

- [ ] T2100 Create `contracts/dataset.schema.yaml` defining required fields and types. **Verification**: T2100‑V checks file existence and schema validity.
- [ ] T2101 Create `contracts/baseline_metrics.schema.yaml`. **Verification**: T2101‑V.
- [ ] T2102 Create `contracts/cleaned_metrics.schema.yaml`. **Verification**: T2102‑V.
- [ ] T2103 Create `contracts/comparison_report.schema.yaml`. **Verification**: T2103‑V.
- [ ] T2104 Create `contracts/analysis_result.schema.yaml`. **Verification**: T2104‑V.
- [ ] T2105 Create `contracts/null_fpr_metrics.schema.yaml`. **Verification**: T2105‑V.
- [ ] T2106 Create `contracts/bootstrap_metrics.schema.yaml`. **Verification**: T2106‑V.
- [ ] T0090 Validate `data/raw/*` against `contracts/dataset.schema.yaml`. **Verification**: T0090‑V.
- [ ] T0100 Validate `baseline_metrics.json` against `contracts/baseline_metrics.schema.yaml`. **Verification**: T0100‑V.
- [ ] T0110 Validate `cleaned_metrics.json` against `contracts/cleaned_metrics.schema.yaml`. **Verification**: T0110‑V.
- [ ] T0120 Validate `null_fpr_metrics.json` against `contracts/null_fpr_metrics.schema.yaml`. **Verification**: T0120‑V.
- [ ] T0130 Validate `bootstrap_metrics.json` against `contracts/bootstrap_metrics.schema.yaml`. **Verification**: T0130‑V.
- [ ] T0140 Validate `comparison_report.json` against `contracts/comparison_report.schema.yaml`. **Verification**: T0140‑V.
- [ ] T0150 Validate `analysis_result.json` (if produced) against `contracts/analysis_result.schema.yaml`. **Verification**: T0150‑V.

## Phase 9: Citation Validation (Principle II)

- [ ] T0200 Run the citation‑validation script defined in the project constitution to verify that all external claims (dataset provenance, statistical method citations) are accurately referenced. Log the verification outcome to `logs/citation_validation.log`. **Verification**: T0200‑V checks log for successful validation.

## Phase 10: External Benchmark Simulation (FR‑020)

- [ ] T0201 Generate synthetic null‑effect datasets (effect size = 0) matching the size distribution of real data. Run the full cleaning pipeline on these benchmarks. **Verification**: T0201‑V asserts FPR ≤ 0.05 on null data.
- [ ] T0202 Generate synthetic non‑null datasets (Cohen’s d = 0.5) matching the size distribution of real data. Run the full cleaning pipeline and verify effect‑size recovery within ±0.1. **Verification**: T0202‑V asserts recovery tolerance.

## Phase 11: Hypothesis‑Testing on Δ‑Metrics (FR‑021)

- [ ] T0203 Compute paired Wilcoxon signed‑rank test on the vector of `p_value_delta` across all datasets for each cleaning operation. Store test statistic and p‑value in `hypothesis_test_results.json`. **Verification**: T0203‑V checks that at least one cleaning operation yields p < 0.05.

## Phase 12: Data‑Model Implementation (Addressing plan‑root cause)

- [ ] T3000 [P] Implement data‑model classes (`DatasetMetadata`, `BaselineMetrics`, `CleanedMetrics`, `BootstrapMetrics`, etc.) with JSON serialization methods in `code/data_model.py`. **Verification**: T3000‑V asserts objects can be instantiated and serialized without error.
- [ ] T3001 [P] Add unit tests for data‑model serialization and schema conformity in `tests/unit/test_data_model.py`. **Verification**: T3001‑V ensures tests pass and schemas are respected.

## Phase 13: Polish & Cross‑Cutting Concerns (Remaining)

- [X] T042 Documentation updates in `docs/README.md` with pipeline overview. **Verification**: T042a diffs README against expected content.
- [X] T046 Additional unit tests for edge cases (no outliers, variance reduction, row removal). **Verification**: T046‑V runs full test suite and asserts pass.
- [X] T046V Verify edge‑case unit tests exist and pass.
- [X] T047 Run quickstart.md validation and fix any pipeline execution issues. **Verification**: T047a confirms quickstart validation succeeded.
- [X] T047b [P] Verify full quickstart end‑to‑end workflow runs without errors.
- [X] T048 Verify all artefacts are checksummed and `state.yaml` is updated. **Verification**: T048a checks entries in state YAML.
- [X] T049 Add CI/CD workflow file for GitHub Actions with CPU‑only constraints. **Verification**: T049‑V checks workflow file syntax and that it triggers on push.
- [X] T049V Verify CI workflow file is syntactically correct and triggers on push.
- [X] T066 Unit test `tests/unit/test_analysis_fix.py` verifying `analysis.run_t_test` uses `scipy.stats.ttest_ind`. **Verification**: T066‑V runs test and asserts success.
- [X] T066V Verify test for Welch’s test usage passes.
- [X] T067 Unit test `tests/unit/test_cleaning_signature.py` verifying cleaning functions return `(cleaned_df, metadata)`. **Verification**: T067‑V runs test and asserts success.
- [X] T067V Verify cleaning‑signature unit test passes.
- [X] T2002 Run citation‑validation script defined in the project constitution to verify all external claims. **Verification**: T2003‑V ensures script runs and logs success.
- [X] T2003‑V Verify citation‑validation script completed without errors and logged outcomes.
- [X] T3000 Run citation‑validation script (Reference‑Validator) and log outcome. **Verification**: T3000‑V confirms successful run.
- [X] T3000‑V Verify citation‑validation script runs and logs success.
- [X] T2108 Generate synthetic benchmark datasets (null effect and d = 0.5) matching size distribution of real data. **Verification**: T2108‑V confirms files created.
- [X] T2108‑V Verify synthetic benchmark datasets are generated.
- [X] T2109 Run full cleaning pipeline on synthetic benchmarks. **Verification**: T2109‑V confirms pipeline completes.
- [X] T2109‑V Verify pipeline runs on synthetic benchmarks without error.
- [X] T3001 Generate synthetic benchmark datasets (null effect & d = 0.5) with size distribution matching real data. **Verification**: T3001‑V confirms creation.
- [X] T3002 Run full cleaning pipeline on synthetic benchmark datasets. **Verification**: T3002‑V ensures pipeline completes and artefacts are produced.
- [X] T3003 Verify synthetic benchmark results: FPR ≤ 0.05 on null‑effect data and effect‑size recovery within ±0.1 on non‑null data. **Verification**: T3003‑V asserts thresholds met.
- [X] T3004 Compute paired Wilcoxon signed‑rank test on `p_value_delta` across datasets for each cleaning operation. **Verification**: T3004‑V checks `hypothesis_test_results.json` is created.
- [X] T3004‑V Verify `hypothesis_test_results.json` exists and contains correct test results.
- [X] T3005 Verify `hypothesis_test_results.json` conforms to its schema and passes validation. **Verification**: T3005‑V runs schema validator.
- [X] T3005‑V Verify schema compliance of hypothesis test results.
- [X] T3006 Generate permuted outcome datasets prior to any cleaning. **Verification**: T3006‑V ensures permuted files exist and are correctly shuffled.
- [X] T3006‑V Verify permutation files are created correctly.
- [X] T3007 Verify permutation ordering by scanning logs for “permutation before cleaning” messages. **Verification**: T3007‑V asserts correct order.
- [X] T3007‑V Verify logs show correct permutation ordering.
- [X] T3008 Verify bootstrap iteration count is sourced from `config.BOOTSTRAP_ITERATIONS` and no fallback is present. **Verification**: T3008‑V scans code for fallback logic.
- [X] T3008‑V Verify no fallback iteration logic in bootstrap code.

## Phase 11: Specification Amendments & Documentation Updates

- [X] T1111, T1112, T1113 already completed with verification (see above).
- [X] T2058‑Update replaced `[deferred]` placeholders in FR‑008 and assumptions with concrete values (≤5 %, ≤10 %, >10 %). **Verification**: Diff check confirms replacement.
- [X] T2058‑V Verify placeholders have been replaced with concrete values.

## Phase 12: Final Verification & Cleanup (Comprehensive)

- [X] T2019 Run full pipeline smoke test: `python -m code.main` from a clean state. **Verification**: Exit code 0.
- [X] T2020a Execute claim verification script (example placeholder). **Verification**: Checks existence and size > 0.
- [X] T2021 Run unit test suite (`pytest -q`) to confirm no regressions. **Success**: exit code 0.
- [X] T2022a Run integration test `tests/integration/test_full_pipeline.py`. **Success**: Generates `integration_success_report.txt`.
- [X] T1120a Ensure integration smoke test validates presence and non‑emptiness of all expected output artefacts.
- [X] T1227 Execute full pipeline from clean state: `python -m code.main`. Verify all artefacts are generated, valid, and match expected schema. **Verification**: T1227a runs smoke test and validates artefacts.
