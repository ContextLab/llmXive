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

**Time Budget & Abort Strategy**: The time limit is strict. T053 implements a "Hard Abort" strategy. If the pre-flight estimation (T052a/b) indicates the N=3 runs will exceed 6 hours, the entire pipeline aborts immediately. NO variant reduction is permitted. All 6 variants [UNRESOLVED-CLAIM: c_1525f263 — status=not_enough_info] defined in the spec must run, or the experiment is declared 'Inconclusive due to time'.

**Time Budget & Reduction**: The time limit is strict. T056 implements a "Variant Reduction Strategy" that triggers at [deferred] of the time budget. If a critical baseline (Standard RL, OPD, Low-Rank RL) is dropped, the experiment flags 'Inconclusive'.

**Early Window Definition**: The "early trajectory" window is defined by `results/early_window_config.json` (T018c). T018c writes the resolved window size (default or CLI override) and logs a warning if the default is used. **No manual approval step is required**; the pipeline proceeds automatically.

**Data Integrity & Failure Policy**: All data loaders (T007) MUST fail loudly if the real GSM8K fetch fails. No synthetic fallbacks permitted. If a verified real data source is injected by the execution stage, T007 must adopt that exact package/recipe immediately.

**Pruning Strategy (T009)**: Target 300M ± 1% (297M-303M). [UNRESOLVED-CLAIM: c_c0e70e41 — status=not_enough_info] **Fallback Logic**: If exact target cannot be met, prune to the **closest available verified model size** (e.g., 290M or 310M) and log a `WARNING: Target 300M unreachable, using closest verified size {size}`. **Abort only if no verified model size is available**. Include verification logic to validate the pruned model architecture.

**CPU Feasibility & Scaling**: All training tasks (T043-T047) are explicitly constrained to CPU-only execution (2 vCPU, 7GB RAM [UNRESOLVED-CLAIM: c_f1e7f089 — status=not_enough_info]) with a 6-hour wall-clock limit. Phase 3 (CPU Feasibility) MUST be completed before Phase 5 (Execution) to ensure streaming and memory safeguards are in place. **NO** GPU tasks are permitted in this revision; the "Real Data + Real Results" rule is satisfied by streaming the GSM8K subset and processing in chunks.

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
- [X] T007 Create `src/data/loader.py` to fetch GSM8K subset (≥1,000 problems) [UNRESOLVED-CLAIM: c_8c05c0c6 — status=not_enough_info] from HuggingFace `datasets` with checksum verification. **Constraint**: Must raise an exception immediately if fetch fails; NO synthetic fallbacks.
- [X] T008 Create `src/data/checksums.py` for data integrity verification
- [X] T009 Implement `src/models/config.py` to programmatically prune `TinyLlama` to a reduced parameter scale. **Target**: 300M ± 1% (297M-303M). **Strategy**: 1) Remove layers from end until target range met. 2) If overshoot, remove attention heads from last remaining layer. 3) **Fallback**: If target not met, use **closest available verified model size** and log warning. 4) **Abort** only if no verified model size is available. **Include verification logic** to validate the pruned model architecture.
- [X] T010 Implement `src/models/backbone.py` with hooks to capture attention projection updates
- [X] T012 Create `src/cli/run_experiment.py` as the single entry point orchestrating all training and analysis. **Requirement**: Must define `--early-window-fraction`, `--early-alignment-threshold`, and `--num-seeds` CLI arguments.
- [X] T013 [P] Create `tests/unit/test_svd.py` to verify SVD on small matrices fits memory constraints
- [X] T014 [P] Create `tests/unit/test_projection.py` to verify projection math (cosine similarity ≥ 0.99 [UNRESOLVED-CLAIM: c_c5e4add5 — status=not_enough_info])

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: CPU Feasibility & Resource Hardening (Mandatory Prerequisites)

**Purpose**: Implement streaming, online stats, and time/memory enforcement to ensure CPU feasibility BEFORE execution. **This phase is a strict prerequisite for all User Story execution tasks.**

- [X] T059 [P] [US1/US2/US3] **Refactor** `src/data/loader.py` to use `datasets.load_dataset(..., streaming=True)`. **Logic**: Iterate over the GSM8K split in chunks (e.g., 100 examples) to process the full dataset without loading it entirely into RAM. **Constraint**: Must not use `.to_list()` or `.map()` on the full dataset before iteration. **Action**: Update T007 to use this streaming approach for all training runs.
- [ ] T060 [P] [US1/US2/US3] Implement **online statistics accumulator** in `src/analysis/metrics.py` for convergence metrics. **Logic**: Instead of storing all accuracy curves in memory, update running means/variances and save intermediate checkpoints to disk every N steps. **Artifact**: `results/online_stats_checkpoint.json`. **Constraint**: Ensure memory footprint remains < 7GB even with N=10 seeds [UNRESOLVED-CLAIM: c_c1b974dc — status=not_enough_info].
- [ ] T061 [P] [US1] Add **SVD fallback logic** in `src/training/projection_utils.py` for "flat spectrum" edge cases. **Logic**: If cumulative variance < 80% for any $k \le 50$, default to $k=10$ [UNRESOLVED-CLAIM: c_00d249dc — status=refuted] and log a `WARNING: Flat spectrum detected, using fixed k=10`. **Constraint**: Do not abort; proceed with fixed $k$ to maintain experiment continuity.
- [ ] T062 [P] [US2] Implement **gradient projection sanity check** in `src/training/low_rank_rl.py` to verify projection matrix is well-conditioned. **Logic**: Check condition number of the subspace matrix; if > 1e6, log `WARNING: Ill-conditioned subspace` and re-normalize vectors before projection.
- [ ] T063 [P] [US3] Add **time-budget enforcement** in `src/cli/run_experiment.py` that strictly aborts the current seed and flags 'inconclusive' if the 6-hour limit is exceeded before N=3 for all active variants is reached. **Constraint**: Must write 'inconclusive' to `results/experiment_status.json` AND exit with code 42. **Action**: T042-a-run must check this file/exit code before proceeding.

**Checkpoint**: CPU safeguards implemented - execution tasks can now proceed safely.

---

## Phase 4: User Story 1 - Establish Geometric Baseline via On-Policy Distillation (Priority: P1) 🎯 MVP

**Goal**: Run OPD baseline on GSM8K subset to generate a "stable subspace" defined by top singular vectors of early parameter updates.

**Independent Test**: Run OPD loop for fixed steps, extract accumulated update matrices, perform SVD, and verify existence of defined subspace (top-k vectors) without running RL.

### Tests for User Story 1

- [ ] T015 [P] [US1] Contract test for OPD SVD output shape in `tests/unit/test_opd_svd.py`
- [ ] T016 [P] [US1] Integration test for OPD data flow in `tests/integration/test_opd_flow.py`

### Implementation for User Story 1

- [ ] T017 [US1] Implement `src/training/opd_baseline.py` runner for GSM8K subset (capped steps). **Status**: Not implemented.
- [ ] T018 [US1] Implement logic in `src/training/opd_baseline.py` to record $\Delta W$ matrices for the initial phase of training (after every optimizer step). Save list of tensors to `results/opd/updates_seed_{i}.pt`. **Status**: Not implemented.
- [ ] T018b [US1] Implement per-step update direction logging in `src/training/opd_baseline.py`. **Storage**: Save per-layer update vectors to separate files `results/opd/updates_seed_{i}/layer_{index:02d}.pt` (NOT a single stacked array) to ensure memory compliance. **Naming Convention**: `layer_{index:02d}.pt` where `index` is derived from the model's `state_dict` keys using regex `layer_(\\d+)`, defaulting to sequential numeric indices if named layers are found.
- [ ] T018c [US1] Implement logic in `src/analysis/metrics.py` to define the 'early' window. **Logic**: Read `early_window_ratio` from CLI or `results/early_window_config.json`. **Default**: If file missing or CLI not provided, use `max(50, ceil(total_steps * 0.10)) ` and log `WARNING: Using default window`. **Action**: Write the resolved window size to `results/early_window_config.json`. **Status**: Not implemented.
- [ ] T019 [US1] Implement **layer-wise SVD logic** in `src/training/projection_utils.py` for accumulated updates
- [ ] T020 [US1] Implement logic to select $k$ such that cumulative explained variance ≥ 80% (default $k=10$ if none)
- [ ] T021 [US1] **Save stable subspace matrix** (shape $k \times n_{params}$) to `results/opd_subspace.npy`. **Dependency**: Must be completed before T026-impl starts. **Depends on**: T017, T018.
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

- [ ] T025 [US2] Implement `src/training/rl_baseline.py` with **lightweight PPO loop using torch.optim** (no external RL libs) and logging schema: steps, accuracy, loss. **Status**: Not implemented.
- [ ] T026-impl [US2] Implement `src/training/low_rank_rl.py` loading subspace from `results/opd_subspace.npy` (Depends on T021 completion). **Constraint**: Phase 5 cannot start until T021 is marked complete. **Dependency**: T059 (Streaming), T060 (Online Stats).
- [ ] T027 [US2] Implement **gradient projection logic** in `low_rank_rl.py` to constrain raw RL gradients to top-$k$ vectors
- [ ] T028 [US2] Add logging to verify update vector lies entirely within span of top-$k$ vectors
- [ ] T029 [US2] Log cosine similarity between applied update and subspace basis and **Assert cosine similarity >= 0.99 **; raise exception if violated.
- [ ] T029a [US2] **Enforce memory limit** for Low-Rank RL training loop. **Logic**: Integrate `memory_monitor` to assert peak RAM < 7GB during training. **Action**: Abort if limit exceeded.
- [ ] T030 [US2] Save Low-Rank RL training logs and checkpoints to `results/low_rank_rl/`
- [ ] T030b [US2] Implement per-step update direction logging in `src/training/low_rank_rl.py`. **Storage**: Save per-layer update vectors to separate files `results/low_rank_rl/updates_seed_{i}/layer_{index:02d}.pt` (NOT a single stacked array). **Naming Convention**: `layer_{index:02d}.pt` where `index` is derived from the model's `state_dict` keys using regex `layer_(\\d+)`, defaulting to sequential numeric indices if named layers are found.
- [ ] T030c-impl [US2] Implement real-time "Early Trajectory Alignment" logging in `src/training/low_rank_rl.py`. **Logic**: During the first `early_window` steps (from T018c config), calculate cosine similarity between current update and OPD trajectory. **Action**: Log to `results/low_rank_rl/early_alignment_log.json` and **Flag run as 'Low Alignment'** if alignment < 0.95 [UNRESOLVED-CLAIM: c_d5ba9b45 — status=not_enough_info] (do NOT abort).
- [ ] T030c-verify [US2] **Verify** that `results/low_rank_rl/early_alignment_log.json` exists and is valid JSON after T030c-impl. **Action**: If missing/invalid, abort T040.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Compare Convergence and Subspace Alignment (Priority: P3)

**Goal**: Compare sample efficiency and subspace alignment of Low-Rank RL vs Standard RL vs OPD.

**Independent Test**: Aggregate accuracy-vs-steps curves, run statistical test (Wilcoxon) on steps-to-threshold metric.

### Tests for User Story 3

- [ ] T031 [P] [US3] Contract test for statistical significance in `tests/unit/test_stats.py`
- [ ] T032 [P] [US3] Integration test for full pipeline comparison in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement `src/training/random_projection.py` (Random Baseline)
- [ ] T033a [US3] **Enforce memory limit** for Random Projection training loop.
- [ ] T034 [P] [US3] Implement `src/training/random_walk_prior.py` with random walk subspace projection logic
- [ ] T034a [US3] **Enforce memory limit** for Random Walk Prior training loop.
- [ ] T035 [P] [US3] Implement `src/training/opd_initialized_rl.py` with OPD weight initialization and no projection
- [ ] T035a [US3] **Enforce memory limit** for OPD-Initialized RL training loop.
- [ ] T036-gen [US3] [P] **Generate** `results/active_variants.json`. **Logic**: Read time budget and variant constraints; write the list of active variants. **Error Handling**: If generation fails, raise a clear error: "Failed to generate active_variants.json". **Dependency**: T056.
- [ ] T036-calc [US3] [P] Implement `src/analysis/metrics.py` to calculate steps-to-threshold-accuracy for **ACTIVE variants**. **Requirement**: Explicitly iterate over the list of active variant keys to ensure all are included in the comparison table. **Error Handling**: If `results/active_variants.json` is missing, raise a clear error: "Missing active_variants.json. Ensure T036-gen has completed." **Note**: This is not a stub; it handles the missing file case explicitly.
- [ ] T037 [US3] Implement `src/analysis/metrics.py` to compute cosine similarity between final update directions and PPO proxy
- [ ] T038a [US3] Implement `src/analysis/power_analysis.py` to perform pre-experiment/post-hoc power analysis and sample size estimation. **Constraint**: {{claim:c_bb1acb93}} (Wikidata Q25503169, https://www.wikidata.org/wiki/Q25503169).
- [ ] T038b-a [US3] Implement Wilcoxon signed-rank test logic in `src/analysis/metrics.py` (N=3 minimum) with dynamic power calculation and conditional re-run flagging.
- [ ] T039 [US3] Implement `src/analysis/plots.py` to generate convergence curves and alignment plots
- [ ] T041-impl [US3] Implement `src/analysis/plots.py` to generate final comparison table and statistical report artifact `results/analysis_report.md` covering **ALL variants**. **Requirement**: Verify that the table includes rows for all 6 variants [UNRESOLVED-CLAIM: c_1525f263 — status=not_enough_info]. If the pipeline aborted early, mark status as 'Inconclusive due to time' and list all variants as 'Not Run'.
- [ ] T041-exec [US3] **Execute** T041-impl logic to generate `results/analysis_report.md`. **Depends on**: T041-impl, T036-exec, T038c.

### Execution Tasks (N=3 Seeds per Variant, Strict Abort Policy)

- [ ] T056 [US3] **Orchestrate** generation of the run list based on time budget. **Action**: Read time budget, determine active variants (Critical: OPD, Standard RL, Low-Rank RL), and write `results/active_variants.json`. **Constraint**: Must complete BEFORE T042-a-gen. **No [P] flag**; this is a sequential prerequisite. **Status**: Not implemented.
- [ ] T057 [US3] Update `src/cli/run_experiment.py` to integrate `variant_reducer` logic, ensuring it aborts pending runs and triggers the "inconclusive" flag if the time budget is exceeded before statistical significance is reached.
- [ ] T058 [US3] [P] Implement a "Time Budget Monitor" thread in `src/cli/run_experiment.py` (not `memory_monitor.py`) that logs a warning at a high percentage of the 6-hour limit and triggers the reduction strategy. **Constraint**: Must enforce minimum N=3; if N=3 cannot be completed, flag 'inconclusive' and stop. **Status**: Not implemented.

- [ ] T042-a-gen [US3] **Orchestrate** generation of the run list based on T056 output. **Action**: Read `results/active_variants.json`, filter variants, and write `results/run_list.json`. **Dependency**: T056.
- [ ] T042-a-run [US3] **Orchestrate** initial training runs for **ACTIVE variants** (filtered by T042-a-gen) with **N=3 seeds**. **Depends on**: T042-a-gen, T056, T059-T063 (Phase 3), T063 (Time Budget Check). **Action**: Execute `src/cli/run_experiment.py --run-list results/run_list.json --seeds 3`. If list is empty, flag 'inconclusive' and stop. **Status**: Not implemented.
- [ ] T043 [US3] Execute training runs for OPD Baseline (N=3 seeds) via CLI (Managed by T042-a-run)
- [ ] T043b [US3] Execute training runs for Low-Rank RL (N=3 seeds) via CLI (Managed by T042-a-run)
- [ ] T044 [US3] Execute training runs for Standard RL (N=3 seeds) via CLI (Managed by T042-a-run)
- [ ] T045 [US3] Execute training runs for Random Projection Baseline (N=3 seeds) via CLI (Managed by T042-a-run)
- [ ] T046 [US3] Execute training runs for Random Walk Prior Baseline (N=3 seeds) via CLI (Managed by T042-a-run)
- [ ] T047 [US3] Execute training runs for OPD-Initialized RL (N=3 seeds) via CLI (Managed by T042-a-run)
- [ ] T036-exec [US3] Execute metrics calculation (T036-calc logic) on generated logs from T043-T047
- [ ] T040 [US3] Compute Early Trajectory Alignment (first `early_window` steps, min) between Low-Rank RL and OPD using logged $\Delta W_t$ vectors (Depends on T018c config, T030c-verify, and T043/T043b execution logs). **Output**: Write alignment scores to `results/early_alignment_scores.json`. **Status**: Not implemented.
- [ ] T038b-d [US3] Execute Wilcoxon signed-rank test on N=3 seeds per variant (FR-006) and generate p-values (Depends on T036-exec, T040)
- [ ] T038c [US3] Generate statistical report artifact in `results/statistical_report.md` containing p-values and effect sizes
- [ ] T048a [US3] Implement power analysis calculation in `src/analysis/power_analysis.py` to check effect size and sample size.
- [ ] T048b [US3] Implement conditional branching logic in `src/analysis/power_analysis.py` to check: (1) time remaining, (2) effect size < 0.5 [UNRESOLVED-CLAIM: c_71e51909 — status=not_enough_info]. If both conditions met AND N < 10, prepare for re-run.
- [ ] T048c-check [US3] **Validate N >= 3**. **Action**: If N < 3, flag 'inconclusive' and **STOP**. Do not proceed to T048c-branch.
- [ ] T048c-branch [US3] Execute conditional branching: if effect size < 0.5 [UNRESOLVED-CLAIM: c_71e51909 — status=not_enough_info] AND N < 10 AND time > 15% remaining [UNRESOLVED-CLAIM: c_d91a73c6 — status=refuted], trigger re-run logic. **Depends on**: T048c-check, T048b, T040, T038b-d.
- [ ] T042-b [US3] **Orchestrate** conditional re-run for **ACTIVE variants** with **N=10 seeds [UNRESOLVED-CLAIM: c_c1b974dc — status=not_enough_info]** if T048c-branch triggers. **Triggered by**: T048c-branch.
- [ ] T048d [US3] Re-run analysis (T036-exec, T038b-d, T038c) on new data if re-run occurred (Depends on T042-b completion).
- [ ] T055 [US3] Verify all `results/` artifacts have SHA-256 hashes recorded in `state/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050a [P] Update `quickstart.md` with CLI usage examples and hard abort explanation.
- [ ] T050b [P] Add API docs for `src/training/projection_utils.py` and `src/utils/memory_monitor.py`.
- [ ] T050c [P] Update `README.md` with experiment status and data availability notes.
- [ ] T051a [P] Extract logging logic to `src/utils/logger.py`.
- [ ] T051b [P] Remove unused imports and refactor training loops for clarity.
- [ ] T052 Performance optimization for CPU execution (batching, mixed precision)
- [ ] T053 [P] Additional unit tests in `tests/unit/`
- [ ] T054 Run quickstart.md validation to ensure 6-hour limit compliance (with N=3 seed count and all variants)
- [ ] T061 [P] **Data Loader Fail-Loud Verification**: Run T007, T033, T034, T035 with simulated network failure to verify they raise exceptions and do NOT fall back to synthetic data. **Output**: `results/verification/fail_loud_test_report.md`.
- [ ] T062 [P] **Memory Assertion Verification**: Run T022a and T029 with artificially inflated memory usage to verify they raise exceptions and do NOT silently degrade.
- [ ] T063 [P] **Streaming Validation**: Execute a dry-run of T007b with a simulated large dataset to verify `streaming=True` and `islice` logic correctly processes chunks without OOM.
- [ ] T064 [P] **Reproducibility Audit**: Run the full pipeline twice with the same seed and verify `results/` artifacts match exactly (bit-for-bit) to confirm deterministic behavior.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **CPU Feasibility (Phase 3)**: Depends on Foundational (Phase 2) - **BLOCKS Execution (Phase 5/6)**
- **User Stories (Phase 4-6)**: All depend on Foundational (Phase 2) and CPU Feasibility (Phase 3)
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) and CPU Feasibility (Phase 3) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) and CPU Feasibility (Phase 3) - **HARD DEPENDENCY**: T021 (Save stable subspace matrix) must be complete before T026-impl starts. **Dependency**: T059, T060.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) and CPU Feasibility (Phase 3) - Depends on US1 and US2 outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational and CPU Feasibility phases complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for OPD SVD output shape in tests/unit/test_opd_svd.py"
Task: "Integration test for OPD data flow in tests/integration/test_opd_flow.py"

# Launch all implementation for User Story 1:
Task: "Implement src/training/opd_baseline.py runner"
Task: "Implement layer-wise SVD logic in src/training/projection_utils.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: CPU Feasibility (CRITICAL - blocks execution)
4. Complete Phase 4: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (SVD output, memory usage)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational + CPU Feasibility → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + CPU Feasibility together
2. Once Foundation is done:
 - Developer A: User Story 1 (OPD Baseline)
 - Developer B: User Story 2 (Low-Rank RL)
 - Developer C: User Story 3 (Analysis & Baselines)
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
- **CRITICAL**: All training must run on CPU-only (2 vCPU, 7GB RAM [UNRESOLVED-CLAIM: c_f1e7f089 — status=not_enough_info]) within 6 hours. No GPU, no low-precision quantization.
- **CRITICAL**: Use real GSM data from HuggingFace; no synthetic data or fabrication.
- **NOTE**: T042-a-run orchestrates N=3 pilot runs for ACTIVE variants (filtered by T056). T042-b handles conditional re-runs to N=10 if power analysis requires and time permits.
- **NOTE**: T018c defines the 'early' window via `results/early_window_config.json` (Automated default or CLI override).
- **NOTE**: T030c-verify ensures the log file exists before T040 begins.
- **NOTE**: T040 (Compute Early Trajectory Alignment) is executed BEFORE T048c-branch to ensure the metric is available for the re-run decision.
- **NOTE**: T048c-check enforces a hard constraint: N must be at least 3. If N < 3, the experiment flags 'inconclusive' and stops.
- **NOTE**: T042-b is triggered by T048c-branch and managed by the CLI orchestration logic, not by itself.
- **NOTE**: T007 must strictly adhere to the "Fail Loudly" policy: if the real GSM8K fetch fails, the process must crash immediately. No synthetic fallbacks are permitted.
- **NOTE**: If a verified real data source is injected by the execution stage, T007 must adopt that exact package/recipe immediately.
- **NOTE**: T009 targets 300M ± 1% with a fallback to closest verified size if target is missed.
- **NOTE**: T059-T063 (Phase 3) are mandatory prerequisites for Execution (Phase 5/6). They must be completed before T042-a-run to ensure the experiment runs within the 6-hour limit and 7GB RAM constraint without fabrication.
- **NOTE**: T056 is a sequential prerequisite for T042-a-gen and T036-gen, not a parallel task.
- **NOTE**: T029a-T035a enforce memory limits for all RL variants, satisfying SC-004.
- **NOTE**: T017 and T018 are currently **Not Implemented** and must be completed before T021.