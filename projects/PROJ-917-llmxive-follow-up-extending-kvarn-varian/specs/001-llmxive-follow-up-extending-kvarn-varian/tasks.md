# Tasks: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-kvarn-varian/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [ ] T001a Create `code/` directory structure (`data_generation`, `model_training`, `simulation`, `analysis`, `tests/`)
- [ ] T001b Create `data/` directory structure (`generated`, `models`, `simulation`, `analysis`) with checksumming logic for immutable raw data. **Deliverable**: A script or function that computes and stores checksums for all files in `data/`.
- [ ] T001c Create `tests/` directory structure (`test_data_generation`, `test_model_training`, `test_simulation`)
- [X] T002 Initialize Python 3.11 project [UNRESOLVED-CLAIM: c_94fa67d9 — status=not_enough_info] with pinned `requirements.txt` (numpy, scipy, torch-cpu, scikit-learn, pandas, pyarrow, pytest, matplotlib)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T005 [P] Implement numerical stability utilities (epsilon floor handling) in `code/data_generation/utils.py`. **Deliverable**: A function `apply_epsilon_floor(value: float, epsilon: float) -> float` that returns `max(value, epsilon)`.
- [X] T005b [P] Implement `epsilon_utils` in `code/data_generation/utils.py` specifically for the sensitivity analysis utility functions. **Deliverable**: A function `generate_epsilon_sweep_values(start: float, end: float, steps: int) -> List[float]`.
- [X] T006 [P] Implement `SimulationState` dataclass in `code/simulation/state.py` with fields: `accumulated_kl: float`, `current_error_state: dict`, `step_index: int`. This module MUST be imported by T027.
- [ ] T007 [P] Create base entities: `AttentionTrajectory` (sequence of steps), `ScalingFactor`, `SimulationRun` in `code/entities.py`. `AttentionTrajectory` MUST store a list of 128x128 matrices and their temporal moments (mean, var) per step.
- [X] T008 [P] [US1] Implement global random seed management in `code/utils/seeds.py` with a `set_global_seed(seed: int)` function that calls `np.random.seed`, `torch.manual_seed`, and `random.seed`. **Verification**: Run `main.py` twice with the same seed and check output checksums match.
- [X] T009 [P] [US1] Setup environment configuration management in `code/config.py` with a `Config` dataclass containing `CPU_ONLY=True`, `EPSILON_FLOOR=1e-6`, and `RANDOM_SEED`. **Verification**: Load `config.py` and assert defaults.
- [X] T010 [P] [US1] Implement unit test for moment extraction and epsilon handling in `tests/test_data_generation.py`. **Deliverable**: A test file that verifies `apply_epsilon_floor` and moment extraction logic.
- [X] T011 [P] [US1] Implement unit test for Sequential Sinkhorn solver convergence and state update in `tests/test_data_generation.py`. **Deliverable**: A test file that verifies `SequentialSinkhornSolver` state transitions.
- [ ] T012 [P] [US2] Implement unit test for MLP architecture definition in `tests/test_model_training.py`.
- [ ] T013 [P] [US2] Implement unit test for closed-form baseline (s = 1/variance) implementation in `tests/test_model_training.py`.
- [ ] T014 [P] [US3] Implement integration test for full simulation loop (static prior vs. sinkhorn) in `tests/test_simulation.py`.
- [ ] T015 [P] [US3] Implement unit test for KL-divergence calculation and accumulation logic in `tests/test_simulation.py`.
- [ ] T032 [P] [US3] Implement theoretical lower bound calculation using an analytical noise model proportional to the square of the quantization interval. in `code/analysis/stats.py`. Output: `data/analysis/theoretical_lower_bound.json`. (Dependency for US3 validation)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.1: Foundational Prerequisites (Strict Sequence)

**Purpose**: Tasks that must strictly precede specific user story implementations to avoid race conditions.

- [ ] T017a [P] [US1] Implement the specific `DriftModel` class in `code/data_generation/utils.py` that generates temporal evolution parameters for mean and variance. **Constraint**: Must be implemented before T017b.

---

## Phase 3: User Story 1 - Generate Ground-Truth Scaling Factors for Synthetic Attention Trajectories (Priority: P1) 🎯 MVP

**Goal**: Generate a configurable number of synthetic attention trajectories with temporal drift and compute ground-truth scaling factors using a Sequential Sinkhorn Optimizer.

**Independent Test**: Can be fully tested by running the data generation script on a small subset and verifying that the output file contains valid scaling factors, that the distribution matches drift parameters, and that computation time per matrix matches the expected overhead of the Sequential Sinkhorn solver.

### Implementation for User Story 1

- [ ] T017b [US1] Implement synthetic trajectory generator with controlled sparsity, outliers, and **temporal drift** in `code/data_generation/synthetic_attention.py`. **Output**: `data/generated/trajectories.parquet`. **Schema**: List of steps per trajectory; each step must include `mean`, `var`, `scaling_factor`. **Requirement**: Must implement `DriftModel` logic (e.g., random walk or sinusoidal drift) that evolves mean and var over steps; must ensure the output is a sequence of steps, not i.i.d. matrices. (Dependency: T017a)
- [ ] T017c [US1] Implement ground-truth label computation logic linking trajectory steps to optimal scaling factors in `code/data_generation/synthetic_attention.py`. **Requirement**: Must use the `SequentialSinkhornSolver` from T016.
- [ ] T019 [US1] Implement data serialization (Parquet/JSON) with checksums for generated dataset in `code/data_generation/utils.py`
- [ ] T020 [US1] Add validation checks for near-zero variance handling and NaN flagging in `code/data_generation/synthetic_attention.py`
- [ ] T021 [US1] Add logging for data generation progress and solver failures in `code/data_generation/utils.py`
- [ ] T016 [P] [US1] Implement `SequentialSinkhornSolver` class in `code/simulation/sequential_sinkhorn.py`. **Signature**: `solve_step(matrix, prev_state: SimulationState) -> (scaling_factor, new_state: SimulationState)`. **Requirement**: Must maintain cumulative error state across steps; must accept and return a `SimulationState` object.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (N trajectories + ground truth labels generated)

---

## Phase 4: User Story 2 - Train and Evaluate the Static Prior Model (Priority: P2)

**Goal**: Train a lightweight MLP on CPU to map input attention moments (mean, var) to ground-truth scaling factors, and evaluate against a closed-form baseline.

**Independent Test**: Can be fully tested by training the model on the training split and reporting the Mean Squared Error (MSE) on the test split. If the MSE is below a specific threshold, the mapping is considered learnable.

### Implementation for User Story 2

- [ ] T022 [P] [US2] Define a multi-layer perceptron (MLP) model architecture (2 inputs: mean, var) in `code/model_training/mlp_model.py`
- [ ] T023 [US2] Implement training loop with MSE loss, CPU-only execution, and epoch logging in `code/model_training/train.py`. **Output**: `data/models/mlp_weights.pt`, `data/metrics/training_log.csv`.
- [ ] T024 [US2] Implement closed-form baseline predictor (s = 1/variance) in `code/model_training/baselines.py`
- [ ] T025 [US3] Implement sensitivity analysis logic for epsilon floor sweep in `code/analysis/stats.py` (Validates normalization logic for US2/US3). **Input**: Configured epsilon values (from T005b) and simulation results. **Output**: `data/analysis/epsilon_sensitivity.json`. **Dependency**: T005b, T030b.
- [ ] T026 [US2] Save trained model weights and training metrics to `data/` artifacts in `code/model_training/train.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Model trained and baseline comparison ready)

---

## Phase 5: User Story 3 - Simulate Long-Horizon Generation and Measure Latency/Accuracy Trade-off (Priority: P3)

**Goal**: Run a simulated autoregressive generation loop replacing the KVarN optimizer with the trained static prior, measuring accumulated KL-divergence and per-token latency.

**Independent Test**: Can be fully tested by running the simulation loop twice (once with KVarN optimizer, once with static prior) and comparing the final accumulated KL-divergence and average wall-clock time per token.

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement autoregressive simulation engine with cumulative error state propagation in `code/simulation/autoregressive_loop.py`. **Default**: 1000 steps. **Input**: `SimulationState` from T006. **Output**: `data/simulation/run_001_results.json`.
- [ ] T028 [US3] Implement KL-divergence accumulation logic comparing quantized vs. full-precision distributions in `code/simulation/kl_divergence.py`
- [ ] T029 [US3] Implement wall-clock profiling for both static prior and Sequential Sinkhorn methods in `code/simulation/profiler.py`. **Requirement**: Must explicitly subtract baseline inference time to isolate the optimization overhead cost.
- [ ] T030a [P] [US3] Implement `code/simulation/batch_runner.py` to execute multiple independent simulation runs. **Output**: Script `batch_runner.py`.
- [ ] T030b [US3] Execute `batch_runner.py` to generate 30 independent simulation runs (n=30). **Output**: `data/simulation/run_001.json` through `data/simulation/run_030.json`.
- [ ] T031 [US3] Implement and run statistical significance test (paired t-test, n=30 runs) on the **accumulated KL-divergence** metric in `code/analysis/stats.py`. **Input**: `data/simulation/accumulated_kl_divergence.csv`. **Output**: `data/analysis/t_test_results.json`.
- [ ] T033 [US3] Generate visualization of accumulated error vs. steps in `code/analysis/visualizations.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `docs/` and `README.md`
- [ ] T035 Code cleanup and refactoring across `code/` modules
- [ ] T036 Performance optimization for Sequential Sinkhorn solver on CPU
- [ ] T037 [P] Additional unit tests for edge cases (NaN handling, extreme outliers) in `tests/`
- [ ] T038 Run `quickstart.md` validation to ensure reproducible execution
- [ ] T039 Verify all artifacts are checksummed and immutable

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Foundational Prerequisites (Phase 2.1)**: Depends on Phase 2 - BLOCKS US1 implementation
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) and **after T017a** (Phase 2.1) - No dependencies on other stories. **Produces the ground truth labels required by US2 and US3.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) and **after US1 data generation** (requires labels).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2), **after US1 (data)** and **after US2 (model trained)**.
 - T030b (30 runs) must complete before T031 (t-test).
 - T025 (Sensitivity) depends on T005b and T030b.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately (after T017a). US2 and US3 must wait for US1 data.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **only after data dependencies are met**

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for moment extraction and epsilon handling in tests/test_data_generation.py"
Task: "Unit test for Sequential Sinkhorn solver convergence and state update in tests/test_data_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement synthetic trajectory generator... in code/data_generation/synthetic_attention.py"
Task: "Implement Sequential Sinkhorn Optimizer... in code/simulation/sequential_sinkhorn.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.1: Foundational Prerequisites (T017a)
4. Complete Phase 3: User Story 1 (Generate Data + Ground Truth)
5. **STOP and VALIDATE**: Verify data generation produces valid labels and matches drift parameters.
6. Deploy/demo if ready (Data artifact ready)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (Data Artifact)
3. Add User Story 2 → Test independently → Deploy/Demo (Trained Model)
4. Add User Story 3 → Test independently → Deploy/Demo (Simulation Results)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Model Training) - *Must wait for A to produce initial data subset*
 - Developer C: User Story 3 (Simulation) - *Must wait for A and B*
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
- **Crucial**: The Sequential Sinkhorn solver (T016) must be CPU-optimized (NumPy/Scipy) as no GPU is available.
- **Crucial**: All data generation (T017b) must use real mathematical models for drift, not random fabrication, to satisfy FR-001.
- **Crucial**: Dataset size for T017b is read from config, not hardcoded, to allow runtime adjustment.
- **Crucial**: T029 must isolate optimization overhead by subtracting baseline inference time.
- **Crucial**: Tb must produce exactly 30 files (run_001.json to run_030.json) via `batch_runner.py`.
- **Crucial**: T031 must perform t-test on accumulated KL-divergence, not per-step error.
- **Crucial**: T017a must be implemented before T017b to ensure the `DriftModel` is available for trajectory generation.
- **Crucial**: T005b must be implemented before T025 to ensure the epsilon sweep values are available for sensitivity analysis.
- **Crucial**: T032 must be implemented before T031 to ensure the theoretical lower bound is available for comparison in the statistical analysis.
- **Crucial**: T025 is placed in Phase 4/5 to ensure simulation results are available for sensitivity analysis, but depends on T005b for configuration.
- **Crucial**: Tasks T040-T042 (Real-World Data) have been removed as they were not authorized by the spec.md and violated the Constitution. The project scope is strictly synthetic.