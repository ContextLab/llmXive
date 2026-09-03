# Tasks: Predicting Amine Reactivity Using Graph Neural Networks and Public Databases

**Input**: Design documents from `/specs/001-predicting-amine-reactivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directory structure: `src/`, `tests/`, `data/raw`, `data/processed`, `data/derived`, `artifacts`, `specs/001-predicting-amine-reactivity/`
- [X] T001b [P] Create `src/data/`, `src/models/`, `src/utils/` subdirectories
- [X] T002 Initialize Python 3.11 project with `pyproject.toml` and core dependencies (`rdkit`, `torch`, `torch-geometric`, `scikit-learn`, `shap`, `pandas`, `datasets`, `chembl_webresource_client`, `mordred`, `pytest`). **Note**: Ensure `rdkit` version compatibility with `torch` and `torch-geometric` is verified in the virtualenv setup script.
- [X] T003a [P] Create `pyproject.toml` configuration sections for `[tool.black]` (line-length 88) and `[tool.ruff]` (select E4, E7, E9, F)
- [X] T003b [P] Create `.gitignore` file excluding `__pycache__`, `*.pyc`, `data/raw/*`, `data/processed/*`, `artifacts/*`, `*.log`, `.env`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/utils/versioning.py` with `update_state()` logic for Constitution Principle V (hash calculation, atomic writes to `state/projects/PROJ-220-...yaml`)
- [X] T005 [P] Implement `src/utils/logging.py` with audit logging infrastructure for data exclusions (FR-007)
- [X] T006 [P] Implement `src/utils/chemistry.py` with SMILES validation, Gasteiger partial charge calculation, and pKa estimation logic
- [X] T007a0 [P] [Spec Update] Update `spec.md` Assumptions section to explicitly state: "The independent descriptor vector (Hammett, Taft, etc.) MUST be calculated on-the-fly using `mordred`/`rdkit` to ensure construct validity for the custom dataset, overriding the previous assumption of literature lookup." **Deliverable**: Updated `spec.md`. **Verification**: Verify text change in `spec.md`. (Resolves T007a1-T007a4 conflict)
- [X] T007a [P] [US1] Implement `src/data/descriptors.py` suite of functions: `compute_hammett_sigma()`, `compute_taft_es()`, `compute_charton()`, `compute_verloop_mr()`, and `aggregate_independent_vector()`. **Mandatory**: Calculate all descriptors on-the-fly (no lookup tables). **Deliverable**: `src/data/descriptors.py` containing all 5 functions. **Verification**: Unit test `tests/unit/test_descriptors.py` verifying non-NaN values for all 10 descriptors and correct aggregation schema. (SC-003, FR-005, Constitution Principle VII, T007a0)
- [X] T008 [P] Implement `src/utils/validate_citations.py` as a standalone script to enforce the Citation Validation Gate (URL reachability, checksum verification, title overlap) per plan.md
- [X] T009a [P] Implement the call to `validate_citations()` within `src/data/ingestion.py` main execution flow, ensuring it triggers *before* any `load_dataset` or API call. **Deliverable**: Code block in `ingestion.py` invoking the validator. **Verification**: Unit test verifying the function is called. (Plan: Citation Validation Gate, Constitution Principle II)
- [X] T009b [P] Implement `tests/integration/test_citation_gate_blocking.py` to verify that the Citation Validation Gate causes the `ingestion.py` pipeline to exit with code 1 and halt processing when validation fails (e.g., unreachable URL). **Deliverable**: Integration test script. **Verification**: Run test with mock unreachable URL and assert exit code 1. (Plan: Citation Validation Gate, Constitution Principle II)
- [X] T010 Implement `src/data/split.py` with scaffold-based split strategy ensuring balanced partitions
- [X] T011a [P] Implement `src/utils/memory_monitor.py` with `check_limits()` function (signature: `check_limits(memory_threshold_mb=6500)`) that returns a boolean and `graceful_exit()` function that calls `sys.exit(137)` on breach. **Deliverable**: `src/utils/memory_monitor.py` with these functions. **Verification**: Unit test asserting `graceful_exit()` raises `SystemExit(137)`. (FR-008)
- [X] T011b [P] Implement `src/utils/sampling.py` with `sample_dataset()` function to reduce dataset size if memory limits are exceeded, logging the sampling strategy (FR-008)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Download SN2 reaction data from ChEMBL/PubChem, filter for amines, normalize kinetics, and construct heterogeneous molecular graphs.

**Independent Test**: The pipeline produces a JSON/CSV file containing molecular graphs (node/edge attributes), normalized log(rate) values, and calculated pKa values, with no missing values for required fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Implement `tests/contract/test_ingestion_schema.py` with function `test_ingestion_schema_validates_reaction_id_field()` asserting that the ingestion output schema contains `reaction_id`, `reactant_smiles`, and `rate_constant`. **Verification**: Run test and assert failure on missing fields. (US-1, FR-001)
- [X] T013 [P] [US1] Implement `tests/integration/test_ingestion_flow.py` with function `test_ingestion_flow_validates_and_excludes()` asserting that invalid SMILES or missing kinetic data are excluded and logged. **Verification**: Run test with mock invalid data and assert exclusion count > 0. (US-1, FR-007)

### Implementation for User Story 1

- [X] T015 [US1] Implement `src/data/ingestion.py` logic to normalize kinetic data using Arrhenius/Eyring equations (`normalize_kinetics`) and calculate reaction-class-specific average Ea (`calculate_class_avg_ea`). **Mandatory**: If `Ea` is missing, use `class_avg_ea`; if both missing, return `None` and flag for exclusion. **Deliverable**: `src/data/ingestion.py` containing `normalize_kinetics` and `calculate_class_avg_ea` functions. **Verification**: Unit test verifying calculation for known values and exclusion logic. (FR-001)
- [X] T014 [US1] Implement `src/data/ingestion.py` logic to fetch from ChEMBL and PubChem APIs, filter for primary/secondary amines and SN2 reactions, handle invalid SMILES, and **call `validate_citations()` (T009a) before fetching**. **Critical**: Must raise on network fetch failure; NO synthetic fallback. **Deliverable**: `src/data/ingestion.py` with fetch logic and citation gate integration. **Depends on**: T015 (normalization logic), T009a. (US-1, FR-001)
- [ ] T016 [US1] Implement `src/data/preprocessing.py` to construct heterogeneous molecular graphs using RDKit. **Schema Definition**: `ReactionRecord` must include: `smiles`, `normalized_log_rate`, `pKa`, `graph` (nodes: `{'atom_type': int, 'hybridization': int, 'charge': float, 'pKa': float}`, edges: `{'bond_order': int}`). **Deliverable**: `src/data/preprocessing.py` with graph construction logic writing to `data/processed/graphs.h5`. **Verification**: Verify file exists and contains a sufficient number of records with non-null node features and correct schema. **Depends on**: T006 (pKa logic), T015. (FR-002, US-1)
- [X] T049 [US1] Implement `src/data/ingestion.py` function `validate_data_integrity()` to perform a statistical sanity check (distribution of log(rate), pKa ranges) on the fetched subset *after* T016 but *before* T017. **Deliverable**: Function writing `data/derived/audit_integrity.json` with `mean_log_rate`, `std_log_rate`, `min_pka`, `max_pka`, and `status` ('PASS'/'FAIL'). **Verification**: Assert file exists and status is 'PASS'. **Depends on**: T016. (FR-001, FR-007, Data Quality Gate)
- [X] T017 [US1] Implement `src/data/streaming_loader.py` with `load_batch()` generator yielding `ReactionRecord` objects (as defined in T016) to handle large datasets exceeding available RAM, accumulating statistics online without full memory load. **Critical**: Must stream real data; no toy dataset substitution. **Depends on**: T014, T015, T016, T049. (Plan: Complexity Tracking)
- [ ] T018a [US1] Implement logging in `src/data/ingestion.py` (T014, T015) to explicitly record all normalization exclusions (missing Ea, missing temperature) to `data/raw/audit_log.json`. **Schema**: `{'excluded_count': int, 'reason': str, 'record_ids': list, 'timestamp': str}`. **Deliverable**: Logging code in `ingestion.py`. **Verification**: Verify `audit_log.json` contains entries for excluded records. **Depends on**: T015. (FR-007)
- [ ] T018b [US1] Implement logging in `src/data/preprocessing.py` (T016) to explicitly record all graph construction exclusions (invalid SMILES, missing pKa) to `data/raw/audit_log.json`. **Schema**: `{'excluded_count': int, 'reason': str, 'record_ids': list, 'timestamp': str}`. **Deliverable**: Logging code in `preprocessing.py`. **Verification**: Verify `audit_log.json` contains entries for excluded records. **Depends on**: T016. (FR-007)
- [X] T019 [US1] Implement `tests/unit/test_dataset_completeness.py` to verify output dataset contains valid records with no missing required fields (SMILES, normalized kinetics, calculated pKa). **Deliverable**: Test script with assertions for non-null SMILES and finite pKa. **Verification**: Run script and assert all records pass. (SC-006)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline and GNN Model Training (Priority: P2)

**Goal**: Train a baseline linear model and a heterophily-aware GNN on the constructed dataset within CPU constraints.

**Independent Test**: The training script executes successfully on a standard CPU environment, producing two model artifacts and a test set prediction file with MAE and R² metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Implement `tests/contract/test_model_artifact.py` with function `test_model_artifact_schema_contains_hyperparameters()` asserting that the saved model artifact contains `hyperparameters`, `training_metrics`, and `scaffold_split_info`. **Verification**: Run test and assert schema presence. (US-2, FR-003)
- [X] T021 [P] [US2] Implement `tests/integration/test_training_flow.py` with function `test_training_flow_completes_within_time_limit()` asserting that the training pipeline completes within 6 hours and memory < 7GB on a subset. **Verification**: Run test with mock timeout and assert completion. (US-2, FR-008)

### Implementation for User Story 2

- [X] T022 [US2] Implement `src/models/baseline.py` with Random Forest/Linear Regression using traditional descriptors (pKa, MW, Taft Es). **Deliverable**: `BaselineModel` class in `baseline.py`. **Verification**: Unit test verifying training on synthetic data. (FR-004, US-2)
- [ ] T023 [US2] Implement `src/models/gnn.py` with a heterophily-aware GAT or GraphSAGE architecture. **Mandatory**: Explicitly implement edge-type awareness in the aggregation function (e.g., separate weight matrices for different bond types) and include logic to log a switch to a heterophily-aware variant if standard aggregation fails. **Deliverable**: `HeterophilyGAT` class in `gnn.py` with `check_convergence_and_switch()` function. **Verification**: Unit test verifying model construction, forward pass, and switch logging. (FR-003, US-2, Plan: Heterophily-aware GNN, Constitution Principle VI)
- [X] T024 [US2] Implement training loop in `src/train.py` with a scaffold split, memory limit enforcement (T011a), sampling (T011b) if limits exceeded, and **explicit integration of the streaming loader from T017** to ensure memory constraints are enforced during training. **Deliverable**: `train.py` with training logic. **Verification**: Run on subset and verify completion. **Depends on**: T016 (graph dataset), T022, T023, T017. (FR-003, FR-008, US-2)
- [X] T025 [US2] Implement evaluation logic to compute R² and MAE for both models on the held-out test set. **Deliverable**: `evaluate()` function in `train.py` or `src/models/baseline.py`. **Verification**: Unit test verifying metric calculation. (US-2 Acceptance Scenario 3)
- [X] T026 [US2] Implement `stratified_permutation_test()` in `src/models/baseline.py` or `src/train.py` to perform a permutation test or bootstrap CI on absolute errors. **Mandatory**: The stratification key MUST be derived from the `MolecularGraph` scaffold ID (as defined in T016), NOT a random sample ID. **Deliverable**: `stratified_permutation_test()` function. **Verification**: Unit test asserting that samples with the same scaffold ID are kept together during resampling and p-value is calculated. (FR-006, SC-002)
- [ ] T027 [US2] Verify training completes within 6 hours on 2-core CPU and memory usage < 7GB, and generate `data/derived/training_metrics.json` containing `duration_seconds`, `peak_memory_mb`, `r2_gnn`, `mae_gnn`, `r2_baseline`, `mae_baseline` fields. **Deliverable**: `training_metrics.json`. **Verification**: Verify file exists and keys are present. (SC-004, SC-005)
- [X] T028 [US2] Implement `tests/unit/test_predictions.py` to ensure GNN predictions contain no NaN values and cover every test sample. **Deliverable**: Test script with assertions for no NaN and full coverage. (US-2 Acceptance Scenario 2)
- [X] T047 [US2] Implement `src/train.py:setup_training_timeout` with a signal handler for SIGALRM to interrupt training if the estimated time remaining exceeds a threshold, triggering a clean exit and logging the reason. **Deliverable**: Function `setup_training_timeout` in `train.py`. **Verification**: `tests/unit/test_train_timeout.py::test_sigalrm_raises_systemexit` asserting `SystemExit` on timeout. (FR-008, SC-005)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Feature Analysis (Priority: P3)

**Goal**: Apply SHAP analysis to rank atomic features and validate against independent chemical descriptors.

**Independent Test**: The interpretability script produces a ranked list of features and a visualization file, with a statistically significant correlation to the independent descriptor vector.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Implement `tests/contract/test_feature_importance.py` with function `test_feature_importance_schema_contains_ranked_list()` asserting that the SHAP output contains `ranked_features`, `shap_values`, and `correlation_metrics`. **Verification**: Run test and assert schema presence. (US-3, FR-005)
- [X] T030 [P] [US3] Implement `tests/integration/test_interpretability_flow.py` with function `test_interpretability_flow_correlates_with_descriptors()` asserting that the correlation between SHAP and descriptors is computed and logged. **Verification**: Run test and assert correlation value is present. (US-3, FR-005)

### Implementation for User Story 3

- [X] T031 [US3] Implement `src/models/interpret.py` to perform SHAP analysis on the trained GNN (T023), generating ranked atomic feature importance. **Deliverable**: `run_shap_analysis()` function writing to `data/derived/shap_importance.csv`. **Verification**: Verify file exists and contains ranked features. **Depends on**: T023. (FR-005, US-3)
- [X] T032 [US3] Implement visualization logic to highlight top-contributing atoms/substructures in molecular graphs. **Deliverable**: `visualize_shap()` function in `interpret.py` writing to `data/derived/shap_plots/`. **Verification**: Verify plot files exist. (US-3 Acceptance Scenario 2)
- [X] T033 [US3] Compute Pearson correlation between aggregated SHAP importance (from T031) and the independent descriptor vector (produced by T007a). **Deliverable**: `compute_correlation()` function in `interpret.py`. **Verification**: Unit test verifying correlation calculation. **Depends on**: T031, T007a. (FR-005, SC-003)
- [X] T034 [US3] Perform statistical significance testing (p < 0.05) and comparison against random baseline. **Mandatory**: Generate a null distribution by shuffling labels *once* and computing the correlation, then compare the observed correlation against this null. **Deliverable**: `test_significance()` function in `interpret.py`. **Verification**: Unit test verifying p-value calculation. (SC-003, US-3 Acceptance Scenario 3)
- [X] T035 [US3] Implement `tests/unit/test_interpretability_report.py` to verify top 5 features show Pearson correlation r ≥ 0.6 with the independent descriptor vector and generate `data/derived/interpretability_report.json` with `correlation_coefficient`, `p_value`, `top_5_features`, `random_baseline_correlation` fields. **Deliverable**: Test script with assertions for report fields. **Verification**: Verify file exists and keys are present. **Depends on**: T033, T034. (US-3 Acceptance Scenario 1, SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Documentation updates in `specs/001-predicting-amine-reactivity/quickstart.md` and `README.md`
- [X] T037 Code cleanup and refactoring of chemistry utilities
- [X] T038 Performance optimization for SHAP analysis on CPU
- [X] T039 [P] Additional unit tests for `src/utils/chemistry.py` and `src/data/split.py` in `tests/unit/`
- [X] T040 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Phase 7: Revision & Review Resolution

**Purpose**: Address specific reviewer concerns regarding data integrity, streaming implementation, statistical rigor, and model architecture.

- [X] T041 [P] [US1] Implement explicit `streaming=True` flag in `src/data/streaming_loader.py` when calling `datasets.load_dataset` or equivalent API for ChEMBL/NIST sources to ensure memory efficiency on the GitHub runner. **Rationale**: Addresses "Large real datasets" constraint; prevents OOM by streaming chunks rather than loading full dataset. (Plan: Complexity Tracking, Rule: Large real datasets: STREAM the real data)
- [X] T042a [P] [US1] Define `src/utils/exceptions.py` with a custom `DataFetchError(Exception)` class. **Deliverable**: `src/utils/exceptions.py` with class definition. **Verification**: Unit test verifying class inheritance. (Supports T042)
- [X] T042 [US1] Add a strict `try/except` block in `src/data/ingestion.py` (T014) that catches *only* network/API errors (e.g., `requests.exceptions.ConnectionError`) and immediately re-raises `DataFetchError` (from T042a) without any `generate_synthetic_*` fallback. **Note**: Data content errors (missing fields) must follow FR-001 exclusion logic. **Rationale**: Addresses "The loader must FAIL LOUDLY" rule for network issues; ensures no silent substitution of fake data when real fetch fails. (Rule: The loader must FAIL LOUDLY, never fall back to synthetic)
- [X] T042b [P] [US1] Implement `tests/unit/test_data_fetch_error.py` to verify `DataFetchError` is raised on simulated network failure and not on data content errors. **Deliverable**: Test script. **Verification**: Assert `DataFetchError` raised for network error, no exception for data error. (Verification for T042)
- [X] T043 [US1] Add a validation step in `src/data/ingestion.py` that checks if the downloaded dataset contains the `reaction_id`, `reactant_smiles`, and `rate_constant` fields before processing. If missing, raise `DataSchemaError`. **Rationale**: Ensures "Dataset-variable fit" and prevents processing empty or malformed API responses. (US-1, FR-001)
- [X] T045 [US3] Add a "collinearity check" in `src/models/interpret.py` (T031) to verify that the independent descriptor vector components (Hammett, Taft, etc.) are not perfectly correlated with each other before computing the Pearson correlation with SHAP values. **Rationale**: Addresses SC-003 requirement for "statistically significant" correlation; ensures the validation vector is robust. (SC-003, FR-005)
- [X] T046 [US1] Implement a "data provenance log" in `src/data/ingestion.py` that records the exact API query parameters, timestamp, and API version used for every fetch, and append this to the audit log (FR-007) rather than creating a separate file. **Rationale**: Supports Constitution Principle I (Reproducibility) by allowing exact re-fetching of the dataset, while adhering to FR-007 logging requirements. (Plan: Reproducibility, FR-007)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on initial implementation of US1, US2, US3; addresses specific review concerns.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (graphs)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output (trained GNN)

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
- Phase 7 tasks (T041-T046) can be implemented in parallel with Phase 6 polish tasks as they address specific code paths.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data ingestion schema in tests/contract/test_ingestion_schema.py"
Task: "Integration test for end-to-end ingestion and graph construction on a small subset in tests/integration/test_ingestion_flow.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/ingestion.py logic to fetch from ChEMBL and PubChem APIs"
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Interpretability)
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
- **Critical**: Data ingestion tasks (T014) must implement strict failure on invalid data (no synthetic fallbacks) as per Constitution Principle II.
- **Critical**: Streaming logic (T017) must be implemented to prevent OOM on GitHub Actions runner.
- **Critical**: Heterophily-aware GNN (T023) is required; standard GCN is insufficient for reaction graphs. T023 now explicitly includes edge-type awareness and switch logging.
- **Critical**: All data loading must use real, verified sources; synthetic data generation is strictly prohibited.
- **Critical**: Sampling strategy (T011b) must be implemented to satisfy FR-008 "or sampling" clause.
- **Critical**: Descriptor calculations (T007a) must be completed to enable US-3 validation, specifically T007a for vector aggregation.
- **Critical**: T015 must implement dynamic `normalize_kinetics` with proper signature for missing Ea handling.
- **Critical**: T026 must implement stratified resampling using the `MolecularGraph` scaffold ID.
- **Critical**: T009b must implement the integration test for the Citation Validation Gate blocking behavior.
- **Critical**: T016 must define the `ReactionRecord` schema explicitly.
- **Critical**: T033 must explicitly depend on T031.
- **Critical (Revision)**: T041, T042, T042a, T042b, T043, T045, T046 must be implemented to address specific review concerns regarding streaming, failure modes, heterophily, collinearity, provenance, and timeout.
- **Note**: Task T044 has been merged into T023 to ensure the heterophily-aware GNN implementation and verification are completed as a single, atomic deliverable.
- **Note**: Task T048 has been removed as its functionality is covered by T034.
- **Note**: Task T015b has been merged into T015.
- **Note**: Task T007a1-T007a4 have been merged into T007a.
- **Note**: Task T049 has been moved to Phase 3 and refined for data quality.
- **Note**: Task T047 has been refined to remove checkpoint saving.
- **Note**: Task T007a0 updates spec.md to resolve assumption conflicts.
