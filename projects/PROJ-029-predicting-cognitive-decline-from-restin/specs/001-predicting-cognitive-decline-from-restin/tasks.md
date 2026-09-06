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
- [X] T004b [P] Create `code/requirements.txt` with pinned dependencies: `nibabel==4.0.2`, `networkx==3.2.1`, `scikit-learn==1.3.2`, `pandas==2.1.4`, `numpy==1.26.2`, `pybids==0.17.0`, `requests==2.31.0`, `tqdm==4.66.1`, `pytest==7.4.3`, `nilearn==0.10.2`, `psutil==5.9.7`, `joblib==1.3.2`, `matplotlib==3.8.2`, `seaborn==0.13.0`, `huggingface_hub==0.20.1`
- [X] T004c [P] Implement `code/00_data_gate.py`: Verify OpenNeuro `ds000246` (Constitution VI, FR-001) availability. Parse metadata to ensure rs-fMRI and longitudinal MMSE/MOCA scores exist. Exit with `EXIT_CODE_NO_LABELS = 2` if missing. Log verification status. **Note**: This task uses `ds000246` as mandated by Spec/Constitution, overriding the plan's incorrect reference to `ds000248`.
- [X] T005a [P] Implement `code/utils/io.py`: BIDS loading functions, dataset versioning checks, and checksum verification (Constitution III).
- [ ] T005b [P] Implement `code/utils/graph.py`: AAL atlas loading, connectivity matrix construction, and graph metric calculation wrappers.
- [ ] T005c [P] Implement `code/utils/stats.py`: Collinearity detection, variance thresholding, and statistical utility functions.
- [X] T006 [P] Setup logging infrastructure in `code/utils/logger.py` to capture excluded subjects and feature‑filtering logs
- [X] T007 [P] Create base schema contracts in `specs/001-predicting-cognitive-decline-from-restin/contracts/` for dataset, graph metrics, and model output
- [X] T008 [P] Configure environment configuration management for random seeds (`random_seed=42`) and runtime limits

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Download raw BIDS rs‑fMRI data, filter for longitudinal scores, and generate graph metrics.

**Independent Test**: The pipeline can be run on a single batch of data to produce `data/processed/graph_metrics.csv` containing subject IDs and calculated graph metrics without any machine learning training. **Critical**: If memory constraints cause any subject to fail processing, the pipeline MUST exit with a non-zero error code. The test is ONLY satisfied if the CSV contains ALL eligible subjects with no missing values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> **NOTE: These tasks are sequential to code creation, NOT parallel.**

- [X] T014 [US1] Unit test for AAL atlas parcellation in `tests/unit/test_parcellation.py`. **Implementation**: Create test function `test_parcellation_applies_aal` that loads a dummy BIDS subject, applies the AAL atlas via `nilearn`, and asserts the output shape is square with a fixed resolution.. **TDD Rule**: This file must exist and FAIL before T018 is implemented.
- [X] T015 [US1] Unit test for graph metric calculation (degree, efficiency) in `tests/unit/test_graph_metrics.py`. **Implementation**: Create test function `test_graph_metrics_calculation` that generates a dummy adjacency matrix of a moderate scale, runs the metric calculation logic, and asserts that degree, efficiency, and clustering coefficient are non-null and within valid ranges (e.g., degree < 90). **TDD Rule**: This file must exist and FAIL before T019 is implemented.
- [X] T016 [US1] Integration test for data filtering logic (MMSE/MOCA non‑null check) in `tests/integration/test_filtering.py`. **Implementation**: Create test function `test_filtering_excludes_missing_scores` that loads a mock dataset with some subjects having missing MMSE/MOCA at one timepoint. Assert that the output CSV contains only subjects with complete longitudinal data, and the exclusion log contains the correct subject IDs. Assert that if all subjects are excluded, the script exits with `EXIT_CODE_NO_ELIGIBLE`.

### Implementation for User Story 1

- [ ] T017a [US1] Implement `code/01_download_and_filter.py`: Download `ds000246` (Constitution VI, FR-001), parse BIDS metadata, and filter for subjects with non‑null MMSE/MOCA at both timepoints. **Dataset Override**: Explicitly use `ds000246` despite plan.md referencing `ds000248`. **Sample Size Logic**: Process ALL eligible subjects if N <= 100. If N > 100, process the first 100 subjects (sorted by subject ID) and log the remaining N-100 as excluded due to resource constraints in `data/artifacts/limitations.txt`. **Mandatory Logging**: Generate `data/processed/excluded_subjects.log` listing every excluded subject ID and the specific reason for exclusion (e.g., "Missing MMSE at follow-up" or "Resource Cap"). This log must be created even if the list is empty (header only). Fail if zero eligible subjects. Output `data/processed/eligible_subjects.csv` and `data/artifacts/data_gate_status.json`. Exit with `EXIT_CODE_NO_ELIGIBLE = 3` if no eligible subjects found. **Depends on**: T014 (Test).
- [ ] T018 [US1] Implement `code/02_preprocess_and_parcellate.py`: Load raw BIDS data for subjects listed in `data/processed/eligible_subjects.csv`, perform motion correction and normalization using `nilearn` (realign to mean image, resample to MNI152), apply the fixed AAL atlas fetched via `nilearn.datasets.fetch_atlas_aal`, and calculate connectivity matrices. Output to `data/processed/connectivity_matrices/`. **Depends on**: T014 (Test), T017a.
- [ ] T019 [US1] Implement `code/03_compute_graph_metrics.py`: Calculate node degree, global efficiency, clustering coefficient, and path length for every subject; output to `data/processed/graph_metrics.csv`. Process subject‑by‑subject to stay within 7GB RAM **CSV Schema**: `subject_id, node_degree, global_efficiency, clustering_coeff, path_length`. **Depends on**: T015 (Test), T018. **Internal Validation**: Include `psutil` to monitor peak RAM during calculation. **Constraint**: Implement streaming/chunked processing to ensure the pipeline never loads all NIfTI files into memory simultaneously. **Error Handling**: If a subject causes a `MemoryError` or processing failure, the script MUST log the error and subject ID to `data/processed/excluded_subjects.log` with the reason "MemoryError/Processing Failure", and then **exit with a non-zero error code**. **Do NOT** silently skip subjects or continue processing. This ensures the 'Single Source of Truth' is maintained by failing explicitly rather than producing partial, unaccounted-for data. The output `data/processed/graph_metrics.csv` must contain exactly the subjects listed in `data/processed/eligible_subjects.csv` that were successfully processed, or the script must fail if any subject cannot be processed. **Output**: `data/processed/processed_subjects.csv` (list of subjects actually processed) and `data/processed/graph_metrics.csv`. **Depends on**: T015 (Test), T018.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Predictive Modeling and Validation (Priority: P2)

**Goal**: Train a Random Forest classifier with nested cross‑validation to predict cognitive decline.

**Independent Test**: The pipeline can be executed to output `data/processed/model.pkl` and `data/processed/performance_report.json` containing ROC‑AUC and F1‑score for nested CV, without running the permutation test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T044 [US2] [FR-008] Unit test verifying that the collinearity filter correctly drops one of a pair of features with Pearson > 0.95. **Implementation**: Create test function `test_collinearity_filter` that generates a feature matrix with two identical columns. Assert that the filter removes one and keeps the other. **TDD Rule**: This file must exist and FAIL *before* T023a implementation. **Dependency**: TDD Dependency: Must fail before T023a implementation.
- [X] T021 [P] [US2] Unit test for nested CV grid‑search logic in `tests/unit/test_nested_cv.py`. **Implementation**: Create test function `test_nested_cv_no_leakage` that runs the nested CV pipeline on a dummy dataset where the target is purely random noise. Assert that the mean ROC-AUC is not significantly better than the baseline of random guessing., confirming no data leakage from the inner loop. Also assert that the grid search explores the defined parameter space.
- [X] T022 [P] [US2] Integration test for model training and evaluation flow in `tests/integration/test_model_training.py`. **Implementation**: Create test function `test_full_training_flow` that runs the training script on a small subset of real data. Assert that `model.pkl`, `cv_results.json`, and `performance_report.json` are generated with valid schemas and non-empty content.

### Implementation for User Story 2

- [ ] T023a [US2] [FR-012] Implement `code/04_train_model_label_def.py`: Define cognitive decline labels. **Logic**: Decline = drop in MMSE/MOCA ≥ 3 points (configurable via CLI `--threshold`). Stable = no significant drop. **Input**: `data/processed/graph_metrics.csv` and `data/processed/eligible_subjects.csv`. **Output**: `data/processed/labels.csv` (subject_id, label). **Depends on**: T019.
- [ ] T023b [US2] [FR-008] Implement `code/04_train_model_feature_selection.py`: Implement nested feature selection logic. **Logic**: Inside the inner CV loop, perform collinearity check (exclude features with correlation > 0.95, keep higher‑variance feature), apply Variance Thresholding (`variance > 0.01`) and RFE to select ≤ 20 features. **Critical**: All feature selection steps MUST be fit **ONLY on the training fold** of the inner loop. **Output**: `code/utils/feature_selection.py` (reusable module). **Depends on**: T044.
- [ ] T023c [US2] [FR-010] [FR-003] Implement `code/04_train_model_core.py`: Implement **Nested Cross-Validation** with an outer $k$-fold loop and an **inner grid search**. **Design Decision**: FR-010 (Nested CV with Grid Search) SUPERSEDES FR-003's fixed-parameter requirement for the purpose of hyperparameter tuning. **Explicit Grid Values**: `n_estimators: [a range of values spanning from low to high counts]` and `max_depth: [None, moderate, high]`. **Input**: `data/processed/labels.csv` and `data/processed/graph_metrics.csv`. **Logic**: Use the feature selection module from T023b. Fit Random Forest with grid search parameters. **TDD Rule**: This task depends on T044 (Test) which must fail before implementation. **Output**: `data/processed/cv_results.json` (Schema: `fold, n_estimators, max_depth, roc_auc, accuracy, f1_score`). **Depends on**: T019, T023a, T023b, T044.
- [ ] T023d [US2] [FR-004] Implement `code/04_train_model_cli.py`: Expose a CLI entry point that accepts `--threshold <int>` (default 3) to allow T030b to re-train with different thresholds. **Logic**: Orchestrates T023a, T023b, T023c. **Output**: `data/processed/model.pkl`, `data/processed/model_params.json` (containing the best parameters found), and `data/processed/performance_report.json`. **Depends on**: T023a, T023b, T023c.
- [ ] T023e [US2] [FR-010] Implement `code/04_train_model_doc.py`: Document the justification for superseding FR-003 (Fixed Parameters) with FR-010 (Nested CV with Grid Search). **Output**: Add a section "Requirement Deviation: Model Architecture" to `data/artifacts/limitations.txt` and include a comment block in `code/04_train_model_core.py` explaining the deviation and referencing the plan's Requirement Mapping. **Depends on**: T023c.
- [X] T024 [US2] Implement `code/05_evaluate_model.py`: Calculate ROC‑AUC, accuracy, and F1‑score per fold and mean; output to `data/processed/performance_report.json`. **JSON Schema**: `fold, roc_auc, accuracy, f1_score, mean_roc_auc, mean_accuracy, mean_f1_score`. **Depends on**: T023d.
- [X] T025 [US2] [FR-011] Implement `code/11_external_outcome_check.py`: **Verify existence** of MCI conversion data in the **OpenNeuro ds000246** dataset metadata. **Logic**: If MCI data is present, perform correlation analysis and output `data/processed/mci_correlation_results.json`. If unavailable, write a limitation note to `data/artifacts/limitations.txt` (output consumed by T031 for final report generation) stating "MCI conversion data not found in ds000246 metadata; limitation documented." **Constraint**: Do NOT attempt to fetch external molecular data or use other datasets (e.g., Allen Brain Atlas, PsychENCODE) as this violates Constitutional Principle VI. **Depends on**: T017a.
- [X] T026 [US2] Verify runtime: Ensure nested‑CV training completes within 30 minutes on the CPU‑only runner (use joblib with `n_jobs=2` and monitor elapsed time)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Validate model significance via permutation test and assess robustness via threshold sensitivity.

**Independent Test**: The pipeline can take an existing model and performance metric, run the permutation test, and output `data/processed/permutation_results.json` and `data/processed/sensitivity_report.json`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for p‑value calculation logic in `tests/unit/test_permutation.py`
- [X] T028 [P] [US3] Unit test for threshold sweep logic in `tests/unit/test_sensitivity.py`
- [X] T042a [P] [US3] Unit test for mini-permutation setup in `tests/unit/test_permutation_setup.py`. **Implementation**: Create test function `test_mini_permutation_setup` that creates a mock dataset of a small number of subjects and verifies the data loading logic.
- [X] T042b [P] [US3] Integration test for mini-permutation execution in `tests/integration/test_mini_permutation.py`. **Implementation**: Create test function `test_mini_permutation_run` that runs the permutation logic on the mock dataset with a sufficient number of iterations and asserts the output format.

### Implementation for User Story 3

- [ ] T029 [US3] [FR-005] [SC-003] Implement `code/06_permutation_test.py`: **Runtime-Bounded Permutation Test**. Target **n=500** (as per FR-005). **Hard Constraint**: Must complete exactly 500 permutations.
 1. **Pilot**: Run **1 pilot permutation** with the full model logic to measure elapsed time (`pilot_time`).
 2. **Estimate**: Calculate `estimated_total_time = pilot_time * 500`.
 3. **Decision**:
 - **Constraint**: If `estimated_total_time > 7200` (2 hours), **FAIL** the script immediately with `sys.exit(5)` and log "ERROR: Estimated runtime for n=500 permutations exceeds 2-hour limit. Cannot proceed without violating FR-005. Statistical rigor compromised if n is reduced."
 - **Do NOT** reduce n. FR-005 requires n=500.
 4. **Execute**: Run exactly 500 permutations (seed = 42), re‑train/re‑evaluate the model for each, and record ROC‑AUC.
 5. **Output**: `data/processed/permutation_results.json` with keys `p_value`, `distribution`, `original_score`, `n_permutations=500`, `runtime_estimate`, `status="completed"`. **Depends on**: T023d.
- [ ] T030a [US3] [FR-006] Implement `code/07_sensitivity_decision_threshold.py`: Perform decision threshold sweep over a range of values **from a lower bound to an upper bound in discrete steps** on the **baseline trained model** (from T023d). Report false‑positive/false‑negative rates. **No re-training required**. Output `data/processed/decision_threshold_report.json`. **Depends on**: T023d.
- [ ] T030b [US3] [FR-012] Implement `code/07_sensitivity_label_definition.py`: Vary the decline‑definition threshold by **±1 point** from the baseline (3 points). **Implementation Requirement**: Re-run the training script (`code/04_train_model_cli.py`) via CLI with modified arguments (e.g., `python code/04_train_model_cli.py --threshold 2`) to re-train the model for each variation (thresholds: **2, 3, 4** points). **Runtime Check**: Before initiating re-runs, estimate total time. If total time exceeds a predefined threshold, log a warning and proceed only if time permits.; otherwise, document the limitation. Compare the FPR/FNR of the re-trained models against the baseline (3-point) model. Output `data/processed/label_sensitivity_report.json` and save re-trained models to `data/processed/label_sensitivity_models/`. **Depends on**: T023a, T023d.
- [X] T031 [US3] Implement `code/09_generate_report.py`: Aggregate all results, explicitly label findings as "associational" (FR‑007), document limitations (read from `data/artifacts/limitations.txt` generated by T025 and T023e), and output `data/artifacts/final_report.md`. **Depends on**: T024, T025, T029, T030a, T030b, T022.
- [X] T032 [US3] Implement `code/10_verify_success_criteria.py`: Check that ROC‑AUC > 0.50, p < 0.05, and total runtime < 6 h; write `VERIFICATION_STATUS` and `runtime_report.json`. **Exit Condition**: If SC-002 (ROC-AUC > 0.50) or SC-003 (p < 0.05) are not met, **exit with `sys.exit(1)`** and log "Success Criteria Not Met". This ensures the pipeline fails explicitly rather than just reporting, implementing the verification requirement for Success Criteria SC-002 and SC-003. **Depends on**: T031.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Plasticity & Biological Grounding (Priority: P4 - Revision)

**Goal**: Address reviewer concerns regarding static topology vs. dynamic synaptic plasticity by explicitly documenting the limitation, as external data fetching is forbidden.

**Independent Test**: The pipeline produces a report section explicitly stating the absence of molecular grounding as a primary limitation.

### Implementation for Revision (Plasticity Grounding)

- [ ] T051 [US3] [Rev] Update `code/09_generate_report.py` (T031) to include a dedicated section **"Biological Plausibility & Plasticity Limitations"**.
 1. **Content**: Explicitly discuss the reviewer's concern (static vs. dynamic).
 2. **Integration**: Incorporate the output from `code/08_plasticity_grounding.py` (T050 - **REMOVED**). Since T050 is removed, this task must explicitly state: "The model relies on static topology. Without concurrent measures of synaptic density or plasticity-related gene expression (e.g., CREB pathway) from the designated OpenNeuro ds000246 cohort, the mechanism of decline remains correlational. External data sources (Allen Brain Atlas, PsychENCODE) were not used to maintain constitutional compliance (Principle VI)."
 3. **Framing**: Ensure the conclusion emphasizes that the topology is a *proxy* for potential plasticity failure, not a direct measure of it. **Depends on**: T031.

**Checkpoint**: Revision concerns addressed; model grounded in biological reality (or explicitly limited).

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates: Update `README.md` with execution order, dataset requirements, and how to reproduce each phase
- [X] T038 Code cleanup: Remove debug prints, ensure all random seeds are pinned to a fixed value to guarantee reproducibility., and enforce PEP 8 compliance via `flake8`
- [X] T039 Performance optimization: Refactor `code/03_compute_graph_metrics.py` to use `joblib.Parallel(n_jobs=2, backend="loky")` and verify runtime reduction (target < 30 min for A cohort of subjects).
- [X] T040 [P] Run the full `tests/` suite and ensure **all** tests pass
- [X] T045 [P] Security hardening: Scan `data/raw/` for PII using `pybids`/`bids-validator`; automatically redact any personal identifiers found in JSON side‑cars or filenames
- [X] T042 [P] Run `quickstart.md` validation to ensure end‑to‑end reproducibility on a fresh runner
- [X] T043 [P] Add a CI step that logs peak memory usage for each major script (download, preprocessing, modeling, permutation) to `data/artifacts/memory_profile.log` for future audit

**Checkpoint**: Project ready for final review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately
- **User Stories (Phase 2+)**: All depend on Setup completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup – No dependencies on other stories
- **User Story 2 (P2)**: Can start after Setup – Depends on T019 (graph metrics)
- **User Story 3 (P3)**: Can start after Setup – Depends on T023d (model training) completion

### Within Each User Story

- Tests (if included) MUST be written and **FAIL** before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked `[P]` can run in parallel
- All user stories can start in parallel after Setup
- All tests for a user story marked `[P]` can run in parallel
- Different user stories can be worked on in parallel by different team members

### Specific Ordering Requirements

- **T017a** must be executed first in Phase 2 to provide data for subsequent tasks.
- **T018** depends on T014 (Test) and T017a.
- **T019** depends on T015 (Test) and T018 (sequential).
- **T044** (Test) must be written and fail *before* T023a implementation (TDD rule).
- **T023a** depends on T019.
- **T023b** depends on T044.
- **T023c** depends on T019, T023a, T023b, T044 (sequential).
- **T023d** depends on T023a, T023b, T023c.
- **T023e** depends on T023c.
- **T024** depends on T023d.
- **T029** depends on T023d.
- **T030a** depends on T023d.
- **T030b** depends on T023a, T023d.
- **T031** depends on T024, T025, T029, T030a, T030b, T022.
- **T032** depends on T031.
- **T051** depends on T031.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: User Story 1
3. **STOP and VALIDATE**: Test User Story 1 independently
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together
2. Once Setup is done:
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
- **Critical**: Ensure `code/03_compute_graph_metrics.py` does **not** load all raw NIfTI files into memory simultaneously; process subject‑by‑subject using streaming/chunked processing. **Crucially**, if a subject fails due to memory pressure, the script must exit with an error code rather than silently skipping, to maintain the 'Single Source of Truth'.
- **Critical**: Ensure `code/04_train_model_core.py` uses `joblib` or similar for parallelisation within the 2‑core limit without oversubscription.
- **Critical**: Ensure `code/06_permutation_test.py` (T029) implements a hard fail if n=500 cannot be completed within 2 hours, **NEVER** reducing n.
- **Critical**: Ensure `code/04_train_model_core.py` correctly implements nested feature selection (Variance Threshold -> RFE) and collinearity handling within the inner loop (training fold only), while performing the grid search for hyperparameters as per FR-010 (superseding FR-003).
- **Critical**: Ensure all tasks reference the correct dataset `ds000246` as per Constitution VI and Spec FR-001, overriding any plan references to `ds000248`.
- **Critical**: Ensure `code/04_train_model_core.py` implements the grid search for `n_estimators` and `max_depth` with valid numeric values `[50, 100, 200]` and `[None, 10, 20]`.
- **Critical**: Ensure `code/07_sensitivity_decision_threshold.py` (T030a) and `code/07_sensitivity_label_definition.py` (T030b) explicitly separate FR-006 (Decision Threshold) and FR-012 (Label Definition) logic, re-training only for FR-012 via CLI.
- **Critical**: Ensure `code/03_compute_graph_metrics.py` implements streaming/chunked processing and explicit error handling for memory failures.
- **Critical**: Ensure `code/01_download_and_filter.py` explicitly generates `excluded_subjects.log` as a mandatory output.
- **Critical**: Ensure `code/10_verify_success_criteria.py` (T032) exits with `sys.exit(1)` if success criteria are not met.
- **Critical**: Ensure `code/11_external_outcome_check.py` (T025) strictly checks `ds000246` for MCI data and does not attempt to fetch external molecular data.
- **Critical**: Ensure `code/04_train_model_cli.py` exposes a CLI interface for re-training with different thresholds.
- **Critical**: Ensure `code/06_permutation_test.py` (T029) enforces a target of 500 and fails if runtime constraints prevent it.
- **Critical**: Ensure `code/07_sensitivity_label_definition.py` (T030b) explicitly separates FR-006 (Decision Threshold) and FR-012 (Label Definition) logic.
- **Critical**: Ensure `code/04_train_model_core.py` implements the grid search for `n_estimators` and `max_depth` with valid numeric values.
- **Note**: Phase 5 (Plasticity & Biological Grounding) has been updated to address the Eric Kandel-simulated review regarding static topology vs. dynamic synaptic plasticity by documenting the limitation rather than fetching forbidden data.
- **Note**: T050 has been removed as it violated Constitution Principle VI. T051 now handles the limitation documentation.
- **Note**: T023e ensures the deviation from FR-003 to FR-010 is documented.
- **Note**: T023 is split into T023a, T023b, T023c, T023d, T023e for executability.
- **Note**: T030 is split into T030a and T030b for executability.
- **Note**: T005 is split into T005a, T005b, T005c for executability.
- **Note**: T029 enforces n = 500 and fails if runtime exceeds limit.
- **Note**: T017a clarifies N=100 as a max cap, not a target to stop early if N < 100.
- **Note**: T017a dependency list corrected to remove self-reference.
- **Note**: T019 'Independent Test' block corrected to require failure on memory errors.