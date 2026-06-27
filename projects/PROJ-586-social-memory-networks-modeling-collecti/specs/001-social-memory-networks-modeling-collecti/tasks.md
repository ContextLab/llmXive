# Tasks: Social Memory Networks: Modeling Collective Remembering in Multi‑Agent LLMs

**Input**: Design documents from `/specs/001-social-memory-networks/`
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

- [ ] T001 Create project structure per implementation plan at `projects/PROJ-586-social-memory-networks-modeling-collecti/code/`
- [ ] T002 Initialize Python 3.11 project with `transformers`, `torch` (CPU-only), `scikit-learn`, `pandas`, `pytest`, `numpy`, `matplotlib` in `code/requirements.txt`
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T010 [P] Setup environment configuration management for random seed (42) and device (CPU) in `code/utils/config.py`
- [ ] T004 [P] Setup dataset loaders with verified URLs or FR-011 synthetic fallback for Hanabi/CoQA in `code/data/loaders.py` and `code/data/synthetic.py` (FR-011)
- [ ] T005 [P] Implement base Agent abstraction using CPU-only `transformers` (small model, float32) in `code/agent/base_agent.py` (FR-002)
- [ ] T006 [P] Implement shared external memory buffer with `<MEMORY_ACTION>` token handling in `code/memory/buffer.py` (FR-003)
- [ ] T009 [P] Configure error logging with timestamps in `code/utils/logging.py` (FR-010)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Transactive‑Memory Measurement (Priority: P1) 🎯 MVP

**Goal**: Obtain baseline measurements of specialization and cue‑retrieval efficiency when agents have full context

**Independent Test**: Run the experiment with the *Full‑context* condition only and verify that the script outputs both metrics and a reproducible CSV summary.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests are written first (TDD) but depend on implementation for execution

- [ ] T011 [US1] Contract test for game result schema in `code/tests/contract/test_game_result.py`
- [ ] T012 [US1] Integration test for full-context simulation in `code/tests/integration/test_full_context.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement specialization index computation (0 to log₂(N_agents)) in `code/metrics/specialization.py` (FR-004)
- [ ] T014 [US1] Implement cue-retrieval efficiency metric (proportion vs. 1/N_agents baseline) in `code/metrics/retrieval.py` (FR-005)
- [ ] T015 [US1] Implement validation logic for cue-retrieval efficiency (proportion of successful fact-retrieval queries relative to uniform chance baseline 1/N_agents) in `code/metrics/validator.py` (FR-005)
- [ ] T016a [US1] Implement CLI flag parsing for --context, --agents, --dataset in `code/run_experiment.py` (FR-001)
- [ ] T016 [US1] Implement game simulation loop for full context (500 games per Plan; Spec N=1000 noted) in `code/run_experiment.py`
- [ ] T017 [US1] Add validation to ensure ≥95% of games produce metrics (SC-001) in `code/metrics/validator.py`
- [ ] T018 [US1] Output `results_full.csv` with `game_id`, `specialization_index`, `retrieval_efficiency`, `context_condition`, `agent_count` to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Context‑Window Truncation Impact (Priority: P2)

**Goal**: Compare baseline metrics against a limited‑context condition to test robustness under context limits

**Independent Test**: Run the experiment with the *Limited‑context* condition and verify that the statistical comparison reports a significant interaction (p < 0.05) or a documented null result.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [US2] Contract test for ANOVA output schema in `code/tests/contract/test_anova.py`
- [ ] T020 [US2] Integration test for limited-context simulation in `code/tests/integration/test_limited_context.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement game simulation loop for limited context (500 games per Plan; Spec N=1000 noted) in `code/run_experiment.py`
- [ ] T022 [US2] Output `results_limited.csv` with same metrics to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/`
- [ ] T023 [US2] Implement two‑way independent‑samples ANOVA with factors Context × Metric in `code/analysis/anova.py` (FR-006)
- [ ] T024 [US2] Apply Bonferroni correction to all family‑wise hypothesis tests and report corrected α in `code/analysis/anova.py` (FR-007)
- [ ] T025 [US2] Conduct sensitivity analysis sweeping context‑truncation token limit over {128, 256, 512} in `code/analysis/sensitivity.py` (FR-008)
- [ ] T026 [US2] Generate power‑analysis report estimating detectable effect size (N=500 per Plan; Spec N=1000 flagged) in `code/analysis/power.py` (FR-009)
- [ ] T027 [US2] Flag "Power limitation" if estimated power < 0.70 in `projects/PROJ-586-social-memory-networks-modeling-collecti/results/power_analysis_report.md` (SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Scaling Analysis Across Agent Populations (Priority: P3)

**Goal**: Investigate how the fidelity of collective remembering scales when the number of agents varies (3, 5, 7)

**Independent Test**: Run the experiment for each specified agent count and produce a plot of specialization index and retrieval efficiency versus number of agents, along with a fitted power‑law exponent.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [US3] Contract test for scaling plot schema in `code/tests/contract/test_scaling.py`
- [ ] T029 [US3] Integration test for agent count variation in `code/tests/integration/test_scaling.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement power-law fitting for metric trends vs. agent count (3, 5, 7) in `code/analysis/scaling.py` (FR-004, US-3)
- [ ] T031 [US3] Calculate 95% confidence interval for exponent β and note sub‑linearity (β < 1) in `code/analysis/scaling.py` (SC-005)
- [ ] T032 [US3] Generate `scaling_plot.pdf` with fitted power‑law curves and explicit note that 3 data points limit power‑law reliability (West review) in `projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address remaining reviewer concerns

- [ ] T035 [P] Run quickstart.md validation to ensure reproducibility on CPU-only CI (Plan.md constraints)
- [ ] T036 [P] Code cleanup and refactoring to ensure no 8-bit/4-bit quantization or CUDA dependencies (Compute Feasibility)
- [ ] T038 [P] Security hardening for file-write conflicts in `code/utils/serialization.py` (FR-012)

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
- All tests for a user story can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement specialization index computation in code/metrics/specialization.py"
Task: "Implement cue-retrieval efficiency metric in code/metrics/retrieval.py"
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
- **Compute Constraint**: All tasks MUST run on CPU-only CI (2 CPU, ~7GB RAM, NO GPU). Use small models (e.g., distilbert, opt-125m) in float32.
- **Review Integration**: Tasks T032 explicitly addresses Prior Research-Stage Review (West review on scaling analysis).
- **Plan.md Kickback Required**: The following issues are in spec.md or plan.md, not tasks.md:
  - FR-009 N=1000 vs plan 500 games mismatch (Addressed in T026)
  - SC-003, SC-004, SC-005 placeholders (Addressed in T025/T026/T032)
  - Dataset Constraint Acknowledgement conflict with Constitution Principle II (Addressed in T004)
  - US-1 1000 games vs plan 500 games inconsistency (Addressed in T016/T021)