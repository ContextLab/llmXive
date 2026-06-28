---
description: "Task list for feature: Quantifying the Impact of Data Cleaning on Statistical Inference"
---

# Tasks: Quantifying the Impact of Data Cleaning on Statistical Inference

**Input**: Design documents from `/specs/001-quantify-cleaning-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [ ] T001 Create project structure per implementation plan (code/, data/raw/, data/processed/, tests/)
- [ ] T002 Initialize Python 3.11 project with requirements.txt (pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pytest)
- [ ] T003 [P] Configure linting and formatting tools (ruff/black) in code/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create utils.py with random seed pinning (numpy, scipy), checksum utilities, logging infrastructure setup, and logging configuration
- [ ] T005 [P] Setup environment configuration management in code/config.py with env vars for DATASET_URLS, OUTPUT_PATH, RANDOM_SEED, BOOTSTRAP_ITERATIONS
- [ ] T006 [P] Create base data models/entities per data-model.md (Dataset, CleaningStrategy, AnalysisResult, ComparisonReport schemas)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Acquisition and Baseline Analysis (Priority: P1) 🎯 MVP

**Goal**: Download public datasets from UCI/OpenML and run baseline statistical analyses (t-tests, linear regressions) on raw, uncleaned data to establish reference metrics (p-values, 95% CI, effect sizes)

**Independent Test**: Can be fully tested by executing the dataset download and baseline analysis script against a single dataset, producing a report with p-values, confidence intervals, and effect sizes for that dataset

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T007 [P] [US1] Contract test for dataset download in tests/unit/test_acquisition.py
- [ ] T008 [P] [US1] Integration test for baseline analysis pipeline in tests/integration/test_baseline.py

### Implementation for User Story 1

- [ ] T009 [US1] Implement acquisition.py with verified dataset URLs (UCI HAR, UCI Shopper) and checksum validation. Note: SPEC DEVIATION - FR-001 requires OpenML but plan flags BLOCKING GAP for kickback; using UCI HAR/Shopper only. Include validation for p-values in (0,1) and CI bounds finite, and logging for download status
- [ ] T010 [US1] Implement baseline analysis in code/analysis.py using scipy.stats (t-tests) and statsmodels (linear regression). Include validation for p-values in (0,1) and CI bounds finite, and dataset size binning (n<50, 50-200, >200) with missingness rate tracking
- [ ] T011 [US1] Record baseline metrics (p-value, 95% CI, Cohen's d/R²) to data/processed/baseline_metrics.json with ≥3 decimal precision. Note: SC-006 requires ≥10 datasets; current 2 datasets flagged as BLOCKING GAP per plan.md Dataset Feasibility Notice

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Systematic Cleaning Strategy Application (Priority: P1)

**Goal**: Apply three cleaning strategies systematically (IQR outlier removal, mean/median/KNN imputation, categorical recoding) and re-run identical statistical tests on each cleaned variant

**Independent Test**: Can be fully tested by applying one cleaning strategy (e.g., IQR outlier removal with k=1.5) to a single dataset and comparing before/after p-values, which delivers the primary research outcome for that strategy

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T012 [P] [US2] Unit test for IQR outlier removal in tests/unit/test_cleaning.py
- [ ] T013 [P] [US2] Unit test for mean/median/KNN imputation in tests/unit/test_cleaning.py
- [ ] T014 [P] [US2] Integration test for cleaning pipeline in tests/integration/test_cleaning.py

### Implementation for User Story 2

- [ ] T015 [US2] Implement IQR outlier removal in code/cleaning.py with k=1.5 threshold (Tukey default) and row removal logging. Include validation for zero missing values post-op and flag cases where ≥50% rows removed with bias note
- [ ] T016 [US2] Implement mean imputation in code/cleaning.py with zero missing values validation post-op and variance reduction warning (≥20% flag)
- [ ] T017 [US2] Implement median imputation in code/cleaning.py with zero missing values validation post-op and variance reduction warning (≥20% flag)
- [ ] T018 [US2] Implement KNN imputation (k=5) in code/cleaning.py using scikit-learn with zero missing values validation post-op and variance reduction warning (≥20% flag)
- [ ] T019 [US2] Implement categorical recoding in code/cleaning.py with factor encoding for statistical testing
- [ ] T020 [US2] Write cleaned datasets to data/processed/ with strategy-specific naming (e.g., dataset_outlier_removed.csv)
- [ ] T021 [US2] Re-run t-tests and linear regressions on each cleaned variant using code/analysis.py
- [ ] T022 [US2] Record cleaned metrics (p-value, 95% CI, effect size) to data/processed/cleaned_metrics.json

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Metrics Comparison and Sensitivity Analysis (Priority: P2)

**Goal**: Compute absolute and relative differences between baseline and cleaned results, perform sensitivity analysis across dataset sizes and missingness rate bins, and generate summary visualizations

**Independent Test**: Can be fully tested by running the comparison script on 2 datasets (one cleaned, one baseline) and verifying the difference report contains p-value shifts, CI width changes, and effect size variations with valid numeric values

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for metrics comparison in tests/unit/test_reporting.py
- [ ] T024 [P] [US3] Unit test for Benjamini-Hochberg correction in tests/unit/test_reporting.py
- [ ] T025 [P] [US3] Integration test for sensitivity analysis in tests/integration/test_sensitivity.py

### Implementation for User Story 3

- [ ] T026 [US3] Implement metrics comparison in code/reporting.py computing |p_cleaned - p_baseline| (≥3 decimal precision), CI width change ((CI_width_cleaned - CI_width_baseline) / CI_width_baseline × 100, ≥2 decimal precision), effect-size delta (Cohen's d or ΔR²), AND inconsistency rate (proportion of datasets where significance status changes between baseline and cleaned) per FR-006
- [ ] T027 [US3] Implement Benjamini-Hochberg False Discovery Rate (FDR) correction (q ≤ 0.05) in code/reporting.py. Note: BH controls FDR, not family-wise error rate (FWER) - spec FR-007 contains error
- [ ] T028 [US3] Implement dataset size binning sensitivity analysis (n<50, 50-200, >200) with ≥1 dataset per bin. Note: Only 2 datasets available; statistical aggregation limited per plan feasibility notice
- [ ] T029 [US3] Implement missingness rate binning (0-[deferred], 5-[deferred], 10-[deferred], >20%) with ≥1 dataset per bin. Note: Bin values to be resolved per research.md or spec kickback update
- [ ] T030 [US3] Implement bootstrap variance estimation (≥1000 resamples per dataset, default 1000 iterations, fallback to 500 if runtime >5h per plan assumptions while preserving Constitution Principle VI minimum) for metric shifts with 95% CI
- [ ] T031 [US3] Implement permutation null dataset generation (outcome variable shuffled) for false-positive rate estimation
- [ ] T032 [US3] Implement outlier threshold sweep (k ∈ {1.0, 1.5, 2.0}) with FPR calculation AND inconsistency rate (proportion of datasets where significance status changes between baseline and cleaned) per threshold per FR-006
- [ ] T033 [US3] Generate forest plot of p-value shifts using matplotlib/seaborn and save as PNG to output/
- [ ] T034 [US3] Generate heatmap of CI-width changes across strategies and dataset bins and save as PNG to output/
- [ ] T035 [US3] Create comparison report (ComparisonReport entity) with baseline_metrics, cleaned_metrics, absolute_diff, relative_diff, sensitivity_analysis
- [ ] T036 [US3] [DEFERRED] Compute median absolute p-value shift with IQR across datasets per cleaning strategy (SC-001). Note: Defer until SC-006 dataset requirement resolved (≥10 datasets); currently limited dataset availability makes median/IQR statistically invalid per plan feasibility notice - BLOCKING GAP requires spec kickback
- [ ] T037 [US3] [DEFERRED] Compute median percentage change in CI width with IQR per cleaning strategy (SC-002). Note: Defer until SC-006 dataset requirement resolved (≥10 datasets); currently only 2 datasets available makes median/IQR statistically invalid per plan feasibility notice - BLOCKING GAP requires spec kickback
- [ ] T038 [US3] [DEFERRED] Compute median effect-size change with IQR per strategy and dataset-size bin (SC-003). Note: Defer until SC-006 dataset requirement resolved (≥10 datasets); currently only 2 datasets available makes median/IQR statistically invalid per plan feasibility notice - BLOCKING GAP requires spec kickback
- [ ] T039 [US3] Log excluded datasets (>80% missing outcome) with warning and record exclusion reason
- [ ] T040 [US3] Add final report generation with all metrics aggregated and visualizations referenced

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in docs/ (README with pipeline overview)
- [ ] T042 Code cleanup and refactoring (remove dead code, optimize imports)
- [ ] T043 [P] Add runtime profiling/logging to monitor execution time and identify bottlenecks
- [ ] T044 [P] Implement conditional bootstrap reduction logic (reduce to 500 iterations if runtime >5h) per plan assumptions while preserving Constitution Principle VI minimum
- [ ] T045 [P] Additional unit tests for edge cases (no outliers, variance reduction, row removal) in tests/unit/
- [ ] T046 Run quickstart.md validation and fix any pipeline execution issues
- [ ] T047 Verify all artifacts are checksummed and state.yaml is updated
- [ ] T048 [P] Add CI/CD workflow file for GitHub Actions with CPU-only constraints

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

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T015-T019 (cleaning.py) and T026-T035 (reporting.py) are NOT parallel-safe due to same-file writes - [P] tags removed

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset download in tests/unit/test_acquisition.py"
Task: "Integration test for baseline analysis pipeline in tests/integration/test_baseline.py"

# Launch all models for User Story 1 together:
Task: "Implement acquisition.py with verified dataset URLs"
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
- **Dataset feasibility**: Only 2 verified datasets (UCI HAR, UCI Shopper) available; SC-006 (≥10 datasets) flagged for spec kickback - median/IQR tasks (T036-T038) DEFERRED until dataset count increases
- **Bootstrap iterations**: 1000 iterations default, fallback to 500 if runtime >5h per plan assumptions (T030) - Constitution Principle VI minimum preserved
- **Edge cases**: Handle no outliers, >80% missing outcome, ≥50% row removal, variance reduction ≥20%
- **Spec deviations**: T009 acknowledges OpenML→UCI deviation; T027 acknowledges FDR vs FWER distinction; T032 acknowledges FR-006 inconsistency rate requirement
- **BLOCKING GAP**: SC-006 requires ≥10 datasets but only 2 available - median/IQR calculations (T036-T038) marked DEFERRED pending spec kickback