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
- [X] T004a [P] Initialize Python 3.11 project structure in `code/`
- [X] T004b [P] Create `code/requirements.txt` with pinned dependencies: `nibabel`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `bids`, `requests`, `tqdm`, `pytest`, `nilearn`, `psutil`, `joblib`, `fslpy`
- [X] T004c [P] Implement `code/00_data_gate.py`: Verify OpenNeuro `ds000246` (Constitution VI, FR-001) availability. Parse metadata to ensure rs-fMRI and longitudinal MMSE/MOCA scores exist. Exit with `EXIT_CODE_NO_LABELS = 2` if missing. Log verification status.
- [X] T005 [P] Implement utility modules: `code/utils/io.py` (BIDS loading), `code/utils/graph.py` (AAL atlas loading), `code/utils/stats.py` (collinearity checks)
- [X] T006 [P] Setup logging infrastructure in `code/utils/logger.py` to capture excluded subjects and feature‑filtering logs
- [X] T007 [P] Create base schema contracts in `specs/001-predicting-cognitive-decline-from-restin/contracts/` for dataset, graph metrics, and model output
- [X] T008 [P] Configure environment configuration management for random seeds (`random_seed=42`) and runtime limits

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

- [X] T017 [P] [US1] Implement `code/01_download_and_filter.py`: Download `ds000246` (Constitution VI, FR-001), parse BIDS metadata, filter for subjects with non‑null MMSE/MOCA at both timepoints, limit to `N = min(100, available_eligible)`, fail if zero eligible subjects. Output `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`, and `data/artifacts/data_gate_status.json`. <!-- FAILED: unspecified -->
- [ ] T018 [P] [US1] Implement `code/02_preprocess_and_parcellate.py`: Load raw BIDS data for subjects listed in `data/processed/eligible_subjects.csv`, perform motion correction using `fsl` (mcflirt with default reference volume and 6 degrees of freedom), normalization using `nilearn`, apply the fixed AAL atlas with a standard number of regions, and {{claim:c_5794f852}} (Constitution Principle VII, FR-002). Output to `data/processed/connectivity_matrices/`. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [ ] T019 [US1] Implement `code/03_compute_graph_metrics.py`: Calculate node degree, global efficiency, clustering coefficient, and path length for every subject; output to `data/processed/graph_metrics.csv`. Process subject‑by‑subject to stay within 7GB RAM. <!-- FAILED: unspecified -->
- [X] T020 [US1] Add validation: Verify memory usage during graph metric calculation stays within the 7 GB RAM limit on a 2‑core runner (use `psutil`).

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

- [ ] T023 [US2] Implement `code/04_train_model.py`: Define decline label (drop ≥ 3 points). Implement Nested CV (K-fold outer cross-validation, grid‑search inner). **Grid Search Parameters**: `n_estimators` over `{50, 100, 200}` and `max_depth` over `{5, 10, None}` (specific values chosen to satisfy FR-010 optimization requirements within CPU constraints). **Inside the inner CV loop**: perform collinearity check (exclude features with correlation > 0.95, keep higher‑variance feature), apply Variance Thresholding (`variance > 0.01`) and RFE to select ≤ 20 features, then fit Random Forest. Output `data/processed/model.pkl`, `data/processed/cv_results.json`, and `data/processed/model_params.json`. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T024 [US2] Implement `code/05_evaluate_model.py`: Calculate ROC‑AUC, accuracy, and F1‑score per fold and mean; output to `data/processed/performance_report.json` <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
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

- [ ] T029 [US3] Implement `code/06_permutation_test.py`: Import training logic from `code/04_train_model.py`. **Pre-flight Check**: Estimate runtime for 100 permutations; if > 2 hours, abort with error. **Execution**: Shuffle labels **100** times (seed = 42), re‑train/re‑evaluate the model for each permutation, and record ROC‑AUC. **Constraint**: Execute 100 permutations as a runtime-optimized override of FR-005's n=500 per Plan runtime constraints. Do NOT compute a 'partial p-value'. If runtime limit is hit, fail explicitly. Output to `data/processed/permutation_results.json` with keys `p_value` and `distribution`. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->
- [X] T030a [US3] Implement `code/07_sensitivity_analysis.py` (Part 1): Perform decision threshold sweep over `{0.45, 0.50, 0.55}` on the trained model. Report false‑positive/false‑negative rates.
- [X] T030b [US3] Implement `code/07_sensitivity_analysis.py` (Part 2): Vary the decline‑definition threshold by ± 1 point on raw MMSE/MOCA scores. **MUST re-train the model** for each variation to assess robustness of the label definition (FR-012). Report false‑positive/false‑negative rates.
- [X] T031 [US3] Implement `code/09_generate_report.py`: Aggregate all results, explicitly label findings as "associational" (FR‑007), document limitations (read from `data/artifacts/limitations.txt` generated by T025), and output `data/artifacts/final_report.md`.
- [X] T032 [US3] Implement `code/10_verify_success_criteria.py`: Check that ROC‑AUC > 0.50, p < 0.05, and total runtime < 6 h; write `VERIFICATION_STATUS` and `runtime_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates: Update `README.md` with execution order, dataset requirements, and how to reproduce each phase
- [X] T034 Code cleanup: Remove debug prints, ensure all random seeds are pinned to a fixed value to guarantee reproducibility., and enforce PEP 8 compliance via `flake8`
- [~] T035 Performance optimization: Refactor `code/03_compute_graph_metrics.py` to use `joblib.Parallel(n_jobs=2)` and verify runtime reduction (target < 30 min for 100 subjects) <!-- FAILED: unspecified -->
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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) – May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) – May integrate with US1/US2 but should be independently testable

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

- **T017** must be executed first in Phase 3 to provide data for subsequent tasks.
- **T023a** and **T024** are sequential steps within the modeling phase.
- **T030** is a single consolidated task covering all sensitivity analysis steps.
- **T019** must be executed before **T023a** to provide graph metrics for modeling.

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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- `[P]` tasks = different files, no dependencies
- `[Story]` label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same‑file conflicts, cross‑story dependencies that break independence
- **Critical**: Ensure `code/01_download_and_filter.py` handles OpenNeuro download failures with retries and clear exit codes.
- **Critical**: Ensure `code/03_compute_graph_metrics.py` does **not** load all raw NIfTI files into memory simultaneously if `N=100` exceeds RAM; process subject‑by‑subject.
- **Critical**: Ensure `code/04_train_model.py` uses `joblib` or similar for parallelisation within the 2‑core limit without oversubscription.
- **Critical**: Ensure `code/06_permutation_test.py` enforces n=500 permutations as per FR-005; failure to complete within 2 hours should be a job error, not a fallback to n=100.
- **Critical**: Ensure `code/04_train_model.py` correctly implements nested feature selection and collinearity handling within the inner loop.
- **Critical**: Ensure all tasks reference the correct dataset `ds000246` as per Constitution VI and Spec FR-001.
- **Critical**: Ensure `code/04_train_model.py` implements the grid search range `{50, 100, 200}` for `n_estimators` and `{5, 10, None}` for `max_depth`, noting the spec's likely typo.
