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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `specs/`)
- [ ] T002 Initialize Python 3.11 project with `pyproject.toml` and core dependencies (`rdkit`, `torch`, `torch-geometric`, `scikit-learn`, `shap`, `pandas`, `datasets`, `chembl_webresource_client`, `mordred`, `pytest`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `src/utils/versioning.py` with `update_state()` logic for Constitution Principle V (hash calculation, atomic writes to `state/projects/PROJ-220-...yaml`)
- [ ] T005 [P] Implement `src/utils/logging.py` with audit logging infrastructure for data exclusions (FR-007)
- [ ] T006 [P] Implement `src/utils/chemistry.py` with SMILES validation, Gasteiger partial charge calculation, and pKa estimation logic
- [ ] T007 Implement `src/data/descriptors.py` to compute independent descriptor vectors (Hammett σ, Taft Es, Charton ν, Verloop B1/B5, MR) for validation (SC-003)
- [ ] T008 Implement `src/data/ingestion.py` skeleton with `validate_citations.py` logic (URL reachability, checksum verification, title overlap) to enforce Citation Validation Gate
- [ ] T009 Implement `src/data/split.py` with scaffold-based split strategy (70/15/15) ensuring balanced partitions
- [ ] T010 Configure environment configuration management and memory limit enforcement (FR-008)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Download SN2 reaction data from ChEMBL/NIST, filter for amines, normalize kinetics, and construct heterogeneous molecular graphs.

**Independent Test**: The pipeline produces a JSON/CSV file containing molecular graphs (node/edge attributes), normalized log(rate) values, and calculated pKa values, with no missing values for required fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for data ingestion schema in `tests/contract/test_ingestion_schema.py`
- [ ] T012 [P] [US1] Integration test for end-to-end ingestion and graph construction on a small subset in `tests/integration/test_ingestion_flow.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `src/data/ingestion.py` logic to fetch from ChEMBL and NIST APIs, filter for primary/secondary amines and SN2 reactions, and handle invalid SMILES (US-1, FR-001)
- [ ] T014 [US1] Implement kinetic data normalization logic (Arrhenius/Eyring) with fallback to reaction-class-specific average Ea; flag/exclude records missing necessary data (FR-001, FR-007)
- [ ] T015 [US1] Implement `src/data/preprocessing.py` to construct heterogeneous molecular graphs using RDKit (node features: atom type, hybridization, Gasteiger charge, pKa; edge features: bond order) (FR-002, US-1)
- [ ] T016 [US1] Implement streaming data loading logic to handle large datasets exceeding available RAM, accumulating statistics online without full memory load (Plan: Streaming Data Loading)
- [ ] T017 [US1] Add logging for all data exclusions (missing kinetic data, invalid SMILES, missing temperature) to `data/raw/audit_log.json` (FR-007)
- [ ] T018 [US1] Verify output dataset contains at least 500 valid records with complete SMILES, normalized kinetics, and calculated pKa (US-1 Acceptance Scenario 1)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline and GNN Model Training (Priority: P2)

**Goal**: Train a baseline linear model and a heterophily-aware GNN on the constructed dataset within CPU constraints.

**Independent Test**: The training script executes successfully on a standard CPU environment, producing two model artifacts and a test set prediction file with MAE and R² metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for model artifact schema in `tests/contract/test_model_artifact.py`
- [ ] T020 [P] [US2] Integration test for training pipeline completion within time/memory limits in `tests/integration/test_training_flow.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `src/models/baseline.py` with Random Forest/Linear Regression using traditional descriptors (pKa, MW, Taft Es) (FR-004, US-2)
- [ ] T022 [US2] Implement `src/models/gnn.py` with a heterophily-aware GAT or GraphSAGE architecture (edge-type awareness) as primary/fallback method (FR-003, US-2, Plan: Heterophily-aware GNN)
- [ ] T023 [US2] Implement training loop in `src/train.py` with 70/15/15 scaffold split, memory limit enforcement, and graceful exit/sampling if limits exceeded (FR-003, FR-008, US-2)
- [ ] T024 [US2] Implement evaluation logic to compute R² and MAE for both models on the held-out test set (US-2 Acceptance Scenario 3)
- [ ] T025 [US2] Implement permutation test or bootstrap-based 95% confidence interval on absolute errors to determine statistical significance (FR-006, SC-002)
- [ ] T026 [US2] Verify training completes within 6 hours on 2-core CPU and memory usage < 7GB (SC-004, SC-005)
- [ ] T027 [US2] Ensure GNN predictions contain no NaN values and cover every test sample (US-2 Acceptance Scenario 2)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Feature Analysis (Priority: P3)

**Goal**: Apply SHAP analysis to rank atomic features and validate against independent chemical descriptors.

**Independent Test**: The interpretability script produces a ranked list of features and a visualization file, with a statistically significant correlation to the independent descriptor vector.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for feature importance schema in `tests/contract/test_feature_importance.py`
- [ ] T029 [P] [US3] Integration test for SHAP analysis and correlation validation in `tests/integration/test_interpretability_flow.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `src/models/interpret.py` to perform SHAP analysis on the trained GNN, generating ranked atomic feature importance (FR-005, US-3)
- [ ] T031 [US3] Implement visualization logic to highlight top-contributing atoms/substructures in molecular graphs (US-3 Acceptance Scenario 2)
- [ ] T032 [US3] Compute Pearson correlation between aggregated SHAP importance and the independent descriptor vector (Hammett/Taft/Verloop/MR) (FR-005, SC-003)
- [ ] T033 [US3] Perform statistical significance testing (p < 0.05) and comparison against random baseline (shuffled labels) (SC-003, US-3 Acceptance Scenario 3)
- [ ] T034 [US3] Verify top 5 features show Pearson correlation r ≥ 0.6 with the independent descriptor vector (US-3 Acceptance Scenario 1)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `specs/001-predicting-amine-reactivity/quickstart.md` and `README.md`
- [ ] T036 Code cleanup and refactoring of chemistry utilities
- [ ] T037 Performance optimization for SHAP analysis on CPU
- [ ] T038 [P] Additional unit tests for `src/utils/chemistry.py` and `src/data/split.py` in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
Task: "Implement src/data/ingestion.py logic to fetch from ChEMBL and NIST APIs"
Task: "Implement src/data/preprocessing.py to construct heterogeneous molecular graphs"
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
- **Critical**: Data ingestion tasks (T013-T014) must implement strict failure on invalid data (no synthetic fallbacks) as per Constitution Principle II.
- **Critical**: Streaming logic (T016) must be implemented to prevent OOM on GitHub Actions runner.
- **Critical**: Heterophily-aware GNN (T022) is required; standard GCN is insufficient for reaction graphs.
