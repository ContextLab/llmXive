# Tasks: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

**Input**: Design documents from `/specs/001-predicting-molecular-reactivity/`
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

- [ ] T001a [P] Create data directories: `data/raw`, `data/processed`, `data/assets`
- [ ] T001b [P] Create code and artifact directories: `code`, `artifacts`, `tests`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `torch`, `rdkit`, `scikit-learn`, `pandas`, `datasets`, `networkx`)
- [ ] T003 [P] Configure linting (flake8/ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/loaders.py` with robust retry logic (exponential backoff) for dataset downloads
- [ ] T005 Implement `code/utils/graph_utils.py` for molecular graph construction (SMILES → Node/Edge features)
- [ ] T006 Implement `code/utils/metrics.py` for MSE, MAE, Pearson R, and statistical testing functions
- [ ] T007 Create base configuration management (`code/config.py`) for random seeds and device settings (`device='cpu'`)
- [ ] T008 Setup logging infrastructure to write structured logs to `artifacts/logs/` and `artifacts/metrics.json`
- [ ] T009 Implement checksum verification (SHA-256) for raw data in `data/raw/`
- [ ] T009a [P] [FR-008] Download, verify, and ingest the curated reference set of 50 known reactive substructures into `data/assets/reference_substructures.csv` (or `.json`), ensuring checksum validation
- [ ] T009b [P] [FR-009] Download, verify, and ingest the external kinetic dataset (≥20 molecules with experimental rates) into `data/assets/kinetic_dataset.csv` (or `.json`), ensuring checksum validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Feasible Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download QM9 subset and preprocess into graph structures using only CPU resources, ensuring memory safety.

**Independent Test**: The pipeline can be fully tested by executing the data download and preprocessing script on a CPU-only runner and verifying that the output graph objects are correctly formed and fit within memory limits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Unit test for SMILES parsing and exclusion logic in `tests/unit/test_parsing.py`
- [ ] T011 [P] [US1] Integration test for full download → preprocess flow in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/01_download_data.py` to fetch QM9 subset (via `datasets.load_dataset` or verified URL) with error handling and retry logic
- [ ] T013 [US1] Implement `code/02_preprocess_graphs.py` to convert SMILES to graphs using RDKit (Node: atomic number, hybridization, formal charge; Edge: bond type, conjugation)
- [ ] T014a [US1] Implement memory monitoring logic in `code/02_preprocess_graphs.py` with an **automatic trigger mechanism** that detects when RAM usage exceeds 4 GB
- [ ] T014b [US1] Implement subset sampling strategy in `code/02_preprocess_graphs.py` that **automatically reduces** batch size or molecule count when T014a's trigger activates, logging the adjustment
- [ ] T015 [US1] Implement Murcko scaffold splitting logic (80/20) in `code/02_preprocess_graphs.py`
- [ ] T016 [US1] Serialize preprocessed graphs to `data/processed/` (`.parquet` or `.pkl`) with derivation logs
- [ ] T017 [US1] Add validation to ensure excluded invalid SMILES count is < 0.1% of total

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train lightweight Spectral GNN, Heterophily-aware GNN, and Random Forest baseline; compare performance.

**Independent Test**: The training and evaluation loop can be tested independently by running the training script for a fixed number of epochs and verifying that both models converge and produce metric logs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for model architecture initialization (CPU mode) in `tests/unit/test_models.py`
- [ ] T019 [P] [US2] Integration test for training loop convergence in `tests/integration/test_training.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement lightweight Spectral GNN architecture in `code/models/spectral_gnn.py` (CPU-only, no CUDA)
- [ ] T021 [US2] Implement Heterophily-aware GNN architecture in `code/models/hetero_gnn.py` (based on VR-GNN principles, CPU-only)
- [ ] T022 [US2] Implement Random Forest baseline using Morgan fingerprints in `code/models/random_forest_baseline.py`
- [ ] T023 [US2] Implement `code/train_models.py` to train all three models for a sufficient number of epochs with early stopping.
- [ ] T024 [US2] Implement `code/04_evaluate.py` to generate predictions and compute MSE, MAE, Pearson R for all models
- [ ] T025 [US2] Implement `code/utils/metrics.py` function for **Cluster-based Permutation Test** to statistically compare GNN vs. RF errors. **Note**: This task executes the ratified Methodological Note in `plan.md` which supersedes the "paired t-test" requirement in FR-006 due to scaffold-based splitting constraints. This task replaces the t-test logic and explicitly satisfies FR-006 via the ratified alternative method.
- [ ] T025a [P] [FR-006] Update `plan.md` Methodological Note to explicitly state: "The Cluster-based Permutation Test is the ratified replacement for FR-006's paired t-test requirement. FR-006 is interpreted as satisfied by this alternative method."
- [ ] T025b [P] [FR-006] Update `spec.md` FR-006 text to explicitly state: "System MUST apply a **Cluster-based Permutation Test** (as the ratified replacement for the initial paired t-test requirement)..."
- [ ] T026 [US2] Log all model weights and metrics to `artifacts/` and `artifacts/metrics.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Attribution and Interpretability Analysis (Priority: P3)

**Goal**: Identify structural/electronic features contributing to predictions and validate against curated references.

**Independent Test**: The attribution analysis can be tested by running the GNNExplainer on a subset of molecules and verifying valid importance scores against the curated reference set.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for attribution score calculation in `tests/unit/test_attribution.py`
- [ ] T028 [P] [US3] Contract test for attribution output schema in `tests/contract/test_attribution_schema.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/05_attribution.py` using GNNExplainer or gradient-based methods to generate importance scores
- [ ] T030 [US3] Load curated reference set of 50 known reactive substructures from `data/assets/reference_substructures.csv` (produced by T009a)
- [ ] T031 [US3] Implement logic to aggregate importance scores across the dataset and rank the most significant structural/electronic features.
- [ ] T032 [US3] Implement validation logic to compare attribution results against the curated reference set (alignment score calculation)
- [ ] T033 [US3] Load external kinetic dataset (≥20 molecules) from `data/assets/kinetic_dataset.csv` (produced by T009b) and validate HOMO-LUMO gap proxy correlation
- [ ] T034 [US3] Generate attribution maps and validation reports in `artifacts/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` (include `quickstart.md` with run instructions)
- [ ] T036 Code cleanup and refactoring to ensure type hints and docstrings are complete
- [ ] T037 Performance optimization: Verify end-to-end runtime ≤ 6 hours and memory ≤ 4 GB on CI
- [ ] T038 [P] Additional unit tests for edge cases (invalid SMILES, download failures) in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation to ensure all artifacts are reproducible
- [ ] T040 Verify `state/` YAML is updated with SHA-256 hashes of final artifacts

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
- **User Story 2 (P2)**: Depends on US1 (requires preprocessed data)
- **User Story 3 (P3)**: Depends on US2 (requires trained models)

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
Task: "Unit test for SMILES parsing and exclusion logic in tests/unit/test_parsing.py"
Task: "Integration test for full download → preprocess flow in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/01_download_data.py to fetch QM9 subset..."
Task: "Implement code/02_preprocess_graphs.py to convert SMILES to graphs..."
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
   - Developer B: User Story 2 (waiting for data)
   - Developer C: User Story 3 (waiting for models)
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