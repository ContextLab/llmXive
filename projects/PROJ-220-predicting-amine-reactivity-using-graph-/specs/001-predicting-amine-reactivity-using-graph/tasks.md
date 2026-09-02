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
- [X] T007a [P] Implement `src/data/descriptors.py` function `compute_hammett()` using `mordred` or lookup tables to calculate Hammett σ_p, σ_m, σ+, σ- for aromatic substituents (SC-003, FR-005)
- [X] T007b [P] Implement `src/data/descriptors.py` function `compute_taft_charton()` to calculate Taft Es, Es_s, and Charton ν parameters (SC-003, FR-005)
- [X] T007c [P] Implement `src/data/descriptors.py` function `compute_verloop()` to calculate Verloop B1, B5 parameters (SC-003, FR-005)
- [X] T007d [P] Implement `src/data/descriptors.py` function `compute_mr()` to calculate Molar Refractivity (MR) using `rdkit`/`mordred` (SC-003, FR-005)
- [X] T007e [P] Implement `src/data/descriptors.py` function `aggregate_independent_vector()` to combine outputs from T007a-d into the single 'independent descriptor vector' required by SC-003 for the correlation test. **Deliverable**: A function returning a structured array/vector of all descriptors per molecule. **Verification**: Unit test verifying the vector contains non-NaN values for all 10 descriptors for a test molecule. (SC-003, FR-005)
- [X] T008 [P] Implement `src/utils/validate_citations.py` as a standalone script to enforce the Citation Validation Gate (URL reachability, checksum verification, title overlap) per plan.md
- [X] T009 [P] Implement the call to `validate_citations()` within `src/data/ingestion.py` main execution flow, ensuring it triggers *before* any `load_dataset` or API call. **Deliverable**: Code block in `ingestion.py` invoking the validator. **Verification**: Pipeline must exit with code 1 if validation fails. (Plan: Citation Validation Gate, Constitution Principle II)
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

- [X] T012 [P] [US1] Contract test for data ingestion schema in `tests/contract/test_ingestion_schema.py`
- [X] T013 [P] [US1] Integration test for end-to-end ingestion and graph construction on a small subset in `tests/integration/test_ingestion_flow.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement `src/data/ingestion.py` logic to fetch from ChEMBL and PubChem APIs, filter for primary/secondary amines and SN2 reactions, handle invalid SMILES, and **call `validate_citations()` (T009) before fetching**. **Critical**: Must raise on fetch failure; NO synthetic fallback. **Deliverable**: `src/data/ingestion.py` with fetch logic and citation gate integration. **Depends on**: T015a (normalization logic), T009. (US-1, FR-001)
- [X] T015a [US1] Implement `src/utils/chemistry.py` function `normalize_kinetics(k, T, Ea: float | None = None, class_avg_ea: float | None = None)` to normalize kinetic data using Arrhenius/Eyring equations. **Mandatory**: If `Ea` is missing, use `class_avg_ea` if provided; if both missing, return `None` and flag for exclusion. **Deliverable**: `normalize_kinetics` function in `chemistry.py`. **Verification**: Unit test verifying calculation for known values and exclusion logic when Ea is missing. (FR-001)
- [X] T015b [US1] Integrate `normalize_kinetics` (T015a) into `src/data/ingestion.py` (T014) to process fetched records. **Deliverable**: Updated `ingestion.py` using T015a. (FR-001)
- [X] T016 [US1] Implement `src/data/preprocessing.py` to construct heterogeneous molecular graphs using RDKit. **Schema Definition**: `ReactionRecord` must include: `smiles`, `normalized_log_rate`, `pKa`, `graph` (nodes: `{'atom_type': int, 'hybridization': int, 'charge': float, 'pKa': float}`, edges: `{'bond_order': int}`). **Deliverable**: `src/data/preprocessing.py` with graph construction logic writing to `data/processed/graphs.h5`. **Verification**: Verify file exists and contains 1000 records with non-null node features and correct schema. **Depends on**: T006 (pKa logic), T015a. (FR-002, US-1)
- [X] T017 [US1] Implement `src/data/streaming_loader.py` with `load_batch()` generator yielding `ReactionRecord` objects (as defined in T016) to handle large datasets exceeding available RAM, accumulating statistics online without full memory load. **Critical**: Must stream real data; no toy dataset substitution. **Depends on**: T014, T015a, T016. (Plan: Complexity Tracking)
- [X] T018a [US1] Implement logging in `src/data/ingestion.py` (T014, T015) to explicitly record all normalization exclusions (missing Ea, missing temperature) to `data/raw/audit_log.json`. **Schema**: `{'excluded_count': int, 'reason': str, 'record_ids': list, 'timestamp': str}`. **Deliverable**: Logging code in `ingestion.py`. **Verification**: Verify `audit_log.json` contains entries for excluded records. **Depends on**: T015a. (FR-007)
- [X] T018b [US1] Implement logging in `src/data/preprocessing.py` (T016) to explicitly record all graph construction exclusions (invalid SMILES, missing pKa) to `data/raw/audit_log.json`. **Schema**: `{'excluded_count': int, 'reason': str, 'record_ids': list, 'timestamp': str}`. **Deliverable**: Logging code in `preprocessing.py`. **Verification**: Verify `audit_log.json` contains entries for excluded records. **Depends on**: T016. (FR-007)
- [X] T019 [US1] Verify output dataset contains valid records with no missing required fields (SMILES, normalized kinetics, calculated pKa) (US-1 Acceptance Scenario 1). **Deliverable**: `tests/unit/test_dataset_completeness.py` script. **Verification**: Run script and assert all records pass. (SC-006)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline and GNN Model Training (Priority: P2)

**Goal**: Train a baseline linear model and a heterophily-aware GNN on the constructed dataset within CPU constraints.

**Independent Test**: The training script executes successfully on a standard CPU environment, producing two model artifacts and a test set prediction file with MAE and R² metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model artifact schema in `tests/contract/test_model_artifact.py`
- [X] T021 [P] [US2] Integration test for training pipeline completion within time/memory limits in `tests/integration/test_training_flow.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement `src/models/baseline.py` with Random Forest/Linear Regression using traditional descriptors (pKa, MW, Taft Es). **Deliverable**: `BaselineModel` class in `baseline.py`. **Verification**: Unit test verifying training on synthetic data. (FR-004, US-2)
- [X] T023 [US2] Implement `src/models/gnn.py` with a heterophily-aware GAT or GraphSAGE architecture (edge-type awareness) as primary/fallback method. **Deliverable**: `HeterophilyGAT` class in `gnn.py`. **Verification**: Unit test verifying model construction and forward pass. (FR-003, US-2, Plan: Heterophily-aware GNN)
- [X] T024 [US2] Implement training loop in `src/train.py` with a scaffold split, memory limit enforcement (T011a), and sampling (T011b) if limits exceeded. **Deliverable**: `train.py` with training logic. **Verification**: Run on subset and verify completion. **Depends on**: T016 (graph dataset), T022, T023. (FR-003, FR-008, US-2)
- [X] T025 [US2] Implement evaluation logic to compute R² and MAE for both models on the held-out test set. **Deliverable**: `evaluate()` function in `train.py` or `src/models/baseline.py`. **Verification**: Unit test verifying metric calculation. (US-2 Acceptance Scenario 3)
- [X] T026 [US2] Implement `stratified_permutation_test()` in `src/models/baseline.py` or `src/train.py` to perform a permutation test or bootstrap CI on absolute errors. **Mandatory**: The resampling strategy MUST be stratified by scaffold (blocking) to account for scaffold-induced correlation as required by FR-006. **Deliverable**: `stratified_permutation_test()` function. **Verification**: Unit test verifying that samples with the same scaffold are kept together during resampling and p-value is calculated. (FR-006, SC-002)
- [X] T027 [US2] Verify training completes within 6 hours on 2-core CPU and memory usage < 7GB, and generate `data/derived/training_metrics.json` containing `duration_seconds`, `peak_memory_mb`, `r2_gnn`, `mae_gnn`, `r2_baseline`, `mae_baseline` fields. **Deliverable**: `training_metrics.json`. **Verification**: Verify file exists and keys are present. (SC-004, SC-005)
- [X] T028 [US2] Ensure GNN predictions contain no NaN values and cover every test sample (US-2 Acceptance Scenario 2). **Deliverable**: Verification script in `tests/unit/test_predictions.py`. (US-2 Acceptance Scenario 2)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Feature Analysis (Priority: P3)

**Goal**: Apply SHAP analysis to rank atomic features and validate against independent chemical descriptors.

**Independent Test**: The interpretability script produces a ranked list of features and a visualization file, with a statistically significant correlation to the independent descriptor vector.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for feature importance schema in `tests/contract/test_feature_importance.py`
- [X] T030 [P] [US3] Integration test for SHAP analysis and correlation validation in `tests/integration/test_interpretability_flow.py`

### Implementation for User Story 3

- [X] T031 [US3] Implement `src/models/interpret.py` to perform SHAP analysis on the trained GNN (T023), generating ranked atomic feature importance. **Deliverable**: `run_shap_analysis()` function writing to `data/derived/shap_importance.csv`. **Verification**: Verify file exists and contains ranked features. **Depends on**: T023, T007e. (FR-005, US-3)
- [X] T032 [US3] Implement visualization logic to highlight top-contributing atoms/substructures in molecular graphs. **Deliverable**: `visualize_shap()` function in `interpret.py` writing to `data/derived/shap_plots/`. **Verification**: Verify plot files exist. (US-3 Acceptance Scenario 2)
- [X] T033 [US3] Compute Pearson correlation between aggregated SHAP importance (from T031) and the independent descriptor vector (produced by T007e). **Deliverable**: `compute_correlation()` function in `interpret.py`. **Verification**: Unit test verifying correlation calculation. **Depends on**: T031, T007e. (FR-005, SC-003)
- [X] T034 [US3] Perform statistical significance testing (p < 0.05) and comparison against random baseline (shuffled labels). **Deliverable**: `test_significance()` function in `interpret.py`. **Verification**: Unit test verifying p-value calculation. (SC-003, US-3 Acceptance Scenario 3)
- [X] T035 [US3] Verify top 5 features show Pearson correlation r ≥ 0.6 with the independent descriptor vector and generate `data/derived/interpretability_report.json` with `correlation_coefficient`, `p_value`, `top_5_features` fields. **Deliverable**: `interpretability_report.json`. **Verification**: Verify file exists and keys are present. (US-3 Acceptance Scenario 1)

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
- **Critical**: Heterophily-aware GNN (T023) is required; standard GCN is insufficient for reaction graphs.
- **Critical**: All data loading must use real, verified sources; synthetic data generation is strictly prohibited.
- **Critical**: Sampling strategy (T011b) must be implemented to satisfy FR-008 "or sampling" clause.
- **Critical**: Descriptor calculations (T007a-e) must be completed to enable US-3 validation, specifically T007e for vector aggregation.
- **Critical**: T015a must implement dynamic `normalize_kinetics` with proper signature for missing Ea handling.
- **Critical**: T026 must implement stratified resampling to handle scaffold-induced correlation.
- **Critical**: T009 must implement the actual code call to the citation validator.
- **Critical**: T016 must define the `ReactionRecord` schema explicitly.
- **Critical**: T033 must explicitly depend on T031.