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
- [X] T004 Create `code/utils.py` with function `pin_random_seed(seed: int)` for numpy and scipy, ensuring reproducibility. **Dependency**: Requires T008 to be complete first.
- [X] T005 Create `code/utils.py` with function `compute_file_checksum(filepath: str) -> str` for SHA256 validation of data files. **Dependency**: Requires T008 to be complete first.
- [X] T006 Create `code/utils.py` with function `setup_logging(log_level: str)` to initialize the logging infrastructure. **Dependency**: Requires T008 to be complete first.
- [X] T007 Setup environment configuration management in `code/config.py` with env vars for DATASET_URLS, OUTPUT_PATH, RANDOM_SEED, BOOTSTRAP_ITERATIONS. **Dependency**: Requires T008 to be complete first.
- [X] T044 Code cleanup and refactoring (remove dead code, optimize imports). **NOTE**: No `[P]` tag – this task modifies `code/utils.py` which is also written by T004‑T006.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Dataset Acquisition and Baseline Analysis (Priority: P1) 🎯 MVP

**Goal**: Download public datasets from UCI/OpenML and run baseline statistical analyses (t‑tests, linear regressions) on raw, uncleaned data to establish reference metrics (p‑values, 95 % CI, effect sizes)

**Independent Test**: Can be fully tested by executing the dataset download and baseline analysis script against a single dataset, producing a report with p‑values, confidence intervals, and effect sizes for that dataset

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test in `tests/unit/test_acquisition.py`: Verify `download_dataset` returns a successful HTTP status and non-empty content for UCI HAR URL.
- [X] T010 [P] [US1] Integration test in `tests/integration/test_baseline.py`: Verify baseline analysis script produces `baseline_metrics.json` with valid p-values (0 < p < 1) and finite CIs.

### Implementation for User Story 1

- [ ] T011 [US1] Implement acquisition logic in `code/data_loader.py`. Downloads verified UCI URLs, validates checksums, logs fallback to OpenML if unavailable, and writes raw files to `data/raw/`. **Deliverable**: `code/data_loader.py` with functions `download_dataset` and `validate_checksum`.
- [ ] T012 [US1] Implement baseline statistical analysis in `code/analysis.py` using `scipy.stats` (t‑tests) and `statsmodels` (linear regression). Writes per‑dataset metrics (p‑value, 95 % CI, effect size) to `data/processed/baseline_metrics.json` with ≥3‑decimal precision. **Deliverable**: `code/analysis.py` baseline functions.
- [ ] T013 [US1] Add orchestration in `code/main.py` to invoke data acquisition and baseline analysis, ensuring `data/processed/baseline_metrics.json` is produced. **Deliverable**: Updated `code/main.py`.
- [ ] T015 [SPEC‑KICKBACK] Create a spec‑amendment markdown `spec_amendment.md` lowering the required dataset count to ≤5 and documenting the deviation from FR‑001. Add a verification test `tests/unit/test_spec_amendment.py` that asserts the file exists. **Deliverable**: `spec_amendment.md` and test file.

**Checkpoint**: User Story 1 will be fully functional once pending tasks are completed.

---

## Phase 3: User Story 2 - Systematic Cleaning Strategy Application (Priority: P1)

**Goal**: Apply three cleaning strategies systematically (IQR outlier removal, mean/median/KNN imputation, categorical recoding) and re‑run identical statistical tests on each cleaned variant

**Independent Test**: Can be fully tested by applying one cleaning strategy (e.g., IQR outlier removal with k=1.5) to a single dataset and comparing before/after p‑values, which delivers the primary research outcome for that strategy

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T014 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_iqr_outlier_removal` removes rows where |z-score| > k and logs count.
- [X] T015 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_mean_imputation` results in zero missing values in target columns.
- [X] T016 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_categorical_recoding` produces factor‑encoded columns and validates against FR‑002 and FR‑003 requirements.

### Implementation for User Story 2

- [X] T017 [US2] Implement function `apply_iqr_outlier_removal(df, k=1.5)` in `code/cleaning.py`. Logs rows removed; flags if ≥50 % rows removed. **Deliverable**: `code/cleaning.py`.
- [X] T018 [US2] Implement function `apply_mean_imputation(df, columns)` in `code/cleaning.py`. Validates zero missing values; flags variance reduction ≥20 %. **Deliverable**: `code/cleaning.py`.
- [X] T019 [US2] Implement function `apply_median_imputation(df, columns)` in `code/cleaning.py`. Same validation as T018. **Deliverable**: `code/cleaning.py`.
- [X] T020 [US2] Implement function `apply_knn_imputation(df, columns, k=5)` in `code/cleaning.py` using scikit‑learn. Same validation as T018. **Deliverable**: `code/cleaning.py`.
- [X] T021 [US2] Implement function `apply_categorical_recoding(df)` in `code/cleaning.py` with factor encoding. **Deliverable**: `code/cleaning.py`.
- [X] T022 [US2] Write cleaned datasets to `data/processed/` with strategy‑specific filenames (e.g., `dataset_outlier_removed.csv`). **Deliverable**: `code/cleaning.py`.
- [X] T023 [US2] Ensure cleaning functions return `(cleaned_df, metadata_dict)` where metadata includes `rows_removed` and `missing_values_remaining`. **Deliverable**: Updated cleaning functions.
- [X] T024 [US2] Re‑run t‑tests and linear regressions on each cleaned variant using `code/analysis.py`. **Deliverable**: Updated analysis pipeline.
- [X] T069 [US2] Generate `data/processed/cleaned_metrics.json` aggregating metrics per cleaning strategy per dataset. **Dependency**: T024. **Deliverable**: `code/reporting.py` or `code/main.py`.

**Checkpoint**: User Story 2 tasks are now complete and ready for execution.

---

## Phase 4: User Story 3 - Metrics Comparison and Sensitivity Analysis (Priority: P2)

**Goal**: Compute absolute and relative differences between baseline and cleaned results, perform sensitivity analysis across dataset sizes and missingness rate bins, and generate summary visualizations

**Independent Test**: Can be fully tested by running the comparison script on 2 datasets (one cleaned, one baseline) and verifying the difference report contains p‑value shifts, CI width changes, and effect‑size variations with valid numeric values

### Shared Preparatory Tasks

- [ ] T099 [P] Prepare baseline and cleaned metric artifacts for downstream comparison. Verifies existence and schema compliance of `data/processed/baseline_metrics.json` and `data/processed/cleaned_metrics.json`. **Deliverable**: Validation script `code/validation.py`.
- [ ] T1105 [US3] Generate baseline metrics artifact (`baseline_metrics.json`) specifically for US3 by invoking the baseline analysis pipeline (re‑uses existing functions). Ensures US3 can run without prior US1 execution.
- [ ] T1106 [US3] Generate cleaned metrics artifact (`cleaned_metrics.json`) for US3 by invoking the cleaning pipeline on all strategies. Ensures US3 does not depend on US2 execution.

### Tests for User Story 3 (OPTIONAL)

- [X] T090 [P] [US3] Unit test in `tests/unit/test_reporting.py`: Verify `calculate_p_value_shift` returns absolute difference with ≥3‑decimal precision.
- [X] T025 [P] [US3] Unit test in `tests/unit/test_reporting.py`: Verify Benjamini‑Hochberg correction is applied correctly (no reference to non‑existent FR‑007). **Deliverable**: Updated test.
- [X] T026 [P] [US3] Integration test in `tests/integration/test_sensitivity.py`: Verify stratification logic logs warnings for empty bins and proceeds.

### Implementation for User Story 3

- [X] T027 [US3] Implement metrics comparison in `code/reporting.py`. Computes |p_cleaned − p_baseline| (≥3‑decimal), CI width change (≥2‑decimal), effect‑size delta, and inconsistency rate (proportion of datasets where significance status changes). **Dependency**: T1105 & T1106.
- [X] T028 [US3] Add claim verification placeholder (no external reference required). **Deliverable**: `code/reporting.py`.
- [X] T029 [US3] Implement missingness‑rate binning with thresholds (0 %, ≤5 %, ≤10 %, >10 %). Logs warning `"Missingness bin empty: bin <X> has no datasets"`. **Note**: No FR‑008 reference.
- [X] T030 [US3] Implement dataset‑size binning (n<50, 50‑200, >200). Logs warning for empty bins. **Note**: No FR‑008 reference.
- [X] T031 [US3] Implement bootstrap variance estimation with **≥1000** resamples per dataset (default 1000). **No fallback**. **Dependency**: baseline & cleaned metrics.
- [X] T032 [US3] Generate permutation null datasets for false‑positive‑rate (FPR) estimation; output `data/processed/null_fpr_metrics.json`. **Dependency**: baseline pipeline.
- [X] T033a [US3] Perform outlier‑threshold sweep for k ∈ {1.5, 2.0} and compute FPR; output `data/processed/outlier_threshold_sweep_report.json`.
- [X] T033b [US3] Compute inconsistency rate per outlier threshold; append to sweep report.
- [X] T034 [US3] Generate forest plot of p‑value shifts (`output/figures/pvalue_shifts_forest.png`).
- [X] T035 [US3] Generate heatmap of CI‑width changes (`output/figures/ci_width_heatmap.png`).
- [X] T036 [US3] Implement per‑dataset p‑value shift reporting (no median/IQR). **Aligns with methodological pivot**.
- [X] T037 [US3] Implement per‑dataset CI width change reporting. **Note**: Enforced minimum 1000 bootstrap iterations; removed 500‑iteration fallback.
- [X] T038 [US3] Implement per‑dataset effect‑size change reporting.
- [X] T039 [US3] Log excluded datasets (>80 % missing outcome) with warning; record reason in `data_quality_report.md`.
- [X] T040 [US3] Create `ComparisonReport` entity and write `data/processed/comparison_report.json` aggregating all results.
- [X] T041 [US3] Generate final report `output/reports/final_report.md` referencing visualizations and noting methodological limitations.

**Checkpoint**: All US3 tasks now have explicit dependencies on T1105/T1106, making the story independently testable.

---

## Phase 5: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042 [P] Documentation updates in `docs/README.md` with pipeline overview.
- [X] T043 Code cleanup and refactoring (remove dead code, optimize imports).
- [X] T045 [P] Enforce minimum 1000 bootstrap iterations (fallback removed).
- [X] T046 [P] Additional unit tests for edge cases (no outliers, variance reduction, row removal) in `tests/unit/`.
- [X] T047 Run quickstart.md validation and fix any pipeline execution issues.
- [X] T048 Verify all artifacts are checksummed and `state.yaml` is updated.
- [X] T049 [P] Add CI/CD workflow file for GitHub Actions with CPU‑only constraints.
- [X] T066 [P] Unit test `tests/unit/test_analysis_fix.py`: Verify `analysis.run_t_test` uses `scipy.stats.ttest_ind` and `statsmodels` OLS.
- [X] T067 [P] Unit test `tests/unit/test_cleaning_signature.py`: Verify cleaning functions return `(cleaned_df, metadata)`.

---

## Phase 6: Specification & Documentation Refinement

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

## Phase 7: Kickback & Specification Amendments

**Purpose**: Address spec‑level blockers and kickback requirements.

- [ ] T1100 [SPEC‑KICKBACK] Add Success Criterion SC‑006 (≤5 datasets) to `spec.md`. Include rationale and update related sections.
- [ ] T1101 [SPEC‑KICKBACK] Create verification test `tests/unit/test_sc006_present.py` that asserts SC‑006 is defined in the spec.
- [ ] T1102 [SPEC‑KICKBACK] Add Success Criterion SC‑008 (stratification with ≥1 dataset per bin) to `spec.md`.
- [ ] T1103 [SPEC‑KICKBACK] Add Functional Requirement FR‑008 (stratification) to `spec.md` and corresponding verification test.
- [ ] T1104 [SPEC‑KICKBACK] Add Functional Requirement FR‑007 (FWER control) to `spec.md` and verification test.
- [ ] T1105 [SPEC‑KICKBACK] Create `spec_amendment_pr.txt` documenting the PR URL that updates the spec with the above amendments.
- [ ] T1106 [SPEC‑KICKBACK] Update `spec_amendment.md` to note the lowered dataset‑count requirement and FR‑001 deviation; ensure test `tests/unit/test_spec_amendment_present.py` checks file existence.

---

## Phase 8: Refactoring – Fine‑Grained Tasks (formerly Phase 9)

**Purpose**: Replace coarse, multi‑action tasks with atomic, verifiable units.

- [X] T094 Delete all `code/t0*.py` scripts after confirming logic migrated.
- [X] T095 Audit `code/cleanup_utils.py` for unique functions.
- [X] T096 Audit `code/profiler.py` for unique functions.
- [X] T097 Merge unique functions from `cleanup_utils.py` and `profiler.py` into `code/utils.py`.
- [X] T098 Delete `code/cleanup_utils.py`.
- [X] T099 Delete `code/profiler.py`.
- [X] T100 Move `code/run_lint.py` to `scripts/run_lint.py`.
- [X] T101 Move `code/run_quickstart_validation.py` to `scripts/run_quickstart_validation.py`.
- [X] T102 Create linting script `scripts/check_config.py` that scans for hard‑coded path strings outside `code/config.py`.
- [X] T103 Execute `scripts/check_config.py` and fix any violations.
- [X] T104 Refactor `code/main.py` to import core pipeline functions only.
- [X] T105 Ensure `code/main.py` is the sole entry point; add test `tests/unit/test_main_entrypoint.py`.
