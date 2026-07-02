# Tasks: Social Memory Networks: Modeling Collective Remembering in Multi‑Agent LLMs

**Input**: Design documents from `/specs/001-social-memory-networks/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US-1, US-2, US-3)
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

- [X] T001 [P] Create `code/` directory structure with subpackages (agent, memory, metrics, analysis, data, utils, tests)
- [X] T002 [P] {{claim:c_a4b64142}}
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement dataset loaders with synthetic fallback only (no Hanabi/CoQA URLs as verified sources unavailable) in `code/data/loaders.py` and `code/data/synthetic.py` (FR-011)
- [X] T005 [P] Implement base Agent abstraction using CPU-only `transformers` (opt-125m, float32 precision) in `code/agent/base_agent.py` (FR-002)
- [X] T006 [P] Implement shared external memory buffer with `<MEMORY_ACTION>` token handling in `code/memory/buffer.py` (FR-003) <!-- FAILED: unspecified -->
- [X] T007 [P] Configure error logging with timestamps to `experiment.log` in `code/utils/logging.py` (FR-010)
- [X] T008 [P] Configure environment management (config.yaml with seed=42, device=cpu) in `code/utils/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Transactive‑Memory Measurement (Priority: P1) 🎯 MVP

**Goal**: Obtain baseline measurements of specialization and cue‑retrieval efficiency when agents have full context

**Independent Test**: Run the experiment with the *Full‑context* condition only and verify that the script outputs both metrics and a reproducible CSV summary.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests are written first (TDD) but depend on implementation for execution

- [X] T009 [P] [US-1] Contract test for game result schema in `code/tests/contract/test_game_result.py`
- [X] T010 [P] [US-1] Integration test for full-context simulation in `code/tests/integration/test_full_context.py`

### Implementation for User Story 1

- [X] T011 [P] [US-1] Implement CLI flag parsing for --context, --agents, --dataset and game simulation loop for 1000 games in `code/run_experiment.py` (FR-001) <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [X] T012 [P] [US-1] Implement specialization index computation (0 to log₂(N_agents)) in `code/metrics/specialization.py` (FR-004)
- [X] T013 [P] [US-1] Implement cue-retrieval efficiency metric (proportion vs. 1/N_agents baseline) in `code/metrics/retrieval.py` (FR-005)
- [X] T014 [P] [US-1] Implement validation logic for metrics (≥95% games produce metrics, SC-001) in `code/metrics/validator.py`
- [X] T015 [US-1] Output `results_full.csv` with `game_id`, `specialization_index`, `retrieval_efficiency`, `context_condition`, `agent_count` to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/` for 1000 games

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Context‑Window Truncation Impact (Priority: P2)

**Goal**: Compare baseline metrics against a limited‑context condition to test robustness under context limits

**Independent Test**: Run the experiment with the *Limited‑context* condition and verify that the statistical comparison reports a significant interaction (p < 0.05) or a documented null result.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US-2] Contract test for ANOVA output schema in `code/tests/contract/test_anova.py`
- [X] T017 [P] [US-2] Integration test for limited-context simulation in `code/tests/integration/test_limited_context.py`

### Implementation for User Story 2

- [ ] T018 [US-2] Implement game simulation loop for limited context (1000 games per spec) in `code/run_experiment.py` <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T019 [US-2] Output `results_limited.csv` with same metrics to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/`
- [X] T020 [P] [US-2] Implement two‑way independent‑samples ANOVA with factors Context × Metric (single ANOVA, not separate) in `code/analysis/anova.py` (FR-006)
- [X] T021 [P] [US-2] Apply Bonferroni correction to all family‑wise hypothesis tests and report corrected α in `code/analysis/anova.py` (FR-007)
- [X] T022 [US-2] Conduct sensitivity analysis sweeping context‑truncation token limit over {128, 256, 512} with performance curves output in `code/analysis/sensitivity.py` (FR-008)
- [X] T023 [US-2] Generate power‑analysis report estimating detectable effect size (N=1000 games per spec FR-009) in `code/analysis/power.py`
- [X] T024 [US-2] Flag "Power limitation" if estimated power < 0.70 in `projects/PROJ-586-social-memory-networks-modeling-collecti/results/power_analysis_report.md` (SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Scaling Analysis Across Agent Populations (Priority: P3)

**Goal**: Investigate how the fidelity of collective remembering scales when the number of agents varies across different group sizes.

**Independent Test**: Run the experiment for each specified agent count and produce a plot of specialization index and retrieval efficiency versus number of agents, along with a fitted power‑law exponent.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US-3] Contract test for scaling plot schema in `code/tests/contract/test_scaling.py`
- [X] T026 [P] [US-3] Integration test for agent count variation in `code/tests/integration/test_scaling.py`

### Implementation for User Story 3

- [ ] T027 [US-3] Implement game simulation for agent counts 3, 5, 7 (800 games per config per spec US-3) in `code/run_experiment.py` <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [X] T028 [P] [US-3] Implement power-law fitting for metric trends vs. agent count (3, 5, 7) in `code/analysis/scaling.py` (US-3)
- [X] T029 [P] [US-3] Calculate 95% confidence interval for exponent β and note sub‑linearity (β < 1) in `code/analysis/scaling.py`
- [X] T030 [US-3] Generate `scaling_plot.pdf` with fitted power‑law curves and explicit note that 3 data points limit power‑law reliability in `projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address remaining requirements

- [X] T031 [P] Run `quickstart.md` validation (execute all commands, verify exit code 0 for each) in `projects/PROJ-586-social-memory-networks-modeling-collecti/code/` <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T032 [P] Remove all 8-bit/4-bit quantization imports, verify no CUDA imports in all Python files (compute feasibility)
- [X] T033 [P] Implement file-locking with fcntl and add conflict retry logic in `code/utils/serialization.py` (FR-012)
- [X] T034 [P] Update `research.md` with reviewer feedback integration notes (Turing, Rockmore, Kahneman, Krakauer, Kandel, West)
- [X] T035 [P] Run full pipeline on CI runner, record runtime/memory/disk in `projects/PROJ-586-social-memory-networks-modeling-collecti/results/` to verify ≤6h, ≤7GB RAM, ≤14GB disk constraints <!-- ATOMIZE: requested -->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US-1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US-1/US-2 but should be independently testable

### Within Each Phase

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Phase complete before moving to next priority

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
# Launch all models for User Story 1 together:
Task: "Implement CLI flag parsing and game simulation in code/run_experiment.py"
Task: "Implement specialization index computation in code/metrics/specialization.py"
Task: "Implement cue-retrieval efficiency metric in code/metrics/retrieval.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch all models for User Story 2 together:
Task: "Implement ANOVA analysis in code/analysis/anova.py"
Task: "Implement sensitivity analysis in code/analysis/sensitivity.py"
Task: "Implement power analysis in code/analysis/power.py"
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
- [Story] label maps task to specific user story for traceability (US-1, US-2, US-3)
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Compute Constraint**: All tasks MUST run on CPU-only CI (2 CPU, ~7GB RAM, NO GPU). Use small models (e.g., opt-125m) in float32.
- **Game Counts**: US-1/US-2 = 1000 games per condition (spec requirement); US-3 = 800 games per configuration
- **Dataset Constraint**: Hanabi/CoQA have NO verified URLs; use synthetic fallback only (code/data/synthetic.py)
- **ANOVA Design**: Single two-way ANOVA with Context × Metric interaction (FR-006), NOT separate ANOVAs
- **Power Analysis**: N=1000 games (FR-009 spec requirement)
- **Reviewer Feedback**: Phases 6-11 from prior draft removed (not in original spec); addressed in T034
