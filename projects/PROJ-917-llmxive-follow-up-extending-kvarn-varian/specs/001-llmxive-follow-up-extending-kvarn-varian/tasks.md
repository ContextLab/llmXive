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

- [ ] T001a [P] Create `code/` root directory. **Action**: Execute `mkdir -p code/`. **Verification**: `test -d code/ && echo OK`. **Deliverable**: An empty `code/` directory.
- [ ] T001a1 [P] Create `code/data_generation/` directory. **Action**: Execute `mkdir -p code/data_generation/`. **Verification**: `test -d code/data_generation/ && echo OK`. **Deliverable**: An empty `code/data_generation/` directory.
- [ ] T001a2 [P] Create `code/model_training/` directory. **Action**: Execute `mkdir -p code/model_training/`. **Verification**: `test -d code/model_training/ && echo OK`. **Deliverable**: An empty `code/model_training/` directory.
- [ ] T001a3 [P] Create `code/simulation/` directory. **Action**: Execute `mkdir -p code/simulation/`. **Verification**: `test -d code/simulation/ && echo OK`. **Deliverable**: An empty `code/simulation/` directory.
- [ ] T001a4 [P] Create `code/analysis/` directory. **Action**: Execute `mkdir -p code/analysis/`. **Verification**: `test -d code/analysis/ && echo OK`. **Deliverable**: An empty `code/analysis/` directory.
- [ ] T001b [P] Create `data/` root directory. **Action**: Execute `mkdir -p data/`. **Verification**: `test -d data/ && echo OK`. **Deliverable**: An empty `data/` directory.
- [ ] T001b1 [P] Create `data/raw/` directory. **Action**: Execute `mkdir -p data/raw/`. **Verification**: `test -d data/raw/ && echo OK`. **Deliverable**: An empty `data/raw/` directory.
- [ ] T001b2 [P] Create `data/processed/` directory. **Action**: Execute `mkdir -p data/processed/`. **Verification**: `test -d data/processed/ && echo OK`. **Deliverable**: An empty `data/processed/` directory.
- [ ] T001b3 [P] Create `data/models/` directory. **Action**: Execute `mkdir -p data/models/`. **Verification**: `test -d data/models/ && echo OK`. **Deliverable**: An empty `data/models/` directory.
- [ ] T001b4 [P] Create `data/simulation/` directory. **Action**: Execute `mkdir -p data/simulation/`. **Verification**: `test -d data/simulation/ && echo OK`. **Deliverable**: An empty `data/simulation/` directory.
- [X] T001c [P] Implement checksumming script in `code/data_generation/utils.py` to compute and store checksums for all files in `data/`. **Output**: A JSON map at `state/checksums.json` using SHA-256 algorithm. **Deliverable**: A script that computes and stores checksums.
- [ ] T001d Execute checksumming script on initial `data/` structure to verify integrity. **Deliverable**: Checksums stored in `state/`. **Dependency**: T001c must be complete and functional.
- [ ] T002 [P] Create `tests/` directory structure (`tests/test_data_generation`, `tests/test_model_training`, `tests/test_simulation`) and create `__init__.py` files. **Action**: Execute `mkdir -p tests/test_data_generation tests/test_model_training tests/test_simulation` and `touch tests/__init__.py tests/test_data_generation/__init__.py tests/test_model_training/__init__.py tests/test_simulation/__init__.py`. **Verification**: `test -f tests/__init__.py && test -f tests/test_data_generation/__init__.py`. **Deliverable**: Directory structure with `__init__.py` files.
- [X] T003 Initialize Python 3.11 project with pinned `requirements.txt` (numpy, scipy, torch-cpu, scikit-learn, pandas, pyarrow, pytest, matplotlib)
- [ ] T004 [P] Verify Python syntax for all `.py` files. **Action**: Execute `python -c "import glob, py_compile; files = glob.glob('code/**/*.py', recursive=True); [py_compile.compile(f, doraise=True) for f in files]"`. **Verification**: Command exits with 0. **Deliverable**: Verification report.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [X] T005 [P] Implement numerical stability utilities (epsilon floor handling) in `code/data_generation/utils.py`. **Deliverable**: A function `apply_epsilon_floor(value: float, epsilon: float) -> float` that returns `max(value, epsilon)`.
- [X] T005b [P] [US2] Define a list of epsilon values for sensitivity analysis in `code/config.py` as a constant `EPSILON_SWEEP_VALUES`. **Requirement**: This constant serves as a **runtime-parameter source** for the dynamic sweep logic in T025, not a fixed compile-time constraint. **Deliverable**: A constant definition. **Note**: This task defines the values; execution logic is in T025.
- [ ] T005a [P] [US3] Implement and run a **pilot** sensitivity analysis to validate epsilon configuration before full batch run. **Input**: `EPSILON_SWEEP_VALUES` from T005b. **Output**: `data/analysis/epsilon_pilot.json`. **Verification**: Assert that `delta_kl_per_step` is monotonic or within expected bounds; if not, flag for config review. **Requirement**: Must complete before T030b. **Dependency**: T005b.
- [X] T006 [P] [US3] Implement `SimulationState` dataclass in `code/simulation/state.py` with fields: `accumulated_kl: float`, `current_error_state: dict`, `step_index: int`, `full_trajectory: list[float]`. This module MUST be imported by T016b and T027d.
- [X] T007a [P] [US1] Implement `AttentionMatrix` dataclass in `code/entities.py`. **Schema**: 128x128 matrix, mean, variance, sparsity, outlier_magnitude. **Note**: Aligns with Spec Key Entities.
- [X] T007b [P] [US1] Implement `ScalingFactor` dataclass in `code/entities.py`. **Schema**: Scalar value, derivation_method.
- [X] T007c [P] [US1] Implement `SimulationRun` dataclass in `code/entities.py`. **Schema**: Sequence of KL-divergence values, timing metrics.
- [X] T008 [P] [US1] Implement global random seed management in `code/utils/seeds.py` with a `set_global_seed(seed: int)` function that calls `np.random.seed`, `torch.manual_seed`, and `random.seed`. **Verification**: Run `main.py` twice with the same seed and check output checksums match.
- [X] T009 [P] [US1] Setup environment configuration management in `code/config.py` with a `Config` dataclass containing `CPU_ONLY=True`, `EPSILON_FLOOR=1e-6`, and `RANDOM_SEED`. **Verification**: Load `config.py` and assert defaults.
- [X] T010 [P] [US1] Implement unit test for moment extraction (mean, variance) and epsilon handling in `tests/test_data_generation.py`. **Deliverable**: A test file that verifies `apply_epsilon_floor` and moment extraction logic for **mean and variance only**. **Constraint**: Must validate extraction of mean and variance as per Spec FR-002.
- [ ] T016 [P] [US1] Implement `SingleStepSinkhornSolver` class in `code/data_generation/sinkhorn_solver.py`. **Signature**: `solve(matrix: np.ndarray, epsilon: float) -> float`. **Requirement**: Must compute a **single** ground-truth scaling factor for an **independent** static matrix. **Requirement**: Must NOT maintain cumulative state. **Requirement**: Must handle non-convergence by raising a specific exception or returning NaN (to be handled by T021b). **Dependency**: T005. **Deliverable**: A solver that outputs a single scalar label per matrix.
- [X] T011 [P] [US1] Implement unit test for SingleStepSinkhorn solver convergence and edge cases in `tests/test_data_generation.py`. **Deliverable**: A test file that verifies `SingleStepSinkhornSolver` handles near-zero variance and non-convergence. **Dependency**: T016.
- [ ] T016b [P] [US3] Implement `SequentialSinkhornSolver` class in `code/simulation/sequential_sinkhorn.py`. **Signature**: `solve_step(matrix, prev_state: SimulationState) -> (scaling_factor, new_state: SimulationState)`. **Requirement**: Must maintain cumulative error state across steps; must accept and return a `SimulationState` object. **Requirement**: Must explicitly accumulate KL-divergence *per step* within the returned `SimulationState` object to satisfy FR-004 and Constitution Principle VI. **Dependency**: T006. **Note**: Distinct from T016 (Single-Step) used in US1.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Ground-Truth Scaling Factors for Synthetic Attention Matrices (Priority: P1) 🎯 MVP

**Goal**: Generate a configurable number of synthetic attention matrices (128x128) with controlled sparsity and outlier magnitudes, and compute ground-truth scaling factors using the KVarN Sinkhorn optimizer.

**Independent Test**: Can be fully tested by running the data generation script on a small subset and verifying that the output file contains valid scaling factors, that the distribution matches drift parameters, and that computation time per matrix matches the expected overhead of the SingleStepSinkhorn solver.

### Implementation for User Story 1

- [ ] T017a [US1] Implement static synthetic matrix generator with controlled sparsity, outlier magnitudes, and **no temporal drift** in `code/data_generation/synthetic_attention.py`. **Requirement**: Must generate matrices with **controlled sparsity and outlier magnitudes** as per FR-001. **Note**: Static data is used for US1 training; US3 will use dynamic data (DriftModel) to address the domain shift. **Output**: `data/generated/static_matrices.parquet`. **Schema**: List of 10000 independent 128x128 matrices; each row must include `mean`, `var`, `sparsity`, `outlier_magnitude`, and `scaling_factor`. **Requirement**: Must generate **static** matrices (no DriftModel). **Dependency**: T016. **Deliverable**: Implementation of generator logic.
- [ ] T017a1 [US1] Implement schema validation for generated matrices in `code/data_generation/synthetic_attention.py`. **Requirement**: Must validate that each row contains `mean`, `var`, `sparsity`, `outlier_magnitude`, and `scaling_factor`. **Dependency**: T017a. **Deliverable**: Validation logic.
- [ ] T017a2 [US1] Execute data generation script and assert count == 10000. **Output**: `data/generated/static_matrices.parquet`. **Requirement**: Must assert **10000** rows in output. **Dependency**: T017a, T017a1. **Deliverable**: Generated dataset.
- [ ] T017b [US1] Implement ground-truth label computation function `compute_scaling_factor(matrix: np.ndarray, epsilon: float) -> float` in `code/data_generation/synthetic_attention.py`. **Requirement**: Must use the `SingleStepSinkhornSolver` from T016 in **single-step mode** (no state accumulation). **Requirement**: Must process each matrix independently. **Requirement**: Must handle non-convergence by raising an exception or returning NaN. **Deliverable**: A function that outputs a single scalar label per matrix.
- [ ] T017c1 [US1] Execute data generation script to produce a substantial set of synthetic attention matrices. **Output**: `data/generated/static_matrices.parquet`. **Dependency**: T017b. **Deliverable**: Execution of script.
- [ ] T017c2 [US1] Verify the count matches the configuration (10000). **Requirement**: Must assert **10000** rows in output. **Dependency**: T017c1. **Deliverable**: Verification report.
- [ ] T019 [US1] Implement data serialization (Parquet/JSON) with checksums for generated dataset in `code/data_generation/utils.py`. **Deliverable**: Serialization logic with checksums.
- [ ] T021 [US1] Add logging for data generation progress and solver failures in `code/data_generation/utils.py`. **Deliverable**: Logging implementation.
- [ ] T021b [US1] Implement verification for Sinkhorn solver non-convergence: skip or flag instances in `code/data_generation/synthetic_attention.py`. **Requirement**: Must not produce NaN labels. Must explicitly implement 'skip or flag' mechanism as per Spec Edge Cases. **Dependency**: T017b. **Deliverable**: Non-convergence handling logic.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (N matrices + ground truth labels generated)

---

## Phase 4: User Story 2 - Train and Evaluate the Static Prior Model (Priority: P2)

**Goal**: Train a lightweight MLP on CPU to map input attention moments (mean, variance) to ground-truth scaling factors, and evaluate against a closed-form baseline.

**Independent Test**: Can be fully tested by training the model on the training split and reporting the Mean Squared Error (MSE) on the test split. If the MSE is below a specific threshold, the mapping is considered learnable.

### Implementation for User Story 2

- [ ] T022 [P] [US2] Define a multi-layer perceptron (MLP) model architecture with **statistical moment features** (mean, variance) in `code/model_training/mlp_model.py`. **Note**: Implements Spec FR-002 (2 moments). **Constraint**: Must use a set of inputs (mean, variance) as per Spec FR-002.
- [ ] T023 [US2] Implement training loop with MSE loss, CPU-only execution, and epoch logging in `code/model_training/train.py`. **Output**: `data/models/mlp_weights.pt`, `data/metrics/training_log.csv`.
- [ ] T024 [US2] Implement closed-form baseline predictor (s = 1/variance) in `code/model_training/baselines.py`. **Deliverable**: Baseline predictor implementation.
- [ ] T026 [US2] Save trained model weights and training metrics to `data/` artifacts in `code/model_training/train.py`. **Deliverable**: Saved model and metrics.
- [ ] T035a [P] [US3] Implement **Out-of-Distribution (OOD) Detection** mechanism in `code/simulation/ood_detector.py`. **Requirement**: Must compute a statistical distance metric (e.g., Mahalanobis distance) between input matrix moments and training distribution moments. **Note**: The specific metric is a **design choice**; any valid OOD detection mechanism suffices to satisfy the spec's "graceful failure" requirement. **Output**: A boolean flag `is_ood` and a confidence score. **Dependency**: T022 (trained model moments).
- [ ] T035b [US3] Implement edge case handler for extreme outlier magnitudes in `code/simulation/autoregressive_loop.py`. **Requirement**: Must implement graceful fallback to KVarN (as per Spec Edge Cases: Extreme Outlier Magnitudes) **only if** `is_ood` is true (from T035a) or if a simple threshold is exceeded. **Requirement**: This task requires the **integrated execution path** of T016b (KVarN) and T022 (Static) within T027d to be functional. **Dependency**: T035a, T027d. **Deliverable**: Fallback logic implementation.
- [ ] T035c [US2] Implement comparison logic for MLP vs. closed-form baseline MSE in `code/analysis/stats.py`. **Output**: `data/metrics/baseline_comparison.json`. **Requirement**: Must verify if MLP captures non-trivial relationships beyond identity (FR-009). **Dependency**: T022, T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Model trained and baseline comparison ready)

---

## Phase 5: User Story 3 - Simulate Long-Horizon Generation and Measure Latency/Accuracy Trade-off (Priority: P3)

**Goal**: Run a simulated autoregressive generation loop replacing the KVarN optimizer with the trained static prior, measuring accumulated KL-divergence and per-token latency.

**Independent Test**: Can be fully tested by running the simulation loop twice (once with KVarN optimizer, once with static prior) and comparing the final accumulated KL-divergence and average wall-clock time per token.

### Implementation for User Story 3

- [ ] T027d [US3] Implement **Unified Autoregressive Simulation Runner** in `code/simulation/autoregressive_loop.py`. **Requirement**: Must execute **1000 steps** (Source: Constitution Principle VI). **Input**: `SimulationState` from T006. **Requirement**: Must explicitly accumulate KL-divergence *per step* within the loop and store it in the state to satisfy FR-004 and Constitution Principle VI. **Requirement**: Must support switching between 'Static Prior' and 'original KVarN method (SequentialSinkhornSolver)' modes within the **same execution pass** using a shared random seed sequence to ensure valid pairing for FR-006. **Requirement**: Must output per-run JSON files containing `final_accumulated_kl` AND `full_trajectory` (list of per-step errors). **Output**: `data/simulation/run_XXX_results.json`. **Dependency**: T016b, T022, T035a. **Deliverable**: Unified engine that runs both modes sequentially with identical seeds.
- [ ] T028 [US3] Implement KL-divergence accumulation logic comparing **quantized output distribution** vs **full-precision distribution** in `code/simulation/kl_divergence.py`. **Requirement**: Must store the full per-step error trajectory (sequence of errors) for each step of the 1,000-step simulation to satisfy Constitution Principle VI. **Requirement**: Must explicitly measure between quantized and full-precision distributions. **Dependency**: T027d.
- [ ] T030a [P] [US3] Implement `code/simulation/batch_runner.py` to execute multiple independent simulation runs. **Output**: Script `batch_runner.py`.
- [ ] T030b [US3] Execute `batch_runner.py` to generate 30 independent simulation runs. **Output**: `data/simulation/run_001.json` through `data/simulation/run_030.json`. **Requirement**: Must use a base seed with offsets (seed + i) for reproducibility. **Requirement**: Each run must be a **1000-step** simulation (Source: Constitution Principle VI). **Requirement**: Each run file must contain both Static and KVarN results paired by seed. **Dependency**: T027d. **Deliverable**: Execution of batch runner.
- [ ] T030b-verify [US3] Verify 30 files exist and contain required fields. **Output**: Verification report. **Requirement**: A corpus of files must exist to support the study.. **Dependency**: T030b. **Deliverable**: Verification report.
- [ ] T030c1 [US3] Implement aggregation script to combine the 30 JSON run files into `data/simulation/accumulated_kl_divergence.csv`. **Output**: `data/simulation/accumulated_kl_divergence.csv`. **Schema**: Columns `run_id`, `method`, `final_accumulated_kl`, `full_trajectory` (JSON string or list). **Requirement**: Must derive the final scalar value from the **1000-step** runs AND preserve the full trajectory for analysis. **Dependency**: T030b. **Deliverable**: Aggregation logic.
- [ ] T030c2 [US3] Execute aggregation script. **Output**: `data/simulation/accumulated_kl_divergence.csv`. **Dependency**: T030c1. **Deliverable**: Execution of script.
- [ ] T030c3 [US3] Verify output CSV. **Output**: Verification report. **Requirement**: Must assert CSV contains data for multiple runs and trajectories. **Dependency**: T030c2. **Deliverable**: Verification report.
- [ ] T032 [US3] Implement theoretical lower bound calculation using the analytical noise model formula $\Delta^2/12$ (where $\Delta$ is the **quantization interval derived from the simulation's quantization scheme**) in `code/analysis/stats.py`. **Output**: `data/analysis/theoretical_lower_bound.json`. **Requirement**: Must include a derivation artifact (comment or docstring) explaining the formula. **Requirement**: Must explicitly reference the **1000-step** horizon for consistency. (Dependency for US3 validation)
- [ ] T025 [US3] Implement full sensitivity analysis logic for epsilon floor sweep in `code/analysis/stats.py` (Validates normalization logic for US2/US3). **Input**: Configured epsilon values (from T005b) and simulation results from T030b. **Output**: `data/analysis/epsilon_sensitivity.json`. **Requirement**: Must calculate and report the **accumulated_kl_divergence_error_rate** (primary metric) and **variation_rate** (secondary derivative metric) for each epsilon step to satisfy Spec FR-007 ("report how... varies"). **Dependency**: T005b, T030b. **Note**: While this runs after the full batch, it validates the epsilon choice for future runs and reports on the robustness of the current run's configuration.
- [ ] T031 [US3] Implement and run statistical significance test (paired t-test, n=30 runs) on the **final accumulated KL-divergence** in `code/analysis/stats.py`. **Input**: `data/simulation/accumulated_kl_divergence.csv` (which contains `full_trajectory`). **Output**: `data/simulation/t_test_results.json`. **Requirement**: Pairing must be between static prior and KVarN results from the same run index (run_XXX_static vs run_XXX_kvarn). **Requirement**: The scalar value used for the t-test MUST be the **sum of the per-step errors** recorded in T028 to ensure the 'accumulation' requirement is met. **Requirement**: Must read and compare the full per-step error trajectory from the CSV to satisfy Constitution Principle VI. **Requirement**: Must explicitly mandate that input data (from T030c2) must contain *both* the static and KVarN results for *each* of the 30 seeds. **Dependency**: T030c2, T032.

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
 - T030b (30 runs) must complete before T030c (CSV aggregation) and T025 (Sensitivity).
 - T030c (CSV aggregation) must complete before T031 (t-test).
 - T032 (Theoretical Lower Bound) must complete before T031 (t-test).
 - T025a (Pilot) must complete before T030b.

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
- **Crucial**: All data generation (T017a) must use real mathematical models for static distributions (mean, variance, sparsity, outliers), not random fabrication, to satisfy FR-001.
- **Crucial**: Dataset size for T017c is read from config, not hardcoded, to allow runtime adjustment, but must assert **10000** rows for MVP.
- **Crucial**: T027d must isolate optimization overhead by running both modes with the same seed sequence for valid pairing.
- **Crucial**: T030b must produce exactly 30 files (run_001.json to run_030.json) via `batch_runner.py` using seed offsets.
- **Crucial**: T031 must perform t-test on the **final scalar** accumulated KL-divergence, not per-step error, with pairing by run index, using input from T030c2, and must store the full trajectory.
- **Crucial**: T005b must be implemented before T025 to ensure the epsilon sweep values are available for sensitivity analysis.
- **Crucial**: T032 must be implemented before T031 to ensure the theoretical lower bound is available for comparison in the statistical analysis.
- **Crucial**: T025 is placed in Phase 5 to ensure simulation results are available for sensitivity analysis, but depends on T005b for configuration.
- **Crucial**: T025 must output `accumulated_kl_divergence_error_rate` as the primary metric and `variation_rate` as secondary to satisfy FR-007.
- **Crucial**: T035a and T035b implement a design choice (Mahalanobis distance) to satisfy the "graceful failure" requirement; the specific metric is not mandated by the spec.
- **Crucial**: The simulation horizon is fixed per Constitution Principle VI. (see T027d, T030b, T031).