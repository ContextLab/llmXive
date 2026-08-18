# Tasks: Predicting Molecular Polarity from SMILES Strings with Machine Learning

**Input**: Design documents from `/specs/001-predict-molecular-polarity/`
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

- [X] T001a Create project directories: `code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/processed/analysis/`, `logs/`
- [X] T001b Create `code/requirements.txt` with pinned versions: rkit, lightgbm, pandas, numpy, scikit-learn, shap, pyyaml, pytest, safety
- [X] T001c Create `.gitignore` excluding `data/raw/`, `data/processed/`, `logs/`, `*.pkl`, `__pycache__/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/config.py` for global seeds (hardcoded), paths, and hyperparameter defaults (loadable from `code/config.yaml` to align with plan's `pyyaml` dependency). **Constraint**: Random seeds MUST be hardcoded in code for reproducibility; hyperparameters MAY be loaded from YAML.
- [X] T005 [P] Implement `code/utils/validators.py` with runtime assertions for 3D exclusion (no `EmbedMolecule`, `Get3DConformer`)
- [X] T006 [P] Setup `tests/contract/` schema validators for dataset and model output
- [X] T007 [P] Create base data loading utilities in `code/data/loader.py` with functions `load_batch(filepath, batch_size)` and `iterate_smiles(filepath)` yielding (smiles, target) tuples; include input validation for SMILES format.
- [X] T008 [P] Configure error handling and logging infrastructure in `code/utils/logging_config.py` using `RotatingFileHandler` for `logs/app.log` with JSON format and specific log level configuration.
- [X] T007b [P] Create orchestration script `code/main.py` with entry point for the full pipeline to ensure file exists before T019.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 2D Descriptor Generation from SMILES (Priority: P1) 🎯 MVP

**Goal**: Parse SMILES from QM9, generate ≥200 2D topological descriptors, exclude 3D/TPSA/SMARTS, and handle NaNs.

**Independent Test**: Run on a dataset of SMILES strings.; verify numeric matrix, no 3D data, no TPSA, no functional group counts, and NaN handling.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`
- [X] T011 [P] [US1] Unit test for 3D exclusion in `tests/unit/test_3d_exclusion.py` (asserts no 3D calls)
- [X] T012 [P] [US1] Unit test for NaN handling in `tests/unit/test_nan_handling.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/download_qm9.py` to fetch QM9 from verified URL (Maxwell/Zenodo) with checksum validation and SMILES format validation.
- [X] T014 [US1] **[FR-001]** Implement `code/data/preprocess_2d.py` to compute 2D descriptors (rdkit.Descriptors) excluding TPSA, TPSA_E, and SMARTS patterns. **Integrate runtime assertions** to verify no 3D conformer generation functions are called during execution. **Note**: This task implements the core pipeline.
- [X] T014b [US1] **[FR-001] [Plan-Override]** Implement Target-Correlation Logic in `code/data/preprocess_2d.py`. **Logic**: Compute Pearson correlation between every descriptor and the target dipole moment. **Constraint**: DO NOT remove any features regardless of correlation strength (|r| > 0.85). **Output**: Write correlation matrix to `data/processed/correlation_matrix.csv`. **Verification**: Add an assertion `assert len(computed_features) == len(original_features)` to ensure no filtering occurred. **Authority**: This implements the plan.md override of spec FR-001(c) (Section 6). Document this override in `data/processed/plan_override_log.md` (see T015b).
- [X] T015b [US1] **[FR-001]** Generate `data/processed/plan_override_log.md` entry documenting the deviation from spec FR-001(c) (feature correlation filtering) as ratified by Plan.md Section 6.
- [X] T016 [US1] **[FR-006]** Implement NaN handling in `code/data/preprocess_2d.py` with deterministic logic: If >5% missing values in a column, drop the record; otherwise, impute with column median. Log the action taken. **Verification**: Assert that the number of *columns* (features) remains unchanged after dropping rows to ensure the 'no filtering' promise of T014b is met regarding feature count. This is distinct from feature filtering.
- [X] T017 [US1] Implement batch processing logic in `code/data/preprocess_2d.py` to ensure <6GB RAM usage by processing `data/raw/` in chunks.
- [X] T018 [US1] **[FR-001] [Plan-Override]** Save processed feature matrix to `data/processed/descriptors.parquet`. **Schema**: Columns must be `smiles` (string), `target` (float), and + 2D descriptor columns (float). **Verification**: Explicitly verify that no columns named 'TPSA', 'TPSA_E', or derived from SMARTS patterns exist in the output file. **Critical Check**: Assert `len(df.columns) == expected_input_columns` to verify the 'compute but do not filter' logic from T014b was applied.
- [X] T019 [US1] Add runtime assertion in `code/main.py` to verify the orchestration pipeline executes without 3D calls and that `data/processed/descriptors.parquet` (produced by T018) is valid before downstream tasks. **Use the schema validators from T006/T010** for validity checks. **Depends on**: T018 (file must exist).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 2D-Only Regression Model Training (Priority: P2)

**Goal**: Train LightGBM on 2D descriptors with standard random split, 5-fold CV, and hyperparameter tuning.

**Independent Test**: Train model, evaluate on test set, verify R² > 0.0 (null model), and check no stratification by target.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T021 [P] [US2] Integration test for full training pipeline in `tests/integration/test_full_pipeline.py`
- [X] T028 [P] [US2] Unit test for 3D exclusion in training pipeline in `tests/unit/test_3d_exclusion_training.py` (asserts no 3D functions are called during training execution)

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/data/split_data.py` for standard random train/test split (no target stratification) using `data/processed/descriptors.parquet`.
- [X] T023 [US2] Implement `code/models/train_lightgbm.py` with LightGBM Regressor.
- [X] T024 [US2] Implement k-fold cross-validation loop in `code/models/train_lightgbm.py` for hyperparameter tuning.
- [X] T025 [US2] Implement logging of optimal parameters (`num_leaves`, `learning_rate`) to `code/config.yaml`.
- [X] T026 [US2] Train final model on full training set and save to `data/processed/model.pkl`.
- [X] T027 [US2] Implement `code/models/evaluate.py` to compute R², RMSE, and compare against null model (R²=0).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

**Goal**: Apply Cluster-Aware SHAP, bootstrap stability analysis (multiple resamples), and VIF clustering diagnostics.

**Independent Test**: Generate SHAP summary, stability report (Jaccard ≥ 0.7), and VIF cluster report.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for SHAP stability calculation in `tests/unit/test_shap_stability.py`
- [X] T030 [P] [US3] Unit test for VIF clustering logic in `tests/unit/test_vif_clustering.py`

### Implementation for User Story 3

- [X] T031 [US3] **[FR-007] [Plan-Override]** Implement VIF diagnostic clustering only in `code/data/feature_clustering.py`. Compute VIF for all descriptors. Group features with |r| > 0.8 into clusters. **DO NOT** implement iterative feature removal. Output a report listing clusters and their internal correlation statistics. **Output**: Write `cluster_map.csv` (feature_id, cluster_id) to `data/processed/`. **Authority**: This implements the plan.md override of spec FR-007 (Section 6). Document this override in `data/processed/plan_override_log.md` (see T031b).
- [X] T031b [US3] **[FR-007]** Generate `data/processed/plan_override_log.md` entry documenting the deviation from spec FR-007 (iterative feature removal) as ratified by Plan.md Section 6.
- [X] T032a [US3] **[FR-005] [SC-003]** Load `cluster_map.csv` from T031 into `code/models/interpret.py`.
- [X] T032b [US3] **[FR-005] [SC-003]** Compute Cluster-Aware SHAP values using `shap.TreeExplainer` on `data/processed/descriptors.parquet` and `data/processed/model.pkl`.
- [X] T032c [US3] **[FR-005] [SC-003]** Aggregate SHAP values by cluster: For each cluster identified in T031, compute the cluster importance as the **mean absolute SHAP value** of all member features.
- [X] T033a [US3] **[FR-005] [SC-003] [Plan-Optimization]** Implement two-stage bootstrap in `code/models/interpret.py` (SHAP-only resampling as per plan.md Complexity Tracking): **Resample the computed SHAP values** directly from the original dataset without re-computing them or re-training. **Method**: Use `np.random.choice` with replacement for **a sufficient number of iterations**. **Authority**: This is a plan-mandated optimization to satisfy SC-003 under CPU constraints, acknowledging the deviation from the spec's requirement for dataset bootstrapping. Document this methodology shift in `data/processed/plan_override_log.md` (see T033b). **Output**: Produce resampled SHAP artifacts for T034a.
- [X] T033b [US3] **[FR-005]** Generate `data/processed/plan_override_log.md` entry documenting the deviation from spec FR-005/SC-003 (dataset bootstrapping vs. SHAP-only resampling) as ratified by Plan.md Complexity Tracking.
- [X] T034a [US3] **[FR-007] [SC-003]** Calculate Jaccard similarity of **top feature clusters** across 100 bootstrap resamples to satisfy plan.md SC-003. **Input**: Read `cluster_map.csv` from T031 and resampled SHAP artifacts from T033a. **Method**: Select the top 10 clusters by mean absolute SHAP value (from T032c). Verify that these top 10 clusters remain consistent (Jaccard similarity ≥ 0.7). **Authority**: This implements the plan.md update to SC-003 (measuring clusters instead of individual features).
- [X] T035 [US3] **[FR-005] [SC-003]** Generate stability report verifying Jaccard ≥ 0.7 for the top 10 feature clusters. **Failure Handling**: If Jaccard < 0.7, log a CRITICAL error using `logging.critical`, write a `stability_failed.json` artifact, and **exit with code 1** (`sys.exit(1)`) to trigger CI failure.
- [X] T036 [US3] Generate SHAP summary plot and feature importance report distinguishing collinear clusters.
- [X] T037 [US3] Save all analysis artifacts (plots, reports, SHAP values) to `data/processed/analysis/`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T038a [P] Create `README.md` with 'Installation' section (pip install).
- [X] T038b [P] Add 'Usage' section with CLI examples for pipeline to `README.md`.
- [X] T038c [P] Add 'Data Sources' section (QM9 URL) to `README.md`.
- [X] T038d [P] Add 'Results' section (link to `data/processed/analysis/`) to `README.md`.
- [ ] T039b [P] Remove all unused imports from `code/` scripts by running `autoflake --remove-all-unused-imports --recursive code/` and verifying with `pytest`.
- [ ] T039c [P] Standardize logging format across all modules to `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'` and verify with `pytest`.
- [ ] T039d [P] Verify unused import removal and logging standardization with `pytest`.
- [X] T040a [P] Optimize `code/data/preprocess_2d.py` for memory by implementing explicit batch iteration and garbage collection to ensure <6GB RAM.
- [X] T040b [P] Tune LightGBM `num_threads` and `verbose` parameters in `code/models/train_lightgbm.py` for CPU-only execution performance.
- [ ] T041 [P] Additional unit tests in `tests/unit/` (if requested)
- [X] T042a [P] Add input validation regex for SMILES strings in `code/data/download_qm9.py` and `code/data/loader.py`.
- [ ] T042b [P] Add `safety check` command to CI workflow for dependency vulnerability scanning.
- [ ] T043 [P] Run `docs/quickstart.md` validation and end-to-end test on small batch.
- [ ] T044 [P] **[SC-004]** Final verification of computational constraints (≤6h runtime, ≤6GB RAM) by running the full pipeline **via GitHub Actions free-tier runner CI workflow**. **Method**: Use `memory_profiler` and `time` command to measure peak memory and total runtime. **Requirement**: Must execute in the target CI environment, not locally.

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
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Unit test for 3D exclusion in tests/unit/test_3d_exclusion.py"
Task: "Unit test for NaN handling in tests/unit/test_nan_handling.py"

# Launch all models for User Story 1 together:
Task: "Implement download_qm9.py"
Task: "Implement preprocess_2d.py"
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
- **CRITICAL**: Tasks T014b, T031, T033a are updated to strictly follow `plan.md` constraints (no feature removal/filtering, SHAP-only bootstrap, cluster-based metrics), overriding conflicting `spec.md` requirements. This is documented in `data/processed/plan_override_log.md`.
- **CRITICAL**: Configuration allows YAML for hyperparameters (T004) but seeds must be hardcoded.
- **CRITICAL**: NaN handling uses deterministic logic: >5% missing -> drop, else impute (T016).
- **CRITICAL**: T018 output schema must explicitly exclude TPSA/SMARTS columns and verify no filtering.
- **CRITICAL**: T032 uses mean absolute SHAP for cluster aggregation.
- **CRITICAL**: T035 exits with code 1 on stability failure.
- **CRITICAL**: T034a explicitly targets feature clusters for Jaccard similarity calculation as per plan.md SC-003.
- **CRITICAL**: T034a uses the VIF-based groups from T031 (cluster_map.csv), not unsupervised clustering.
- **CRITICAL**: T038a-T038d split the README update into atomic tasks.
- **CRITICAL**: T039b uses `autoflake` for deterministic import removal.
- **CRITICAL**: T039c specifies the exact logging format string.
- **CRITICAL**: T013 must fail loudly on download failure; no synthetic fallback allowed.
- **CRITICAL**: T017 must implement chunked streaming of the QM9 dataset to stay within RAM limits.
- **CRITICAL**: T016 must log the exact number of rows dropped due to NaN handling for auditability.
- **CRITICAL**: T035 must generate a `stability_report.md` containing the Jaccard similarity scores for all 100 resamples.
- **CRITICAL**: T044 must run on GitHub Actions free-tier runner.