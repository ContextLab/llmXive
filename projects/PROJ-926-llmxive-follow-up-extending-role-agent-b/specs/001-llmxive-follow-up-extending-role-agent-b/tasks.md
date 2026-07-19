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
- [X] T002 [P] Initialize Python project with `requirements.txt` containing pinned versions: `python==3.11`, `transformers==4.35.0`, `torch==2.1.0`, `scipy==1.11.0`, `datasets==2.14.0`, `alfworld==1.1.0`, `pandas==2.1.0`, `pytest==7.4.0`, `ruff==0.1.0`, `black==23.0.0`. **Note**: Model runs in default precision (float32) for CPU compatibility as per Spec Assumptions.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with standard configs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **T007c is the first blocking prerequisite for all data generation tasks.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Implement `src/config/config.py` with pinned random seeds, paths, and ALFWorld hyperparameters. Define `SEED=42`, `DATA_PATH`, `MODEL_ID`.
- [X] T005 [P] Create `src/sim/alfworld_runner.py` to wrap the ALFWorld environment with deterministic state logging. Implement `run_episode(task_id, seed)` returning action log and state transitions.
- [X] T006 [P] Implement `src/sim/validation.py` to map agent actions to ground-truth state transitions. Define `validate_trajectory(action_log, ground_truth_log)` function.
- [X] T007c [Sequential after T004] [P] [FR-002] Implement `src/sim/validation.py` to define the **specific validation mapping logic** (algorithm) that maps the *agent's failure description* to the *ground-truth state transition*. **Rule Definition**: "Select the first failure step in the trajectory where the agent's action deviates from the optimal path defined in the task bank (Spec Assumptions: Deterministic Priority Rule)." **Deliverable**: A function `define_validation_mapping()` in `src/sim/validation.py` that returns the logic configuration.
- [X] T007a [Sequential after T007c] [P] [FR-002] Implement `src/sim/validation.py` to **extract** ground-truth state transitions from the ALFWorld simulator's state transition log using a specific API method and save raw logs to `data/raw/ground_truth_raw.json` with checksumming. **Log Format**: JSON list of state transitions. **Crucially, do NOT apply the priority rule here; only extract raw logs.** Ensure logs are saved as a distinct artifact for 'Validation Independence'.
- [X] T007b [Sequential after T007a] [P] Implement `src/sim/validation.py` to **apply** the mapping logic defined in T007c to the raw logs from T007a and save the validated ground-truth mapping to `data/derived/ground_truth_validated.json`. Ensure strict separation from raw logs.
- [X] T007d [Sequential after T007b] [P] Create `specs/001-llmxive-followup/contracts/trajectory_schema.yaml` defining the exact JSON schema for trajectory outputs (keys: `id`, `failure_step`, `ground_truth_id`, `action_log`, `failure_description`). **Deliverable**: Valid YAML schema file. **Note**: This artifact is required for T011 (Contract Test).
- [X] T008 [P] Create `src/retrieval/task_bank.py` to load the frozen, human-annotated task bank (SQLite/JSON). Implement `get_task_definition(task_id)`.
- [X] T009 [P] Implement `src/config/cpu_config.yaml` with `CPU_DEVICE=true`, `MAX_RAM_GB=7`.
- [X] T010 [P] Implement data streaming utilities in `src/data/stream_utils.py` to handle large trajectory logs in chunks using `datasets.load_dataset(..., streaming=True)`.
- [X] T046 [Sequential after T002, T004] [P] [US1] Implement **real data source verification** in `src/sim/trajectory_generator.py`. Explicitly verify that the **`meta-llama/Llama-3-8B`** model is accessible via Hugging Face `transformers` and can be loaded in default precision (float32) on 7GB RAM before generation starts.  If the model cannot be loaded, the script MUST raise the exception and exit immediately. **Do NOT** implement a fallback to a smaller model or synthetic data. **Deliverable**: Write a verification log to `data/raw/model_verification_log.json` with keys: `model_id`, `status` (SUCCESS/FAILED), `error_message` (if failed).  **Note**: This is a constitutional requirement and FR-002; the 'CPU-only' constraint refers to the execution environment, not model loading ability.
- [X] T047 [P] [US1] Implement **ALFWorld environment health check** in `src/sim/alfworld_runner.py`. Before generating trajectories, run a single "dummy" episode using task_id: [a representative task] to verify the simulator is correctly installed and configured. If this fails, raise an exception.
- [X] T048 [P] [US1] Implement **strict ground-truth validation logging** in `src/sim/validation.py`. For every trajectory processed, log a detailed entry in `data/raw/validation_log.json` indicating: `trajectory_id`, `validation_status` (PASS/FAIL/AMBIGUOUS), `reason_code`, and `ground_truth_snapshot_id`.
- [X] T057 [P] Implement **CPU Memory Guardrails** in `src/config/cpu_config.py`. Add a runtime check that monitors RAM usage during trajectory generation and scoring.

---

## Phase 3: User Story 1 - Generate and Validate Baseline Failure Trajectories (Priority: P1) 🎯 MVP

**Goal**: Generate a dataset of at least 500 failed agent trajectories in ALFWorld using **Llama-3-8B** (default precision, CPU mode) and validate them against ground-truth.

**Independent Test**: Run the generation script and verify `data/raw/baseline_failures.json` contains ≥500 entries with valid IDs, failure steps, and linked ground-truth transitions.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [Sequential after T007d] [P] [US1] Write contract test: Verify output schema of `src/sim/trajectory_generator.py` in `tests/contract/test_trajectory_schema.py`.
- [X] T012 [P] [US1] Write integration test: Validate end-to-end generation of 500 failures in `tests/integration/test_baseline_generation.py`.

### Implementation for User Story 1

- [X] T013 [Sequential after T046, T007a, T007b, T007d] [US1] [FR-002] Implement `src/sim/trajectory_generator.py` to load **`meta-llama/Llama-3-8B`** (default precision, float32) and load task definitions from Frozen Task Bank (T008).  Implement generation loop: Run ALFWorld episodes to generate failures. Hard Cap Logic: If total attempts > `MAX_TOTAL_ATTEMPTS=1500` without reaching 500 valid failures, raise a `RuntimeError`. Ambiguity Handling: Exclude ambiguous trajectories and do not retry for that specific trajectory. Timeout/Retry Logic: Log errors, retry up to 3 times before skipping.  Validate against ground-truth (T006). Deliverable: `data/raw/baseline_failures.json` containing ≥500 entries.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 4: User Story 2 - Execute Degraded World Model Condition (Priority: P2)

**Goal**: Simulate the "Degraded" condition (WIA horizon=0) by **re-running the ALFWorld agent** with the WIA prediction horizon set to 0 on the baseline failure trajectories and recording retrieval relevance scores.

**Independent Test**: Run the degraded script on P1 data and verify `data/derived/degraded_scores.json` contains scores consistent with failure modes.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T019 [P] [US2] Write contract test: Verify score calculation logic in `tests/contract/test_degraded_scoring.py`.
- [X] T020 [P] [US2] Write integration test: Verify degraded condition output in `tests/integration/test_degraded_condition.py`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `src/conditions/degraded.py` to configure WIA prediction horizon = 0.
- [X] T022a [Sequential after T013] [US2] Implement `src/conditions/run_degraded.py` to load `data/raw/baseline_failures.json`.
- [X] T022b [Sequential after T022a] [US2] Implement `src/conditions/run_degraded.py` to configure the WIA=0 environment.
- [X] T022c [Sequential after T022b] [US2] Implement `src/conditions/run_degraded.py` to execute the re-simulation loop with batch limits (BATCH_SIZE=50, MAX_BATCHES=10). Save to `data/raw/degraded_failures.json`.
- [X] T023 [P] [US2] Integrate `src/retrieval/relevance_scorer.py` to calculate retrieval relevance scores for each degraded trajectory.
- [X] T024 [P] [US2] Aggregate results and save mean scores to `data/derived/degraded_stats.json`.

**Checkpoint**: At this point, User Story 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Apply Syntactic Abstraction Intervention (Priority: P3)

**Goal**: Apply the rule-based "failure abstraction layer" to the Degraded cohort and measure recovery in retrieval relevance and task completion rates.

**Independent Test**: Run the intervention script and verify `data/derived/intervention_scores.json` shows measurable increase over degraded scores.

### Tests for User Story 3 (MANDATORY) ⚠️

- [X] T025 [P] [US3] Write contract test: Verify syntactic parser output schema in `tests/contract/test_syntactic_parser.py`.
- [X] T026 [P] [US3] Write integration test: Verify intervention recovery metrics in `tests/integration/test_intervention_condition.py`.

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `src/conditions/intervention.py` to load the rule-based parser.
- [X] T028 [P] [US3] Implement `src/conditions/syntactic_parser.py` using `re` and `json`.
- [X] T029 [Sequential after T022c] [US3] Apply the parser to Degraded failure analyses (from T022c) to generate abstracted failure signals.
- [X] T030 [US3] Re-calculate retrieval relevance scores using abstracted signals via `src/retrieval/relevance_scorer.py`.
- [X] T032 [Sequential after T029] [US3] Implement re-execution logic in `src/sim/alfworld_runner.py`.
- [X] T033a [US3] Implement outcome verification in `src/sim/alfworld_runner.py`.
- [X] T033b [Sequential after T033a] [US3] Aggregate task completion rates and compute recovery rate.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Statistical Analysis & Power Validation (Cross-Cutting)

- [X] T036 [P] Implement `src/analysis/power_analysis.py` to perform post-hoc power analysis for N=1500. Check if achieved power ≥ 0.8. Log results to `data/derived/power_analysis_report.json`. **Do NOT halt execution if power < 0.8**; log as a warning for the final paper discussion.
- [X] T037 [P] Implement `src/analysis/statistical_tests.py` with Shapiro-Wilk normality check.
- [X] T038 [P] Implement conditional logic in `src/analysis/statistical_tests.py` to select Mann-Whitney U or t-test based on Shapiro-Wilk p-value.
- [X] T039 [Sequential after T013, T022c, T029, T049] [P] Run statistical comparison across Baseline, Degraded, and Intervention groups. **Dependency Note**: This task depends on data generation and the excluded log (T049), but NOT on the Power Analysis Report (T036).

**Checkpoint**: At this point, all statistical analysis should be complete

---

## Phase 7: Exclusion Handling & Logging

- [X] T049 [Sequential after T007b, T013, T022c, T029] [P] Aggregate all excluded trajectories (ambiguous, timeout, validation fail) from all cohorts into `data/raw/excluded_log.json`. Ensure this artifact is generated before T039 runs to ensure clean statistical inputs.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T041 [P] Documentation updates in `docs/` (README, quickstart.md).
- [X] T042 [P] Performance optimization for CPU-only execution.
- [X] T043 [P] Additional unit tests in `tests/unit/`.