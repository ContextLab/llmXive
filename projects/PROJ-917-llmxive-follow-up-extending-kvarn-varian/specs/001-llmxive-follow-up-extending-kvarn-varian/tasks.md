# Tasks: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-kvarn-varian/`
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

- [ ] T001 Create project structure per implementation plan (`code/data_generation`, `code/model_training`, `code/simulation`, `code/analysis`, `code/evaluation`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with pinned `requirements.txt` (numpy, scipy, torch-cpu, scikit-learn, pandas, pyarrow, pytest, matplotlib)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup `data/` directory structure with checksumming logic for immutable raw data
- [ ] T005 [P] Implement numerical stability utilities (epsilon floor handling, drift models) in `code/data_generation/utils.py`
- [ ] T006 [P] Setup simulation state tracking framework (cumulative error state, KL-divergence accumulator)
- [ ] T007 Create base entities: `AttentionTrajectory`, `ScalingFactor`, `SimulationRun` in `code/` shared module
- [ ] T008 Configure random seed management for reproducibility across all modules
- [ ] T009 Setup environment configuration management for CPU-only execution flags
- [ ] T032 [P] [US3] Implement theoretical lower bound calculation (analytical noise floor, formula Δ²/) in `code/analysis/stats.py` (Dependency for US3 validation)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Ground-Truth Scaling Factors for Synthetic Attention Trajectories (Priority: P1) 🎯 MVP

**Goal**: Generate a configurable number of synthetic attention trajectories with temporal drift and compute ground-truth scaling factors using a Sequential Sinkhorn Optimizer.

**Independent Test**: Can be fully tested by running the data generation script on a small subset and verifying that the output file contains valid scaling factors, that the distribution matches drift parameters, and that computation time per matrix matches the expected overhead of the Sequential Sinkhorn solver.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for moment extraction and epsilon handling in `tests/test_data_generation.py`
- [ ] T011 [P] [US1] Unit test for Sequential Sinkhorn solver convergence and state update in `tests/test_data_generation.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement Sequential Sinkhorn Optimizer that maintains cumulative error state in `code/simulation/sequential_sinkhorn.py` (Shared utility for data generation and simulation)
- [ ] T013 [US1] Implement synthetic trajectory generator with controlled sparsity, outliers, and temporal drift in `code/data_generation/synthetic_attention.py` (Reads dataset size from config)
- [ ] T014 [US1] Implement ground-truth label computation logic linking trajectory steps to optimal scaling factors in `code/data_generation/synthetic_attention.py`
- [ ] T015 [US1] Implement data serialization (Parquet/JSON) with checksums for generated dataset in `code/data_generation/utils.py`
- [ ] T016 [US1] Add validation checks for near-zero variance handling and NaN flagging in `code/data_generation/synthetic_attention.py`
- [ ] T017 [US1] Add logging for data generation progress and solver failures in `code/data_generation/utils.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (N trajectories + ground truth labels generated)

---

## Phase 4: User Story 2 - Train and Evaluate the Static Prior Model (Priority: P2)

**Goal**: Train a lightweight MLP on CPU to map input attention moments (mean, var, skew, kurt) to ground-truth scaling factors, and evaluate against a closed-form baseline.

**Independent Test**: Can be fully tested by training the model on the training split and reporting the Mean Squared Error (MSE) on the test split. If the MSE is below a specific threshold, the mapping is considered learnable.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for MLP architecture definition in `tests/test_model_training.py`
- [ ] T019 [P] [US2] Unit test for closed-form baseline (s = 1/variance) implementation in `tests/test_model_training.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Define a multi-layer perceptron (MLP) model architecture (4 inputs: mean, var, skew, kurt) in `code/model_training/mlp_model.py`
- [ ] T021 [US2] Implement training loop with MSE loss, CPU-only execution, and epoch logging in `code/model_training/train.py`
- [ ] T022 [US2] Implement closed-form baseline predictor (s = 1/variance) in `code/model_training/baselines.py`
- [ ] T023 [US2] Implement evaluation logic comparing MLP MSE vs. Baseline MSE on held-out test set in `code/model_training/train.py`
- [ ] T025 [US2] Save trained model weights and training metrics to `data/` artifacts in `code/model_training/train.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Model trained and baseline comparison ready)

---

## Phase 5: User Story 3 - Simulate Long-Horizon Generation and Measure Latency/Accuracy Trade-off (Priority: P3)

**Goal**: Run a simulated autoregressive generation loop replacing the KVarN optimizer with the trained static prior, measuring accumulated KL-divergence and per-token latency.

**Independent Test**: Can be fully tested by running the simulation loop twice (once with KVarN optimizer, once with static prior) and comparing the final accumulated KL-divergence and average wall-clock time per token.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Integration test for full simulation loop (static prior vs. sinkhorn) in `tests/test_simulation.py`
- [ ] T027 [P] [US3] Unit test for KL-divergence calculation and accumulation logic in `tests/test_simulation.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement autoregressive simulation engine with cumulative error state propagation in `code/simulation/autoregressive_loop.py`
- [ ] T029 [US3] Implement KL-divergence accumulation logic comparing quantized vs. full-precision distributions in `code/simulation/kl_divergence.py`
- [ ] T030 [US3] Implement wall-clock profiling for both static prior and Sequential Sinkhorn methods in `code/simulation/profiler.py`
- [ ] T031 [US3] Implement statistical significance test (paired t-test, n=30 runs) in `code/analysis/stats.py`
- [ ] T024 [US3] Implement sensitivity analysis logic for epsilon floor sweep in `code/analysis/stats.py` (Moved from US2 to US3 to ensure simulation data availability)
- [ ] T034 [US3] Generate visualization of accumulated error vs. steps in `code/analysis/visualizations.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5.1: User Story 4 - Evaluate Static Prior on Real-World Attention Maps (Priority: P4)

**Goal**: Extract attention matrices from a real-world pre-trained model (DistilBERT) and evaluate the static prior on these maps to validate generalization.

**Independent Test**: Can be fully tested by running the extraction script on a subset of the GLUE dataset and verifying that the model produces valid scaling factors without crashing.

### Implementation for User Story 4

- [ ] T034 [US4] Implement real-world attention map extraction from pre-trained DistilBERT on GLUE/SQuAD dataset in `code/evaluation/real_world_extractor.py` (Outputs: JSON/Parquet with layer indices and extracted matrices)
- [ ] T035 [US4] Evaluate trained static prior on extracted real-world maps and compute MSE in `code/evaluation/real_world_evaluator.py`
- [ ] T036 [US4] Compare real-world MSE against synthetic test set MSE in `code/analysis/stats.py`

**Checkpoint**: Generalization performance validated

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` and `README.md`
- [ ] T038 Code cleanup and refactoring across `code/` modules
- [ ] T039 Performance optimization for Sequential Sinkhorn solver on CPU
- [ ] T040 [P] Additional unit tests for edge cases (NaN handling, extreme outliers) in `tests/`
- [ ] T041 Run `quickstart.md` validation to ensure reproducible execution
- [ ] T042 Verify all artifacts are checksummed and immutable

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces the ground truth labels required by US2 and US3.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) and **after US1 data generation** (requires labels).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2), **after US1 (data)** and **after US2 (model trained)**.
- **User Story 4 (P4)**: Can start after **US2 (model trained)**.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately. US2 and US3 must wait for US1 data.
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
3. Complete Phase 3: User Story 1 (Generate Data + Ground Truth)
4. **STOP and VALIDATE**: Verify data generation produces valid labels and matches drift parameters.
5. Deploy/demo if ready (Data artifact ready)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (Data Artifact)
3. Add User Story 2 → Test independently → Deploy/Demo (Trained Model)
4. Add User Story 3 → Test independently → Deploy/Demo (Simulation Results)
5. Add User Story 4 → Test independently → Deploy/Demo (Generalization Results)
6. Each story adds value without breaking previous stories

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
- **Crucial**: The Sequential Sinkhorn solver (T012) must be CPU-optimized (NumPy/Scipy) as no GPU is available.
- **Crucial**: All data generation (T013) must use real mathematical models for drift, not random fabrication, to satisfy FR-001.
- **Crucial**: Dataset size for T013 is read from config, not hardcoded, to allow runtime adjustment.