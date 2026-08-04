# Tasks: llmXive follow-up: extending "Self-Distilled Agentic Reinforcement Learning"

**Input**: Design documents from `/specs/001-llmxive-student-only-gating/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project root directory structure `projects/PROJ-825-llmxive-follow-up-extending-self-distill/` and `code/` subdirectory, including `code/agents/`, `code/environments/`, `code/metrics/`, `code/utils/`, `code/tests/`, `code/models/`, `data/`, `data/processed/`, `state/`, and `code/config.py` per plan.md structure
- [X] T004 Initialize Python project with `requirements.txt` containing pinned versions: `transformers>=4.40.0 `, `datasets>=2.14.0 `, `sentence-transformers>=2.2.0 `, `torch>=2.0.0 `, `scikit-learn>=1.3.0 `, `{{claim:c_44be7bf6}} (pi, https://en.wikipedia.org/wiki/Pi)`, `alfworld>=0.3.0 `, `webshop>=0.1.0 `, `pandas>=2.0.0 `, `numpy>=1.24.0 `
- [ ] T005 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T006 [P] Configure configuration management in `code/config.py` (seeds, hyperparameters, variant flags)
- [X] T007 [P] Implement base logging infrastructure in `code/utils/logging.py` to support JSON/CSV output for `TrainingRun` and `GatingSignal` artifacts
- [ ] T008 [P] Setup environment wrappers for ALFWorld (`code/environments/alfworld_env.py`) and WebShop (`code/environments/webshop_env.py`) ensuring they are fetchable via `pip`
- [ ] T009 Create base agent class `code/agents/base_agent.py` defining the RL loop interface
- [ ] T010 Setup cost profiling utility in `code/metrics/cost_profiler.py` to track CPU time and RSS memory per step
- [ ] T011 [P] Verify Qwen2.5-1.7B availability AND measure peak RSS memory of combined Qwen2.5-1.7B (8-bit quantized) + sentence-transformers ({{claim:c_47307b3b}} (2607.07974, https://arxiv.org/abs/2607.07974) quantized) in a dry-run script; FAIL if combined RSS >7GB RAM (Constitution VI)
- [ ] T012 [P] [FR-002] [SC-001] Implement `code/agents/baseline_agent.py` (dual-model SDAR with Teacher + Student) per FR-002 requirements, ensuring it **explicitly logs teacher-student gap scores** to `data/processed/` with `paired_trajectory_id` for later replay analysis (FR-004, Constitution VII).
- [ ] T013 [P] Implement `code/agents/student_only_agent.py` skeleton inheriting from `base_agent.py` (logic to be completed in Phase 3)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Student-Only Gating Training Loop (Priority: P1) 🎯 MVP

**Goal**: Train the "Student-Only Gating" variant of SDAR on ALFWorld and WebShop using only student entropy and context stability, eliminating the teacher model.

**Independent Test**: Execute a training run with `--variant student-only` on ALFWorld; verify logs contain gating scores derived *only* from $H_t$ and $S_t$ with zero teacher calls.

### Tests for User Story 1 (TDD - Write Failing Tests First)

> **NOTE**: These are TDD tasks. Write them first; they must FAIL initially, then pass after implementation.
> **TDD Note**: T014/T015 are written first (expect failure) and then implemented.

- [ ] T014 [P] [US1] TDD: Unit test for `student_only_agent.py` gating logic in `code/tests/test_gating.py` (verify $g_t$ calculation without teacher)
- [ ] T015 [P] [US1] TDD: Integration test for Student-Only loop termination in `code/tests/test_training_loop.py` (verify stop when **average per-episode cumulative reward reaches 0.8 for 3 consecutive episodes** OR step cap, as per US-1 Acceptance Scenario 1)

The research question is: How to determine optimal termination conditions for the agent?
The method is: Implementing early stopping based on a predefined reward threshold or maximum step count.
References: (None provided in original passage))

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implement `code/utils/gating.py` with functions to calculate token entropy ($H_t$) and retrieved context stability ($S_t$) via cosine similarity
- [ ] T017 [US1] Implement `code/agents/student_only_agent.py` logic: apply $g_t = \sigma(\alpha H_t + \beta S_t)$ without teacher invocation
- [ ] T018 [US1] Implement robustness checks in `code/agents/student_only_agent.py` to handle $S_t \approx 0$ (noisy context) and prevent NaN in sigmoid
- [ ] T019 [US1] Integrate `cost_profiler.py` into the Student-Only training loop to log per-step metrics to `data/processed/student_only_logs.jsonl`
- [ ] T020 [US1] Update `code/main.py` to accept `--variant student-only` and route to the new agent, ensuring no teacher model is loaded

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compare Baseline vs. Student-Only Performance (Priority: P2)

**Goal**: Execute Baseline SDAR, GRPO, and Student-Only variants and compare their task success rates and convergence speeds.

**Independent Test**: Run three distinct training jobs (GRPO, Baseline, Student-Only) on WebShop with identical seeds; generate a comparison table of success rates and steps-to-threshold.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for artifact persistence in `code/tests/test_artifacts.py` (verify paired trajectory IDs match across variants)
- [ ] T022 [P] [US2] Integration test for comparison report generation in `code/tests/test_analysis.py`

### Implementation for User Story 2

- [ ] T040 [P] [US2] Implement `code/agents/grpo_agent.py` (GRPO baseline) per FR-002 requirements, ensuring it logs metrics to `data/processed/` with `paired_trajectory_id`
- [ ] T023 [US2] Implement artifact persistence logic in `code/utils/logging.py` to save Baseline teacher-student gap scores (from T012), GRPO metrics (from T040), and Student-Only heuristics to `data/processed/` with shared `paired_trajectory_id`
- [ ] T024 [US2] Implement `code/main.py` logic to execute multiple independent runs for GRPO, Baseline, and Student-Only on ALFWorld and WebShop, enforcing the Early Stopping Protocol (stop at reward or step cap)
- [ ] T025 [US2] Create `code/scripts/compare_variants.py` to aggregate logs and output a comparison table of final task success rates and steps-to-threshold (0.8 reward) for all three variants
- [ ] T026 [US2] [Depends on: T019, T012] Implement `code/agents/student_only_agent.py` paired replay logic: load Baseline trajectories (from T012) and replay them through the Student-Only agent to compute scores on identical states; **compute and report Pearson correlation coefficient** between Student-Only scores and Baseline Teacher-Student gaps (FR-007, Constitution VII)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Computational Efficiency and Statistical Significance (Priority: P3)

**Goal**: Measure per-step cost reduction and perform statistical hypothesis testing on performance results.

**Independent Test**: Profile CPU time/memory for Student-Only vs. Baseline; run Bootstrapping on 5 runs; output p-value and cost reduction %.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for `statistical_test.py` bootstrapping logic in `code/tests/test_statistics.py`
- [ ] T028 [P] [US3] Contract test for cost reduction metric calculation in `code/tests/test_metrics.py`
- [ ] T029 [P] [US3] Full integration test: Run full suite on sample data in `code/tests/test_full_suite.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `code/metrics/statistical_test.py` with **Bootstrapping only** for N=5 bounded data (per FR-005 and Plan "Complexity Tracking"); remove any conditional logic for Mann-Whitney U or normality tests as these are explicitly rejected for this data regime.
- [ ] T031 [US3] Implement `code/scripts/analyze_results.py` to calculate:
 - Cost reduction % (CPU time) comparing Student-Only vs. Baseline (target ≥60%)
 - **Import and execute the Bootstrapping logic from `code/metrics/statistical_test.py` (T030)** to determine the P-value (target p < 0.05)
 - Performance retention % using formula: `(Success_Student - Success_GRPO) / (Success_Baseline - Success_GRPO) * 100` (SC-001 metric)
 - **Explicitly verify the performance retention inequality**: `(Success_Student - Success_GRPO) ≥ 0.8 × (Success_Baseline - Success_GRPO)` and output a **PASS/FAIL boolean** result as required by SC-001
 - Convergence speed comparison (SC-004)
 - Fetch GRPO baseline data explicitly for the SC-001 calculation
- [ ] T032 [US3] Compute Pearson correlation coefficient between Student-Only scores and Baseline Teacher-Student gaps on paired trajectories (FR-007, Constitution VII) and report result in `data/processed/correlation_results.json`
- [ ] T033 [US3] Generate final report artifacts in `data/processed/` containing all metrics, effect sizes (Cohen's d), and power analysis caveats

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `docs/` including `quickstart.md` for running the three variants
- [ ] T035 Code cleanup and refactoring of `code/agents/` to ensure clear separation of concerns
- [ ] T036 Performance optimization: verify context window chunking limits are enforced to prevent OOM on CI
- [ ] T037 [P] Additional unit tests for edge cases (random noise context, high-confidence incorrect tokens) in `code/tests/`
- [ ] T038 Run `quickstart.md` validation to ensure all scripts execute end-to-end

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on `student_only_agent` implementation from US1 for comparison
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data generation from US1 and US2

### Within Each User Story

- Tests (TDD) MUST be written and FAIL before implementation
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
# Launch all TDD tests for User Story 1 together:
Task: "TDD: Unit test for `student_only_agent.py` gating logic in `code/tests/test_gating.py`"
Task: "TDD: Integration test for Student-Only loop termination in `code/tests/test_training_loop.py`"

# Launch all models for User Story 1 together:
Task: "Implement `code/utils/gating.py` with functions to calculate token entropy and stability"
Task: "Implement `code/agents/student_only_agent.py` inheriting from `base_agent.py`"
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
 - Developer A: User Story 1 (Student-Only Agent)
 - Developer B: User Story 2 (Baseline Agent & Comparison)
 - Developer C: User Story 3 (Statistical Analysis & Profiling)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: Ensure all data fetching tasks (T008, T011) use verified real sources (pip/conda/HuggingFace) and fail loudly if unavailable; no synthetic fallbacks.
- **Compute Feasibility**: All tasks assume CPU-first execution with quantized models; GPU escape hatch (Kaggle) is reserved for OOM failures only.
- **Statistical Rigor**: T030 implements Bootstrapping exclusively for N=5 data as mandated by the plan.
- **Memory Constraint**: T011 explicitly verifies the 7GB RAM limit.