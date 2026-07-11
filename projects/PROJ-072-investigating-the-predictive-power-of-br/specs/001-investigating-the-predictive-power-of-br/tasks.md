# Tasks: Investigating the Predictive Power of Brain Network Metrics for Schizophrenia Diagnosis

**Input**: Design documents from `/specs/001-investigating-the-predictive-power-of-br/`
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

- [X] T001 Create project structure per implementation plan: Create root directories `code/`, `data/`, `data/raw/`, `data/processed/`, `data/metadata/`, `tests/`, `docs/`, `scripts/`, `state/`. Create `requirements.txt` at root. Create `__init__.py` in `code/` and `tests/`. Ensure all directories exist before proceeding to Phase 2.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with dependencies (`requirements.txt`: nibabel, numpy, pandas, scikit-learn, networkx, bctpy, scipy, huggingface_hub, nilearn, pydantic, joblib)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T005 Implement `scripts/hash_artifacts.sh` to generate SHA-256 hashes for `data/` and `code/` and update `state/` YAML (Constitution V)
- [X] T006 Create `code/__init__.py` and configure logging infrastructure
- [X] T007 Define `data/metadata/schema.yaml` (Pydantic models for Subject, ConnectivityMatrix, FeatureVector)
- [ ] T008 Implement `code/main.py` orchestrator with runtime monitoring (stop if >6h) and DATA_GAP stop condition

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw rs-fMRI data from OpenNeuro ds000030, preprocess (motion correction, normalization, bandpass low-frequency range), and generate subject-level connectivity matrices.

**Independent Test**: Run on a cohort of subjects.; verify output is square correlation matrices of appropriate dimension (CSV/NumPy) with valid dimensions, no NaNs, and values within the valid range for correlation coefficients..

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for data download validation in `tests/unit/test_preprocessing.py`: Implement `test_download_url_exists` which asserts `pipeline.download_url_exists('https://openneuro.org/datasets/ds000030')` returns `True`. Implement `test_download_checksum` which asserts `pipeline.verify_checksum('data/raw/ds000030.zip', 'expected_sha256')` returns `True`.
- [~] T010 [P] [US1] Integration test for preprocessing pipeline on 1 subject in `tests/integration/test_preprocessing.py`: Implement `test_preprocess_single_subject` which runs `pipeline.preprocess(subject_id='sub')` and asserts the output file `data/processed/sub-<id>_matrix.npy` exists, has shape `(90, 90)`, contains no NaNs, and all values are within `[-1.0, 1.0]`.

### Implementation for User Story 1

- [~] T011 [US1] Implement `code/preprocessing/download.py`: Download logic for OpenNeuro dataset ds000030. The research question and method remain unchanged as per the planning document guidelines, with specific empirical identifiers generalized to reflect the dataset source without asserting precise low-level values. References: OpenNeuro (); handle missing diagnostic labels by excluding subjects and logging the count to `data/metadata/exclusion_log.txt`.
- [~] T012 [US1] Implement `code/preprocessing/preprocess.py`: motion correction, normalization, and bandpass filtering (low-frequency range) using nilearn's FSL-compatible wrappers; verify output headers match FSL standard logs to ensure Constitution Principle VI compliance.
- [~] T013 [US1] Implement `code/preprocessing/parcellate.py`: AAL atlas parcellation to generate connectivity matrices.
- [~] T014 [US1] Implement motion flagging logic: exclude subjects with >2mm translation; update `data/metadata/subject_status.csv` with exclusion flags and reasons.
- [~] T015 [US1] Implement `code/preprocessing/metadata.py`: metadata generation (Subject ID -> Label mapping) and save to `data/metadata/subject_labels.csv`. <!-- FAILED: unspecified -->
- [ ] T015.5 [US1] Implement metadata parsing in `code/preprocessing/metadata.py` to detect presence of `medication_status` field in OpenNeuro JSON sidecars; save result as `analysis_config.json` with key `medication_status_available: true/false`.
- [~] T016 [US1] Add validation for positive semi-definite matrices (apply regularization if needed) and log anomalies.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Graph Metric Computation and Feature Extraction (Priority: P2)

**Goal**: Compute graph metrics (efficiency, modularity, centrality) and extract a feature vector per subject, highlighting prefrontal/hippocampal regions.

**Independent Test**: Run on synthetic matrix with known properties; verify efficiency=1.0 for fully connected graph; verify output dimensions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T017 [P] [US2] Unit test for graph metric calculator in `tests/unit/test_graph_metrics.py`: Implement `test_efficiency_full_graph` which creates a x10 matrix of all 1.0s and asserts `calculator.global_efficiency(matrix) == 1.0`. Implement `test_modularity_output` which asserts `calculator.modularity(matrix)` returns a value within the expected normalized range.
- [~] T018 [P] [US2] Integration test for feature extraction in `tests/integration/test_graph_metrics.py`: Implement `test_feature_extraction` which runs `calculator.extract_features(all_matrices)` and asserts the output `data/processed/features.csv` has a shape consistent with the number of subjects and the expected feature dimensionality., contains no NaNs, and includes columns for 'global_efficiency', 'local_efficiency', 'modularity', 'prefrontal_centrality', 'hippocampal_centrality'. <!-- ATOMIZE: requested -->

### Implementation for User Story 2

- [~] T019 [P] [US2] Implement `code/graph_metrics/calculator.py` to compute Global Efficiency, Local Efficiency, Modularity (Louvain), Betweenness Centrality.
- [~] T020 [US2] Implement `code/graph_metrics/calculator.py` to extract regional centrality specifically for Prefrontal and Hippocampal ROIs.
- [~] T021 [US2] Implement collinearity check (r > 0.8) in `code/graph_metrics/calculator.py`; if found, apply PCA and save reduced matrix to `data/processed/features_pca.csv`, OR drop features and log to `data/metadata/collinearity_log.txt`.
- [~] T022 [US2] Implement feature vector assembly (multiple metrics) and save to `data/processed/features.csv`. This task must run AFTER T019, T020, T021. It produces the PRIMARY feature set for the main analysis.
- [~] T023 [US2] Implement summary statistics report generation (mean/std per metric, stratified by group) in `docs/`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Classification and Statistical Validation (Priority: P3)

**Goal**: Train LR/SVM classifiers with nested CV, perform permutation tests (sufficient iterations) and FDR-corrected t-tests to validate predictive power.

**Independent Test**: Run on randomized labels; verify accuracy ~chance and permutation p > 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T024 [P] [US3] Unit test for permutation test logic in `tests/unit/test_validation.py`: Implement `test_permutation_p_value` which runs `validation.permutation_test(y_real, y_shuffled, 100)` and asserts the returned p-value is > 0.05 when labels are shuffled.
- [ ] T025 [P] [US3] Integration test for full classification pipeline in `tests/integration/test_classification.py`: Implement `test_full_pipeline` which runs the full pipeline on a small subset and asserts `data/processed/results.json` exists, contains 'accuracy', 'p_value', 'mde', and 'significance_flag' keys, and that `significance_flag` is `False` when labels are shuffled.

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `code/classification/models.py` with Logistic Regression and SVM, using strict stratified train-test split.
- [ ] T027 [US3] Implement Stability Selection in `code/classification/models.py` using the Meinshausen & Bühlmann algorithm: Manually implement a loop with multiple subsamples, [deferred] sample size per subsample, L1 penalty, and a retention frequency threshold of >60%. Save selected feature indices to `data/processed/stable_features.csv`. Do NOT use `sklearn.linear_model.RandomizedLasso` as it is deprecated and does not implement the full algorithm.
- [ ] T028 [US3] Implement `code/classification/validation.py` for non-parametric permutation t-tests with FDR correction.
- [ ] T029 [US3] Implement `code/classification/validation.py` for separate permutation test (sufficient iterations) to assess accuracy significance against chance.
- [ ] T030 [US3] Implement calculation of Cohen's d for significant group differences.
- [ ] T031 [US3] Implement sensitivity analysis data generation: Read `data/metadata/analysis_config.json`. If `medication_status_available` is false, generate simulated covariate `sim_med_status` (Bernoulli p=0.5, seed=42) and append it to `data/processed/features.csv` to create a NEW file `data/processed/features_sim_med.csv`. This file is for exploratory sensitivity analysis ONLY and must NOT replace `features.csv`.
- [ ] T031a [US3] Implement sensitivity analysis plan documentation: Generate `docs/sensitivity_plan.md`. This document must explicitly state: 1) The limitation (medication data missing), 2) The plan to simulate covariates (as per T031), 3) The conclusion that the primary analysis is 'associational only' and the simulation is a 'what-if' scenario. This satisfies FR-006's requirement to 'report a sensitivity analysis plan'.
- [ ] T032a [US3] Implement calculation of a 95% Confidence Interval for accuracy using **permutation-based resampling** (shuffling labels and re-running the classifier repeatedly to build the null distribution of accuracies); save results to `data/processed/ci_results.json`. This method must be consistent with the permutation testing approach mandated by FR-005 and SC-003, rather than bootstrapping.
- [ ] T032b [US3] Generate final report at `docs/results/final_report.md`:
 1. Read CI values from `data/processed/ci_results.json`.
 2. Calculate Minimum Detectable Effect (MDE) for the observed sample size (N=60) and power=0.8.
 3. Compute `significance_flag`:
 - If `ci_lower_bound >= 0.65` AND `observed_effect >= MDE`: `true`
 - If `ci_lower_bound >= 0.65` BUT `observed_effect < MDE`: `false` (Label: "Exploratory (Underpowered)")
 - Else: `false`
 4. Include Accuracy, Precision, Recall, AUC-ROC, p-values, and MDE in the report.
 5. Use the following Markdown structure:
 ```markdown
 # Final Report
 ## Classification Results
 - Accuracy: {value}
 - 95% CI: [{lower}, {upper}]
 - MDE: {mde_value}
 ## Significance Assessment
 - Significance Flag: {significance_flag}
 - Interpretation: {if underpowered: "Exploratory finding due to limited power"}
 ## Statistical Validation
 - Permutation p-value: {p_value}
 - FDR-corrected p-values: {list}
 ```

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `docs/` (figures generated programmatically from `data/`) including `sensitivity_plan.md` from T031a.
- [ ] T034 Code cleanup and refactoring for memory efficiency (ensure <7GB RAM usage)
- [ ] T035 Performance optimization: ensure pipeline completes <6h on 2-core CPU
- [ ] T036 [P] Additional unit tests for edge cases (missing labels, non-PSD matrices) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation and verify all artifacts are hashed

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (connectivity matrices)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (feature matrix)
 - **CRITICAL**: Classification tasks (US3) MUST run AFTER Feature Extraction (US2) completes.

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
Task: "Unit test for data download validation in tests/unit/test_preprocessing.py"
Task: "Integration test for preprocessing pipeline on 1 subject in tests/integration/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement code/preprocessing/download.py"
Task: "Implement code/preprocessing/preprocess.py"
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
- **Data Integrity**: All tasks involving data generation must use REAL data from OpenNeuro ds000030; synthetic data is strictly for unit testing logic or isolated sensitivity analysis (T031), not hypothesis validation.
- **Hardware Constraint**: No tasks may require GPU, CUDA, or >7GB RAM. All models must run in default precision on CPU.