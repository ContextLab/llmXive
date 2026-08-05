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
- [X] T002 [P] Initialize Python virtual environment and install dependencies from `requirements.txt`.
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement dataset loaders in `code/data/loaders.py`: Verify URLs against a whitelist. If the dataset (Hanabi/CoQA) lacks a verified URL in the `verified_datasets` block, raise a clear error and trigger the synthetic fallback. (FR-001, FR-011)
- [X] T004b [P] Implement synthetic fallback generator in `code/data/synthetic.py`: Create a set of synthetic cue-response pairs (minimum 10) from available context spans if explicit cues are missing. (FR-011)
- [X] T005 [P] Implement base Agent abstraction using CPU-only `transformers` (model: `facebook/opt-*`, precision: standard floating-point) in `code/agent/base_agent.py`. Ensure no CUDA imports. (FR-002)
- [X] T006 [P] Implement shared external memory buffer in `code/memory/buffer.py`: Support `<MEMORY_ACTION>` tokens with JSON schema `{"type": "write"|"read", "key": str, "value": str}`. Implement queue-based write conflict resolution. (FR-003, FR-012)
- [X] T007 [P] Configure error logging with timestamps to `experiment.log` in `code/utils/logging.py`. Log format: `[TIMESTAMP] [LEVEL] [MODULE] Message`. (FR-010)
- [X] T008 [P] Create `code/utils/config.py` with explicit configuration: `seed=42`, `device="cpu"`, `model_name="facebook/opt-125m"`. Ensure these are the default values used by all agents. (FR-002)

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

- [X] T011 [S] [US-1] Implement CLI flag parsing in `code/run_experiment.py`: Accept `--context {full,limited}`, `--agents N`, and `--dataset {hanabi,coqa}`. If dataset is missing or URL not in verified block, raise ValueError and trigger synthetic fallback with explicit error logging. (FR-001)
- [X] T011c [S] [US-1] **DEPENDENCY: T011c must complete before T011b.** Implement dataset loading logic in `code/run_experiment.py`: Integrate `loaders.py` and `synthetic.py`, ensuring data is checksummed before use. **Specifics**: Compute sha256 checksum of the downloaded dataset file and write the hash and source URL to `data/manifest.json`. This task prepares the data stream required by the simulation loop. Dependencies: T004, T004b.
- [X] T011b [S] [US-1] Implement game simulation loop in `code/run_experiment.py`: Orchestrate agents, memory buffer, and turn-based interaction for a single game. Protocol: (1) Agent observes state, (2) Agent generates action/memory, (3) Buffer updates, (4) Next agent. Output a single game result row with `game_id`, `specialization_index`, `retrieval_efficiency`. Dependencies: T011c. (FR-004, FR-005)
- [X] T012 [P] [US-1] Implement specialization index computation in `code/metrics/specialization.py`: Calculate distribution-based metric of per-agent fact contribution, bounded within a non-negative range. Include validation logic to log failures if bounds are violated. (FR-004)
- [X] T013 [P] [US-1] Implement cue-retrieval efficiency in `code/metrics/retrieval.py`: Calculate proportion of successful retrievals vs. a theoretical baseline derived from the number of agents. Include validation logic to log failures if metric is out of bounds [0, 1]. (FR-005)
- [X] T015 [S] [US-1] Output `results_full.csv` to `projects/PROJ-social-memory-networks-modeling-collecti/results/` with `game_id`, `specialization_index`, `retrieval_efficiency`, `context_condition`, `agent_count` for N games. **Game Count Logic**: Read `N` from `os.environ.get('SIMULATION_GAME_COUNT', '200')`. If `SIMULATION_GAME_COUNT` is not set, default to 200 (CPU budget). If set to 1000, run 1000 (GPU budget). (US-1, FR-004, FR-005, SC-001). Dependencies: T011b, T012, T013.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Context‑Window Truncation Impact (Priority: P2)

**Goal**: Compare baseline metrics against a limited‑context condition to test robustness under context limits

**Independent Test**: Run the experiment with the *Limited‑context* condition and verify that the statistical comparison reports a significant interaction (p < 0.05) or a documented null result.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US-2] Contract test for ANOVA output schema in `code/tests/contract/test_anova.py`
- [X] T017 [P] [US-2] Integration test for limited-context simulation in `code/tests/integration/test_limited_context.py`

### Implementation for User Story 2

- [X] T018 [S] [US-2] Implement limited-context simulation and systematic sweep in `code/run_experiment.py`. **Sweep Logic**: Explicitly iterate over token limits {128, 256, 512} as mandated by FR-008. For each limit, run the simulation and accumulate raw results. **Output**: Write a raw CSV `results_sweep_raw.csv` to `projects/PROJ-social-memory-networks-modeling-collecti/results/` containing all game results for all limits. Do not generate the trend report here; T022 will process this file. Dependencies: T011b, T011c. (FR-008, US-2)
- [X] T019 [S] [US-2] Output `results_limited.csv` with same metrics to `projects/PROJ-social-memory-networks-modeling-collecti/results/` for N games. **Game Count Logic**: Read `N` from `os.environ.get('SIMULATION_GAME_COUNT', '200')`. If `SIMULATION_GAME_COUNT` is not set, default to 200 (CPU budget). If set to 1000, run 1000 (GPU budget). (US-2). Dependencies: T011b, T018.
- [X] T015 [S] [US-1] Output `results_full.csv` to `projects/PROJ-social-memory-networks-modeling-collecti/results/` with `game_id`, `specialization_index`, `retrieval_efficiency`, `context_condition`, `agent_count` for N games. **Game Count Logic**: Read `N` from `os.environ.get('SIMULATION_GAME_COUNT', '200')`. If `SIMULATION_GAME_COUNT` is not set, default to 200 (CPU budget). If set to 1000, run 1000 (GPU budget). (US-1, FR-004, FR-005, SC-001). Dependencies: T011b, T012, T013.
- [X] T020 [S] [US-2] Implement a Mixed-Design ANOVA in `code/analysis/anova.py` using `statsmodels`.
 - **Data Structure**: Combine `results_full.csv` and `results_limited.csv` into a single long-format DataFrame with columns: `game_id`, `context_condition` (full/limited), `metric_name` (specialization/retrieval), and `metric_value`.
 - **Model Formula**: `metric_value ~ C(context_condition) * C(metric_name)`.
 - **Output**: Compute and report the interaction p-value for the term `C(context_condition):C(metric_name)`. Dependencies: T011b (Full Context Sim), T018 (Limited Context Sim), T015, T019. (FR-006)
- [X] T021 [P] [US-2] Apply Bonferroni correction to all family‑wise hypothesis tests and report corrected α in `code/analysis/anova.py`. (FR-007)
- [X] T022 [S] [US-2] Implement sensitivity analysis in `code/analysis/sensitivity.py`: Read `results_sweep_raw.csv` generated by T018. Aggregate metrics by token limit {128, 256, 512}. Output CSV trend report `results/sensitivity_trend.csv` with columns: `token_limit`, `mean_specialization`, `mean_retrieval`. (FR-008). Dependencies: T018.
- [X] T023 [S] [US-2] Implement power analysis in `code/analysis/power.py`: Estimate detectable effect size for N=1000, alpha=0.05, power=0.80. Flag if power < 0.70. (FR-009)
- [X] T024 [US-2] Generate `power_analysis_report.md` in `projects/PROJ-586-social-memory-networks-modeling-collecti/results/` with results from T023. (SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Scaling Analysis Across Agent Populations (Priority: P3)

**Goal**: Investigate how the fidelity of collective remembering scales when the number of agents varies across different group sizes.

**Independent Test**: Run the experiment for each specified agent count and produce a plot of specialization index and retrieval efficiency versus number of agents, along with a fitted power‑law exponent.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US-3] Contract test for scaling plot schema in `code/tests/contract/test_scaling.py`
- [X] T026 [P] [US-3] Integration test for agent count variation in `code/tests/integration/test_scaling.py`

### Implementation for User Story 3

- [X] T027 [S] [US-3] Implement game simulation for varying agent counts in `code/run_experiment.py`. Run multiple games for varying agent counts. (US-3)
- [X] T028 [P] [US-3] Implement power-law fitting in `code/analysis/scaling.py`: Fit log-log curves for metric trends vs. agent count (a small set of discrete values) for specialization index and retrieval efficiency. (US-3)
- [X] T029 [P] [US-3] Compute confidence intervals for fitted exponents using bootstrapping and output results to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_confidence_intervals.json`. (US-3, SC-005)
- [X] T030 [US-3] Generate `scaling_plot.pdf` with fitted power‑law curves for specialization index and retrieval efficiency. **Verification**: Verify PDF contains the exact string: "a limited number of data points limits power-law reliability" in the figure caption or footnote. (US-3, SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2).
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). **CRITICAL**: T018 (Sweep) must be completed before T022 (Sensitivity Analysis).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2).

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
Task: "Implement CLI flag parsing in code/run_experiment.py"
Task: "Implement specialization index computation in code/metrics/specialization.py"
Task: "Implement cue-retrieval metric in code/metrics/retrieval.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch all models for User Story 2 together:
Task: "Implement Mixed-Design ANOVA analysis in code/analysis/anova.py"
Task: "Implement sensitivity analysis in code/analysis/sensitivity.py"
Task: "Implement power analysis in code/analysis/power.py"
Task: "Implement limited-context simulation and sweep in code/run_experiment.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently.
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (includes Sweep & ANOVA)
4. Add User Story 3 → Test independently → Deploy/Demo (includes Scaling)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (Sweep & ANOVA)
 - Developer C: User Story 3 (Scaling)
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
- **Compute Constraint**: CPU-only inference, no CUDA, default float32 precision
- **Game Counts**: Controlled by `SIMULATION_GAME_COUNT` env var (Default 200 for CPU, 1000 for GPU).
- **Dataset Constraint**: Hanabi/CoQA URLs are not in the verified block; synthetic fallback is mandatory if URLs are missing.
- **ANOVA Design**: Mixed-Design ANOVA with Context × Metric interaction (FR-006), NOT separate ANOVAs.
- **Power Analysis**: N=1000 (FR-009 spec requirement)
- **Scaling Analysis**: Strictly plots specialization index and retrieval efficiency (SC-005).
- **Scope Integrity**: The project scope is strictly limited to User Stories 1, 2, and 3 as defined in `spec.md` and `FR-001` through `FR-012`. No unauthorized features (Blind Cue, Topology, Forgetting, Noise) are included.
- **Sweep Logic**: T018 performs the systematic sweep over {128, 256, 512} and outputs raw data. T022 analyzes this data.