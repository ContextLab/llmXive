# Tasks: Investigating the Impact of Network Centrality on the Consolidation of Motor Memories

**Input**: Design documents from `/specs/001-network-centrality-motor-consolidation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[D]**: Dependent (must wait for upstream artifacts)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
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

## Phase 0: Data Validation & Feasibility Check (Priority: P0 - BLOCKING)

**Purpose**: Validate data availability and completeness BEFORE any processing. Enforces hard stops for missing data.

**⚠️ CRITICAL**: No preprocessing (Phase 1) can begin until this phase passes.

- [X] T001 [P] [US1] Download a dataset from OpenNeuro using `openneuro-cli` in `code/data/download.py`.
- [X] T002 [US1] **Fatal Gate**: Verify presence of required columns (`pre_motor_score`, `post_motor_score`, `age`, `sex`, `subject_id`) in the downloaded metadata. **If missing, log "Fatal: Dataset lacks behavioral motor task metrics" and exit immediately. Do not proceed.**
- [X] T003 [US1] **Retention & Behavioral Validation**: Read the downloaded metadata from `data/raw/metadata.csv`. Calculate retention rate (subjects with valid data / total subjects). **If < 80% due to missing behavioral data, log "Fatal: Retention < 80% due to missing behavioral data" and exit. If < 80% due to motion artifacts, log warning and proceed.** Save the retention rate proportion, total subjects, and retained subjects count to `data/processed/behavioral/retention_metrics.json` to satisfy SC-001.
- [ ] T004 [US1] **Power Check**: If N < 85, log warning "Underpowered for small effects (r=0.3)" and proceed with caution, but flag in report.

**Checkpoint**: Data validated. Proceed to preprocessing only if Phase 0 passes.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T005a [P] Create project directory `code/` and subdirectories `code/data/`, `code/analysis/`, `code/utils/`
- [X] T005b [P] Create project directory `data/` and subdirectories `data/raw/`, `data/processed/`, `data/artifacts/`
- [X] T005c [P] Create project directory `tests/` and subdirectories `tests/contract/`, `tests/integration/`, `tests/unit/`
- [X] T006 [P] Initialize git repository and create `.gitignore` for data and artifacts
- [X] T007 Initialize Python project with dependencies: `pandas`, `numpy`, `networkx`, `scikit-learn`, `statsmodels`, `nilearn`, `openneuro-cli`, `matplotlib`, `seaborn`, `pymvpa` (for permutation) in `code/requirements.txt`
- [X] T008 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [X] T009 Setup data directory structure: `data/raw/`, `data/processed/`, `data/artifacts/`
- [X] T010 [P] Implement logging infrastructure in `code/utils/logging.py` to track wall_clock_time and RAM usage
- [X] T011 [P] Setup reproducibility reporting utility in `code/utils/metrics.py` to generate `reproducibility_report.json`
- [X] T012 Create base data models/entities in `code/__init__.py` and `code/data/` for Subject and ConnectivityMatrix
- [X] T013 Configure environment configuration management for dataset URLs and thresholds in `code/utils/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Preprocess fMRI data with fMRIPrep (memory efficient) and extract behavioral metrics.

**Independent Test**: The pipeline produces a CSV with subject IDs, behavioral improvement scores, and pre-processed fMRI time-series for ≥ 50 subjects with no missing values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [X] T015 [P] [US1] Integration test for download and exclusion logic in `tests/integration/test_data_ingestion.py`

### Implementation for User Story 1

- [X] T016 [P] [US1] Implement fMRIPrep preprocessing wrapper with memory-efficient settings (float32, batch processing) in `code/data/preprocess.py`
- [ ] T017 [US1] Implement behavioral metric extraction (pre/post motor scores, age, sex) from `data/raw/metadata.csv`. **Output**: Save subject IDs, scores, and demographics to `data/processed/behavioral/subject_scores.csv` with columns `subject_id`, `pre_motor_score`, `post_motor_score`, `age`, `sex`, `improvement_score`.
- [X] T018 [US1] Implement retention rate calculation and power check (N >= 85 warning) in `code/data/preprocess.py`
- [ ] T019 [US1] Add validation to ensure ≥ 80% subject retention and fail gracefully if behavioral data is missing (Logic moved to Phase 0 T002/T003, this task ensures logging)
- [ ] T020 [US1] **Log Exclusions**: Write a log of excluded subjects and reasons (e.g., motion artifacts, missing data) to `data/processed/logs/exclusion_log.csv`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Centrality Calculation and Association Modeling (Priority: P2)

**Goal**: Compute centrality metrics from connectivity matrices for the **FULL AAL3 atlas (~90 regions)**, calculate FD, check VIF, aggregate to global score, and fit linear/GAM models with covariates.

**Independent Test**: The analysis script outputs a regression summary table, scatter plot, non-linearity check results, and regional p-values (if triggered).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for centrality metric calculation in `tests/contract/test_centrality.py`
- [X] T022 [P] [US2] Integration test for regression model fitting in `tests/integration/test_regression.py`

### Implementation for User Story 2

- [P] T023 [US2] **Calculate Full-Atlas Centrality**: From preprocessed fMRI data, extract functional connectivity matrices for the **FULL AAL3 atlas (~90 regions)**. Use `nilearn.connectome.ConnectivityMeasure` to load the AAL3 atlas file. Calculate degree, betweenness, and eigenvector centrality for **EVERY region** using `networkx`. Save raw metrics for all regions to `data/processed/centrality/subject_id_metrics.csv` (columns: `subject_id`, `region_id`, `region_name`, `degree`, `betweenness`, `eigenvector`).
- [P] T024 [US2] **Compute Global Score**: Read `data/processed/centrality/subject_id_metrics.csv` (T023). Aggregate the full set of regional metrics (all available regions) into a single 'global_centralty' score per subject (e.g., mean of all regions or mean of top hub nodes as defined in plan). Save to `data/processed/centrality/global_scores.csv` in `code/analysis/centrality.py`.
- [P] T025 [US2] **Calculate Mean FD**: Read fMRIPrep confounds (`data/processed/fmriprep/*/desc-confounds_timeseries.tsv`), calculate Mean Framewise Displacement per subject, and save to `data/processed/behavioral/fd_mean.csv` in `code/analysis/centrality.py`.
- [P] T026 [US2] **Calculate VIF**: Load degree, betweenness, eigenvector metrics for the **FULL SET OF REGIONS** from `data/processed/centrality/subject_id_metrics.csv` (T023). Calculate Variance Inflation Factor (VIF) for these three metrics across the full network. Save VIF values to `data/processed/centrality/vif_values.csv` in `code/analysis/centrality.py`.
- [P] T027 [US2] **Determine Predictor Set**: Read `vif_values.csv` (T026). **IF** any VIF > 5: Run PCA on degree/betweenness/eigenvector metrics from the full set, retain first component, set `model_type`='PCA-Adjusted'. **ELSE**: Use 'Global_Centrality', set `model_type`='Global'. Save decision and selected predictors to `data/processed/centrality/model_predictors.csv` (columns: `model_type`, `selected_predictors`, `vif_values`, `formula_string`).
- [P] T028 [US2] **Fit Linear Regression**: Read `model_predictors.csv` (T027), `fd_mean.csv` (T025), and behavioral data from `data/processed/behavioral/subject_scores.csv` (T017). **If `model_type`='PCA-Adjusted'**, formula is `Improvement ~ PCA_Component + Age + Sex + Mean_FD`. **Else**, formula is `Improvement ~ Global_Centrality + Age + Sex + Mean_FD`. Fit model using `statsmodels`. Save summary to `data/processed/regression/linear_model_summary.csv` in `code/analysis/regression.py`.
- [P] T029 [US2] **Fit Null Model & Baseline**: Fit intercept-only model (`Improvement ~ 1`) and calculate residuals. Save residuals to `data/processed/validation/null_residuals.csv`. **Additionally, calculate and save the baseline R² (R² of intercept-only model) to `data/processed/validation/baseline_r2.json`** in `code/analysis/regression.py`.
- [P] T030 [US2] **Non-Linearity Check**: Fit GAM/Polynomial model using the SAME predictor set as T028. Compare AIC/BIC with Linear Model. Save comparison to `data/processed/regression/nonlinearity_check.csv` in `code/analysis/regression.py`.
- [P] T031 [US2] **Generate Scatter Plot**: Generate scatter plot with regression line and non-linearity fit in `code/analysis/regression.py`.
- [P] T032 [US2] **Regional Analysis**: **IF** `config.regional_analysis_flag == true`: Fit separate regression models for each of the ~90 regions (using metrics from T023) to generate regional p-values. Save to `data/processed/regression/regional_pvalues.csv`. **ELSE**: Skip and log "Regional analysis skipped per config". (Triggers fallback only if needed).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation and Robustness Assessment (Priority: P3)

**Goal**: Perform Freedman-Lane permutation test and k-fold cross-validation to validate findings.

**Independent Test**: The validation module produces a null distribution histogram, empirical p-value, and cross-validated R²/RMSE.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Contract test for permutation test logic in `tests/contract/test_permutation.py`
- [X] T034 [P] [US3] Integration test for cross-validation loop in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [P] T035 [US3] **Generate Null Distribution**: Read `null_residuals.csv` (T029). Permute residuals **1000 times** (Freedman-Lane) with `random_seed=42`. For each permutation, refit the model (using the same formula as T028) and record the coefficient for the primary predictor. Save distribution to `data/processed/validation/null_distribution.csv` in `code/analysis/validation.py`.
- [P] T036 [US3] **Calculate Empirical P-Value**: Read `null_distribution.csv` (T035) and the observed coefficient from `linear_model_summary.csv` (T028). Calculate empirical p-value. Save to `data/processed/validation/permutation_results.json` in `code/analysis/validation.py`.
- [D] T037 [US3] **Cross-Validation**: Perform **5-fold k-fold cross-validation** with `random_seed=42`. **Inputs**: Feature matrix from `data/processed/centrality/model_predictors.csv` (T027) and target vector from `data/processed/behavioral/subject_scores.csv` (T017). **Output**: Calculate out-of-sample R² and RMSE and their standard deviations. Compare mean R² against the baseline R² from `baseline_r2.json` (T029). Save metrics and comparison to `data/processed/validation/cv_results.json` in `code/analysis/validation.py`.
- [P] T038 [US3] **Generate Null Distribution Histogram**: Generate histogram of null distribution and overlay observed coefficient in `code/analysis/validation.py`.
- [P] T039 [US3] **Conditional FDR Correction**: IF `regional_analysis_flag == true` (i.e., T032 was executed): Apply Benjamini-Hochberg FDR correction to the regional p-values from T032. Save to `data/processed/validation/fdr_corrected_pvalues.csv`. ELSE: Skip and log "FDR correction skipped (regional analysis not triggered)".

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Finalization

**Purpose**: Generate final artifacts after all analysis and validation are complete

- [X] T040 [US3] Generate final `reproducibility_report.json` with checksums, wall clock time, RAM usage, and ALL validation metrics (p-values, R², RMSE, baseline comparison) in `code/utils/metrics.py`

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `docs/` and `README.md`
- [ ] T042 Code cleanup and refactoring
- [ ] T043 Performance optimization across all stories (ensure float32 usage and batch processing)
- [ ] T044 [P] Additional unit tests in `tests/unit/`
- [ ] T045 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0**: No dependencies - MUST run first. Blocks all other phases.
- **Phase 1**: No dependencies - can start immediately.
- **Phase 2**: Depends on Phase 1 completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Phase 2 completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Reporting (Phase 6)**: Depends on all validation tasks (Phase 5) completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Phase 2 - Depends on US1 data output.
- **User Story 3 (P3)**: Can start after Phase 2 - Depends on US2 model output.

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Integration test for download and exclusion logic in tests/integration/test_data_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement fMRIPrep preprocessing wrapper in code/data/preprocess.py"
Task: "Implement behavioral metric extraction in code/data/preprocess.py"
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
- [D] tasks = dependent on upstream artifacts (must wait)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Conditional Tasks**: Tasks T032 and T039 only execute if specific trigger conditions are met.
- **Data Flow**: T023 calculates metrics for FULL atlas (AAL3 ~90 regions). T024 aggregates full set. T026 checks VIF on full set. T027 decides model type. T028 fits model based on T027. T029 generates null residuals AND baseline R². T035 permutes residuals (1000 times, seed 42). T037 performs CV (5-fold, seed 42) using full feature matrix and target vector.
- **Freedman-Lane Requirement**: T035 explicitly requires permuting residuals of the null model (T029) to preserve motion confound structure, as mandated by the plan.
- **Baseline Comparison**: T037 explicitly requires comparing out-of-sample R² against the intercept-only model baseline (T029) to ensure predictive value.
- **Bias Control**: T023 targets FULL atlas to ensure valid network topology analysis.
- **VIF Logic**: T026 calculates VIF on full set. T027 decides between Global or PCA based on T026. T028 uses T027's decision.
- **Motion Control**: T025 calculates Mean FD. T028 includes Mean_FD as a covariate.
- **Retention Gate**: T002 and T003 in Phase 0 enforce hard stops for missing data or low retention.
- **Logging**: T020 logs excluded subjects to a specific CSV file.