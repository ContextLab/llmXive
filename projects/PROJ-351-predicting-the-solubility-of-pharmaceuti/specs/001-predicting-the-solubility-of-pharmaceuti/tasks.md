# Tasks: Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

**Input**: Design documents from `/specs/001-predict-solubility-gnn/`
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

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `models/`, `results/`, `tests/`)
- [X] T002 Initialize Python 3.10 project with `requirements.txt` (pinning `rdkit`, `torch` CPU, `torch-geometric` CPU, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `scipy`)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/data/download_esol.py` to fetch ESOL dataset from MoleculeNet/HuggingFace URL, validate `logS` column, and save raw CSV to `data/raw/`
- [X] T005 [P] Implement `code/data/preprocess.py` to load raw CSV, parse SMILES with RDKit, exclude invalid SMILES/NaN `logS` *before* split, extract atom/bond features, and save cleaned graphs to `data/processed/`
- [X] T006 [P] Implement `code/data/split.py` to perform a stratified train/validation/test split on cleaned data using quantile binning on `logS` and save indices to `data/processed/`
- [X] T007 Create base data models/entities (`Molecule`, `DatasetSplit`) in `code/__init__.py` or `code/models.py`
- [ ] T008 Configure logging infrastructure to capture exclusion counts and training metrics to `data/logs/`
- [ ] T009 Setup environment configuration management for random seeds (pinned in `code/`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline and Baseline Establishment (Priority: P1) 🎯 MVP

**Goal**: Download ESOL, clean invalid SMILES, preprocess to graphs, and train Random Forest baseline to establish a performance floor.

**Independent Test**: The pipeline can be fully tested by running the data download, cleaning, preprocessing, and Random Forest training script, verifying that a model is saved and metrics are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for SMILES validation logic in `tests/unit/test_preprocess.py`
- [ ] T011 [P] [US1] Unit test for quantile binning split logic in `tests/unit/test_split.py`
- [ ] T012 [P] [US1] Integration test for full RF baseline pipeline in `tests/integration/test_baseline_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement Random Forest baseline training in `code/models/baseline_rf.py` using Morgan fingerprints (radius=2, 2048 bits)
- [ ] T014 [US1] Implement `code/training/train_baseline.py` to train RF on training set, evaluate on test set, and save model to `models/`
- [ ] T015 [US1] Implement logging of R-squared and RMSE to `results/baseline_metrics.json` within 10 minutes of CPU time
- [~] T016 [US1] Add error handling for RDKit parsing failures (log invalid count, exclude from dataset)
- [~] T017 [US1] Add logging for baseline training operations and exclusion counts

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Model Training and Evaluation (Priority: P2)

**Goal**: Implement and train a Message Passing Neural Network (MPNN) configured strictly for CPU execution and evaluate against the Random Forest baseline.

**Independent Test**: The GNN training script can be run independently (assuming data exists), and the resulting model must produce a test set RMSE that is recorded and compared to the baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for MPNN architecture (CPU-only verification) in `tests/unit/test_gnn_arch.py`
- [ ] T019 [P] [US2] Integration test for GNN training loop with early stopping in `tests/integration/test_gnn_training.py` <!-- ATOMIZE: requested -->

### Implementation for User Story 2

- [X] T020 [US2] Implement Message Passing Neural Network (MPNN) in `code/models/gnn_mpnn.py` using PyTorch Geometric, ensuring NO CUDA/GPU calls
- [X] T021 [US2] Implement `code/training/train_gnn.py` to train MPNN with early stopping on validation loss
- [~] T022 [US2] Ensure GNN training completes within 6 hours on 2-core CPU runner (simplify architecture if needed: fewer layers, smaller hidden dims)
- [X] T023 [US2] Implement evaluation script in `code/evaluation/metrics.py` to calculate RMSE and R-squared for GNN on test set
- [ ] T024 [US2] Save GNN predictions and metrics to `results/gnn_metrics.json`
- [~] T025 [US2] Implement comparison logic to calculate RMSE delta between Baseline and GNN without arbitrary pass/fail flags

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Interpretability (Priority: P3)

**Goal**: Perform paired t-test on prediction errors, calculate statistical power, and generate feature importance visualizations.

**Independent Test**: The analysis script takes the prediction files from US-1 and US-2, runs the t-test and power analysis, and generates a plot or table of feature importance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for paired t-test and power analysis logic in `tests/unit/test_stats.py`
- [X] T027 [P] [US3] Unit test for visualization generation (non-zero variance, >1KB) in `tests/unit/test_viz.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `code/evaluation/statistical_test.py` to perform paired t-test on absolute errors of RF and GNN (alpha=0.05) and calculate post-hoc power
- [X] T029 [US3] Implement `code/evaluation/interpretability.py` to generate attention heatmaps or node importance rankings for sample molecules
- [~] T030 [US3] Ensure visualizations are saved as PNG files with non-zero variance and size > 1KB to `results/`
- [X] T031 [US3] Implement `code/evaluation/report_generator.py` to compile RMSE, R², p-value, power, and delta into a final summary table
- [~] T032 [US3] Add logic to detect and report "ceiling effect" if Baseline R² > 0.95

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T033 [P] Documentation updates in `docs/` and `README.md`
- [~] T034 Code cleanup and refactoring across `code/` <!-- ATOMIZE: requested -->
- [~] T035 Performance optimization for GNN training loop (CPU efficiency)
- [~] T036 [P] Additional unit tests for edge cases (malformed SMILES, non-convergent GNN) in `tests/unit/`
- [~] T037 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Relies on data pipeline from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Relies on results from US1 and US2

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
Task: "Unit test for SMILES validation logic in tests/unit/test_preprocess.py"
Task: "Unit test for quantile binning split logic in tests/unit/test_split.py"

# Launch all models for User Story 1 together:
Task: "Implement Random Forest baseline training in code/models/baseline_rf.py"
Task: "Implement logging of R-squared and RMSE to results/baseline_metrics.json"
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
 - Developer A: User Story 1 (Data + RF)
 - Developer B: User Story 2 (GNN)
 - Developer C: User Story 3 (Stats + Viz)
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
- **Constraint**: All GNN tasks must run on CPU-only; no CUDA/GPU calls allowed.
- **Constraint**: All tasks must complete within 6 hours on 2 vCPU.
- **Constraint**: No synthetic data; use real ESOL dataset from canonical source.
