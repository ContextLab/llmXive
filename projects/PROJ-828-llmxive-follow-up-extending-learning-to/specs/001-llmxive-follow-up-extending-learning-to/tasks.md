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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (src/, tests/, data/, results/)
- [ ] T002 Initialize Python 3.10 project with `torch`, `transformers`, `datasets`, `peft`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `src/utils/seeds.py` for deterministic seed pinning across all variants
- [ ] T005 Implement `src/utils/memory_monitor.py` to track RAM usage and enforce a memory limit
- [ ] T006 Implement `src/utils/hasher.py` to compute SHA-256 hashes of all derived artifacts
- [ ] T007 Create `src/data/loader.py` to fetch GSM8K subset (≥1,000 problems) from HuggingFace `datasets` with checksum verification
- [ ] T008 Create `src/data/checksums.py` for data integrity verification
- [ ] T009 Implement `src/models/config.py` to programmatically prune `TinyLlama` to a reduced parameter scale. **Logic**: Detect source model layer count. If a reduced number of layers, remove the final subset (indices 6-10). If 24 layers, remove last 18. Verify `hidden_size=512` and final param count ~300M.
- [ ] T009b Implement verification logic in `src/models/config.py` to validate the pruned model architecture (layer count, attention heads, hidden size) matches TinyLlama-300M specifications before training begins.
- [ ] T010 Implement `src/models/backbone.py` with hooks to capture attention projection updates
- [ ] T011 [P] Create stub file `src/training/projection_utils.py` containing signatures for `layer_wise_svd` and `project_gradient` functions
- [ ] T012 Create `src/cli/run_experiment.py` as the single entry point orchestrating all training and analysis
- [ ] T013 [P] Create `tests/unit/test_svd.py` to verify SVD on small matrices fits memory constraints
- [ ] T014 [P] Create `tests/unit/test_projection.py` to verify projection math (cosine similarity ≥ 0.99)
- [ ] T018c [P] Implement logic in `src/analysis/metrics.py` to define the 'early' window (first [deferred] of training steps, minimum 50 steps) and write it to `results/early_window_config.json`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Establish Geometric Baseline via On-Policy Distillation (Priority: P1) 🎯 MVP

**Goal**: Run OPD baseline on GSM8K subset to generate a "stable subspace" defined by top singular vectors of early parameter updates.

**Independent Test**: Run OPD loop for fixed steps, extract accumulated update matrices, perform SVD, and verify existence of defined subspace (top-k vectors) without running RL.

### Tests for User Story 1

- [ ] T015 [P] [US1] Contract test for OPD SVD output shape in `tests/unit/test_opd_svd.py`
- [ ] T016 [P] [US1] Integration test for OPD data flow in `tests/integration/test_opd_flow.py`

### Implementation for User Story 1

- [ ] T017 [US1] Implement `src/training/opd_baseline.py` runner for GSM8K subset (capped steps)
- [ ] T018 [US1] Implement logic in `src/training/opd_baseline.py` to record $\Delta W$ matrices for the initial phase of training (after every optimizer step). Save list of tensors to `results/opd/updates_seed_{i}.pt`
- [ ] T018b [US1] Implement per-step update direction logging in `src/training/opd_baseline.py`. **Storage**: Save per-layer update vectors to separate files `results/opd/updates_seed_{i}/layer_{l}.pt` (NOT a single stacked array) to ensure memory compliance.
- [ ] T019 [US1] Implement **layer-wise SVD logic** in `src/training/projection_utils.py` for accumulated updates
- [ ] T020 [US1] Implement logic to select $k$ such that cumulative explained variance ≥ 80% (default $k=10$ if none)
- [ ] T021 [US1] Save stable subspace matrix (shape $k \times n_{params}$) to `results/opd_subspace.npy`
- [ ] T022 [US1] Log memory usage during SVD to ensure < 7GB limit

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
- [ ] T029 [US2] Log cosine similarity between applied update and subspace basis (must be ≥ 0.99)
- [ ] T030 [US2] Save Low-Rank RL training logs and checkpoints to `results/low_rank_rl/`
- [ ] T030b [US2] Implement per-step update direction logging in `src/training/low_rank_rl.py`. **Storage**: Save per-layer update vectors to separate files `results/low_rank_rl/updates_seed_{i}/layer_{l}.pt` (NOT a single stacked array).

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
- [ ] T036 [US3] Implement `src/analysis/metrics.py` to calculate steps-to-threshold-accuracy for all 4 variants (OPD, Low-Rank, Standard, Random Projection)
- [ ] T037 [US3] Implement `src/analysis/metrics.py` to compute cosine similarity between final update directions and PPO proxy
- [ ] T038a [US3] Implement `src/analysis/power_analysis.py` to perform pre-experiment/post-hoc power analysis and sample size estimation
- [ ] T038b-a [US3] Implement Wilcoxon signed-rank test logic in `src/analysis/metrics.py` (N=3 minimum) with dynamic power calculation and conditional re-run flagging.
- [ ] T039 [US3] Implement `src/analysis/plots.py` to generate convergence curves and alignment plots
- [ ] T041 [US3] Generate final comparison table and statistical report in `results/analysis_report.md`

### Execution Tasks (N=3 Seeds per Variant, Adaptive to N=10)

- [ ] T042-a [US3] **Orchestrate** initial training runs for 4 variants (OPD, Low-Rank RL, Standard RL, Random Projection) with **N=3 seeds**.
- [ ] T043 [US3] Execute training runs for OPD Baseline (N=3 seeds) via CLI (Managed by T042-a)
- [ ] T043b [US3] Execute training runs for Low-Rank RL (N=3 seeds) via CLI (Managed by T042-a)
- [ ] T044 [US3] Execute training runs for Standard RL (N=3 seeds) via CLI (Managed by T042-a)
- [ ] T045 [US3] Execute training runs for Random Projection Baseline (N=3 seeds) via CLI (Managed by T042-a)
- [ ] T036-exec [US3] Execute metrics calculation (T036 logic) on generated logs from T043-T045
- [ ] T038b-d [US3] Execute Wilcoxon signed-rank test on N=3 seeds per variant (FR-006) and generate p-values (Depends on T036-exec)
- [ ] T038c [US3] Generate statistical report artifact in `results/statistical_report.md` containing p-values and effect sizes
- [ ] T040 [US3] Compute Early Trajectory Alignment (first [deferred] of steps, min 50) between Low-Rank RL and OPD using logged $\Delta W_t$ vectors (Depends on T018c config and T043/T043b execution logs)
- [ ] T042-b [US3] **Orchestrate** conditional re-run for 4 variants with **N=10 seeds** if T048c triggers (Managed by T042-b)
- [ ] T048 [US3] Implement adaptive sample size logic in `src/analysis/power_analysis.py` to trigger re-runs if effect size < 0.5 (up to N=10) OR flag for human review if time limit is exceeded.
- [ ] T048b [US3] Implement conditional branching logic in `src/analysis/power_analysis.py` to check effect size and prepare for re-run (Depends on T038b-d)
- [ ] T048c [US3] Execute conditional branching logic: if effect size < 0.5 AND N < 10 AND time permits, re-invoke T042-b via CLI flag `--rerun-seeds` (Depends on T048b)
- [ ] T048d [US3] Re-run analysis (T036-exec, T038b-d, T038c) on new data if re-run occurred (Depends on T048c)
- [ ] T049 [US3] **Monitor** execution time and trigger Variant Reduction Strategy if 6-hour limit is at risk.
- [ ] T049a [US3] **Resolve** hardware constraint: Implement 'Variant Reduction Strategy' to ensure pipeline completes within 6 hours. If time exceeded, reduce variants (e.g., drop Random Walk Prior) or flag as 'inconclusive' and stop.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T051 Code cleanup and refactoring of training loops
- [ ] T052 Performance optimization for CPU execution (batching, mixed precision)
- [ ] T053 [P] Additional unit tests in `tests/unit/`
- [ ] T054 Run quickstart.md validation to ensure 6-hour limit compliance (with N=3 seed count and 4 variants)
- [ ] T055 Verify all `results/` artifacts have SHA-256 hashes recorded in `state/`

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
- **CRITICAL**: All training must run on CPU-only (2 vCPU, 7GB RAM) within 6 hours. No GPU, no 8-bit quantization.
- **CRITICAL**: Use real GSM8K data from HuggingFace; no synthetic data or fabrication.
- **NOTE**: Task T042-a orchestrates N=3 pilot runs for 4 variants. T042-b handles conditional re-runs to N=10 if power analysis requires and time permits.
- **NOTE**: T018b and T030b explicitly log per-step vectors **layer-wise** to separate files to satisfy FR-008 and memory constraints.
- **NOTE**: T049 and T049a explicitly resolve the hardware constraint conflict by implementing a 'Variant Reduction Strategy' to ensure completion within 6 hours, flagging 'inconclusive' if statistical power cannot be achieved within time limits.
- **NOTE**: T018c defines the 'early' window (first [deferred] of steps, min 50) and writes it to `results/early_window_config.json` for T040 to consume.
- **NOTE**: T009b verifies the pruned model architecture to ensure 'Verified Accuracy'.