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

- [ ] T001 Create directory structure: `mkdir -p src/ src/environment/ src/agent/ src/simulation/ src/analysis/ tests/ data/raw/synthetic_graphs/ data/processed/`
- [X] T002 Create `requirements.txt` with pinned versions: `networkx==3.2.1`, `numpy==1.26.4`, `pandas==2.2.1`, `scipy==1.13.0`, `pytest==8.1.1`
- [X] T003 [P] Create `ruff.toml` and `pyproject.toml` for linting (ruff) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `src/config.py` with global constants: `SEED=42`, `TIER_NODE_RANGES` (dict), `THRESHOLD_STEPS=11`. **MUST** also implement seed initialization: Call `np.random.seed(SEED)` and `random.seed(SEED)` at module load to ensure reproducibility (FR-007, Const I). **Do NOT hardcode EPISODES_PER_SETTING here.**
- [ ] T004b [P] Implement `verify_feasibility` function in `src/config.py`: Calculate estimated runtime using deterministic constants: `100 nodes` (Tier 3 max), `200 steps/episode`, and `N=1000` episodes. Formula: `estimated_time = (100 * 200 * 1000 * 11_thresholds * 3_tiers) * constant_overhead`. **MUST raise RuntimeError** if estimated time > 6 hours. **MUST NOT** return a reduced episode count. This enforces FR-003 (N=1000) and SC-005 (Feasibility) by failing if constraints are violated.
- [ ] T005 [P] Create `src/utils/metrics.py` with functions: `calculate_success_rate(trajectory, ground_truth)`, `calculate_action_entropy(actions)`, `calculate_checksum(file_path)`
- [ ] T006 [P] Create `src/simulation/runner.py` skeleton with `run_episode` stub and `process_sequential` loop structure
- [ ] T007 Create `src/environment/state_graph.py` defining `StateGraph` class with attributes: `nodes`, `edges`, `start`, `goal`, `tier`, `is_valid()`
- [ ] T008 [P] Create `src/seed.py` module: Implement `set_seed(seed)` function that initializes `numpy.random`, `random`, and `os.environ` for reproducibility. Call this at the very start of `main.py` or `runner.py`. (FR-007, Const I).
- [ ] T009 [P] Implement `log_data_hygiene` function in `src/utils/metrics.py` to record file checksums (Const III)
- [ ] T014 [US1] Implement `validate_graph` function in `src/environment/validator.py`: Use `networkx.has_path` to verify a path exists from `start` to `goal`. **Depends on**: T007 (StateGraph definition). **Return**: Boolean. Raise `RuntimeError` if path is missing. (FR-001, Edge Cases).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Environment Construction & Tier Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a suite of synthetic State-Graph Environments with multiple distinct complexity tiers, ranging from deterministic to stochastic and high-entropy regimes.

**Independent Test**: The system can be tested by instantiating the environment generator, verifying that Tier graphs have a single deterministic path with a small number of nodes., Tier graphs have branching paths with a moderate number of nodes., and Complex graphs have sparse rewards with numerous nodes., all generated without external dependencies.
*Test Implementation*: Verify via `tests/unit/test_graph_generator.py::test_tier_1_nodes`, `tests/unit/test_graph_generator.py::test_tier_2_branching`, and `tests/unit/test_graph_generator.py::test_tier_3_sparsity`.

### Implementation for User Story 1

- [ ] T011a [P] [US1] Implement `generate_tier_1_nodes` in `src/environment/graph_generator.py`: Create a linear chain of **5 to 10 nodes** (randomly selected within range) with no branching.
- [ ] T011b [P] [US1] Implement `generate_tier_1_edges` in `src/environment/graph_generator.py`: Create deterministic edges connecting the chain. **MUST** set transition probability = 1.0.
- [ ] T011c [US1] Implement `generate_tier_1` wrapper in `src/environment/graph_generator.py`: Combine T011a and T011b. **MUST** call T014 (Validator) in a loop (max_retries=100) until a valid graph is produced. Raise `RuntimeError` if validation fails 100 times. **Depends on**: T011a, T011b. (FR-001).
- [ ] T012a [P] [US1] Implement `generate_tier_2_nodes` in `src/environment/graph_generator.py`: Create **20 to 50 nodes** (randomly selected within range) with branching structure.
- [ ] T012b [P] [US1] Implement `generate_tier_2_edges` in `src/environment/graph_generator.py`: Create edges with **stochastic transition probabilities** (p=0.8). **MUST** ensure at least 2 branching paths exist.
- [ ] T012c [US1] Implement `generate_tier_2` wrapper in `src/environment/graph_generator.py`: Combine T012a and T012b. **MUST** call T014 (Validator) in a loop (max_retries=100) until a valid graph is produced. Raise `RuntimeError` if validation fails 100 times. **Depends on**: T012a, T012b. (FR-001).
- [ ] T013a [P] [US1] Implement `generate_tier_3_nodes` in `src/environment/graph_generator.py`: Create **100+ nodes** (fixed 100 for determinism in testing, scalable in logic) with sparse structure.
- [ ] T013b [P] [US1] Implement `generate_tier_3_edges` in `src/environment/graph_generator.py`: Create edges with **high-entropy transitions** and **sparse rewards** (1 reward per ~10 nodes).
- [ ] T013c [US1] Implement `generate_tier_3` wrapper in `src/environment/graph_generator.py`: Combine T013a and T013b. **MUST** call T014 (Validator) in a loop (max_retries=100) until a valid graph is produced. Raise `RuntimeError` if validation fails 100 times. **Depends on**: T013a, T013b. (FR-001).
- [ ] T015 [US1] Implement `verify_deterministic_regeneration` test: Create `tests/unit/test_graph_generator.py::test_deterministic_regeneration` which runs the generator for each tier with a fixed seed, computes checksums, regenerates, recomputes checksums, and asserts equality to satisfy FR-001 and Const I.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - OPID Integration with Tunable Routing Threshold (Priority: P2)

**Goal**: Integrate the OPID algorithm with a tunable "critical-first" routing threshold parameter (0 to 1) to control hindsight skill injection density

**Independent Test**: The system can be tested by running the agent with the threshold set to 0 (always inject) and 1 (never inject) and verifying that the log-probability shifts and action selections differ significantly.

### Implementation for User Story 2

- [X] T016 [P] [US2] Implement `PolicyHead` class in `src/agent/policy.py`: A lightweight baseline policy using **CPU-only numpy operations** (no PyTorch/TensorFlow). Implementation MUST be a **Stochastic Softmax Policy** with a temperature parameter `tau > 0` to ensure non-zero baseline entropy variance.
- [ ] T017 [P] [US2] Implement `OPIDRouter` class in `src/agent/opid_router.py` with `__init__(self, routing_threshold)` and `should_inject(state)` methods. **Depends on**: T016 (Policy interface).
- [ ] T018 [P] [US2] Implement critical-first routing logic in `OPIDRouter.should_inject`: Perform a Bernoulli trial with p = 1 - threshold. Return True if successful.
- [ ] T019 [P] [US2] Implement `inject_skill_signal` method in `src/agent/opid_router.py` to simulate a log-probability shift (e.g., add a constant advantage to the goal-directed action).
- [ ] T020 [P] [US2] Implement logic to suppress skill signals when `should_inject` returns False, ensuring the policy acts as the baseline.
- [ ] T021 [US2] Implement logging in `src/simulation/runner.py` to record `log_prob_shift` and `action_selected` for every step where injection occurs or is suppressed. **MUST** store these shifts in a temporary buffer: `list[dict]` where each dict has keys `state` (int), `action` (int), `log_prob_shift` (float), `injected` (bool). **Depends on**: T017 (Router logic).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Performance & Rigidity Measurement Across Thresholds (Priority: P3)

**Goal**: Execute a sufficient number of simulated episodes per threshold setting for each complexity tier to ensure statistical reliability. and record "policy rigidity" and "success rate"

**Independent Test**: The system can be tested by running a batch of episodes for Tier 1 at a specific threshold and verifying that a success rate and action entropy variance are recorded and stored.

### Implementation for User Story 3

- [ ] T022 [P] [US3] Implement `ExperimentRunner` class in `src/simulation/runner.py` to orchestrate the full sweep.
- [ ] T023 [US3] Implement sweep logic in `ExperimentRunner.run_sweep`: Iterate thresholds across the full range using `np.arange(0.0, 1.01, 0.1)` to explicitly satisfy FR-006 (intervals of 0.1). **MUST** enforce the loop over thresholds before the episode loop.
- [ ] T024 [US3] Implement episode loop in `ExperimentRunner.run_sweep`: Execute a loop `for _ in range(N)` for each (Tier, Threshold) combination. **MUST** use `N=1000` (enforced by T004b). **MUST** run the FULL set of episodes (no splitting) to ensure statistical power and Single Source of Truth. **Depends on**: T004b (Feasibility Check).
- [ ] T024b [US3] [P] Implement `enforce_episode_minimum` logic in `src/simulation/runner.py`: Verify that N=1000 is feasible before starting. **MUST** raise `RuntimeError` if feasibility check fails, preventing any reduction in episodes. **Depends on**: T004b.
- [ ] T025 [US3] Implement sequential processing logic **in `src/simulation/runner.py`**: Ensure episodes are processed one-by-one and intermediate trajectory data is discarded immediately to keep memory < 7GB.
- [ ] T026 [US3] Implement "success rate" calculation: % of episodes where the agent traverses the ground-truth path (using `calculate_success_rate` from T005).
- [ ] T031 [US3] Implement data logging: Write `episode_results.csv` and `summary_stats.csv` (including success rate, policy rigidity, inflection point, and distillation cost-benefit ratio) to `data/processed/`. **MUST** include all columns: `tier`, `threshold`, `success`, `entropy`, `log_prob_shift`.
- [ ] T030a [US3] Implement `aggregate_log_prob_shift` in `src/analysis/aggregation.py`: Read the temporary buffer from T021 (or the raw CSV if buffered there) and calculate `mean_log_prob_shift` per (tier, threshold). Write this to `data/processed/log_prob_shifts.csv` or append to `episode_results.csv`. **MUST** ensure this happens before T030. **Depends on**: T031.
- [ ] T027b [US3] Implement `run_success_rate_regression` in `src/analysis/stats.py`: Perform a **quadratic regression** of **success rate vs threshold** (NOT entropy). **MUST** use `numpy.polyfit` with degree=2. Output coefficients (a, b, c) to `data/processed/regression_results.json` with keys `a`, `b`, `c` (floats, 6 decimal precision), `p_value` (float), and `is_inverted_u` (boolean). **MUST assert** that `p_value < 0.05 AND a < 0`. If not, raise `AssertionError: "Hypothesis failed: No inverted U-curve detected"`. **Depends on**: T031.
- [ ] T027c [US3] Implement `run_entropy_regression` in `src/analysis/stats.py`: Perform a **linear regression** of **action entropy vs threshold**. Output coefficients to `data/processed/entropy_regression.json`. **MUST** run before T027d. **Depends on**: T031.
- [ ] T027d [US3] Implement `calculate_residuals` in `src/analysis/stats.py`: Load `entropy_regression.json` (from T027c) and `episode_results.csv`. Calculate **residuals = observed_entropy - predicted_entropy** (using linear coefficients). Output residuals to `data/processed/residuals.csv`. **Depends on**: T027c.
- [ ] T027e [US3] Implement "policy rigidity" calculation: Calculate **var(residuals)** from `data/processed/residuals.csv`. Output to `data/processed/rigidity_metrics.json`. **Depends on**: T027d.
- [ ] T027 [US3] Implement `calculate_policy_rigidity` in `src/analysis/aggregation.py`: Combine results from T027b (for inflection context) and T027e (residuals). **MUST** explicitly depend on T027b and T027c. **Depends on**: T027b, T027c.
- [ ] T028 [US3] [P] Implement `run_interaction_anova` in `src/analysis/stats.py`: Perform a **Two-Way ANOVA** (or equivalent interaction test) to measure the interaction between routing threshold and environment complexity (Tier) to satisfy SC-004. Output interaction p-value to `data/processed/interaction_results.json`. **Depends on**: T031.
- [ ] T029 [US3] Implement inflection point detection: Derive the inflection point **mathematically from the quadratic regression coefficients** (vertex formula: -b/a) from `data/processed/regression_results.json` (T027b) and record it. **Depends on**: T027b.
- [ ] T042 [US3] [P] Implement `calculate_baseline_success_rate` in `src/analysis/aggregation.py`: Filter the full `episode_results.csv` for `threshold == 1.0`, calculate the success rate, and write the float value to `data/processed/baseline_success_rate.json`. **MUST** ensure this file is written for T030 to read. **Depends on**: T031.
- [ ] T030 [US3] Implement "distillation cost-benefit ratio" calculation: **MUST** load the FULL `episode_results.csv` (no held-out split). Compute the ratio: `mean_log_prob_shift / (success_rate_full - baseline_success_rate)`. **MUST** read `baseline_success_rate` from `data/processed/baseline_success_rate.json` (output of T042). **MUST** detect the inflection point: Identify the first threshold T where `success_rate[T] < success_rate[T-0.1]` OR the cost-benefit ratio becomes negative. If both occur, report the earlier threshold. Output to `data/processed/cost_benefit_ratio.json`. **Note**: The spec mentions "held-out validation set", but the Plan and Constitution require Single Source of Truth (full dataset). This task uses the full dataset as mandated by the Plan. A comment is added to the code to flag the spec inconsistency for future amendment. **Depends on**: T031, T042, T030a.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates: Update `README.md` with CLI usage instructions and `docs/research/analysis-method.md` with detailed statistical definitions for rigidity and cost-benefit ratio.
- [ ] T033 Code cleanup and refactoring: Refactor `src/analysis/aggregation.py` to use pandas groupby for memory efficiency and remove duplicate calculation functions.
- [ ] T035 [P] Add unit tests: Add `tests/unit/test_opid_router.py` for Bernoulli injection logic and `tests/unit/test_policy.py` for entropy variance calculation.
- [ ] T036 Run `quickstart.md` validation
- [ ] T037 Verify all edge cases: Create `tests/unit/test_edge_cases.py` with tests for: deterministic policy (variance=0), zero injection baseline, and unreachable goal handling.
- [ ] T038 [P] Add contract tests for graph generation tiers to verify node counts and path properties against spec requirements
- [ ] T039 [P] Add contract tests for statistical output schemas to ensure ANOVA and regression results match SC-001/SC-004 formats
- [ ] T040 [P] Verify memory footprint: Run the full sweep and assert that peak memory usage remains < 7GB (replacing T034 numba vectorization which contradicts sequential streaming constraints).
- [ ] T041 [P] [US1] Add explicit `max_retries` exception handling in `generate_tier_*` methods to raise a `RuntimeError` if a valid graph cannot be generated within 100 attempts, ensuring the "fail loud" principle is met for unreachable goal edge cases.
- [ ] T043 [P] [US3] Implement a "streaming aggregation" task in `src/simulation/runner.py` that updates running statistics (mean, variance) incrementally per episode without storing full trajectory lists, further enforcing the <7GB memory constraint for large N.

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
- **Critical Constraint**: The experiment must run the FULL set of episodes (minimum 1000 per setting) for the primary metric to satisfy FR-003. No data splitting for the primary metric.
- **Critical Constraint**: SC-002 requires the cost-benefit ratio to be derived from the FULL dataset (Single Source of Truth).
- **Critical Constraint**: SC-001 requires the quadratic regression to be performed on SUCCESS RATE vs threshold.
- **Critical Constraint**: FR-004 requires policy rigidity to be calculated via LINEAR regression of entropy vs threshold.
- **Critical Constraint**: T027b (Success Rate Regression) and T027c (Entropy Regression) must run before T027d (Residuals).
- **Critical Constraint**: T023 must explicitly use `np.arange(0.0, 1.01, 0.1)` to satisfy FR-006.
- **Critical Constraint**: T004b must implement a strict feasibility check that raises RuntimeError if time > 6h.
- **Critical Constraint**: T027c must perform LINEAR regression, not quadratic, to isolate the threshold effect correctly.
- **Critical Constraint**: T030 must use the full dataset, not a held-out set.
- **Critical Constraint**: T041 ensures the "fail loud" principle is met for graph generation.
- **Critical Constraint**: T042 ensures the baseline for cost-benefit calculation is robust.
- **Critical Constraint**: T043 reinforces the memory constraint by mandating incremental statistics updates.
- **Critical Constraint**: T027b must assert the inverted U-curve condition (p < 0.05 AND a < 0).
- **Critical Constraint**: T027c, T027d, T027e split the rigidity calculation for granularity.
- **Critical Constraint**: T042 depends on T031 to ensure data exists.
- **Critical Constraint**: T024 depends on T004b to ensure feasibility before running.
- **Critical Constraint**: T014 is not [P] because it depends on T007.
- **Critical Constraint**: T027 depends on both T027b and T027c.
- **Critical Constraint**: T030 must read baseline from T042's JSON output.
- **Critical Constraint**: T030a must aggregate log_prob_shift before T030.
- **Critical Constraint**: T011c, T012c, T013c must depend on their respective sub-tasks.
- **Critical Constraint**: T024b must raise an error if N=1000 is not feasible.
- **Critical Constraint**: T004b must define worst-case parameters (100 nodes, 200 steps).
- **Critical Constraint**: T027b must define output schema (a, b, c, p_value, is_inverted_u).
- **Critical Constraint**: T021 must define buffer schema (state, action, log_prob_shift, injected).