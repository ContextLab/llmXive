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
- [X] T002 [P] Initialize Python project with `requirements.txt` containing pinned versions: `transformers==4.35.0`, `torch==2.1.0`, `scipy==1.11.0`, `datasets==2.14.0`, `alfworld==1.1.0`, `pandas==2.1.0`, `pytest==7.4.0`, `ruff==0.1.0`, `black==23.0.0`. **Note**: Model runs in standard floating-point precision as per Spec Assumptions. **Instruction**: Include `torch.set_float32_matmul_precision('high')` in `src/config/config.py` as a safety measure to enforce float32 in the CPU environment, aligning with the Spec's intent without contradicting the 'default precision' assumption.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with standard configs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **T046 is the first blocking prerequisite for all data generation tasks.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **T046 must be completed before T013.**

- [X] T004 [P] Implement `src/config/config.py` with pinned random seeds, paths, and ALFWorld hyperparameters. Define `SEED=42`, `DATA_PATH`, `MODEL_ID`.
- [X] T005 [P] Create `src/sim/alfworld_runner.py` to wrap the ALFWorld environment with deterministic state logging. Implement `run_episode(task_id, seed)` returning action log and state transitions.
- [X] T006 [P] Implement `src/sim/validation.py` to map agent actions to ground-truth state transitions. Define `validate_trajectory(action_log, ground_truth_log)` function.
- [X] T007a [P] Implement `src/sim/validation.py` to extract ground-truth state transitions from the **ALFWorld simulator state transition log** (via the simulator's API/stdout) and save raw logs to `data/raw/ground_truth_raw.json` with checksumming. **Crucially, implement the 'deterministic priority rule' for ambiguous cases as defined in Spec Assumptions before saving.** Ensure logs are saved as a distinct artifact for 'Validation Independence'.
- [X] T007b [P] Implement `src/sim/validation.py` to save the validated ground-truth mapping (if any processing occurs) to `data/derived/ground_truth_validated.json`. Ensure strict separation from raw logs.
- [X] T008 [P] Create `src/retrieval/task_bank.py` to load the frozen, human-annotated task bank (SQLite/JSON). Implement `get_task_definition(task_id)`.
- [X] T009 [P] Implement `src/config/cpu_config.yaml` with `CPU_DEVICE=true` and `MAX_RAM_GB=7` to enforce CPU-only execution constraints.
- [X] T010 [P] Implement data streaming utilities in `src/data/stream_utils.py` to handle large trajectory logs in chunks using `datasets.load_dataset(..., streaming=True)`.
- [ ] T046 [P] [US1] Implement **real data source verification** in `src/sim/trajectory_generator.py`. Explicitly verify that the **`meta-llama/Llama-3-8B`** model is accessible via Hugging Face `transformers` before generation starts. **If the model cannot be loaded (e.g., `RepositoryNotFoundError`, `OSError`), the script MUST raise the exception and exit immediately.** **Do NOT** implement a fallback to a smaller model or synthetic data. **Deliverable**: Write a verification log to `data/raw/model_verification_log.json` with keys: `model_id`, `status` (SUCCESS/FAILED), `error_message` (if failed), `timestamp`. **Note**: This is a constitutional requirement for Data Hygiene; the 'CPU-only' constraint refers to the execution environment, not the ability to load the model. The task enforces the 'no synthetic fallback' rule.
- [X] T047 [P] [US1] Implement **ALFWorld environment health check** in `src/sim/alfworld_runner.py`. Before generating trajectories, run a single "dummy" episode using **task_id: [a representative task]** (pick up key) to verify the simulator is correctly installed and configured. If this fails, raise an exception. **Do NOT** attempt to skip environment checks or proceed with a degraded simulator.
- [X] T048 [P] [US1] Implement **strict ground-truth validation logging** in `src/sim/validation.py`. For every trajectory processed, log a detailed entry in `data/raw/validation_log.json` indicating: `trajectory_id`, `validation_status` (PASS/FAIL/AMBIGUOUS), `reason_code`, and `ground_truth_snapshot_id`. This ensures full auditability for FR-002.
- [ ] T049 [P] [US1] Implement **ambiguous case handling** in `src/sim/validation.py`. If a failure trajectory has multiple potential ground-truth causes that cannot be resolved by the deterministic priority rule, mark the trajectory as `EXCLUDED` and write it to `data/raw/excluded_log.json` with a specific `ambiguity_reason` field. **Deliverable**: `data/raw/excluded_log.json` must contain entries with keys: `trajectory_id`, `ambiguity_reason`, `timestamp`. **Do NOT** arbitrarily assign a cause to force inclusion.
- [X] T050 [P] [US2] Implement **WIA Horizon Zero Verification** in `src/conditions/degraded.py`. Add an assertion or unit test within the script that confirms the WIA prediction horizon is strictly set to 0 (or the equivalent "no prediction" state) before processing any trajectory. Log this configuration state to `data/derived/degraded_config.json`.
- [X] T051 [P] [US3] Implement **Syntactic Parser Fallback Safety** in `src/conditions/syntactic_parser.py`. If the rule-based parser fails to match any pattern, the system must **log the specific failure** to `data/derived/parser_fallbacks.json` and **retain the original raw text** for that trajectory in the abstracted output field. **Do NOT** replace the raw text with a generic placeholder or synthetic string.
- [X] T052 [P] [US3] Implement **Re-execution Prompt Injection Validation** in `src/sim/alfworld_runner.py` (T032). Before re-executing a task, verify that the injected prompt (derived from the abstracted signal) is non-empty and contains the required task definition fields: `task_id`, `goal`, `constraints`. If invalid, skip the re-execution and log the error to `data/derived/reexecution_errors.json`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Validate Baseline Failure Trajectories (Priority: P1) 🎯 MVP

**Goal**: Generate a dataset of at least 500 failed agent trajectories in ALFWorld using **Llama-3-8B** (Standard WIA) and validate them against ground-truth.

**Independent Test**: Run the generation script and verify `data/raw/baseline_failures.json` contains ≥500 entries with valid IDs, failure steps, and linked ground-truth transitions.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T011 [P] [US1] Write contract test: Verify output schema of `src/sim/trajectory_generator.py` in `tests/contract/test_trajectory_schema.py`. **Deliverable**: Function `test_trajectory_schema_matches_spec` that loads `specs/001-llmxive-followup/contracts/trajectory_schema.yaml` and asserts the output of `generate_trajectory` matches the schema.
- [X] T012 [P] [US1] Write integration test: Validate end-to-end generation of 500 failures in `tests/integration/test_baseline_generation.py`. **Deliverable**: Function `test_baseline_generation_reaches_500` that asserts `len(data)` >= 500 and all entries have required keys.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `src/sim/trajectory_generator.py` to load **`meta-llama/Llama-3-8B`** (**float32, CPU mode**, using `AutoModelForCausalLM` with `torch_dtype=torch.float32`, `use_cache=False`, and **explicitly calling** `torch.set_float32_matmul_precision('high')`) and load task definitions from Frozen Task Bank (T008). **Pre-requisites**: This task **MUST** wait for T046 (Model Verification) and **T007a** (Ground Truth) to be complete. **Read ground-truth data from `data/raw/ground_truth_raw.json`** for validation. **Implement generation loop**: Run ALFWorld episodes to generate failures. If a trajectory fails ground-truth validation (T006), discard it and retry. **Timeout Logic**: If the loop exceeds `MAX_ATTEMPTS` (configurable, default 1000) without reaching 500 valid failures, **raise a `RuntimeError` with message "Generation failed: <N> valid failures found, expected 500"** and exit with code 1. **Logging**: Log excluded trajectories (ambiguous root causes) to `data/raw/excluded_log.json` (keys: `trajectory_id`, `ambiguity_reason`, `timestamp`). **Validation Filter**: Implement logic to check trajectory validity against ground-truth before saving. **Hard Count Verification**: After generation completes, verify the count of validated trajectories is ≥500. If count < 500, **exit with code 1** and log error to `data/raw/generation_log.json`. **Deliverable**: `data/raw/baseline_failures.json` containing ≥500 entries with keys: `id`, `failure_step`, `ground_truth_id`, `action_log`, `failure_description`. **Do NOT proceed** if valid failures < 500.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Degraded World Model Condition (Priority: P2)

**Goal**: Simulate the "Degraded" condition (WIA horizon=0) by **re-running the ALFWorld agent** with the WIA prediction horizon set to 0 on the baseline failure trajectories and recording retrieval relevance scores. **Note**: The "Degraded Cohort" is generated by re-simulating the agent with WIA=0, not by post-processing text logs. This aligns with the Spec's definition of simulating the condition.

**Independent Test**: Run the degraded script on P1 data and verify `data/derived/degraded_scores.json` contains scores consistent with failure modes.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T019 [P] [US2] Write contract test: Verify score calculation logic in `tests/contract/test_degraded_scoring.py`.
- [X] T020 [P] [US2] Write integration test: Verify degraded condition output in `tests/integration/test_degraded_condition.py`. **Note**: This test is written in TDD style before T022 but requires T013 to be logically complete for execution.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `src/conditions/degraded.py` to configure WIA prediction horizon = 0 (or randomized prompt) and verify output contains no predictive context.
- [ ] T022 [US2] Create `src/conditions/run_degraded.py` to **load `data/raw/baseline_failures.json`** (output of T013) and **re-run the ALFWorld agent** with the **WIA prediction horizon set to 0** for each trajectory. **Do NOT** simply post-process text logs. Instead, re-execute the failure scenarios in the simulator with the WIA=0 configuration to generate the actual degraded failure logs. **Deliverable**: Save to `data/raw/degraded_failures.json` with keys: `id`, `original_id`, `failure_description`, `context_type` (WIA_ZERO). **Verification**: Ensure the file contains N entries (matching the input count) and all entries have the required keys. **Pre-requisite**: **T013** must be completed before T022 starts.
- [X] T023 [P] [US2] Integrate `src/retrieval/relevance_scorer.py` to calculate retrieval relevance scores for each degraded trajectory.
- [X] T024 [P] [US2] Aggregate results and save mean scores to `data/derived/degraded_stats.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Apply Syntactic Abstraction Intervention (Priority: P3)

**Goal**: Apply the rule-based "failure abstraction layer" to the Degraded cohort and measure recovery in retrieval relevance and task completion rates. **Note**: The "Intervention Cohort" is generated by applying the Syntactic Abstraction parser to the Degraded data, not by generating new LLM trajectories. This aligns with the Spec's definition of 'processing baseline trajectories'.

**Independent Test**: Run the intervention script and verify `data/derived/intervention_scores.json` shows measurable increase over degraded scores.

### Tests for User Story 3 (MANDATORY) ⚠️

- [X] T025 [P] [US3] Write contract test: Verify syntactic parser output schema in `tests/contract/test_syntactic_parser.py`.
- [X] T026 [P] [US3] Write integration test: Verify intervention recovery metrics in `tests/integration/test_intervention_condition.py`.

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `src/conditions/intervention.py` to load the rule-based parser.
- [X] T028 [US3] Implement `src/conditions/syntactic_parser.py` using `re` and `json` to extract patterns (e.g., "failed to pick up object X") from the **failure description field** (derived from the action log) in the Degraded cohort. **Note**: The parser operates on the `failure_description` field, not the raw action log directly, to align with the Spec's definition of 'failure event'.
- [ ] T029 [US3] Apply the parser to Degraded failure analyses (from T022) to generate **abstracted failure signals**. **Pre-requisite**: T022 must be completed before T029 starts.
- [ ] T029b [US3] Implement **mapping logic** in `src/retrieval/task_bank.py` to map the **abstracted failure signals** (from T029) to specific task definitions in the Frozen Task Bank. **Deliverable**: Save the resulting retrieved task definitions to `data/derived/retrieved_tasks.json` with keys: `abstracted_signal`, `task_id`, `task_definition`. **Verification**: Ensure the file contains N entries (matching the number of abstracted signals).
- [ ] T030 [US3] Re-calculate retrieval relevance scores using abstracted signals via `src/retrieval/relevance_scorer.py`.
- [ ] T032 [US3] Implement `run_reexecution(task_id, trajectory_id)` in `src/sim/alfworld_runner.py` to measure task completion rates. **Must use the task definition from `data/derived/retrieved_tasks.json` (T029b)** and inject it as the prompt for re-execution in the simulator. **Prompt Template**: `System: {abstracted_signal} User: {task_definition}`. Explicitly describe the injection mechanism: use the abstracted signal to construct the system prompt for the next N steps in the simulator. **Pre-requisite**: **T022** and **T029b** must be completed before T032 starts. **Verify the simulator return code and final state** to determine success/failure.
- [ ] T033a [US3] Implement **outcome verification** in `src/sim/alfworld_runner.py`. After re-execution (T032), check the simulator return code and final state to determine success/failure. Aggregate these results into a `task_completion_rate` metric. **Deliverable**: Save to `data/derived/intervention_completion_results.json` with keys: `trajectory_id`, `success` (bool), `completion_rate`.
- [X] T034 [P] [US3] Save intervention scores and completion rates to `data/derived/intervention_stats.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Statistical Analysis & Power Validation (Cross-Cutting)

**Purpose**: Perform statistical comparisons and power analysis as required by FR-007 and FR-008

- [ ] T036a [P] Implement `src/analysis/power_analysis.py` to perform **pre-experimental** power analysis for **N=1500 total** (500 per cohort) with target power ≥0.8. **Explicitly assume Cohen's d=0.5 and alpha=0.05**. Output `data/derived/power_analysis_report.json` justifying sample size. **Note**: This analysis is for the total N=1500, not a single dataset of 500.
- [ ] T036b [P] Implement `src/analysis/power_analysis.py` to perform the **final power calculation** using the actual generated N (1500). **If power < 0.8, flag the result** in `data/derived/power_calculation_log.json` with `status: FAILED` and `reason: power < 0.8`, but **DO NOT halt** the pipeline. **Deliverable**: Log power calculation details to `data/derived/power_calculation_log.json`. **Do NOT** implement a loop to increase N or proceed with insufficient power without a flag. **Pre-requisite**: This task **MUST** wait for US1, US2, and US3 data generation to be complete.
- [ ] T036c [P] Implement `src/analysis/report_generator.py` to generate the final **Power Analysis Report** (`data/derived/final_power_report.json`) if T036b detects a power shortfall, explicitly stating the constraint violation and the decision to proceed with N=500 (only if T036b is bypassed by human intervention, which is not allowed per T036b).
- [X] T037 [P] Implement `src/analysis/statistical_tests.py` with Shapiro-Wilk normality check.
- [X] T038 [P] Implement conditional logic in `src/analysis/statistical_tests.py`: IF p < 0.05 THEN Mann-Whitney U, ELSE t-test.
- [ ] T039 [P] Run statistical comparison across Baseline, Degraded, and Intervention groups. **Explicitly invoke pairwise comparisons** (Baseline vs. Degraded, Degraded vs. Intervention, Baseline vs. Intervention) using the selected test (t-test or Mann-Whitney U) defined in T037/T038. **Deliverable**: Save final statistical results to `data/derived/final_stats.csv` with columns: `comparison`, `test_type`, `p_value`, `effect_size`, `n1`, `n2`. **Pre-requisite**: This task **MUST** wait for **T036c** to confirm power validity (or flag the shortfall).
- [X] T040 [P] **REMOVED**: Logic merged into T039.

**Checkpoint**: At this point, all statistical analysis should be complete

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
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**. **T046 is the first blocking prerequisite for all data generation tasks.**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Statistical Analysis (Phase 6)**: Depends on completion of US1, US2, and US3 data generation
- **Data Robustness (Phase 2)**: Must be completed before any data generation tasks (T013, T022, T029) to ensure safe execution

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Consumes US1 output** (T013) for Degraded processing
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
- Statistical analysis tasks (T036-T039) can run in parallel once data is generated

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
- **Compute Constraints**: All LLM inference must be configured for CPU-only execution (**Llama-3-8B** **float32**).
- **Streaming**: Use `datasets.load_dataset(..., streaming=True)` for any large data processing to respect RAM limits.
- **Validation**: Every generated trajectory MUST be validated against ground-truth before saving; unvalidated ones must be discarded.
- **Cohorts**: Three independent cohorts (Baseline, Degraded, Intervention) must be generated sequentially: Baseline -> Degraded (process Baseline) -> Intervention (process Degraded).
- **Power Analysis**: N=1500 is a fixed target. If power < 0.8, flag the result and generate report; do not dynamically increase N.
- **Robustness**: T046-T052 are mandatory to ensure the pipeline does not silently succeed with invalid data or configurations.