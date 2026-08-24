# Tasks: Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations

**Input**: Design documents from `/specs/001-predicting-molecular-surface-charge/`
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
  
  Tasks MUST be organized by user story so each story can:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan by executing: `mkdir -p projects/PROJ-404-predicting-molecular-surface-charge-dist/{code/{data,models,utils},tests,reports,data/{raw,processed}}` and creating empty `__init__.py` files in all `code/` subdirectories.
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`: `torch==2.1.0`, `torch-geometric==2.4.0`, `rdkit==2023.9.1`, `datasets==2.14.0`, `pandas==2.1.0`, `numpy==1.24.0`, `scikit-learn==1.3.0`.
- [ ] T003 [P] Configure linting and formatting by creating `code/pyproject.toml` with `[tool.ruff]` (line-length=100) and `[tool.black]` (line-length=100) sections.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement seed setting and logging utility in `code/utils.py`: Define `def set_seed(seed: int) -> None` using `random`, `numpy`, and `torch` seeds; define `def get_logger(name: str) -> logging.Logger` with format `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`.
- [ ] T005 [P] Create base data model classes in `code/data/dataset.py`: Define `class MoleculeData(torch_geometric.data.Data)` with attributes `x` (atomic numbers), `pos` (coordinates), `y` (charges), and `scaffold_id`.
- [ ] T006 [P] Setup memory profiling and adaptive sampling logic in `code/data/loader.py`: Implement streaming wrapper around HuggingFace dataset.
- [ ] T006a [P] Orchestrate runtime probe-calculate-adapt sequence in `code/data/loader.py`: Define `def adaptive_sample_size(batch_size: int, target_gb: float) -> int` that returns `max_samples` based on measured per-molecule overhead and a predefined memory limit.
- [ ] T007 Implement coordinate normalization (center of mass) in `code/data/preprocess.py`: Define function to shift coordinates such that `mean(pos) == 0` for each molecule.
- [ ] T008 [P] Implement Bemis-Murcko scaffold extraction and splitting logic in `code/data/preprocess.py`: Use `rdkit.Chem.Scaffolds.MurckoScaffold.GetScaffoldForMol` to generate scaffold strings and group molecules.
- [ ] T009 [P] Apply Bemis-Murcko split logic from T008 to generate train/val/test index streams for the loader in `code/data/preprocess.py`: Use a fixed random seed and stratify by scaffold string.
- [ ] T009a [P] Execute scaffold split: Implement function in `code/data/preprocess.py` that consumes split indices from T009 and filters the `MoleculeData` stream for train/val/test sets, returning filtered iterators.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Construction and Validation (Priority: P1) 🎯 MVP

**Goal**: Ingest QM9 subset with Merz-Kollman charges, validate memory constraints, and ensure data integrity.

**Independent Test**: The system can be fully tested by executing the data loading script on the free-tier runner, confirming the dataset loads into memory without OOM errors, and verifying that the extracted features match the expected schema.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for memory profiling logic in `tests/test_loader.py`
- [ ] T011 [P] [US1] Integration test for full data loading and schema validation in `tests/test_loader.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement HuggingFace dataset loader with `streaming=True` for QM (Merz-Kollman subset) in `code/data/loader.py`, consuming split indices from T009a.
- [ ] T013 [US1] Implement "Fail Loudly" logic: raise explicit `RuntimeError` if real data fetch fails, NO synthetic fallback in `code/data/loader.py`.
- [ ] T014 [US1] Implement dynamic memory calculation to determine `max_samples` based on a predefined memory limit in `code/data/loader.py` (reusing T006a logic).
- [ ] T015 [US1] Implement data validation checks (non-null charges, connectivity alignment) AND specific filtering/imputation strategy for missing coordinates or undefined bonds in `code/data/loader.py` (filter molecule if undefined bonds; impute coordinates with mean if missing).
- [ ] T016 [US1] Add logging for loaded feature dimensions and memory usage in `code/data/loader.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Geometric Graph Neural Network Training (Priority: P2)

**Goal**: Implement and train a Geometric GNN (SchNet/DimeNet) on CPU, respecting time and memory limits.

**Independent Test**: The system can be tested by running the training script for a fixed number of epochs and verifying that the loss decreases, the model weights are saved, and the process completes within a reasonable wall-clock time limit.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for SchNet/DimeNet architecture initialization in `tests/test_model.py`
- [ ] T019 [P] [US2] Integration test for training loop completion and early stopping in `tests/test_model.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement Geometric GNN (SchNet or DimeNet) architecture class in `code/models/schnet.py` inheriting from `torch.nn.Module`.
- [ ] T020a [P] [US2] Configure model hyperparameters in `code/models/config.yaml`: Set `num_filters=128`, `num_gaussians=50`, `num_interaction_blocks=3`.
- [ ] T021 [US2] Implement connectivity-only GNN (2D) baseline architecture in `code/models/baseline_2d.py` (ignores `pos` attribute).
- [ ] T022 [US2] Implement Atom-Type Average baseline logic in `code/models/baseline_atom.py` (returns mean charge per atomic number).
- [ ] T023a [US2] Construct validation data loader in `code/train.py`: Wrap the validation split from T009a into a `DataLoader` for early stopping.
- [ ] T023 [US2] Implement training loop with Adam optimizer (lr=1e-3), max 100 epochs in `code/train.py`: Must accept train and validation loaders.
- [ ] T023b [US2] Implement early stopping logic based on validation MAE (patience=10) in `code/train.py`.
- [ ] T023c [US2] Wire split indices: Ensure `code/train.py` explicitly loads the train/val splits generated by T009a before calling the training loop.
- [ ] T024 [US2] Implement model checkpointing (save state dict < 500 MB) in `code/train.py`.
- [ ] T026 [US2] Add logging for epoch loss and validation MAE in `code/train.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluation and Baseline Comparison (Priority: P3)

**Goal**: Evaluate models against test set, compare 3D GNN vs 2D GNN vs Atom-Type baseline, and validate hypothesis.

**Independent Test**: The system can be tested by loading the trained model and test set, running inference, and generating a report containing MAE, RMSE, and $R$ values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T040 [P] [US3] Unit test for metric calculation (MAE, RMSE, Pearson R) in `tests/test_eval.py`
- [ ] T041 [P] [US3] Integration test for full evaluation pipeline and baseline comparison in `tests/test_eval.py`

### Implementation for User Story 3

- [ ] T042 [P] [US3] Implement evaluation script to calculate MAE, RMSE, and Pearson R in `code/eval.py`.
- [ ] T043 [US3] Implement baseline comparison logic (3D GNN vs 2D GNN vs Atom-Type) in `code/eval.py`.
- [ ] T044 [US3] Implement hypothesis validation check: Calculate 3D GNN test MAE; if MAE > 0.05 e, raise `AssertionError` with message "Hypothesis failed: MAE > 0.05 e" and log result.
- [ ] T045 [US3] Calculate and report MAE deltas between test/validation and training/validation sets for generalization error detection in `code/eval.py`.
- [ ] T046 [US3] Implement exit code logic: If 3D GNN MAE > 0.05 e (from T044) OR if 3D GNN MAE > 2D GNN MAE, exit with `EXIT_CODE_BASELINE_LOSS` (non-zero).
- [ ] T047 [US3] Aggregate metrics into JSON/CSV in `code/eval.py`.
- [ ] T048 [US3] Render final report `reports/results.md` from aggregated data in `code/eval.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034a [P] Generate Google-style docstrings for all classes and functions in `code/` directory.
- [ ] T035a Refactor `code/data/loader.py` to ensure streaming logic is efficient and handles chunking correctly.
- [ ] T036a Verify load time < 10 minutes by running `code/data/loader.py` with timing instrumentation and logging the result.
- [ ] T037 [P] Additional unit tests for edge cases (missing coordinates, undefined bonds) in `tests/`.
- [ ] T038 Run quickstart.md validation by executing `python code/quickstart.py` and verifying exit code 0.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Unit test for memory profiling logic in tests/test_loader.py"
Task: "Integration test for full data loading and schema validation in tests/test_loader.py"

# Launch all models for User Story 1 together:
Task: "Implement HuggingFace dataset loader with streaming=True for QM9 in code/data/loader.py"
Task: "Implement 'Fail Loudly' logic: raise explicit error if real data fetch fails in code/data/loader.py"
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
- **Removed T013a**: Secondary DFT calculation fallback removed as it violates CPU-only/No-API constraints and lacks a defined engine.
- **Removed T025a/b/c**: Coordinate Randomization ablation removed as it is scope creep not authorized by spec.md.
- **Removed T049/050**: Power Analysis removed as it is not in spec.md FR/SC.