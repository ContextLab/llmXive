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
- [X] T004b [P] Create `code/requirements.txt` with pinned dependencies: `nibabel`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `bids`, `requests`, `tqdm`, `pytest`, `nilearn`, `psutil`, `joblib`, `matplotlib`, `seaborn`
- [X] T004c [P] Implement `code/00_data_gate.py`: Verify OpenNeuro `ds000246` (Constitution VI, FR-001) availability. Parse metadata to ensure rs-fMRI and longitudinal MMSE/MOCA scores exist. Exit with `EXIT_CODE_NO_LABELS = 2` if missing. Log verification status. **Note**: This task uses `ds000246` as mandated by Spec/Constitution, overriding any conflicting references in plan.md.
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
> **NOTE: These tasks are sequential to code creation, NOT parallel.**

- [X] T014 [US1] Unit test for AAL atlas parcellation in `tests/unit/test_parcellation.py`. **Implementation**: Create test function `test_parcellation_applies_aal` that loads a dummy BIDS subject, applies the AAL atlas via `nilearn`, and asserts the output shape is (90, 90). **TDD Rule**: This file must exist and FAIL before T018 is implemented.
- [X] T015 [US1] Unit test for graph metric calculation (degree, efficiency) in `tests/unit/test_graph_metrics.py`. **Implementation**: Create test function `test_graph_metrics_calculation` that generates a dummy 90x90 adjacency matrix, runs the metric calculation logic, and asserts that degree, efficiency, and clustering coefficient are non-null and within valid ranges (e.g., degree < 90). **TDD Rule**: This file must exist and FAIL before T019 is implemented.
- [X] T016 [US1] Integration test for data filtering logic (MMSE/MOCA non‑null check) in `tests/integration/test_filtering.py`. **Implementation**: Create test function `test_filtering_excludes_missing_scores` that loads a mock dataset with some subjects having missing MMSE/MOCA at one timepoint. Assert that the output CSV contains only subjects with complete longitudinal data, and the exclusion log contains the correct subject IDs. Assert that if all subjects are excluded, the script exits with `EXIT_CODE_NO_ELIGIBLE`.

### Implementation for User Story 1

- [X] T017a [US1] Implement `code/01_download_and_filter.py` (Part 1): Download `ds000246` (Constitution VI, FR-001), parse BIDS metadata, and filter for subjects with non‑null MMSE/MOCA at both timepoints. Limit to a sample size defined by the minimum of a predetermined upper threshold and the total number of available eligible participants. Fail if zero eligible subjects. Output `data/processed/eligible_subjects.csv` and `data/artifacts/data_gate_status.json`. Exit with `EXIT_CODE_NO_ELIGIBLE = 3` if no eligible subjects found. **Note**: This task uses `ds000246` as mandated by Spec/Constitution, overriding any conflicting references in plan.md.
- [X] T017b [US1] Implement `code/01_download_and_filter.py` (Part 2): **Mandatory Logging**: Generate `data/processed/excluded_subjects.log` listing every excluded subject ID and the specific reason for exclusion (e.g., "Missing MMSE at follow-up"). This log must be created even if the list is empty (header only). **Depends on**: T017a.
- [X] T018 [US1] Implement `code/02_preprocess_and_parcellate.py`: Load raw BIDS data for subjects listed in `data/processed/eligible_subjects.csv`, perform motion correction and normalization using `nilearn` (realign to mean image, resample to MNI152), apply the fixed AAL atlas fetched via `nilearn.datasets.fetch_atlas_aal`, and calculate connectivity matrices. Output to `data/processed/connectivity_matrices/`. **Depends on**: T014 (Test), T017a, T017b.
- [ ] T019 [US1] Implement `code/03_compute_graph_metrics.py`: Calculate node degree, global efficiency, clustering coefficient, and path length for every subject; output to `data/processed/graph_metrics.csv`. Process subject‑by‑subject to stay within 7GB RAM. **CSV Schema**: `subject_id, node_degree, global_efficiency, clustering_coeff, path_length`. **Depends on**: T015 (Test), T018. **Internal Validation**: Include `psutil` to monitor peak RAM during calculation. **Constraint**: If peak RAM > 7GB during processing, FAIL immediately with `EXIT_CODE_RAM_EXCEEDED = 5`. Do not continue or warn silently.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Validation (Priority: P2)

**Goal**: Train a Random Forest classifier with nested cross‑validation to predict cognitive decline.

**Independent Test**: The pipeline can be executed to output `data/processed/model.pkl` and `data/processed/performance_report.json` containing ROC‑AUC and F1‑score for nested CV, without running the permutation test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for nested CV grid‑search logic in `tests/unit/test_nested_cv.py`. **Implementation**: Create test function `test_nested_cv_no_leakage` that runs the nested CV pipeline on a dummy dataset where the target is purely random noise. Assert that the mean ROC-AUC is not significantly better than the baseline of random guessing., confirming no data leakage from the inner loop. Also assert that the grid search explores the defined parameter space (even if fixed).
- [X] T022 [P] [US2] Integration test for model training and evaluation flow in `tests/integration/test_model_training.py`. **Implementation**: Create test function `test_full_training_flow` that runs the training script on a small subset of real data. Assert that `model.pkl`, `cv_results.json`, and `performance_report.json` are generated with valid schemas and non-empty content. <!-- FAILED: unspecified -->
- [ ] T041 [P] [US2] Unit test verifying that the collinearity filter correctly drops one of a pair of features with Pearson > 0.95 (Tests logic in T023)

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/04_train_model.py`: Define decline label (drop ≥ 3 points). Implement Nested CV (K-fold outer cross-validation, grid‑search inner). **Note on Spec Conflict Resolution**: FR-003 mandates fixed parameters `n_estimators=100` and `max_depth=None`. FR-010 mandates Nested CV. This task implements FR-010's Nested CV structure but **FIXES** the Random Forest parameters to FR-003 values (n_estimators=100, max_depth=None). The inner loop is used **strictly for nested feature selection** (Variance Thresholding + RFE) and collinearity handling, NOT for tuning n_estimators or max_depth. **Inside the inner CV loop**: perform collinearity check (exclude features with correlation > 0.95, keep higher‑variance feature), apply Variance Thresholding (`variance > 0.01`) and RFE to select ≤ 20 features, then fit Random Forest with fixed params. Output `data/processed/model.pkl`, `data/processed/cv_results.json` (Schema: `fold, n_estimators, max_depth, roc_auc, accuracy, f1_score`), and `data/processed/model_params.json`. **Depends on**: T019. <!-- FAILED: unspecified -->
- [ ] T024 [US2] Implement `code/05_evaluate_model.py`: Calculate ROC‑AUC, accuracy, and F1‑score per fold and mean; output to `data/processed/performance_report.json`. **JSON Schema**: `fold, roc_auc, accuracy, f1_score, mean_roc_auc, mean_accuracy, mean_f1_score`. **Depends on**: T023.
- [X] T025 [US2] Implement `code/11_external_outcome_check.py`: Check for MCI conversion data in the dataset; if unavailable, write a limitation note to `data/artifacts/limitations.txt` (output consumed by T031 for final report generation) (FR-011).
- [X] T026 [US2] Verify runtime: Ensure nested‑CV training completes within 30 minutes on the CPU‑only runner (use joblib with `n_jobs=2` and monitor elapsed time)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Validate model significance via permutation test and assess robustness via threshold sensitivity.

**Independent Test**: The pipeline can take an existing model and performance metric, run the permutation test, and output `data/processed/permutation_results.json` and `data/processed/sensitivity_report.json`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for p‑value calculation logic in `tests/unit/test_permutation.py`
- [X] T028 [P] [US3] Unit test for threshold sweep logic in `tests/unit/test_sensitivity.py`
- [ ] T042 [P] [US3] Add integration test that runs the full permutation pipeline on a **mini‑subset** (e.g., 5 subjects, 10 permutations) to ensure end‑to‑end correctness without exceeding CI limits.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/06_permutation_test.py`: **Runtime-Bounded Permutation Test**. Target n=500, bounded by max_runtime=2 hours (7200 seconds).
 1. **Pilot**: Run a single permutation with the full model logic to measure elapsed time (`pilot_time`).
 2. **Estimate**: Calculate `estimated_total_time = pilot_time * 500`.
 3. **Decision**: If `estimated_total_time > 7200`, calculate `n_executed = floor(7200 / pilot_time)`. If `n_executed < 10`, abort with `EXIT_CODE_RUNTIME_EXCEEDED = 4` and error "Runtime limit exceeded even for minimum n=10". Otherwise, proceed with `n_executed`.
 4. **Execute**: Run `n_executed` permutations (seed = 42), re‑train/re‑evaluate the model for each, and record ROC‑AUC.
 5. **Output**: `data/processed/permutation_results.json` with keys `p_value`, `distribution`, `original_score`, `n_permutations_requested=500`, `n_permutations_executed` (actual count), `runtime_estimate`. **Depends on**: T023.
- [ ] T030 [US3] Implement `code/07_sensitivity_analysis.py`:
 1. **Part 1 (Decision Threshold Sweep - FR-006)**: Perform decision threshold sweep over a range of values around the standard 0.50 mark. on the **baseline trained model** (from T023). Report false‑positive/false‑negative rates. Output `data/processed/decision_threshold_report.json`.
 2. **Part 2 (Label Definition Sensitivity - FR-012)**: Vary the decline‑definition threshold by testing drop values of **{, 3, 4} points** on raw MMSE/MOCA scores. **Implementation Requirement**: Create a parameterized wrapper for the training logic (T023) to accept the threshold as an argument. Re-train the model for each variation (2 and 4 points) to assess robustness of the label definition. Compare the FPR/FNR of the re-trained models against the baseline (3-point) model. Output `data/processed/label_sensitivity_report.json` and save re-trained models to `data/processed/label_sensitivity_models/`. **Depends on**: T023.
- [X] T031 [US3] Implement `code/09_generate_report.py`: Aggregate all results, explicitly label findings as "associational" (FR‑007), document limitations (read from `data/artifacts/limitations.txt` generated by T025), and output `data/artifacts/final_report.md`. **Depends on**: T024, T025, T029, T030.
- [X] T032 [US3] Implement `code/10_verify_success_criteria.py`: Check that ROC‑AUC > 0.50, p < 0.05, and total runtime < 6 h; write `VERIFICATION_STATUS` and `runtime_report.json`. **Exit Condition**: If SC-002 (ROC-AUC > 0.50) or SC-003 (p < 0.05) are not met, exit with `sys.exit(1)` and log "Success Criteria Not Met".

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates: Update `README.md` with execution order, dataset requirements, and how to reproduce each phase
- [X] T034 Code cleanup: Remove debug prints, ensure all random seeds are pinned to a fixed value to guarantee reproducibility., and enforce PEP 8 compliance via `flake8`
- [X] T035 Performance optimization: Refactor `code/03_compute_graph_metrics.py` to use `joblib.Parallel(n_jobs=2, backend="loky")` and verify runtime reduction (target < 30 min for 100 subjects).
- [X] T036 [P] Run the full `tests/` suite and ensure **all** tests pass
- [X] T037 Security hardening: Scan `data/raw/` for PII using `pybids`/`bids-validator`; automatically redact any personal identifiers found in JSON side‑cars or filenames
- [X] T038 [P] Run `quickstart.md` validation to ensure end‑to‑end reproducibility on a fresh runner
- [X] T043 [P] Add a CI step that logs peak memory usage for each major script (download, preprocessing, modeling, permutation) to `data/artifacts/memory_profile.log` for future audit

**Checkpoint**: Project ready for final review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion – BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) – No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) – Depends on T019 (graph_metrics.csv) completion
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) – Depends on T023 (model training) completion

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
- **T017b** depends on T017a.
- **T018** depends on T014 (Test) and T017a, T017b (sequential).
- **T019** depends on T015 (Test) and T018 (sequential).
- **T023** depends on T019 (sequential).
- **T024** depends on T023 (sequential).
- **T029** depends on T023 (sequential).
- **T030** depends on T023 (sequential).
- **T031** depends on T024, T025, T029, T030.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL – blocks all stories)
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
 - Developer A: User Story 1 (Data & Graphs)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Validation)
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
- **Critical**: Ensure `code/06_permutation_test.py` (T029) implements dynamic n reduction based on runtime estimation, bounded by 2 hours, rather than relying on CI kills.
- **Critical**: Ensure `code/04_train_model.py` correctly implements nested feature selection (Variance Threshold -> RFE) and collinearity handling within the inner loop (training fold only), while keeping hyperparameters fixed per FR-003.
- **Critical**: Ensure all tasks reference the correct dataset `ds000246` as per Constitution VI and Spec FR-001.
- **Critical**: Ensure `code/04_train_model.py` implements fixed parameters (n_estimators=100, max_depth=None) as per Spec FR-003, using Nested CV only for feature selection.
- **Critical**: Ensure `code/07_sensitivity_analysis.py` (T030) explicitly separates FR-006 (Decision Threshold) and FR-012 (Label Definition) logic, re-training only for FR-012.
- **Critical**: Ensure `code/03_compute_graph_metrics.py` fails immediately if RAM > 7GB.
- **Critical**: Ensure `code/01_download_and_filter.py` explicitly generates `excluded_subjects.log` as a mandatory output.