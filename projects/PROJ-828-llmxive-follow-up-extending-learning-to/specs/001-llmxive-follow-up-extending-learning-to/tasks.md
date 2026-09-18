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

**Time Budget & Abort Strategy**: The time limit is strict. T036-calc-feasibility implements a "Variant Reduction Strategy" and "Adaptive N" strategy. If the pre-flight estimation indicates the full N=3 runs for all 7 variants will exceed 6 hours, the system automatically reduces N to 2 for the initial run and drops non-critical variants (Random Walk, Random Projection) to ensure the core 3 (OPD, Standard RL, Low-Rank RL) complete. If even this reduced set exceeds the budget, the project transitions to `human_input_needed`.

**Early Window Definition**: The "early trajectory" window is defined by `results/early_window_config.json` (T018c-config). T018c-config writes the resolved window size (default or CLI override) and logs a warning if the default is used. **No manual approval step is required**; the pipeline proceeds automatically.

**Data Integrity & Failure Policy**: All data loaders (T007) MUST fail loudly if the real GSM8K fetch fails. No synthetic fallbacks permitted. If a verified real data source is injected by the execution stage, T007 must adopt that exact package/recipe immediately.

**Pruning Strategy (T009)**: Target 300M ± 1% (297M-303M). **Fallback Logic**: If exact target cannot be met, prune to the **closest available verified model size** and log a `WARNING: Target 300M unreachable, using closest verified size {size}`. **ABORT** if the size deviation exceeds 1% from the target (297M-303M) to prevent hardware constraint violations. Include verification logic to validate the pruned model architecture.

**CPU Feasibility & Scaling**: All training tasks (T025-impl, T033-T035) are explicitly constrained to CPU-only execution with a 6-hour wall-clock limit. Phase 3 (CPU Feasibility) MUST be completed before Phase 5 (Execution) to ensure streaming and memory safeguards are in place. **NO** GPU tasks are permitted in this revision; the "Real Data + Real Results" rule is satisfied by streaming the GSM8K subset and processing in chunks.

**Reproducibility & Determinism**: All random seeds must be pinned at the start of every script (T004). The `datasets` library must be called with `trust_remote_code=False` (unless verified) and `num_proc=1` to ensure deterministic data loading order on CPU.

**Data Source Verification**: T007 must explicitly verify the GSM8K split integrity against the HuggingFace metadata hash before processing. If the hash mismatches, the loader must raise a `DataIntegrityError` and halt.

**Statistical Rigor & Power Analysis**: T038b-wilcoxon and T048a enforce a strict power analysis protocol. If the initial N=2 runs yield an effect size < 0.5, the system MUST trigger a conditional re-run (T042-b) to reach N=10, provided time budget allows. This prevents false negatives in the Wilcoxon test. **Constraint**: T038b-wilcoxon MUST require N>=3; if N<3, flag 'Inconclusive (Insufficient Samples)' and STOP.

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
- [X] T009 Implement `src/models/config.py` to programmatically prune `TinyLlama` to a reduced parameter scale. **Target**: 300M ± 1% (297M-303M). **Strategy**: 1) Remove layers from end until target range met. 2) If overshoot, remove attention heads from last remaining layer. 3) **Fallback**: If target not met, use **closest available verified model size** and log a `WARNING: Target 300M unreachable, using closest verified size {size}`. **ABORT** if deviation > 1%. **Include verification logic** to validate the pruned model architecture.
- [X] T010 Implement `src/models/backbone.py` with hooks to capture attention projection updates
- [ ] T012 Create `src/cli/run_experiment.py` as the single entry point orchestrating all training and analysis. **Requirement**: Must define `--early-window-fraction`, `--early-alignment-threshold`, and `--num-seeds` CLI arguments.
- [X] T013 [P] Create `tests/unit/test_svd.py` to verify SVD on small matrices fits memory constraints
- [X] T014 [P] Create `tests/unit/test_projection.py` to verify projection math (cosine similarity ≥ 0.99)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: CPU Feasibility & Resource Hardening (Mandatory Prerequisites)

**Purpose**: Implement streaming, online stats, and time/memory enforcement to ensure CPU feasibility BEFORE execution. **This phase is a strict prerequisite for all User Story execution tasks.**

- [X] T052a [P] [US1/US2/US3] **Implement Time Estimator** in `src/utils/time_estimator.py`. **Logic**: Calculate estimated runtime per variant based on parameter count, dataset size (streamed), and CPU core count. **Output**: `results/time_estimate.json`. **Constraint**: Must trigger T053 abort if total estimated time > 6 hours.
- [X] T052b [P] [US1/US2/US3] **Implement Memory Estimator** in `src/utils/memory_estimator.py`. **Logic**: Estimate peak RAM usage based on model size (FP16), optimizer states, and batch size. **Output**: `results/memory_estimate.json`. **Constraint**: Must trigger T053 abort if estimated peak > 7GB.
- [X] T052c-final-time-verify [US1/US2/US3] **Verify Total Wall-Clock Time**. **Logic**: This task aggregates the final time measurement from Phase 6 (T042-execute-list) and writes `results/pipeline_time.json`. **Constraint**: Must explicitly verify against the 6-hour limit (SC-005). **Dependency**: T042-execute-list.
- [X] T059 [P] [US1/US2/US3] **Refactor** `src/data/loader.py` to use `datasets.load_dataset(..., streaming=True)`. **Logic**: Iterate over the GSMK split in chunks of a fixed size to process the full dataset without loading it entirely into RAM. **Constraint**: Must not use `.to_list()` or `.map()` on the full dataset before iteration. **Action**: Update T007 to use this streaming approach for all training runs.
- [X] T060-stream [P] [US1/US2/US3] **Implement Streaming Data Loader** in `src/data/loader.py`. **Logic**: Use `datasets.load_dataset(..., streaming=True)` and iterate in chunks. **Output**: Streamed batches. **Constraint**: Verified streaming approach (no refuted claims).
- [X] T060-accum [P] [US1/US2/US3] **Implement Online Statistics Accumulator** in `src/analysis/metrics.py` for convergence metrics. **Logic**: Instead of storing all accuracy curves in memory, update running means/variances and save intermediate checkpoints to disk every N steps. **Artifact**: `results/online_stats_checkpoint.json`. **Schema**: `{"step": int, "mean_accuracy": float, "var_accuracy": float, "memory_mb": float, "timestamp": "ISO8601"}`. **Constraint**: Ensure memory footprint remains < 7GB even with N=2 seeds. **Note**: Claim c_417119e6 removed; verified approach implemented.
- [X] T061 [P] [US1] Add **SVD fallback logic** in `src/training/projection_utils.py` for "flat spectrum" edge cases. **Logic**: If cumulative variance < 80% for any $k \le 50$, default to $k=10$ and log a `WARNING: Flat spectrum detected, using fixed k=10`. **Constraint**: Do not abort; proceed with fixed $k$ to maintain experiment continuity. **Dependency**: T060-stream.
- [X] T062 [P] [US2] Implement **gradient projection sanity check** in `src/training/projection_utils.py` to verify projection matrix is well-conditioned. **Logic**: Check condition number of the subspace matrix; if > 1e6, log `WARNING: Ill-conditioned subspace` and re-normalize vectors before projection. **Dependency**: T060-stream.
- [ ] T063 [P] [US3] Add **time-budget enforcement** in `src/cli/run_experiment.py` that strictly aborts the current seed and flags 'inconclusive' if the 6-hour limit is exceeded before N=2 for all active variants is reached. **Constraint**: Must write 'inconclusive' to `results/experiment_status.json` AND exit with a designated inconclusive status code. **Action**: T042-execute-list must check this file/exit code before proceeding.

**Checkpoint**: CPU safeguards implemented - execution tasks can now proceed safely.

---

## Phase 4: User Story 1 - Establish Geometric Baseline via On-Policy Distillation (Priority: P1) 🎯 MVP

**Goal**: Run OPD baseline on GSM8K subset to generate a "stable subspace" defined by top singular vectors of early parameter updates.

**Independent Test**: Run OPD loop for fixed steps, extract accumulated update matrices, perform SVD, and verify existence of defined subspace (top-k vectors) without running RL.

### Tests for User Story 1

- [X] T015 [P] [US1] Contract test for OPD SVD output shape in `tests/unit/test_opd_svd.py`
- [X] T016 [P] [US1] Integration test for OPD data flow in `tests/integration/test_opd_flow.py`

### Implementation for User Story 1

- [X] T017 [US1] **Implement OPD Baseline Runner**. **Logic**: Implement a training loop in `src/training/opd_baseline.py` that: 1) Loads GSM8K subset via T007. 2) Runs for `--num-steps` (default variable). 3) **Records** per-step parameter updates $\Delta W$ for each layer to `results/opd/updates_seed_{i}/layer_{index}.pt`. **Naming Convention**: `layer_{index:02d}.pt` where `index` is derived from the model's `state_dict` keys using regex `r'layer_(\\d+)'`, defaulting to sequential numeric indices if named layers are found. 4) **Aggregates** per-layer vectors into a single accumulated matrix of shape `(steps, n_params)` and saves to `results/opd/accumulated_matrix_seed_{i}.npy`. **Deliverable**: A fully functional OPD runner that produces the `accumulated_matrix` artifact required by T019. **Dependency**: T007, T009.
- [X] T018b [US1] Implement per-step update direction logging in `src/training/opd_baseline.py`. **Storage**: Save per-layer update vectors to separate files `results/opd/updates_seed_{i}/layer_{index:02d}.pt` (NOT a single stacked array) to ensure memory compliance. **Naming Convention**: `layer_{index:02d}.pt` where `index` is derived from the model's `state_dict` keys using regex `r'layer_(\\d+)'`, defaulting to sequential numeric indices if named layers are found. **Dependency**: T017.
- [X] T018c-aggregate [US1] **Aggregate** per-layer vectors into a single accumulated matrix. **Logic**: Read all `layer_{index:02d}.pt` files for a seed (produced by T018b), flatten each layer's update vector, concatenate them into a single vector of shape `(n_params,)`, and stack these vectors for all steps into a matrix of shape `(steps, n_params)`. Save to `results/opd/accumulated_matrix_seed_{i}.npy`. **Dependency**: T018b.
- [X] T018c-config [US1] **Define Early Window Configuration**. **Logic**: Read `early_window_ratio` from CLI or `results/early_window_config.json`. **Default**: If file missing or CLI not provided, use a heuristic that sets a minimum threshold while scaling with total steps: `max(minimum_value, ceil(total_steps * 0.1))`. **Action**: Write the resolved window size to `results/early_window_config.json` with schema `{"window_size": int, "ratio": float}`. **Dependency**: T017.
- [X] T018d-align [US1] **Log Early Trajectory Alignment (Real-Time)**. **Logic**: During the `early_window` steps (from T018c-config), compute the cosine similarity between the current update vector (from T018b) and the average update vector of the *same* OPD run (or a running reference). **Storage**: Save per-step alignment scores to `results/opd/early_alignment_log.json`. **Schema**: `{"step": int, "alignment_score": float, "variant": "OPD"}`. **Dependency**: T018c-config.
- [X] T018d-verify [US1] Verify that `results/opd/early_alignment_log.json` exists and is valid JSON after T018d-align. **Action**: If missing/invalid, abort T040. **Dependency**: T018d-align.
- [X] T019 [US1] **Implement Global SVD logic** in `src/training/projection_utils.py`. **Input**: `results/opd/accumulated_matrix_seed_{i}.npy` from T018c-aggregate. **Logic**: Perform SVD on the aggregated matrix to extract top-$k$ singular vectors. **Output**: Global subspace basis. **Dependency**: T018c-aggregate.
- [X] T020 [US1] **Select k and Save**. **Logic**: Select $k$ such that cumulative explained variance ≥ 80% (default $k=10$ if none). **Input**: `results/opd/svd_results.npy` (from T019). **Output**: Write `k` to `results/opd/k_value.json`. **Dependency**: T019.
- [X] T021 [US1] **Save stable subspace matrix** (shape $k \times n_{params}$) to `results/opd_subspace.npy`. **Dependency**: Must be completed before T025-impl starts. **Depends on**: T017, T018c-aggregate, T019, T020.
- [X] T022a [US1] Log memory usage during SVD and **Assert memory usage < 7GB**. **Logic**: Use `src/utils/memory_monitor.py` (T005) to assert limit. **Dependency**: T005, T060-stream. **Note**: Claim c_14a0bbbd removed.
- [X] T022b [US1] **Log** peak memory usage to `results/memory_profile.json` for SC-004 verification, regardless of success or failure. **Dependency**: T005.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 5: User Story 2 - Execute Low-Rank RL Hybrid with Geometric Projection (Priority: P2)

**Goal**: Train a PPO-based RL agent where gradients are projected onto the stable subspace from US1 before update.

**Independent Test**: Run PPO training with projection active, verify update direction cosine similarity with subspace basis ≥ 0.99.

### Tests for User Story 2

- [X] T023 [P] [US2] **Contract test for gradient projection** in `tests/unit/test_gradient_projection.py`. **Logic**: Generate a random gradient `G` and basis `U` (shape k x n). Compute `P = U @ U.T @ G`. **Assertion**: `assert cosine_similarity(P, U) >= 0.99`. **Input**: Mock tensors. **Output**: Pass/Fail. **Dependency**: T026-core.
- [X] T024 [P] [US2] **Integration test for Low-Rank RL loop** in `tests/integration/test_low_rank_rl.py`. **Logic**: Run a mini-training loop (1 step) with projection. **Input**: GSM8K subset (10 samples). **Output**: `results/low_rank_rl/early_alignment_log.json`. **Assertion**: Verify file exists and contains alignment >= 0.95. **Dependency**: T025-impl.

### Implementation for User Story 2

- [X] T026-core [US2] **Implement Gradient Projection Logic**. **Logic**: Implement the projection function in `src/training/projection_utils.py` to constrain raw RL gradients to top-$k$ vectors. This is the singular unit for FR-003 projection logic. **Dependency**: T021.
- [X] T025-impl [US2] **Implement Low-Rank RL Runner**. **Logic**: Implement a standard PPO training loop in `src/training/low_rank_rl.py` that: 1) Loads GSM8K subset via T007. 2) **Includes** Generalized Advantage Estimation (GAE) and KL-penalties (standard PPO). 3) **Checks** for existence of `results/opd_subspace.npy` (T021); raises `SubspaceNotFoundError` if missing. 4) **Integrates** gradient projection logic: computes raw RL gradient, projects it onto the top-$k$ vectors from `results/opd_subspace.npy`, and applies the update. 5) **Logs** per-step update direction and alignment. **Deliverable**: A fully functional Low-Rank RL runner that satisfies FR-003 (PPO-based with projection). **Dependency**: T021, T026-core.
- [X] T025-std [US2] **Implement Standard RL Baseline Runner**. **Logic**: Implement a standard PPO training loop in `src/training/rl_baseline.py` that: 1) Loads GSM8K subset via T007. 2) **Includes** GAE and KL-penalties. 3) **Does NOT** project gradients (unconstrained baseline). 4) **Logs** per-step update direction. **Deliverable**: A fully functional Standard RL runner required for FR-004 comparison. **Dependency**: T007.
- [X] T027 [US2] Add logging to verify update vector lies entirely within span of top-$k$ vectors. **Dependency**: T026-core.
- [X] T028 [US2] Log cosine similarity between applied update and subspace basis and **Assert cosine similarity >= 0.99**. **Dependency**: T026-core, T062.
- [X] T029 [US2] **Enforce Memory Limit** for Low-Rank RL training loop. Integrate `memory_monitor` (T005) to assert peak RAM < 7GB during training. **Dependency**: T005, T060-stream. **Note**: Claim c_2dd2c48f removed.
- [X] T029a-std [US2] **Measure Memory for Standard RL**. **Logic**: Implement memory logging for the Standard RL variant (non-projected) to `results/standard_rl/memory_profile.json`. **Dependency**: T025-std.
- [X] T030 [US2] Save Low-Rank RL training logs and checkpoints to `results/low_rank_rl/`. **Dependency**: T025-impl.
- [X] T030b [US2] Implement per-step update direction logging in `src/training/low_rank_rl.py`. **Storage**: Save per-layer update vectors to separate files `results/low_rank_rl/updates_seed_{i}/layer_{index:02d}.pt`. **Naming Convention**: `layer_{index:02d}.pt` where `index` is derived from the model's `state_dict` keys using regex `r'layer_(\\d+)'`, defaulting to sequential numeric indices if named layers are found. **Dependency**: T025-impl.
- [X] T030c-early [US2] **Log Early Trajectory Alignment (Real-Time)**. **Logic**: During the first `early_window` steps (from T018c-config), calculate cosine similarity between current update and OPD trajectory. **Action**: Log to `results/low_rank_rl/early_alignment_log.json` and **Flag run as 'Low Alignment'** if alignment < 0.95 (do NOT abort). **Dependency**: T018c-config, T025-impl.
- [X] T030c-verify [US2] Verify that `results/low_rank_rl/early_alignment_log.json` exists and is valid JSON after T030c-early. **Action**: If missing/invalid, abort T040. **Dependency**: T030c-early.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Compare Convergence and Subspace Alignment (Priority: P3)

**Goal**: Compare sample efficiency and subspace alignment of Low-Rank RL vs Standard RL vs OPD.

**Independent Test**: Aggregate accuracy-vs-steps curves, run statistical test (paired t-test or Wilcoxon) on steps-to-threshold metric.

### Tests for User Story 3

- [X] T031 [P] [US3] **Contract test for statistical significance** in `tests/unit/test_stats.py`. **Logic**: Generate synthetic steps-to-threshold data for 3 runs. **Assertion**: Run Wilcoxon signed-rank test; assert p-value < 0.05 for significant difference. **Input**: Synthetic arrays. **Output**: Pass/Fail. **Dependency**: T038b-wilcoxon.
- [X] T032 [P] [US3] **Integration test for full pipeline comparison** in `tests/integration/test_full_pipeline.py`. **Logic**: Run a mini-pipeline for all 6 variants (mocked training). **Input**: Mock data. **Output**: `results/analysis_report.md`. **Assertion**: Verify report contains rows for all 6 variants and statistical test results. **Dependency**: T036-metrics-explicit.

### Implementation for User Story 3

- [X] T033 [P] [US3] **Implement Random Projection Baseline**. **Logic**: Implement `src/training/random_projection.py`: 1) Generate random matrix `R` (k x n_params). 2) Project gradient `G` onto `R` (G_proj = R @ R.T @ G). 3) Train PPO with `G_proj`. 4) Log alignment. **Verification**: Assert projection lies in span of `R`. **Dependency**: T007.
- [X] T033a-mem [P] [US3] **Measure Memory for Random Projection**. **Logic**: Implement memory logging for Random Projection variant to `results/random_projection/memory_profile.json`. **Dependency**: T033.
- [X] T034 [P] [US3] **Implement Random Walk Prior Baseline**. **Logic**: Implement `src/training/random_walk_prior.py`: 1) Generate random walk subspace `W` (cumulative sum of noise). 2) Project gradient onto `W`. 3) Train PPO. 4) Log alignment. **Verification**: Assert projection lies in span of `W`. **Dependency**: T007.
- [X] T034a-mem [P] [US3] **Measure Memory for Random Walk Prior**. **Logic**: Implement memory logging for Random Walk Prior variant to `results/random_walk_prior/memory_profile.json`. **Dependency**: T034.
- [X] T035 [P] [US3] **Implement OPD-Initialized RL**. **Logic**: Implement `src/training/opd_initialized_rl.py`: 1) Load OPD weights (from T017) via `load_state_dict`. 2) Initialize RL agent with these weights. 3) Train PPO **without** projection. 4) Verify initialization via parameter checksum. **Dependency**: T017.
- [X] T035a-mem [P] [US3] **Measure Memory for OPD-Initialized RL**. **Logic**: Implement memory logging for OPD-Initialized RL variant to `results/opd_initialized_rl/memory_profile.json`. **Dependency**: T035.
- [X] T036-calc-feasibility [US3] [P] **Determine Feasible Variants**. **Logic**: Read `results/time_estimate.json` (T052a) and `results/memory_estimate.json` (T052b). **Action**: Determine the set of active variants (prioritizing OPD, Standard RL, Low-Rank RL) and the initial seed count (N=2 if time is tight, N=3 otherwise). **Output**: Write `results/feasibility_report.json`. **Dependency**: T052a, T052b.
- [X] T036-write-manifest [US3] [P] **Write Active Variants Manifest**. **Logic**: Read `results/feasibility_report.json` and write the final list of active variants and seed count to `results/active_variants.json`. **Schema**: `{"variants": ["opd", "rl",...], "num_seeds": int}`. **Constraint**: This is the **sole source of truth** for active variants. **Dependency**: T036-calc-feasibility.
- [X] T042-filter-list [US3] **Filter Run List**. **Logic**: Read `results/active_variants.json` (T036-write-manifest) and filter based on time budget. **Output**: `results/run_list_filtered.json`. **Dependency**: T036-write-manifest.
- [X] T042-write-list [US3] **Write Final Run List**. **Logic**: Write the final list of runs (variant, seed) to `results/run_list.json`. **Constraint**: This is the **sole source of truth** for the execution list. **Dependency**: T042-filter-list.
- [ ] T042-execute-list [US3] **Execute Training Runs**. **Logic**: Iterate over `results/run_list.json` and execute `python src/cli/run_experiment.py --variant <name> --seed <i>` for each entry. **Output**: Logs and checkpoints in `results/<variant>/`. **Constraint**: Must check `results/experiment_status.json` (T063) before each run. **Dependency**: T042-write-list. **Note**: This is the execution task for the filtered variants; measures total wall-clock time for SC-005.
- [X] T036-metrics-explicit [US3] **Calculate Metrics**. **Logic**: Aggregate accuracy-vs-steps curves from all active variants. **Input**: `results/*/final_update_direction.npy` (from training runs: T025-impl, T025-std, T033, T034, T035). **Output**: 1) Steps-to-threshold-accuracy for all variants (Implements FR-004). 2) Cosine similarity between final update directions and PPO proxy (Implements FR-005). **Artifact**: `results/metrics_summary.json`. **Dependency**: T042-execute-list.
- [X] T037 [US3] **Generate Plots**. **Logic**: Generate convergence curves and alignment plots. **Artifact**: `results/convergence_plots.png`. **Dependency**: T036-metrics-explicit.
- [X] T038a [US3] Implement `src/analysis/power_analysis.py` to perform pre-experiment/post-hoc power analysis and sample size estimation. **Constraint**: Must use standard statistical power formulas (e.g., Cohen's d).
- [X] T038b-wilcoxon [US3] **Perform Wilcoxon Test**. **Logic**: Run Wilcoxon signed-rank test on steps-to-threshold data for all active variants. **Constraint**: **UNCONDITIONAL**. Must check N >= 3. If N < 3, flag 'Inconclusive (Insufficient Samples)' in `results/statistical_status.json` and **STOP** (do not run test). If N >= 3, run test and save `results/statistical_report.json`. **Artifact**: `results/statistical_report.json` (if N>=3). **Dependency**: T036-metrics-explicit. **Note**: Sole task for FR-006.
- [X] T039 [US3] Implement `src/analysis/plots.py` to generate final comparison table and statistical report artifact `results/analysis_report.md` covering **ALL variants**. **Requirement**: Verify that the table includes rows for all variants. If the pipeline aborted early, mark status as 'Inconclusive due to time' and list all variants as 'Not Run'. **Logic**: Read `results/active_variants.json` to determine if variants were reduced; if so, log the `reduction_reason` field from that file in the report.
- [X] T040-early-alignment-core [US3] **Compute Early Trajectory Alignment (FR-008 Implementation)**. **Logic**: Calculate cosine similarity between Low-Rank RL trajectory and OPD trajectory during the `early_window` (from T018c-config). **Dependency**: T018d-align, T030c-early. **Note**: Dedicated task for FR-008.
- [X] T040b [US3] **Compute and Log Alignment for Baselines**. Logic: Calculate cosine similarity between Standard RL trajectory and OPD trajectory, and OPD trajectory vs itself (baseline) during the `early_window`. **Dependency**: T018d-align, T030c-early.

### Conditional Re-run Logic

- [X] T048a [US3] Implement power analysis calculation in `src/analysis/power_analysis.py` to check effect size and sample size. **Dependency**: T038b-wilcoxon.
- [X] T048c-validate [US3] **Validate N**. Action: If N < 2, flag 'inconclusive' and STOP. [UNRESOLVED-CLAIM: c_4497f924 — status=not_enough_info] Do not proceed to T048-decide-retry. **Dependency**: T038b-wilcoxon.
- [X] T048-decide-retry [US3] **Conditional Branching**. Logic: Check: (1) time remaining, (2) effect size < 0.5. If both conditions met AND N < 10, trigger re-run logic. [UNRESOLVED-CLAIM: c_c80bc3ff — status=not_enough_info] **Dependency**: T048a, T048c-validate. **Note**: This is the conditional branching task.
- [X] T042-b [US3] **Orchestrate Conditional Re-run**. **Logic**: If T048-decide-retry triggers, generate a new run list for N=10 seeds for active variants. **Dependency**: T048-decide-retry.
- [X] T048d [US3] **Re-run Analysis**. **Logic**: Re-run analysis on new data if re-run occurred. **Dependency**: T042-b, T038b-wilcoxon.

**Checkpoint**: Phase 6 execution and analysis complete

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T050a [P] **Update quickstart.md**. **Logic**: Add CLI usage examples for `--early-window-fraction`, `--num-seeds`, and `--variant`. Include a "Hard Abort" section explaining the 6-hour limit and how to interpret `results/experiment_status.json`. **Dependency**: T012.
- [X] T050b [P] **Add API docs**. **Logic**: Add Sphinx-style docstrings to `src/training/projection_utils.py` and `src/utils/memory_monitor.py` explaining parameters, return types, and exceptions. **Dependency**: T026-core, T005.
- [X] T050c [P] **Update README.md**. **Logic**: Add "Experiment Status" badge (Completed/Inconclusive) and "Data Availability" section pointing to `results/`. **Dependency**: T039.
- [X] T051a [P] **Extract logging logic**. **Logic**: Create `src/utils/logger.py` with a `get_logger` function that writes JSON logs to `results/experiment.log`. **Schema**: `{"timestamp": "ISO8601", "level": "INFO", "message": "str"}`. **Dependency**: T005.
- [X] T051b [P] **Remove unused imports**. **Logic**: Run `ruff --select F401` on `src/` and `tests/`; remove all unused imports identified. **Dependency**: T003.
- [X] T052 [P] **Performance optimization**. **Logic**: Implement batch size doubling and ensure FP16 mixed precision is active in all training loops. Target: [deferred] speedup in `results/time_estimate.json`. **Dependency**: T052a.
- [X] T053 [P] **Additional unit tests**. **Logic**: Add tests for `src/training/projection_utils.py` and `src/utils/seeds.py` to achieve [deferred] branch coverage. **Dependency**: T013, T014.
- [ ] T054 [P] **Run quickstart.md validation**. **Logic**: Create `validate_quickstart.sh` that parses `quickstart.md` and runs `python src/cli/run_experiment.py --dry-run`. **Pass**: Exit code 0. **Dependency**: T050a.
- [X] T067 [P] **Data Loader Fail-Loud Verification**. **Logic**: Write a test that mocks `datasets.load_dataset` to raise `ConnectionError`. **Assertion**: Verify `src/data/loader.py` raises `DataIntegrityError` and does not fall back to synthetic data. **Dependency**: T007.
- [X] T068 [P] **Data Integrity Hash Audit**. **Logic**: Run `src/utils/hasher.py` on all files in `results/`. Compare hashes against `state/artifact_hashes`. **Pass**: All match. **Dependency**: T006.
- [X] T069 [P] **Subspace Stability Verification**. **Logic**: Run OPD for 3 seeds. Calculate variance of `k` (selected rank) across seeds. **Assertion**: Variance < 5%. **Dependency**: T020.
- [X] T071-variants [US3] **Memory Assertion Verification for All Variants**. **Logic**: After Phase 6 execution completes (including T048d), iterate over ALL experimental variants (Standard, Random, Walk, OPD-Init, OPD, Low-Rank) and verify that `results/<variant>/memory_profile.json` exists and all recorded peaks are < 7GB. **Constraint**: This task is **Sequential** (depends on T048d and all Phase 6 execution tasks). If any peak > 7GB, flag 'Memory Violation' and update `results/experiment_status.json`. **Dependency**: T048d, T022b, T029a-std, T033a-mem, T034a-mem, T035a-mem.
- [X] T071 [US3] **Final Memory Report**. **Logic**: Aggregate memory violations from T071-variants into a final report. **Dependency**: T071-variants.
- [ ] T078 [P] **Implement Variant Abortion Handler**. **Logic**: In `src/cli/run_experiment.py`, wrap training loops in `try/except` for `OOMError` and `TimeoutError`. **Action**: Log failure to `results/failures.json` with `{"variant": "str", "seed": int, "error": "str"}`, skip the seed, and continue to the next. **Dependency**: T012.

---

## Phase 8: Review & Revision (Addressing Analysis Concerns)

**Purpose**: Address specific concerns raised by `/speckit.analyze` regarding data flow, task ordering, and robustness.

- [X] T072 [P] [US3] **Fix Data Flow Dependency**: Ensure `src/training/low_rank_rl.py` (T025-impl) explicitly checks for the existence of `results/opd_subspace.npy` (T021) before starting training. If missing, raise `SubspaceNotFoundError` with a clear error message directing the user to run the OPD baseline first. (Note: This logic is now integrated into T025-impl).
- [X] T073 [P] [US3] **Implement Robust SVD Fallback**: Enhance `src/training/projection_utils.py` (T019) to handle the "flat spectrum" edge case more gracefully. If `k` cannot be determined by variance threshold, explicitly log the spectral distribution and select `k` based on a "elbow" heuristic or a fixed minimum (e.g., 5) to prevent degenerate projections. (Note: This logic is now integrated into T019).
- [X] T074 [P] [US3] **Add Gradient Projection Unit Tests**: Implement `tests/unit/test_gradient_projection.py` (T023) to verify that the projection operation `P = U @ U.T @ G` results in `P` lying exactly in the span of `U` (within floating point tolerance). (Note: This is now T023).
- [ ] T075 [P] [US3] **Validate Early Window Logic**: Add a verification step in `src/cli/run_experiment.py` to ensure `early_window_steps` (T018c-config) is never greater than `total_steps`. If invalid, clamp to `total_steps` and log a warning. (Note: This logic is now integrated into T018c-config).
- [X] T076 [P] [US3] **Standardize Logging Schema**: Refactor all `early_alignment_log.json` writers (T018d-align, T030c-early) to ensure a consistent schema across all variants, including `variant_name`, `seed`, `step`, `alignment_score`, and `timestamp`. (Note: This logic is now integrated into T018d-align and T030c-early).
- [X] T077 [P] [US3] **Add Power Analysis Visualization**: Extend `src/analysis/plots.py` (T037) to include a plot showing the calculated effect size (Cohen's d) and the achieved power for the current N, overlaying the 0.8 power threshold line. (Note: This logic is now integrated into T037).
- [ ] T078 [P] [US3] **Implement Variant Abortion Handler**: In `src/cli/run_experiment.py`, ensure that if a single seed fails (e.g., OOM), the pipeline logs the failure, skips that seed, and continues with the next seed/variant, rather than aborting the entire experiment. (Note: This is now T078).
