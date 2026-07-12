# Tasks: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

**Input**: Design documents from `/specs/001-structural-mismatch-cost/`
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

## Phase 0: Pre-Flight (Constitution & Spec Alignment)

**Purpose**: Resolve critical contradictions and gaps before implementation begins.

- [ ] T000 Update `plan.md` to formally document the GAM/ANOVA amendment (Constitution Principle VII override) and resolve the SC-003 gap flag (GAP-001) status to "Resolved".

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create exact project directory structure: `src/generators/`, `src/engines/`, `src/orchestrator/`, `src/analysis/`, `src/models/`, `src/utils/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `data/raw/`, `data/processed/`, `results/plots/`
- [ ] T001b Create `__init__.py` files in all new directories (`src/generators/`, `src/engines/`, `tests/unit/`, etc.)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, statsmodels, matplotlib, pyyaml, datasets, networkx)
- [ ] T003 [P] Configure linting and formatting tools (ruff/black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup deterministic random seed configuration and global `config.yaml`
- [ ] T005 [P] Implement **simulated** CPU throttling using `resource` module limits and CPU-burner loops in `src/engines/throttler.py` (Per Plan: Simulation for reproducibility). Ensure throttling logic is ready before execution tasks (T016) start.
- [ ] T005b [P] Implement "Throttling Validity Check" in `src/engines/throttler.py` to detect if limits fail to apply and raise a specific error code to fail the run (Per Spec Edge Cases).
- [ ] T005c [P] Define strict interface contract for `runner.py` (input/output types, plan capture mechanism) in `src/orchestrator/contracts.py` to enable parallel US1/US2 development.
- [ ] T006 [P] Create base data models for `QueryInstance` and `ExecutionMetric` (including `timeout_flag` boolean) in `src/models/data_models.py`
- [ ] T007 Setup directory structure for `data/raw`, `data/processed`, and `results/` with checksumming utilities
- [ ] T008 Implement deterministic, exhaustive, rule-based reference engine (`src/generators/ground_truth_solver.py`) per FR-008
- [ ] T009 Configure error handling and logging infrastructure with specific timeout detection for predefined limits.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify Latency Penalties of High-Complexity Queries on CPU (Priority: P1) 🎯 MVP

**Goal**: Measure end-to-end latency differences between low and high complexity queries under CPU constraints to validate the non-linear scaling hypothesis.

**Independent Test**: Can be fully tested by executing a predefined set of synthetic queries against a simulated CPU-throttled environment and recording the mean latency difference between the two complexity groups.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for query complexity classification logic in `tests/unit/test_query_generator.py`
- [ ] T011 [P] [US1] Integration test for throttling mechanism validity in `tests/integration/test_throttler.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement synthetic query generator in `src/generators/synthetic_query.py` (handles depth 1-2 vs 3+ partitioning)
- [ ] T013 [P] [US1] Implement Text retrieval engine simulation in `src/engines/text_engine.py` (simulated latency)
- [ ] T014 [P] [US1] Implement Relational (SQLite) engine simulation in `src/engines/sql_engine.py`
- [ ] T015 [P] [US1] Implement Graph (NetworkX) engine simulation in `src/engines/graph_engine.py`
- [ ] T016 [US1] Implement main execution loop in `src/orchestrator/runner.py` (orchestrates engines, applies throttling, records latency) - **Depends on T005c contract**
- [ ] T017 [US1] Implement latency aggregation and CSV export in `src/orchestrator/metrics.py` (output `results/latency_data.csv`)
- [ ] T018 [US1] Implement Generalized Additive Model (GAM) analysis in `src/analysis/gam_model.py` to test interaction effects (FR-005). Output `results/gam_stats.json` containing `p_value` (float) and `confidence_interval_95` (list of two floats) fields; verify extraction of these fields to satisfy SC-001.
- [ ] T019 [US1] Implement sensitivity analysis script in `src/analysis/sensitivity.py` (sweep cutoffs 2, 3, 4) per FR-007
- [ ] T019b [US1] Generate SC-004 validation report in `src/analysis/sensitivity.py`. Output `results/sensitivity_report.json` and validate schema matches SC-004 requirements (cutoff, spike_point, slope_change) before writing.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Measure Translation Error Rates Under Resource Constraints (Priority: P2)

**Goal**: Track translation error rates (plan mismatches) under CPU throttling to verify if accuracy penalty correlates with complexity.

**Independent Test**: Can be fully tested by comparing the ground-truth execution plan (from rule-based solver) against the system's generated plan, counting mismatches. **Note**: Requires stable runner contract (T005c) and ground truth solver (T008).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for ground-truth plan comparison logic in `tests/unit/test_ground_truth_solver.py`

### Implementation for User Story 2

- [ ] T021 [US2] Extend `src/orchestrator/runner.py` to capture generated plans and pass them to the comparison logic. **Depends on T016 (stable runner)** and **T021b (comparison module)**.
- [ ] T021b [US2] Implement Plan Comparison Logic in `src/orchestrator/metrics.py` to compare generated vs. ground-truth plans (FR-004) using a distinct, testable diff algorithm. Output comparison results to `results/comparison_raw.json` (list of objects with query_id and mismatch boolean).
- [ ] T022 [US2] Implement translation error calculation logic (binary mismatch flag) and append column `translation_error` (boolean 0/1) to `results/latency_data.csv` (FR-004).
- [ ] T023 [US2] Implement error rate aggregation and JSON export in `src/orchestrator/metrics.py` (output `results/error_rates.json`)
- [ ] T024 [US2] Update `ExecutionMetric` model with `timeout_flag` boolean and ensure `runner.py` logs timeout events to `results/latency_data.csv` without raising exceptions (non-blocking) (Spec Edge Cases).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (US2 relies on T005c contract and T016 stability).

---

## Phase 5: User Story 3 - Visualize Non-Linear Scaling and Interaction Effects (Priority: P3)

**Goal**: Generate interaction plots showing latency vs. query complexity for each source type to visually demonstrate the "structural mismatch cost".

**Independent Test**: Can be fully tested by generating a plot file (e.g., PNG/PDF) where the X-axis is query complexity, Y-axis is latency, and lines are grouped by source type.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Contract test for plot file generation in `tests/contract/test_visualizer.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement visualization script in `src/analysis/visualizer.py` (matplotlib/seaborn). **Reads** `results/latency_data.csv` (T017) and `results/error_rates.json` (T023) to initialize data structures.
- [ ] T027 [US3] Generate interaction plot (Latency vs. Complexity, grouped by Source Type) reading `results/latency_data.csv` (generated by T017) in `results/plots/interaction_plot.png`
- [ ] T028 [US3] Generate sensitivity analysis plot (Spike point vs. Cutoff) reading `results/sensitivity_report.json` (generated by T019b) in `results/plots/sensitivity_plot.png`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `specs/001-structural-mismatch-cost/quickstart.md`
- [ ] T030a Refactor error handling logic into `src/utils/error_utils.py`
- [ ] T030b Refactor logging configuration into `src/utils/logging_utils.py`
- [ ] T031a Unit test `test_timeout_does_not_block_batch` in `tests/unit/test_runner.py`
- [ ] T031b Unit test `test_recursion_depth_limits` in `tests/unit/test_query_generator.py`
- [ ] T032 Run `pytest` full suite and verify all tests pass on CPU-only environment
- [ ] T033 Verify `results/` outputs match Success Criteria (SC-001, SC-002, SC-004). **Note**: SC-003 is excluded per GAP-001.
- [ ] T033a Create `specs/001-structural-mismatch-cost/SC-003-gap-resolution.md` to formally document the exclusion of SC-003 in the spec.
- [ ] T033b Generate `results/gap_resolution_log.json` documenting the SC-003 exclusion as an implementation artifact, including the rationale and reference to GAP-001.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Pre-Flight)**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Phase 0 completion
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on `ground_truth_solver` (T008), `runner` (T016, via T005c contract), and `Plan Comparison Logic` (T021b). **Note**: T021 extends T016; they require a stable interface contract defined in T005c.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on `latency_data.csv` (T017), `error_rates.json` (T023), and `sensitivity_report.json` (T019b)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
  - **WARNING**: T005 (Throttling) must complete before T016 (Runner) starts to prevent race conditions, even if in different phases.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for query complexity classification logic in tests/unit/test_query_generator.py"
Task: "Integration test for throttling mechanism validity in tests/integration/test_throttler.py"

# Launch all engine implementations for User Story 1 together:
Task: "Implement Text retrieval engine simulation in src/engines/text_engine.py"
Task: "Implement Relational (SQLite) engine simulation in src/engines/sql_engine.py"
Task: "Implement Graph (NetworkX) engine simulation in src/engines/graph_engine.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Pre-Flight
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

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
   - Developer B: User Story 2 (Note: T021/T021b extends T016 runner, requires stable contract defined in T005c)
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
- **Critical Constraint**: All tasks must run on free CPU-only CI (limited CPU, 7GB RAM). No GPU libraries, no 8-bit quantization, no large model training. Use synthetic data and simulated engines.