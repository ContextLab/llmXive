# Tasks: Low-Rank RL for Foresight in LLM Training

**Input**: Design documents from `/specs/001-low-rank-rl-foresight/`
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

---

## Implementation Notes

**Time Budget & Abort Strategy**: The time limit is strict. T053 implements a "Hard Abort" strategy. If the pre-flight estimation (T052a/b) indicates the N=3 runs will exceed 6 hours, the entire pipeline aborts immediately. NO variant reduction is permitted. All 6 variants defined in the spec must run, or the experiment is declared 'Inconclusive due to time'.

**Early Window Definition**: The "early trajectory" window is defined dynamically as the first 10% of the total training trajectory (or a fixed minimum of 50 steps if total steps < 500). This is calculated in T018c-gen. The value is configurable via `--early-window-fraction` CLI argument.

**Data Integrity & Fail-Loud**: All data loading tasks (T007, T033, T034, T035) MUST raise an exception if the real GSM8K dataset cannot be fetched from the verified HuggingFace source. NO synthetic fallbacks, mocks, or random data generation are permitted. A failed fetch must cause the run to fail immediately.

**Memory Management**: All SVD and training operations must strictly adhere to the available RAM limit. Layer-wise processing and streaming are mandatory. T022a and T029 enforce hard assertions that raise exceptions if limits are violated.

**Model Pruning**: T009 must generate a valid `transformers.PretrainedConfig` object. It selects the closest available layer count to 300M parameters without a strict 5% tolerance band, adhering to the spec's "M parameter model" approximation.

**Streaming & Sampling**: T007 implements streaming for GSM8K to avoid OOM. If a full sample is required for a specific variant, T007b implements a deterministic sampling strategy (`itertools.islice` with seed) to ensure reproducibility and honesty about sample size limitations.

**Statistical Rigor**: The experiment enforces N=3 independent seeds per variant as the strict baseline (FR-006). No dynamic increase to N=10 is permitted in this implementation. If N=3 cannot be completed within the time budget, the experiment aborts (T053) rather than weakening the design.

**Non-Convergence Handling**: Tb explicitly handles cases where a variant does not reach the 80% accuracy threshold. The output CSV uses a string sentinel "Did Not Converge" for such cases, and the analysis script (T038b-d) handles this via `dtype=object`.

**Alignment Threshold**: The alignment threshold for "Early Trajectory Alignment" is not hardcoded. It is read from the CLI argument `--early-alignment-threshold` (default 0.95) and stored in the config, ensuring it is not a silent narrowing of the spec.

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
- [X] T007 Create `src/data/loader.py` to fetch GSM8K subset (≥1,000 problems) from HuggingFace `datasets` with checksum verification
- [X] T007b [P] Implement streaming logic in `src/data/loader.py` using `load_dataset(..., streaming=True)` and `itertools.islice` for deterministic sampling if full dataset exceeds RAM. **Constraint**: Must raise exception if real fetch fails; NO synthetic fallback.
- [X] T008 Create `src/data/checksums.py` for data integrity verification
- [ ] T009 Implement `src/models/config.py` to programmatically prune `TinyLlama` to a reduced parameter scale. **Logic**: Create a function `generate_pruned_config(base_model_name)` that returns a valid `transformers.PretrainedConfig` object. **Requirement**: Detect source model layer count. Select the layer count that results in a parameter count **closest** to 300M (no strict 5% tolerance band). **Include verification logic** to validate the pruned model architecture (layer count, hidden size, attention heads) matches TinyLlama-300M specifications before training begins.
- [X] T010 Implement `src/models/backbone.py` with hooks to capture attention projection updates
- [X] T012 Create `src/cli/run_experiment.py` as the single entry point orchestrating all training and analysis. **Requirement**: Must define `--early-window-fraction`, `--early-alignment-threshold`, and `--num-seeds` CLI arguments.
- [X] T013 [P] Create `tests/unit/test_svd.py` to verify SVD on small matrices fits memory constraints
- [X] T014 [P] Create `tests/unit/test_projection.py` to verify projection math (cosine similarity ≥ 0.99)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Establish Geometric Baseline via On-Policy Distillation (Priority: P1) 🎯 MVP

**Goal**: Run OPD baseline on GSM8K subset to generate a "stable subspace" defined by top singular vectors of early parameter updates.

**Independent Test**: Run OPD loop for fixed steps, extract accumulated update matrices, perform SVD, and verify existence of defined subspace (top-k vectors) without running RL.

### Tests for User Story 1

- [X] T015 [P] [US1] Contract test for OPD SVD output shape in `tests/unit/test_opd_svd.py`
- [X] T016 [P] [US1] Integration test for OPD data flow in `tests/integration/test_opd_flow.py`

### Implementation for User Story 1

- [ ] T017 [US1] Implement `src/training/opd_baseline.py` runner for GSM8K subset (capped steps). **Deliverable**: Script must accept `--seed` and `--steps` arguments. **Output**: Must save `results/opd/updates_seed_{i}.pt` (list of tensors) and `results/opd/logs_seed_{i}.json`. **Verification**: Script must exit with code 0 only if output files exist and contain valid tensors.
- [ ] T018 [US1] Implement logic in `src/training/opd_baseline.py` to record $\Delta W$ matrices for the initial phase of training (after every optimizer step). **Verification**: Add a post-run check to verify `results/opd/updates_seed_{i}.pt` exists and contains a list of tensors with shapes matching the model's layer dimensions.
- [ ] T018b [US1] Implement per-step update direction logging in `src/training/opd_baseline.py`. **Storage**: Save per-layer update vectors to separate files `results/opd/updates_seed_{i}/layer_{l}.pt` (NOT a single stacked array) to ensure memory compliance.
- [ ] T018c-impl [US1] Implement logic in `src/analysis/metrics.py` to define the 'early' window dynamically. **Logic**: Calculate `early_window_steps = max(50, int(total_steps * early_window_fraction))`. **Configuration**: Read `early_window_fraction` from CLI (default 0.1). **Action**: Write the resolved window size and fraction to `results/early_window_config.json`.
- [ ] T018c-gen [US1] **Execute** T018c-impl logic to generate `results/early_window_config.json` with the calculated window size (default [deferred] of total, min 50) before any training starts. **Depends on**: T018c-impl implementation. **Note**: This task calculates the specific step count corresponding to the '[deferred]' fraction of the trajectory.
- [ ] T019 [US1] Implement **layer-wise SVD logic** in `src/training/projection_utils.py` for accumulated updates
- [ ] T020 [US1] Implement logic to select $k$ such that cumulative explained variance ≥ 80% (default $k=10$ if none)
- [ ] T021 [US1] Save stable subspace matrix (shape $k \times n_{params}$) to `results/opd_subspace.npy`
- [ ] T022a [US1] Log memory usage during SVD and **Assert memory usage < 7GB **; raise exception if limit exceeded.
- [ ] T022b [US1] **Log** peak memory usage to `results/memory_profile.json` for SC-004 verification, regardless of success or failure.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Low-Rank RL Hybrid with Geometric Projection (Priority: P2)

**Goal**: Train a PPO-based RL agent where gradients are projected onto the stable subspace from US1 before update.

**Independent Test**: Run PPO training with projection active, verify update direction cosine similarity with subspace basis ≥ 0.99.

### Tests for User Story 2

- [ ] T023 [P] [US2] Contract test for gradient projection in `tests/unit/test_gradient_projection.py`
- [ ] T024 [P] [US2] Integration test for Low-Rank RL loop in `tests/integration/test_low_rank_rl.py`

### Implementation for User Story 2

- [ ] T025 [US2] Implement `src/training/rl_baseline.py` with **lightweight PPO loop using torch.optim** (no external RL libs) and logging schema: steps, accuracy, loss. **Deliverable**: Script must save `results/rl_baseline/logs_seed_{i}.json`.
- [ ] T026 [US2] Implement `src/training/low_rank_rl.py` loading subspace from `results/opd_subspace.npy`. **Requirement**: This task MUST wait for T021 completion. **Verification**: Assert subspace file exists and loads correctly before starting training. **Depends on**: T021.
- [ ] T027 [US2] Implement **gradient projection logic** in `low_rank_rl.py` to constrain raw RL gradients to top-$k$ vectors
- [ ] T028 [US2] Add logging to verify update vector lies entirely within span of top-$k$ vectors
- [ ] T029 [US2] Log cosine similarity between applied update and subspace basis and **Assert cosine similarity >= 0.99 **; raise exception if violated.
- [ ] T030 [US2] Save Low-Rank RL training logs and checkpoints to `results/low_rank_rl/`
- [ ] T030b [US2] Implement per-step update direction logging in `src/training/low_rank_rl.py`. **Storage**: Save per-layer update vectors to separate files `results/low_rank_rl/updates_seed_{i}/layer_{l}.pt` (NOT a single stacked array).
- [ ] T030c-impl [US2] Implement real-time "Early Trajectory Alignment" logging logic in `src/training/low_rank_rl.py`. **Logic**: During the first `early_window` steps (from T018c-gen config), calculate cosine similarity between current update and OPD trajectory. **Configuration**: Read alignment threshold from CLI `--early-alignment-threshold` (default 0.95). **Action**: Log to `results/low_rank_rl/early_alignment_log.json` and **Flag run as 'Low Alignment'** if alignment < threshold (do NOT abort). **Dependency**: Requires `results/early_window_config.json` from T018c-gen.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compare Convergence and Subspace Alignment (Priority: P3)

**Goal**: Compare sample efficiency and subspace alignment of Low-Rank RL vs Standard RL vs OPD.

**Independent Test**: Aggregate accuracy-vs-steps curves, run statistical test (Wilcoxon) on steps-to-threshold metric.

### Tests for User Story 3

- [ ] T031 [P] [US3] Contract test for statistical significance in `tests/unit/test_stats.py`
- [ ] T032 [P] [US3] Integration test for full pipeline comparison in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement `src/training/random_projection.py` (Random Baseline). **Note**: Mandatory control per Plan's Complexity Tracking.
- [ ] T034 [P] [US3] Implement `src/training/random_walk_prior.py` with random walk subspace projection logic. **Note**: Mandatory control per Plan's Complexity Tracking.
- [ ] T035 [P] [US3] Implement `src/training/opd_initialized_rl.py` with OPD weight initialization and no projection. **Note**: Mandatory control per Plan's Complexity Tracking.
- [ ] T036-impl [US3] Implement `src/analysis/metrics.py` to calculate steps-to-threshold-accuracy for **ALL variants**. **Output**: Write a CSV file `results/metrics/steps_to_threshold.csv` with columns `variant`, `seed`, `steps`. **Format**: Use `dtype=object` for the `steps` column to support mixed integers and string sentinels. **Threshold**: Explicitly use 0.80 (80%) as the accuracy threshold.
- [ ] T036b [US3] Implement non-convergence logic in `src/analysis/metrics.py`. **Logic**: If a variant never reaches the 80% threshold, record the string "Did Not Converge" in the CSV. **Requirement**: Ensure T036-impl calls this logic.
- [ ] T037 [US3] Implement `src/analysis/metrics.py` to compute cosine similarity between final update directions and PPO proxy
- [ ] T038a [US3] Implement `src/analysis/power_analysis.py` to perform pre-experiment/post-hoc power analysis and sample size estimation. **Constraint**: Must NOT allow N < 3.
- [ ] T038b-d [US3] **Execute** Wilcoxon signed-rank test on N=3 seeds per variant (FR-006), calculate **p-values and effect sizes**, and write results to `results/statistical_test_results.json`. **Depends on**: T036-exec (Metrics Calculation), T040 (Early Alignment), T038a implementation. **Note**: Handles "Did Not Converge" strings by filtering or imputing as max_steps + 1.
- [ ] T038c [US3] Generate statistical report artifact in `results/statistical_report.md` containing p-values and effect sizes. **Depends on**: T038b-d (which outputs p-values and effect sizes), T036-exec.
- [ ] T039 [US3] Implement `src/analysis/plots.py` to generate convergence curves and alignment plots
- [ ] T041-impl [US3] Implement `src/analysis/plots.py` to generate final comparison table and statistical report artifact `results/analysis_report.md` covering **ALL variants**. **Requirement**: Verify that the table includes rows for all 6 variants. If the pipeline aborted early, mark status as 'Inconclusive due to time' and list all variants as 'Not Run'.
- [ ] T041-exec [US3] **Execute** T041-impl logic to generate `results/analysis_report.md`. **Depends on**: T041-impl, T036-exec, T038c.

### Execution Tasks (N=3 Seeds per Variant, Strict Abort Policy)

- [ ] T052a [US3] [P] **Pre-flight Estimation**: Run a quick estimation script to calculate `Estimated_N3_Time` for the 6 variants and write to `results/time_estimates.json`. **Depends on**: T009 (Model Config), T007 (Data).
- [ ] T052b [US3] [P] **Write Estimates**: Write `results/time_estimates.json` with the calculated time. **Depends on**: T052a.
- [ ] T053 [US3] **Hard Abort Check**: Implement logic in `src/cli/run_experiment.py` to check `Estimated_N3_Time` from T052b. **Logic**: If `Estimated_N3_Time > 6 hours`, abort the entire pipeline immediately with a clear error message "Experiment aborted: N=3 runs exceed 6-hour budget. All variants required." **Constraint**: NO variant reduction. **Dependency**: Must run before T042-a.
- [ ] T042-a [US3] [P] **Implement Orchestration**: Implement orchestration logic in `src/cli/run_experiment.py` to manage N=3 seeds for all 6 variants. **Depends on**: T053.
- [ ] T042-b [US3] **Execute Initial Runs**: Execute training runs for all 6 variants with **N=3 seeds** via CLI. **Triggered by**: T042-a logic. **Constraint**: Must abort if T053 triggers. **Depends on**: T042-a, T053.
- [ ] T043 [US3] Execute training runs for OPD Baseline (N=3 seeds) via CLI (Managed by T042-b)
- [ ] T043b [US3] Execute training runs for Low-Rank RL (N=3 seeds) via CLI (Managed by T042-b). **Includes**: Execution of T030c-impl logic during training (Early Trajectory Alignment).
- [ ] T044 [US3] Execute training runs for Standard RL (N=3 seeds) via CLI (Managed by T042-b)
- [ ] T045 [US3] Execute training runs for Random Projection Baseline (N=3 seeds) via CLI (Managed by T042-b)
- [ ] T046 [US3] Execute training runs for Random Walk Prior Baseline (N=3 seeds) via CLI (Managed by T042-b)
- [ ] T047 [US3] Execute training runs for OPD-Initialized RL (N=3 seeds) via CLI (Managed by T042-b). **Dependency**: Explicitly managed by T042-b.
- [ ] T036-exec [US3] Execute metrics calculation (T036-impl logic) on generated logs from T043-T047. **Depends on**: T042-b completion, T036b.
- [ ] T040 [US3] Compute Early Trajectory Alignment (first `early_window` steps, min) between Low-Rank RL and OPD using logged $\Delta W_t$ vectors (Depends on T018c-gen config, T030c-impl logs, and T043/T043b execution logs). **Output**: Write alignment scores to `results/early_alignment_scores.json`. **Depends on**: Completion of T043b (which includes T030c-impl execution).
- [ ] T048a [US3] Implement power analysis calculation in `src/analysis/power_analysis.py` to check effect size and sample size.
- [ ] T048b [US3] Implement conditional branching logic in `src/analysis/power_analysis.py` to check: (1) time remaining, (2) effect size < 0.5. **Note**: Since N=10 is removed, this logic only flags 'Inconclusive' if effect size is low but N=3 is the max possible.
- [ ] T048c [US3] **Report** conditional branching: if effect size < 0.5 AND N=3 is max possible, flag 'Inconclusive due to low power' in the final report. **Depends on**: T048b, T040, T038b-d, T052. **Output**: Flag for report. **Note**: No re-run logic; this is a reporting task only.
- [ ] T055 [US3] Verify all `results/` artifacts have SHA-256 hashes recorded in `state/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

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
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 completion (T021 output)**.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 outputs

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
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (SVD output, memory usage)
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
- **CRITICAL**: All training must run on CPU-only (2 vCPU, 7GB RAM) within 6 hours. No GPU, no low-precision quantization.
- **CRITICAL**: Use real GSM data from HuggingFace; no synthetic data or fabrication.
- **NOTE**: T053 enforces a hard abort if N=3 runs exceed 6 hours. NO variant reduction is permitted.
- **NOTE**: T018c-gen calculates the 'early' window dynamically ([deferred] of total steps, min 50).
- **NOTE**: T030c-impl uses a CLI-configurable alignment threshold (default 0.95), not hardcoded.
- **NOTE**: T036b handles non-convergence with a string sentinel "Did Not Converge".
- **NOTE**: T040 depends on the completion of T043b (which includes T030c-impl execution).
- **NOTE**: T048c flags 'Inconclusive due to low power' if N=3 is max possible and effect size is low.
- **NOTE**: T061 and T062 ensure that data loaders and memory assertions strictly raise exceptions on failure, preventing any silent degradation.
- **NOTE**: T063 and T064 verify streaming integrity and reproducibility, ensuring the experiment is robust against OOM and stochastic variance.
- **NOTE**: T052a/b and T053 ensure the time budget is respected before any training starts.
- **NOTE**: T042-b orchestrates N=3 runs for ALL 6 variants. If T053 triggers, no runs occur.
- **NOTE**: T041-impl reports 'Inconclusive due to time' if T053 aborts, rather than listing skipped variants.