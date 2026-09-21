# Tasks: OPID Critical-First Routing Complexity Analysis

**Input**: Design documents from `/specs/001-opid-routing-complexity/`
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

- [ ] T001 Create directory structure: `src/`, `src/environment/`, `src/agent/`, `src/simulation/`, `src/analysis/`, `tests/`, `data/raw/synthetic_graphs/`, `data/processed/`
- [X] T002 Create `requirements.txt` with pinned versions: `networkx==3.2.1`, `numpy==1.26.4`, `pandas==2.2.1`, `scipy==1.13.0`, `pytest==8.1.1`
- [X] T003 [P] Create `ruff.toml` and `pyproject.toml` for linting (ruff) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `src/config.py` with global constants: `SEED=42`, `TIER_NODE_RANGES` (dict), `EPISODES_PER_SETTING=[deferred]` (minimum 1,000 based on G*Power analysis, to be determined in research phase), `THRESHOLD_STEPS=11`
- [ ] T005 [P] Create `src/utils/metrics.py` with functions: `calculate_success_rate(trajectory, ground_truth)`, `calculate_action_entropy(actions)`, `calculate_checksum(file_path)`
- [ ] T006 [P] Create `src/simulation/runner.py` skeleton with `run_episode` stub and `process_sequential` loop structure
- [ ] T007 Create `src/environment/state_graph.py` defining `StateGraph` class with attributes: `nodes`, `edges`, `start`, `goal`, `tier`, `is_valid()`
- [ ] T008 [P] Implement seed initialization in `src/config.py`: Set `np.random.seed(SEED)` and `random.seed(SEED)` at module load to ensure reproducibility (FR-007, Const I)
- [ ] T009 [P] Implement `log_data_hygiene` function in `src/utils/metrics.py` to record file checksums (Const III)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Environment Construction & Tier Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a suite of synthetic State-Graph Environments with multiple distinct complexity tiers, ranging from deterministic to stochastic and high-entropy regimes.

**Independent Test**: The system can be tested by instantiating the environment generator, verifying that Tier graphs have a single deterministic path with a small number of nodes., Tier graphs have branching paths with tens of nodes., and Complex graphs have sparse rewards with numerous nodes., all generated without external dependencies.
*Test Implementation*: Verify via `tests/unit/test_graph_generator.py::test_tier_1_nodes`, `tests/unit/test_graph_generator.py::test_tier_2_branching`, and `tests/unit/test_graph_generator.py::test_tier_3_sparsity`.

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement `GraphGenerator` class in `src/environment/graph_generator.py` with `__init__` and `generate(tier, seed)` methods
- [ ] T011 [P] [US1] Implement `generate_tier_1` method: Create a single unique path with a variable number of nodes (random length within a defined range) and zero stochastic branching. **MUST** include an internal loop: regenerate the graph if `graph.is_valid()` is false (unreachable goal) until a valid graph is produced. Do not cache invalid graphs.
- [ ] T012 [P] [US1] Implement `generate_tier_2` method: Create -50 nodes with multiple branching paths and stochastic transition probabilities (p=0.8). **MUST** include an internal loop: regenerate the graph if `graph.is_valid()` is false until a valid graph is produced. Do not cache invalid graphs.
- [ ] T013 [P] [US1] Implement `generate_tier_3` method: Create a scalable network of nodes with sparse reward signals (approximately one reward per ten nodes) and high-entropy transitions. **MUST** include an internal loop: regenerate the graph if `graph.is_valid()` is false until a valid graph is produced. Do not cache invalid graphs.
- [ ] T015 [US1] Implement `verify_deterministic_regeneration` task: Explicitly run the generator for each tier with a fixed seed, compute checksums, regenerate, recompute checksums, and assert equality to satisfy FR-001 and Const I. (Note: T014 removed as validation is now internal to T011-T013).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - OPID Integration with Tunable Routing Threshold (Priority: P2)

**Goal**: Integrate the OPID algorithm with a tunable "critical-first" routing threshold parameter (0 to 1) to control hindsight skill injection density

**Independent Test**: The system can be tested by running the agent with the threshold set to 0 (always inject) and 1 (never inject) and verifying that the log-probability shifts and action selections differ significantly.

### Implementation for User Story 2

- [X] T016 [P] [US2] Implement `PolicyHead` class in `src/agent/policy.py`: A lightweight baseline policy using **CPU-only numpy operations** (no PyTorch/TensorFlow). Implementation MUST support EITHER a **Stochastic Softmax Policy** with a temperature parameter `tau > 0` to ensure non-zero baseline entropy variance, OR a **small rule-based agent** as permitted by the spec's Assumptions.
- [ ] T017 [US2] Implement `OPIDRouter` class in `src/agent/opid_router.py` with `__init__(self, routing_threshold)` and `should_inject(state)` methods.
- [ ] T018 [US2] Implement critical-first routing logic in `OPIDRouter.should_inject`: Perform a Bernoulli trial with p = 1 - threshold. Return True if successful.
- [ ] T019 [US2] Implement `inject_skill_signal` method in `src/agent/opid_router.py` to simulate a log-probability shift (e.g., add a constant advantage to the goal-directed action).
- [ ] T020 [US2] Implement logic to suppress skill signals when `should_inject` returns False, ensuring the policy acts as the baseline.
- [ ] T021 [US2] [P] Implement logging in `src/simulation/runner.py` to record `log_prob_shift` and `action_selected` for every step where injection occurs or is suppressed. **MUST** store these shifts in a temporary buffer during the episode run.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Performance & Rigidity Measurement Across Thresholds (Priority: P3)

**Goal**: Execute a sufficient number of simulated episodes per threshold setting for each complexity tier to ensure statistical reliability. and record "policy rigidity" and "success rate"

**Independent Test**: The system can be tested by running a single batch of [deferred] episodes for Tier 1 at a specific threshold and verifying that a success rate and action entropy variance are recorded and stored.

### Implementation for User Story 3

- [ ] T022 [P] [US3] Implement `ExperimentRunner` class in `src/simulation/runner.py` to orchestrate the full sweep.
- [ ] T023 [US3] Implement sweep logic in `ExperimentRunner.run_sweep`: Iterate thresholds from **0.0 to 1.0** in **steps of 0.1** (A set of thresholds).
- [ ] T023b [US3] [P] Implement data splitting logic: Before the sweep, split the total available episodes (or simulation budget) into a **training set** (for the main sweep) and a **held-out validation set** (for SC-002 baseline comparison). Save the held-out set to `data/processed/validation_set.csv`.
- [ ] T024 [US3] Implement episode loop in `ExperimentRunner.run_sweep`: Execute **`EPISODES_PER_SETTING`** (from T004) simulated episodes for each (Tier, Threshold) combination.
- [ ] T025 [US3] Implement sequential processing logic **in `src/simulation/runner.py`**: Ensure episodes are processed one-by-one and intermediate trajectory data is discarded immediately to keep memory < 7GB.
- [ ] T026 [US3] Implement "success rate" calculation: % of episodes where the agent traverses the ground-truth path (using `calculate_success_rate` from T005).
- [ ] T028 [US3] [P] Implement `run_regression_and_anova` in `src/analysis/stats.py`: Use **`numpy.polyfit` with degree=2** for quadratic fit (success rate vs threshold) and `scipy.stats.f_oneway` for ANOVA. **MUST** extract the quadratic coefficient's p-value and assert p < 0.05 to satisfy SC-001. Output regression coefficients (a, b, c) and ANOVA p-values to `data/processed/regression_results.json`.
- [ ] T027b [US3] [P] Implement `run_entropy_regression` in `src/analysis/stats.py`: Perform a separate quadratic regression of **action entropy vs threshold** (distinct from T028). Output the coefficients to `data/processed/entropy_regression.json`.
- [ ] T027 [US3] Implement "policy rigidity" calculation: Load `entropy_regression.json` (T027b) and `episode_results.csv`. Calculate **residual variance of action entropy** (FR-004) by regressing out the deterministic effect of the threshold using coefficients from T027b.
- [ ] T029 [US3] Implement inflection point detection: Derive the inflection point **mathematically from the quadratic regression coefficients** (vertex formula: -b/2a) and record it.
- [ ] T030 [US3] [P] Implement "distillation cost-benefit ratio" calculation: Load `episode_results.csv` (T026) for training data log-prob shifts. Load the **held-out validation set** (from T023b) to calculate the baseline success rate. Compute the ratio of the mean log-prob shift to the success rate improvement relative to the baseline (threshold=0.0) to satisfy SC-002. Output to `data/processed/cost_benefit_ratio.json`.
- [ ] T031 [US3] Implement data logging: Write `episode_results.csv` and `summary_stats.csv` (including success rate, policy rigidity, inflection point, and distillation cost-benefit ratio) to `data/processed/`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `docs/` and `README.md`
- [ ] T033 Code cleanup and refactoring
- [ ] T034 Performance optimization for the A multi-threshold, multi-tiered episode sweep (Multiple thresholds × 3 tiers × a large number of episodes) using `numba` or `numpy` vectorization where applicable
- [ ] T035 [P] Additional unit tests in `tests/unit/`
- [ ] T036 Run `quickstart.md` validation
- [ ] T037 Verify all edge cases: Deterministic policy observed (variance=0), zero injection baseline, unreachable goal handling
- [ ] T038 [P] Add contract tests for graph generation tiers to verify node counts and path properties against spec requirements
- [ ] T039 [P] Add contract tests for statistical output schemas to ensure ANOVA and regression results match SC-001/SC-004 formats

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US1 (graph gen) and US2 (router)** to run episodes

### Within Each User Story

- Models/Entities before Services/Logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes:
 - US1 (Graph Gen) and US2 (Router) can run in parallel
 - US3 (Experiments) must wait for US1 and US2 to be functional
- All tests for a user story marked [P] can run in parallel (if tests were requested)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement Tier 1 logic in src/environment/graph_generator.py::generate_tier_1"
Task: "Implement Tier 2 logic in src/environment/graph_generator.py::generate_tier_2"
Task: "Implement Tier 3 logic in src/environment/graph_generator.py::generate_tier_3"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Graph Generation)
4. **STOP and VALIDATE**: Test Graph Generation independently
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
 - Developer A: User Story 1 (Graph Gen)
 - Developer B: User Story 2 (OPID Router)
 - Developer C: User Story 3 (Runner/Analysis) - *Note: Can start skeleton work, but full execution requires US1/US2*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All logic must run on CPU-only hardware; no GPU/CUDA required.
- **Critical Constraint**: Data must be processed sequentially to stay within available RAM limits.
- **Critical Constraint**: `EPISODES_PER_SETTING` is a deferred empirical value (minimum 1,000) to be determined in the research phase; tasks must use the config variable, not hardcoded numbers.
- **Critical Constraint**: The experiment must complete a substantial number of total episodes (multiple thresholds × multiple tiers × a sufficient number per tier) within the fixed CPU time limit.
- **Critical Constraint**: SC-002 requires the cost-benefit ratio to be derived from a held-out validation set; T023b and T030 must implement this explicitly.
- **Critical Constraint**: The policy head must be configurable (Stochastic OR Rule-based) to match the spec's assumptions.
- **Critical Constraint**: Validation of graph existence must happen *inside* the generator (T011-T013) before any caching occurs.
- **Critical Constraint**: SC-001 requires the quadratic term's p-value to be tested; T028 must explicitly perform this check.