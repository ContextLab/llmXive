# Tasks: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

**Input**: Design documents from `/specs/001-llmxive-gam-symbolic-planner/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a-reqs [P] Create `requirements.txt` with pinned dependencies: `pybullet`, `torch==2.0.0+cpu --index-url https://download.pytorch.org/whl/cpu`, `cvxpy`, `diff-taichi`, `scipy`, `pandas`, `numpy`, `pytest`.
- [ ] T001a-gitignore [P] Create `.gitignore` file excluding `data/`, `__pycache__`, `*.pyc`, and environment files
- [ ] T001a-init [P] Create `code/__init__.py` and `tests/__init__.py`
- [ ] T001b [P] Create `code/`, `data/`, `tests/` directories
- [ ] T001c [P] Create `.gitkeep` files in all data subdirectories (`data/raw`, `data/generated`, `data/results`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 (`requirements.txt`: pybullet, torch (cpu, `--index-url https://download.pytorch.org/whl/cpu`), cvxpy, diff-taichi, scipy, pandas, numpy, pytest)
- [ ] T003 [P] Create `ruff.toml` and `.pre-commit-config.yaml` for linting and formatting
- [ ] T004 Setup data directory structure (`data/raw`, `data/generated`, `data/results`) and `.gitkeep` files
- [X] T005 [P] Implement `code/utils.py` with logging, deterministic seeding (numpy/torch), and SHA-256 hashing utilities
- [X] T006-frozen [P] **Implement** `code/gfm_wrapper.py` (Frozen Inference Mode) to **load frozen GFM weights** from `data/raw/gfm_weights.pt` (CPU-only, `eval()` mode) and **freeze all parameters**. **Requirement**: Must **fully implement** `encode`/`decode` methods (forward pass) to map 3D observations to latent space and latent vectors to 3D actions. **Constraint**: This wrapper MUST disable autograd (`torch.no_grad()`) to ensure it is used only for inference. **Input Shape**: `encode` takes `(batch, 3, N_points)`, outputs `(batch, D_latent)`. `decode` takes `(batch, D_latent)`, outputs `(batch, 3, N_points)`. **Output**: Functional `GFMWrapperFrozen` class ready for inference.
- [X] T006-diff [P] **Implement** `code/gfm_wrapper.py` (Differentiable Gradient Check Mode) to **load frozen GFM weights** from `data/raw/gfm_weights.pt`. **Requirement**: Must implement `encode`/`decode` methods that **enable autograd** (`requires_grad=True` on inputs) specifically for numerical gradient verification. This wrapper is used ONLY for T014b-fd-verify's gradient check. **Output**: Functional `GFMWrapperDiff` class for gradient verification.
- [X] T005-baseline-fetch [P] **Fetch and Validate** `data/raw/gfm_baseline.pt`. **Logic**: 1. Read `baseline_model_url` from `code/config.yaml`. 2. If URL is present and valid, fetch the file using `huggingface_hub.hf_hub_download` or `requests`. 3. Verify SHA-256 checksum against `data/raw/baseline_checksums.json`. 4. **If fetch fails or URL is missing**: Check for local file `data/raw/gfm_baseline.pt`. 5. If local file exists, use it. 6. If **neither** URL fetch nor local file exists, **attempt to instantiate a local baseline implementation** from `code/models/baseline_gam.py` (as per Plan Phase 0.4). If all fail, **EXIT WITH CODE 1** with a clear error message: "Baseline model URL not configured, local file missing, and local implementation unavailable. Cannot proceed with comparative analysis (FR-005)." **Constraint**: Do NOT generate synthetic weights. **Output**: Valid `data/raw/gfm_baseline.pt` or local implementation confirmation with checksum validation. **Note**: This task explicitly acquires the Baseline GAM weights required for FR-005, distinct from the GFM encoder/decoder weights used in the symbolic approach.
- [X] T007a [P] Create `code/config.yaml` defining experiment parameters: `topology_counts` (list of integers, default `[, 10]`), `timeout_limits` (configurable duration), `seed`, `trial_count` (100), `sim_fps` (default), `max_attempts` (default a sufficient sample size to ensure statistical power and representativeness), `stiffness_range` (default `[a lower bound, 0.5]`), `target_zone` (dict with `center` and `radius`), `baseline_model_url` (string, optional, URL for baseline weights), `MAX_TASKS` (integer, default 150, max tasks to generate before subset selection).
- [X] T007b [P] Implement `code/config.py` loader to parse `code/config.yaml` and expose parameters as a typed configuration object
- [X] T008 [P] **Implement** `.github/workflows/ci.yml` to match FR-004: Multi-core x86_64 runner, no GPU/CUDA, with a fixed timeout limit to constrain the duration of the experimental trial, ensuring environment matches the requirement.
- [X] T009a-fetch-stats [US1] [Depends on T007b] **Generate or Fetch** `data/raw/gam_reference_stats.json`. **Logic**: 1. **PRIORITY**: Attempt to **generate locally** by computing mean/covariance of latent vectors from a representative subset of the training set (or a synthetic proxy if the training set is inaccessible, but log this as a warning). 2. If local generation fails, **attempt to fetch** from `reference_stats_url` in `code/config.yaml`. 3. If both fail, **EXIT WITH CODE 1**. **Output**: Valid `data/raw/gam_reference_stats.json` with validation status. **Note**: This task prioritizes local generation to satisfy Plan Phase 1.4 requirements, ensuring FR-001 (zero overlap) can be verified without a hardcoded URL dependency.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Topology-Shift Test Set Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of manipulation tasks with novel kinematic chains and deformable materials using PyBullet, ensuring zero overlap with original GAM training data.

**Independent Test**: Run generation script; verify output contains valid physics states for a diverse set of distinct topologies; confirm checksum hash differs from original GAM metadata.

### Implementation for User Story 1

- [X] T008-manifest-gen [US1] [Depends on T009a-fetch-stats] **Generate or Load** `data/raw/training-topology-manifest.json` (Plan 0.1). **Logic**: 1. If a reference dataset is available, compute topology hashes and save to manifest. 2. If no reference exists, create a mock manifest with a placeholder hash. 3. Output `data/raw/training-topology-manifest.json`. **Requirement**: This artifact is required for FR-001's zero-overlap verification.
- [X] T008-drift-calib [US1] [Depends on T009a-fetch-stats] **Calculate** reference mean/covariance for latent drift detection (Plan 0.2). **Logic**: Read `data/raw/gam_reference_stats.json` (or training subset) and compute mean/covariance. **Output**: `data/raw/latent_drift_stats.json`.
- [X] T008-latent-validity [US1] [Depends on T006-frozen, T008-drift-calib] **Perform** preliminary test to verify frozen GFM encoder produces valid latents for novel topologies (Plan 0.3). **Logic**: Run encoder on a small subset of novel topologies and log validity. **Output**: `data/results/latent_validity_log.json`. **Constraint**: If latent drift is detected, log alert and flag for manual review (do NOT exit).
- [X] T009-gen-impl [US1] [Depends on T007a, T007b] **Implement** `code/data/generator.py` logic to generate a set of unique manipulation tasks (Plan 1.1). **Logic**: Generate novel kinematic chains and deformable materials using PyBullet. **Output**: `code/data/generator.py` and initial test set generation capability.
- [X] T009-gen-unified [US1] [Depends on T008-manifest-gen, T009-gen-impl] **Generate** a set of **at least 100 unique manipulation tasks** (FR-001, US-1). **Logic**: Generate novel topologies. **Constraint**:
 1. If N < 100, **EXIT WITH CODE 1**.
 2. If N >= 100, **use ALL generated tasks** (do not truncate to 100).
 3. **Output**: `data/generated/physics_states.json` containing N (>=100) unique physics states.
- [X] T009-verify-overlap [US1] [Depends on T008-manifest-gen, T009-gen-unified] **Verify** zero overlap against `data/raw/training-topology-manifest.json`. **Input**: `data/raw/training-topology-manifest.json`, `data/generated/physics_states.json`. **Logic**: Verify that none of the topology hashes exist in the manifest [UNRESOLVED-CLAIM: c_33156b9b — status=not_enough_info]. **Output**: `data/generated/unique_topology_ids.json`. **Constraint**: If overlap is detected, **EXIT WITH CODE 1**.
- [X] T009-serialize [US1] [Depends on T009-verify-overlap] **Serialize** validated unique physics states into `data/generated/physics_states.json` and `data/generated/latent_trajectory.csv`. **Requirement**: Output must capture full simulation state history including vertex positions for deformable objects at every timestep.
- [X] T010a [US1] [Depends on T009-serialize] **Extract** and serialize full physics simulation states (vertex positions for deformable objects, joint angles for kinematic chains) into `data/generated/physics_states.json`. **Schema**: `object_type` ('rigid'/'deformable'), `vertex_data` (list of floats), `joint_angles` (list of floats).
- [X] T011 [US1] Implement error handling for physics simulation failures in `code/data/generator.py`: handle specific failure modes (PyBullet `p.loadURDF` returns error, simulation step returns NaN); recovery mechanism (retry with exponential backoff: initial=1s, multiplier=2, max=5 retries), log to `data/results/errors.log` and skip trial; verification (unit test `test_crash_recovery` passes).
- [X] T013 [US1] Create `scripts/generate_test_set.py` to execute generation with configurable seeds
- [X] T009b-gt-traj [US1] [Depends on T009-serialize] **Generate Ground Truth Trajectories** via PyBullet (Plan 0.4). **Logic**: Select a diverse set of novel topologies from `data/generated/physics_states.json`. Run high-fidelity PyBullet simulation **without** the decoder to generate ground-truth positions/velocities for **solver validation**. **Output**: `data/generated/ground_truth_traj.json`.
- [X] T009b-gt-decoder [US1] [Depends on T009-serialize] **Generate Ground Truth States for Decoder Validation**. **Logic**: Select a diverse set of novel topologies from `data/generated/physics_states.json`. Run high-fidelity PyBullet simulation **without** the decoder to generate ground-truth positions/velocities for **decoder validation**. **Output**: `data/generated/ground_truth_decoder.json`. **Note**: This is the sole producer of this artifact.
- [X] T009-mock [US1] [P] **Generate Mock Data for Early Solver Testing**. **Logic**: Create synthetic topology tasks to allow T014-solver-impl and T016 to run independently of full US1 completion. **Requirement**: The schema MUST conform to `contracts/trial_log.schema.yaml`. Each entry must include a valid topology hash. **Output**: `data/generated/mock_topology_data.json` containing exactly 5 entries with valid topology hashes conforming to the contract. **Note**: This task enables parallel US2 development by providing a minimal valid input for solver testing.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Symbolic Latent Planner Execution (Priority: P2)

**Goal**: Execute frozen GFM encoder/decoder and inject a differentiable symbolic solver to enforce geometric constraints in 3D space, running entirely on CPU.

**Independent Test**: Load frozen GFM, run symbolic planner on a single P1 test case, decode action, verify constraint satisfaction in PyBullet without GPU.

### Implementation for User Story 2

- [X] T014-solver-impl [US2] [Depends on T006-diff, T009-mock] **Implement** `code/models/symbolic_solver.py` with DiffTaichi solver and hybrid convex/non-convex fallback (Plan 1.2). **Requirement**: The solver **optimizes latent vectors** but performs *constraint validation* by mapping the optimized latent state back to physical 3D space through the decoder. Constraints ('non-penetration', 'joint limits') are **defined and enforced in physical 3D space via the GFM decoder output, not in latent space**. **Output**: Functional `symbolic_solver.py` class ready for inference.
- [X] T014b-fd-verify [US2] [Depends on T014-solver-impl, T006-diff] **Execute** numerical finite difference check to validate solver differentiability (Plan 1.4). **Logic**: Perturb solver input parameters by $\epsilon = 10^{-6}$ and measure change in constraint violation loss to verify gradient flow through the solver, stopping at the decoder input. **Output**: `data/results/finite_diff_verification.json`. **Verification**: Assert gradient norms are non-zero.
- [X] T016 [US2] Integrate `code/gfm_wrapper.py` (T006-frozen for inference, T006-diff for check) and `code/symbolic_solver.py` (T014-solver-impl) to encode observations to latent space and decode solver outputs to 3D actions (Depends on T006-frozen, T014-solver-impl, T009-serialize).
- [X] T017 [US2] Implement timeout mechanism for solver steps: read `timeout_limits` from `code/config.yaml` and enforce a configurable timeout per step; record timeout events to `data/results/trial_log.csv` with `timeout=true` and `timeout_reason: step_limit`; link to <300ms/step assumption in spec's Assumptions and 6-hour total limit in SC-005. **Constraint**: This task implements the timeout logic *within* the execution loop orchestrated by T020-trial-exec.
- [X] T018 [US2] Implement "infeasible" flag logic when constraints cannot be satisfied: append `infeasible=true` to `data/results/trial_log.csv`; verification (assert that `trial_log.csv` contains at least one row with `infeasible=true` when constraints are unsatisfiable).
- [X] T019-decoder-control [US2] [Depends on T006-frozen, T009-serialize] **Implement Decoder Robustness Control** (Plan 1.3). **Logic**: Measure decoder reconstruction error independently by decoding latent states to physical space **without** the solver. **Output**: `data/results/decoder_control_log.json`. **Constraint**: If latent drift is detected, log alert and flag for manual review (do NOT exit).
- [X] T019b-symbolic-mse [US2] [Depends on T006-frozen, T009b-gt-decoder, T020-trial-exec] **Compute Symbolic Decoder MSE**. **Logic**: 1. Load symbolic latent actions from `data/results/trial_logs.jsonl`. 2. Decode using frozen GFM to physical space. 3. Compare against ground truth from `data/generated/ground_truth_decoder.json` (T009b-gt-decoder). 4. Calculate Mean Squared Error (MSE). **Output**: `data/results/symbolic_decoder_mse.json` containing `symbolic_mse` (float). **Requirement**: This metric is required for T019c verification of SC-003.
- [X] T022b-baseline-mse [US2] [Depends on T006-frozen, T009b-gt-decoder, T022a] **Compute Baseline Decoder MSE**. **Logic**: 1. Load baseline latent actions from `data/results/baseline_results.csv` (T022a). 2. Decode using frozen GFM to physical space. 3. Compare against ground truth from `data/generated/ground_truth_decoder.json` (T009b-gt-decoder). 4. Calculate Mean Squared Error (MSE). **Output**: `data/results/baseline_decoder_mse.json` containing `baseline_mse` (float). **Requirement**: This metric is required for T019c verification of SC-003.
- [X] T019c [US2] [Depends on T019b-symbolic-mse, T022b-baseline-mse] **Calculate Baseline Decoder Error and Ratio Check**. **Logic**: 1. Load symbolic MSE from `data/results/symbolic_decoder_mse.json`. 2. Load baseline MSE from `data/results/baseline_decoder_mse.json`. 3. Compare symbolic MSE to baseline MSE. 4. **Verify** that symbolic MSE is **≤ 1.5x baseline MSE**. **Output**: `data/results/decoder_ratio_check.json` with `baseline_mse`, `symbolic_mse`, `ratio`, `passed`. **Constraint**: Task must fail if ratio > 1.5.
- [X] T019d-constraint-sat [US2] [Depends on T014-solver-impl, T020-trial-exec] **Measure** and verify constraint satisfaction rate (SC-003). **Logic**: Run symbolic solver on test cases, check constraint satisfaction for each trial, and calculate the rate. **Output**: `data/results/constraint_satisfaction_log.json`.
- [X] T023-feasibility-pilot [US3] [Depends on T020b] **Run Pilot and Record CI Limit Status**. **Logic**: 1. Run a pilot set of trials (e.g., a small fraction of the total). 2. Measure total time. 3. **Calculate** projected total time for full experiment. 4. **Check** if projected time > 6 hours. 5. **Write** `ci_time_limit_exceeded` flag (true/false) to `data/results/feasibility_status.json`. 6. **Log** a warning if exceeded but **DO NOT abort** the experiment; proceed with full execution. **Output**: `data/results/feasibility_status.json` with `projected_time`, `ci_time_limit_exceeded` (boolean). **Note**: This task must run before T020-trial-exec to validate feasibility without halting the project.
- [X] T020-trial-exec [US2] [Depends on T014-solver-impl, T016, T009-serialize, T017, T018, T019d-constraint-sat, T023-feasibility-pilot] **Run** a sufficient number of trials for both symbolic and baseline methods (Plan 2.1). **Output**: `data/results/trial_logs.jsonl` containing per-trial results.
- [X] T020b [US2] [SC-005] **Validate Per-Step Latency Assumption**. **Logic**: 1. Run a small subset of trials on the symbolic pipeline. 2. Measure per-step latency. 3. **Verify** that per-step latency is **< 300 milliseconds** (Spec Assumption). 4. **Calculate** projected total time for a series of trials (10 steps each). 5. **Verify** projected time **< 3 hours (2111.01007, https://arxiv.org/abs/2111.01007) hours**. 6. If validation fails, **EXIT WITH CODE 2** and log `data/results/latency_validation_error.json`. **Output**: `data/results/latency_validation.json` with `per_step_latency`, `projected_total_time`, `passed`. **Note**: This task must run before T023-feasibility-pilot to ensure feasibility.
- [X] T021 [US2] Add logging for inference latency (ms) and success/failure status for each trial
- [X] T021b [US2] [SC-001] [Depends on T021c, T022a] Implement logic to measure and record the success metric: read `data/generated/physics_states.json` (T010a) and `data/results/trial_logs.jsonl` (T020-trial-exec). **Logic**: For each trial, verify that `collision_flag == 0` AND `distance to target object center < 5cm` for **every frame** in a window of `success_frames >= int(config.sim_fps)` (approx 1 second). **Constraint**: If any frame in the window fails the collision or distance check, the trial is marked as failure. **Output**: `data/results/symbolic_results.csv` with schema: `trial_id`, `approach="Symbolic"`, `success`, `latency_ms`, `timeout`, `infeasible`, `timestamp`.
- [X] T022a [US3] [Depends on T005-baseline-fetch, T021c, T022b-baseline-impl] Run `code/baseline_runner.py` on the test set generated in T009-serialize; load weights from `data/raw/gfm_baseline.pt` (acquired in T005-baseline-fetch); output results to `data/results/baseline_results.csv` (Schema: trial_id, success, latency_ms, approach="Baseline", timestamp).
- [X] T023b-ci-time-verify [US3] [Depends on T020-trial-exec] **Measure** and record `ci_time_limit_exceeded` flag (Plan 2.4). **Logic**: Monitor total runtime of the full experiment. **Output**: `data/results/ci_time_limit_status.json`.
- [X] T023 [P] [US3] [Depends on T021c, T022a] Implement `code/analysis.py` to load results from `data/results/symbolic_results.csv` (T021c) and `data/results/baseline_results.csv` (T022a); expect CSV schema: columns `trial_id`, `approach`, `success`, `latency_ms`, `timestamp`.
- [X] T024a-load [US3] [Depends on T023] Implement data loading and schema verification in `code/analysis.py`.
- [X] T024a-detect-censor [US3] [Depends on T021c, T022a] **Detect Censored Data**. **Logic**: Inspect `data/results/symbolic_results.csv` and `data/results/baseline_results.csv` for the presence of the `timeout` flag set to `true`. **Output**: `data/results/censoring_status.json` with schema: `{"symbolic_censored": bool, "baseline_censored": bool, "any_censored": bool}`. **CRITICAL**: This status is used by T024a-select to count censored trials as failures in McNemar's test. **Note**: Trials with `timeout=true` or `infeasible=true` MUST be counted as **0 (failure)** in the McNemar's test success rate matrix.
- [X] T024a-select [US3] [Depends on T024a-load, T024a-detect-censor] **Implement Conditional Statistical Test Selection**. **Logic**: Read `data/results/censoring_status.json`. **Filter out trials with timeout=true from the dataset before performing Shapiro-Wilk test**. Perform Shapiro-Wilk test for normality on the remaining non-censored latency differences. If p < 0.05 (non-normal): Perform Wilcoxon Signed-Rank test. Otherwise: Perform Paired t-test. **CRITICAL HANDLING OF CENSORED DATA**: Trials with `timeout=true` or `infeasible=true` MUST be counted as **0 (failure)** in the McNemar's test success rate matrix, even though they are excluded from the latency distribution. **Output**: `data/results/stat_test_selection.json` containing the chosen test names and the reasons.
- [X] T024a-report [US3] [Depends on T024a-select] Implement report generation logic in `code/analysis.py` to create `data/results/analysis_report.md` as a Markdown table with columns: Metric, Symbolic, Baseline, Difference, P-value, 95% CI, Effect Size.
- [X] T024a-validate [US3] [Depends on T024a-report] Validate SC-001 (one-second duration) in the report and verify all p-values are present.
- [X] T025-validate-experiment [US3] [Depends on T019c, T019d-constraint-sat] **Validate Experiment Results**. **Logic**: Load constraint satisfaction rate from `data/results/constraint_satisfaction_log.json` and decoder ratio from `data/results/decoder_ratio_check.json`. {{claim:c_84b12dd5}}. Output a pass/fail flag to data/results/experiment_validation.json.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Update `README.md` with CLI usage instructions and project structure
- [ ] T030 Code cleanup and refactoring of `code/` modules
- [ ] T032 [P] Additional unit tests for solver constraints and latent drift detection in `tests/unit/`
- [X] T033 [P] Run `scripts/validate_quickstart.sh` (or equivalent) to ensure end-to-end reproducibility; verify exit code 0 and generate `data/results/quickstart_validation.json` with pass/fail status.

---

## Phase Revision: Addressing Analyze Findings

**Purpose**: Tasks added to resolve specific issues identified by the analysis agent (e.g., missing edge case handling, data flow gaps).

- [ ] T034 [P] [US1] **Implement Robust Topology Hashing**. **Logic**: Create `code/utils/topology_hasher.py` to generate deterministic SHA-256 hashes for kinematic chains and deformable meshes. **Requirement**: The hash must include the number of links, joint types, material properties (stiffness, damping), and mesh vertex count. **Output**: Function `compute_topology_hash(config_dict)` returning a hex string. **Dependency**: Used by T009-gen-unified and T009-verify-overlap to ensure strict zero-overlap verification.
- [ ] T035 [US2] **Implement Mahalanobis Distance Drift Detection**. **Logic**: In `code/evaluation/runner.py`, calculate the Mahalanobis distance between the current latent vector and the reference mean/covariance (from T008-drift-calib). **Requirement**: If distance > threshold (configurable, default value determined by context), set `drift_flag=true` in the trial log and log to `data/results/drift_events.json`. **Constraint**: Do NOT crash the pipeline; record the event as a potential OOD failure. **Output**: Updated `trial_logs.jsonl` with `drift_flag` column.
- [ ] T036 [US2] **Implement Solver Timeout Handler**. **Logic**: Wrap the DiffTaichi solver call in `code/models/symbolic_solver.py` with a `signal.alarm` (Unix) or `threading.Timer` (cross-platform) to enforce the `timeout_limits` from `config.yaml`. **Requirement**: On timeout, catch the exception, set `timeout=true` in the trial log, and return a "timeout" status to the runner. **Output**: Robust solver execution that never hangs indefinitely.
- [ ] T037 [US3] **Implement Censoring-Aware Statistical Analysis**. **Logic**: In `code/analysis.py`, explicitly handle the `timeout` and `infeasible` flags. **Requirement**: When calculating success rates for McNemar's test, treat `timeout` and `infeasible` as **failures** (0). When calculating latency for Wilcoxon/T-test, **exclude** trials where `timeout=true` (censored data) from the latency distribution, but include them in the success rate calculation. **Output**: `analysis_report.md` with correct handling of censored data.
- [ ] T038 [US1] **Implement Deformable Material Parameterization**. **Logic**: Update `code/data/generator.py` to support generating soft-body parameters (Young's modulus, Poisson's ratio) for the deformable objects. **Requirement**: These parameters must be stored in `data/generated/physics_states.json` and used in the PyBullet soft-body simulation setup. **Output**: Valid soft-body physics states in the generated dataset.
- [ ] T039 [US2] **Implement Differentiable Constraint Validation**. **Logic**: In `code/models/symbolic_solver.py`, ensure that the constraint violation loss (e.g., interpenetration depth) is differentiable with respect to the latent variables. **Requirement**: Use `torch.autograd.grad` to verify that gradients flow from the loss to the solver inputs. **Output**: Verification log in `data/results/gradient_flow_check.json`.
- [ ] T040 [US3] **Implement Effect Size Calculation**. **Logic**: In `code/analysis.py`, calculate Cohen's h for success rates and Cohen's d for latency differences. **Requirement**: Include these values in the `analysis_report.md` table. **Output**: Updated report with effect sizes.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase N)**: Depends on specific analysis findings; can be integrated into existing phases or run as a separate pass.

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
- Revision tasks (T034-T040) can be implemented in parallel with the main US2/US3 implementation if the dependencies are clear.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
- **Revision Tasks (T034-T040)**: These were added to address specific edge cases and data flow gaps identified in the analysis phase (e.g., missing drift detection, timeout handling, censoring-aware statistics). They are critical for the robustness and scientific validity of the experiment.