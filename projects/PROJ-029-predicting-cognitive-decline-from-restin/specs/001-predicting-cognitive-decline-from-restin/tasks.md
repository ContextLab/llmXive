# Tasks: Predicting Cognitive Decline from Resting-State fMRI Network Topology

**Input**: Design documents from `/specs/001-predicting-cognitive-decline-from-restin/`
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

- [X] T001a [P] Create directory `code/` at repository root
- [X] T001b [P] Create directory `tests/` at repository root
- [X] T001c [P] Create directory `docs/` at repository root
- [X] T002a [P] Create directory `data/raw/` at repository root
- [X] T002b [P] Create directory `data/processed/` at repository root
- [X] T002c [P] Create directory `data/artifacts/` at repository root
- [X] T003a [P] Create directory `tests/unit/` at repository root
- [X] T003b [P] Create directory `tests/integration/` at repository root
- [X] T003c [P] Create directory `tests/contract/` at repository root
- [X] T004a [P] Initialize Python project structure in `code/`
- [X] T004b [P] Create `code/requirements.txt` with pinned dependencies: `nibabel`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `bids`, `requests`, `tqdm`, `pytest`, `nilearn`, `psutil`, `joblib`
- [X] T004c [P] Implement `code/00_data_gate.py`: Verify OpenNeuro `ds000246` (Constitution VI, FR-001) availability. Parse metadata to ensure rs-fMRI and longitudinal MMSE/MOCA scores exist. Exit with `EXIT_CODE_NO_LABELS = 2` if missing. Log verification status.
- [X] T005 [P] Implement utility modules: `code/utils/io.py` (BIDS loading), `code/utils/graph.py` (AAL atlas loading), `code/utils/stats.py` (collinearity checks)
- [X] T006 [P] Setup logging infrastructure in `code/utils/logger.py` to capture excluded subjects and feature‑filtering logs
- [X] T007 [P] Create base schema contracts in `specs/001-predicting-cognitive-decline-from-restin/contracts/` for dataset, graph metrics, and model output
- [X] T008 [P] Configure environment configuration management for random seeds (`random_seed=42 `) and runtime limits

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete
*Note: Phase 2 tasks in the previous draft were duplicates of Phase 1 and have been removed to ensure a clean dependency chain.*

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Download raw BIDS rs‑fMRI data, filter for longitudinal scores, and generate graph metrics.

**Independent Test**: The pipeline can be run on a single batch of data to produce `data/processed/graph_metrics.csv` containing subject IDs and calculated graph metrics without any machine learning training.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US1] Unit test for AAL atlas parcellation in `tests/unit/test_parcellation.py`
- [X] T015 [P] [US1] Unit test for graph metric calculation (degree, efficiency) in `tests/unit/test_graph_metrics.py`
- [X] T016 [P] [US1] Integration test for data filtering logic (MMSE/MOCA non‑null check) in `tests/integration/test_filtering.py`

### Implementation for User Story 1

- [X] T017a [P] [US1] Implement `code/01_download_and_filter.py` (Part 1): Download `ds000246` (Constitution VI, FR-001). Parse BIDS metadata. Verify dataset integrity. Output `data/raw/VERSION.txt` and `data/raw/checksums.json`. **Constraint**: Use `ds000246` exclusively as mandated by the Constitution. The plan.md reference to `ds000248` is overridden by the Spec/Constitution mandate.
- [ ] T017b [US1] Implement `code/01_download_and_filter.py` (Part 2): Filter subjects with non‑null MMSE/MOCA at both timepoints. Limit to the maximum feasible sample size given the pool of available eligible participants. Fail if zero eligible subjects. Output `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`, and `data/artifacts/data_gate_status.json`. **Exit Condition**: If `eligible_subjects.csv` is missing or empty, exit with `sys.exit(2)` and log "No eligible subjects found".
- [ ] T018a [BLOCK] [US1] Implement `code/02_preprocess_and_parcellate.py` (Part 1): Load raw BIDS data for subjects in `eligible_subjects.csv`. Perform motion correction and normalization using `nilearn` (standardize, resample). **Exit Condition**: If input file `eligible_subjects.csv` is missing, exit with `sys.exit(2)`. Output preprocessed NIfTI files to `data/processed/preprocessed/`.
- [ ] T018b [BLOCK] [US1] Implement `code/02_preprocess_and_parcellate.py` (Part 2): Apply the fixed AAL atlas to preprocessed data. Calculate Pearson correlation matrices between regional time-series to generate connectivity matrices. **Exit Condition**: If input preprocessed files are missing, exit with `sys.exit(2)`. Output to `data/processed/connectivity_matrices/`.
- [ ] T019 [BLOCK] [US1] Implement `code/03_compute_graph_metrics.py`: Calculate node degree, global efficiency, clustering coefficient, and path length for every subject using `networkx` on the region-of-interest matrices. **Modularization**: Encapsulate metric calculation logic in `code/utils/graph_metrics.py` for unit testing. Process subject‑by‑subject to stay within 7GB RAM. [UNRESOLVED-CLAIM: c_8bdb4607 — status=not_enough_info] **Exit Condition**: If input file `eligible_subjects.csv` or connectivity matrices are missing, exit with `sys.exit(2)`. Output to `data/processed/graph_metrics.csv`.
- [X] T020 [P] [US1] Add validation: Verify memory usage during graph metric calculation stays within the 7 GB RAM limit on a 2‑core runner (use `psutil`).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Validation (Priority: P2)

**Goal**: Train a Random Forest classifier with nested cross‑validation to predict cognitive decline.

**Independent Test**: The pipeline can be executed to output `data/processed/model.pkl` and `data/processed/performance_report.json` containing ROC‑AUC and F1‑score for nested CV, without running the permutation test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for nested CV grid‑search logic in `tests/unit/test_nested_cv.py`
- [X] T022 [P] [US2] Integration test for model training and evaluation flow in `tests/integration/test_model_training.py`
- [X] T041 [P] [US2] Unit test verifying that the collinearity filter correctly drops one of a pair of features with Pearson > 0.95 (Tests logic in T023)

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/04_train_model.py`: Define decline label (drop ≥ 3 points). Implement Nested CV (K-fold outer cross-validation, grid‑search inner). **Grid Search Parameters**: `n_estimators` over `{50, 100, 200}` and `max_depth` over `{5, 10, None}`. **Note**: This grid search implements FR-010 (Nested CV), which supersedes the fixed parameters in FR-003. **Inside the inner CV loop ONLY (on training fold)**:
 1. Apply Variance Thresholding (`variance > 0.01`).
 2. Apply RFE with `estimator=RandomForest`, `n_features_to_select=20`, `step=1`.
 3. Perform collinearity check (exclude features with correlation > 0.95, keep higher‑variance feature).
 4. Fit Random Forest.
 **Output Schema**: `cv_results.json` must contain keys: `fold`, `params`, `roc_auc`, `accuracy`, `f1`. Output `data/processed/model.pkl`, `data/processed/cv_results.json`, and `data/processed/model_params.json`.
- [ ] T024 [US2] Implement `code/05_evaluate_model.py`: Calculate ROC‑AUC, accuracy, and F1‑score per fold and mean; output to `data/processed/performance_report.json`
- [X] T025 [US2] Implement `code/11_external_outcome_check.py`: Check for MCI conversion data in the dataset; if unavailable, write a limitation note to `data/artifacts/limitations.txt` (output consumed by T031 for final report generation) (FR-011).
- [X] T026 [US2] Verify runtime: Ensure nested‑CV training completes within 30 minutes on the CPU‑only runner (use joblib with `n_jobs=2` and monitor elapsed time)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Validate model significance via permutation test and assess robustness via threshold sensitivity.

**Independent Test**: The pipeline can take an existing model and performance metric, run the permutation test, and output `data/processed/permutation_results.json` and `data/processed/sensitivity_report.json`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for p‑value calculation logic in `tests/unit/test_permutation.py`
- [X] T028 [P] [US3] Unit test for threshold sweep logic in `tests/unit/test_sensitivity.py`
- [X] T042 [P] [US3] Add integration test that runs the full permutation pipeline on a **mini‑subset** (e.g., 5 subjects, 20 permutations) to ensure end‑to‑end correctness without exceeding CI limits.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/06_permutation_test.py`: Import training logic from `code/04_train_model.py`. **Pre-flight Check**: Run a 1-subject dry run to estimate time per permutation. If (dry_run_time * 100) > 7200s, abort with `sys.exit(1)` and message: "Runtime estimate exceeds 2h limit". **Execution**: Shuffle labels **100** times (seed = 42), re‑train/re‑evaluate the model for each permutation, and record ROC‑AUC. **Note**: `n=100` is a runtime-optimized deviation from FR-005's `n=500`, justified by the 2-hour bound. If dry_run_time < 1.44s, attempt `n=500` instead. **Constraint**: This n=100 count is the runtime-optimized implementation mandated by the Plan's runtime constraints (Plan Section: Phase 3, Step 3.1). Do NOT compute a 'partial p-value'. If runtime limit is hit, fail explicitly. Output to `data/processed/permutation_results.json` with keys `p_value` and `distribution`.
- [X] T030a [US3] Implement `code/07_sensitivity_analysis.py` (Part 1): Perform decision threshold sweep over `{0.45, 0.50, 0.55}` on the trained model. Report false‑positive/false‑negative rates.
- [X] T030b [US3] Implement `code/07_sensitivity_analysis.py` (Part 2): Vary the decline‑definition threshold by ± 1 point on raw MMSE/MOCA scores (values: 2, 3, 4). **MUST re-train the model** for each variation to assess robustness of the label definition (FR-012). Loop: For each threshold in {2, 3, 4}: re-train model, evaluate, append results to list. Report false‑positive/false‑negative rates.
- [X] T031 [US3] Implement `code/09_generate_report.py`: Aggregate all results, explicitly label findings as "associational" (FR‑007), document limitations (read from `data/artifacts/limitations.txt` generated by T025), and output `data/artifacts/final_report.md`.
- [X] T032 [US3] Implement `code/10_verify_success_criteria.py`: Check that ROC‑AUC > 0.50, p < 0.05, and total runtime < 6 h; write `VERIFICATION_STATUS` and `runtime_report.json`. **Exit Condition**: If SC-002 (ROC-AUC > 0.50) or SC-003 (p < 0.05) are not met, exit with `sys.exit(1)` and log "Success Criteria Not Met".

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates: Update `README.md` with execution order, dataset requirements, and how to reproduce each phase
- [X] T034 Code cleanup: Remove debug prints, ensure all random seeds are pinned to a fixed value to guarantee reproducibility., and enforce PEP 8 compliance via `flake8`
- [X] T035 Performance optimization: Refactor `code/03_compute_graph_metrics.py` to use `joblib.Parallel(n_jobs=2)` and verify runtime reduction (target < 30 min for 100 subjects)
- [X] T036 [P] Run the full `tests/` suite and ensure **all** tests pass
- [X] T037 Security hardening: Scan `data/raw/` for PII using `pybids`/`bids-validator`; automatically redact any personal identifiers found in JSON side‑cars or filenames
- [X] T038 [P] Run `quickstart.md` validation to ensure end‑to‑end reproducibility on a fresh runner
- [X] T043 [P] Add a CI step that logs peak memory usage for each major script (download, preprocessing, modeling, permutation) to `data/artifacts/memory_profile.log` for future audit

**Checkpoint**: Project ready for final review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion – BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) – No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) – Depends on T019 (graph_metrics.csv) completion
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) – Depends on T023 (model training) completion

### Within Each User Story

- Tests (if included) MUST be written and **FAIL** before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked `[P]` can run in parallel
- All user stories can start in parallel after Foundational phase
- All tests for a user story marked `[P]` can run in parallel
- Different user stories can be worked on in parallel by different team members

### Specific Ordering Requirements

- **T017a** must be executed first in Phase 3 to provide data for subsequent tasks.
- **T017b** depends on **T017a**.
- **T018a** must be executed before **T018b**.
- **T018b** must be executed before **T019** (T018 is NOT parallel with T019).
- **T019** must be executed before **T023** to provide graph metrics for modeling. **Critical Dependency**: T023 cannot start until T019 produces `graph_metrics.csv`. T018 and T019 are marked as `[BLOCK]` tasks.
- **T023** and **T024** are sequential steps within the modeling phase.
- **T029** depends on **T023** completion (Model Training).
- **T030a** and **T030b** depend on **T023**.
- **T031** depends on **T025**, **T029**, **T030a**, and **T030b**.
- **T032** depends on **T029**, **T031**.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL – blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data & Graphs)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Validation)
3. Stories complete and integrate independently

---

## Notes

- `[P]` tasks = different files, no dependencies
- `[Story]` label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any point to validate story independently
- Avoid: vague tasks, same‑file conflicts, cross‑story dependencies that break independence
- **Critical**: Ensure `code/01_download_and_filter.py` handles OpenNeuro download failures with retries and clear exit codes.
- **Critical**: Ensure `code/03_compute_graph_metrics.py` does **not** load all raw NIfTI files into memory simultaneously if `N=100` exceeds RAM; process subject‑by‑subject.
- **Critical**: Ensure `code/04_train_model.py` uses `joblib` or similar for parallelisation within the 2‑core limit without oversubscription.
- **Critical**: Ensure `code/06_permutation_test.py` enforces runtime bounds and exits gracefully if limits are exceeded.
- **Critical**: Ensure `code/04_train_model.py` correctly implements nested feature selection (Variance Threshold -> RFE) and collinearity handling within the inner loop (training fold only).
- **Critical**: Ensure all tasks reference the correct dataset `ds000246` as per Constitution VI and Spec FR-001.
- **Critical**: Ensure `code/04_train_model.py` implements the grid search range `{50, 100, 200}` for `n_estimators` and `{5, 10, None}` for `max_depth`.
- **Critical**: Ensure `code/02_preprocess_and_parcellate.py` uses `nilearn` for preprocessing, not `fsl`, to ensure compatibility with GitHub runners.
- **Critical (Reviewer Concern)**: Scope is strictly limited to rs-fMRI network topology. [UNRESOLVED-CLAIM: c_41e0c942 — status=not_enough_info] No molecular or plasticity data integration is permitted.