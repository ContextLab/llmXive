# Tasks: Investigating the Predictive Power of Brain Network Metrics for Schizophrenia Diagnosis

**Input**: Design documents from `/specs/001-investigating-the-predictive-power-of-br/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.,g., US1, US2, US3)
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

- [X] T001 Create project structure per implementation plan: Create root directories `code/`, `data/`, `data/raw/`, `data/processed/`, `data/metadata/`, `tests/`, `docs/`, `scripts/`, `state/`. Create `requirements.txt` at root. Create __init__.py in `code/` and `tests/`. Ensure all directories exist before proceeding to Phase 2.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with dependencies (`requirements.txt`: nibabel, numpy, pandas, scikit-learn, networkx, bctpy, scipy, huggingface_hub, nilearn, pydantic, joblib)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T005 Implement `scripts/hash_artifacts.sh` to generate cryptographic hashes for `data/` and `code/` and update `state/` YAML (Constitution V)
- [X] T006 Create `code/__init__.py` and configure logging infrastructure
- [X] T007 Define `data/metadata/schema.yaml` (Pydantic models for Subject, ConnectivityMatrix, FeatureVector)
- [X] T008 Implement `code/main.py` orchestrator with runtime monitoring (stop if >6h) and memory monitoring (stop if >7GB RAM using psutil for 5 consecutive seconds) and DATA_GAP stop condition. **Verification**: Assert script exits with code 1 if memory threshold exceeded.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw rs-fMRI data from OpenNeuro, preprocess (motion correction, normalization, bandpass low-frequency range), and generate subject-level connectivity matrices.

**Independent Test**: Run on a cohort of subjects.; verify output is square correlation matrices of appropriate dimension (CSV/NumPy) with valid dimensions, no NaNs, and values within the valid range for correlation coefficients.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Unit test for data download validation in `tests/unit/test_preprocessing.py`: Implement `test_download_url_exists` which asserts `pipeline.download_url_exists` returns `True` for a valid OpenNeuro dataset identifier. Implement `test_download_checksum` which asserts `pipeline.verify_checksum('data/raw/ds000030.zip', 'expected_sha256')` returns `True`.
- [X] T010 [P] [US1] Integration test for preprocessing pipeline on 1 subject in `tests/integration/test_preprocessing.py`: Implement `test_preprocess_single_subject` which runs the pipeline on the **first subject from data/raw/ds** and verifies output `data/processed/test_subject_matrix.csv` exists, is a 90x90 matrix, and contains no NaNs.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/preprocessing/download.py`: Download logic for an OpenNeuro dataset. [UNRESOLVED-CLAIM: c_196646e9 — status=not_enough_info] The research question and method remain unchanged as per the planning document guidelines, with specific empirical identifiers generalized to reflect the dataset source without asserting precise low-level values. References: OpenNeuro (); handle missing diagnostic labels by excluding subjects and logging the count to `data/metadata/exclusion_log.txt`.
- [X] T012 [US1] Implement `code/preprocessing/preprocess.py`: motion correction, normalization, and bandpass filtering (low-frequency range) using nilearn's FSL-compatible wrappers [UNRESOLVED-CLAIM: c_6ea54051 — status=not_enough_info]; verify output headers match FSL standard logs to ensure Constitution Principle VI compliance.
- [X] T013 [US1] Implement `code/preprocessing/parcellate.py`: AAL atlas parcellation to generate connectivity matrices. [UNRESOLVED-CLAIM: c_c9447631 — status=not_enough_info]
- [X] T015 [US1] Implement `code/preprocessing/metadata.py`: Generate `data/metadata/subject_labels.csv` mapping Subject ID to diagnostic label and preprocessing status. **Schema**: columns `subject_id` (str), `diagnosis` (str: 'Schizophrenia' or 'Control'), `status` (str: 'included' or 'excluded'). **Verification**: Assert file exists, has correct columns, and no NaN values. This task MUST run before T014.
- [X] T015.5 [US1] Implement metadata parsing in `code/preprocessing/metadata.py` to detect presence of `medication_status` field in OpenNeuro JSON sidecars; save result as `analysis_config.json` with key `medication_status_available: true` or `medication_status_available: false`. **Schema**: JSON object with single boolean key. **Verification**: Assert JSON file exists and contains exactly one boolean key. **Note**: The spec assumes medication status is missing; this task confirms that absence.
- [X] T014b [US1] Implement motion parameter check in `code/preprocessing/download.py`: Check if motion parameters exist in the dataset metadata. Save result to `data/metadata/motion_params_available.json` with key `motion_params_available: true/false`. **Verification**: Assert file exists.
- [X] T014 [US1] Implement motion flagging logic: **Depends on T015 and T014b**. If T014b found motion parameters, flag subjects with >2mm translation for inclusion as covariates. If T014b found NO motion parameters, exclude subjects with >2mm translation. Update `data/metadata/subject_status.csv` with exclusion flags and reasons. **Verification**: Assert file exists and contains correct flags based on T014b's output.
- [X] T016 [US1] Add validation for positive semi-definite matrices in `code/preprocessing/validate.py`: Apply regularization (add 1e-6 to diagonal) if matrix is not PSD. Log anomalies to `data/metadata/anomaly_log.txt` with format: `[subject_id] [timestamp] [reason] [regularization_applied]`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Graph Metric Computation and Feature Extraction (Priority: P2)

**Goal**: Compute graph metrics (efficiency, modularity, centrality) and extract a feature vector per subject, highlighting prefrontal/hippocampal regions.

**Independent Test**: Run on synthetic matrix with known properties; verify efficiency=1.0 for fully connected graph; verify output dimensions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for graph metric calculator in `tests/unit/test_graph_metrics.py`: Implement `test_efficiency_full_graph` which creates a x10 matrix of all 1.0s and asserts `calculator.global_efficiency(matrix) == 1.0`. Implement `test_modularity_output` which asserts `calculator.modularity(matrix)` returns a value within the expected normalized range.
- [X] T018 [P] [US2] Integration test for feature extraction in `tests/integration/test_graph_metrics.py`: Implement `test_feature_extraction` which runs `calculator.extract_features(all_matrices)` on a **synthetic matrix of moderate dimensionality** and asserts the output `data/processed/features.csv` has a shape consistent with the number of subjects and the expected feature dimensionality (e.g., **60 rows x 18 columns**), contains no NaNs, and includes columns for 'global_efficiency', 'local_efficiency', 'modularity', 'prefrontal_centrality', 'hippocampal_centrality'.

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/graph_metrics/calculator.py` to compute Global Efficiency, Local Efficiency, Modularity (Louvain), Betweenness Centrality. [UNRESOLVED-CLAIM: c_b90ffbe8 — status=not_enough_info]
- [X] T020 [US2] Implement `code/graph_metrics/calculator.py` to extract regional centrality specifically for Prefrontal and Hippocampal ROIs.
- [X] T021 [US2] Implement collinearity check (r > 0.8) in `code/graph_metrics/calculator.py`: If found, drop the feature with lower variance and log to `data/metadata/collinearity_log.txt`. **Decision Logic**: Define 'collinear' as pairwise correlation r > 0.8. If r > 0.8, remove the feature with lower variance. If >50% of features are collinear, apply PCA. **Output**: Save cleaned matrix to `data/processed/features_cleaned.csv`.
- [X] T022 [US2] Implement feature vector assembly (multiple metrics) and save to `data/processed/features.csv`. This task must run AFTER T019, T020, T021. It produces the PRIMARY feature set for the main analysis.
- [ ] T022b [US2] Verify regional centrality preservation in `code/graph_metrics/verify.py`: **Depends on T022**. Check that `data/processed/features.csv` contains columns 'prefrontal_centrality' and 'hippocampal_centrality'. If missing, raise `ERROR: Missing regional centrality columns: {cols}` and log to `data/metadata/feature_verification_log.txt`. **Verification**: Assert file exists and contains required columns.
- [X] T023 [US2] Implement summary statistics report generation in `docs/summary_stats.md`: Calculate mean and standard deviation for each metric, **stratified by diagnostic group ('Schizophrenia' vs. 'Control')**. Use subject labels from T015 to perform stratification. **Output**: Markdown file with two tables (one per group) and a comparison section. **Depends on T015**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Classification and Statistical Validation (Priority: P3)

**Goal**: Train LR/SVM classifiers with nested CV, perform permutation tests (sufficient iterations) and FDR-corrected t-tests to validate predictive power.

**Independent Test**: Run on randomized labels; verify accuracy ~chance and permutation p > 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for permutation test logic in `tests/unit/test_validation.py`: Implement `test_permutation_p_value` which runs `validation.permutation_test(y_real, y_shuffled, 100 (1411.7565, https://arxiv.org/abs/1411.7565))` where `y_real` is **60 random labels with 30/30 split (seed=42)** and `y_shuffled` is a **shuffled version**. Assert the returned p-value is > 0.05 when labels are shuffled.
- [X] T025 [P] [US3] Integration test for full classification pipeline in `tests/integration/test_classification.py`: Implement `test_full_pipeline` which runs the full pipeline on a **small subset (a limited number of subjects from data/processed/features.csv with shuffled labels)** and asserts `data/processed/results.json` exists, contains 'accuracy', 'p_value', 'mde', and 'significance_flag' keys, and that `significance_flag` is `False`.

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement `code/classification/models.py` with Logistic Regression and SVM, using strict stratified train-test split. [UNRESOLVED-CLAIM: c_cde17073 — status=not_enough_info]
- [ ] T027a [US3] Implement Stability Selection algorithm class in `code/classification/models.py`: Manually implement a loop with **sample size per subsample = 30 ([deferred] of N=60)**, **subsamples**, L1 penalty, and a retention frequency threshold of >60%. Save selected feature indices to `data/processed/stable_features.csv`. Do NOT use `sklearn.linear_model.RandomizedLasso` as it is deprecated and does not implement the full algorithm.
- [X] T027b [US3] Integrate Stability Selection into the nested cross-validation loop in `code/classification/models.py`: **Depends on T027a**. Ensure Stability Selection is executed **inside the inner loop** of the nested CV structure. **Verification**: Assert that feature selection is re-run for every fold. Do NOT run on the full training set.
- [X] T027c [US3] Verify nested CV integration in `code/classification/models.py`: **Depends on T027b**. Add unit tests to confirm that feature selection logic is isolated to the inner loop and does not leak information from the test fold.
- [X] T028 [US3] Implement `code/classification/validation.py` for non-parametric permutation t-tests with FDR correction.
- [X] T029 [US3] Implement `code/classification/validation.py` for a separate permutation test (sufficient iterations) to assess accuracy significance against chance.
- [X] T030 [US3] Implement calculation of Cohen's d for significant group differences in `code/classification/validation.py`. Save results to `data/processed/cohen_d_results.json`.
- [X] T030b [US3] Implement calculation of Minimum Detectable Effect (MDE) in `code/classification/validation.py`: Calculate MDE for observed sample size (N=60) and power=0.8. [UNRESOLVED-CLAIM: c_cab934a6 — status=not_enough_info] Save results to `data/processed/mde_results.json` with keys: `mde_value` (float), `sample_size` (int), `power` (float).
- [ ] T031 [US3] Implement sensitivity analysis data generation: **Depends on T015.5**. Read `data/metadata/analysis_config.json`. **Schema**: JSON with key `medication_status_available`. If file is missing, **raise FileNotFoundError**. If `medication_status_available` is false, generate simulated covariate `sim_med_status` (Bernoulli p=0.5, seed=42, dtype=float) and append it to `data/processed/features.csv` to create a NEW file `data/processed/features_sim_med.csv`. **Verification**: Ensure `features_sim_med.csv` has exactly one additional column `sim_med_status` and is distinct from `features.csv`.
- [X] T031a [US3] Implement sensitivity analysis plan documentation: **Depends on T031**. Generate `docs/sensitivity_plan.md`. This document must explicitly state: 1) The limitation (medication data missing), 2) The plan to simulate covariates (as per T031), 3) The conclusion that the primary analysis is 'associational only' and the simulation is a 'what-if' scenario. This satisfies FR-006's requirement to 'report a sensitivity analysis plan'.
- [ ] T031b [US3] Run sensitivity analysis: **Depends on T031a and T031**. Re-run the classifier using `data/processed/features_sim_med.csv`. Save results to `data/processed/sensitivity_results.json` with schema: `accuracy` (float), `p_value` (float), `cohen_d_value` (float). **Verification**: Assert file exists and contains all keys.
- [ ] T032a [US3] Implement calculation of a confidence interval for accuracy using **permutation-based resampling**: **Depends on T029**. Shuffle labels, retrain model, record accuracy distribution. Save results to `data/processed/ci_results.json`. **Schema**: keys `accuracy` (float, 4 decimals), `lower_bound` (float, 4 decimals), `upper_bound` (float, 4 decimals), `method` (str: 'permutation'), `iterations` (int: 1000). This method aligns with SC-003 requirements.
- [ ] T032b [US3] Generate final report at `docs/results/final_report.md`: **Depends on T030b, T032a, T031a, T031b**.
 1. Read CI values from `data/processed/ci_results.json`.
 2. Read MDE value from `data/processed/mde_results.json` (output of T030b).
 3. Read Cohen's d from `data/processed/cohen_d_results.json` using key **'cohen_d_value'**.
 4. Read sensitivity results from `data/processed/sensitivity_results.json`.
 5. Compute `significance_flag`:
 - If `ci_lower_bound >= 0.65` AND `observed_effect >= MDE`: `true`
 - If `ci_lower_bound >= 0.65` BUT `observed_effect < MDE`: `false` (Label: "Exploratory (Underpowered)")
 - Else: `false`
 6. Include Accuracy, Precision, Recall, AUC-ROC, p-values, **Cohen's d**, and MDE in the report.
 7. Use the following Markdown structure:
 ```markdown
 # Final Report
 ## Classification Results
 - Accuracy: {value}
 - 95% CI: [{lower}, {upper}]
 - MDE: {mde_value}
 - Cohen's d: {cohen_d_value}
 ## Significance Assessment
 - Significance Flag: {significance_flag}
 - Interpretation: {if underpowered: "Exploratory finding due to limited power"}
 ## Statistical Validation
 - Permutation p-value: {p_value}
 - FDR-corrected p-values: {list}
 ## Sensitivity Analysis
 - Results: {sensitivity_results}
 ```
 **Depends on**: T030b (MDE calculation), T032a (CI calculation), T031a (Plan), T031b (Sensitivity Results).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033a [P] Generate Figure 1: Connectivity Matrix Heatmap from `data/processed/features.csv` in `docs/figures/heatmap.png`.
- [X] T033b [P] Generate Figure 2: Accuracy Comparison Bar Chart from `data/processed/results.json` in `docs/figures/accuracy_bar.png`.
- [X] T033c [P] Documentation updates: Ensure `docs/sensitivity_plan.md` (from T031a) is included in the final report references.
- [X] T034 Code cleanup and refactoring for memory efficiency (ensure <7GB RAM usage)
- [X] T035 Performance optimization: ensure pipeline completes <6h on 2-core CPU
- [X] T036 [P] Additional unit tests for edge cases (missing labels, non-PSD matrices) in `tests/unit/`
- [X] T037 Run `quickstart.md` validation and verify all artifacts are hashed

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
- **Data Integrity**: All tasks involving data generation must use REAL data from OpenNeuro.; synthetic data is strictly for unit testing logic or isolated sensitivity analysis (T031), not hypothesis validation.
- **Hardware Constraint**: No tasks may require GPU, CUDA, or >7GB RAM. All models must run in default precision on CPU.
- **Statistical Rigor**: All significance claims must be backed by permutation-based p-values and FDR correction as defined in FR-005.
- **Medication Confounder**: If medication status is missing, the analysis is explicitly framed as associational, and sensitivity analysis (T031/T031a/T031b) is performed as a "what-if" scenario only.

## Phase Revision: Addressing Reviewer Concerns

**Goal**: Resolve specific issues raised during the analysis phase regarding data sourcing, streaming, and robust error handling.

### Implementation for Revision

- [ ] T038a [US1] Implement dataset metadata schema validator in `code/preprocessing/download.py`: Define a Pydantic model for the expected dataset metadata structure.
- [ ] T038b [US1] Implement dataset ID checker in `code/preprocessing/download.py`: **Depends on T038a**. Check if dataset ID matches a designated target dataset or a 'verified equivalent' (as defined in plan.md). If not, raise `DATA_GAP` exception immediately.
- [ ] T038c [US1] Implement exception handler in `code/preprocessing/download.py`: **Depends on T038b**. Catch `DATA_GAP` and terminate the run with a clear error message.
- [ ] T039a [US1] Implement streaming iterator wrapper in `code/preprocessing/streaming.py`: Use `datasets.load_dataset(..., streaming=True)` [UNRESOLVED-CLAIM: c_13b9ed9e — status=not_enough_info].
- [ ] T039b [US1] Implement chunked processing logic in `code/preprocessing/streaming.py`: **Depends on T039a**. Process subjects in chunks (size determined by memory profiling to ensure <7GB RAM). Accumulate statistics online.
- [ ] T039c [US1] Implement online statistics accumulator in `code/preprocessing/streaming.py`: **Depends on T039b**. Ensure no full dataset is held in RAM.
- [ ] T040a [US1] Refactor download logic in `code/preprocessing/download.py` to remove all `try/except` blocks that fall back to synthetic data.
- [ ] T040b [US1] Implement `DataFetchError` exception class in `code/preprocessing/download.py`.
- [ ] T040c [US1] Implement main orchestrator termination logic in `code/main.py`: **Depends on T040b**. Terminate run on `DataFetchError`.
- [ ] T041 [US2] Add explicit sample size declaration in `code/graph_metrics/calculator.py`: Update the summary statistics report generation to explicitly state the sample size (N) and the specific streaming/sampling rule used (e.g., "First 60 subjects from streaming split"). This ensures transparency regarding data representativeness.
- [ ] T042 [US3] Update sensitivity analysis documentation in `docs/sensitivity_plan.md`: Explicitly reference the "Fail Loudly" policy (T040) and the streaming strategy (T039) to clarify that no synthetic data was used for the primary hypothesis test, only for the isolated sensitivity analysis of medication status.