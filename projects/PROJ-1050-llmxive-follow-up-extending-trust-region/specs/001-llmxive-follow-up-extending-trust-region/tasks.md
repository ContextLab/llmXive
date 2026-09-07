# Tasks: llmXive follow-up: extending "Trust Region Policy Distillation"

**Input**: Design documents from `/specs/001-llmxive-topd-extension/`
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

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-1050-llmxive-follow-up-extending-trust-region/`
- [ ] T002 Initialize Python project with `numpy`, `scipy`, `pandas`, `matplotlib`, `pytest`, `statsmodels` in `projects/PROJ-1050-llmxive-follow-up-extending-trust-region/code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `projects/PROJ-1050-llmxive-follow-up-extending-trust-region/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create base `__init__.py` files for `code/env`, `code/student`, `code/experiments`, `code/analysis`
- [ ] T004a [P] Create `code/utils/` directory and `__init__.py` file to support utility modules
- [X] T005 [P] Implement deterministic random seed management utility in `code/utils/seed_manager.py`
- [X] T006 [P] Create base logging configuration to write to `data/raw/` in `code/utils/logger.py`
- [ ] T007 Setup experiment configuration schema for $\alpha$ and horizon sweeps in `code/experiments/grid_config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Reasoning Environment & Teacher Policy (Priority: P1) 🎯 MVP

**Goal**: Implement a deterministic synthetic "Reasoning MDP" environment and a perfect Teacher Policy to generate ground-truth optimal paths.

**Independent Test**: The environment can be instantiated, and the teacher policy can be queried to produce a valid, optimal path of a specified depth without external dependencies.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Unit test for valid state transitions in `tests/unit/test_mdp.py`
- [X] T009 [P] [US1] Unit test for teacher policy generating optimal paths in `tests/unit/test_teacher_policy.py`
- [X] T010 [P] [US1] Unit test for invalid action penalty handling in `tests/unit/test_mdp.py` <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `ReasoningMDP` class with state graph, inference rules, and transitions in `code/env/reasoning_mdp.py` (FR-001)
- [X] T011a [P] [US1] Implement the ground-truth path generation algorithm (BFS/DFS solver) to generate valid paths of varying depths in `code/env/path_generator.py` (FR-001, FR-007)
- [X] T012 [P] [US1] Implement `TeacherPolicy` class that returns deterministic optimal paths using the path generator in `code/env/teacher_policy.py` (FR-001)
- [X] T013 [US1] Implement validation logic to ensure ground-truth path accessibility before training in `code/env/reasoning_mdp.py` (FR-007)
- [X] T014 [US1] Add error handling for unsolvable states and invalid inference rules in `code/env/reasoning_mdp.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Capacity-Constrained Student Policy & TOP-D Training Loop (Priority: P2)

**Goal**: Implement a student policy with configurable "cognitive horizon" and the TOP-D training loop with variable interpolation coefficient $\alpha$.

**Independent Test**: The training loop can run for a fixed number of epochs with a specific $\alpha$ and horizon, producing a trained student model and loss logs without GPU acceleration.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Unit test for horizon constraint enforcement in `tests/unit/test_student_policy.py`
- [X] T016 [P] [US2] Unit test for TOP-D loss calculation with $\alpha$ interpolation in `tests/unit/test_topd_loss.py`
- [X] T017 [P] [US2] Integration test for training loop convergence with distinct $\alpha$ values in `tests/integration/test_training_loop.py`

### Implementation for User Story 2

- [ ] T018a [P] [US2] Implement the cognitive horizon enforcement mechanism (step counter truncation/penalty injection) in `code/student/policy.py` (FR-002)
- [ ] T018 [P] [US2] Implement `StudentPolicy` class skeleton in `code/student/policy.py` (FR-002)
- [ ] T019 [P] [US2] Implement `TOPDLoss` class for probability-space interpolation with $\alpha$ in `code/student/topd_loss.py` (FR-003)
- [ ] T020 [US2] Implement training loop in `code/experiments/runner.py` that records effective depth, teacher depth, and calculates the collapse ratio (effective depth / teacher depth) for each episode (FR-004, SC-002)
- [ ] T021 [US2] Implement logic to handle $\alpha=0$ (pure student learning) in `code/student/policy.py`
- [ ] T022 [US2] Add logging for per-episode loss values and convergence stability (variance of the loss) for *every* training episode to `data/raw/episode_logs.csv` in `code/experiments/runner.py` (FR-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interaction Analysis & Collapse Detection (Priority: P3)

**Goal**: Implement automated analysis pipeline using Tobit regression to detect reasoning collapse and non-monotonic relationships.

**Independent Test**: The analysis script can ingest the training logs, run the Tobit regression, and output a report indicating whether a significant interaction effect exists.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for Tobit regression execution and p-value extraction in `tests/unit/test_tobit_model.py`
- [ ] T024 [P] [US3] Unit test for collapse detection logic (depth ≤ 0.5 × teacher depth) in `tests/unit/test_analysis.py`
- [ ] T025 [P] [US3] Integration test for full sensitivity analysis sweep in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `TobitModel` class for censored regression using `statsmodels.regression.tobit` in `code/analysis/tobit_model.py` (FR-005)
- [ ] T027 [US3] Implement collapse detection logic (effective depth ≤ 0.5 × teacher depth) in `code/analysis/tobit_model.py` (FR-006)
- [ ] T028 [US3] Implement and execute the sensitivity analysis runner to sweep $\alpha$ across the set {0.1, 0.3, 0.5, 0.7, 0.9} across all student horizon limits, generating the full experimental grid dataset and writing the results to `data/processed/collapse_sweep.csv` (FR-006, SC-004)
- [ ] T029 [US3] Implement non-monotonicity check to identify peak effective reasoning depth at intermediate $\alpha$ and write the result (peak alpha, hypothesis flag) to `docs/results/hypothesis_validation.json` (FR-006, SC-004)
- [ ] T030 [US3] Generate analysis report with likelihood ratio test statistics and p-values in `code/analysis/tobit_model.py` (FR-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/results/` for experimental setup and metrics definitions
- [ ] T032 Code cleanup and refactoring to ensure CPU-only compliance (no accidental GPU imports)
- [ ] T033a [P] Execute the full experimental grid (combining alpha sweep and horizon limits) and measure wall-clock runtime to generate timing data for verification
- [ ] T033 [US3] Run full integration test suite to verify experimental grid completion within 6 hours using timing data from T033a; MUST generate `data/processed/timing_report.json` recording the runtime and asserting the 6-hour constraint (SC-005)
- [ ] T034 Verify data hygiene: checksum training logs in `data/raw/` and ensure no synthetic fallbacks
- [ ] T035 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for environment/teacher data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for training logs

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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for valid state transitions in tests/unit/test_mdp.py"
Task: "Unit test for teacher policy generating optimal paths in tests/unit/test_teacher_policy.py"

# Launch all models for User Story 1 together:
Task: "Implement ReasoningMDP class in code/env/reasoning_mdp.py"
Task: "Implement ground-truth path generator in code/env/path_generator.py"
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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