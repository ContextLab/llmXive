# Tasks: llmXive follow-up: extending "Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are **MANDATORY** per Spec Independent Test requirements.

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project structure per `plan.md` by executing: `mkdir -p src/{config,sim,retrieval,conditions,analysis,data/{raw,derived},tests/{contract,integration,unit}} data/raw data/derived state docs`. Ensure `src/`, `tests/`, `data/` directories exist.
- [X] T002 [P] Initialize Python project with `requirements.txt` containing pinned versions: `transformers==4.35.0`, `torch==2.1.0`, `scipy==1.11.0`, `datasets==2.14.0`, `alfworld==1.1.0`, `pandas==2.1.0`, `pytest==7.4.0`, `ruff==0.1.0`, `black==23.0.0`. **Note**: Model runs in **float32** (default precision) as per Spec Assumptions.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with standard configs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/config/config.py` with pinned random seeds, paths, and ALFWorld hyperparameters. Define `SEED=42`, `DATA_PATH`, `MODEL_ID`.
- [X] T005 [P] Create `src/sim/alfworld_runner.py` to wrap the ALFWorld environment with deterministic state logging. Implement `run_episode(task_id, seed)` returning action log and state transitions.
- [X] T006 [P] Implement `src/sim/validation.py` to map agent actions to ground-truth state transitions. Define `validate_trajectory(action_log, ground_truth_log)` function.
- [X] T007a [P] Implement `src/sim/validation.py` to extract ground-truth state transitions from the **ALFWorld simulator state transition log** (via the simulator's API/stdout) and save raw logs to `data/raw/ground_truth_raw.json` with checksumming. Ensure logs are saved as a distinct artifact for 'Validation Independence'.
- [X] T007b [P] Implement `src/sim/validation.py` to save the validated ground-truth mapping (if any processing occurs) to `data/derived/ground_truth_validated.json`. Ensure strict separation from raw logs.
- [X] T008 [P] Create `src/retrieval/task_bank.py` to load the frozen, human-annotated task bank (SQLite/JSON). Implement `get_task_definition(task_id)`.
- [X] T009 [P] Implement `src/config/cpu_config.yaml` with `CPU_DEVICE=true` and `MAX_RAM_GB=7` to enforce CPU-only execution constraints.
- [X] T010 [P] Implement data streaming utilities in `src/data/stream_utils.py` to handle large trajectory logs in chunks using `datasets.load_dataset(..., streaming=True)`.
- [X] T036a [P] Implement `src/analysis/power_analysis.py` to perform **pre-experimental** power analysis for N=500 (single dataset processed into 3 conditions) with target power ≥0.8. Output `data/derived/power_analysis_report.json` justifying sample size.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Validate Baseline Failure Trajectories (Priority: P1) 🎯 MVP

**Goal**: Generate a dataset of at least 500 failed agent trajectories in ALFWorld using Llama-8B (Standard WIA) and validate them against ground-truth.

**Independent Test**: Run the generation script and verify `data/raw/baseline_failures.json` contains ≥500 entries with valid IDs, failure steps, and linked ground-truth transitions.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Write contract test: Verify output schema of `src/sim/trajectory_generator.py` in `tests/contract/test_trajectory_schema.py`.
- [X] T012 [P] [US1] Write integration test: Validate end-to-end generation of 500 failures in `tests/integration/test_baseline_generation.py`.

### Implementation for User Story 1

- [X] T013 [US1] Implement `src/sim/trajectory_generator.py` to load `meta-llama/Llama-3-8B-Instruct` (**float32, CPU mode**) and load task definitions from Frozen Task Bank (T008). Run ALFWorld episodes to generate failures. **Implement generation loop**: if a trajectory fails ground-truth validation (T006), discard it and retry.
- [X] T013b [US1] Implement **validation filter** in `src/sim/trajectory_generator.py` to check trajectory validity against ground-truth before saving.
- [X] T013c [US1] Implement **timeout and skip logic** in `src/sim/trajectory_generator.py`. If the loop exceeds `MAX_ATTEMPTS` (e.g., 2000) without reaching 500 valid failures, log the specific failure reason to `data/raw/excluded_log.json`, save available data, and proceed to ensure the pipeline does not hang indefinitely.
- [X] T014 [US1] Implement `extract_failure_reason(action_log)` function in `src/sim/trajectory_generator.py` to detect failure states and extract patterns (e.g., "failed to pick up object X after Y steps").
- [X] T016 [US1] Save validated baseline trajectories to `data/raw/baseline_failures.json` with unique IDs and failure reasons. **Ensure only validated trajectories are saved**; unvalidated ones must be discarded per T013 logic.
- [X] T017 [US1] Add logging for excluded trajectories (ambiguous root causes) to `data/raw/excluded_log.json`.
- [X] T018 [US1] Apply ground-truth validation logic (from T006) in `src/sim/validation.py` to cross-reference `data/raw/baseline_failures.json` with `data/raw/ground_truth_raw.json`.
- [X] T018a [US1] Implement explicit 'discard/retry' logic in `src/sim/trajectory_generator.py` to halt the generation loop and exclude invalid entries before saving, ensuring FR-002 compliance.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Degraded World Model Condition (Priority: P2)

**Goal**: Simulate the "Degraded" condition (WIA horizon=0) by **processing the validated Baseline trajectories** and recording retrieval relevance scores.

**Independent Test**: Run the degraded script on P1 data and verify `data/derived/degraded_scores.json` contains scores consistent with failure modes.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T019 [P] [US2] Write contract test: Verify score calculation logic in `tests/contract/test_degraded_scoring.py`.
- [X] T020 [P] [US2] Write integration test: Verify degraded condition output in `tests/integration/test_degraded_condition.py`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `src/conditions/degraded.py` to configure WIA prediction horizon = 0 (or randomized prompt) and verify output contains no predictive context.
- [X] T022 [US2] Create `src/conditions/run_degraded.py` to **load `data/raw/baseline_failures.json`** and apply the WIA=0 transformation (re-simulate the failure analysis step with WIA=0) to generate the **Degraded Cohort**. Save to `data/raw/degraded_failures.json`. **Do NOT generate fresh trajectories.**
- [X] T023 [US2] Integrate `src/retrieval/relevance_scorer.py` to calculate retrieval relevance scores for each degraded trajectory.
- [X] T024 [US2] Aggregate results and save mean scores to `data/derived/degraded_stats.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Apply Syntactic Abstraction Intervention (Priority: P3)

**Goal**: Apply the rule-based "failure abstraction layer" to the Degraded cohort and measure recovery in retrieval relevance and task completion rates.

**Independent Test**: Run the intervention script and verify `data/derived/intervention_scores.json` shows measurable increase over degraded scores.

### Tests for User Story 3 (MANDATORY) ⚠️

- [X] T025 [P] [US3] Write contract test: Verify syntactic parser output schema in `tests/contract/test_syntactic_parser.py`.
- [X] T026 [P] [US3] Write integration test: Verify intervention recovery metrics in `tests/integration/test_intervention_condition.py`.

### Implementation for User Story 3

- [X] T022a [US3] Create `src/conditions/run_intervention.py` to **load `data/raw/degraded_failures.json`** (output of T022) and prepare for syntactic abstraction. **Do NOT generate fresh data.**
- [X] T027 [P] [US3] Implement `src/conditions/intervention.py` to load the rule-based parser.
- [X] T028 [US3] Implement `src/conditions/syntactic_parser.py` using `re` and `json` to extract patterns (e.g., "failed to pick up object X") from **raw action logs** in the Degraded cohort.
- [X] T029 [US3] Apply the parser to Degraded failure analyses (from T022) to generate **abstracted failure signals**.
- [X] T029b [US3] Implement **mapping logic** in `src/retrieval/task_bank.py` to map the **abstracted failure signals** (from T029) to specific task definitions in the Frozen Task Bank. Save the resulting retrieved task definitions to `data/derived/retrieved_tasks.json`.
- [X] T030 [US3] Re-calculate retrieval relevance scores using abstracted signals via `src/retrieval/relevance_scorer.py`.
- [X] T031 [US3] Retrieve and output task definitions for re-execution from the Intervention step to `data/derived/retrieved_tasks.json` (consumes T029b output).
- [X] T032 [US3] Implement `run_reexecution(task_id, trajectory_id)` in `src/sim/alfworld_runner.py` to measure task completion rates. **Must use the task definition from `data/derived/retrieved_tasks.json` (T029b)** and inject it as the prompt for re-execution in the simulator. Explicitly describe the injection mechanism: use the abstracted signal to construct the system prompt for the next N steps in the simulator.
- [X] T033 [US3] Execute the re-execution loop for all retrieved tasks and save completion rates to `data/derived/intervention_completion.json`.
- [X] T034 [US3] Save intervention scores and completion rates to `data/derived/intervention_stats.json`.
- [X] T035 [US3] Implement fallback logic: if parser fails, copy raw degraded analysis to abstracted field and log event to `data/derived/parser_fallbacks.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Statistical Analysis & Power Validation (Cross-Cutting)

**Purpose**: Perform statistical comparisons and power analysis as required by FR-007 and FR-008

- [X] T036b [P] Implement `src/analysis/power_analysis.py` to perform the **final power calculation** using the actual generated N. **If power < 0.8**, generate a report documenting the limitation and justifying the fixed N=500 per Spec Assumptions. **Do NOT implement a loop to increase N.**
- [X] T036c [P] Implement `src/analysis/report_generator.py` to generate the final **Power Analysis Report** (`data/derived/final_power_report.json`) if T036b detects a power shortfall, explicitly stating the constraint violation and the decision to proceed with N=500.
- [X] T037 [P] Implement `src/analysis/statistical_tests.py` with Shapiro-Wilk normality check.
- [X] T038 [P] Implement conditional logic in `src/analysis/statistical_tests.py`: IF p < 0.05 THEN Mann-Whitney U, ELSE t-test.
- [X] T039 [P] Run statistical comparison across Baseline, Degraded, and Intervention groups. **Explicitly invoke the conditional branch** (Shapiro-Wilk -> t-test/Mann-Whitney) defined in T037/T038 based on normality check results.
- [X] T040 [P] Save final statistical results to `data/derived/final_stats.csv` with p-values and effect sizes.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Documentation updates in `docs/` (README, quickstart.md).
- [X] T042 [P] Performance optimization for CPU-only execution: Enable streaming in `datasets.load_dataset` and ensure peak RAM < 7GB.
- [X] T043 [P] Additional unit tests in `tests/unit/` for parser and scorer.
- [X] T044 [P] Implement `src/utils/checksums.py` to verify all data artifacts have checksums recorded in `state/...yaml`.
- [X] T045 [P] Run `quickstart.md` validation to ensure reproducibility.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Statistical Analysis (Phase 6)**: Depends on completion of US1, US2, and US3 data generation

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Consumes US1 output** (T016) for Degraded processing
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Consumes US2 output** (T022) for Intervention processing

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
- Statistical analysis tasks (T036-T040) can run in parallel once data is generated

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Write contract test for trajectory schema in tests/contract/test_trajectory_schema.py"
Task: "Write integration test for baseline generation in tests/integration/test_baseline_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement trajectory generation loop in src/sim/trajectory_generator.py"
Task: "Implement validation filter in src/sim/trajectory_generator.py"
Task: "Implement timeout and skip logic in src/sim/trajectory_generator.py"
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
- **Data Integrity**: All data loaders MUST fail loudly on real data fetch errors; no synthetic fallbacks allowed.
- **Compute Constraints**: All LLM inference must be configured for CPU-only execution (Llama-8B **float32**).
- **Streaming**: Use `datasets.load_dataset(..., streaming=True)` for any large data processing to respect RAM limits.
- **Validation**: Every generated trajectory MUST be validated against ground-truth before saving; unvalidated ones must be discarded.
- **Cohorts**: Three independent cohorts (Baseline, Degraded, Intervention) must be generated sequentially: Baseline -> Degraded (process Baseline) -> Intervention (process Degraded).
- **Power Analysis**: N=500 is a fixed target. If power < 0.8, report the limitation; do not dynamically increase N.