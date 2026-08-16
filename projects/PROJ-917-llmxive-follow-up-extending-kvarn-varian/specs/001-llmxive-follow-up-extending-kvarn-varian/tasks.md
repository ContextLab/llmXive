---
description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

**Input**: Design documents from `/specs/001-llmxive-kvarn-static-prior/`
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

- [ ] T001a [P] Initialize `code/` directory structure. **Action**: Execute `mkdir -p code/{data_generation,model_training,simulation,analysis}`. **Verification**: `test -d code/data_generation && test -d code/model_training`. **Deliverable**: `code/` directory tree.
- [ ] T001b [P] Initialize `data/` directory structure. **Action**: Execute `mkdir -p data/{raw,processed,models,simulation}`. **Verification**: `test -d data/raw && test -d data/processed`. **Deliverable**: `data/` directory tree.
- [ ] T001c [P] Initialize `tests/` directory structure. **Action**: Execute `mkdir -p tests/test_data_generation tests/test_model_training tests/test_simulation` and `touch tests/__init__.py tests/test_data_generation/__init__.py tests/test_model_training/__init__.py tests/test_simulation/__init__.py`. **Verification**: `test -f tests/__init__.py`. **Deliverable**: `tests/` directory tree with `__init__.py` files.
- [ ] T003 [P] Initialize Python 3.11 project with pinned `requirements.txt` (numpy, scipy, torch-cpu, scikit-learn, pandas, pyarrow, pytest, matplotlib). **Deliverable**: `requirements.txt` file.
- [ ] T001d [P] Initialize project state file. **Action**: Execute `mkdir -p state/projects` and create `state/projects/PROJ-917-llmxive-follow-up-extending-kvarn-varian.yaml` with content: `artifact_hashes: {}`. **Verification**: `test -f state/projects/PROJ-917-llmxive-follow-up-extending-kvarn-varian.yaml`. **Deliverable**: Initial state YAML file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [ ] T005b [P] [US1] Define initial epsilon sweep values in `code/config.py`. **Action**: Define constant `EPSILON_SWEEP_VALUES = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4]`. **Verification**: Import `config` and assert `EPSILON_SWEEP_VALUES` matches the list. **Deliverable**: Constant definition in `code/config.py`. **Note**: This provides the hardcoded defaults required to break circular dependencies.
- [ ] T005a [P] [US1] Implement and run a **pilot** sensitivity analysis to validate epsilon configuration before full batch run. **Input**: `EPSILON_SWEEP_VALUES` from T005b. **Output**: `data/analysis/epsilon_pilot.json`. **Verification**: Assert that `delta_kl_per_step` is monotonic or within expected bounds; if not, flag for config review. **Requirement**: Must complete before T030b. **Dependency**: T005b.
- [ ] T006 [P] [US3] Implement `SimulationState` dataclass in `code/simulation/state.py` with fields: `accumulated_kl: float`, `current_error_state: dict`, `step_index: int`, `full_trajectory: list[float]`. This module MUST be imported by T016b.
- [ ] T007a [P] [US1] Implement `AttentionMatrix` dataclass in `code/entities.py`. **Schema**: 128x128 matrix, mean, variance, sparsity, outlier_magnitude. **Note**: Aligns with Spec Key Entities.
- [ ] T007b [P] [US1] Implement `ScalingFactor` dataclass in `code/entities.py`. **Schema**: Scalar value, derivation_method.
- [ ] T007c [P] [US1] Implement `SimulationRun` dataclass in `code/entities.py`. **Schema**: Sequence of KL-divergence values, timing metrics.
- [ ] T008 [P] [US1] Implement global random seed management in `code/utils/seeds.py` with a `set_global_seed(seed: int)` function that calls `np.random.seed`, `torch.manual_seed`, and `random.seed`. **Verification**: Run `main.py` twice with the same seed and check output checksums match.
- [ ] T009 [P] [US1] Setup environment configuration management in `code/config.py` with a `Config` dataclass containing `CPU_ONLY=True`, `EPSILON_FLOOR=1e-6`, `RANDOM_SEED`, `NUM_MATRICES=10000`, `SIMULATION_STEPS=1000`, `NUM_RUNS=30`. **Verification**: Load `config.py` and assert defaults.
- [ ] T010 [P] [US1] Implement unit test for moment extraction (mean, variance, sparsity, outlier_magnitude) and epsilon handling in `tests/test_data_generation.py`. **Deliverable**: A test file that verifies `apply_epsilon_floor` and moment extraction logic for **mean, variance, sparsity, and outlier_magnitude**. **Constraint**: Must validate extraction of all fields defined in Spec Key Entities.
- [ ] T016 [P] [US1] Implement `SingleStepSinkhornSolver` class in `code/data_generation/sinkhorn_solver.py`. **Signature**: `solve(matrix: np.ndarray, epsilon: float) -> float`. **Requirement**: Must compute a **single** ground-truth scaling factor for an **independent** static matrix. **Requirement**: Must NOT maintain cumulative state. **Requirement**: Must handle non-convergence by raising a specific exception or returning NaN (to be handled by T017c). **Deliverable**: A solver that outputs a single scalar label per matrix.
- [ ] T011 [P] [US1] Implement unit test for SingleStepSinkhorn solver convergence and edge cases in `tests/test_data_generation.py`. **Deliverable**: A test file that verifies `SingleStepSinkhornSolver` handles near-zero variance and non-convergence. **Dependency**: T016.
- [ ] T016b [P] [US3] Implement `SequentialSinkhornSolver` class and accumulation loop in `code/simulation/sequential_sinkhorn.py`. **Signature**: `solve_step(matrix, prev_state: SimulationState) -> (scaling_factor, new_state: SimulationState)`. **Requirement**: Must maintain cumulative error state across steps; must accept and return a `SimulationState` object. **Requirement**: Must implement the core solver logic and step update. **Requirement**: The simulation horizon MUST be [deferred] steps as defined by Constitution Principle VI. **Requirement**: Must integrate with `SimulationState` to update `full_trajectory`. **Dependency**: T006. **Note**: Distinct from T016 (Single-Step) used in US1.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Ground-Truth Scaling Factors for Synthetic Attention Matrices (Priority: P1) 🎯 MVP

**Goal**: Generate a configurable number of synthetic attention matrices (128x128) with controlled sparsity and outlier magnitudes, and compute ground-truth scaling factors using the KVarN Sinkhorn optimizer.

**Independent Test**: Can be fully tested by running the data generation script on a small subset and verifying that the output file contains valid scaling factors, that the distribution matches drift parameters, and that computation time per matrix matches the expected overhead of the SingleStepSinkhorn solver.

### Implementation for User Story 1

- [ ] T017c [US1] Implement and execute the **Unified Data Generation and Labeling** script in `code/data_generation/synthetic_attention.py`. **Requirement**: Must generate **exactly 10,000** synthetic attention matrices with controlled sparsity and outlier magnitudes. **Requirement**: Must compute ground-truth scaling factors using `SingleStepSinkhornSolver` (T016) **during** the generation loop. **Requirement**: Must write a single output file `data/raw/synthetic_attention_matrices.parquet` containing **both** the matrix data (mean, var, sparsity, outlier) **and** the computed `scaling_factor`. **Requirement**: Must handle non-convergence by skipping or flagging instances (do not produce NaN labels). **Verification**: Assert count matches [deferred]. **Dependency**: T016. **Deliverable**: A complete dataset with matrices and labels. **Note**: Merged T017a, T017b, T017c1, T017c2 into one task to ensure labels are written.
- [ ] T019 [US1] Implement data serialization (Parquet/JSON) with checksums for generated dataset in `code/data_generation/utils.py`. **Deliverable**: Serialization logic with checksums.
- [ ] T021 [US1] Add logging for data generation progress and solver failures in `code/data_generation/utils.py`. **Deliverable**: Logging implementation.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (N matrices + ground truth labels generated)

---

## Phase 4: User Story 2 - Train and Evaluate the Static Prior Model (Priority: P2)

**Goal**: Train a lightweight MLP on CPU to map input attention moments (mean, variance) to ground-truth scaling factors, and evaluate against a closed-form baseline.

**Independent Test**: Can be fully tested by training the model on the training split and reporting the Mean Squared Error (MSE) on the test split. If the MSE is below a specific threshold, the mapping is considered learnable.

### Implementation for User Story 2

- [ ] T022 [P] [US2] [FR-009] Define a multi-layer perceptron (MLP) model architecture with **statistical moment features** (mean, variance) in `code/model_training/mlp_model.py`. **Note**: Implements Spec FR-002 (2 moments). **Constraint**: Must use a set of inputs (mean, variance) as per Spec FR-002.
- [ ] T023 [US2] [FR-009] Implement training loop with MSE loss, CPU-only execution, and epoch logging in `code/model_training/train.py`. **Output**: `data/models/mlp_weights.pt`, `data/metrics/training_log.csv`.
- [ ] T024 [US2] Implement closed-form baseline predictor (s = 1/variance) in `code/model_training/baselines.py`. **Deliverable**: Baseline predictor implementation.
- [ ] T026 [US2] Save trained model weights and training metrics to `data/` artifacts in `code/model_training/train.py`. **Deliverable**: Saved model and metrics.
- [ ] T035c [US2] [FR-009] Implement comparison logic for MLP vs. closed-form baseline MSE in `code/analysis/stats.py`. **Output**: `data/metrics/baseline_comparison.json`. **Requirement**: Must verify if MLP captures non-trivial relationships beyond identity (FR-009). **Dependency**: T022, T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Model trained and baseline comparison ready)

---

## Phase 5: User Story 3 - Simulate Long-Horizon Generation and Measure Latency/Accuracy Trade-off (Priority: P3)

**Goal**: Run a simulated autoregressive generation loop replacing the KVarN optimizer with the trained static prior, measuring accumulated KL-divergence and per-token latency.

**Independent Test**: Can be fully tested by running the simulation loop twice (once with KVarN optimizer, once with static prior) and comparing the final accumulated KL-divergence and average wall-clock time per token.

### Implementation for User Story 3

- [ ] T035a [P] [US3] Implement **Out-of-Distribution (OOD) Detection** mechanism in `code/simulation/ood_detector.py`. **Requirement**: Must compute a statistical distance metric (e.g., Mahalanobis distance, simple thresholding) between input matrix moments and training distribution moments. **Note**: The specific metric is a **design choice**; any valid OOD detection mechanism suffices to satisfy the spec's "graceful failure" requirement. **Output**: A boolean flag `is_ood` and a confidence score. **Dependency**: T022 (trained model moments).
- [ ] T035b [US3] Implement generic edge case handler for extreme outlier magnitudes in `code/simulation/autoregressive_loop.py`. **Requirement**: Must implement graceful failure (e.g., raise exception or log warning) for extreme outliers **only if** `is_ood` is true (from T035a) or if a simple threshold is exceeded. **Requirement**: This task requires the **integrated execution path** of T016b (SequentialSinkhorn) and T022 (Static) within T027d to be functional. **Dependency**: T035a, T016b. **Deliverable**: Fallback logic implementation. **Note**: Does NOT mandate a specific KVarN fallback mechanism, only graceful failure as per Spec Edge Cases.
- [ ] T027d [US3] Implement **Unified Autoregressive Simulation Runner** in `code/simulation/autoregressive_loop.py`. **Requirement**: Must execute a configurable number of steps (default [deferred], defined in `code/config.py` per Constitution Principle VI). **Input**: `SimulationState` from T006. **Requirement**: Must explicitly accumulate KL-divergence *per step* within the loop and store it in the state to satisfy FR-004 and Constitution Principle VI. **Requirement**: Must support switching between 'Static Prior' and 'original KVarN method (SequentialSinkhornSolver)' modes within the **same execution pass** using a shared random seed sequence to ensure valid pairing for FR-006. **Requirement**: Must output per-run JSON files containing `final_accumulated_kl` AND `full_trajectory` (list of per-step errors). **Output**: `data/simulation/run_XXX_results.json`. **Dependency**: T016b, T022, T035a, T035b. **Deliverable**: Unified engine that runs both modes sequentially with identical seeds.
- [ ] T028 [US3] Implement KL-divergence accumulation logic comparing **quantized output distribution** vs **full-precision distribution** in `code/simulation/kl_divergence.py`. **Requirement**: Must store the full per-step error trajectory (sequence of errors) for each step of the simulation (1,000 steps per Constitution Principle VI) to satisfy Constitution Principle VI. **Requirement**: Must explicitly measure between quantized and full-precision distributions. **Dependency**: T027d.
- [ ] T030a [P] [US3] Implement `code/simulation/batch_runner.py` to execute multiple independent simulation runs. **Output**: Script `batch_runner.py`.
- [ ] T030b [US3] Execute `batch_runner.py` to generate **exactly 30** independent simulation runs, with the default set via `code/config.py`. **Output**: `data/simulation/run_001.json` through `data/simulation/run_030.json`. **Requirement**: Must use a base seed with offsets (seed + i) for reproducibility. **Requirement**: Each run must be [deferred] steps (per Constitution Principle VI). **Requirement**: Each run file must contain both Static and KVarN results paired by seed. **Dependency**: T027d. **Deliverable**: Execution of batch runner.
- [ ] T030b-verify [US3] Verify 30 files exist and contain required fields. **Output**: Verification report. **Requirement**: A corpus of 30 files must exist to support the study. **Dependency**: T030b. **Deliverable**: Verification report.
- [ ] T030c1 [US3] Implement aggregation script to combine the 30 JSON run files into `data/simulation/accumulated_kl_divergence.csv`. **Output**: `data/simulation/accumulated_kl_divergence.csv`. **Schema**: Columns `run_id`, `method`, `final_accumulated_kl`, `full_trajectory` (JSON string or list). **Requirement**: Must derive the final scalar value from the simulation runs AND preserve the full trajectory for analysis. **Dependency**: T030b. **Deliverable**: Aggregation logic.
- [ ] T030c2 [US3] Execute aggregation script. **Output**: `data/simulation/accumulated_kl_divergence.csv`. **Dependency**: T030c1. **Deliverable**: Execution of script.
- [ ] T030c3 [US3] Verify output CSV. **Output**: Verification report. **Requirement**: Must assert CSV contains data for 30 runs and trajectories. **Dependency**: T030c2. **Deliverable**: Verification report.
- [ ] T032 [US3] Implement theoretical lower bound calculation using the analytical noise model formula $\Delta^/12$ (where $\Delta$ is the **quantization interval derived from the simulation's quantization scheme**) in `code/analysis/stats.py`. **Output**: `data/analysis/theoretical_lower_bound.json`. **Requirement**: Must include a derivation artifact (comment or docstring) explaining the formula. **Requirement**: Must explicitly reference the simulation horizon for consistency. (Dependency for US3 validation)
- [ ] T032b [US3] Perform comparison against the Theoretical Lower Bound. **Input**: `data/simulation/accumulated_kl_divergence.csv` and `data/analysis/theoretical_lower_bound.json`. **Output**: `data/analysis/bound_comparison.json`. **Requirement**: Must calculate the difference between the static prior's accumulated KL-divergence and the theoretical lower bound. **Requirement**: Must report the gap as a percentage of the bound to validate FR-008. **Dependency**: T030c2, T032.
- [ ] T025b [US3] Implement **Full Sensitivity Analysis** in `code/analysis/stats.py`. **Input**: `EPSILON_SWEEP_VALUES` from T005b and simulation results from T030b. **Output**: `data/analysis/epsilon_sensitivity.json`. **Requirement**: Must calculate and report the **accumulated_kl_divergence_error_rate** (primary metric) and **variation_rate** (secondary derivative metric) for each epsilon step to satisfy Spec FR-007 ("report how... varies"). **Dependency**: T005b, T030b. **Note**: This runs after the full batch to report on the robustness of the configuration used.
- [ ] T031 [US3] Implement and run statistical significance test (paired t-test, n=30 runs) on the **final accumulated KL-divergence** in `code/analysis/stats.py`. **Input**: `data/simulation/accumulated_kl_divergence.csv`. **Logic**: Read `full_trajectory` from CSV -> Sum trajectory to scalar `final_accumulated_kl` -> Run paired t-test on the scalars. **Output**: `data/simulation/t_test_results.json`. **Requirement**: Pairing must be between static prior and KVarN results from the same run index (run_XXX_static vs run_XXX_kvarn). **Requirement**: The scalar value used for the t-test MUST be the **sum of the per-step errors** recorded in T028. **Requirement**: Must explicitly state that the test is run on scalars, not trajectories. **Requirement**: The sample size 'n' is exactly 30. **Dependency**: T030c2.
- [ ] T033 [US3] Generate final report and plots. **Input**: Results from T031 (t-test), T032b (bound comparison), T025b (sensitivity), T042 (latency). **Output**: `data/results/final_report.md`. **Requirement**: Must combine results, visualize the comparison (including the bound comparison from T032b), and summarize findings. **Dependency**: T031, T032b, T025b, T042.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034a [P] Update `README.md` with installation instructions and quickstart guide.
- [ ] T034b [P] Update `docs/quickstart.md` with step-by-step execution guide.
- [ ] T034c [P] Update `docs/api.md` with module interface definitions.
- [ ] T035 Code cleanup and refactoring across `code/` modules
- [ ] T036 Performance optimization for Sequential Sinkhorn solver on CPU
- [ ] T037 [P] Additional unit tests for edge cases (NaN handling, extreme outliers) in `tests/`
- [ ] T038 Run `quickstart.md` validation to ensure reproducible execution
- [ ] T039 Verify all artifacts are checksummed and immutable
- [ ] T040 [P] Finalize `data-model.md` with updated entity definitions for `AttentionMatrix` and `SimulationState`. (Note: Removed 'AttentionTrajectory' to align with spec).
- [ ] T041 [P] Update `contracts/` directory with interface definitions for `SingleStepSinkhornSolver`, `SequentialSinkhornSolver`, and `StaticPriorModel`.
- [ ] T042 [P] [US3] Implement explicit runtime profiling for per-token latency in `code/simulation/autoregressive_loop.py` to satisfy FR-005 and SC-003. **Requirement**: Must use `time.perf_counter()` for high-resolution timing around the quantization and scaling step. **Requirement**: Must output `per_token_latency_ms` to the run JSON file. **Dependency**: T027d.
- [ ] T043 [P] [US2] Add explicit logging of training hyperparameters (learning rate, batch size, epochs) to `data/metrics/training_log.csv` to ensure reproducibility per Constitution Principle I. **Requirement**: Must include a header row and a row for the final epoch. **Dependency**: T023.
- [ ] T044 [P] [US1] Implement a "Data Generation Health Check" script in `code/data_generation/health_check.py` that validates the generated dataset for NaNs, infinite values, and reasonable distribution ranges before training begins. **Requirement**: Must fail loudly (exit code 1) if any anomalies are detected. **Dependency**: T017c.
- [ ] T004 [P] Verify Python syntax for all `.py` files. **Action**: Execute `python -c "import glob, py_compile; files = glob.glob('code/**/*.py', recursive=True); [py_compile.compile(f, doraise=True) for f in files]"`. **Verification**: Command exits with 0. **Deliverable**: Verification report. **Dependency**: All code generation tasks complete.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces the ground truth labels required by US2 and US3.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) and **after US1 data generation** (requires labels).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2), **after US1 (data)** and **after US2 (model trained)**.
 - T030b (30 runs) must complete before T030c (CSV aggregation) and T025b (Full Sensitivity).
 - T030c (CSV aggregation) must complete before T031 (t-test).
 - T032 (Theoretical Lower Bound) and T032b (Comparison) must complete before T033 (Report).
 - T005a (Pilot) must complete before T030b.

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
Task: "Unit test for SingleStepSinkhorn solver convergence in tests/test_data_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement static synthetic matrix generator... in code/data_generation/synthetic_attention.py"
Task: "Implement SingleStepSinkhorn Optimizer... in code/data_generation/sinkhorn_solver.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Generate Data + Ground Truth)
4. **STOP and VALIDATE**: Verify data generation produces valid labels and matches static distribution parameters.
5. Deploy/demo if ready (Data artifact ready)

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
- **Crucial**: The SingleStepSinkhorn solver (T016) must be CPU-optimized (NumPy/Scipy) as no GPU is available.
- **Crucial**: The SequentialSinkhorn solver (T016b) is distinct from T016 and used only in US3.
- **Crucial**: All data generation (T017c) must use real mathematical models for static distributions (mean, variance, sparsity, outliers), not random fabrication, to satisfy FR-001.
- **Crucial**: Dataset size for T017c is [deferred] matrices as per FR-001.
- **Crucial**: T027d must isolate optimization overhead by running both modes with the same seed sequence for valid pairing.
- **Crucial**: T030b must produce exactly 30 files (run_001.json to run_030.json) via `batch_runner.py` using seed offsets, where n=30 is mandatory.
- **Crucial**: T031 must perform t-test on the **final scalar** accumulated KL-divergence (sum of trajectory), not per-step error, with pairing by run index, using input from T030c2. The sample size 'n' is exactly 30.
- **Crucial**: T005b must be implemented before T005a to ensure the epsilon sweep values are defined before the pilot runs.
- **Crucial**: T032 must be implemented before T033 to ensure the theoretical lower bound is available for comparison in the final report.
- **Crucial**: T032b must explicitly compare the results against the bound to satisfy FR-008.
- **Crucial**: T025a (Pilot) must complete before T030b; T025b (Full) must complete after T030b.
- **Crucial**: T025a must output `accumulated_kl_divergence_error_rate` as the primary metric and `variation_rate` as secondary to satisfy FR-007.
- **Crucial**: T035a and T035b implement a generic edge case handler (not a specific KVarN fallback) to satisfy the "graceful failure" requirement; the specific metric is not mandated by the spec.
- **Crucial**: The simulation horizon is fixed per Constitution Principle VI ([deferred] steps). (see T016b, T027d, T028, T030b, T031).
- **Crucial**: T042 must explicitly measure wall-clock time per token to satisfy FR-005 and SC-003, ensuring the latency reduction claim is empirically grounded.
- **Crucial**: T043 ensures that the training process is fully reproducible by logging all hyperparameters, satisfying Constitution Principle I.
- **Crucial**: T044 acts as a gatekeeper for data quality, preventing the propagation of NaNs or outliers into the training and simulation phases.