# Tasks: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

**Input**: Design documents from `/specs/001-predicting-catalytic-activity/`
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

**Purpose**: Project initialization and basic structure. All file system paths must be created here before any logic tasks run.

- [ ] T001a [P] Create project directory structure: Create `data/raw/`, `data/processed/`, `code/`, `outputs/`, `tests/`, `state/projects/`, `code/models/`. **Verification**: Run `os.path.isdir()` for each path; if any missing, `sys.exit(1)` with message "Directory initialization failed".
- [ ] T001b [P] Initialize Python packages: Create `__init__.py` in all Python packages (`code/`, `tests/`, `code/utils/`, `code/models/`). **Verification**: Run `python -c "import code"` to ensure importability.
- [X] T001j [P] Initialize Python 3.10 project with `requirements.txt` (pinned versions using `==`: pandas==2.0.3, numpy==1.24.3, scikit-learn==1.3.0, xgboost==1.7.6, shap==0.42.1, requests==2.31.0, pyyaml==6.0.1, rdkit==2023.3.1, huggingface_hub==0.16.4)
- [ ] T002 [P] Configure linting (ruff/flake8) and formatting (black) tools: Create `pyproject.toml` with black config and `.ruff.toml` with specific rules (E, F, W, I). **Verification**: Run `ruff check --config=.ruff.toml.` and `black --check.`.
- [ ] T001c [P] **Document Scope Adjustment**: Create `outputs/scope_adjustment.md` explicitly stating that the Plan.md "Critical Scope Adjustment" supersedes Spec FR-001's requirement for Materials Project and 2025 CO₂ study datasets. **Content**: Must include `exclusion_reason`, `decision_rationale`, `spec_amendment_reference`, and `constitutional_override` sections. **Crucially**, the `constitutional_override` section MUST explicitly justify how the OC20-only pivot still satisfies Constitution Principle VI (Descriptor-Based Model Interpretability) by confirming that OC20 contains the necessary electronic descriptors (d-band center, adsorption energy) for SHAP analysis. **Depends on**: T001a, plan.md.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure logic that MUST be complete before ANY user story can be implemented.
**Note**: This phase assumes directory structure from Phase 1 (T001) is already present.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement content hashing mechanism for `state/` artifacts (Constitution Principle V) in `code/utils/hashing.py`
- [X] T005 [P] Configure base configuration loader for environment variables and paths in `code/config.py`
- [X] T006 [P] Setup logging infrastructure to write logs to `outputs/run.log`
- [X] T007 [P] Implement data validation helpers (checksum verification, schema checks) in `code/utils/validation.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download OC20 stratified sample, align descriptors, impute missing values, and produce `aligned_dataset.csv`.
**Scope Note**: Per plan.md "Critical Scope Adjustment", this pipeline relies exclusively on the verified OC20 dataset. External datasets (Materials Project, 2025 CO2 study) are excluded due to data unavailability.

**Independent Test**: The pipeline can be tested by verifying that the output CSV contains exactly the expected columns (composition, surface_facet, energy_change, d_band_center, adsorption_energy) with no NaN values in the target column after imputation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Contract test for data alignment logic in `tests/test_preprocess.py::test_alignment_columns`
- [X] T009 [P] [US1] Integration test for full download-to-csv flow in `tests/test_preprocess.py::test_full_pipeline_sample`
- [X] T050 [P] [US1] Implement `tests/test_preprocess.py::test_data_integrity`: A contract test that verifies no NaN values exist in the `energy_change` column of `aligned_dataset.csv` and that all `composition` strings are non-empty. **Fails loudly** if data integrity is compromised. **Depends on T020.**

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/download_data.py`: Download stratified sample of OC20 dataset from HuggingFace. **Dataset ID**: `oc/oc20`. **File**: `oc20.h5`. **Stratification**: `composition_family`. **Output**: `data/raw/oc20_sample.h5`. **Depends on T001a.**
- [X] T011 [US1] Implement `code/download_data.py`: Verify checksums of downloaded OC20 file against known hashes. **Depends on T010.**
- [X] T013a [US1] Implement `code/preprocess.py`: **Parse OC20 into DataFrame**. Load `oc20_sample.h5` and parse into a single Pandas DataFrame with columns: `composition`, `surface_facet`, `energy_change`, `d_band_center`, `adsorption_energy`. **Verification**: Verify DataFrame shape is (N, M) and columns match schema. **Depends on T010, T011.**
- [X] T013b [US1] Implement `code/preprocess.py`: **Construct Unified DataFrame**. Combine parsed OC20 data into the final unified structure required by FR-001. Log that Materials Project and 2025 CO2 datasets are excluded per T001c. **Depends on T013a, T001c.**
- [X] T013 [US1] **Compute Alignment Success Rate (SC-002)**. Calculate (matched entries / total OC20 entries in sample). **Note**: Since the plan pivots to OC20-only, the "total experimental entries" baseline from the spec is redefined here to "total OC20 entries in sample". Log this redefinition explicitly in `outputs/alignment_metrics.json`. **Output**: `outputs/alignment_metrics.json`. **Depends on T013b.**
- [X] T014a [US1] Implement `code/preprocess.py`: **Implement Alignment Logic per Plan**. Align OC20 entries using exact string matching on `composition` and `surface_facet`. **Check for `synthesis_condition`**: if it exists, use it; if missing, log "FR-002 requirement for synthesis_condition not applicable (column missing)" and proceed to T014b without excluding entries. Implement exclusion logic for entries missing `composition` or `surface_facet`. **Depends on T013b.**
- [X] T014b [US1] Implement `code/preprocess.py`: **Implement FR-002 Exclusion Logic for synthesis_condition**. If `synthesis_condition` column exists, exclude entries where it is not uniquely identifiable. **If the column is missing**, explicitly log that FR-002 exclusion logic is inapplicable due to schema mismatch and **PROCEED** with the dataset (do NOT exclude all entries). Log this as a data coverage limitation in `outputs/exclusion_log.json`. **Depends on T014a.**
- [X] T015 [US1] Implement `code/preprocess.py`: Retrieve target variable `energy_change` from OC20 data (per plan pivot). Log any missing target values for exclusion. **Depends on T014b.**
- [X] T016a [P] [US1] Implement `code/preprocess.py`: **Compute Stoichiometry Features**. Calculate normalized element counts (formula: `count / total_atoms`) for each catalyst entry to create the stoichiometry feature vector. **Output**: Append `stoich_<Element>` columns (e.g., `stoich_Fe`, `stoich_O`) to the dataframe. **Depends on T015.**
- [X] T016b [US1] Implement `code/preprocess.py`: **Compute Stoichiometry Distance**. Implement the Euclidean distance calculation in stoichiometry space (normalized element counts) as required by FR-003. **Depends on T016a.**
- [X] T017a [US1] **Strict Stoichiometry KNN Imputation**. Implement k-nearest-neighbors (k=5) based on Euclidean distance in stoichiometry space (normalized element counts) as required by FR-003. **Constraint**: Do NOT use Morgan fingerprints or structure-based features. **Logic**: If <5 neighbors exist for an entry, **flag and exclude** that entry from the training set (do not fallback to other methods). **Output**: Save imputed dataset to `data/processed/imputed_dataset.csv` and save list of excluded entries to `outputs/excluded_entries.json`. **Depends on T016b.**
- [X] T019 [US1] Implement `code/preprocess.py`: Scale all numeric features to zero mean and unit variance. **Depends on T017a.**
- [X] T020 [US1] Generate `data/processed/aligned_dataset.csv` with final schema. **Schema**: `composition` (str), `surface_facet` (str), `energy_change` (float), `d_band_center` (float), `adsorption_energy` (float), `stoich_*` (float). **Depends on T019.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train XGBoost model, compare against linear baseline, and perform statistical significance testing

**Independent Test**: The model training can be tested by running the script and verifying that both the XGBoost and linear models produce predictions on the hold-out test set with calculated R² and MAE metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US2] Contract test for metric calculation in `tests/test_train.py::test_metrics_output`
- [X] T023 [P] [US2] Integration test for nested CV flow in `tests/test_train.py::test_nested_cv_execution`

### Implementation for User Story 2

- [X] T024 [US2] Implement `code/train.py`: Load `aligned_dataset.csv` and split into train/test sets (stratified). **Depends on T020.**
- [ ] T047 [US2] Implement `code/utils/runtime_estimator.py`: Create a lightweight estimator that calculates projected runtime for the XGBoost training phase (T026) based on the number of samples in `aligned_dataset.csv` and the grid search space size. **Output**: Log projected hours to `outputs/runtime_projection.json`. **Depends on T020.**
- [ ] T048a [US2] **Define Deviation Logging**. Create `outputs/deviation_log.json` with schema `{ "task_id": "T048", "deviation_type": "dynamic_grid_reduction", "original_spec": "n_estimators <= 200", "reduced_value": "<int>", "reason": "runtime_constraint" }`. **Depends on T047.**
- [ ] T048 [US2] **Integrate Runtime Estimator**. **Before** starting the full nested CV (T026), read `outputs/runtime_projection.json`. If the projection exceeds 4 hours, automatically reduce the grid search range for `n_estimators` (e.g., cap at 100). **Output**: Generate `code/configs/grid_config.json` with the final grid parameters. **Log** the reduction to `outputs/deviation_log.json` (via T048a). **Depends on T047, T048a, T020.**
- [X] T025 [US2] Implement `code/train.py`: Train Linear Baseline using only `d_band_center` and `adsorption_energy`. **Depends on T024.**
- [X] T026 [US2] Implement `code/train.py`: Train XGBoost with nested cross-validation. **Outer loop**: 5-fold. **Inner loop**: Grid search `max_depth` ∈ {3, 5, 7}, `learning_rate` ∈ {0.01, 0.1, 0.2}, `n_estimators` ≤ 200 (or reduced value from T048). **Seed**: 42. **Save best model to `code/models/best_xgboost.json`** (FR-004). **Depends on T024, T048.**
- [X] T027 [US2] Implement `code/evaluate.py`: Compute absolute errors for both models on hold-out test set. **Depends on T025, T026.**
- [X] T028a [US2] **Statistical Test Logic (Normality Check on Paired Differences)**. Compute the absolute errors for both models. Calculate the *difference* distribution: `diff = |error_XGB| - |error_lin|`. Perform Shapiro-Wilk test on the **distribution of these differences** to satisfy FR-005. **Alpha**: 0.05. **Output**: `outputs/normality_check.json` with schema `{ "statistic": float, "p_value": float, "decision": "use_t_test" | "use_wilcoxon" }`. **Depends on T027.**
- [X] T028b [US2] **Perform Selected Statistical Test**. Based on T028a's decision, perform a two-tailed paired t-test (if normal) or Wilcoxon signed-rank test (if not normal) on the paired differences of absolute errors. **Depends on T028a.**
- [X] T029 [US2] Generate `outputs/metrics.json` containing R², MAE, Pearson R, and p-value for both models. **Depends on T028b.**
- [X] T030 [US2] Create `tests/test_train.py` unit tests for grid search parameter selection logic. **Depends on T026.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Interpretability Analysis (Priority: P3)

**Goal**: Perform SHAP analysis, rank top descriptors, verify SC-003, and generate final report

**Independent Test**: The interpretability step can be tested by running the SHAP calculation and verifying that the a subset of top descriptors are listed in descending order of importance with a corresponding bar plot generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [P] [US3] Contract test for SHAP value computation in `tests/test_evaluate.py::test_shap_values`
- [X] T032 [P] [US3] Integration test for reduced model verification in `tests/test_evaluate.py::test_reduced_model_sc003`

### Implementation for User Story 3

- [X] T033 [US3] Implement `code/evaluate.py`: Compute SHAP values for the final XGBoost model using `shap.TreeExplainer`. **Depends on T026.**
- [X] T034 [US3] Implement `code/evaluate.py`: Rank descriptors by mean absolute SHAP impact (FR-006). **Depends on T033.**
- [X] T035 [US3] Implement `code/evaluate.py`: Generate `outputs/feature_importance.png` bar plot of top descriptors. **Depends on T034.**
- [X] T039a [US3] **Create Nørskov Reference List**. Create a static local file `code/data/norskov_2005_descriptors.json` containing the hardcoded list of descriptors from Nørskov et al., 2005. **Do NOT attempt to download**. **Schema**: `{"descriptors": ["d_band_center", "reaction_energy", "activation_barrier"]}`. **Content**: Hardcode these three strings exactly as the reference set. **Output**: `code/data/norskov_2005_descriptors.json`. **Depends on T001a.**
- [X] T039b [US3] **Compare Descriptors**. Compare the top-ranked SHAP descriptors against the Nørskov list. from T039a. Explicitly state matches or novel findings. **Depends on T034, T039a.**
- [X] T036a [P] [US3] Implement `code/evaluate.py`: **Define Reduced Model Search Space**. Explicitly define the hyperparameter search space (max_depth, learning_rate, n_estimators) for the reduced model. **Output**: Save grid config to `code/configs/reduced_model_grid.json` with schema `{ "max_depth": [5,7], "learning_rate": [a lower magnitude, 0.1], "n_estimators": a range of values including 100 and 200 }`. **Depends on T034.**
- [X] T036 [US3] Implement `code/evaluate.py`: Train a reduced model using only the top-ranked SHAP descriptors. **Requirement**: Perform independent hyperparameter tuning using the grid search defined in T036a. **Seed**: 42. **Save best model to `code/models/best_reduced_xgboost.json`**. **Depends on T036a.**
- [X] T037 [US3] Implement `code/evaluate.py`: **Verify SC-003 quantitatively**. Calculate reduced model R² and full model R². Compute the ratio (reduced_r2 / full_r2). **Append quantitative results (reduced_r2, full_r2, ratio) and verification status to outputs/metrics.json** and `outputs/sc003_verification.json`. If ratio < 0.50, set 'SC-003_status': 'FAILED'. **Depends on T036.**
- [X] T039 [US3] Implement `code/report.py`: **Generate Descriptor Comparison Table**. Append comparison table to `outputs/final_report.md` under section "Descriptor Comparison" using results from T039b. **Depends on T034, T037, T039b.**
- [X] T040 [US3] Implement `code/report.py`: Generate `outputs/final_report.md` containing Pearson R, MAE, p-value, top 5 list, SC-003 verification result (quantitative), and Nørskov comparison table (FR-007). **Depends on T037, T039.**
- [X] T041 [US3] Create `tests/test_evaluate.py` unit tests for SC-003 quantitative logic. **Depends on T037.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042a [P] Run full pipeline end-to-end. **Capture start/end timestamps explicitly** and log them to `outputs/runtime.log`.
- [X] T042b [P] Log duration (calculated from T042a timestamps) to `outputs/metrics.json`.
- [X] T042c [P] **Adaptive Runtime Check**. Read duration from `outputs/metrics.json`. If duration > 4 hours, log a warning and re-run the pipeline with reduced `n_estimators` (as per plan Risk Mitigation). If duration > 6 hours even after reduction, raise `RuntimeError` (SC-004). **Depends on T042a, T042b.**
- [X] T043a [P] Run `black --check.` and `ruff check.` on all code. Fix any formatting/linting errors.
- [X] T043c [P] Remove all debug prints from `code/preprocess.py` and `code/train.py`.
- [X] T044 [P] Update `README.md` with usage instructions and data sources.
- [X] T045 [P] Add additional unit tests for edge cases (missing neighbors, non-normal error distributions).
- [X] T046 [P] Run quickstart.md validation to ensure reproducibility.
- [ ] T049 [US3] Implement `code/report.py`: **Add "Data Lineage" Section**. Explicitly list the exact HuggingFace commit hash of the OC20 dataset used (from T010) and the exact `requirements.txt` hash used. **Output**: Append to `outputs/final_report.md` under "Reproducibility Metadata". **Depends on T011, T040.**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T001) - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on T020 (artifact `aligned_dataset.csv`), not US1 completion.
- **User Story 3 (P3)**: Depends on T026 (artifact `best_xgboost.json`), not US2 completion.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Modeling) - *Can start once T020 (aligned_dataset.csv) is done*
 - Developer C: User Story 3 (Interpretability) - *Can start once T026 (model saved) is done*
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all story)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify `aligned_dataset.csv`)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Model comparison)
4. Add User Story 3 → Test independently → Deploy/Demo (Interpretability)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Modeling) - *Can start once T020 (aligned_dataset.csv) is done*
 - Developer C: User Story 3 (Interpretability) - *Can start once T026 (model saved) is done*
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
- **Constraint**: All tasks must run on CPU-only CI (limited cores, constrained RAM, 6h limit). No GPU, no 8-bit quantization, no large LLMs.
- **Data Scope**: Per plan.md, this project uses OC20 exclusively. External dataset tasks (Materials Project, 2025 CO2 study) are omitted due to data unavailability, handled explicitly by T001c with an override note and formal artifact.
- **Spec-Plan Note**: The tasks implement the plan's OC20-only pivot. The spec.md still references removed features; this is a known contradiction to be resolved in the next cycle. Tasks explicitly document these overrides to prevent silent drift.

---

## Revision: Addressing Analyze Findings

**Purpose**: New tasks added to resolve specific issues raised by `/speckit.analyze` regarding data flow, runtime estimation, and spec alignment.

- [X] T049 [US3] Implement `code/report.py`: **Add "Data Lineage" Section**. Explicitly list the exact HuggingFace commit hash of the OC20 dataset used (from T010) and the exact `requirements.txt` hash used. **Output**: Append to `outputs/final_report.md` under "Reproducibility Metadata". **Depends on T011, T040.**
- [X] T050 [P] [US1] Implement `tests/test_preprocess.py::test_data_integrity`: A contract test that verifies no NaN values exist in the `energy_change` column of `aligned_dataset.csv` and that all `composition` strings are non-empty. **Fails loudly** if data integrity is compromised. **Depends on T020.**

**Note**: T042d (Dynamic Runtime Adaptation) has been removed as it is logically impossible (post-hoc check). The logic is fully handled by T048 (pre-flight check) and T042c (adaptive re-run).