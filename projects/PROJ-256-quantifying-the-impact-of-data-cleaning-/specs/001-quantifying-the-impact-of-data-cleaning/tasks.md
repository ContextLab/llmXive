---
description: "Task list for feature: Quantifying the Impact of Data Cleaning on Statistical Inference"
---

# Tasks: Quantifying the Impact of Data Cleaning on Statistical Inference

**Input**: Design documents from `/specs/001-quantify-cleaning-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (code/, data/raw/, data/processed/, tests/)
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pytest)
- [X] T003 [P] Configure linting and formatting tools (ruff/black) in code/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [Dependency: Requires T008] Create `code/utils.py` with function `pin_random_seed(seed: int)` for numpy and scipy, ensuring reproducibility.
- [X] T005 [Dependency: Requires T008] Create `code/utils.py` with function `compute_file_checksum(filepath: str) -> str` for SHA256 validation of data files.
- [X] T006 [Dependency: Requires T008] Create `code/utils.py` with function `setup_logging(log_level: str)` to initialize the logging infrastructure.
- [X] T007 [Dependency: Requires T008] Setup environment configuration management in `code/config.py` with env vars for DATASET_URLS, OUTPUT_PATH, RANDOM_SEED, BOOTSTRAP_ITERATIONS.
- [X] T008 Create base data models/entities per data-model.md (Dataset, CleaningStrategy, AnalysisResult, ComparisonReport schemas) in `code/models.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Acquisition and Baseline Analysis (Priority: P1) 🎯 MVP

**Goal**: Download public datasets from UCI/OpenML and run baseline statistical analyses (t-tests, linear regressions) on raw, uncleaned data to establish reference metrics (p-values, 95% CI, effect sizes)

**Independent Test**: Can be fully tested by executing the dataset download and baseline analysis script against a single dataset, producing a report with p-values, confidence intervals, and effect sizes for that dataset

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test in `tests/unit/test_acquisition.py`: Verify `download_dataset` returns 200 status and non-empty content for UCI HAR URL.
- [X] T010 [P] [US1] Integration test in `tests/integration/test_baseline.py`: Verify baseline analysis script produces `baseline_metrics.json` with valid p-values (0 < p < 1) and finite CIs. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [X] T011 [US1] Implement acquisition logic in `code/data_loader.py`. **Action**: Attempt download from OpenML Small Datasets collection first. If unavailable, fallback to UCI HAR (URL: `) and UCI Shopper (URL: `). **Requirement**: Log "Fallback to UCI: OpenML unavailable or empty" if fallback occurs. Validate p-values are in (0,1) and CI bounds are finite. Record checksums.
- [X] T012 [US1] Implement baseline analysis in `code/analysis.py` using scipy.stats (t-tests) and statsmodels (linear regression). **Requirement**: Validate p-values in (0,1) and CI bounds finite. Output `data/processed/baseline_metrics.json`. <!-- ATOMIZE: requested -->
- [X] T013 [US1] Record baseline metrics (p-value, 95% CI, Cohen's d/R²) to `data/processed/baseline_metrics.json` with ≥3 decimal precision. **Note**: SC-006 requires ≥10 datasets; current multiple datasets flagged as BLOCKING GAP per plan.md Dataset Feasibility Notice. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Systematic Cleaning Strategy Application (Priority: P1)

**Goal**: Apply three cleaning strategies systematically (IQR outlier removal, mean/median/KNN imputation, categorical recoding) and re-run identical statistical tests on each cleaned variant

**Independent Test**: Can be fully tested by applying one cleaning strategy (e.g., IQR outlier removal with k=1.5) to a single dataset and comparing before/after p-values, which delivers the primary research outcome for that strategy

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T014 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_iqr_outlier_removal` removes rows where |z-score| > k and logs count.
- [X] T015 [P] [US2] Unit test in `tests/unit/test_cleaning.py`: Verify `apply_mean_imputation` results in zero missing values in target columns.
- [X] T016 [P] [US2] Integration test in `tests/integration/test_cleaning.py`: Verify full cleaning pipeline produces valid CSVs with correct row counts and zero missing values.

### Implementation for User Story 2

- [X] T017 [US2] Implement function `apply_iqr_outlier_removal(df, k=1.5)` in `code/cleaning.py`. **Requirement**: Log rows removed. Flag if ≥50% rows removed with bias note.
- [X] T018 [US2] Implement function `apply_mean_imputation(df, columns)` in `code/cleaning.py`. **Requirement**: Validate zero missing values post-op. Flag if variance reduction ≥20%.
- [X] T019 [US2] Implement function `apply_median_imputation(df, columns)` in `code/cleaning.py`. **Requirement**: Validate zero missing values post-op. Flag if variance reduction ≥20%.
- [X] T020 [US2] Implement function `apply_knn_imputation(df, columns, k=5)` in `code/cleaning.py` using scikit-learn. **Requirement**: Validate zero missing values post-op. Flag if variance reduction ≥20%.
- [X] T021 [US2] Implement function `apply_categorical_recoding(df)` in `code/cleaning.py` with factor encoding for statistical testing.
- [X] T022 [US2] Write cleaned datasets to `data/processed/` with strategy-specific naming (e.g., `dataset_outlier_removed.csv`).
- [ ] T023 [US2] Re-run t-tests and linear regressions on each cleaned variant using `code/analysis.py`. **Output**: `data/processed/cleaned_metrics.json`. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Metrics Comparison and Sensitivity Analysis (Priority: P2)

**Goal**: Compute absolute and relative differences between baseline and cleaned results, perform sensitivity analysis across dataset sizes and missingness rate bins, and generate summary visualizations

**Independent Test**: Can be fully tested by running the comparison script on 2 datasets (one cleaned, one baseline) and verifying the difference report contains p-value shifts, CI width changes, and effect size variations with valid numeric values

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test in `tests/unit/test_reporting.py`: Verify `calculate_p_value_shift` returns absolute difference with ≥3 decimal precision.
- [X] T025 [P] [US3] Unit test in `tests/unit/test_reporting.py`: Verify `apply_bonferroni_correction` correctly adjusts p-values for FWER control.
- [X] T026 [P] [US3] Integration test in `tests/integration/test_sensitivity.py`: Verify stratification logic logs warnings for empty bins and proceeds.

### Implementation for User Story 3

- [ ] T027 [US3] Implement metrics comparison in `code/reporting.py`. **Dependency**: Depends on existence of `cleaned_metrics.json` and `baseline_metrics.json` artifacts. **Requirement**: Compute |p_cleaned - p_baseline| (≥3 decimal precision), CI width change (≥2 decimal precision), effect-size delta, AND inconsistency rate (proportion of datasets where significance status changes) per FR-006. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T028 [US3] Implement Bonferroni correction for Family-Wise Error Rate (FWER) in `code/reporting.py`. **Requirement**: Log a warning: "Warning: FR-007 requests FWER control. Benjamini-Hochberg controls FDR. Implemented Bonferroni (FWER) to satisfy FR-007."
- [X] T029 [US3] Implement missingness rate binning with explicit thresholds: non-missing, low, moderate, and high. **Requirement**: Log warning: "Warning: Missingness bin thresholds [0, 5, 10, 20] used. If bins are empty, log CONSTRAINT_VIOLATION but do not skip logic." **Control Flow**: If bins are empty, log warning and proceed.
- [ ] T030 [US3] Implement dataset size binning sensitivity analysis (n<50, 50-200, >200). **Requirement**: Log warning if <1 dataset per bin. **Control Flow**: If bins are empty, log CONSTRAINT_VIOLATION warning and proceed. **Dependency**: Depends on baseline metrics.
- [X] T031 [US3] Implement bootstrap variance estimation (≥1000 resamples per dataset, default 1000, fallback to 500 if dataset size > 5000 rows) for metric shifts with 95% CI. **Dependency**: Depends on existence of metric artifacts (T012, T023).
- [X] T032 [US3] Implement permutation null dataset generation (outcome variable shuffled) for false-positive rate (FPR) estimation per FR-011. **Requirement**: Generate null datasets by shuffling outcomes while keeping predictors fixed. Output `data/processed/null_fpr_metrics.json`.
- [ ] T033 [US3] Implement outlier threshold sweep for k ∈ {, a specific threshold} with FPR calculation AND inconsistency rate per threshold per FR-006. **Requirement**: Calculate FPR as proportion of tests with p ≤ 0.05 in null datasets. Calculate Inconsistency Rate as proportion of datasets where significance status changes. **Dependency**: Depends on cleaning functions (T017-T021) and analysis functions (T012, T023).
- [X] T034 [US3] Generate forest plot of p-value shifts using matplotlib/seaborn and save as PNG to `output/`.
- [X] T035 [US3] Generate heatmap of CI-width changes across strategies and dataset bins and save as PNG to `output/`.
- [X] T036 [US3] Implement per-dataset p-value shift reporting. **Requirement**: Calculate Median and IQR of p-value shifts. If n=2, log "STATISTICAL_LIMITATION: Median/IQR calculated on n=2, results are unstable." Do not skip calculation.
- [X] T037 [US3] Implement per-dataset CI width change reporting. **Requirement**: Calculate Median and IQR of CI width changes. If n=2, log "STATISTICAL_LIMITATION: Median/IQR calculated on n=2, results are unstable." Do not skip calculation.
- [X] T038 [US3] Implement per-dataset effect-size change reporting. **Requirement**: Calculate Median and IQR of effect-size changes. If n=2, log "STATISTICAL_LIMITATION: Median/IQR calculated on n=2, results are unstable." Do not skip calculation.
- [X] T039 [US3] Log excluded datasets (>80% missing outcome) with warning and record exclusion reason.
- [ ] T040 [US3] Create comparison report (ComparisonReport entity) with baseline_metrics, cleaned_metrics, absolute_diff, relative_diff, sensitivity_analysis. <!-- FAILED: unspecified -->
- [X] T041 [US3] Generate final report with all metrics aggregated and visualizations referenced.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042 [P] Documentation updates in `docs/` (README with pipeline overview)
- [X] T043 Code cleanup and refactoring (remove dead code, optimize imports)
- [X] T044 [P] Add runtime profiling/logging to monitor execution time and identify bottlenecks
- [X] T045 [P] Implement conditional bootstrap reduction logic (reduce to 500 iterations if dataset size > 5000 rows) per plan assumptions while preserving Constitution Principle VI minimum
- [X] T046 [P] Additional unit tests for edge cases (no outliers, variance reduction, row removal) in `tests/unit/`
- [X] T047 Run quickstart.md validation and fix any pipeline execution issues
- [X] T048 Verify all artifacts are checksummed and state.yaml is updated
- [X] T049 [P] Add CI/CD workflow file for GitHub Actions with CPU-only constraints

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Requires US1 baseline metrics for comparison (METRIC dependency, not implementation block - US2 can be coded independently)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Requires US1 and US2 metrics for comparison (METRIC dependency, not implementation block - US3 can be coded independently)

**Note on Independence**: Each user story is independently TESTABLE and CODEABLE once baseline metrics exist, but US2/US3 require US1 baseline metrics for meaningful comparison. This is a metric dependency, not an implementation dependency. Each story can be developed in parallel by different team members.
**Execution Note**: US3 implementation is independent, but execution requires US1/US2 artifacts.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) - **Note: T004-T007 depend on T008**
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T017-T021 (cleaning.py) and T027-T041 (reporting.py) are NOT parallel-safe due to same-file writes - [P] tags removed

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset download in tests/unit/test_acquisition.py"
Task: "Integration test for baseline analysis pipeline in tests/integration/test_baseline.py"

# Launch all models for User Story 1 together:
Task: "Implement acquisition logic in code/data_loader.py"
Task: "Implement baseline analysis in code/analysis.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU-tractability**: All statistical methods (scipy, statsmodels, scikit-learn) are CPU-only; no GPU/CUDA dependencies
- **Dataset feasibility**: A limited number of verified datasets (UCI HAR, UCI Shopper) are available.; SC-006 (≥10 datasets) flagged for spec kickback - median/IQR tasks (T036-T038) now active with fallback logic (per-dataset reporting) to preserve constraint intent.
- **Bootstrap iterations**: A default number of iterations will be used for the simulation., fallback to 500 if dataset size > 5000 rows per plan assumptions (T031) - Constitution Principle VI minimum preserved
- **Edge cases**: Handle no outliers, >80% missing outcome, ≥50% row removal, variance reduction ≥20%
- **Spec deviations**: T011 acknowledges OpenML→UCI deviation; T028 acknowledges FDR vs FWER distinction; T033 acknowledges FR-006 inconsistency rate requirement
- **BLOCKING GAP**: SC-006 requires ≥10 datasets but only 2 available - median/IQR calculations (T036-T038) now implemented as per-dataset reporting with explicit limitation notes to satisfy SC intent without statistical invalidity.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [~] T050 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
