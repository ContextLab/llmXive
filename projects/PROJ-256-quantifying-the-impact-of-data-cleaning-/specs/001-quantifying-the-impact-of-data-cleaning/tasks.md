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

- [ ] T1235 Perform a priori power analysis (two‑sample t‑test, d=0.5, α=0.05, power≥0.8, allocation ratio 1:1) BEFORE any dataset acquisition. Record justification in `power_analysis.txt`. **Verification**: T1235‑V checks file existence and that calculated power ≥ 0.8.
- [ ] T1236 [P] Validate that the acquired datasets (from T011) meet the power requirement calculated in T1235. **Dependency**: T011 must complete first. **Verification**: T1236‑V asserts power ≥ 0.8 for the final dataset pool.

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, bug fixes, configuration, and unit tests that MUST be complete before ANY user story can be implemented.

- [X] T1201 Audit `code/` directory to identify all files matching `t0*.py` pattern. **Verification**: Generates `audit/t0_files.txt`; asserts file exists.
- [X] T1202 [US2] Migrate logic from identified `code/t0*.py` scripts into `code/cleaning.py`, `code/analysis.py`, `code/reporting.py`. **Dependency**: T1201 must complete first. **Verification**: Unit tests confirm logic integrity in new modules.
- [X] T1203 [US3] Migrate reporting logic from `code/t0*.py` scripts into `code/reporting.py` and `code/main.py`. **Dependency**: T1201 must complete first. **Verification**: Verifies all functions are callable from `main.py` and produce identical artifacts.
- [X] T1204 Delete all standalone `code/t0*.py` scripts after successful migration. **Verification**: Script `scripts/verify_no_t0_scripts.py` asserts no files matching `t0*.py` remain.
- [X] T056 [P] Ensure `code/config.py` is the sole source of paths/parameters; add verification task T056‑V that greps for hard‑coded path strings.
- [X] T1205 Audit all Python modules in `code/` for hardcoded path strings. **Verification**: Generates `audit/hardcoded_paths.txt`.
- [X] T1206 [BUG] Refactor all identified hardcoded paths to import constants from `code/config.py`. **Dependency**: T007 (file creation), T056 (config population), T1205 (audit). **Verification**: Static analysis confirms no hardcoded paths remain.
- [X] T1207 Update `code/main.py` to load configuration from `code/config.py` and pass paths explicitly. **Verification**: Executes `main.py` with a clean environment to confirm correct path resolution.
- [X] T1213 Audit `code/cleanup_utils.py`, `code/profiler.py` for duplicate functions. **Verification**: Generates diff report of overlapping functions.
- [X] T1214 Consolidate unique logic from `code/cleanup_utils.py` and `code/profiler.py` into `code/utils.py`. Delete originals. **Verification**: Asserts deletion and successful import.
- [X] T1215 Move maintenance scripts `code/run_lint.py` and `code/run_quickstart_validation.py` to `scripts/`. **Verification**: Confirms scripts are moved and executable.
- [X] T1216 Fix `code/analysis.py`: Remove hardcoded `p_value = 0.05`. Replace with `scipy.stats.ttest_ind` (equal_var=False for Welch's) and pass `assumptions_met` flag. **Verification**: Runs analysis on a known dataset and verifies p-values are dynamic.
- [X] T1217 Fix Cohen's d calculation in `code/analysis.py`: Ensure pooled standard deviation is computed from the two specific groups defined by the outcome variable. **Verification**: Unit test compares computed Cohen's d against manual calculation.
- [X] T1218 Update `code/cleaning.py`: Ensure all cleaning functions return `(cleaned_df, metadata_dict)` including `rows_removed`, `missing_before`, `missing_after`, and `variance_reduction`.
- [X] T1219 Fix `code/reporting.py`: Ensure it correctly consumes metadata from cleaning functions and populates `cleaned_metrics.json` with exactly these fields: `rows_removed` (numeric), `missing_before` (numeric), `missing_after` (numeric), `variance_reduction` (numeric). **Dependency**: `contracts/cleaned_metrics.schema.yaml`. **Verification**: Validates `cleaned_metrics.json` schema compliance.
- [ ] T1220 Correct Bootstrap Configuration: Update all bootstrap calls to use `config.BOOTSTRAP_ITERATIONS` with a standard, non‑default iteration count and **NO** fallback. **Verification**: Audits code for absence of fallback logic.
- [X] T1220b Add unit test `tests/unit/test_bootstrap.py::test_iteration_count` to ensure bootstrap receives the correct iteration count. **Verification**: Asserts test passes.
- [X] T1208 Create `tests/` directory structure with subdirectories `unit/`, `integration/`, `contract/`.
- [X] T1209 Create `tests/fixtures/sample_data.csv` with known values.
- [X] T1210 Implement unit tests in `tests/unit/test_cleaning.py` for IQR, imputation, recoding. **Verification**: Asserts pass rate.
- [X] T1211 Implement unit tests in `tests/unit/test_analysis.py` for t-test and regression. **Verification**: Asserts pass rate.
- [X] T1212 Implement integration test `tests/integration/test_full_pipeline.py`. **Verification**: Asserts all artifacts exist.
- [X] T1213a Implement contract‑validation tests in `tests/contract/` for all JSON artifacts. **Verification**: Asserts pass rate.
- [X] T1221 Create `data/raw/README.md` documenting URLs, DOIs, and cryptographic checksums. **Verification**: Validates README completeness.
- [ ] T1223 Update `code/data_loader.py` to fail (non‑zero exit) if download fails. Remove silent fallback. **Verification**: Simulates a failed download and asserts error exit.
- [ ] T1237 [P] Verify robust alternatives are executed when `assumptions_met` is false. **Verification**: T1237‑V forces a violation and checks that Welch’s test or rank‑based regression results are recorded.
- [ ] T1238 [P] Verify that cleaning‑metadata fields (`rows_removed`, `missing_before`, `missing_after`, `variance_reduction`) are written for **every** cleaning variant in `cleaned_metrics.json`. **Verification**: T1238‑V scans the JSON for completeness.
- [X] T1239 [P] Verify README references generated figures (`output/figures/`) per Principle IV. **Verification**: T1239‑V parses README and checks figure links.
- [X] T1247 [P] Verify that all numeric metrics have ≥3‑decimal precision across JSON artefacts. **Verification**: T1247‑V asserts precision for p‑values, CIs, effect sizes, etc.

## Phase 2: User Story 1 – Dataset Acquisition and Baseline Analysis (Priority: P1) 🎯 MVP

**Goal**: Download public datasets from UCI/OpenML and run baseline statistical analyses (t‑tests, linear regressions) on raw, uncleaned data to establish reference metrics (p‑values, 95 % CI, effect sizes)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test in `tests/unit/test_acquisition.py`: Verify `download_dataset` returns a successful HTTP status and non-empty content.
- [ ] T010 [P] [US1] Integration test in `tests/integration/test_baseline.py`: Verify baseline analysis script produces `baseline_metrics.json` with valid p‑values.

### Implementation for User Story 1

- [ ] T011 [US1] Implement acquisition logic in `code/data_loader.py`. Downloads verified UCI URLs, validates checksums, writes raw files to `data/raw/`, **records the verified outcome column name, sample size, and missingness proportion** in `data/processed/dataset_metadata.json`. **Verification**: T011a checks HTTP status; T011b verifies outcome column name is captured; T011c validates SHA256 checksum; T011d records outcome column name.
- [X] T011‑acquire‑bin‑coverage [US1] Ensure at least one dataset per size bin (n < 50, 50‑200, >200) and per missingness level by dynamically acquiring additional public datasets if needed. **Source**: UCI Repository. **Selection**: Alphabetical order. **Verification**: T011‑V confirms bin coverage before pipeline proceeds.
- [ ] T012 [US1] Implement baseline statistical analysis in `code/analysis.py` using `scipy.stats` and `statsmodels`. Writes per‑dataset metrics (p‑value, 95% CI, effect size, `ci_overlap`, `effect_size_change`) to `data/processed/baseline_metrics.json` with ≥3‑decimal precision. **Verification**: T012a runs the analysis; T012b asserts file existence, schema compliance, and precision.
- [ ] T012v [US1] Validate `baseline_metrics.json` against `contracts/baseline_metrics.schema.yaml` after generation. **Verification**: T012v‑V asserts schema compliance.
- [X] T012c‑V Verify that outcome column name is recorded in `dataset_metadata.json` for each dataset (ties to FR‑005/FR‑017).
- [ ] T013 [US1] Add orchestration in `code/main.py` to invoke data acquisition and baseline analysis. **Verification**: T013a runs `python -m code.main --stage baseline` and checks exit code 0.
- [ ] T011b [US1] Verify and record the outcome column name in `dataset_metadata.json` for each dataset (fulfills FR‑005). **Verification**: T011b‑V checks presence and correctness of the outcome field.

## Phase 2.5: Missingness Mechanism Generation (After Dataset Acquisition)

- [ ] T074a [US2] Generate MCAR and MAR missingness mechanisms for each dataset. **Implementation**: Use `sklearn.utils.shuffle` for MCAR and a logistic model for MAR. Store in `data/processed/missingness_mechanisms/`. **Dependency**: T011 must complete first. **Verification**: T074a‑V asserts files exist, correct shape, and reproducible randomness.
- [X] T074a‑V Verify missingness mechanism files exist, have expected dimensions, and were generated with the fixed random seed.
- [ ] T074b [US2] Permute the outcome variable **before** any cleaning step for each dataset under both MCAR and MAR mechanisms. Store permuted raw files in `data/processed/permuted/`. **Verification**: T074b‑V checks existence and correct usage downstream.
- [ ] T074c [US2] Compute permutation‑based false‑positive‑rate (FPR) for each cleaning variant by running the full pipeline on permuted data and recording proportion of significant results after Holm‑Bonferroni. Store in `data/processed/null_fpr_metrics.json`. **Verification**: T074c‑V asserts FPR values between 0 and 1 and flags >0.05.

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
- [ ] T024 [US2] Re‑run t‑tests and linear regressions on each cleaned variant using `code/analysis.py`. **Verification**: T024a asserts per‑variant metric files are generated.
- [ ] T069 [US2] Generate `data/processed/cleaned_metrics.json` aggregating metrics per cleaning strategy per dataset, including `ci_overlap` and `effect_size_change`. **Verification**: T069a runs generation; T069b checks schema, precision, and metadata.
- [X] T1300 [US2] Verify outcome column documentation and recording (FR‑005). **Verification**: T1300‑V confirms outcome column captured in `dataset_metadata.json`.
- [X] T1301 [US2] Validate raw datasets against schema (FR‑009). **Verification**: T1301‑V.
- [X] T1302 [US2] Generate and validate `dataset_metadata.json` (FR‑017). **Verification**: T1302‑V.

## Phase 3.5: Outlier‑Threshold Sweep, Assumption Checks & Robust Fallback (FR‑006)

- [ ] T033a [P] [FR-006] Perform outlier‑threshold sweep using IQR with k = 1.5 and k = 2.0 for each dataset; generate cleaned versions and record per‑threshold metrics in `cleaned_metrics.json`. **Verification**: T033a‑V asserts both thresholds processed and metadata captured.
- [ ] T072 [P] [FR-006] Run assumption checks (Shapiro‑Wilk normality α=0.05, Levene homoscedasticity α=0.05, linearity R²≥0.7) on baseline and each cleaned variant; record `assumptions_met` flag. **Verification**: T072‑V creates `assumption_checks.json` and validates contents.
- [ ] T073 [P] [FR-006] Verify that when `assumptions_met` is false, robust alternatives (Welch’s t‑test or rank‑based regression) are executed and results stored; flag fallback in `cleaned_metrics.json`. **Verification**: T073‑V checks `robust_fallbacks.json` for appropriate entries.
- [ ] T074b [P] [FR-006] Permute outcome variable **before** any cleaning for each dataset under both MCAR and MAR mechanisms; store permuted raw files. **Verification**: T074b‑V ensures permutation occurs prior to cleaning steps.
- [ ] T074c [P] [FR-006] Compute permutation‑based FPR on permuted datasets for each cleaning variant; store results in `null_fpr_metrics.json`. **Verification**: T074c‑V asserts FPR values between 0 and 1 and raises warning if >0.05.

## Phase 4: Multiple‑Comparison Correction (FR‑007)

- [ ] T007a [P] [FR-007] Apply Holm‑Bonferroni correction across **all** cleaning‑variant p‑values **within each dataset**; record adjusted p‑values in `cleaned_metrics.json`. **Verification**: T007a‑V asserts adjusted p‑values exist and family‑wise error rate ≤ 0.05.

## Phase 5: Bootstrap Variance Estimation (FR‑014)

- [ ] T031 [US3] Perform bootstrap variance estimation for each cleaned variant with `config.BOOTSTRAP_ITERATIONS` (default ≥ 1000). Store bootstrap confidence intervals in `data/processed/bootstrap_metrics.json`. **Verification**: T031b checks that the bootstrap routine was called with exactly `config.BOOTSTRAP_ITERATIONS` and that no fallback reduction occurs.

## Phase 6: Sensitivity Analysis (FR‑008)

- [ ] T008a [US2] Perform stratified sensitivity analysis across size bins (n < 50, 50‑200, >200) and missingness levels (≤5 %, ≤10 %, >10 %). Input from `data/processed/missingness_mechanisms/`. **Verification**: T008a‑V produces `sensitivity_summary.json` summarizing bin coverage and asserts each bin contains ≥1 dataset.

## Phase 7: Metrics Comparison & Reporting (US‑003)

- [ ] T040 [US3] Create `ComparisonReport` entity and write `data/processed/comparison_report.json` aggregating all delta metrics, CI overlap, effect‑size changes, and FPR values across datasets. **Verification**: T040‑V validates against `contracts/comparison_report.schema.yaml`.
- [X] T034 [US3] Generate forest plot of p‑value shifts (`output/figures/pvalue_shifts_forest.png`). **Verification**: T034a checks file existence.
- [X] T035 [US3] Generate heatmap of CI‑width changes (`output/figures/ci_width_heatmap.png`). **Verification**: T035a checks file existence.
- [X] T041 [US3] Generate final report `output/reports/final_report.md`.
- [X] T041-Verify [US3] Verify that `final_report.md` contains references to `output/figures/pvalue_shifts_forest.png` and `output/figures/ci_width_heatmap.png`. **Verification**: T041-Verify‑V asserts string presence.
- [X] T1303 [US3] Verify per‑dataset delta fields (`p_value_delta`, `direction`, `ci_overlap`, `effect_size_change`) exist and are correctly typed. **Verification**: T1303‑V.
- [X] T1304 [US3] Verify all numeric metrics have ≥3‑decimal precision across JSON artefacts. **Verification**: T1304‑V.

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

- [X] T042 [P] Documentation updates in `docs/README.md` with pipeline overview. **Verification**: T042a diffs README against expected content.
- [X] T046 [P] Additional unit tests for edge cases (no outliers, variance reduction, row removal) in `tests/unit/`.
- [X] T047 Run quickstart.md validation and fix any pipeline execution issues. **Verification**: T047a confirms quickstart validation succeeded.
- [X] T047b [P] Verify full quickstart end‑to‑end workflow runs without errors.
- [X] T048 Verify all artefacts are checksummed and `state.yaml` is updated. **Verification**: T048a checks entries in state YAML.
- [X] T049 [P] Add CI/CD workflow file for GitHub Actions with CPU‑only constraints.
- [X] T067 [P] Unit test `tests/unit/test_cleaning_signature.py`: Verify cleaning functions return `(cleaned_df, metadata)`.
- [X] T060 Update `.gitignore` to exclude temporary script patterns, compiled files, Jupyter checkpoints, and data temp files. **Verification**: T060a checks `.gitignore` contains required patterns.
- [X] T1224 [TEST] Run full test suite (`pytest -q`) to confirm all new tests pass and no regressions exist. **Verification**: T1224‑V asserts exit code 0.
- [X] T1226 [HYGIENE] Run `scripts/check_config.py` to ensure no hard‑coded paths remain. **Verification**: T1226‑V asserts script exits with success.
- [X] T1107 [HYGIENE] Delete all remaining `code/t*.py` scripts after confirming logic migrated. **Verification**: T1107a asserts no such files exist.
- [X] T1110 [HYGIENE] Update `.gitignore` to exclude patterns `t*.py`, `scratch*.py`, `debug*.py`. **Verification**: T1110a checks `.gitignore`.
- [X] T1123a [HYGIENE] Run `scripts/check_config.py` and fail if any hard‑coded path strings remain.
- [X] T1124a [HYGIENE] Assert bootstrap routine uses `config.BOOTSTRAP_ITERATIONS` without fallback.

## Phase 14: Final Verification & Cleanup (Comprehensive)

- [X] T2019 [P] Run full pipeline smoke test: `python -m code.main` from a clean state. **Verification**: Exit code 0.
- [X] T2021 [P] Run unit test suite (`pytest -q`) to confirm no regressions. **Success**: Exit code 0.
- [X] T2022a [P] Run integration test `tests/integration/test_full_pipeline.py`. **Success**: Generates `integration_success_report.txt`.
- [X] T1227 [PIPELINE] Execute full pipeline from clean state: `python -m code.main`. Verify all artifacts are generated, valid, and match expected schema. **Verification**: T1227a runs smoke test and validates artifacts.