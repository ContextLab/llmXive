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
- [X] T002 [P] Initialize `requirements.txt` with pinned versions: `transformers>=4.35.0`, `torch>=2.0.0+cpu`, `scikit-learn>=1.3.0`, `pandas>=2.0.0`, `pytest>=7.0.0`, `numpy>=1.24.0`, `matplotlib>=3.7.0`, `statsmodels>=0.14.0`.
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement dataset loaders in `code/data/loaders.py`: Verify URLs against a whitelist. If the dataset (Hanabi/CoQA) lacks a verified URL in the `verified_datasets` block, raise a clear error and trigger the synthetic fallback. (FR-001, FR-011)
- [X] T004b [P] Implement synthetic fallback generator in `code/data/synthetic.py`: Create a set of synthetic cue-response pairs (minimum 10 per game) from available context spans if explicit cues are missing. (FR-011)
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

- [X] T011 [P] [US-1] Implement CLI flag parsing in `code/run_experiment.py`: Accept `--context {full,limited}`, `--agents N`, and `--dataset {hanabi,coqa}`. If dataset is missing, invoke synthetic fallback. (FR-001) <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T011b [P] [US-1] Implement game simulation loop in `code/run_experiment.py`: Orchestrate agents, memory buffer, and turn-based interaction for a single game.
- [X] T011c [P] [US-1] Implement dataset loading logic in `code/run_experiment.py`: Integrate `loaders.py` and `synthetic.py`, ensuring data is checksummed before use.
- [X] T012 [P] [US-1] Implement specialization index computation in `code/metrics/specialization.py`: Calculate distribution-based metric of per-agent fact contribution, bounded 0 to log2(N_agents). (FR-004)
- [ ] T013 [P] [US-1] Implement cue-retrieval efficiency in `code/metrics/retrieval.py`: Calculate proportion of successful retrievals vs. a theoretical baseline derived from the number of agents. (FR-005)
- [X] T014 [P] [US-1] Implement validation logic in `code/metrics/validator.py`: Assert `(games_with_metrics / total_games) >= 0.95`; log errors for failed games. (SC-001)
- [ ] T015 [US-1] Output `results_full.csv` to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/` with `game_id`, `specialization_index`, `retrieval_efficiency`, `context_condition`, `agent_count` for [deferred] games. (US-1, FR-004, FR-005, SC-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Context‑Window Truncation Impact (Priority: P2)

**Goal**: Compare baseline metrics against a limited‑context condition to test robustness under context limits

**Independent Test**: Run the experiment with the *Limited‑context* condition and verify that the statistical comparison reports a significant interaction (p < 0.05) or a documented null result.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US-2] Contract test for ANOVA output schema in `code/tests/contract/test_anova.py`
- [X] T017 [P] [US-2] Integration test for limited-context simulation in `code/tests/integration/test_limited_context.py`

### Implementation for User Story 2

- [ ] T018 [US-2] Implement limited-context simulation in `code/run_experiment.py`: Truncate context to a specified token limit before passing to the model. (US-2)
- [X] T019 [US-2] Output `results_limited.csv` with same metrics to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/` for 1000 games. (US-2)
- [X] T020 [P] [US-2] Implement a two-way independent-samples ANOVA in `code/analysis/anova.py` using `statsmodels.stats.anova.anova_lm`.
 - **Data Structure**: Combine `results_full.csv` and `results_limited.csv` into a single long-format DataFrame with columns: `game_id`, `context_condition` (full/limited), `metric_name` (specialization/retrieval), and `metric_value`.
 - **Model Formula**: `metric_value ~ C(context_condition) * C(metric_name)`.
 - **Output**: Compute and report the interaction p-value for the term `C(context_condition):C(metric_name)`. (FR-006)
- [X] T021 [P] [US-2] Apply Bonferroni correction to all family‑wise hypothesis tests and report corrected α in `code/analysis/anova.py`. (FR-007)
- [~] T022 [US-2] Implement sensitivity analysis in `code/analysis/sensitivity.py`: Sweep token thresholds explicitly across the set {128, 256, 512} tokens and record how specialization and retrieval metrics vary for each threshold. (FR-008)
- [X] T023 [US-2] Implement power analysis in `code/analysis/power.py`: Estimate detectable effect size for N=1000, alpha=0.05, power=0.80; flag if power < 0.70. (FR-009)
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

- [~] T027 [US-3] Implement game simulation for varying agent counts (800 games per configuration) in `code/run_experiment.py`. (US-3) <!-- FAILED: unspecified -->
- [~] T028 [P] [US-3] Implement power-law fitting in `code/analysis/scaling.py`: Fit log-log curves for metric trends vs. agent count (small to medium cohorts) for specialization index and retrieval efficiency. (US-3)
- [X] T029 [P] [US-3] Compute 95% confidence intervals for fitted exponents using bootstrapping (1000 resamples) and output results to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_confidence_intervals.json`. (US-3, SC-005)
- [ ] T030 [US-3] Generate `scaling_plot.pdf` with fitted power‑law curves for specialization index and retrieval efficiency, and an explicit text note stating that "3 data points limit power-law reliability". (US-3, SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address remaining requirements

- [X] T031 [P] Run `quickstart.md` validation: Execute all commands listed, verify exit code 0 for each. (FR-001)
- [X] T032 [P] Remove all 8-bit/4-bit quantization imports, verify no CUDA imports in all Python files (compute feasibility)
- [X] T033 [P] Implement file-locking with fcntl and add conflict retry logic in `code/utils/serialization.py` (FR-012)
- [X] T034 [P] Update `research.md` with reviewer feedback integration notes
- [X] T035 [P] Run full pipeline on CI runner, record runtime (seconds), peak RAM (GB), and disk usage (GB) in `projects/PROJ-586-social-memory-networks-modeling-collecti/results/compute_metrics.json`. (FR-001)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **CRITICAL**: T020 (ANOVA) depends on the completion of T015 (results_full.csv) and T019 (results_limited.csv). T018 and T019 must run before T020.
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
Task: "Implement CLI flag parsing in code/run_experiment.py"
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
- **Compute Constraint**: CPU-only inference, no CUDA, default float32 precision
- **Game Counts**: US-1/US-2 = 1,000 games per condition (spec requirement); US-3 = 800 games per configuration (spec requirement)
- **Dataset Constraint**: Hanabi/CoQA URLs are not in the verified block; synthetic fallback is mandatory if URLs are missing.
- **ANOVA Design**: Single two-way ANOVA with Context × Metric interaction (FR-006), NOT separate ANOVAs. The plan's "Separate ANOVAs" description is overridden by the spec's FR-006.
- **Power Analysis**: N=1000 (FR-009 spec requirement)
- **Scaling Analysis**: Strictly plots specialization index and retrieval efficiency (SC-005).
