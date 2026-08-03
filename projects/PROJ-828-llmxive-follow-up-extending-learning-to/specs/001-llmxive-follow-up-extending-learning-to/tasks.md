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

## Implementation Notes

**Historical Context (T004, T005)**: Previous runs flagged `src/utils/seeds.py` (T004) and `src/utils/memory_monitor.py` (T005) as missing/invalid. The current tasks (T004, T005) are explicitly defined to implement these artifacts with strict determinism and memory enforcement. Implementers must ensure these are fully functional before proceeding to Phase 5 orchestration.

**Time Budget & Reduction**: The time limit is strict. [UNRESOLVED-CLAIM: c_0fded012 — status=not_enough_info] T056 implements a "Variant Reduction Strategy" that triggers at [deferred] of the time budget. If a critical baseline (Standard RL) is dropped, the experiment flags 'Inconclusive'.

**Early Window Definition**: The "early trajectory" window is defined as `max(50, ceil(total_steps * 0.10))` (T018c). This value is calculated in T018c and used by T030c and T040.

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
- [X] T008 Create `src/data/checksums.py` for data integrity verification
- [X] T009 Implement `src/models/config.py` to programmatically prune `TinyLlama` to a reduced parameter scale. **Logic**: Detect source model layer count. Remove layers from the end until the total parameter count is within 5 (2303.06480, https://arxiv.org/abs/2303.06480)% of 300M. **Include verification logic** to validate the pruned model architecture (layer count, attention heads, hidden size) matches TinyLlama-300M specifications before training begins.
- [X] T010 Implement `src/models/backbone.py` with hooks to capture attention projection updates
- [X] T012 Create `src/cli/run_experiment.py` as the single entry point orchestrating all training and analysis. **Requirement**: Must define a `--rerun-seeds` CLI flag for adaptive sample size logic.
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

- [ ] T017 [US1] Implement `src/training/opd_baseline.py` runner for GSM8K subset (capped steps)
- [ ] T018 [US1] Implement logic in `src/training/opd_baseline.py` to record $\Delta W$ matrices for the initial phase of training (after every optimizer step). Save list of tensors to `results/opd/updates_seed_{i}.pt`
- [ ] T018b [US1] Implement per-step update direction logging in `src/training/opd_baseline.py`. **Storage**: Save per-layer update vectors to separate files `results/opd/updates_seed_{i}/layer_{l}.pt` (NOT a single stacked array) to ensure memory compliance.
- [ ] T018c [US1] Implement logic in `src/analysis/metrics.py` to define the 'early' window. **Logic**: Calculate as `max(50, ceil(total_steps * 0.10))`. **Note**: This formula is a provisional default pending researcher approval. Write the resolved window size to `results/early_window_config.json`.
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

- [ ] T025 [US2] Implement `src/training/rl_baseline.py` with **lightweight PPO loop using torch.optim** (no external RL libs) and logging schema: steps, accuracy, loss.
- [ ] T026 [US2] Implement `src/training/low_rank_rl.py` loading subspace from `results/opd_subspace.npy` (Depends on T021)
- [ ] T027 [US2] Implement **gradient projection logic** in `low_rank_rl.py` to constrain raw RL gradients to top-$k$ vectors
- [ ] T028 [US2] Add logging to verify update vector lies entirely within span of top-$k$ vectors
- [ ] T029 [US2] Log cosine similarity between applied update and subspace basis and **Assert cosine similarity >= 0.99 **; raise exception if violated.
- [ ] T030 [US2] Save Low-Rank RL training logs and checkpoints to `results/low_rank_rl/`
- [ ] T030b [US2] Implement per-step update direction logging in `src/training/low_rank_rl.py`. **Storage**: Save per-layer update vectors to separate files `results/low_rank_rl/updates_seed_{i}/layer_{l}.pt` (NOT a single stacked array).
- [ ] T030c [US2] Implement real-time "Early Trajectory Alignment" logging in `src/training/low_rank_rl.py`. **Logic**: During the first `early_window` steps (from T018c), calculate cosine similarity between current update and OPD trajectory. **Action**: Log to `results/low_rank_rl/early_alignment_log.json` and **Flag run as 'Low Alignment'** if alignment < 0.95 (do NOT abort).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compare Convergence and Subspace Alignment (Priority: P3)

**Goal**: Compare sample efficiency and subspace alignment of Low-Rank RL vs Standard RL vs OPD.

**Independent Test**: Aggregate accuracy-vs-steps curves, run statistical test (Wilcoxon) on steps-to-threshold metric.

### Tests for User Story 3

- [ ] T031 [P] [US3] Contract test for statistical significance in `tests/unit/test_stats.py`
- [ ] T032 [P] [US3] Integration test for full pipeline comparison in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement `src/training/random_projection.py` (Random Baseline)
- [ ] T034 [P] [US3] Implement `src/training/random_walk_prior.py` with random walk subspace projection logic
- [ ] T035 [P] [US3] Implement `src/training/opd_initialized_rl.py` with OPD weight initialization and no projection
- [ ] T036 [US3] Implement `src/analysis/metrics.py` to calculate steps-to-threshold-accuracy for **ACTIVE variants** (read list from `results/active_variants.json` generated by T056). **Requirement**: Explicitly iterate over the list of active variant keys to ensure all are included in the comparison table.
- [ ] T037 [US3] Implement `src/analysis/metrics.py` to compute cosine similarity between final update directions and PPO proxy
- [ ] T038a [US3] Implement `src/analysis/power_analysis.py` to perform pre-experiment/post-hoc power analysis and sample size estimation. **Constraint**: Must NOT allow N < 3.
- [ ] T038b-a [US3] Implement Wilcoxon signed-rank test logic in `src/analysis/metrics.py` (N=3 minimum) with dynamic power calculation and conditional re-run flagging.
- [ ] T039 [US3] Implement `src/analysis/plots.py` to generate convergence curves and alignment plots
- [ ] T041 [US3] Generate final comparison table and statistical report in `results/analysis_report.md` covering **ACTIVE variants**. **Requirement**: Verify that the table includes rows for Random Walk Prior and OPD-Initialized RL if they are in the active list. If a variant was skipped (due to T056), mark as 'Skipped' and update report status to 'Inconclusive' if critical baselines are missing.

### Execution Tasks (N=3 Seeds per Variant, Adaptive to N=10)

- [ ] T056 [US3] [P] Implement `src/utils/variant_reducer.py` to dynamically disable non-essential training variants (e.g., Random Walk Prior) based on elapsed time thresholds (85% of 6-hour budget). **Constraint**: Only allow reduction if N=3 for all *remaining* variants is still achievable; if a critical baseline (Standard RL) is dropped, flag 'inconclusive'. Output list of active variants to `results/active_variants.json`.
- [ ] T057 [US3] Update `src/cli/run_experiment.py` to integrate `variant_reducer` logic, ensuring it aborts pending runs and triggers the "inconclusive" flag if the time budget is exceeded before statistical significance is reached.
- [ ] T058 [US3] [P] Implement a "Time Budget Monitor" thread in `src/cli/run_experiment.py` (not `memory_monitor.py`) that logs a warning at [deferred] of the 6-hour limit and triggers the reduction strategy. **Constraint**: Must enforce minimum N=3; if N=3 cannot be completed, flag 'inconclusive' and stop.

- [ ] T042-a [US3] **Orchestrate** initial training runs for **ACTIVE variants** (filtered by T056) with **N=3 seeds**. **Depends on**: T056 (Variant Reducer) to determine which variants to run. **Manage** T043-T047.
- [ ] T043 [US3] Execute training runs for OPD Baseline (N=3 seeds) via CLI (Managed by T042-a)
- [ ] T043b [US3] Execute training runs for Low-Rank RL (N=3 seeds) via CLI (Managed by T042-a)
- [ ] T044 [US3] Execute training runs for Standard RL (N=3 seeds) via CLI (Managed by T042-a)
- [ ] T045 [US3] Execute training runs for Random Projection Baseline (N=3 seeds) via CLI (Managed by T042-a)
- [ ] T046 [US3] Execute training runs for Random Walk Prior Baseline (N=3 seeds) via CLI (Managed by T042-a)
- [ ] T047 [US3] Execute training runs for OPD-Initialized RL (N=3 seeds) via CLI (Managed by T042-a)
- [ ] T036-exec [US3] Execute metrics calculation (T036 logic) on generated logs from T043-T047
- [ ] T040 [US3] Compute Early Trajectory Alignment (first `early_window` steps, min) between Low-Rank RL and OPD using logged $\Delta W_t$ vectors (Depends on T018c config, T030c implementation, and T043/T043b execution logs). **Output**: Write alignment scores to `results/early_alignment_scores.json`.
- [ ] T038b-d [US3] Execute Wilcoxon signed-rank test on N=3 seeds per variant (FR-006) and generate p-values (Depends on T036-exec, T040)
- [ ] T038c [US3] Generate statistical report artifact in `results/statistical_report.md` containing p-values and effect sizes
- [ ] T048a [US3] Implement power analysis calculation in `src/analysis/power_analysis.py` to check effect size and sample size.
- [ ] T048b [US3] Implement conditional branching logic in `src/analysis/power_analysis.py` to check: (1) time remaining, (2) effect size < 0.5. If both conditions met AND N < 10, prepare for re-run.
- [ ] T048c [US3] Execute conditional branching: if effect size < 0.5 AND N < 10 AND time permits, trigger re-run logic. **Depends on**: T048b, T040, T038b-d.
- [ ] T042-b [US3] **Orchestrate** conditional re-run for **ACTIVE variants** with **N=10 seeds** if T048c triggers. **Triggered by**: T048c.
- [ ] T048d [US3] Re-run analysis (T036-exec, T038b-d, T038c) on new data if re-run occurred (Depends on T042-b completion).
- [ ] T055 [US3] Verify all `results/` artifacts have SHA-256 hashes recorded in `state/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050a [P] Update `quickstart.md` with CLI usage examples and variant reduction explanation.
- [ ] T050b [P] Add API docs for `src/training/projection_utils.py` and `src/utils/variant_reducer.py`.
- [ ] T050c [P] Update `README.md` with experiment status and data availability notes.
- [ ] T051a [P] Extract logging logic to `src/utils/logger.py`.
- [ ] T051b [P] Remove unused imports and refactor training loops for clarity.
- [ ] T052 Performance optimization for CPU execution (batching, mixed precision)
- [ ] T053 [P] Additional unit tests in `tests/unit/`
- [ ] T054 Run quickstart.md validation to ensure 6-hour limit compliance (with N=3 seed count and active variants)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`opd_subspace.npy`)
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
- **NOTE**: T042-a orchestrates N=3 pilot runs for ACTIVE variants (filtered by T056). T042-b handles conditional re-runs to N=10 if power analysis requires and time permits.
- **NOTE**: T018b and T030b explicitly log per-step vectors **layer-wise** to separate files to satisfy FR-008 and memory constraints.
- **NOTE**: T056 and T058 explicitly resolve the hardware constraint by implementing a 'Variant Reduction Strategy' to ensure completion within 6 hours, flagging 'inconclusive' if statistical power cannot be achieved within time limits.
- **NOTE**: T018c defines the 'early' window as `max(50, ceil(total_steps * 0.10))` (provisional default) and writes it to `results/early_window_config.json` for T030c and T040 to consume.
- **NOTE**: T030c logs 'Early Trajectory Alignment' during training and flags runs with alignment < 0.95 (does NOT abort) to preserve experimental protocol.
- **NOTE**: T040 (Compute Early Trajectory Alignment) is executed BEFORE T048c (Conditional Branching) to ensure the metric is available for the re-run decision.
- **NOTE**: T048 and T048b enforce a hard constraint: N must be at least 3. If time limits prevent achieving N=3, the experiment flags 'inconclusive' rather than weakening statistical validity.
- **NOTE**: T042-b is triggered by T048c and managed by the CLI orchestration logic, not by itself.