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

- [X] T001 Create project structure per implementation plan by executing: `mkdir -p projects/PROJ-404-predicting-molecular-surface-charge-dist/{code/{data,models,utils},tests,reports,data/{raw,processed}}` and creating `__init__.py` files in all `code/` subdirectories, then verifying all directories exist and contain `__init__.py`.

- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`: `torch==2.1.0`, `torch-geometric==2.4.0`, `rdkit==2023.9.1`, `datasets==2.14.0`, `pandas==2.1.0`, `numpy==1.24.0`, `scikit-learn==1.3.0`.

- [X] T003 [P] Configure linting and formatting by creating `code/pyproject.toml` with `[tool.ruff]` (line-length=100) and `[tool.black]` (line-length=100) sections.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement seed setting and logging utility in `code/utils.py`: Define `def set_seed(seed: int) -> None` using `random`, `numpy`, and `torch` seeds; define `def get_logger(name: str) -> logging.Logger` with format `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`.

- [X] T005 [P] Create base data model classes in `code/data/dataset.py`: Define `class MoleculeData(torch_geometric.data.Data)` with attributes `x` (atomic numbers), `pos` (coordinates), `y` (charges), and `scaffold_id` to satisfy FR-001 data model requirements.

- [X] T006 [P] Setup memory profiling and adaptive sampling logic in `code/data/loader.py`: Implement streaming wrapper around HuggingFace dataset.

- [X] T006a [P] Orchestrate runtime probe-calculate-adapt sequence in `code/data/loader.py`: Define `def adaptive_sample_size(batch_size: int, target_gb: float) -> int` that returns `max_samples` based on measured per-molecule overhead and a predefined memory limit.

- [X] T007 [P] Implement coordinate normalization (center of mass) in `code/data/preprocess.py`: Define function to shift coordinates such that `mean(pos) == 0` for each molecule, satisfying FR-001.

- [X] T008 [P] Implement Bemis-Murcko scaffold extraction and splitting logic in `code/data/preprocess.py`: Use `rdkit.Chem.Scaffolds.MurckoScaffold.GetScaffoldForMol` to generate scaffold strings and group molecules, satisfying FR-004.

- [X] T009 [P] Apply Bemis-Murcko split logic from T008 to generate train/val/test index streams for the loader in `code/data/preprocess.py`: Use a fixed random seed of 42 and stratify by scaffold string; write the indices to `data/processed/splits.json`, satisfying FR-004.

- [X] T009a [P] Execute scaffold split: Implement function in `code/data/preprocess.py` that consumes split indices from T009 and filters the `MoleculeData` stream for train/val/test sets, returning filtered iterators; explicitly write split indices to `data/processed/splits.json` and record checksums for reproducibility.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Construction and Validation (Priority: P1) 🎯 MVP

**Goal**: Ingest QM9 subset with Merz-Kollman charges, validate memory constraints, and ensure data integrity.

**Independent Test**: The system can be fully tested by executing the data loading script on the free-tier runner, confirming the dataset loads into memory without OOM errors, and verifying that the extracted features match the expected schema.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for memory profiling logic in `tests/test_loader.py`: Implement `test_adaptive_sample_size_returns_correct_limit` and assert `max_samples > 0` based on measured overhead.

- [X] T011 [P] [US1] Integration test for full data loading and schema validation in `tests/test_loader.py`: Implement `test_full_load_schema_validation` and assert `'charge' in batch.y` and schema fields match expected types.

### Implementation for User Story 1

- [X] T012 [US1] Implement HuggingFace dataset loader with `streaming=True` for QM (Merz-Kollman subset) in `code/data/loader.py`, consuming split indices from T009a; verify the existence of Merz-Kollman charges before proceeding.

- [X] T013 [US1] Implement "Fail Loudly" logic: raise explicit `RuntimeError` if real data fetch fails, NO synthetic fallback in `code/data/loader.py`.

- [X] T014 [US1] Implement dynamic memory calculation to determine `max_samples` based on a predefined memory limit in `code/data/loader.py` (reusing T006a logic).

- [X] T015 [US1] Implement data validation checks (non-null charges, connectivity alignment) AND specific filtering/imputation strategy for missing coordinates or undefined bonds in `code/data/loader.py` (filter molecule if undefined bonds; impute coordinates with mean if missing); assert schema validity; output a summary of loaded feature dimensions to the console.

- [X] T016 [US1] Add logging for loaded feature dimensions and memory usage in `code/data/loader.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Geometric Graph Neural Network Training (Priority: P2)

**Goal**: Implement and train a Geometric GNN (SchNet/DimeNet) on CPU, respecting time and memory limits.

**Independent Test**: The system can be tested by running the training script for a fixed number of epochs and verifying that the loss decreases, the model weights are saved, and the process completes within a reasonable wall-clock time limit.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for SchNet/DimeNet architecture initialization in `tests/test_model.py`: Implement `test_schnet_init` and assert `model.num_parameters > 0`.

- [X] T019 [P] [US2] Integration test for training loop completion and early stopping in `tests/test_model.py`: Implement `test_training_loop_completion` and assert `final_loss < initial_loss` after 10 epochs.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement Geometric GNN (SchNet or DimeNet) architecture class in `code/models/schnet.py` inheriting from `torch.nn.Module`.

- [X] T020a [P] [US2] Configure model hyperparameters in `code/models/config.yaml`: Set `num_filters=128`, `num_gaussians=50`, `num_interaction_blocks=3`.

- [X] T021 [US2] Implement connectivity-only GNN (2D) baseline architecture in `code/models/baseline_2d.py` (ignores `pos` attribute), satisfying FR-006.

- [X] T022 [US2] Implement Atom-Type Average baseline logic in `code/models/baseline_atom.py` (returns mean charge per atomic number).

- [X] T023a [US2] Construct validation data loader in `code/train.py`: Wrap the validation split from T009a into a `DataLoader` for early stopping.

- [X] T023 [US2] Implement training loop with Adam optimizer (lr=1e-3), max 100 epochs in `code/train.py`: Must accept train and validation loaders, satisfying FR-003.

- [X] T023b [US2] Implement early stopping logic based on validation MAE (patience=10) in `code/train.py`.

- [X] T023c [US2] Wire split indices: Ensure `code/train.py` explicitly loads the train/val splits generated by T009a before calling the training loop.

- [X] T024 [US2] Implement model checkpointing (save state dict < 500 MB) in `code/train.py`, satisfying FR-003.

- [X] T026 [US2] Add logging for epoch loss and validation MAE in `code/train.py`, satisfying FR-003.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluation and Baseline Comparison (Priority: P3)

**Goal**: Evaluate models against test set, compare 3D GNN vs 2D GNN vs Atom-Type baseline, and validate hypothesis.

**Independent Test**: The system can be tested by loading the trained model and test set, running inference, and generating a report containing MAE, RMSE, and $R$ values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T040 [P] [US3] Unit test for metric calculation (MAE, RMSE, Pearson R) in `tests/test_eval.py`: Implement `test_mae_rmse_pearson_known_values` with known input/output pairs.

- [X] T041 [P] [US3] Integration test for full evaluation pipeline and baseline comparison in `tests/test_eval.py`: Implement `test_full_evaluation_pipeline` and assert expected report file path and metrics.

### Implementation for User Story 3

- [X] T042 [US3] Implement evaluation script to calculate MAE, RMSE, and Pearson R in `code/eval.py`, satisfying FR-005.

- [X] T043 [US3] Implement baseline comparison logic (3D GNN vs 2D GNN vs Atom-Type) in `code/eval.py`, satisfying FR-006.

- [X] T044 [US3] Implement hypothesis validation check: Calculate 3D GNN test MAE in `code/eval.py` function `validate_hypothesis`; if MAE > 0.05 e, raise `AssertionError` with message "Hypothesis failed: MAE > 0.05 e" and log result, satisfying FR-007.

- [X] T045 [US3] Calculate and report MAE deltas between test/validation and training/validation sets for generalization error detection in `code/eval.py` function `calculate_generalization_deltas`, satisfying SC-006/SC-007.

- [X] T046 [US3] Implement exit code logic: If 3D GNN MAE > 0.05 e (from T044) OR if 3D GNN MAE > 2D GNN MAE, exit with `sys.exit(EXIT_CODE_BASELINE_LOSS)` (non-zero), satisfying FR-006.

- [X] T047 [US3] Aggregate metrics into JSON/CSV in `code/eval.py` to `reports/metrics.json`, satisfying FR-005.

- [X] T048 [US3] Render final report `reports/results.md` from aggregated data in `code/eval.py`, satisfying Constitution Principle IV.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034a [P] Generate Google-style docstrings for all classes and functions in `code/` directory using `pydocstyle --count --select=D` and verify 0 errors, satisfying Constitution Principle IV.

- [X] T035a Refactor `code/data/loader.py` to ensure streaming logic is efficient and handles chunking correctly by extracting `ChunkedIterator` class and verifying memory profile < 7GB, satisfying Constitution Principle III.

- [X] T036a Run benchmark script `python code/data/loader.py --benchmark` and verify load time < 10 minutes, recording result in `reports/load_time.log`, satisfying Constitution Principle VI.

- [X] T037 [P] Additional unit tests for edge cases (missing coordinates, undefined bonds) in `tests/`: Implement `test_missing_coordinates_imputation` and `test_undefined_bond_filtering` with specific assertions, satisfying Constitution Principle V.

- [X] T038 Run quickstart.md validation by executing `python code/quickstart.py --validate` and verifying exit code 0, satisfying Constitution Principle I.

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
- Different user stories can be worked on in parallel by different team members

---

## Memory Feasibility Strategy

The plan implements a **Dynamic Memory Profiling** strategy to guarantee feasibility:
1. **Probe**: The loader first streams a small batch of molecules to measure per-molecule RAM overhead.
2. **Calculate**: It computes `max_samples = (Target_RAM_GB * 1024^3) / per_molecule_bytes`.
3. **Adapt**: The final sample size is set to a computationally feasible upper bound determined by the calculated maximum. If `calculated_max < 10000`, a warning is logged, but the run proceeds to ensure the pipeline completes.
4. **Stream**: The dataset is loaded using `streaming=True` and iterated in batches, ensuring peak memory never exceeds the calculated limit.

This approach replaces the static "50k molecule" assumption with a runtime-safe calculation.