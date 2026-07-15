# Tasks: Predicting Individual Differences in Sensory Processing Speed from Resting‑State EEG Power Spectra

**Input**: Design documents from `/specs/001-predict-sensory-speed-from-eeg/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project directory structure (`code/`, `tests/`, `data/raw/`, `data/interim/`, `data/processed/`, `code/utils/`)
- [X] T002 Initialize `requirements.txt` with pinned versions (mne, scikit-learn, pandas, numpy, scipy, matplotlib, seaborn, pyyaml)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` to define constants (paths, filter params, seeds, band definitions)
- [X] T005 [P] Implement `code/utils/eeg_helpers.py` with band-pass, notch, and variance rejection utilities
- [X] T006 [P] Implement `code/utils/stats_helpers.py` with Bonferroni, permutation, and MDES utilities
- [ ] T007 Create `code/01_download_data.py` to fetch PhysioNet EEG Motor Movement/Imagery data and verify checksums (FR-001)
- [ ] T008a [P] Create `code/00_feasibility_check_join.py` to join EEG and RT datasets on `participant_id` and validate demographic metadata (Phase 0.5 Gate Part 1). **Exit Condition**: If join fails or datasets incompatible, exit with code 1 and generate `data/processed/feasibility_report.md`. **Must run after T007 completes**.
- [ ] T008b [P] Create `code/00_feasibility_check_report.py` to generate `data/processed/feasibility_report.md` based on join results if T008a fails (Phase 0.5 Gate Part 2). **Must run after T008a completes**.
- [ ] T009 Setup environment configuration management and random seed pinning

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Band-Power Features and Behavioral Metrics (Priority: P1) 🎯 MVP

**Goal**: Ingest raw EEG and behavioral data, preprocess, extract PSD features, and compute median RTs.

**Independent Test**: Run on a subset of PhysioNet data; verify `data/processed/features.csv` contains one row per participant with delta/theta/alpha/beta/gamma power and median RT, no nulls.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/02_preprocess_eeg.py`: Apply 1-40Hz band-pass, 50/60Hz notch, reject channels >3SD variance, and implement participant exclusion logic (drop if >30% channels rejected) (FR-002). **Must run after T007 completes**.
- [X] T010b [US1] Implement ICA cleaning in `code/02_preprocess_eeg.py` to remove ocular/muscle artifacts (Constitution Principle VI). **Must run after T010 completes and before T012 starts**.
- [X] T012 [US1] Implement `code/03_extract_features.py`: Compute Welch's PSD on continuous 5-minute epochs using **4-second windows** with **[deferred] overlap (2s)** and aggregate power into delta, theta, alpha, low-beta, high-beta, and gamma bands (FR-003). **Must run after T010b completes**.
- [~] T013 [US1] Implement behavioral parsing: extract median RT, exclude outliers (<100ms, >2000ms), exclude participants if <70% trials remain (FR-004). **Must run after T010b completes**.
- [ ] T015 [US1] Implement relative power calculation (band/total) for all bands to control for total power confound (FR-010). Consume `data/processed/features_raw.csv` (from T012/T013 merge) and produce `data/processed/features.csv`. **Must run after T012 and T013 complete**.
- [~] T016 [US1] Validate schema of `data/processed/features.csv` (no nulls, correct columns, valid RT range). **Must run after T015 completes**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fit Predictive Models and Test Associations (Priority: P2)

**Goal**: Fit Linear/LASSO models, perform correlations, permutation tests, and non-linear checks.

**Independent Test**: Run modeling script on `features.csv`; verify `data/processed/model_results.json` contains R², RMSE, p-values, and Bonferroni flags.

### Implementation for User Story 2

- [~] T017 [P] [US2] Implement `code/04_modeling.py`: Fit Multiple Linear Regression with 5-fold CV (depends on `data/processed/features.csv`) (FR-005). **Must run after T016 completes**.
- [~] T018 [US2] Implement LASSO regression with lambda tuning to minimize RMSE (FR-005). **Must run after T017 completes**.
- [~] T019 [US2] Calculate and log Adjusted R² and optimal lambda to `data/processed/model_results.json`. **Must run after T018 completes**.
- [ ] T020 [P] [US2] Implement Pearson correlation tests between relative band powers and median RT (depends on `data/processed/features.csv`) (FR-006). **Must run after T016 completes**.
- [ ] T021 [US2] Apply Bonferroni correction for 6 bands (0.05/6 = 0.0083) as per Spec FR-006 and flag significant results. **Must run after T020 completes**.
- [ ] T022 [US2] Implement permutation test (sufficient shuffles) on held-out test set ONLY (using split indices from `data/processed/split_indices.json`, seed from config.py) to prevent data leakage (per Plan feasibility constraint) for R² significance (FR-007). **Must run after T017 completes**.
- [ ] T023 [US2] Perform post-hoc power analysis to estimate the required sample size (N) for R²=0.10 with power ≥ 0.80 and report in results (FR-011). **Must run after T019 completes**.
- [ ] T024 [P] [US2] Implement non-linear interaction analysis (polynomial alpha/beta) and F-test comparison (FR-012). **Must run after T019 completes**.
- [ ] T025 [US2] Generate `data/processed/correlations.csv` and `data/processed/non_linear_comparison.json`. **Must run after T021 and T024 complete**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Robustness Checks and Sensitivity Analysis (Priority: P3)

**Goal**: Re-run analysis with alternative parameters to test stability.

**Independent Test**: Run robustness script; verify `data/processed/robustness_report.csv` shows R² variation across window lengths and ICA status.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/05_robustness_analysis.py`: Re-run pipeline with shorter time windows (vs primary 4s) and without ICA cleaning (depends on US1 completion). **Must run after T016 completes**.
- [ ] T027 [US3] Compare R² stability and report percentage difference in alpha power means (FR-008). **Must run after T026 completes**.
- [ ] T028 [P] [US3] Implement `code/06_sensitivity_analysis.py`: Sweep p-value threshold from a stringent to a lenient level. (FR-009). **Must run after T021 completes**.
- [ ] T029 [US3] Generate sensitivity plot and report exact threshold where result becomes non-significant (FR-009). **Must run after T028 completes**.
- [ ] T030 [US3] Generate `data/processed/robustness_report.csv` and `data/processed/sensitivity_plot.png`. **Must run after T027 and T029 complete**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Validation

**Purpose**: Aggregate results and verify success criteria.

- [ ] T031 [P] Implement `code/07_generate_report.py` to aggregate all metrics into `data/processed/final_report.md`. **Must run after T030 completes**.
- [ ] T032 [P] Verify SC-001 to SC-005: Adjusted R², Bonferroni p-value, stability metrics, sensitivity threshold, and CPU feasibility by aggregating specific metrics into final report. **Must run after T031 completes**.
- [ ] T033 [P] Run unit tests for `utils/` helpers.
- [ ] T034 [P] Run integration test `tests/integration/test_pipeline.py` to ensure end-to-end flow.
- [ ] T035 [P] Run contract tests for `feature_schema` and `result_schema`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Reporting (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 output (`features.csv`)
- **User Story 3 (P3)**: Depends on US1 output (preprocessing) and US2 output (modeling)

### Within Each User Story

- Models before services (scripts)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 tasks can start in parallel if US1 is done
- All tests for a user story marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify `features.csv`)
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
 - Developer B: User Story 2 (once US1 data ready)
 - Developer C: User Story 3 (once US2 results ready)
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
- **CRITICAL**: Do not use `load_in_8bit` or GPU-specific code. All processing must run on CPU-only CI.
- **CRITICAL**: Ensure `code/00_feasibility_check_join.py` and `code/00_feasibility_check_report.py` run AFTER `code/01_download_data.py` to prevent wasted compute on missing data.
- **CRITICAL**: Primary analysis uses 4-second windows (Spec FR-003); robustness check uses 2-second windows (Spec FR-008).
- **NOTE**: Plan.md Phase 1 states 2-second windows as primary; this Task list corrects to 4-second windows to align with Spec FR-003. Plan.md flagged for kickback to align.