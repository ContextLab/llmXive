# Tasks: llmXive follow-up: extending "Beyond the Current Observation: Evaluating Multimodal Large Language M"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-beyond-the-c/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are INCLUDED as they are critical for validating the scientific methodology and data hygiene requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c/`
- **Source**: `code/`, `utils/`
- **Tests**: `tests/`
- **Data**: `data/`

---

## Phase 1: Setup (Shared Infrastructure & Utilities)

**Purpose**: Project initialization and core utility implementation.
**Note**: Utility scripts (checksum, hasher, validator) are implemented here as code artifacts. Their *execution* on data occurs later.

- [X] T001a [P] Re-create project directory structure in `projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c/`: Create directories `code/`, `utils/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/integration/`, `docs/`, `results/`, `config/`, `specs/contracts/`. Create `code/__init__.py`.
- [X] T001b [P] Create and pin `projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c/requirements.txt` with **exact pinned versions**: `transformers==4.40.0`, `bitsandbytes==0.43.1`, `scikit-learn==1.5.0`, `sentence-transformers==3.0.1`, `numpy==1.26.4`, `pandas==2.2.2`, `pytest==8.2.0`, `pyyaml==6.0.1`, `datasets==2.19.1`, `sentencepiece==0.2.0`, `memory-profiler==0.61.0`, `llama-cpp-python==0.2.91`. **Verification**: Run `pip install -r requirements.txt` and verify all packages install without error. **Artifact**: `requirements.txt` with full content. **Note**: Merged with original T002 to ensure reproducibility (Constitution Principle I).
- [X] T002 [X] **REMOVED**: Merged into T001b. **Note**: ID T002 is retired.
- [X] T003a [P] Create `pyproject.toml` in project root with configuration for `black` and `ruff` (rules: E, F, W, I, N).
- [X] T003b [P] Run initial lint/format check on empty codebase to verify tool configuration. **Execute command**: `ruff check. > results/lint_report.txt`. **Verification**: Exit code must be 0 or 1 (warnings/errors allowed). **Artifact**: `results/lint_report.txt` must exist with the logged output.
- [X] T004a [P] Implement `utils/checksum.py` core logic to generate SHA-256 checksums for `data/processed/` (Constitution Principle III). **Verification**: Run `python utils/checksum.py --input data/processed/ --output state/checksums.yaml` on **mock data**. **Artifact**: `state/checksums.yaml`.
- [X] T004b [P] Add CLI interface and error handling to `utils/checksum.py`. **Verification**: Run `python utils/checksum.py --help` and verify CLI arguments. **Artifact**: `utils/checksum.py` with full CLI support. **Depends on T004a**. **Note**: Use mock data for verification.
- [X] T005a [P] Implement `utils/hasher.py` core logic to generate version hashes for artifacts (Constitution Principle V). **Verification**: Run `python utils/hasher.py --input data/processed/ --output state/artifact_hashes.yaml` on **mock data**. **Artifact**: `state/artifact_hashes.yaml`.
- [X] T005b [P] Add CLI interface and error handling to `utils/hasher.py`. **Verification**: Run `python utils/hasher.py --help` and verify CLI arguments. **Artifact**: `utils/hasher.py` with full CLI support. **Depends on T005a**. **Note**: Use mock data for verification.
- [X] T006a [P] Implement `utils/renderer_validator.py` core logic to verify ASCII vs Visual ground truth consistency (SC-005). **Verification**: Run `python utils/renderer_validator.py --input data/processed/seeds_*.ascii --visual-input data/processed/seeds_*.png --output results/validation_report.json` on **mock data**. **Artifact**: `results/validation_report.json`.
- [X] T006b [P] Add CLI interface and error handling to `utils/renderer_validator.py`. **Verification**: Run `python utils/renderer_validator.py --help` and verify CLI arguments. **Artifact**: `utils/renderer_validator.py` with full CLI support. **Depends on T006a**. **Note**: Use mock data for verification.
- [X] T007 [P] Create base `code/__init__.py` and data model contracts in `specs/contracts/`:
  - **`state_snapshot.schema.yaml`** content:
    ```yaml
    type: object
    required:
      - ascii_grid
      - event_log
      - ground_truth_state
      - masked_ground_truth
    properties:
      ascii_grid:
        type: string
      event_log:
        type: array
        items:
          type: object
      ground_truth_state:
        type: object
      masked_ground_truth:
        type: object
    ```
  - **`metric_result.schema.yaml`** content:
    ```yaml
    type: object
    required:
      - memory_gap_score
      - p_value
      - confidence_interval
      - run_id
    properties:
      memory_gap_score:
        type: number
      p_value:
        type: number
      confidence_interval:
        type: array
        items:
          type: number
      run_id:
        type: string
    ```
  - **Verification**: Run `pytest tests/unit/test_schemas.py` (to be created) to validate schema files exist and are valid YAML. **Artifact**: `specs/contracts/state_snapshot.schema.yaml`, `specs/contracts/metric_result.schema.yaml`.
- [X] T008 [P] Implement `code/logger.py` with JSON-formatted rotating file handler (`max_bytes=10MB`, `backupCount=5`) and configure `code/main.py` to use it for all stdout/stderr redirection.
- [X] T009 [P] Create `config/seeds.yaml` containing a **pinned list of integers** for reproducibility (Pilot Phase). Implement `code/config_loader.py` to load this file and export a global `SEEDS` list. **Note**: These seeds are for the Pilot phase; full set determined by Power Analysis (T039c-1).

**Checkpoint**: Setup and Utilities ready. **Blocking**: Phase 3 tasks depend on T004b, T005b, T006b verification passing.

---

## Phase 2: Foundational Design (Blocking Prerequisites)

**Purpose**: Design tasks and test definitions that block implementation.

- [X] T017 [P] [US3 Design] Design test cases for "Hidden State Masking" logic in `tests/unit/test_hidden_masking.py` (define inputs: masked state, outputs: pass/fail, expected behavior based on Spec FR-007). **Depends on T007 contracts.**
- [X] T036 [P] [US3 Test] Implement unit test for Hidden State Masking in `tests/unit/test_hidden_masking.py` (verify visible items excluded). **Depends on T017 design and T007 contracts.**

**Checkpoint**: Design ready - implementation can now begin.

---

## Phase 3: User Story 1 & 2 Implementation (Data Generation)

**Goal**: Implement Renderer (US1), Agent (US2), and Baseline (US2) to generate data for scoring.

### Implementation for User Story 1 (Renderer)

- [X] T014 [P] [US1] Implement `code/renderer.py` to convert RNG-Bench visual state to ASCII grid string.
- [X] T015 [P] [US1] Implement `code/renderer.py` to generate JSON event logs for every time step (FR-001).
- [X] T015b [US1] **Execution**: Run `code/renderer.py` on seeds from `config/seeds.yaml` to generate ASCII grids and JSON logs in `data/processed/`. **Command**: `python code/renderer.py --seeds config/seeds.yaml --output data/processed/`. **Artifact**: `data/processed/seeds_*.ascii`, `data/processed/seeds_*.json`. **Depends on T014, T015.**
- [X] T015c [US1] **Execution**: Run `code/renderer.py` (or a dedicated visual extractor) on seeds from `config/seeds.yaml` to generate **Visual Frames** (raw images) in `data/processed/`. **Command**: `python code/renderer.py --seeds config/seeds.yaml --output data/processed/ --mode visual`. **Artifact**: `data/processed/seeds_*.png`. **Depends on T014.**
- [X] T016 [US1] Implement validation for out-of-bounds states in `code/renderer.py`: MUST output the standardized error block `ERROR: STATE_CORRUPT` for corrupted states (US-1 Acceptance Scenario 3). **Include a verification step to ensure the string matches exactly.**
- [X] T016b [US1] Unit test for out-of-bounds state validation in `tests/unit/test_renderer.py` (verify `ERROR: STATE_CORRUPT` output).
- [X] T021 [P] [US1] Integration test for full renderer pipeline in `tests/integration/test_full_loop.py` (verify ASCII consistency). **Note: Uses `utils/renderer_validator.py` (T006b).** **Depends on T006b**.
- [X] T022 [US1] **BLOCKING**: Execute `utils/renderer_validator.py` on generated `data/processed/seeds_*.ascii` and `data/processed/seeds_*.png` files to generate `results/validation_report.json` ensuring Levenshtein distance = 0 (SC-005). **Data cannot be used in subsequent phases until this task passes.** **Depends on T015b, T015c, T016b, T021, T006b**. **COMMAND**: `python utils/renderer_validator.py --input data/processed/seeds_*.ascii --visual-input data/processed/seeds_*.png --output results/validation_report.json`. **Verification**: `results/validation_report.json` must exist with `status: PASS` AND `levenshtein_distance == 0`. **Note: This task validates RENDERER FIDELITY (ASCII vs Visual) ONLY, not the Memory Gap metric.** **Fail if `utils/renderer_validator.py` is missing.**

### Implementation for User Story 2 (Text Agent)

- [X] T023 [P] [US2] Implement `code/agent_loop.py` to load quantized text-only LLM (≤3B params) using CPU-optimized engine (FR-002).
- [X] T024 [US2] Implement `code/agent_loop.py` inference cycle: receive ASCII/Log, output JSON action + updated mental map (FR-003). **Implementation Details**: Include **context window management** (sliding window/truncation: 'Keep last events; if overflow, discard oldest [deferred] of history to maintain [deferred] context'), **hard step limit** (steps), and **error handling** (NaN, OOM) as integral parts of this task. **Output Schema**: `{"action": "move_up|move_down|move_left|move_right|wait", "mental_map": "string"}`. **Artifact**: `data/processed/agent_run_<seed>.json`. **Depends on T023.**
- [X] T025 [US2] **Verification**: Verify context window truncation logic in `code/agent_loop.py` (keep last N=50 events). **Test**: Run a synthetic long-log input and verify the oldest events are dropped. **Artifact**: `results/context_truncation_test.log`. **Depends on T024.**
- [X] T026 [US2] **Verification**: Verify hard step limit logic in `code/agent_loop.py` (limit a configurable maximum number of steps). **Test**: Run a synthetic infinite-loop scenario and verify the run is marked "timeout" and logged to `results/discarded_runs.csv`. **Artifact**: `results/step_limit_test.log`. **Depends on T024.**
- [X] T027 [US2] **Verification**: Verify error handling logic in `code/agent_loop.py` (NaN, OOM). **Test**: Inject NaN into output tensor and verify the run is discarded and logged to `results/discarded_runs.csv`. **Artifact**: `results/error_handling_test.log`. **Depends on T024.**
- [X] T028 [US2] Implement `code/resource_monitor.py` to log peak RAM and CPU usage to `results/resource_profile.json` after every agent run (Constitution Principle VII). **Output Schema**: `{"peak_ram_mb": float, `cpu_percent`: float, `run_id`: string}`. **Frequency**: Log at regular, periodic intervals. **Verification**: Assert `peak_ram_mb <= 7168` and `cpu_percent <= 200`. **Depends on T024.**
- [X] T028b [US2] **Verification**: Verify Text Agent memory footprint <= 7GB RAM using `memory_profiler` before finalizing the runner. **Command**: `python -m memory_profiler code/agent_loop.py --seed 1`. **Artifact**: `results/memory_profile_text.txt`. **Constraint**: If model > 7GB, select a smaller quantized model. **Depends on T024.**

### Implementation for User Story 2 (Baseline Agent)

- [X] T039a [P] [US2] Implement `code/baseline_runner.py` to load a Vision-capable MLLM (e.g., `Qwen-VL-Chat-Int4`), process Visual inputs (raw frames), manage context, and output structured JSON mental maps. **Implements Plan Override of FR-008.** **Output Schema**: `{"action": "string", "mental_map": "string"}`. **Artifact**: `data/processed/baseline_seeds_*.json`. **Verification**: Confirm output is compared against the *same masked ground truth* as the Text Agent. **Depends on T015c (Visual Frames).**
  - [X] T039a-1 [P] Verify baseline model memory footprint <= 7GB RAM using `memory_profiler` before finalizing the runner. **Command**: `python -m memory_profiler code/baseline_runner.py --seed 1`. **Artifact**: `results/memory_profile_baseline.txt`. **Constraint**: If model > 7GB, select a smaller quantized model (e.g., Qwen-VL-Chat-Int4). **Depends on T039a-3 (Adapter Implementation Complete)**.
  - [X] T039a-2 [P] Verify Baseline's output is compared against the *same masked ground truth* as the Text Agent (Plan Decision). **Verification**: Run a mock comparison with `tests/unit/test_hidden_masking.py` logic on baseline output. **Input**: `tests/fixtures/mock_baseline_output.json`. **Assertion**: Verify masked ground truth logic is identical to Text Agent. **Artifact**: `results/baseline_masking_verification.json`. **Depends on T039a-3 (Adapter Implementation Complete) AND T035 (Scorer Masking Logic Complete).**
  - [X] T039a-3 [P] Implement `code/baseline_adapter.py` to parse Baseline MLLM (Visual) output into structured JSON mental map. **Parsing Logic**: Extract `action` and `mental_map` fields from JSON. **Target Schema**: Matches `state_snapshot.schema.yaml`. **Validation**: Confirm output matches the masked ground-truth format used by the Text Agent. **Depends on T007**.
  - [X] T039a-4 [P] Verify Data Hygiene and Versioning logic in `baseline_adapter.py` and `baseline_runner.py`. **Verification**: Run `utils/checksum.py` and `utils/hasher.py` on baseline output files. **Artifact**: `state/checksums.yaml`, `state/artifact_hashes.yaml`. **Depends on T039a-3, T004b, T005b**.
  - [X] T039a-5 [P] Verify Kickback Ratification Status. **Verification**: Check if T033b (Spec Update) is complete. **Artifact**: `results/kickback_status.json`. **Depends on T033b**.
- [ ] T039b [US2] Execute `code/baseline_runner.py` on seeds from `config/seeds.yaml` to generate baseline logs in `data/processed/`. **Command**: `python code/baseline_runner.py --seeds config/seeds.yaml --output data/processed/baseline_seeds_*.json`. **Depends on T039a (ALL sub-tasks complete) AND T022 (Data Validation) AND T015c AND T039a-5.**

### Performance Verification (Blocking)

- [X] T041a [US2] Implement `code/benchmark_runner.py` to orchestrate the execution of N=20 game instances for the Text Agent. **Artifact**: `code/benchmark_runner.py`. **Depends on T023-T028.**
- [X] T041 [US2] Execute `code/benchmark_runner.py` on seeds from `config/seeds.yaml` to generate `results/benchmark_log.json`. **Command**: `python code/benchmark_runner.py --seeds config/seeds.yaml --output results/benchmark_log.json`. **Verification**: `results/benchmark_log.json` must exist with `total_time_hours < 6.0` and `passed: true`. **Depends on T041a, T023-T028, T015b.**

**Checkpoint**: All data generation (US1, US2, Baseline) complete.

---

## Phase 4: User Story 3 Implementation (Scoring & Statistics)

**Goal**: Implement Scorer (US3) and Statistical Analysis.

### Tests for User Story 3 ⚠️
- [X] T030 [P] [US3] Unit test for Structured JSON comparison in `tests/unit/test_scorer.py`.
- [X] T031 [P] [US3] Unit test for Mann-Whitney U test in `tests/unit/test_stats.py`.
- [X] T032 [P] [US3] Integration test for full scoring pipeline in `tests/integration/test_full_loop.py`.

### Implementation for User Story 3

- [X] T033a [P] [US3] **Kickback Submission**: Submit the Spec Kickback for FR-006 and FR-008 overrides. **Action**: Create a formal Kickback request in `docs/kickbacks/` detailing the Plan Override (Structured Metric, Visual Baseline). **Artifact**: `docs/kickbacks/001-metric-baseline-override.md`. **Verification**: Kickback must be **SUBMITTED** (status: submitted). **Depends on T007, T030, T031**.
- [X] T033b [P] [US3] **Spec Update**: Update `spec.md` to formally ratify the "Structured JSON Comparison + Semantic Similarity" metric (Plan Override of FR-006) and the Baseline Visual Input strategy (Plan Override of FR-008). **Content**: Add section "Metric Definition: Structured JSON + Semantic Similarity" and update FR-008/FR-006. **Specific Edits**:
  - Replace FR-008 with: "System MUST re-run the baseline MLLM on the exact same **Visual inputs** (raw frames) generated from the same RNG-Bench seeds as the text-only agent. The 'Memory Gap' metric MUST be calculated on the **same masked ground truth state** for both agents to ensure a valid comparison of modality impact."
  - Replace FR-006 with: "System MUST calculate the 'Memory Gap' as the sum of: (1) a Structured JSON comparison score (exact match + semantic similarity) between the agent's recalled state and the ground-truth state, and (2) a penalty of 1.0 for every critical item present in the hidden ground truth but missing from the agent's mental map."
  - **Verification**: Ensure the Spec update is completed and ratified. **Depends on T033a (Submitted)**.
- [X] T033c [P] [US3] **Verify Kickback Ratification**: Check if T033b (Spec Update) is complete. **Artifact**: `results/kickback_status.json`. **Depends on T033b**.
- [X] T033d [US3] Implement `code/scorer.py` to calculate "Memory Gap" using Structured JSON comparison + Semantic Similarity (Plan Override of FR-006). **Library**: `sentence-transformers/all-MiniLM-L6-v2`. **Formula**: `score = (1 - semantic_similarity) + (1.0 * missing_items)`. **Threshold**: If `semantic_similarity < 0.5`, treat as 0.0 for penalty calculation. **Verification**: Include a step to confirm the new metric satisfies the *intent* of FR-006 (measuring state retention) and explicitly tags the deviation as 'Plan Override' in the code comments and logs. **Depends on T007, T033c (Ratified), T030**.
  - [X] **Verification**: Run `tests/unit/test_scorer.py` to validate the new metric.
- [X] T035 [US3] Implement `code/scorer.py` logic to apply a penalty for missing critical items in hidden ground truth (FR-007). **Penalty**: A significant penalty per critical item (key, door) missing from agent's mental map. **Logic**: Identify critical items in `masked_ground_truth` and compare with `agent_mental_map`. **Verify masking logic is applied to Baseline agent comparison**. (Depends on T007 contract). **Depends on T033d**.
- [X] T037 [US3] Implement `code/stats.py` to perform one-tailed Mann-Whitney U test (FR-005). **Depends on T031**.
- [X] T038a [P] [US3] Implement `code/main.py` orchestration logic: orchestrate Text Agent and Baseline runs, aggregate results into `results/statistical_summary.json`, and trigger `utils/checksum.py` on `data/processed/`. 
  - **Input Schema**: List of run IDs, paths to agent/baseline logs.
  - **Aggregation Logic**: 
    1. Load all `agent_run_*.json` and `baseline_run_*.json` from `data/processed/`.
    2. Extract `memory_gap_score` from each run.
    3. Compute mean, std, and confidence interval for Text and Baseline groups.
    4. Perform Mann-Whitney U test (one-tailed) on the two distributions.
    5. Write `results/statistical_summary.json` with keys: `text_mean`, `text_std`, `baseline_mean`, `baseline_std`, `p_value`, `conclusion`, `n_runs`.
  - **Output Schema**: `{"text_mean": float, "text_std": float, "baseline_mean": float, "baseline_std": float, "p_value": float, "conclusion": "string", "n_runs": int}`.
  - **Verification**: Include a step to confirm the aggregation logic is deterministic and matches expected schema. **Depends on T033d, T035, T037, T039a-1, T039a-2, T039a-3, T039a-4, T033c (Ratified)**. **Fail if `code/main.py` is missing or contains only placeholders.**
- [X] T038c [P] [US3] Implement `code/main.py` checksum trigger: trigger `utils/checksum.py` on `data/processed/`. **Command**: `python utils/checksum.py --input data/processed/ --output state/checksums.yaml`. **Verification**: Ensure checksums are generated correctly. **Depends on T038a, T004b**.

**Checkpoint**: Scoring and Statistics implementation complete.

---

## Phase 5: Execution, Finalization & Polish

**Purpose**: Run final experiments, finalize artifacts, and validate.

- [ ] T039c [US3] Execute full experiment batch (Text Agent + Baseline) for **N=20** (Pilot) and generate `results/statistical_summary.json`. **Command**: `python code/main.py --mode pilot --seeds 1..20`. **Depends on T041 pass, T039a (ALL sub-tasks complete), T038a, T038c**.
- [ ] T039c-1 [US3] Perform Power Analysis on Pilot results. **Method**: G*Power (effect size calculation). **Input**: `results/statistical_summary.json`. **Artifact**: `results/power_analysis_report.json`. **Depends on T039c**.
- [ ] T039d [US3] **Conditional**: If Power Analysis requires scaling (power < 0.8), execute full experiment batch for **N=64** and update `results/statistical_summary.json`. **Command**: `python code/main.py --mode full --seeds 1..64`. **Depends on T039c-1 (Decision Gate)**.
- [ ] T040a [P] Documentation: Update `docs/methodology.md` with the Structured Metric definition and Baseline Visual Input strategy. **Content**: Add sections "Metric: Structured JSON + Semantic Similarity" and "Baseline: Visual Input Strategy".
- [ ] T040b [P] Documentation: Update `docs/quickstart.md` with exact execution commands. **Commands**: `python code/main.py --mode pilot`, `python code/main.py --mode full`.
- [ ] T040c [P] Documentation: Update `docs/api.md` with new module signatures. **Modules**: `code/renderer.py`, `code/agent_loop.py`, `code/scorer.py`, `code/stats.py`.
- [ ] T042a [P] Add edge case tests for `code/stats.py` Mann-Whitney edge cases in `tests/unit/test_stats.py`: **empty input**, **single sample**, **identical values**. **Test Names**: `test_mann_whitney_empty`, `test_mann_whitney_single`, `test_mann_whitney_identical`.
- [ ] T042b [P] Add integration tests for full loop in `tests/integration/test_full_loop.py`. **Test Name**: `test_full_loop_integration`. **Input**: `data/processed/seeds_1.ascii`. **Expected**: `results/statistical_summary.json` generated.
- [ ] T043 [Phase 5] Run `utils/checksum.py` on `data/processed/` and update `state/...yaml`. **Command**: `python utils/checksum.py --input data/processed/ --output state/checksums.yaml`. **Depends on T039c/T039d, T004b**.
- [ ] T046 [Phase 5] Run `utils/hasher.py` to finalize artifact versions (Constitution V). **Command**: `python utils/hasher.py --input data/processed/ --output state/artifact_hashes.yaml`. **Depends on T039c/T039d and T043, T005b**. **Serial final step**.
- [ ] T044 [Phase 5] Execute all commands in `docs/quickstart.md` in a fresh virtualenv and verify exit code 0 for all steps, logging output to `results/quickstart_validation.log`. **Command**: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python code/main.py --mode pilot`.

**Checkpoint**: Project complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational Design (Phase 2)**: Depends on Setup - BLOCKS implementation
- **Implementation (Phase 3)**: Depends on Design - Generates Data
- **Scoring (Phase 4)**: Depends on Data Generation (Phase 3) AND Kickback Submission (T033a) AND Spec Update (T033b) - Calculates Metrics
- **Finalization (Phase 5)**: Depends on Scoring - Hashes & Validates

### User Story Dependencies

- **User Story 1 (P1)**: Phase 3 (T014-T022)
- **User Story 2 (P2)**: Phase 3 (T023-T039b, T041, T041b)
- **User Story 3 (P3)**: Phase 4 (T033-T038), Phase 5 (T039c, T039d)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Design phase completes, US1, US2 (Text), US2 (Baseline) can start in parallel
- All tests for a user story marked [P] can run in parallel

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: All data files in `data/processed/` MUST have checksums generated before use (T043).
- **Modality Isolation**: Ensure Baseline runs on Visual inputs and Text Agent runs on ASCII inputs (Plan Override of FR-008).
- **Metric Validity**: Ensure "Memory Gap" uses Structured JSON comparison, not raw Levenshtein distance (Plan Override of FR-006).
- **Serial Final Step**: T046 is a serial final step dependent on all data generation and scoring tasks.
- **Validation Blocking**: T022 must pass before any Phase 4 tasks (Scoring) can execute.
- **Kickback Process**: T033a (Kickback Submission) must be completed and **RATIFIED** (T033b) before T033d (Scorer) and T039a (Baseline) can proceed.
- **Blocking Verification**: Phase 3 tasks (T015b, T023, T039a) depend on T004b, T005b, T006b verification passing.
- **T002 Retirement**: Task ID T002 was merged into T001b and is retired.