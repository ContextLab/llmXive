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

- [X] T001 [US1] Download a dataset from OpenNeuro using `openneuro-cli` in `code/data/download.py`.
- [ ] T002 [D] [US1] **Fatal Gate**: Verify presence of required columns (`pre_motor_score`, `post_motor_score`, `age`, `sex`, `subject_id`) in the downloaded metadata. **If missing, log "Fatal: Dataset lacks behavioral motor task metrics" and exit immediately. Do not proceed.** (Depends on T001)
- [ ] T003 [D] [US1] **Retention & Behavioral Validation**: Read the downloaded metadata from `data/raw/metadata.csv`. Calculate retention rate (subjects with valid data / total subjects). **If < 80% due to missing behavioral data, log "Fatal: Retention < 80% due to missing behavioral data" and exit. If < 80% due to motion artifacts, log warning and proceed.** Save the retention rate proportion, total subjects, and retained subjects count to `data/processed/behavioral/retention_metrics.json` to satisfy SC-001. (Depends on T001)
- [ ] T004a [D] [US1] **Power Calculation**: Read `data/processed/behavioral/retention_metrics.json` (T003). Calculate the number of retained subjects (N). Compare N against the spec's threshold of ≥ 50 subjects. [UNRESOLVED-CLAIM: c_6f3e6755 — status=not_enough_info] Output the result to `data/processed/behavioral/power_metrics.json` with keys `n_subjects`, `threshold`, `meets_threshold`. (Depends on T003)
- [ ] T004b [D] [US1] **Power Logging**: If N < 50 (from T004a), log warning "Underpowered for small effects (r=0.3)" and set `pipeline_metrics.power_warning: true` in the `reproducibility_report.json`. If 50 <= N < 85, log warning "N < 85: Power may be limited for small effects". If N >= 85, log success. **Note: This is an advisory research check, not a spec-mandated gate.** (Depends on T004a)

**Checkpoint**: Data validated. Proceed to preprocessing only if Phase 0 passes.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T005a [P] Create project directory `code/` and subdirectories `code/data/`, `code/analysis/`, `code/utils/`
- [ ] T005b [P] Create project directory `data/` and subdirectories `data/raw/`, `data/processed/`, `data/artifacts/`
- [ ] T005c [P] Create project directory `tests/` and subdirectories `tests/contract/`, `tests/integration/`, `tests/unit/`
- [ ] T006 [P] Initialize git repository and create `.gitignore` for data and artifacts
- [X] T007 Initialize Python project with dependencies: `pandas`, `numpy`, `networkx`, `scikit-learn`, `statsmodels`, `nilearn`, `openneuro-cli`, `matplotlib`, `seaborn`, `pymvpa` (for permutation) in `code/requirements.txt`
- [~] T008 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [X] T010 [P] Implement logging infrastructure in `code/utils/logging.py` to track wall_clock_time and RAM usage
- [ ] T011 [P] Setup reproducibility reporting utility in `code/utils/metrics.py` to generate `reproducibility_report.json`
- [ ] T012 [P] Create base data models/entities in `code/__init__.py` and `code/data/` for Subject and ConnectivityMatrix
- [ ] T013 [D] Configure environment configuration management for dataset URLs and thresholds in `code/utils/config.py`. **Note: Must complete before T016 and T023 which read config values. Depends on T005b/T005c for directory structure.** (Depends on T005b, T005c)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Preprocess fMRI data with fMRIPrep (memory efficient) and extract behavioral metrics.

**Independent Test**: The pipeline produces a CSV with subject IDs, behavioral improvement scores, and pre-processed fMRI time-series for ≥ 50 subjects with no missing values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [ ] T015 [P] [US1] Integration test for download and exclusion logic in `tests/integration/test_data_ingestion.py`

### Implementation for User Story 1

- [ ] T016 [D] [US1] Implement fMRIPrep preprocessing wrapper with memory-efficient settings (float32, batch processing) in `code/data/preprocess.py`. **Depends on T013 (config) and T005b (data dirs).** (Depends on T013, T005b)
- [ ] T017 [D] [US1] Implement behavioral metric extraction (pre/post motor scores, age, sex) from `data/raw/metadata.csv`. **Explicitly verify the presence of columns**: `pre_motor_score`, `post_motor_score`, `age`, `sex`, `subject_id`. **If missing, raise error.** **Output**: Save subject IDs, scores, and demographics to `data/processed/behavioral/subject_scores.csv` with columns `subject_id`, `pre_motor_score`, `post_motor_score`, `age`, `sex`, `improvement_score`. **Also log excluded subjects and reasons to `data/processed/logs/exclusion_log.csv` here.** (Depends on T003, T016)
- [ ] T018 [D] [US1] Implement retention rate calculation and power check (N >= 50 warning) in `code/data/preprocess.py` (Logic moved to T003/T004a/b, this task ensures logging). (Depends on T017)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Centrality Calculation and Association Modeling (Priority: P2)

**Goal**: Compute centrality metrics from connectivity matrices for the **top hub nodes** (data-driven per spec FR-002.1), calculate FD, check VIF on the three aggregated metrics, aggregate to global score, and fit linear/GAM models with covariates.

**Note**: The plan.md suggests 'fixed regions: AAL indices 1-10', but the spec FR-002.1 explicitly requires 'top hub nodes' (data-driven). The tasks below follow the **spec's explicit requirement** for the scientific hypothesis. The plan's instruction is superseded by the spec.

**Independent Test**: The analysis script outputs a regression summary table, scatter plot, non-linearity check results, and regional p-values (if triggered).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for centrality metric calculation in `tests/contract/test_centrality.py`
- [ ] T022 [P] [US2] Integration test for regression model fitting in `tests/integration/test_regression.py`

### Implementation for User Story 2

- [P] T023 [D] [US2] **Calculate Data-Driven Hub Centrality**: From preprocessed fMRI data, extract functional connectivity matrices. **Calculate degree centrality for all regions, select the top N hub nodes (data-driven selection per FR-002.1)**. Calculate degree, betweenness, and eigenvector centrality for **these selected hub regions** using `networkx`. Save raw metrics for these hub regions to `data/processed/centrality/subject_id_metrics.csv` (columns: `subject_id`, `region_id`, `region_name`, `degree`, `betweenness`, `eigenvector`). (Depends on T016, T013)
- [D] T024a [US2] **Read and Validate Input**: Read `data/processed/centrality/subject_id_metrics.csv` (T023). Validate that it contains rows per subject corresponding to the selected hub regions. **Output**: Save validation status to `data/processed/centrality/validation_status.csv` with columns `subject_id`, `is_valid`. (Depends on T023)
- [D] T024b [US2] **Compute Global Score**: From the validated data (T024a), **aggregate the metrics from the selected hub regions** into a single 'global_centrality' score per subject (e.g., mean of the hub region values for each metric type, or mean of all values). Save to `data/processed/centrality/global_scores.csv` in `code/analysis/centrality.py`. (Depends on T024a)
- [P] T025 [US2] **Calculate Mean FD**: Read fMRIPrep confounds (`data/processed/fmriprep/*/desc-confounds_timeseries.tsv`), calculate Mean Framewise Displacement per subject, and save to `data/processed/behavioral/fd_mean.csv` in `code/analysis/centrality.py`. (Depends on T016)
- [D] T026 [US2] **Calculate VIF**: Load `data/processed/centrality/subject_id_metrics.csv` (T023). **For each subject, aggregate the hub region-level values into three subject-level values**: one 'degree' (mean of hubs), one 'betweenness' (mean of hubs), one 'eigenvector' (mean of hubs). **Calculate Variance Inflation Factor (VIF)** for these **three aggregated metrics** (degree, betweenness, eigenvector) across the full subject set. Save VIF values to `data/processed/centrality/vif_values.csv` in `code/analysis/centrality.py`. (Depends on T024b)
- [D] T027a [US2] **Determine Predictor Set (Decision)**: Read `vif_values.csv` (T026). **IF** any of the three VIF values > 5: Mark decision as 'PCA-Adjusted'. **ELSE**: Mark decision as 'Global'. Save decision to `data/processed/centrality/model_decision.csv` (columns: `decision`, `vif_max`). (Depends on T026)
- [D] T027b [US2] **Execute PCA (if needed)**: **IF** decision is 'PCA-Adjusted' (from T027a): Run PCA on the three aggregated metrics (degree, betweenness, eigenvector) from the hub set, retain first component. **ELSE**: Do nothing. Save the selected predictor set (either 'Global_Centrality' or 'PCA_Component_1') to `data/processed/centrality/model_predictors.csv` (columns: `model_type`, `selected_predictors`, `formula_string`). (Depends on T027a)
- [D] T027c [US2] **Report Multicollinearity**: Read `vif_values.csv` (T026) and `model_decision.csv` (T027a). **Explicitly write** the VIF values, the threshold (5), and the decision logic to the `reproducibility_report.json` under `pipeline_metrics.multicollinearity_check` with structure: `{\"vif_values\": {...}, \"threshold\": 5, \"decision\": \"...\", \"logic\": \"...\"}` to satisfy SC-004. (Depends on T027a)
- [D] T028a [US2] **Prepare Formula**: Read `model_predictors.csv` (T027b), `fd_mean.csv` (T025), and behavioral data from `data/processed/behavioral/subject_scores.csv` (T017). **Construct the formula string**: If `model_type`='PCA-Adjusted', formula is `Improvement ~ PCA_Component + Age + Sex + Mean_FD`. Else, formula is `Improvement ~ Global_Centrality + Age + Sex + Mean_FD`. Save formula to `data/processed/regression/formula.txt`. (Depends on T027b, T025, T017)
- [D] T028b [US2] **Fit Linear Regression**: Read `formula.txt` (T028a) and input data. Fit model using `statsmodels`. Save summary to `data/processed/regression/linear_model_summary.csv` in `code/analysis/regression.py`. (Depends on T028a)
- [D] T029 [US2] **Fit Null Model & Generate Residuals**: Fit intercept-only model (`Improvement ~ 1`) using the same covariates (Age, Sex, Mean_FD) as the full model but without the centrality predictor. **Save null model residuals to `data/processed/validation/null_residuals.csv`**. Do NOT save baseline R² separately. (Depends on T028a)
- [D] T030a [US2] **Fit GAM Model**: Fit a Generalized Additive Model (GAM) using the SAME predictor set as T028. **The output of this task (AIC/BIC comparison with Linear Model) is the specific deliverable to 'test' non-linearity per FR-003.** Save summary to `data/processed/regression/gam_model_summary.csv` in `code/analysis/regression.py`. (Depends on T028a)
- [D] T030b [US2] **Fit Polynomial Model**: Fit a Polynomial Regression model (degree=2) using the SAME predictor set as T028. **The output of this task (AIC/BIC comparison with Linear Model) is the specific deliverable to 'test' non-linearity per FR-003.** Save summary to `data/processed/regression/poly_model_summary.csv` in `code/analysis/regression.py`. (Depends on T028a)
- [D] T031 [US2] **Generate Scatter Plot**: Generate scatter plot with regression line and non-linearity fits in `code/analysis/regression.py`. (Depends on T030a, T030b)
- [D] T032 [US2] **Regional Analysis Fallback**: **IF** VIF > 5 (from T026) OR **model validation fails** (defined as R² < 0.05 or p > 0.1 from T028b): Fit separate regression models for each of the ~90 regions (using metrics from T023) to generate regional p-values. Save to `data/processed/regression/regional_pvalues.csv`. **ELSE**: Skip and log "Regional analysis skipped (VIF acceptable)". (Triggers fallback only if needed). (Depends on T026, T028b)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation and Robustness Assessment (Priority: P3)

**Goal**: Perform Freedman-Lane permutation test and k-fold cross-validation to validate findings.

**Independent Test**: The validation module produces a null distribution histogram, empirical p-value, and cross-validated R²/RMSE.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Contract test for permutation test logic in `tests/contract/test_permutation.py`
- [ ] T034 [P] [US3] Integration test for cross-validation loop in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [P] T035 [US3] **Generate Null Distribution (Freedman-Lane)**: Read `null_residuals.csv` (T029). **Perform exactly 1000 iterations (shuffles) as per FR-004 (≥1000 shuffles)** using the Freedman-Lane procedure:
 1. Permute the residuals of the null model.
 2. **Re-fit the null model (including covariates: Age, Sex, Mean_FD)** on the permuted data to generate new permuted residuals.
 3. Refit the full model (using the same formula as T028) on the permuted data and record the coefficient for the primary predictor.
 **For each of the 1000 iterations, save the coefficient to `data/processed/validation/null_distribution.csv`**. Save distribution to `data/processed/validation/null_distribution.csv` in `code/analysis/validation.py`. **Explicitly ensure the null model is re-fit with covariates for every permutation.** (Depends on T029, T028b)
- [D] T036 [US3] **Calculate Empirical P-Value**: Read `null_distribution.csv` (T035) and the observed coefficient from `linear_model_summary.csv` (T028). Calculate empirical p-value. Save to `data/processed/validation/permutation_results.json` in `code/analysis/validation.py`. (Depends on T035, T028b)
- [P] T037a [US3] **Run Cross-Validation**: Perform **5-fold k-fold cross-validation** with `random_seed=42`. **Inputs**: Feature matrix from `data/processed/centrality/model_predictors.csv` (T027b) and target vector from `data/processed/behavioral/subject_scores.csv` (T017). **Output**: Calculate out-of-sample R² and RMSE and their standard deviations. Save raw metrics to `data/processed/validation/cv_raw_metrics.csv` in `code/analysis/validation.py`. (Depends on T027b, T017)
- [D] T037b [US3] **Compare to Baseline and Save**: Read `cv_raw_metrics.csv` (T037a) and `linear_model_summary.csv` (T028). Compare mean R² against the baseline (intercept-only model) performance. Save final metrics and comparison to `data/processed/validation/cv_results.json` in `code/analysis/validation.py`. (Depends on T037a, T028b)
- [D] T038 [US3] **Generate Null Distribution Histogram**: Generate histogram of null distribution and overlay observed coefficient in `code/analysis/validation.py`. (Depends on T035)
- [D] T039 [US3] **Conditional FDR Correction**: **IF** T032 was executed (Regional analysis triggered): Apply Benjamini-Hochberg FDR correction to the regional p-values from T032. Save to `data/processed/validation/fdr_corrected_pvalues.csv`. **ELSE**: Skip and log "FDR correction skipped (regional analysis not triggered)". (Depends on T032)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Finalization

**Purpose**: Generate final artifacts after all analysis and validation are complete

- [ ] T040 [US3] Generate final `reproducibility_report.json` with checksums, wall clock time, RAM usage, and ALL validation metrics (p-values, R², RMSE, baseline comparison, multicollinearity check) in `code/utils/metrics.py`. **Dependencies: T036, T037b, T038, T039.** (Depends on T036, T037b, T038, T039)
- [ ] T041 [US3] **Update Documentation**: Update `docs/` and `README.md` based on the final `reproducibility_report.json` (T040) to ensure consistency with the "Single Source of Truth". (Depends on T040)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Remove unused imports from all Python files in `code/`
- [ ] T047 [P] Optimize float32 usage in `code/data/preprocess.py` and `code/analysis/centrality.py`
- [ ] T048 [P] Add unit tests in `tests/unit/test_centrality.py`
- [ ] T049 [P] Run `quickstart.md` validation

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
- **Conditional Tasks**: Tasks T032 and T039 only execute if specific trigger conditions are met (VIF > 5 or model validation fails).
- **Data Flow**: T023 calculates metrics for **top N hub nodes (data-driven)**. T024a validates input. T024b aggregates hub regions. T026 calculates VIF on the three aggregated metrics. T027a/b decides model type. T027c reports VIF. T028 uses T027's decision. T029 generates null residuals. T035 permutes residuals (1000 times, seed 42) with **Freedman-Lane re-fit**. T037a/b performs CV (5-fold, seed 42) and compares to baseline.
- **Freedman-Lane Requirement**: T035 explicitly requires permuting residuals of the null model (T029) and **re-fitting the null model with covariates for every permutation** to preserve motion confound structure, as mandated by the plan.
- **Bias Control**: T023 targets **top N hub nodes (data-driven)** to ensure valid network topology analysis per spec FR-002.1. The plan's 'fixed region' instruction is superseded by the spec.
- **VIF Logic**: T026 calculates VIF on the three aggregated metrics (degree, betweenness, eigenvector) derived from the hub set. T027a/b decides between Global or PCA based on T026. T027c reports the decision. T028 uses T027's decision.
- **Motion Control**: T025 calculates Mean FD. T028 includes Mean_FD as a covariate.
- **Retention Gate**: T002 and T003 in Phase 0 enforce hard stops for missing data or low retention.
- **Logging**: T017 logs excluded subjects to a specific CSV file.
- **Spec/Plan Conflict**: The plan restricts centrality calculation to AAL3 indices 1-10 for bias control, while FR-002.1 implies the full atlas/data-driven selection. Tasks follow the spec's explicit requirement for data-driven hub selection. The plan's conflicting instruction is overridden by the spec.
- **Power Check**: T004a gate is N ≥ 50 (spec). T004b warning is N < 85 (plan).