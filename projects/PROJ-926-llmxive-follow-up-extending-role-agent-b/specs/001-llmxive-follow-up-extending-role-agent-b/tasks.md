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

- [X] T001 [P] Create project structure per `plan.md` by executing a Python script: `python -c "import os; [os.makedirs(p, exist_ok=True) for p in ['src/config', 'src/sim', 'src/retrieval', 'src/conditions', 'src/analysis', 'src/data/raw', 'src/data/derived', 'tests/contract', 'tests/integration', 'tests/unit', 'data/raw', 'data/derived', 'state', 'docs']]".` Ensure `src/`, `tests/`, `data/` directories exist.
- [X] T002 [P] Initialize Python project with `requirements.txt` containing pinned versions: `python==3.11`, `transformers==4.35.0`, `torch==2.1.0`, `scipy==1.11.0`, `datasets==2.14.0`, `alfworld==1.1.0`, `pandas==2.1.0`, `pytest==7.4.0`, `ruff==0.1.0`, `black==23.0.0`. **Note**: Model runs in single-precision floating-point format. `bitsandbytes` is removed to enforce Spec Assumptions.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with standard configs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **T007c is the first blocking prerequisite for all data generation tasks.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Implement `src/config/config.py` with pinned random seeds, paths, and ALFWorld hyperparameters. Define `SEED=42`, `DATA_PATH`, `MODEL_ID`.
- [X] T005 [P] Create `src/sim/alfworld_runner.py` to wrap the ALFWorld environment with deterministic state logging. Implement `run_episode(task_id, seed)` returning action log and state transitions.
- [X] T006 [P] Implement `src/sim/validation.py` to map agent actions to ground-truth state transitions. Define `validate_trajectory(action_log, ground_truth_log)` function.
- [X] T007c [P] [FR-002] Implement `src/sim/validation.py` to define the **specific validation mapping logic** (algorithm) that maps the *agent's failure description* to the *ground-truth state transition*. **Rule Definition**: "Select the first failure step in the trajectory where the agent's action deviates from the optimal path defined in the task bank (Spec Assumptions: Deterministic Priority Rule)." **Deliverable**: A function `define_validation_mapping()` in `src/sim/validation.py` that returns the logic configuration. **Note**: This is a config-only task; it defines the logic constant but does not apply it.
- [X] T007a [Sequential after T007c] [P] [FR-002] Implement `src/sim/validation.py` to **extract** ground-truth state transitions from the ALFWorld simulator's state transition log using the API method `simulator.get_state_log()` and save raw logs to `data/raw/ground_truth_raw.json` with checksumming. **Log Format**: JSON list of state transitions. **Crucially, do NOT apply the priority rule here; only extract raw logs.** Ensure logs are saved as a distinct artifact for 'Validation Independence'. **Dependency**: Requires T007c's logic definition to be present in the file, but does not execute it.
- [X] T007b [Sequential after T007a] [P] Implement `src/sim/validation.py` to **apply** the mapping logic defined in T007c to the raw logs from T007a and save the validated ground-truth mapping to `data/derived/ground_truth_validated.json`. Ensure strict separation from raw logs.
- [X] T007d [Sequential after T007b] [P] Create `specs/001-llmxive-followup/contracts/trajectory_schema.yaml` defining the exact JSON schema for trajectory outputs (keys: `id`, `failure_step`, `ground_truth_id`, `action_log`, `failure_description`). **Deliverable**: Valid YAML schema file. **Note**: This artifact is required for T011 (Contract Test).
- [X] T008 [P] Create `src/retrieval/task_bank.py` to load the frozen, human-annotated task bank (SQLite/JSON). Implement `get_task_definition(task_id)`.
- [X] T009 [P] Implement `src/config/cpu_config.yaml` with `CPU_DEVICE=true`, `MAX_RAM_GB=7`.
- [X] T010 [P] Implement data streaming utilities in `src/data/stream_utils.py` to handle large trajectory logs in chunks using `datasets.load_dataset(..., streaming=True)`.
- [X] T013b [P] [US1] Implement **Mock Data Generator** for unit testing ONLY. **Script Path**: `src/data/generate_mock.py`. **Command**: `python src/data/generate_mock.py --output data/raw/mock_failures.json --count 50 --seed 42`. **Logic**: Generate synthetic trajectories matching the schema in T007d (keys: `id`, `failure_step`, `ground_truth_id`, `action_log`, `failure_description`). **Constraint**: Each entry MUST have `is_mock=true`. **Verification**: After generation, run a validation script to ensure the JSON structure matches `specs/001-llmxive-followup/contracts/trajectory_schema.yaml`. **Deliverable**: `data/raw/mock_failures.json`. **Note**: This is for testing US2/US3 logic ONLY; it must be clearly marked as `is_mock=true` in the JSON.
- [X] T047 [P] [US1] Implement **ALFWorld environment health check** in `src/sim/alfworld_runner.py`. Before generating trajectories, run a single "dummy" episode using task_id: [a representative task] to verify the simulator is correctly installed and configured. If this fails, raise an exception.
- [X] T048 [P] [US1] Implement **strict ground-truth validation logging** in `src/sim/validation.py`. For every trajectory processed, log a detailed entry in `data/raw/validation_log.json` indicating: `trajectory_id`, `validation_status` (PASS/FAIL/AMBIGUOUS), `reason_code`, and `ground_truth_snapshot_id`.
- [X] T057 [P] Implement **CPU Memory Guardrails** in `src/config/cpu_config.py`. Add a runtime check that monitors RAM usage during trajectory generation and scoring.

---

## Phase 3: User Story 1 - Generate and Validate Baseline Failure Trajectories (Priority: P1) 🎯 MVP

**Goal**: Generate a dataset of at least 500 failed agent trajectories in ALFWorld using **Llama-3-8B-Instruct** (float32 only) and validate them against ground-truth.

**Independent Test**: Run the generation script and verify `data/raw/baseline_failures.json` contains ≥500 entries with valid IDs, failure steps, and linked ground-truth transitions.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [Sequential after T007d] [P] [US1] Write contract test: Verify output schema of `src/sim/generate_baseline.py` in `tests/contract/test_trajectory_schema.py`.
- [ ] T012 [P] [US1] Write integration test: Validate end-to-end generation of multiple failures in `tests/integration/test_baseline_generation.py`. **Constraint**: This test MUST run the actual `generate_baseline.py` script and verify `data/raw/baseline_failures.json`. Do NOT use mock data. <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T013 [Sequential after T007a, T007b, T007d, T047] [US1] [FR-001, FR-002] Implement `src/sim/generate_baseline.py` to load **`meta-llama/Llama-3-8B-Instruct`** with the following logic:
 1. **Verification**: Attempt to load the model in `float32` using `transformers.AutoModel.from_pretrained(..., torch_dtype=torch.float32)`.
 2. **Memory Check**: If load fails or `psutil.virtual_memory().available < 16GB`, calculate estimated RAM usage (`model_params * 4 bytes`). If < 7GB, raise a `MemoryError` with a clear message.
 3. **Fallback**: **DO NOT use 8-bit quantization.** If float32 fails, raise a `MemoryError` and halt. This enforces Spec Assumptions.
 4. **Generation Loop**: Run ALFWorld episodes to generate failures. Hard Cap Logic: If total attempts > `MAX_TOTAL_ATTEMPTS=1500` without reaching 500 valid failures, raise a `RuntimeError`. Ambiguity Handling: Exclude ambiguous trajectories and do not retry for that specific trajectory. Timeout/Retry Logic: Log errors, retry up to 3 times before skipping. Validate against ground-truth (T006).
 5. **Deliverable**: `data/raw/baseline_failures.json` containing ≥500 entries. Each entry MUST have keys: `trajectory_id`, `failure_step`, `ground_truth_id`, `action_log`, `failure_description`. **Command**: `python src/sim/generate_baseline.py`. **Note**: This task implements the 'Compute Feasibility' rule by enforcing float32 and halting on memory error rather than fabricating data.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3b: User Story 1 - Generate Degraded and Intervention Cohorts (Priority: P1)

**Goal**: Generate distinct datasets for the Degraded and Intervention cohorts as required by the Plan Summary (N=1500 total).

- [X] T013-degraded [Sequential after T007a, T007b, T007d, T047] [US1] [FR-001, FR-003] Implement `src/sim/generate_degraded.py` to load **`meta-llama/Llama-3-8B-Instruct`** with **WIA prediction horizon = 0**.
 1. **Logic**: Same as T013, but configure the agent prompt to disable predictive context (WIA=0).
 2. **Deliverable**: `data/raw/degraded_cohort_failures.json` containing ≥500 entries.
 3. **Command**: `python src/sim/generate_degraded.py`.
- [X] T013-intervention [Sequential after T007a, T007b, T007d, T047] [US1] [FR-001, FR-005] Implement `src/sim/generate_intervention.py` to load **`meta-llama/Llama-3-8B-Instruct`** with **WIA prediction horizon = 0** and **Syntactic Abstraction active**.
 1. **Logic**: Same as T013-degraded, but apply the rule-based parser during the failure analysis phase of generation.
 2. **Deliverable**: `data/raw/intervention_cohort_failures.json` containing ≥500 entries.
 3. **Command**: `python src/sim/generate_intervention.py`.

---

## Phase 4: User Story 2 - Execute Degraded World Model Condition (Priority: P2)

**Goal**: Simulate the "Degraded" condition by processing the **generated** degraded cohort trajectories and recording retrieval relevance scores.

**Independent Test**: Run the degraded script on the degraded cohort data and verify `data/derived/degraded_scores.json` contains scores consistent with failure modes.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T019 [P] [US2] Write contract test: Verify score calculation logic in `tests/contract/test_degraded_scoring.py`.
- [X] T020 [P] [US2] Write integration test: Verify degraded condition output in `tests/integration/test_degraded_condition.py`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `src/conditions/degraded.py` to configure WIA prediction horizon = 0.
- [X] T022a [Sequential after T013-degraded] [US2] [FR-003] Implement `src/conditions/run_degraded.py` to load `data/raw/degraded_cohort_failures.json`. **Constraint**: **Do NOT allow mock data.** If the file is missing, raise a `FileNotFoundError`. Validate schema against T007d. **Function**: `run_degraded_condition(input_path, output_path)`. **Command**: `python src/conditions/run_degraded.py`.
- [X] T022b [Sequential after T022a] [US2] Implement `src/conditions/run_degraded.py` to configure the WIA=0 environment for processing.
- [X] T022c [Sequential after T022b] [US2] Implement `src/conditions/run_degraded.py` to **process** the degraded cohort trajectories (from T013-degraded) and record retrieval relevance scores. **Constraint**: Do NOT generate new trajectories. Process in batches (BATCH_SIZE=50, MAX_BATCHES=10). Save to `data/raw/degraded_failures_processed.json`.
- [X] T022d [Sequential after T022c] [US2] Implement `src/conditions/run_degraded.py` to save the processing log and output.
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
- [X] T039 [Sequential after T013, T013-degraded, T013-intervention, T022c, T029, T049] [P] Run statistical comparison across Baseline, Degraded, and Intervention groups. **Dependency Note**: This task depends on data generation and the excluded log (T049), but NOT on the Power Analysis Report (T036).

**Checkpoint**: At this point, all statistical analysis should be complete

---

## Phase 7: Exclusion Handling & Logging

- [X] T049 [Sequential after T007b, T013, T013-degraded, T013-intervention, T022c, T029] [P] Aggregate all excluded trajectories (ambiguous, timeout, validation fail) from all cohorts into `data/raw/excluded_log.json`. Ensure this artifact is generated before T039 runs to ensure clean statistical inputs.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T041 [P] Documentation updates in `docs/` (README, quickstart.md).
- [X] T042 [P] Performance optimization for CPU-only execution.
- [X] T043 [P] Additional unit tests in `tests/unit/`.

---

## Phase 9: Revision - Addressing Data Integrity & Execution Constraints

**Purpose**: Address specific reviewer concerns regarding data sourcing, execution feasibility, and failure handling to ensure the project passes the fabrication gate and execution constraints.

### Implementation for Revision Concerns

- [X] T050 [Sequential after T002] [FR-008, FR-010] Implement **explicit ALFWorld dataset fetching** in `src/sim/alfworld_runner.py`. Replace any generic "download" logic with a specific function `fetch_alfworld_data()` that uses `datasets.load_dataset('alfworld/alfworld', split='train', streaming=True)`. **Constraint**: This task MUST define the exact source ID or URL to prevent "download from UCI" ambiguity. **Note**: This addresses the "Dataset-download tasks MUST name a real, reachable URL" rule. **Command**: `python src/sim/alfworld_runner.py --fetch-data`.
- [X] T054 [Sequential after T013, T013-degraded, T013-intervention] [FR-007, FR-008] Implement **Sample Size Justification** in `src/analysis/power_analysis.py`. Define `PowerInsufficientError` in `src/analysis/exceptions.py`. Add a function `calculate_required_n(effect_size=0.5, power=0.8)` and log the result to `data/derived/power_analysis_report.json`. **Constraint**: If the calculated `n` > 500 per group, the script must raise a `PowerInsufficientError` with the message "Power insufficient: achieved {p}, required {n}" and log the specific power achieved in `data/derived/power_analysis_report.json` with keys: `target_power`, `achieved_power`, `sample_size`, `error_raised`. **Note**: This addresses the "power analysis (target power ≥ 0.8)" requirement and ensures the sample size is statistically valid.
- [X] T055 [Sequential after T013, T013-degraded, T013-intervention] [FR-002, FR-011] Implement **Ambiguity Handling Logic** in `src/sim/validation.py`. Explicitly define the "Deterministic Priority Rule" for ambiguous cases (e.g., "If multiple failure steps exist, select the one with the lowest step ID; if tied, select the one with the highest semantic similarity to the task definition"). **Constraint**: This logic must be deterministic and logged for every ambiguous case. **Note**: This addresses the "ground-truth root cause is not influenced by the agent's internal predictions" rule.
- [X] T056 [Sequential after T007d, T007a] [P] [FR-002] Implement **Validation Independence Check** in `tests/unit/test_validation_independence.py`. Write a test that verifies the `ground_truth_id` in the output is derived *only* from the simulator log and *never* from the agent's text generation. **Constraint**: The test must fail if any dependency on the agent's text is found in the validation logic. **Note**: This ensures the "Validation Independence" principle is met.
- [X] T060 [Sequential after T002, T004, T013] [P] [FR-001] Implement **Execution Time Monitoring** in `src/config/config.py`. Add a `MAX_RUNTIME_HOURS=6` check that monitors the total runtime of the generation script. **Constraint**: If the runtime exceeds this limit, the script must save the current state to a checkpoint file and exit gracefully, allowing the execution stage to resume or re-run. **Note**: This addresses the "total compute time... constrained to... <6 hours" assumption.
