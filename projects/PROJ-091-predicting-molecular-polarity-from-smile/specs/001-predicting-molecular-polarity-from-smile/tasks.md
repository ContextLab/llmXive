# Tasks: Predicting Molecular Polarity from SMILES Strings with Machine Learning

**Input**: Design documents from `/specs/001-predict-molecular-polarity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

- [X] T001a Create project directories: `code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/processed/analysis/`, `logs/`
- [X] T001b Create `code/requirements.txt` with pinned versions: rkit, lightgbm, pandas, numpy, scikit-learn, shap, pyyaml, pytest, safety
- [X] T001c Create `.gitignore` excluding `data/raw/`, `data/processed/`, `logs/`, `*.pkl`, `__pycache__/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/config.py` for global seeds (hardcoded), paths, and hyperparameter defaults (loadable from `code/config.yaml` to align with plan's `pyyaml` dependency). **Constraint**: Random seeds MUST be hardcoded in code for reproducibility; hyperparameters MAY be loaded from YAML.
- [X] T005 [P] Implement `code/utils/validators.py` with runtime assertions for 3D exclusion (no `EmbedMolecule`, `Get3DConformer`)
- [ ] T006 [P] Setup `tests/contract/` schema validators for dataset and model output. **Schema Definition**: Implement Pydantic models with dynamic column validation:
 - `DescriptorMatrix`: `smiles: str`, `target: float`, and **any number of columns starting with 'desc_'** (regex pattern `^desc_.*`). The validator must accept any count of descriptor columns without hardcoding specific names.
 - `ModelOutput`: `smiles: str`, `prediction: float`, `shap_value: float`.
 **Verification**: Ensure validators raise `ValidationError` on mismatch or if required columns are missing. **Dependency**: This task is a prerequisite for T019.
- [X] T007 [P] Create base data loading utilities in `code/data/loader.py` with functions `load_batch(filepath, batch_size)` and `iterate_smiles(filepath)` yielding (smiles, target) tuples; include input validation for SMILES format.
- [X] T008 [P] Configure error handling and logging infrastructure in `code/utils/logging_config.py` using `RotatingFileHandler` for `logs/app.log` with JSON format and specific log level configuration.
- [X] T007b [P] Create orchestration script `code/main.py` with entry point for the full pipeline to ensure file exists before T019.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 2D Descriptor Generation from SMILES (Priority: P1) 🎯 MVP

**Goal**: Parse SMILES from QM9, generate ≥200 2D topological descriptors, exclude 3D/TPSA/SMARTS, and handle NaNs. **Constraint**: NO feature removal based on correlation (Plan Override).

**Independent Test**: Run on a dataset of SMILES strings.; verify numeric matrix, no 3D data, no TPSA, no functional group counts, and NaN handling.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`
- [X] T011 [P] [US1] Unit test for 3D exclusion in `tests/unit/test_3d_exclusion.py` (asserts no 3D calls)
- [X] T012 [P] [US1] Unit test for NaN handling in `tests/unit/test_nan_handling.py`
- [X] T016b [P] [US1] **[FR-006]** Implement dedicated unit test for 3D exclusion *within the NaN handling pipeline* in `tests/unit/test_3d_exclusion_nan_pipeline.py`. **Logic**: Assert that the `preprocess_2d.py` function (specifically the NaN handling block) does not call any 3D conformer generation functions. **Authority**: This satisfies FR-006's specific requirement for a dedicated test within the NaN context, distinct from the generic T011.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/download_qm9.py` to fetch QM9 from verified URL (Maxwell/Zenodo) with checksum validation and SMILES format validation. **Constraint**: MUST use `streaming=True` to handle large datasets without OOM. **Verification**: Assert that `sys.getsizeof(batch_df)` never exceeds a reasonable memory threshold (e.g., 500MB) during iteration over `batch_df`.
- [X] T014a [US1] **[FR-001]** Implement `code/data/preprocess_2d.py` to compute 2D descriptors (rdkit.Descriptors) excluding TPSA, TPSA_E, and SMARTS patterns. **Output**: Generate a raw list of descriptor names and a feature matrix. **Constraint**: Do NOT remove features based on correlation with target (|r| > 0.85). **Integrate runtime assertions** to verify no 3D conformer generation functions are called during execution. **Authority**: This task implements the descriptor generation phase of the **Ratified Plan Override** regarding correlation filtering.
- [X] T014b [US1] **[FR-001] [Plan Override]** Implement correlation audit in `code/data/preprocess_2d.py`. **Logic**: Compute Pearson correlation coefficients between all generated descriptors and the target. **Action**: Log any descriptors with |r| > 0.85 to `logs/correlation_audit.log` but **DO NOT remove them**. **Verification**: Assert that the final feature matrix contains all generated descriptors. **Authority**: This task explicitly validates the 'No-Filter' decision mandated by the **Ratified Plan Override** (Plan.md Section 6), ensuring high correlations are observed but not acted upon.
- [ ] T014c [US1] **[FR-001]** Save processed feature matrix to `data/processed/descriptors.parquet`. **Schema**: Columns must be `smiles` (string), `target` (float), and + 2D descriptor columns (float). **Verification**: Explicitly verify that no columns named 'TPSA', 'TPSA_E', or derived from SMARTS patterns exist in the output file. **Critical Check**: Assert `len(df.columns) == 2 + len(descriptor_names)` where `descriptor_names` is the list generated in T014a. **Depends on**: T014a (descriptor generation), T014b (correlation audit). **Note**: This task saves the *raw* computed matrix before any filtering logic is applied.
- [X] T016 [US1] **[FR-006]** Implement NaN handling in `code/data/preprocess_2d.py` with deterministic logic: If >5% missing values in a column, drop the record; otherwise, impute with column median. Log the action taken. **Verification**: Assert that the number of *columns* (features) remains unchanged after dropping rows to ensure the 'no filtering' promise is met regarding feature count. This is distinct from feature filtering.
- [X] T017 [US1] Implement batch processing logic in `code/data/preprocess_2d.py` to ensure <6GB RAM usage by processing `data/raw/` in chunks. **Constraint**: MUST use `streaming=True` to handle large datasets without OOM. **Verification**: Assert that `sys.getsizeof(batch_df)` never exceeds 500MB during iteration.
- [ ] T018 [US1] **[FR-001]** Validate processed feature matrix integrity in `code/main.py` or `code/data/validate.py`. **Logic**: Load `data/processed/descriptors.parquet` (produced by T014c). **Verification**: Assert `len(df.columns) == expected_input_columns` where `expected_input_columns` is derived dynamically as `2 + len(descriptor_names)` from the output of T014a. **Depends on**: T014c (file must exist), T014a (to derive column count). **Note**: This task is a validation step, not a producer.
- [ ] T019 [US1] Add runtime assertion in `code/main.py` to verify the orchestration pipeline executes without 3D calls and that `data/processed/descriptors.parquet` (produced by T014c) is valid before downstream tasks. **Use the schema validators from T006** for validity checks. **Depends on**: T014c (file must exist), T006 (validators implementation).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 2D-Only Regression Model Training (Priority: P2)

**Goal**: Train LightGBM on 2D descriptors with standard random split, 5-fold CV, and hyperparameter tuning.

**Independent Test**: Train model, evaluate on test set, verify R² > 0.0 (null model), and check no stratification by target.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T021 [P] [US2] Integration test for full training pipeline in `tests/integration/test_full_pipeline.py`
- [X] T041 [US2] Unit test for 3D exclusion in training pipeline in `tests/unit/test_3d_exclusion_training.py` (asserts no 3D functions are called during training execution)

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

**Goal**: Apply Cluster-Aware SHAP, bootstrap stability analysis (SHAP-only resampling), and VIF clustering diagnostics. **Constraint**: NO feature removal based on VIF (Plan Override).

**Independent Test**: Generate SHAP summary, stability report (Jaccard ≥ 0.7), and VIF cluster report.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for SHAP stability calculation in `tests/unit/test_shap_stability.py`
- [X] T030 [P] [US3] Unit test for VIF clustering logic in `tests/unit/test_vif_clustering.py`

### Implementation for User Story 3

- [ ] T031a [US3] **[FR-007]** Implement VIF calculation in `code/data/feature_clustering.py`. Compute VIF for all descriptors. **Output**: Write VIF scores to `data/processed/vif_scores.csv`. **Constraint**: DO NOT remove features.
- [X] T031b [US3] **[FR-007]** Implement cluster grouping in `code/data/feature_clustering.py`. Group features with |r| > 0.8 into clusters. **Output**: Write `cluster_map.csv` (feature_id, cluster_id) to `data/processed/`. **Constraint**: DO NOT remove features.
- [ ] T031c [US3] **[FR-007]** Write `cluster_map.csv` to `data/processed/` from T031b output. **Depends on**: T031b.
- [X] T031d [US3] **[FR-007]** Migrate VIF logic: Remove `code/data/feature_selection.py` (if it exists) and ensure all VIF logic resides exclusively in `code/data/feature_clustering.py`. **Authority**: This satisfies the Plan Override moving logic from Spec's `feature_selection.py` to Plan's `feature_clustering.py`.
- [X] T031e [US3] **[FR-007]** Generate `data/processed/plan_override_log.md` entry documenting the deviation from the Spec's FR-007 (iterative feature removal) as ratified by Plan.md Section 6. **Authority**: This entry constitutes a **Ratified Plan Override** that legally supersedes Spec FR-007 and confirms the intentional voiding of the removal requirement.
- [ ] T032b [US3] **[FR-005] [SC-003]** Compute Cluster-Aware SHAP values using `shap.TreeExplainer` on `data/processed/descriptors.parquet` and `data/processed/model.pkl`. **Input**: Read `cluster_map.csv` from T031c and `model.pkl` from T026. **Depends on**: T031c, T026.
- [X] T032c [US3] **[FR-005] [SC-003]** Aggregate SHAP values by cluster: For each cluster identified in T031c, compute the cluster importance as the **mean absolute SHAP value** of all member features.
- [X] T033a [US3] **[FR-005] [SC-003] [Ratified Plan Override]** Implement SHAP-only resampling logic in `code/models/interpret.py`. **Logic**: Resample the computed SHAP values directly from the original dataset without re-computing them or re-training. **Input**: Read `cluster_map.csv` from T031c and SHAP values from T032b. **Authority**: This task implements the **Ratified Plan Override** for FR-005/SC-003, shifting from dataset bootstrapping to SHAP-only resampling as mandated by Plan.md Complexity Tracking.
- [ ] T033b [US3] **[FR-005] [SC-003]** Generate resampled SHAP artifacts for T034a. **Input**: Read resampled SHAP logic from T033a. **Output**: Generate resampled SHAP artifacts. **Authority**: This implements the Plan's override of Spec FR-005/SC-003 (dataset bootstrapping vs. SHAP-only resampling) as ratified by Plan.md Complexity Tracking. **Depends on**: T033a.
- [X] T033c [US3] **[FR-005] [SC-003]** Generate `data/processed/plan_override_log.md` entry documenting the deviation from the Spec's FR-005/SC-003 (dataset bootstrapping vs. SHAP-only resampling) as ratified by Plan.md Complexity Tracking. **Authority**: This entry constitutes a **Ratified Plan Override** that legally supersedes Spec SC-003 and confirms the intentional shift to SHAP-only resampling.
- [ ] T034a [US3] **[FR-007] [SC-003]** Calculate Jaccard similarity of **top feature clusters** across 100 bootstrap resamples to satisfy plan.md SC-003. **Input**: Read `cluster_map.csv` from T031c and resampled SHAP artifacts from T033b. **Method**: Select the top-ranked clusters by mean absolute SHAP value (from T032c). Verify that these top 10 clusters remain consistent (Jaccard similarity ≥ 0.7). **Authority**: This implements the plan.md update to SC-003 (measuring clusters instead of individual features) as ratified by the **Ratified Plan Override** in `plan_override_log.md` (T033e/T033c), which supersedes the Spec's individual feature requirement. **Depends on**: T032c (cluster importance), T033b (resampled artifacts).
- [X] T035 [US3] **[FR-005] [SC-003]** Generate stability report verifying Jaccard ≥ 0.7 for the top 10 feature clusters. **Success Artifact**: Generate `stability_report.md` containing Jaccard scores for all resamples. **Failure Handling**: If Jaccard < 0.7, log a CRITICAL error using `logging.critical`, write a `stability_failed.json` artifact, and **exit with code 1** (`sys.exit(1`) to trigger CI failure.
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
- [X] T039b [P] **[FR-003]** Remove all unused imports from `code/` scripts by running `autoflake --remove-all-unused-imports --recursive code/` and verifying with `pytest`. **Verification**: pytest must pass with 0 warnings; git diff must show unused imports removed. **Authority**: Implements Constitution Principle I (Reproducibility) by ensuring clean dependency graphs.
- [X] T039c [P] **[FR-003]** Standardize logging format across all modules to `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'` and verify with `pytest`. **Authority**: Implements Constitution Principle I (Reproducibility) by ensuring reproducible audit trails.
- [X] T040a [P] Optimize `code/data/preprocess_2d.py` for memory by implementing explicit batch iteration and garbage collection to ensure <6GB RAM. <!-- FAILED: unspecified -->
- [X] T040b [P] Tune LightGBM `num_threads` and `verbose` parameters in `code/models/train_lightgbm.py` for CPU-only execution performance.
- [X] T042a [P] Create `.github/workflows/ci.yml` to define the GitHub Actions free-tier runner workflow for automated testing and constraint verification.
- [X] T042b [P] Add `safety check` command to CI workflow for dependency vulnerability scanning.
- [X] T043 [P] Run `docs/quickstart.md` validation and end-to-end test on small batch.
- [X] T044a [P] **[SC-004]** Implement local memory and time measurement script in `code/utils/constraints.py`. **Method**: Use `memory_profiler` and `time` command to measure peak memory and total runtime. **Output**: Write metrics to `logs/constraint_metrics.json`. **Authority**: Implements SC-004 (Computational Feasibility) by making the constraint locally measurable.
- [X] T044b [P] **[SC-004]** Update `.github/workflows/ci.yml` (T042a) to execute `code/utils/constraints.py` and fail if constraints are exceeded. **Method**: Run T044a script in CI and parse `logs/constraint_metrics.json`. **Requirement**: Must execute in the target CI environment. **Depends on**: T042a (CI workflow), T044a (local script).
- [ ] T049a [P] **[FR-003]** Generate `state/manifest.json` with checksums for `data/processed/descriptors.parquet` (T014c) and `data/processed/cluster_map.csv` (T031c). **Input**: Read `data/processed/descriptors.parquet` and `data/processed/cluster_map.csv`. **Output**: Write `state/manifest.json`. **Authority**: Implements Constitution Principle III (Data Hygiene) and V (Versioning Discipline).
- [ ] T049 [P] **[FR-003]** Add checksum validation step in `code/main.py` to verify that `data/processed/cluster_map.csv` (T031c) and `data/processed/descriptors.parquet` (T014c) have not been modified between the clustering and SHAP stages. **Verification**: Assert that file hashes match the expected values stored in `state/manifest.json` (T049a). **Depends on**: T049a (manifest generation).

---

## Phase 7: Revision & Stability Hardening (Post-Analyze Fixes)

**Purpose**: Address specific stability and reproducibility concerns raised by the analysis phase to ensure robust execution on free-tier CI.

- [X] T046 [P] [US1] **[Determinism Fix]** Add a deterministic seed to the `np.random` call in `code/data/split_data.py` (T022) and verify that the train/test split is identical across multiple runs. **Verification**: Run split 5 times; assert `df_train.shape` and `df_test.shape` are identical every time. **Authority**: Addresses potential non-determinism in random split implementation.
- [X] T047 [P] [US3] **[Bootstrap Robustness]** Refactor `code/models/interpret.py` (T033a) to use a fixed random seed for the bootstrap resampling loop and ensure the `np.random.choice` logic handles edge cases (e.g., empty clusters) gracefully without crashing. **Verification**: Assert that the bootstrap loop completes 100 iterations without raising `IndexError` or `ValueError`.
- [X] T048 [P] [US3] **[Metric Precision]** Update `code/models/interpret.py` (T034a) to calculate Jaccard similarity using `scipy.spatial.distance.jaccard` or a precise set-based implementation to avoid floating-point drift in similarity scores. **Verification**: Assert that Jaccard scores for identical sets are maximal.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on completion of Phase 6 and analysis feedback

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
- **Phase 7 tasks** are independent of each other and can be run in parallel once Phase 6 is complete.

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
- **CRITICAL**: Tasks T014a, T014b, T014c are the ONLY active implementation paths for descriptor generation, correlation audit, and saving. All 'Spec-Default' tasks (T014c, T014d old) have been removed to prevent code conflicts with the ratified Plan.
- **CRITICAL**: Configuration allows YAML for hyperparameters (T004) but seeds must be hardcoded.
- **CRITICAL**: NaN handling uses deterministic logic: >5% missing -> drop, else impute (T016).
- **CRITICAL**: T018 output schema must explicitly exclude TPSA/SMARTS columns and verify no filtering by deriving column count from T014a.
- **CRITICAL**: T032 uses mean absolute SHAP for cluster aggregation.
- **CRITICAL**: T035 exits with code 1 on stability failure and generates `stability_report.md` on success.
- **CRITICAL**: T034a explicitly targets feature clusters for Jaccard similarity calculation as per plan.md SC-003.
- **CRITICAL**: T034a uses the VIF-based groups from T031c (cluster_map.csv), not unsupervised clustering.
- **CRITICAL**: T038a-T038d split the README update into atomic tasks.
- **CRITICAL**: T039b uses `autoflake` for deterministic import removal with explicit verification criteria.
- **CRITICAL**: T039c specifies the exact logging format string.
- **CRITICAL**: T013 must fail loudly on download failure; no synthetic fallback allowed.
- **CRITICAL**: T017 must implement chunked streaming of the QM9 dataset to stay within RAM limits.
- **CRITICAL**: T016 must log the exact number of rows dropped due to NaN handling for auditability.
- **CRITICAL**: T044 must run on GitHub Actions free-tier runner (T042a).
- **CRITICAL**: T042a creates the CI workflow required for T044.
- **CRITICAL**: **NEW**: Phase 7 tasks (T046-T048) address stability, determinism, and numerical precision identified in analysis to ensure robust CI execution.
- **CRITICAL**: **NEW**: T046 ensures deterministic splits for reproducibility.
- **CRITICAL**: **NEW**: T047 and T048 fix potential numerical instability in bootstrap and Jaccard calculations.
- **CRITICAL**: **NEW**: T049 and T049a add artifact integrity checks to prevent silent data corruption.
- **CRITICAL**: **NEW**: T044a and T044b split the constraint verification into local and CI components to ensure executability.
- **CRITICAL**: **NEW**: T013 and T017 explicitly implement `streaming=True` to prevent OOM on limited RAM.
- **CRITICAL**: **UPDATED**: Removed all 'Spec-Default' tasks (T014c, T031a, T033a old) that implement logic forbidden by the Plan. Retained only the ratified 'Plan-Override' tasks as the sole active implementation paths.
- **CRITICAL**: **UPDATED**: Reordered Phase 3 and Phase 5 to ensure strict Producer-Consumer dependencies (T014a -> T014c -> T018, T031a/b/c -> T032b -> T033a/b -> T034a).
- **CRITICAL**: **UPDATED**: Explicitly defined schema for T006 (tests/contract/ validators) to prevent ambiguity using dynamic column patterns.
- **CRITICAL**: **UPDATED**: T006 is explicitly listed as a prerequisite for T019 in the Dependencies section.
- **CRITICAL**: **UPDATED**: T014a, T014b, T014c split the descriptor generation, audit, and saving logic to ensure independent verification.
- **CRITICAL**: **UPDATED**: T014b explicitly implements the 'Ratified Plan Override' for correlation filtering by logging but not removing features.
- **CRITICAL**: **UPDATED**: T031a, T031b, T031c split VIF logic into calculation, grouping, and writing for independent testing.
- **CRITICAL**: **UPDATED**: T033a, T033b split SHAP-only resampling logic and artifact generation.
- **CRITICAL**: **UPDATED**: T031d ensures migration of VIF logic from `feature_selection.py` to `feature_clustering.py`.
- **CRITICAL**: **UPDATED**: T016b adds a dedicated unit test for 3D exclusion within the NaN handling pipeline.
- **CRITICAL**: **UPDATED**: T018 derives `expected_input_columns` dynamically from T014a output to avoid hardcoded values.
- **CRITICAL**: **UPDATED**: T019 depends on T014c (producer) and T006, not T018.
- **CRITICAL**: **UPDATED**: T032b depends directly on T031c and T026, removing redundant T032a.
- **CRITICAL**: **UPDATED**: T031b depends on T014c (via T014c) to ensure data exists.
- **CRITICAL**: **UPDATED**: T033b explicitly references the 'Ratified Plan Override' in its description.