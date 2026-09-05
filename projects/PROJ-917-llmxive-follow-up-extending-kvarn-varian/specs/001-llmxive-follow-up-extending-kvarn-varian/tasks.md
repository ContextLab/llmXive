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

- [X] T001a [P] Initialize `code/` directory and subdirectories. **Action**: Execute `mkdir -p code/{data_generation,models,simulation,analysis,utils}`. **Verification**: `test -d code && test -d code/data_generation && test -d code/models && test -d code/simulation && test -d code/analysis && test -d code/utils`. **Deliverable**: `code/` directory tree matching plan.md schema.
- [X] T001b [P] Initialize `data/` directory structure including `raw`, `processed`, and `results`. **Action**: Execute `mkdir -p data/{raw, processed, results}`. **Verification**: `test -d data/raw && test -d data/processed && test -d data/results`. **Deliverable**: `data/` directory tree matching plan.md schema.
- [X] T001c [P] Initialize `tests/` directory structure. **Action**: Execute `mkdir -p tests/test_data_generation tests/test_model_training tests/test_simulation` and `touch tests/__init__.py tests/test_data_generation/__init__.py tests/test_model_training/__init__.py tests/test_simulation/__init__.py`. **Verification**: `test -f tests/__init__.py`. **Deliverable**: `tests/` directory tree with `__init__.py` files.
- [X] T001d [P] Initialize project state file. **Action**: Execute `mkdir -p state/projects` and create `state/projects/PROJ-917-llmxive-follow-up-extending-kvarn-varian.yaml` with content: `artifact_hashes: {}`. **Verification**: `test -f state/projects/PROJ-917-llmxive-follow-up-extending-kvarn-varian.yaml`. **Deliverable**: Initial state YAML file.
- [X] T001e [P] Initialize Python 3.x project with pinned `requirements.txt`. **Action**: Create `requirements.txt` with `numpy`, `scipy`, `torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu`, `scikit-learn`, `pandas`, `pyarrow`, `pytest`, `matplotlib`. **Verification**: `cat requirements.txt | grep "torch==2.1.0+cpu" && grep "download.pytorch.org"`. **Deliverable**: `requirements.txt` file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [X] T005b [P] [US3] [FR-007] Define initial epsilon sweep values in `code/config.py`. **Action**: Define constant `EPSILON_SWEEP_VALUES` containing a range of small magnitudes spanning multiple orders of magnitude (e.g., `[1e-8, 1e-6, 1e-4]`). **Verification**: Import `config` and assert `EPSILON_SWEEP_VALUES` matches the list. **Deliverable**: Constant definition in `code/config.py`. **Note**: This provides the hardcoded defaults required to break circular dependencies.
- [X] T006 [P] [US3] Implement `SimulationState` dataclass in `code/simulation/state.py` with fields: `accumulated_kl: float`, `current_error_state: dict`, `step_index: int`, `full_trajectory: list[float]`. This module MUST be imported by T027d.
- [X] T007a [P] [US1] Implement `AttentionMatrix` dataclass in `code/entities.py`. **Schema**: 128x128 matrix (float32), mean (float32), variance (float32), sparsity (float32 ratio of zero elements calculated as `count(zeros) / total_elements`), outlier_magnitude (float32). **Note**: Aligns with Spec Key Entities.
- [X] T007b [P] [US1] Implement `ScalingFactor` dataclass in `code/entities.py`. **Schema**: Scalar value, derivation_method.
- [X] T008 [P] [US1] Implement global random seed management in `code/utils/seeds.py` with a `set_global_seed(seed: int)` function that calls `np.random.seed`, `torch.manual_seed`, and `random.seed`. **Verification**: Run `main.py` twice with the same seed and check output checksums match.
- [X] T009 [P] [US1] Setup environment configuration management in `code/config.py` with a `Config` dataclass containing `CPU_ONLY=True`, `EPSILON_FLOOR=1e-6`, `RANDOM_SEED`, `NUM_MATRICES=None` (default '[deferred]' per spec deferral, researcher MUST set before execution), `SIMULATION_STEPS=None` (default '[deferred]' per spec deferral, researcher MUST set before execution), `NUM_RUNS=30`. **Verification**: Load `config.py` and assert defaults. **Note**: Explicitly enforces [deferred] matrices per FR-001; the exact count is a research decision.
- [X] T009b [P] [US3] [FR-008] Define quantization constants in `code/config.py`. **Action**: Define `QUANTIZATION_MAX` and `QUANTIZATION_MIN` for Uniform INT8 Quantization. **Verification**: Import `config` and assert values are defined. **Deliverable**: Constants definition in `code/config.py`. **Note**: Required by T032_base for quantization logic.
- [X] T016 [P] [US1] Implement `SingleStepSinkhornSolver` class in `code/data_generation/sinkhorn_solver.py`. **Signature**: `solve(matrix: np.ndarray, epsilon: float) -> float`. **Requirement**: Must compute a **single** ground-truth scaling factor for an **independent** static matrix. **Requirement**: Must NOT maintain cumulative state. **Requirement**: Must handle non-convergence by defining a custom exception class `SinkhornConvergenceError` in the same file and raising it if convergence fails. **Deliverable**: A solver that outputs a single scalar label per matrix.
- [X] T010 [P] [US1] Implement unit test for moment extraction (mean, variance, sparsity, outlier_magnitude) and epsilon handling in `tests/test_data_generation.py`. **Deliverable**: A test file that verifies `apply_epsilon_floor` and moment extraction logic for **mean, variance, sparsity, and outlier_magnitude**. **Constraint**: Must validate extraction of all fields defined in Spec Key Entities. **Dependency**: T016 (requires T016 implementation or mocking). **Mock Definition**: Define a mock `SingleStepSinkhornSolver` class with a `solve` method returning a fixed float (e.g., 1.0) to allow test execution without the real solver. **Note**: Removed [P] tag due to semantic dependency on T016.
- [X] T011 [P] [US1] Implement unit test for SingleStepSinkhorn solver convergence and edge cases in `tests/test_data_generation.py`. **Deliverable**: A test file that verifies `SingleStepSinkhornSolver` handles near-zero variance (threshold: 1e-6) and non-convergence (raises `SinkhornConvergenceError`). **Requirement**: Must include specific test functions `test_near_zero_variance` and `test_non_convergence_exception`. **Dependency**: T016.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Ground-Truth Scaling Factors for Synthetic Attention Matrices (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic attention matrices (128x128) with controlled sparsity and outlier magnitudes, and compute ground-truth scaling factors using the KVarN Sinkhorn optimizer.

**Independent Test**: Can be fully tested by running the data generation script on a small subset and verifying that the output file contains valid scaling factors, that the distribution matches drift parameters, and that computation time per matrix matches the expected overhead of the SingleStepSinkhorn solver.

### Implementation for User Story 1

- [X] T019a_jsonl [P] [US1] Implement data serialization logic (JSONL format) in `code/data_generation/utils.py`. **Deliverable**: Serialization function using `pandas` or `json` to write `data/raw/synthetic_attention_matrices.jsonl`. **Note**: Must precede T017c.
- [X] T019b [P] [US1] Implement checksum generation (SHA-256) for generated dataset in `code/data_generation/utils.py`. **Deliverable**: Checksum function that writes `data/raw/synthetic_attention_matrices.jsonl.sha256`. **Note**: Must precede T017c.
- [X] T021 [P] [US1] Add logging for data generation progress and solver failures in `code/data_generation/utils.py`. **Deliverable**: Logging implementation. **Note**: Must precede T017c to ensure logging is available.
- [X] T017c [US1] Implement and execute the **Unified Data Generation and Labeling** script in `code/data_generation/synthetic_attention.py`. **Requirement**: Must generate a number of synthetic matrices equal to `config.NUM_MATRICES` (which MUST be set by the researcher before execution, default is '[deferred]'). **Requirement**: Must compute ground-truth scaling factors using `SingleStepSinkhornSolver` (T016) **during** the generation loop. **Requirement**: Must write a single output file `data/raw/synthetic_attention_matrices.jsonl` containing **both** the matrix data (mean, var, sparsity, outlier) **and** the computed `scaling_factor`. **Requirement**: Must handle non-convergence by skipping or flagging instances (do not produce NaN labels). **Verification**: Assert count matches `config.NUM_MATRICES` and file exists with SHA-256 checksum. **Dependency**: T016, T019a_jsonl, T019b, T021. **Deliverable**: A complete dataset with matrices and labels. **Note**: The exact count is deferred to the research phase; the researcher MUST set `NUM_MATRICES` in `config.py` before running.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (synthetic matrices + ground truth labels generated)

---

## Phase 4: User Story 2 - Train and Evaluate the Static Prior Model (Priority: P2)

**Goal**: Train a lightweight MLP on CPU to map input attention moments (mean, variance) to ground-truth scaling factors, and evaluate against a closed-form baseline.

**Independent Test**: Can be fully tested by training the model on the training split and reporting the Mean Squared Error (MSE) on the test split. If the MSE is below a specific threshold, the mapping is considered learnable.

### Implementation for User Story 2

- [X] T022 [P] [US2] [FR-009] Define a multi-layer perceptron (MLP) model architecture with **statistical moment features** (mean, variance) in `code/model_training/mlp_model.py`. **Requirement**: Architecture: Input (mean, variance) -> Hidden layer with a moderate number of neurons and ReLU activation -> Hidden layer with a moderate number of neurons and ReLU activation -> Output (single scalar). **Requirement**: Use Xavier initialization. **Requirement**: Use MSE loss and Adam optimizer. **Verification**: Instantiate model and assert layer dimensions match specification. **Note**: Implements Spec FR-002 (2 moments). **Constraint**: Must use a fixed 2-feature input (mean, variance) as per Spec FR-002.
- [X] T023 [US2] [FR-009] Implement training loop with MSE loss, CPU-only execution, and epoch logging in `code/model_training/train.py`. **Verification**: Verify `train.py` exists and is not truncated. **Output**: `data/models/mlp_weights.pt`, `data/metrics/training_log.csv`. **Requirement**: Verify `mlp_weights.pt` is a valid torch state_dict (non-zero size) and `training_log.csv` contains a header and at least one epoch row. **Deliverable**: Trained model and metrics.
- [X] T024 [US2] Implement closed-form baseline predictor (s = 1/variance) in `code/model_training/baselines.py`. **Deliverable**: Baseline predictor implementation.
- [X] T026 [US2] Save trained model weights and training metrics to `data/` artifacts in `code/model_training/train.py`. **Deliverable**: Saved model and metrics.
- [X] T035c [US2] [FR-009] Implement comparison logic for MLP vs. closed-form baseline MSE in `code/analysis/stats.py`. **Output**: `data/metrics/baseline_comparison.json`. **Requirement**: Must verify if MLP captures non-trivial relationships beyond identity (FR-009) by including a p-value (from paired t-test) or ratio in the output. **Schema**: `{"mlp_mse": float, "baseline_mse": float, "p_value": float, "improvement_ratio": float}`. **Requirement**: Must use a paired t-test to calculate the p-value. **Dependency**: T022, T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Model trained and baseline comparison ready)

---

## Phase 5: User Story 3 - Simulate Long-Horizon Generation and Measure Latency/Accuracy Trade-off (Priority: P3)

**Goal**: Run a simulated autoregressive generation loop replacing the KVarN optimizer with the trained static prior, measuring accumulated KL-divergence and per-token latency.

**Independent Test**: Can be fully tested by running the simulation loop twice (once with KVarN optimizer, once with static prior) and comparing the final accumulated KL-divergence and average wall-clock time per token.

### Implementation for User Story 3

- [X] T035a [US3] [Edge Cases] Implement **Out-of-Distribution (OOD) Detection** mechanism in `code/simulation/ood_detector.py`. **Requirement**: Must explicitly implement the epsilon floor check and outlier threshold logic defined in Spec Edge Cases. **Requirement**: Must compute a statistical distance metric using a **Statistical threshold** (e.g., 3 standard deviations) based on training set std between input matrix moments and training distribution moments. **Output**: A boolean flag `is_ood` and a confidence score (optional, for graceful failure). **Requirement**: Must skip or flag the instance if `is_ood` is true (do not crash). **Verification**: Verify `code/simulation/ood_detector.py` exists and contains functions `is_ood` and `get_confidence`. **Dependency**: T022 (trained model moments). **Note**: T035a is MANDATORY for T027d to satisfy spec Edge Cases; T027d must implement basic handling independently if T035a is not used (but T035a is required).
- [X] T035b [US3] [Edge Cases] Implement generic edge case handler for extreme outlier magnitudes in `code/simulation/autoregressive_loop.py`. **Requirement**: Must implement graceful failure (skip/flag) for extreme outliers **only if** `is_ood` is true (from T035a) or if a simple threshold is exceeded. **Requirement**: This task requires the **integrated execution path** of T016 (SingleStepSinkhorn) and T022 (Static) within T027d to be functional. **Dependency**: T035a, T016. **Deliverable**: Fallback logic implementation. **Note**: Must mandate skip/flag as per spec.
- [X] T009_calc [P] [US3] [FR-008] Implement `code/analysis/theoretical_lower_bound.py` to **calculate the theoretical lower bound** of KL-divergence. **Requirement**: Must derive the analytical lower bound based on the quantization noise model defined in T032_base (Uniform INT8). **Formula**: `KL_lower_bound = 0.5 * log2(2 * pi * e * sigma_q^2)` where `sigma_q^2 = (Delta^2) / 12` and `Delta = (QUANTIZATION_MAX - QUANTIZATION_MIN) / 255`. **Requirement**: Must output `data/analysis/theoretical_lower_bound.json` containing the scalar bound value and the derivation formula. **Requirement**: This artifact is required for FR-008 and SC-002 to avoid circular validation. **Dependency**: T032_base. **Deliverable**: Theoretical lower bound artifact.
- [X] T005a [US3] [FR-007] Implement **Direct Sensitivity Analysis** in `code/analysis/stats.py`. **Input**: `EPSILON_SWEEP_VALUES` from T005b. **Output**: `data/analysis/epsilon_sensitivity.json`. **Schema**: `{epsilon: float, accumulated_kl_divergence_error_rate: float, variation_rate: float}`. **Requirement**: Must iterate over each epsilon value, execute the simulation loop (T027d), and report the **accumulated_kl_divergence_error_rate** and **variation_rate** for each epsilon step to satisfy Spec FR-007. **Requirement**: The `error_rate` MUST be defined as the **maximum** of the relative deviations from the **Theoretical Lower Bound** (from T009_calc) AND the **KVarN Baseline** (from T027d). **Requirement**: Must generate the final report/plot of the variation rate. **Dependency**: T027d, T009_calc. **Note**: Replaces the multi-stage pilot workflow with a direct sweep.
- [X] T027d [US3] Implement **Unified Autoregressive Simulation Runner** in `code/simulation/autoregressive_loop.py`. **Requirement**: Must execute a configurable number of steps equal to `config.SIMULATION_STEPS` (which MUST be set by the researcher before execution, default is '[deferred]'). **Input**: `SimulationState` from T006. **Requirement**: Must explicitly accumulate KL-divergence *per step* within the loop and store the **per-step error** in the state to satisfy FR-004 and Constitution Principle VI. **Requirement**: Must support switching between 'Static Prior' and 'original KVarN method (SingleStepSinkhornSolver)' modes within the **same execution pass** using a shared random seed sequence to ensure valid pairing for FR-006. **Requirement**: Must output per-run JSON files containing `final_accumulated_kl` AND `full_trajectory` (list of per-step errors). **Requirement**: The `full_trajectory` MUST be serialized as a **JSON array of floats** representing the **per-step KL-divergence errors**. **Requirement**: Must handle basic edge cases (fail-fast/skip) without requiring full OOD logic (T035a) to be complete first. **Output**: `data/results/simulation_run_{:03d}.json`. **Dependency**: T016, T022, T032_base, T035a, T035b. **Deliverable**: Unified engine that runs both modes sequentially with identical seeds.
- [X] T028 [US3] Implement KL-divergence accumulation logic comparing **quantized output distribution** vs **full-precision distribution** in `code/simulation/kl_divergence.py`. **Requirement**: Must store the full per-step error trajectory (sequence of errors) for each step of the simulation to satisfy Constitution Principle VI. **Requirement**: Must explicitly measure between quantized and full-precision distributions. **Dependency**: T027d. **Note**: The simulation horizon is defined by `config.SIMULATION_STEPS` (default 1,000 if set by researcher).
- [X] T030a [P] [US3] Implement `code/simulation/batch_runner.py` to execute multiple independent simulation runs. **Output**: Script `batch_runner.py`.
- [X] T030b [US3] Execute `batch_runner.py` to generate a sufficient number of independent simulation runs. **Action**: Execute with n=30 (per FR-006) using pattern `simulation_run_{:03d}.json`. **Algorithm**: For each run `i` from 0 to 29, use `base_seed + i` as the random seed (where `base_seed` is `config.RANDOM_SEED`). **Output**: `data/results/simulation_run_001.json` through `data/results/simulation_run_030.json`. **Requirement**: Must use a base seed with offsets (seed + i) for reproducibility. **Requirement**: Each run must be of `config.SIMULATION_STEPS` (default 1,000 if set by researcher). **Requirement**: Each run file must contain both Static and KVarN results paired by seed. **Requirement**: Source for n=30: Standard statistical power analysis for paired t-tests (target power >= 0.8) and Spec FR-006. **Verification**: Verify that 30 files exist using glob pattern `simulation_run_{:d}.json`. **Dependency**: T027d. **Deliverable**: Execution of batch runner.
- [X] T030b-verify [US3] [FR-006] [SC-004] Verify 30 files exist and contain required fields. **Output**: Verification report. **Requirement**: A corpus of files must exist to support the study. **Dependency**: T030b. **Deliverable**: Verification report.
- [X] T030c1 [US3] Implement aggregation script to combine the 30 JSON run files into `data/results/accumulated_kl_divergence.csv`. **Output**: `data/results/accumulated_kl_divergence.csv`. **Schema**: Columns `run_id`, `method`, `final_accumulated_kl`, `full_trajectory` (JSON stringified array). **Requirement**: Must derive the final scalar value from the simulation runs AND preserve the full trajectory for analysis. **Requirement**: Must ensure the CSV structure preserves the pairing (Static vs KVarN) for each run index. **Requirement**: The `full_trajectory` column MUST contain a valid JSON stringified array of floats representing per-step errors. **Dependency**: T030b. **Deliverable**: Aggregation logic.
- [X] T030c2 [US3] Execute aggregation script. **Output**: `data/results/accumulated_kl_divergence.csv`. **Verification**: Verify CSV contains data for 30 runs and trajectories, and that pairing is preserved. **Requirement**: Must verify that the `full_trajectory` column exists and contains valid JSON arrays for all rows. **Dependency**: T030c1. **Deliverable**: Execution of script.
- [X] T030c3 [US3] Verify output CSV. **Output**: Verification report. **Requirement**: Must assert CSV contains data for multiple runs and trajectories. **Dependency**: T030c2. **Deliverable**: Verification report.
- [X] T032_bound [US3] [FR-008] Perform comparison against the Theoretical Lower Bound. **Input**: `data/results/accumulated_kl_divergence.csv` and `data/analysis/theoretical_lower_bound.json`. **Output**: `data/analysis/bound_comparison.json`. **Requirement**: Must calculate the difference between the static prior's accumulated KL-divergence and the theoretical lower bound. **Requirement**: Must report the gap as a percentage of the bound to validate FR-008. **Requirement**: Aligns with Plan.md Phase 4 (T010) for independent validation. **Dependency**: T030c2, T032_base, T009_calc. **Note**: T032_base provides the quantization logic; T009_calc provides the bound value.
- [X] T031 [US3] [FR-006] Implement and run statistical significance test (paired t-test, n=30 runs) on the **final accumulated KL-divergence** in `code/analysis/stats.py`. **Input**: `data/results/accumulated_kl_divergence.csv`. **Action**: Read `full_trajectory` (list of per-step errors) from CSV -> Sum trajectory to scalar `final_accumulated_kl` -> Run paired t-test on the scalars with n=30. **Output**: `data/results/t_test_results.json`. **Requirement**: Pairing must be between static prior and KVarN results from the same run index (run_XXX_static vs run_XXX_kvarn). **Verification**: Validate that the CSV structure preserves the pairing before running the test. **Requirement**: The scalar value used for the t-test MUST be the **sum of the per-step errors** recorded in T028. **Requirement**: Must explicitly state that the test is run on scalars, not trajectories. **Requirement**: The sample size 'n' is exactly 30 (per FR-006). **Requirement**: Source for n=30: Standard statistical power analysis for paired t-tests (target power >= 0.8) and Spec FR-006. **Dependency**: T030c2.
- [X] T042 [P] [US3] Implement explicit runtime profiling for per-token latency in `code/simulation/autoregressive_loop.py` to satisfy FR-005 and SC-003. **Requirement**: Must use `time.perf_counter()` for high-resolution timing around the quantization and scaling step. **Requirement**: Must measure wall-clock time per single token generation step (forward pass + quantization). **Requirement**: Must calculate and output `latency_reduction_ms` (difference between KVarN and Static Prior) to the run JSON file. **Dependency**: T027d.
- [X] T033 [US3] Generate final report and plots. **Input**: Results from T031 (t-test), T032_bound (bound comparison), T005a (sensitivity), T042 (latency). **Output**: `data/results/final_report.md`. **Requirement**: Must combine results, visualize the comparison (including the bound comparison from T032_bound), and summarize findings. **Dependency**: T031, T032_bound, T005a, T042.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034a [P] Update `README.md` with installation instructions and quickstart guide.
- [X] T034b [P] Update `docs/quickstart.md` with step-by-step execution guide.
- [X] T034c [P] Update `docs/api.md` with module interface definitions.
- [X] T035a_refactor [P] Refactor `code/data_generation/` modules for clarity and modularity.
- [X] T035b_refactor [P] Refactor `code/simulation/` modules for clarity and modularity.
- [X] T035c_refactor [P] Refactor `code/analysis/` modules for clarity and modularity.
- [X] T036a [P] [US1] Performance optimization for Sequential Sinkhorn solver: Vectorize operations with NumPy. **Action**: Refactor `code/data_generation/sinkhorn_solver.py` to use NumPy vectorized operations. **Target**: Reduce runtime per matrix by [deferred]. **Dependency**: T016.
- [X] T036b [P] [US1] Performance optimization for Sequential Sinkhorn solver: Use SciPy sparse matrices where applicable. **Action**: Refactor `code/data_generation/sinkhorn_solver.py` to use SciPy sparse matrices. **Target**: Reduce runtime per matrix by [deferred]. **Dependency**: T016.
- [X] T037a [P] [Edge Cases] Implement unit test `test_nan_handling` in `tests/test_data_generation.py`.
- [X] T037b [P] [Edge Cases] Implement unit test `test_extreme_outlier` in `tests/test_data_generation.py`.
- [X] T037c [P] [Edge Cases] Implement unit test `test_epsilon_floor` in `tests/test_data_generation.py`.
- [X] T038a [P] Run `quickstart.md` validation to ensure reproducible execution. **Action**: Execute `python -m code.main` with default config. **Verification**: Command exits with code 0 and generates `data/results/final_report.md`. **Deliverable**: Validation report.
- [X] T038b [P] Verify `quickstart.md` outputs. **Action**: Check existence of `data/results/final_report.md` and `data/` artifacts. **Verification**: Assert files exist. **Deliverable**: Verification report.
- [X] T039a [P] Compute SHA-256 checksums for all files in `data/`. **Action**: Execute `sha256sum data/**/* > data/checksums.txt`. **Verification**: Command exits with 0. **Deliverable**: Checksum file.
- [X] T039b [P] Verify all artifacts are checksummed and immutable. **Action**: Compare `data/checksums.txt` with `state/projects/PROJ-917-llmxive-follow-up-extending-kvarn-varian.yaml` `artifact_hashes` map. **Verification**: Assert all hashes match. **Deliverable**: Verification report.
- [X] T040 [P] Finalize `data-model.md` with updated entity definitions for `AttentionMatrix` and `SimulationState`. (Note: Removed 'AttentionTrajectory' to align with spec).
- [X] T041 [P] Update `contracts/` directory with interface definitions for `SingleStepSinkhornSolver`, `StaticPriorModel`, and `Quantizer`.
- [X] T043 [P] [US2] Add explicit logging of training hyperparameters (learning rate, batch size, epochs) to `data/metrics/training_log.csv` to ensure reproducibility per Constitution Principle I. **Requirement**: Must include a header row and a row for the final epoch. **Dependency**: T023.
- [X] T044 [P] [Edge Cases] Implement a "Data Generation Health Check" script in `code/data_generation/health_check.py` that validates the generated dataset for NaNs, infinite values, and reasonable distribution ranges before training begins. **Requirement**: Must fail loudly (exit code 1) if any anomalies are detected. **Dependency**: T017c.
- [X] T004 [P] Verify Python syntax for all `.py` files. **Action**: Execute `python -c "import glob, py_compile; files = glob.glob('code/**/*.py', recursive=True); [py_compile.compile(f, doraise=True) for f in files]"`. **Verification**: Command exits with 0. **Deliverable**: Verification report. **Dependency**: All code generation tasks complete.

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
 - T030b (30 runs) must complete before T030c (CSV aggregation) and T005a (Full Sensitivity).
 - T030c (CSV aggregation) must complete before T031 (t-test).
 - T032_bound (Theoretical Lower Bound) and T032_base (Quantizer) must complete before T033 (Report).
 - T005a (Direct Sensitivity) must complete before T033.
 - T035a (OOD Detection) and T035b (Edge Case Handler) are MANDATORY for T027d to satisfy spec Edge Cases.

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
- **Crucial**: The quantization logic (T032_base) MUST be implemented before T027d to satisfy FR-008 and Plan Phase 3/4 separation.
- **Crucial**: All data generation (T017c) must use real mathematical models for static distributions (mean, variance, sparsity, outliers), not random fabrication, to satisfy FR-001.
- **Crucial**: Dataset size for T017c is **[deferred]** (per FR-001), overriding the config default. The researcher MUST set `NUM_MATRICES` in `config.py` before execution.
- **Crucial**: T027d must isolate optimization overhead by running both modes with the same seed sequence for valid pairing.
- **Crucial**: T030b must produce exactly 30 files (simulation_run_001.json to simulation_run_030.json) via `batch_runner.py` using seed offsets (base_seed + i), where n=30 is mandatory (per FR-006 and standard power analysis).
- **Crucial**: T031 must perform t-test on the **final scalar** accumulated KL-divergence (sum of per-step errors), not per-step error, with pairing by run index, using input from T030c2. The sample size 'n' is exactly 30.
- **Crucial**: T005b must be implemented before T005a to ensure the epsilon sweep values are defined before the sensitivity analysis runs.
- **Crucial**: T032_base must be implemented before T027d to ensure the quantization logic is available for the simulation.
- **Crucial**: T032_bound must explicitly compare the results against the bound (generated by T009_calc) to satisfy FR-008.
- **Crucial**: T005a (Direct Sensitivity) must complete before T033; T005a outputs `accumulated_kl_divergence_error_rate` (defined as maximum deviation from bound and baseline) as the primary metric and `variation_rate` as secondary to satisfy FR-007.
- **Crucial**: T035a and T035b implement a 'skip/flag' mechanism to satisfy the "graceful failure" requirement; the specific metric is not mandated by the spec.
- **Crucial**: The simulation horizon is defined by **[deferred] steps** (see T027d, T028, T030b, T031). The researcher MUST set `SIMULATION_STEPS` in `config.py` before execution.
- **Crucial**: T042 must explicitly measure wall-clock time per token AND calculate the latency reduction to satisfy FR-005 and SC-003, ensuring the latency reduction claim is empirically grounded.
- **Crucial**: T043 ensures that the training process is fully reproducible by logging all hyperparameters, satisfying Constitution Principle I.
- **Crucial**: T044 acts as a gatekeeper for data quality, preventing the propagation of NaNs or outliers into the training and simulation phases.
- **Crucial**: T009_calc is mandatory to generate the theoretical lower bound required for FR-008 and T032_bound.
- **Crucial**: T035a and T035b are MANDATORY to satisfy spec Edge Cases regarding graceful failure for extreme outliers.