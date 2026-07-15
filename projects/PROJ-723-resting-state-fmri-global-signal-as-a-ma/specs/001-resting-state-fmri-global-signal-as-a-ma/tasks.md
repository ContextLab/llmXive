# Tasks: Resting‑State fMRI Global Signal as a Marker of Mind‑Wandering

**Input**: Design documents from `/specs/001-resting-state-fmri-global-signal-as-a-ma/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjusted based on plan.md structure

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

- [X] T001a Create `code/` directory at repository root
- [X] T001b Create `data/raw/` directory at repository root
- [X] T001c Create `data/processed/` directory at repository root
- [X] T001d Create `tests/` directory at repository root
- [X] T002 Initialize Python project with dependencies from `requirements.txt` (pandas, numpy, scikit-learn, nibabel, requests, pyyaml, statsmodels, scipy)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T004 Implement `code/config.py` to define paths, random seeds, and hyperparameters
- [~] T005 [P] Implement `code/utils.py` for logging, file I/O helpers, and error handling
- [~] T006 [P] Create `code/mwq_scoring.py` to document MWQ version, reverse-scoring rules, and total score calculation (Principle VII)
- [~] T007 [P] Implement `prepare_bids_structure()` function in `code/ingestion.py` to generate BIDS-compatible directory structure logic. Output: reusable function. Verification: Run on sample subject, verify `sub-<label>/func/` exists. (Phase 0, Step 3)
- [~] T008 [P] Implement `generate_sidecars()` function in `code/ingestion.py` to create JSON sidecars for fMRI runs. Output: reusable function. File pattern: `sub-<label>_task-rest_bold.json`. Required keys: `TR`, `voxel_size`, `pipeline_version`. (Phase 0, Step 3)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Metric Computation (Priority: P1) 🎯 MVP

**Goal**: Download HCP data, compute global signal amplitude (SD), and export a clean CSV with predictors and outcomes.

**Independent Test**: Run ingestion script on a small subset of subjects and verify output CSV contains `Subject_ID`, `Global_Signal_SD`, `MWQ_Score`, `Age`, `Sex`, `FD`, `DVARS` with no missing values.

### Implementation for User Story 1

- [~] T009 [US1] Implement data download logic in `code/ingestion.py` to fetch HCP resting-state fMRI (NPI source, parquet/zip format) and MWQ scores. Output: files in `data/raw/`. (FR-001) <!-- FAILED: unspecified -->
- [~] T010 [US1] [Requires: T009] Implement schema verification in `code/ingestion.py` to halt with `FATAL: Dataset Mismatch` if `contracts/dataset.schema.yaml` required columns (global_signal, global_signal_sd, etc.) are missing. Output: Log or exit code. (FR-001)
- [~] T011 [US1] [Requires: T010] Implement voxel-wise mean time series (global signal) computation per run in `code/ingestion.py` (FR-002)
- [~] T012 [US1] [Requires: T011] Implement standard deviation calculation of global signal per run and averaging across runs per subject in `code/ingestion.py` (FR-002)
- [~] T013 [US1] [Requires: T012] Implement subject validation logic to join fMRI and MWQ data, excluding unmatched pairs and logging counts (FR-009)
- [~] T014 [US1] [Requires: T013] Implement motion exclusion logic to filter subjects where **per-subject mean FD** > 0.5mm and log exclusion counts (FR-008)
- [ ] T015 [US1] [Requires: T014] Implement zero-variance check to exclude subjects with `global_signal_sd == 0` and log warnings
- [ ] T016 [US1] [Requires: T015] Generate `data/processed/cleaned_data.csv` containing Subject_ID, Global_Signal_SD, MWQ_Score, Age, Sex, Mean_FD, Mean_DVARS
- [ ] T017 [P] [US1] Unit test: Verify global signal SD calculation matches manual calculation on sample data in `tests/test_ingestion.py`
- [ ] T018 [P] [US1] Unit test: Verify exclusion logic for missing pairs and high motion subjects in `tests/test_ingestion.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Association Modeling and Baseline Comparison (Priority: P2)

**Goal**: Run ridge regression to predict MWQ from global signal amplitude (adjusted for covariates), compare against null model, and generate report.

**Independent Test**: Run modeling script on synthetic data (r=0.3) and verify out-of-fold Pearson r falls within 0.25–0.35 and null model performance is near zero.

### Implementation for User Story 2

- [ ] T019 [US2] Implement primary ridge regression pipeline in `code/modeling.py` with nested 5-fold CV for alpha tuning (FR-004)
- [ ] T020 [US2] [Requires: T019] Implement model structure `Y ~ Global_Signal_SD + FD + DVARS + Age + Sex` in `code/modeling.py` (FR-003, FR-004)
- [ ] T021 [US2] [Requires: T016] Implement null distribution generation in `code/modeling.py` by training on **[deferred]** permuted MWQ vectors (Plan Phase 2 Step 3, Complexity Tracking). Verification: Assert permutation count is 1,000 in output logs/metadata. (FR-005, Plan Constraint)
- [ ] T022 [US2] [Requires: T021] Implement empirical p-value calculation: proportion of null MAEs <= observed MAE (standard convention, SC-002). (FR-005)
- [ ] T023 [US2] [Requires: T016] Implement Reduced Model (Y ~ FD + DVARS + Age + Sex) to isolate GSA effect (Plan Phase 2 Step 3). Output: `data/results/delta_r2.json` containing Delta R². Verification: Verify file exists and contains valid JSON with numeric Delta R². (Plan Methodology)
- [ ] T024 [US2] [Requires: T016] Implement collinearity diagnostics (VIF, GSA-FD correlation) in `code/diagnostics.py`. Input: `data/processed/cleaned_data.csv`. Output: `data/results/diagnostics.json` with VIF values per predictor. Flag if VIF > 5 (log warning). (Plan Phase 1 Step 3)
- [ ] T025 [US2] [Requires: T020, T021, T022] Generate `data/results/model_report.json` containing mean out-of-fold MAE, Pearson r, R², p-value, and null distribution stats
- [ ] T026 [P] [US2] Unit test: Verify nested CV logic and alpha tuning on synthetic data in `tests/test_modeling.py`
- [ ] T027 [P] [US2] Unit test: Verify null model performance is near zero on permuted data in `tests/test_modeling.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate findings with alternative metrics (variance vs SD), additional confounds, and regularization parameter sweeps.

**Independent Test**: Run robustness script and verify reported correlation coefficients remain statistically significant across all variants.

### Implementation for User Story 3

- [ ] T028 [US3] [Requires: T016, T019] Implement sensitivity analysis in `code/robustness.py` to sweep alpha over a range of small to large values and report MAE variation (FR-006)
- [ ] T029 [US3] [Requires: T016, T019] Implement alternative metric analysis in `code/robustness.py` using global-signal variance instead of SD and report Pearson r (FR-007)
- [ ] T030 [US3] [Requires: T016, T019] Implement partial correlation analysis controlling for mean FD to verify independence of GSA effect. Verification: Assert p < 0.05 (SC-005). (FR-003, SC-005)
- [ ] T031 [US3] [Requires: T028, T029, T030] Generate `data/results/robustness_report.json` containing alpha sweep results, variance metric correlation, and partial correlation stats
- [ ] T032 [P] [US3] Unit test: Verify alpha sweep results match expected MAE variations in `tests/test_robustness.py`
- [ ] T033 [P] [US3] Unit test: Verify variance metric correlation is within ±0.05 of primary SD result in `tests/test_robustness.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Final Validation

**Purpose**: Aggregate results and verify success criteria.

- [ ] T034a [P] Aggregate all results into `data/results/final_report.json` (Primary, Null, Robustness). (SC-001 to SC-005)
- [ ] T034b [P] [Requires: T034a] Verify success criteria status in `final_report.json`: assert p-value < 0.05, correlation stability, etc. (SC-001 to SC-005)
- [ ] T035 [P] [Requires: T034a] Generate visualizations: `data/results/null_dist.png`, `data/results/alpha_sweep.png`, `data/results/corr_matrix.png` using `matplotlib`.
- [ ] T036 [P] Run end-to-end integration test on full pipeline with sample data subset

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
- **User Story 2 (P2)**: Depends on US1 (requires `cleaned_data.csv` from US1)
- **User Story 3 (P3)**: Depends on US1 (requires `cleaned_data.csv`) and modeling logic (T019), but can run in parallel with US2 reporting (T025).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- US3 (T028, T029, T030) can run in parallel with US2 reporting (T025) once T016 and T019 are complete.

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

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must be feasible on CPU-only CI with limited computational resources, including a small number of cores, approximately modest RAM, and no GPU. No 8-bit/4-bit quantization, no large LLMs, no deep nets from scratch.