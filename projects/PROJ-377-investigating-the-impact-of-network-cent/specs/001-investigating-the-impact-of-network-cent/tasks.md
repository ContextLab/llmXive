# Tasks: Investigating the Impact of Network Centrality on the Consolidation of Motor Memories

**Input**: Design documents from `/specs/001-network-centrality-motor-consolidation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project directory structure: `projects/PROJ-377-investigating-the-impact-of-network-cent/` with subdirs `code/`, `data/`, `tests/`, `state/`
- [ ] T001b [P] Initialize git repository and create `.gitignore` for data and artifacts
- [ ] T002 Initialize Python project with dependencies: `pandas`, `numpy`, `networkx`, `scikit-learn`, `statsmodels`, `nilearn`, `openneuro-cli`, `matplotlib`, `seaborn` in `code/requirements.txt`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [ ] T004 Setup data directory structure: `data/raw/`, `data/processed/`, `data/artifacts/`
- [ ] T005 [P] Implement logging infrastructure in `code/utils/logging.py` to track wall_clock_time and RAM usage
- [ ] T006 [P] Setup reproducibility reporting utility in `code/utils/metrics.py` to generate `reproducibility_report.json`
- [ ] T007 Create base data models/entities in `code/__init__.py` and `code/data/` for Subject and ConnectivityMatrix
- [ ] T008 Configure environment configuration management for dataset URLs and thresholds in `code/utils/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download OpenNeuro ds000030, preprocess with fMRIPrep (memory efficient), and extract behavioral metrics.

**Independent Test**: The pipeline produces a CSV with subject IDs, behavioral improvement scores, and pre-processed fMRI time-series for ≥ 50 subjects with no missing values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [ ] T010 [P] [US1] Integration test for download and exclusion logic in `tests/integration/test_data_ingestion.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement dataset download script using `openneuro-cli` in `code/data/download.py` targeting ds000030
- [ ] T012 [P] [US1] Implement fMRIPrep preprocessing wrapper with memory-efficient settings (float32, batch processing) in `code/data/preprocess.py`
- [ ] T013 [US1] Implement behavioral metric extraction (pre/post motor scores, age, sex) and subject exclusion logic in `code/data/preprocess.py`
- [ ] T014 [US1] Implement retention rate calculation and power check (N >= 85 warning) in `code/data/preprocess.py`
- [ ] T015 [US1] Add validation to ensure ≥ 80% subject retention and fail gracefully if behavioral data is missing
- [ ] T016 [US1] Add logging for excluded subjects and reasons in `code/data/preprocess.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Centrality Calculation and Association Modeling (Priority: P2)

**Goal**: Compute centrality metrics from connectivity matrices for ALL regions, calculate FD, check VIF, aggregate to global score, and fit linear/GAM models with covariates.

**Independent Test**: The analysis script outputs a regression summary table, scatter plot, non-linearity check results, and regional p-values (if triggered).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for centrality metric calculation in `tests/contract/test_centrality.py`
- [ ] T018 [P] [US2] Integration test for regression model fitting in `tests/integration/test_regression.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement functional connectivity matrix extraction for **FULL AAL3 atlas (~90 nodes)** using `nilearn.connectome.ConnectivityMeasure` and save to `data/processed/connectivity/subject_id_matrix.npy` in `code/analysis/centrality.py`
- [ ] T020 [US2] Implement centrality metric calculation (degree, betweenness, eigenvector) using NetworkX for **ALL regions (~90 nodes)**. Persist raw metrics to `data/processed/centrality/subject_id_metrics.csv` in `code/analysis/centrality.py`
- [ ] T020.5 [US2] **Extract Fixed Subset**: From `data/processed/centrality/subject_id_metrics.csv`, extract metrics for **fixed regions (AAL3 indices 1-10)**. Compute mean to create 'global_centralty' column. Save to `data/processed/centrality/global_scores.csv` in `code/analysis/centrality.py`. (Aligns with Plan's bias-control strategy).
- [ ] T021 [US2] Implement Mean Framewise Displacement (FD) calculation from fMRIPrep outputs (`data/processed/fmriprep/*/desc-confounds_timeseries.tsv`) and aggregate to mean per subject. Save to `data/processed/behavioral/fd_mean.csv` in `code/analysis/centrality.py`
- [ ] T022 [US2] Implement VIF check on degree, betweenness, and eigenvector metrics; if VIF > 5, switch to PCA components; load raw metrics from `data/processed/centrality/subject_id_metrics.csv` in `code/analysis/centrality.py`. **Output**: `data/processed/centrality/model_predictors.csv` (contains either Global_Centrality or PCA_Component + Age + Sex + Mean_FD).
- [ ] T023 [US2] Implement global centrality aggregation (mean of fixed subset 1-10) from validated metrics in `code/analysis/centrality.py`. (Note: This task is now largely superseded by T020.5 but kept for logic separation if T020.5 is refactored).
- [ ] T023.5 [US2] **Null Model Generation**: Implement generation of the 'null model' (intercept-only: `Improvement ~ 1`) and calculate its residuals. Save residuals to `data/processed/validation/null_residuals.csv`. This artifact is required for T030.
- [ ] T024 [US2] Implement Linear Regression model in `code/analysis/regression.py`. **Logic**: IF PCA used (from T022), formula is `Improvement ~ PCA_Component + Age + Sex + Mean_FD`; ELSE formula is `Improvement ~ Global_Centrality + Age + Sex + Mean_FD`. Save summary to `data/processed/regression/linear_model_summary.csv`.
- [ ] T025 [US2] Implement GAM/Polynomial non-linearity check and AIC/BIC comparison in `code/analysis/regression.py`. **Logic**: Use the SAME predictor set (PCA or Global) as determined in T022.
- [ ] T026 [US2] Generate scatter plot with regression line and non-linearity fit in `code/analysis/regression.py`
- [ ] T027.1 [US2] **Conditional Regional Analysis**: IF `global_model_p_value > 0.05` OR `config.regional_analysis_flag == true`: Fit separate regression models for each of the ~90 regions to generate regional p-values. Save to `data/processed/regression/regional_pvalues.csv`. ELSE: Skip and log "Regional analysis skipped per primary strategy". (Triggers fallback only if needed).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation and Robustness Assessment (Priority: P3)

**Goal**: Perform Freedman-Lane permutation test and k-fold cross-validation to validate findings.

**Independent Test**: The validation module produces a null distribution histogram, empirical p-value, and cross-validated R²/RMSE.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for permutation test logic in `tests/contract/test_permutation.py`
- [ ] T029 [P] [US3] Integration test for cross-validation loop in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement Freedman-Lane permutation test in `code/analysis/validation.py`. **Requirements**: Exactly **1000 shuffles** of the **null residuals** (from T023.5) with a **fixed random seed**. Calculate empirical p-value for the primary coefficient. Save to `data/processed/validation/permutation_results.json`.
- [ ] T031 [US3] Implement k-fold cross-validation in `code/analysis/validation.py`. **Requirements**: Calculate out-of-sample R² and RMSE. **Explicitly calculate and compare** the out-of-sample R² against the baseline R² (intercept-only model from T023.5). Save metrics and comparison to `data/processed/validation/cv_results.json`.
- [ ] T032 [US3] Generate null distribution histogram and empirical p-value calculation in `code/analysis/validation.py`
- [ ] T033.1 [US3] **Conditional FDR Correction**: IF `regional_analysis_flag == true` (i.e., T027.1 was executed): Apply Benjamini-Hochberg FDR correction to the regional p-values from T027.1. Save to `data/processed/validation/fdr_corrected_pvalues.csv`. ELSE: Skip and log "FDR correction skipped (regional analysis not triggered)".
- [ ] T034 [US3] [P] Contract test for permutation test logic in `tests/contract/test_permutation.py` (Kept for completeness if tests requested, removed duplicate T034/T035 from previous version).
- [ ] T035 [US3] [P] Integration test for cross-validation loop in `tests/integration/test_validation.py` (Kept for completeness if tests requested, removed duplicate T034/T035 from previous version).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Finalization

**Purpose**: Generate final artifacts after all analysis and validation are complete

- [ ] T036 [US3] Generate final `reproducibility_report.json` with checksums, wall clock time, RAM usage, and ALL validation metrics (p-values, R², RMSE, baseline comparison) in `code/utils/metrics.py`

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` and `README.md`
- [ ] T038 Code cleanup and refactoring
- [ ] T039 Performance optimization across all stories (ensure float32 usage and batch processing)
- [ ] T040 [P] Additional unit tests in `tests/unit/`
- [ ] T041 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Reporting (Phase 6)**: Depends on all validation tasks (Phase 5) completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
Task: "Implement dataset download script in code/data/download.py"
Task: "Implement fMRIPrep preprocessing wrapper in code/data/preprocess.py"
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
- **Conditional Tasks**: Tasks T027.1 and T033.1 only execute if specific trigger conditions are met (global model insignificant or explicit config flag).
- **Data Flow**: T020 saves ALL regions; T020.5 extracts fixed subset; T027.1 uses ALL regions if triggered.