# Tasks: Predicting Molecular Reactivity Using Graph Neural Networks

**Input**: Design documents from `/specs/001-predict-molecular-reactivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. [UNRESOLVED-CLAIM: c_12047e55 — status=not_enough_info] Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. [UNRESOLVED-CLAIM: c_c6628f3b — status=not_enough_info]

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

- [ ] T001a [P] Create directory structure: `src/`, `tests/`
- [ ] T001b [P] Create directory structure: `data/`, `results/`, `models/`, `contracts/`
- [ ] T001c [P] Initialize Python 3.11 project with CPU-only dependencies (torch, torch-geometric, rdkit, scikit-learn, pandas, pyyaml) in `requirements.txt`
- [ ] T001d [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Create configuration manager in `src/config.py` (paths, seeds, hyperparameters)
- [ ] T003 [P] Implement logging infrastructure in `src/utils/logging.py`
- [~] T004 [P] Setup random seed pinning utility in `src/utils/seeding.py` (numpy, torch, python)
- [~] T005 Create data schema contracts in `contracts/data_schema.yaml` (MolecularGraph, ReactionDataset including reaction_class field)
- [ ] T006 Create model output schema in `contracts/prediction_result.schema.yaml`
- [ ] T007 Implement basic error handling wrapper in `src/utils/errors.py`
- [ ] T008 [P] Implement CPU memory optimization strategies (batch size tuning, gradient accumulation, memory-efficient data loaders) in `src/utils/performance.py` to ensure pipeline constraint

The research question, method, and references remain unchanged as no specific citation or methodological detail was provided in the source text to preserve.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest raw SMILES from USPTO-50k, parse into molecular graphs using RDKit, and extract features for CPU-based analysis.

**Independent Test**: Execute `src/data/ingestion.py` on a subset of the USPTO dataset; verify output is a valid PyG `Data` object with non-null features and >95% parsing success rate.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T009 [P] [US1] Unit test for SMILES parsing logic in `tests/unit/test_ingestion.py` (validates RDKit graph construction)
- [ ] T010 [P] [US1] Unit test for feature extraction in `tests/unit/test_preprocessing.py` (validates atomic/bond features)
- [ ] T011 [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py` (DEPENDS ON T005 stability; cannot run in parallel if schema is changing)

### Implementation for User Story 1

- [ ] T012 [US1] Implement SMILES ingestion script in `src/data/ingestion.py` (fetches from HuggingFace USPTO dataset, handles NaN yields, extracts and validates reaction_class labels)
- [ ] T013 [US1] Implement RDKit graph construction and validation in `src/data/ingestion.py` (handles stereochemistry errors, logs failures)
- [ ] T014 [US1] Implement feature extraction (atomic number, charge, hybridization, bond type) in `src/data/preprocessing.py`
- [ ] T015 [US1] Implement PyG `Data` object conversion and saving to `data/processed/` in `src/data/loaders.py`
- [ ] T016 [US1] Add success rate logging and error reporting to `results/ingestion_report.json`, explicitly capturing the specific error reason string for each failed parse
- [ ] T017 [US1] Implement success rate calculation and threshold assertion in `src/data/validation.py` (calculates rate from logs, fails build if <95%, reports metric)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline and GNN Model Training (Priority: P2)

**Goal**: Train a lightweight MPNN and a Random Forest baseline on the constructed dataset within 4 hours on CPU.

**Independent Test**: Run -fold CV training loop; verify both models converge, produce valid predictions across the full probability spectrum, and complete within time limits.

### Tests for User Story 2

- [ ] T018 [P] [US2] Unit test for MPNN architecture in `tests/unit/test_mpnn.py` (validates forward pass on dummy data)
- [ ] T019 [P] [US2] Unit test for Random Forest baseline in `tests/unit/test_baseline.py` (validates Morgan fingerprint generation)
- [ ] T020 [P] [US2] Integration test for 5-fold CV loop in `tests/integration/test_training.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement Message Passing Neural Network (MPNN) in `src/models/mpnn.py` (CPU-optimized, no CUDA, early stopping)
- [ ] T022 [P] [US2] Implement Random Forest baseline using Morgan fingerprints in `src/models/baseline.py`
- [ ] T023 [US2] Implement 5-fold cross-validation training loop in `src/training/trainer.py` (handles data splitting, model training, checkpointing, and aggregation of fold-level metrics to calculate mean R² and standard deviation)
- [ ] T024 [US2] Implement metrics calculation (R², MAE, RMSE) in `src/training/utils.py`
- [ ] T025 [P] [US2] Integrate conformal prediction wrapper for MPNN model in `src/models/conformal.py` (applies to MPNN predictions only)
- [ ] T026 [P] [US2] Integrate conformal prediction wrapper for Random Forest baseline in `src/models/conformal.py` (applies to RF predictions only)
- [ ] T027 [US2] Validate conformal prediction calibration for both models in `src/analysis/conformal_validation.py` (checks coverage rate, generates calibration report in `results/conformal_metrics.json`)
- [ ] T028 [US2] Generate final model checkpoints and metrics report in `results/metrics.json`, explicitly logging the standard deviation of R² scores across folds

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison and Sensitivity Analysis (Priority: P3)

**Goal**: Compare GNN vs. Baseline, perform sensitivity analysis on noise tolerance, and run GNNExplainer for attribution.

**Independent Test**: Run analysis script; verify report includes R² comparison, MAE sensitivity sweep, and ranked subgraph features.

### Tests for User Story 3

- [ ] T029 [P] [US3] Unit test for statistical comparison logic in `tests/unit/test_comparison.py`
- [ ] T030 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`
- [ ] T031 [P] [US3] Integration test for attribution analysis in `tests/integration/test_attribution.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement statistical comparison module in `src/analysis/comparison.py` (calculates relative error reduction, significance)
- [ ] T033 [US3] Implement sensitivity analysis (noise tolerance sweep) in `src/analysis/sensitivity.py` (sweeps values across a range including zero, reports MAE variation)
- [ ] T034 [US3] Implement GNNExplainer attribution analysis in `src/analysis/attribution.py` (identifies top subgraph patterns)
- [ ] T035 [US3] Generate final analysis report in `results/analysis_report.json` and `results/sensitivity.csv`
- [ ] T036 [US3] Create visualization script for subgraph attribution in `src/analysis/visualize.py` (optional, for human review)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates: `README.md`, `quickstart.md`, and `research.md`
- [ ] T038 Code cleanup and refactoring
- [ ] T039 [P] Run full pipeline end-to-end integration test in `tests/integration/test_pipeline.py`
- [ ] T040 Validate `quickstart.md` instructions work on a fresh environment
- [ ] T041 Verify all `results/` artifacts match schema contracts

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 model outputs

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
Task: "Unit test for SMILES parsing logic in tests/unit/test_ingestion.py"
Task: "Unit test for feature extraction in tests/unit/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement RDKit graph construction in src/data/ingestion.py"
Task: "Implement feature extraction in src/data/preprocessing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (valid graph dataset generated)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Model training complete)
4. Add User Story 3 → Test independently → Deploy/Demo (Analysis complete)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Models)
 - Developer C: User Story 3 (Analysis)
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
- **CPU Constraint**: All tasks must be executable on a multi-core CPU with moderate memory capacity, no GPU. Avoid 8-bit quantization or large models.
- **Data Integrity**: Use real USPTO dataset from HuggingFace; no synthetic data generation.