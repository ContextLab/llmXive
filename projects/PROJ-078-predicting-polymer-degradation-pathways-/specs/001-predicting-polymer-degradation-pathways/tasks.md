# Tasks: Predicting Polymer Degradation Pathways with Graph Neural Networks

**Input**: Design documents from `/specs/001-polymer-degradation/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `state/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pins: `rdkit`, `torch`, `torch-geometric`, `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `requests`)
- [ ] T003 [P] Configure linting (`ruff` or `flake8`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup shared logging infrastructure with file handlers in `code/utils.py`
- [ ] T005 Implement exponential backoff utility (max 3 retries) in `code/utils.py` for API rate limiting
- [ ] T006 Create base configuration loader for environment variables and paths in `code/utils.py`
- [ ] T007 Define `PolymerRecord` and `MolecularGraph` data classes in `code/data_models.py`
- [ ] T008 Setup pytest framework and directory structure (`tests/unit`, `tests/integration`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, filter, and convert polymer degradation records from NIST Chemistry WebBook and Materials Project into a structured graph dataset.

**Independent Test**: Can be fully tested by executing the ingestion script against a small subset of known NIST entries and verifying the output CSV contains valid SMILES strings, numeric environmental parameters, and categorical degradation labels.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [US1] Unit test for SMILES validation and RDKit graph conversion in `tests/unit/test_ingest.py::test_smiles_validation_rejects_invalid`
- [ ] T010 [US1] Unit test for missing data exclusion logic in `tests/unit/test_preprocess.py::test_missing_env_excludes_record`
- [ ] T011 [US1] Integration test for API rate-limit backoff in `tests/integration/test_api_ingestion.py::test_backoff_on_rate_limit`

### Implementation for User Story 1

- [ ] T012 [US1] (Depends on T007) Implement `ingest.py`: Download records from NIST/Materials Project with rate-limit backoff (FR-001, FR-008)
- [ ] T013 [US1] (Depends on T007) Implement `ingest.py`: Validate presence of explicit 'degradation pathway' labels; exclude records if missing (FR-008)
- [ ] T014 [US1] (Depends on T007) Implement `preprocess.py`: Convert SMILES to molecular graphs using RDKit; flag or impute missing temp/pH/UV with documented defaults (pH 7, 25°C) per Spec FR-002; exclude from training set if missing (Plan constraint)
- [ ] T015 [US1] (Depends on T007) Implement `preprocess.py`: Filter dataset to retain only polyesters based on functional group detection in SMILES
- [ ] T016 [US1] (Depends on T007) Implement `preprocess.py`: Save raw and processed datasets to `data/raw/` and `data/processed/` with checksums
- [ ] T017 [US1] (Depends on T007) Add logging for data ingestion actions, exclusions, and flags in `code/ingest.py` and `code/preprocess.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight GNN Training and Feature Attribution (Priority: P2)

**Goal**: Train a lightweight Graph Neural Network (≤3 layers, hidden dim ≤128) on the prepared dataset and generate feature importance scores via Integrated Gradients.

**Independent Test**: Can be fully tested by running the training script on a fixed random seed, verifying the model converges within 6 hours on a CPU-only runner, and confirming that the Integrated Gradients output highlights specific atoms/bonds in the polymer chain.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [US2] Unit test for GNN architecture constraints (layers ≤3, dim ≤128) in `tests/unit/test_model.py::test_gnn_layers_constraint`
- [ ] T019 [US2] Unit test for Integrated Gradients calculation on a dummy graph in `tests/unit/test_model.py::test_integrated_gradients_on_dummy_graph`
- [ ] T020 [US2] Integration test for training loop convergence on CPU in `tests/integration/test_training.py::test_training_converges_cpu`

### Implementation for User Story 2

- [ ] T021 [US2] (Depends on T016) Implement `model.py`: Define lightweight GNN architecture (≤3 layers, hidden dim ≤128) CPU-only (FR-003)
- [ ] T022 [US2] (Depends on T016) Implement `preprocess.py`: Apply bond rotation and atom masking augmentation per Spec FR-004; supplement with functional-group-preserving edge dropout (non-ester bonds only) and SMILES canonicalization if chemically invalid
- [ ] T023 [US2] (Depends on T016) Implement `train.py`: Training loop with 5-fold cross-validation (or leave-one-out if n < 50) and random seed pinning (FR-003)
- [ ] T024 [US2] (Depends on T016) Implement `model.py`: Compute feature importance scores using Integrated Gradients (FR-005)
- [ ] T025 [US2] (Depends on T016) Implement `evaluate.py`: Save model checkpoints, validation metrics (macro-F1), and IG attribution maps to `data/reports/`
- [ ] T026 [US2] (Depends on T016) Add logging for training progress, validation scores, and augmentation stats in `code/train.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Motif Reporting (Priority: P3)

**Goal**: Receive a statistical report confirming that the identified structure-mechanism correlations are significant (via permutation test) and listing the top 3-5 structural motifs.

**Independent Test**: Can be fully tested by running the analysis script on the final model outputs and verifying the generated report contains a p-value from the permutation test and a ranked list of motifs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [US3] Unit test for permutation test logic (shuffling motifs) in `tests/unit/test_evaluate.py::test_permutation_test_shuffling`
- [ ] T028 [US3] Unit test for motif extraction and ranking logic in `tests/unit/test_evaluate.py::test_motif_extraction_ranking`
- [ ] T029 [US3] Integration test for full report generation pipeline in `tests/integration/test_reporting.py::test_full_report_generation`

### Implementation for User Story 3

- [ ] T030 [US3] (Depends on T025) Implement `evaluate.py`: Perform permutation test (shuffling input motifs 1000 times) to validate significance (FR-006)
- [ ] T031 [US3] (Depends on T025) Implement `evaluate.py`: Implement χ² Discretization Protocol (binning IG scores) to satisfy Constitution VI; implement Motif-Masking Permutation Test as primary validation for motif significance (FR-006)
- [ ] T032 [US3] (Depends on T025) Implement `evaluate.py`: Aggregate feature importances to identify top 3-5 structural motifs and their correlation with degradation types (FR-007)
- [ ] T033 [US3] (Depends on T025) Implement `evaluate.py`: Generate final report in `data/reports/` including p-values, motif list, and confidence flags (FR-007)
- [ ] T034 [US3] (Depends on T025) Add logic to flag predictions with confidence < 0.6 as "low confidence" in the report (US-3 Acceptance Scenario 3)
- [ ] T035 [US3] (Depends on T025) Add logging for statistical test results and report generation in `code/evaluate.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` (README, usage examples)
- [ ] T037 Code cleanup and refactoring of shared utilities in `code/utils.py`
- [ ] T038a [P] Implement memory monitoring utility in `code/utils.py`
- [ ] T038b [P] Integrate subsampling trigger in `code/preprocess.py` if memory > 7GB
- [ ] T039 [P] Additional unit tests for edge cases in `tests/unit/`: `test_invalid_smiles_raises`, `test_empty_dataset_raises`
- [ ] T040 Run `quickstart.md` validation to ensure end-to-end pipeline executes within 6 hours

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1 (T016)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model outputs from US2 (T025)

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
Task: "Unit test for SMILES validation and RDKit graph conversion in tests/unit/test_ingest.py::test_smiles_validation_rejects_invalid"
Task: "Unit test for missing data exclusion logic in tests/unit/test_preprocess.py::test_missing_env_excludes_record"

# Launch implementation tasks for User Story 1 together (if dependencies allow):
Task: "Implement ingest.py: Download records..."
Task: "Implement preprocess.py: Convert SMILES to molecular graphs..."
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
   - Developer A: User Story 1 (Data Pipeline)
   - Developer B: User Story 2 (Model Training) - *Wait for T016 output*
   - Developer C: User Story 3 (Validation) - *Wait for T025 output*
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
- **CRITICAL**: All data ingestion must use real URLs; no synthetic data generation allowed.
- **CRITICAL**: Records with missing environmental data (temp/pH/UV) MUST be flagged or imputed per Spec FR-002, then excluded from training per Plan constraints.
- **CRITICAL**: GNN must run on CPU only; no CUDA/GPU dependencies.
- **CRITICAL**: Bond rotation and atom masking MUST be implemented per Spec FR-004, with edge dropout as a supplement.
- **CRITICAL**: Permutation test (shuffling motifs) MUST be implemented per Spec FR-006.
- **CRITICAL**: χ² Discretization Protocol MUST be implemented to satisfy Constitution VI.