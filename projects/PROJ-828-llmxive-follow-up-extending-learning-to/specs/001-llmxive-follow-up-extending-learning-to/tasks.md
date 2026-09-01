# Tasks: Low-Rank RL for Foresight in LLM Training

**Input**: Design documents from `/specs/001-low-rank-rl-foresight/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Implementation Notes

**Time Budget & Abort Strategy**: The time limit is strict. T053 implements a "Hard Abort" strategy. If the pre-flight estimation (T052a/b) indicates the N=3 runs will exceed 6 hours, the entire pipeline aborts immediately. NO variant reduction is permitted. All multiple variants defined in the spec must run, or the project transitions to `human_input_needed`.

**Time Budget & Reduction**: The time limit is strict. T056 implements a "Variant Reduction Strategy" that triggers at [deferred] of the time budget. If a critical baseline (Standard RL, OPD, Low-Rank RL) is dropped, the experiment flags 'Inconclusive'.

**Early Window Definition**: The "early trajectory" window is defined by `results/early_window_config.json` (T018c). T018c writes the resolved window size (default or CLI override) and logs a warning if the default is used. **No manual approval step is required**; the pipeline proceeds automatically.

**Data Integrity & Failure Policy**: All data loaders (T007) MUST fail loudly if the real GSM8K fetch fails. No synthetic fallbacks permitted. If a verified real data source is injected by the execution stage, T007 must adopt that exact package/recipe immediately.

**Pruning Strategy (T009)**: Target 300M ± 1% (297M-303M). **Fallback Logic**: If exact target cannot be met, prune to the **closest available verified model size** (e.g., a representative number of top components) and log a `WARNING: Target 300M unreachable, using closest verified size {size}`. **Abort only if no verified model size is available**. Include verification logic to validate the pruned model architecture.

**CPU Feasibility & Scaling**: All training tasks (T043-T047) are explicitly constrained to CPU-only execution (vCPU, 7GB RAM) with a 6-hour wall-clock limit. Phase 3 (CPU Feasibility) MUST be completed before Phase 5 (Execution) to ensure streaming and memory safeguards are in place. **NO** GPU tasks are permitted in this revision; the "Real Data + Real Results" rule is satisfied by streaming the GSM8K subset and processing in chunks.

**Reproducibility & Determinism**: All random seeds must be pinned at the start of every script (T004). The `datasets` library must be called with `trust_remote_code=False` (unless verified) and `num_proc=1` to ensure deterministic data loading order on CPU.

**Data Source Verification**: T007 must explicitly verify the GSM8K split integrity against the HuggingFace metadata hash before processing. If the hash mismatches, the loader must raise a `DataIntegrityError` and halt.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (src/, tests/, data/, results/)
- [X] T002 Initialize Python 3.10 project with `torch`, `transformers`, `datasets`, `peft`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

- [X] T004 Implement `src/utils/seeds.py` for deterministic seed pinning across all variants
- [X] T005 Implement `src/utils/memory_monitor.py` to track RAM usage and enforce a memory limit
- [X] T006 Implement `src/utils/hasher.py` to compute SHA-256 hashes of all derived artifacts
- [X] T007 Create `src/data/loader.py` to fetch GSM8K subset (≥1,000 problems) from HuggingFace `datasets` with checksum verification. **Constraint**: Must raise an exception immediately if fetch fails; NO synthetic fallbacks.
- [X] T008 Create `src/data/checksums.py` for data integrity verification
- [X] T009 Implement `src/models/config.py` to programmatically prune `TinyLlama` to a reduced parameter scale. **Target**: 300M ± 1% (297M-303M). **Strategy**: 1) Remove layers from end until target range met. 2) If overshoot, remove attention heads from last remaining layer. 3) **Fallback**: If target not met, use **closest available verified model size** and log a `WARNING: Target 300M unreachable, using closest verified size {size}`. **Abort only if no verified model size is available**. **Include verification logic** to validate the pruned model architecture.
- [X] T010 Implement `src/models/backbone.py` with hooks to capture attention projection updates
- [X] T012 Create `src/cli/run_experiment.py` as the single entry point orchestrating all training and analysis. **Requirement**: Must define `--early-window-fraction`, `--early-alignment-threshold`, and `--num-seeds` CLI arguments.
- [X] T013 [P] Create `tests/unit/test_svd.py` to verify SVD on small matrices fits memory constraints
- [X] T014 [P] Create `tests/unit/test_projection.py` to verify projection math (cosine similarity ≥ 0.99)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: CPU Feasibility & Resource Hardening (Mandatory Prerequisites)

**Purpose**: Implement streaming, online stats, and time/memory enforcement to ensure CPU feasibility BEFORE execution. **This phase is a strict prerequisite for all User Story execution tasks.**

- [X] T052a [P] [US1/US2/US3] **Implement Time Estimator** in `src/utils/time_estimator.py`. **Logic**: Calculate estimated runtime per variant based on parameter count, dataset size (streamed), and CPU core count. **Output**: `results/time_estimate.json`. **Constraint**: Must trigger T053 abort if total estimated time > 6 hours.
- [X] T052b [P] [US1/US2/US3] **Implement Memory Estimator** in `src/utils/memory_estimator.py`. **Logic**: Estimate peak RAM usage based on model size (FP16), optimizer states, and batch size. **Output**: `results/memory_estimate.json`. **Constraint**: Must trigger T053 abort if estimated peak > 7GB.
- [X] T059 [P] [US1/US2/US3] **Refactor** `src/data/loader.py` to use `datasets.load_dataset(..., streaming=True)`. **Logic**: Iterate over the GSMK split in chunks of a fixed size to process the full dataset without loading it entirely into RAM. **Constraint**: Must not use `.to_list()` or `.map()` on the full dataset before iteration. **Action**: Update T007 to use this streaming approach for all training runs.
- [X] T060 [P] [US1/US2/US3] Implement **online statistics accumulator** in `src/analysis/metrics.py` for convergence metrics. **Logic**: Instead of storing all accuracy curves in memory, update running means/variances and save intermediate checkpoints to disk every N steps. **Artifact**: `results/online_stats_checkpoint.json`. **Schema**: `{"step": int, "mean_accuracy": float, "var_accuracy": float, "memory_mb": float, "timestamp": "ISO8601"}`. **Constraint**: Ensure memory footprint remains < 7GB even with N=3 seeds.
- [X] T061 [P] [US1] Add **SVD fallback logic** in `src/training/projection_utils.py` for "flat spectrum" edge cases. **Logic**: If cumulative variance < 80% for any $k \le 50$, default to $k=10$ and log a `WARNING: Flat spectrum detected, using fixed k=10`. **Constraint**: Do not abort; proceed with fixed $k$ to maintain experiment continuity.
- [X] T062 [P] [US2] Implement **gradient projection sanity check** in `src/training/low_rank_rl.py` to verify projection matrix is well-conditioned. **Logic**: Check condition number of the subspace matrix; if > 1e6, log `WARNING: Ill-conditioned subspace` and re-normalize vectors before projection.
- [X] T063 [P] [US3] Add **time-budget enforcement** in `src/cli/run_experiment.py` that strictly aborts the current seed and flags 'inconclusive' if the 6-hour limit is exceeded before N=3 for all active variants is reached. **Constraint**: Must write 'inconclusive' to `results/experiment_status.json` AND exit with a designated inconclusive status code. **Action**: T042-a-run must check this file/exit code before proceeding.

**Checkpoint**: CPU safeguards implemented - execution tasks can now proceed safely.

---

## Phase 4: User Story 1 - Establish Geometric Baseline via On-Policy Distillation (Priority: P1) 🎯 MVP

**Goal**: Run OPD baseline on GSM8K subset to generate a "stable subspace" defined by top singular vectors of early parameter updates.

**Independent Test**: Run OPD loop for fixed steps, extract accumulated update matrices, perform SVD, and verify existence of defined subspace (top-k vectors) without running RL.

### Tests for User Story 1

- [X] T015 [P] [US1] Contract test for OPD SVD output shape in `tests/unit/test_opd_svd.py`
- [X] T016 [P] [US1] Integration test for OPD data flow in `tests/integration/test_opd_flow.py`

### Implementation for User Story 1

- [ ] T017 [US1] Implement `src/training/opd_baseline.py` runner for GSM8K subset (capped steps). **Deliverable**: A training loop that accepts a GSM8K subset, runs for a specified number of steps, and logs per-step parameter updates.
- [ ] T018 [US1] Implement logic in `src/training/opd_baseline.py` to record $\Delta W$ matrices for the initial phase of training (after every optimizer step). Save list of tensors to `results/opd/updates_seed_{i}.pt`. **Deliverable**: A mechanism to capture and save parameter updates during the OPD training loop in a structured format.
- [ ] T018b [US1] Implement per-step update direction logging in `src/training/opd_baseline.py`. **Storage**: Save per-layer update vectors to separate files `results/opd/updates_seed_{i}/layer_{index:02d}.pt` (NOT a single stacked array) to ensure memory compliance. **Naming Convention**: `layer_{index:02d}.pt` where `index` is derived from the model's `state_dict` keys using regex `layer_(\\d+)`, defaulting to sequential numeric indices if named layers are found.
- [ ] T018c [US1] **Aggregate** per-layer vectors into a single accumulated matrix. **Logic**: Read all `layer_{index:02d}.pt` files for a seed, flatten each layer's update vector, concatenate them into a single vector of shape `(n_params,)`, and stack these vectors for all steps into a matrix of shape `(steps, n_params)`. Save to `results/opd/accumulated_matrix_seed_{i}.npy`. **Dependency**: T018b.
- [ ] T018c-config [US1] Implement logic in `src/analysis/metrics.py` to define the 'early' window. **Logic**: Read `early_window_ratio` from CLI or `results/early_window_config.json`. **Default**: If file missing or CLI not provided, use `max(a predefined minimum threshold, ceil(total_steps * a small proportional factor))` and log `WARNING: Using default window`. **Action**: Write the resolved window size to `results/early_window_config.json`.
- [ ] T018d-impl [US1] Implement per-step update direction logging in `src/training/opd_baseline.py`. **Logic**: During the `early_window` steps, compute the cosine similarity between the current update vector (from T018b) and the average update vector of the *same* OPD run (or a running reference). **Storage**: Save per-step alignment scores to `results/opd/early_alignment_log.json`. **Schema**: `{"step": int, "alignment_score": float, "variant": "OPD"}`.
- [ ] T018d-verify [US1] Verify that `results/opd/early_alignment_log.json` exists and is valid JSON after T018d-impl. **Action**: If missing/invalid, abort T040b.
- [ ] T019 [US1] Implement **Global SVD logic** in `src/training/projection_utils.py`. **Input**: `results/opd/accumulated_matrix_seed_{i}.npy` from T018c. **Logic**: Perform SVD on the aggregated matrix to extract top-$k$ singular vectors. **Output**: Global subspace basis. **Dependency**: T018c.
- [ ] T020 [US1] Implement logic to select $k$ such that cumulative explained variance ≥ 80% (default $k=10$ if none)
- [ ] T021 [US1] **Save stable subspace matrix** (shape $k \times n_{params}$) to `results/opd_subspace.npy`. **Dependency**: Must be completed before T026-impl starts. **Depends on**: T017, T018, T018c, T019.
- [ ] T022a [US1] Log memory usage during SVD and **Assert memory usage < 7GB **; raise exception if limit exceeded.
- [ ] T022b [US1] **Log** peak memory usage to `results/memory_profile.json` for SC-004 verification, regardless of success or failure.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 5: User Story 2 - Execute Low-Rank RL Hybrid with Geometric Projection (Priority: P2)

**Goal**: Train a PPO-based RL agent where gradients are projected onto the stable subspace from US1 before update.

**Independent Test**: Run PPO training with projection active, verify update direction cosine similarity with subspace basis ≥ 0.99.

### Tests for User Story 2

- [ ] T023 [P] [US2] Contract test for gradient projection in `tests/unit/test_gradient_projection.py`
- [ ] T024 [P] [US2] Integration test for Low-Rank RL loop in `tests/integration/test_low_rank_rl.py`

### Implementation for User Story 2

- [ ] T025 [US2] Implement `src/training/rl_baseline.py` with **lightweight PPO loop using torch.optim** (no external RL libs) and logging schema: steps, accuracy, loss. **Deliverable**: A minimal PPO training loop that accepts a GSM8K subset and runs for a specified number of steps, logging relevant metrics.
- [ ] T026-impl [US2] Implement `src/training/low_rank_rl.py` loading subspace from `results/opd_subspace.npy` (Depends on T021 completion). **Constraint**: Phase 5 cannot start until T021 is marked complete. **Dependency**: T059 (Streaming), T060 (Online Stats).
- [ ] T027 [US2] Implement **gradient projection logic** in `low_rank_rl.py` to constrain raw RL gradients to top-$k$ vectors
- [ ] T028 [US2] Add logging to verify update vector lies entirely within span of top-$k$ vectors
- [ ] T029 [US2] Log cosine similarity between applied update and subspace basis and **Assert cosine similarity >= 0.99 **; raise exception if violated.
- [ ] T029a [US2] Enforce memory limit for Low-Rank RL training loop. Integrate `memory_monitor` to assert peak RAM < 7GB during training.
- [ ] T030 [US2] Save Low-Rank RL training logs and checkpoints to `results/low_rank_rl/`
- [ ] T030b [US2] Implement per-step update direction logging in `src/training/low_rank_rl.py`. **Storage**: Save per-layer update vectors to separate files `results/low_rank_rl/updates_seed_{i}/layer_{index:02d}.pt` (NOT a single stacked array). **Naming Convention**: `layer_{index:02d}.pt` where `index` is derived from the model's `state_dict` keys using regex `layer_(\\d+)`, defaulting to sequential numeric indices if named layers are found.
- [ ] T030c-impl [US2] Implement real-time "Early Trajectory Alignment" logging in `src/training/low_rank_rl.py`. **Logic**: During the first `early_window` steps, calculate cosine similarity between current update and OPD trajectory. **Action**: Log to `results/low_rank_rl/early_alignment_log.json` and **Flag run as 'Low Alignment'** if alignment < 0.95 (do NOT abort).
- [ ] T030c-verify [US2] Verify that `results/low_rank_rl/early_alignment_log.json` exists and is valid JSON after T030c-impl. **Action**: If missing/invalid, abort T040.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Compare Convergence and Subspace Alignment (Priority: P3)

**Goal**: Compare sample efficiency and subspace alignment of Low-Rank RL vs Standard RL vs OPD.

**Independent Test**: Aggregate accuracy-vs-steps curves, run statistical test (paired t-test or Wilcoxon) on steps-to-threshold metric.

### Tests for User Story 3

- [ ] T031 [P] [US3] Contract test for statistical significance in `tests/unit/test_stats.py`
- [ ] T032 [P] [US3] Integration test for full pipeline comparison in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement `src/training/random_projection.py` (Random Baseline)
- [ ] T033a [P] [US3] Enforce memory limit for Random Projection training loop.
- [ ] T034 [P] [US3] Implement `src/training/random_walk_prior.py` with random walk subspace projection logic
- [ ] T034a [P] [US3] Enforce memory limit for Random Walk Prior training loop.
- [ ] T035 [P] [US3] Implement `src/training/opd_initialized_rl.py` with OPD weight initialization and no projection
- [ ] T035a [P] [US3] Enforce memory limit for OPD-Initialized RL training loop.
- [ ] T036-gen [US3] [P] **Generate** `results/active_variants.json`. **Logic**: Read time budget and variant constraints; write the list of active variants. **Error Handling**: If generation fails, raise a clear error: "Failed to generate active_variants.json". **Dependency**: T056.
- [ ] T036-calc [US3] [P] Implement `src/analysis/metrics.py` to calculate steps-to-threshold-accuracy for **ACTIVE variants**. **Requirement**: Explicitly iterate over the list of active variant keys to ensure all are included in the comparison table. **Error Handling**: If `results/active_variants.json` is missing, raise a clear error: "Missing active_variants.json. Ensure T056 and T036-gen have completed."
- [ ] T037 [US3] Implement `src/analysis/metrics.py` to compute cosine similarity between final update directions and PPO proxy
- [ ] T038a [US3] Implement `src/analysis/power_analysis.py` to perform pre-experiment/post-hoc power analysis and sample size estimation. **Constraint**: Must use standard statistical power formulas (e.g., Cohen's d).
- [ ] T038b-d [US3] Execute Wilcoxon signed-rank test logic in `src/analysis/metrics.py` (N=3 minimum) with dynamic power calculation and conditional re-run flagging.
- [ ] T038b-primary [US3] **Aggregate N=3 results** for the primary statistical report. **Logic**: After T036-exec completes, aggregate the N=3 results for all active variants into `results/primary_report_data.json`. **Constraint**: This task MUST run unconditionally, regardless of whether T048c-branch triggers a re-run.
- [ ] T039 [US3] Implement `src/analysis/plots.py` to generate convergence curves and alignment plots
- [ ] T041-impl [US3] Implement `src/analysis/plots.py` to generate final comparison table and statistical report artifact `results/analysis_report.md` covering **ALL variants**. **Requirement**: Verify that the table includes rows for all variants. If the pipeline aborted early, mark status as 'Inconclusive due to time' and list all variants as 'Not Run'. **Logic**: Read `results/active_variants.json` to determine if variants were reduced; if so, log the `reduction_reason` field from that file in the report.

### Execution Tasks (N=3 Seeds per Variant, Strict Abort Policy)

- [ ] T056 [US3] **Orchestrate** generation of the run list based on time budget. **Action**: Read time budget, determine active variants (Critical: OPD, Standard RL, Low-Rank RL, Random Projection, Random Walk, OPD-Initialized RL), and write `results/active_variants.json`. **Constraint**: Must include all variants unless time budget strictly forbids it. If reduction occurs, write `reduction_reason` to the JSON file.
- [ ] T057 [US3] Update `src/cli/run_experiment.py` to integrate `variant_reducer` logic, ensuring it aborts pending runs and triggers the "inconclusive" flag if the time budget is exceeded before N=3 seeds are completed for each variant.
- [ ] T058 [US3] [P] Implement a "Time Budget Monitor" thread in `src/cli/run_experiment.py` (not `memory_monitor.py`) that logs a warning at a high percentage of the 6-hour limit and triggers the reduction strategy.

- [ ] T042-a-gen [US3] **Orchestrate** generation of the run list based on T056 output. **Action**: Read `results/active_variants.json`, filter variants, and write `results/run_list.json`.
- [ ] T042-a-run [US3] **Orchestrate** initial training runs for **ACTIVE variants** (filtered by T042-a-gen) with **N=3 seeds**.
- [ ] T043 [US3] Execute training runs for OPD Baseline (N=3 seeds) via CLI
- [ ] T043b [US3] Execute training runs for Low-Rank RL (N=3 seeds) via CLI
- [ ] T044 [US3] Execute training runs for Standard RL (N=3 seeds) via CLI
- [ ] T045 [US3] Execute training runs for Random Projection Baseline (N=3 seeds) via CLI
- [ ] T046 [US3] Execute training runs for Random Walk Prior Baseline (N=3 seeds) via CLI
- [ ] T047b [US3] Execute training runs for OPD-Initialized RL (N=3 seeds) via CLI

### Post-Execution Analysis

- [ ] T040 [US3] Compute Early Trajectory Alignment (first `early_window` steps, min) between Low-Rank RL and OPD
- [ ] T040b [US3] **Compute and Log Alignment for Baselines**. Logic: Calculate cosine similarity between Standard RL trajectory and OPD trajectory, and OPD trajectory vs itself (baseline) during the `early_window`.

### Conditional Re-run Logic

- [ ] T048a [US3] Implement power analysis calculation in `src/analysis/power_analysis.py` to check effect size and sample size.
- [ ] T048b [US3] Implement conditional branching logic in `src/analysis/power_analysis.py` to check: (1) time remaining, (2) effect size < 0.5. If both conditions met AND N < 10, prepare for re-run.
- [ ] T048c-check [US3] **Validate N >= 3**. Action: If N < 3, flag 'inconclusive' and STOP. Do not proceed to T048c-branch.
- [ ] T048c-branch [US3] Execute conditional branching: if effect size < 0.5 AND N < 10 AND time > 15% remaining, trigger re-run logic.
- [ ] T042-b [US3] **Orchestrate** conditional re-run for **ACTIVE variants** with **N=10 seeds ** if T048c-branch triggers.
- [ ] T048d [US3] Re-run analysis on new data if re-run occurred.

### Phase 7: Polish & Cross-Cutting Concerns

- [ ] T050a [P] Update `quickstart.md` with CLI usage examples and hard abort explanation.
- [ ] T050b [P] Add API docs for `src/training/projection_utils.py` and `src/utils/memory_monitor.py`.
- [ ] T050c [P] Update `README.md` with experiment status and data availability notes.
- [ ] T051a [P] Extract logging logic to `src/utils/logger.py`.
- [ ] T051b [P] Remove unused imports and refactor training loops for clarity.
- [ ] T052 Performance optimization for CPU execution (batching, mixed precision)
- [ ] T053 [P] Additional unit tests in `tests/unit/`
- [ ] T054 Run quickstart.md validation to ensure 6-hour limit compliance (with N=3 seed count and all variants)
- [ ] T067 [P] Data Loader Fail-Loud Verification
- [ ] T068 [P] Data Integrity Hash Audit
- [ ] T069 [P] Subspace Stability Verification
- [ ] T071 [US3] **Memory Assertion Verification**. **Logic**: After Phase 6 execution completes, verify that `results/memory_profile.json` exists and all recorded peaks are < 7GB. **Constraint**: This task is sequential (depends on Phase 6 completion). If any peak > 7GB, flag 'Memory Violation' and update `results/experiment_status.json`.
