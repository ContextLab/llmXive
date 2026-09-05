# Tasks: Social Memory Networks: Modeling Collective Remembering in Multi‑Agent LLMs

**Input**: Design documents from `/specs/001-social-memory-networks/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T004 [P] **Verify Dataset URLs**: Implement `code/data/loaders.py` to verify the existence of data sources.
 1. **Hanabi**: Use `gymnasium.make('hanabi-v0')`. If this fails, log the error but DO NOT fallback yet.
 2. **CoQA**: Use `datasets.load_dataset('coqa')`. If this fails, log the error but DO NOT fallback yet.
 3. If a dataset is missing or unreachable, the verification step must log a clear warning but allow the pipeline to proceed to the fallback integration task (T004c) which will handle the final decision. (FR-001, FR-011)
 4. **Output**: Write verification status to `data/verification_status.json` with schema `{"dataset_name": str, "status": "verified"|"missing", "timestamp": str}`. (Executability)
- [X] T004b [P] **Implement Synthetic Fallback**: Implement `code/data/synthetic.py` to create a set of synthetic cue-response pairs (minimum 10) from available context spans if explicit cues are missing. This task MUST NOT be called during the verification phase (T004). It is only to be used as a fallback mechanism if the real dataset fetch fails during the actual run. (FR-011)
- [X] T004c [P] **Integrate Fallback Logic**: Update `code/data/loaders.py` to call T004b ONLY if T004 verification fails AND the real dataset fetch fails during the actual run. Ensure no silent fallbacks occur during the verification phase. If the real fetch fails, log the fallback usage to `experiment.log` with specific format: `[FALLBACK] Synthetic cues generated for dataset [NAME]`. (FR-001, FR-011)
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

- [X] T011 [S] [US-1] Implement CLI flag parsing in `code/run_experiment.py`: Accept `--context {full,limited}`, `--agents N`, and `--dataset {hanabi,coqa}`. If dataset is missing or URL not in verified block, proceed to the synthetic fallback mechanism (T004b) with explicit error logging. (FR-001) <!-- FAILED: unspecified -->
- [X] T011c [S] [US-1] **IMPLEMENTATION**: Implement dataset loading logic in `code/run_experiment.py`: Integrate `loaders.py` and `synthetic.py`.
 1. **Streaming**: Use `datasets.load_dataset(..., streaming=True)` for CoQA to handle large files.
 2. **Hanabi**: Use `gymnasium.make('hanabi-v0')`.
 3. **Checksum**: Compute `sha256` checksum of the downloaded dataset file (or the stream if streaming) and write the hash, source URL, and download path to `data/manifest.json`.
 4. **JSON Schema for manifest**: `{"dataset_name": str, "source_url": str, "sha256_hash": str, "download_path": str}`.
 5. **Error Handling**: If the real dataset is unavailable, call T004b to generate synthetic cues and log the fallback usage. Do NOT raise ValueError. (FR-011)
 Dependencies: T004, T004b, T004c. (FR-001, FR-011)
- [X] T011b [S] [US-1] **DEPENDENCY: T011c must complete before T011b.** Implement game simulation loop in `code/run_experiment.py`: Orchestrate agents, memory buffer, and turn-based interaction for a single game. Protocol: (1) Agent observes state, (2) Agent generates action/memory, (3) Buffer updates, (4) Next agent. **Termination Condition**: Game ends when all cards are played or `max_turns=50` is reached. Output a single game result row with `game_id`, `specialization_index`, `retrieval_efficiency`. Dependencies: T011c. (FR-004, FR-005)
- [X] T012 [P] [US-1] Implement specialization index computation in `code/metrics/specialization.py`: Calculate distribution-based metric of per-agent fact contribution, bounded within a non-negative range. Include validation logic to log failures if bounds are violated. (FR-004)
- [X] T013 [P] [US-1] Implement cue-retrieval efficiency in `code/metrics/retrieval.py`: Calculate proportion of successful retrievals vs. a theoretical baseline derived from the number of agents. Include validation logic to log failures if metric is out of bounds [0, 1]. (FR-005)
- [X] T015 [S] [US-1] **Output `results_full.csv`**: Write to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_full.csv`.
 **Columns**: `game_id` (int), `specialization_index` (float), `retrieval_efficiency` (float), `context_condition` (str), `agent_count` (int).
 **Game Count Logic**:
 1. Read `N` from `os.environ.get('SIMULATION_GAME_COUNT', '200')`. The specific value to remove/generalize: 'DEFAULT_COUNT'
 2. **Validation**: If `N` is not an integer or is negative, raise `ValueError("Invalid SIMULATION_GAME_COUNT: must be a positive integer")`. If the variable is unset, default to 200.
 3. **Full Run**: Execute the full simulation (N=200) and write results.
 4. **Power Analysis**: Calculate power based on the planned N=200 (or configured N) with alpha=0.05, power=0.80. If estimated power < 0.70, flag a "Power limitation" in the output. (FR-009)
 Dependencies: T011b, T012, T013. (US-1, FR-004, FR-005, SC-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Context‑Window Truncation Impact (Priority: P2)

**Goal**: Compare baseline metrics against a limited‑context condition to test robustness under context limits

**Independent Test**: Run the experiment with the *Limited‑context* condition and verify that the statistical comparison reports a significant interaction (p < 0.05) or a documented null result.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US-2] Contract test for ANOVA output schema in `code/tests/contract/test_anova.py`
- [X] T017 [P] [US-2] Integration test for limited-context simulation in `code/tests/integration/test_limited_context.py`

### Implementation for User Story 2

- [X] T018 [S] [US-2] **IMPLEMENTATION**: Implement limited-context simulation and systematic sweep in `code/run_experiment.py`.
 **Sweep Logic**: Explicitly iterate over token limits {128, 256, 512} as mandated by FR-008.
 **Execution**: For each limit, run the simulation with N=200 games (planned CPU budget) and accumulate raw results.
 **Output**: Write a raw CSV `results_sensitivity.csv` to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/` containing all game results for all limits.
 **Schema**: `token_limit` (int), `game_id` (int), `specialization_index` (float), `retrieval_efficiency` (float), `context_condition` (str).
 **Error Handling**: If `results_sensitivity.csv` is not generated, raise `FileNotFoundError`.
 Dependencies: T011b, T011c. (FR-008, US-2)
- [X] T019 [S] [US-2] **Output `results_limited.csv`**: Write to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_limited.csv` with same metrics for N games.
 **Game Count Logic**: Read `N` from `os.environ.get('SIMULATION_GAME_COUNT', '200')`. Validate as in T015.
 **Data Source**: Derive from `results_sensitivity.csv` (T018) by filtering for `context_condition="limited"`.
 Dependencies: T011b, T018. (US-2)
- [X] T020 [S] [US-2] **IMPLEMENTATION**: Implement a Two-Way Independent-Samples ANOVA in `code/analysis/anova.py` using `statsmodels`.
 **Data Structure**: Combine `results_full.csv` (T015) and `results_limited.csv` (T019) into a single long-format DataFrame.
 **Transformation**: For each row in the combined data, create two rows in the long-format: one for `metric_name="specialization"` and one for `metric_name="retrieval"`.
 **Model Formula**: `metric_value ~ C(context_condition) * C(metric_name)`.
 **Design Constraint**: Explicitly treat `context_condition` as a **Between-Subjects** factor (different games) and `metric_name` as a **Within-Subjects** factor (same game, two measurements) is NOT applicable here. Instead, treat `context_condition` and `metric_name` as independent factors in a Two-Way ANOVA where games are the unit of analysis, as per FR-006.
 **Output**: Compute and report the interaction p-value for the term `C(context_condition):C(metric_name)`.
 Dependencies: T015, T019. (FR-006)
- [X] T021 [P] [US-2] Apply Bonferroni correction to all family‑wise hypothesis tests and report corrected α in `code/analysis/anova.py`. (FR-007)
- [X] T022 [S] [US-2] **IMPLEMENTATION**: Implement sensitivity analysis in `code/analysis/sensitivity.py`.
 **Input**: Read `results_sensitivity.csv` generated by T018.
 **Check**: If file is missing, raise `FileNotFoundError("results_sensitivity.csv not found. Run T018 first.")`.
 **Aggregation**: Aggregate metrics by token limit {128, 256, 512}.
 **Output**: Write CSV `results/sensitivity_trend.csv` with columns: `token_limit`, `mean_specialization`, `mean_retrieval`, `max_absolute_change`.
 **Calculation**: `max_absolute_change` must be the maximum absolute difference in any metric between any two adjacent thresholds.
 Dependencies: T018. (FR-008)
- [X] T023 [S] [US-2] Implement power analysis in `code/analysis/power.py`: Estimate detectable effect size for N=200 (using full run data from T015/T019), alpha=0.05, power=0.80. **Requirement**: If the estimated power < 0.70, the system MUST flag a "Power limitation" in the output. (FR-009)
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

- [X] T027 [S] [US-3] **IMPLEMENTATION**: Implement game simulation for varying agent counts in `code/run_experiment.py`. Run multiple games for varying agent counts (small, medium, and large groups). Dependencies: T011b, T011c. (US-3)
- [X] T028 [S] [US-3] **IMPLEMENTATION**: Implement power-law fitting in `code/analysis/scaling.py`.
 **Algorithm**: Use `numpy.polyfit` on log-transformed data (`log(N)` vs `log(metric)`) for specialization index and retrieval efficiency.
 **Bootstrapping**: Perform bootstrap resamples to estimate the confidence interval for the slope (beta).
 **Output**: Write results to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_confidence_intervals.json` with schema: `{"metric": str, "beta": float, "ci_lower": float, "ci_upper": float}`.
 Dependencies: T027. (US-3, SC-005)
- [X] T029 [P] [US-3] Compute confidence intervals for fitted exponents using bootstrapping and output results to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_confidence_intervals.json`. (US-3, SC-005)
- [X] T030 [S] [US-3] **IMPLEMENTATION**: Generate `scaling_plot.pdf` with fitted power‑law curves.
 **Library**: Use `matplotlib`.
 **Requirement**: Inject the exact string "a limited number of data points limits power-law reliability" into the figure caption or footnote.
 **Implementation Detail**: Use `plt.suptitle("Scaling Analysis")` AND use `plt.text(0.5, -0.1, f"Note: {N} data points limit power-law reliability", transform=ax.transAxes, ha='center', fontsize=8)` to ensure the string appears in the final PDF. The string must be dynamically generated from the spec requirement, not hardcoded as a static title.
 Dependencies: T028. (US-3, SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Advanced Transactive Memory Dynamics & Robustness (REMOVED)

**Status**: REMOVED. These tasks (T031-T038) were identified as unapproved scope creep as they implement features (Blind Agents, Forgetting Mechanisms, Noise Modeling, Network Topology) not present in `spec.md` or `plan.md`. All tasks in this phase have been excised to maintain scope integrity.

**Removed Tasks**:
- T031: Implement "Blind" Agent Condition
- T032: Implement Cue-Driven Retrieval Specificity Test
- T033: Implement Signal Decay / Forgetting Mechanism
- T034: Implement Adaptive Noise in Consolidation
- T035: Implement Noise Modeling for System 1 vs System 2
- T036: Implement Network Topology Analysis
- T037: Implement Epistemic Decay / Obsolete Prior Discarding
- T038: Implement Consolidation Mechanism (CREB Analogue)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Advanced Dynamics (Phase 6)**: REMOVED.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2).
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). **CRITICAL**: T018 (Sweep) must be completed before T022 (Sensitivity Analysis).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2).
- **Advanced Dynamics (Phase 6)**: REMOVED.

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
Task: "Implement Two-Way Independent-Samples ANOVA analysis in code/analysis/anova.py"
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
- **Game Counts**: Controlled by `SIMULATION_GAME_COUNT` env var (Default for CPU). **Note**: T015 runs full simulation (N=200) directly.
- **Dataset Constraint**: Hanabi uses `gymnasium`; CoQA uses HuggingFace. Synthetic fallback is mandatory if URLs are missing (T011c).
- **ANOVA Design**: Two-Way Independent-Samples ANOVA with Context × Metric interaction (FR-006), NOT Mixed-Design ANOVA.
- **Power Analysis**: N=200 (planned design) enforced by T015 and T023 to correctly flag limitations if power < 0.70.
- **Scaling Analysis**: Strictly plots specialization index and retrieval efficiency (SC-005).
- **Scope Integrity**: The project scope is strictly limited to User Stories 1, 2, and 3 as defined in `spec.md` and `FR-001` through `FR-012`. **Phase 6 has been removed** as it contained unapproved scope creep.
- **Sweep Logic**: T018 performs the systematic sweep over {128, 256, 512} and outputs `results_sensitivity.csv`. T022 analyzes this data and calculates max_absolute_change.
- **Research Enhancements**: REMOVED. The project scope is strictly limited to the spec.
- **Reviewer Concerns Addressed**:
 - Phase 6 tasks (T031-T038) removed due to lack of spec definition.
 - T011c now implements mandatory synthetic fallback (FR-011).
 - T015 removed pilot run logic; power analysis based on planned N=200.
 - T018 output renamed to `results_sensitivity.csv` with defined schema.
 - T030 uses dynamic string formatting for reliability note.
 - T020 implements Two-Way Independent-Samples ANOVA as per spec.
