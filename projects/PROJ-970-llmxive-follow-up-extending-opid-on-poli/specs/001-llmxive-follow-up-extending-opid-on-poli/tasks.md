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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with `networkx`, `numpy`, `pandas`, `scipy`, `pytest` dependencies
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup base configuration management (`code/config.py`) for seeds, tier definitions, and hyperparameters
- [X] T005 [P] Implement utility metrics module (`code/utils/metrics.py`) for basic success rate and raw entropy calculators only (complex stats like residual variance deferred to Phase 5)
- [X] T006 [P] Setup experiment runner skeleton (`code/experiments/runner.py`) with sequential episode processing logic
- [X] T007 Create base `StateGraph` entity definition (`code/env/state_graph.py`)
- [ ] T008 Configure random seed initialization to ensure reproducibility across runs
- [ ] T009 Setup data directory structure (`data/raw/synthetic_graphs/`, `data/processed/`) and logging infrastructure

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Environment Construction & Tier Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a suite of synthetic State-Graph Environments with three distinct complexity tiers (Tier: Deterministic, Tier 2: Stochastic, Tier 3: High-Entropy)

**Independent Test**: The system can be tested by instantiating the environment generator, verifying that Tier graphs have a single deterministic path with a small number of nodes., Tier graphs have branching paths with a moderate number of nodes., and Tier-level graphs have sparse rewards with a large number of nodes., all generated without external dependencies.

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement `GraphGenerator` class in `code/env/graph_generator.py` with tier-specific logic
- [ ] T011 [US1] Implement Tier 1 logic: Generate a single unique path, a small number of nodes, zero stochastic branching
- [ ] T012 [US1] Implement Tier 2 logic: Generate multiple branching paths, a moderate number of nodes, stochastic transition probabilities
- [ ] T013 [US1] Implement Tier 3 logic: Generate a sufficient number of nodes, sparse reward signals, high-entropy state transitions
- [ ] T014 [US1] Implement graph validation step to ensure valid path exists (regenerate if unreachable goal)
- [ ] T015 [US1] Implement seed-based deterministic regeneration logic: Generate graphs on-the-fly using the seed and code version hash; validate checksums against expected values to ensure reproducibility without static caching of artifacts

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - OPID Integration with Tunable Routing Threshold (Priority: P2)

**Goal**: Integrate the OPID algorithm with a tunable "critical-first" routing threshold parameter (to 1) to control hindsight skill injection density

**Independent Test**: The system can be tested by running the agent with the threshold set to 0 (always inject) and 1 (never inject) and verifying that the log-probability shifts and action selections differ significantly.

### Implementation for User Story 2

- [X] T016 [P] [US2] Implement lightweight baseline policy (rule-based or distilled) in `code/agent/policy.py`
- [X] T017 [US2] Implement `OPIDRouter` class in `code/agent/opid_router.py` with configurable `routing_threshold` parameter
- [ ] T018 [US2] Implement critical-first routing logic: Bernoulli trial with p = 1 - threshold for skill injection
- [ ] T019 [US2] Implement logic to inject hindsight skill distillation signals based on routing outcome
- [~] T020 [US2] Implement suppression of skill signals when threshold prevents injection
- [~] T021 [US2] Add logging for log-probability shifts and action selections relative to threshold settings
- [X] T021b [US2] Implement aggregation logic in `code/utils/metrics.py` to calculate the **mean log-probability shift** per (Tier, Threshold) setting from the logs generated in T021, required for the distillation cost-benefit ratio

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Performance & Rigidity Measurement Across Thresholds (Priority: P3)

**Goal**: Execute a sufficient number of simulated episodes per threshold setting for each complexity tier and record "policy rigidity" and "success rate"

**Independent Test**: The system can be tested by running a single batch of episodes for Tier 1 at a specific threshold and verifying that a success rate and action entropy variance are recorded and stored.

### Implementation for User Story 3

- [X] T022 [P] [US3] Implement `ExperimentRunner` in `code/experiments/runner.py` to orchestrate the full sweep
- [~] T023 [US3] Implement sweep logic: Iterate thresholds from **0.0 to 1.0** in **steps of 0.1** to satisfy FR-006 sensitivity analysis
- [~] T024 [US3] Implement episode loop: Execute **exactly 1,000 simulated episodes** per (Tier, Threshold) combination to satisfy FR-003 statistical power requirements
- [ ] T025 [US3] Implement sequential processing logic to ensure memory footprint < 7GB (discard intermediate data)
- [ ] T026 [US3] Implement "success rate" calculation: % of episodes traversing ground-truth path
- [ ] T028 [US3] Implement regression logic (Quadratic) in `code/experiments/analyzer.py` to isolate threshold effect, **and implement ANOVA** to measure statistical significance (p < 0.05) of the interaction term as required by SC-001 and SC-004
- [ ] T029 [US3] Implement inflection point detection logic: Derive the inflection point **mathematically from the quadratic regression coefficients** (vertex formula: -b/2a) rather than using a heuristic detector, as per FR-006 and SC-001
- [ ] T027 [US3] Implement "policy rigidity" calculation: Calculate the **residual variance of action entropy** after regressing out the deterministic effect of the routing threshold (requires output from T028)
- [ ] T030 [US3] Implement "distillation cost-benefit ratio" calculation: Compute ratio of **mean log-probability shift (calculated in T021b)** to success rate improvement (from T026)
- [ ] T031 [US3] Implement data logging: Write `episode_results.csv` and `summary_stats.csv` (including success rate, policy rigidity, inflection point, and distillation cost-benefit ratio) to `data/processed/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `docs/` and `README.md`
- [ ] T033 Code cleanup and refactoring
- [ ] T034 Performance optimization for the k episode sweep
- [ ] T035 [P] Additional unit tests in `code/tests/`
- [ ] T036 Run `quickstart.md` validation
- [ ] T037 Verify all edge cases: Deterministic policy observed (variance=0), zero injection baseline, unreachable goal handling

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
Task: "Implement Tier 1 logic in code/env/graph_generator.py"
Task: "Implement Tier 2 logic in code/env/graph_generator.py"
Task: "Implement Tier 3 logic in code/env/graph_generator.py"
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
- **Critical Constraint**: Data must be processed sequentially to stay under 7GB RAM.
- **Critical Constraint**: A sufficient number of episodes per setting is mandatory for statistical power. (FR-003).