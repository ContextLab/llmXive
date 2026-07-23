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
- [ ] T001b [P] Create empty `projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c/requirements.txt` and `.gitignore` (with standard Python patterns like `__pycache__`, `.env`, `*.pyc`).
- [ ] T002 [P] Update `projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c/requirements.txt` with **pinned versions**: `transformers==4.40.0`, `bitsandbytes==0.43.1`, `scikit-learn==1.5.0`, `sentence-transformers==3.0.1`, `numpy==1.26.4`, `pandas==2.2.2`, `pytest==8.2.0`, `pyyaml==6.0.1`, `datasets==2.19.1`, `sentencepiece==0.2.0`.
- [X] T003a [P] Create `pyproject.toml` in project root with configuration for `black` and `ruff` (rules: E, F, W, I, N).
- [X] T003b [P] Run initial lint/format check on empty codebase to verify tool configuration. **Execute command**: `ruff check. > results/lint_report.txt`. **Verification**: Exit code must be 0 or 1 (warnings/errors allowed). **Artifact**: `results/lint_report.txt` must exist with the logged output.
- [ ] T004 [P] Implement `utils/checksum.py` to generate SHA-256 checksums for `data/processed/` (Constitution Principle III).
- [ ] T005 [P] Implement `utils/hasher.py` to generate version hashes for artifacts (Constitution Principle V).
- [ ] T006 [P] Implement `utils/renderer_validator.py` to verify ASCII vs Visual ground truth consistency (SC-005).
- [X] T007 [P] Create base `code/__init__.py` and data model contracts in `specs/contracts/`:
 - `state_snapshot.schema.yaml` (fields: `ascii_grid`, `event_log`, `ground_truth_state`, `masked_ground_truth`)
 - `metric_result.schema.yaml` (fields: `memory_gap_score`, `p_value`, `confidence_interval`, `run_id`)
- [X] T008 [P] Implement `code/logger.py` with JSON-formatted rotating file handler (`max_bytes=10MB`, `backupCount=5`) and configure `code/main.py` to use it for all stdout/stderr redirection.
- [X] T009 [P] Create `config/seeds.yaml` containing a **representative** list of integers for reproducibility. and implement `code/config_loader.py` to load this file and export a global `SEEDS` list.

**Checkpoint**: Setup and Utilities ready.

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
- [X] T021 [P] [US1] Integration test for full renderer pipeline in `tests/integration/test_full_loop.py` (verify ASCII consistency). **Note: Uses `utils/renderer_validator.py` (T006).**
- [X] T022 [US1] **BLOCKING**: Execute `utils/renderer_validator.py` on generated `data/processed/seeds_*.ascii` and `data/processed/seeds_*.png` files to generate `results/validation_report.json` ensuring Levenshtein distance = 0 (SC-005). **Data cannot be used in subsequent phases until this task passes.** **Depends on T015b, T015c, T016b, T021.** **COMMAND**: `python utils/renderer_validator.py --input data/processed/seeds_*.ascii --visual-input data/processed/seeds_*.png --output results/validation_report.json`. **Verification**: `results/validation_report.json` must exist with `status: PASS`. **Note: This task validates RENDERER FIDELITY (ASCII vs Visual) ONLY, not the Memory Gap metric.**

### Implementation for User Story 2 (Text Agent)

- [X] T023 [P] [US2] Implement `code/agent_loop.py` to load quantized text-only LLM (≤3B params) using CPU-optimized engine (FR-002).
- [X] T024 [US2] Implement `code/agent_loop.py` inference cycle: receive ASCII/Log, output JSON action + updated mental map (FR-003). **Implementation Details**: Include **context window management** (sliding window/truncation), **hard step limit** (500 steps), and **error handling** (NaN, OOM) as integral parts of this task. **Output Schema**: `{"action": "move_up|move_down|move_left|move_right|wait", "mental_map": "string"}`. **Artifact**: `data/processed/agent_run_<seed>.json`. **Depends on T023.**
- [X] T025 [US2] **Verification**: Verify context window truncation logic in `code/agent_loop.py` (keep last N=50 events). **Test**: Run a synthetic long-log input and verify the oldest events are dropped. **Artifact**: `results/context_truncation_test.log`. **Depends on T024.**
- [X] T026 [US2] **Verification**: Verify hard step limit logic in `code/agent_loop.py` (limit a configurable maximum number of steps). **Test**: Run a synthetic infinite-loop scenario and verify the run is marked "timeout" and logged to `results/discarded_runs.csv`. **Artifact**: `results/step_limit_test.log`. **Depends on T024.**
- [X] T027 [US2] **Verification**: Verify error handling logic in `code/agent_loop.py` (NaN, OOM). **Test**: Inject NaN into output tensor and verify the run is discarded and logged to `results/discarded_runs.csv`. **Artifact**: `results/error_handling_test.log`. **Depends on T024.**
- [X] T028 [US2] Implement `code/resource_monitor.py` to log peak RAM and CPU usage to `results/resource_profile.json` after every agent run (Constitution Principle VII). **Output Schema**: `{"peak_ram_mb": float, `cpu_percent`: float, `run_id`: string}`. **Frequency**: Log at regular, periodic intervals. **Verification**: Assert `peak_ram_mb <= 7168` and `cpu_percent <= 200`. **Depends on T024.**

### Implementation for User Story 2 (Baseline Agent)

- [ ] T039a [P] [US2] Implement `code/baseline_runner.py` to load a Vision-capable MLLM (e.g., `Qwen-VL-Chat-Int4`), process Visual inputs (raw frames), manage context, and output structured JSON mental maps. **Implements Plan Override of FR-008.** **Output Schema**: `{"action": "string", "mental_map": "string"}`. **Artifact**: `data/processed/baseline_seeds_*.json`. **Verification**: Confirm output is compared against the *same masked ground truth* as the Text Agent. **Depends on T015c (Visual Frames).**
 - [ ] **T039a-1**: Verify baseline model memory footprint <= 7GB RAM using `memory_profiler` before finalizing the runner. **Command**: `python -m memory_profiler code/baseline_runner.py --seed 1`. **Artifact**: `results/memory_profile_baseline.txt`. **Depends on T039a.**
 - [ ] **T039a-2**: Verify Baseline's output is compared against the *same masked ground truth* as the Text Agent (Plan Decision). **Verification**: Run a mock comparison with `tests/unit/test_hidden_masking.py` logic on baseline output. **Artifact**: `results/baseline_masking_verification.json`. **Depends on T039a.**
- [ ] T039b [US2] Execute `code/baseline_runner.py` on seeds from `config/seeds.yaml` to generate baseline logs in `data/processed/`. **Command**: `python code/baseline_runner.py --seeds config/seeds.yaml --output data/processed/baseline_seeds_*.json`. **Depends on T039a AND T022 (Data Validation) AND T015c.** <!-- FAILED: unspecified -->

### Performance Verification (Blocking)

- [X] T041a [US2] Implement `code/benchmark_runner.py` to orchestrate the execution of N=20 game instances for the Text Agent. **Artifact**: `code/benchmark_runner.py`. **Depends on T023-T028.**
- [ ] T041 [US2] Execute `code/benchmark_runner.py` on seeds from `config/seeds.yaml` to generate `results/benchmark_log.json`. **Command**: `python code/benchmark_runner.py --seeds config/seeds.yaml --output results/benchmark_log.json`. **Verification**: `results/benchmark_log.json` must exist with `total_time_hours < 6.0` and `passed: true`. **Depends on T041a, T023-T028, T015b.**

**Checkpoint**: All data generation (US1, US2, Baseline) complete.

---

## Phase 4: User Story 3 Implementation (Scoring & Statistics)

**Goal**: Implement Scorer (US3) and Statistical Analysis.

### Tests for User Story 3 ⚠️
- [X] T030 [P] [US3] Unit test for Structured JSON comparison in `tests/unit/test_scorer.py`.
- [X] T031 [P] [US3] Unit test for Mann-Whitney U test in `tests/unit/test_stats.py`.
- [X] T032 [P] [US3] Integration test for full scoring pipeline in `tests/integration/test_full_loop.py`.

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/baseline_adapter.py` to parse Baseline MLLM (Visual) output into structured JSON mental map. **Parsing Logic**: Extract `action` and `mental_map` fields from JSON. **Target Schema**: Matches `state_snapshot.schema.yaml`. **Validation**: Confirm output matches the masked ground-truth format used by the Text Agent. **Depends on T007.**
- [X] T033c [P] [US3] **Kickback Submission**: Submit the Spec Kickback for FR-006 and FR-008 overrides. **Action**: Create a formal Kickback request in `docs/kickbacks/` detailing the Plan Override (Structured Metric, Visual Baseline). **Artifact**: `docs/kickbacks/001-metric-baseline-override.md`. **Depends on T033.**
- [ ] T033b [P] [US3] **Spec Update**: Update `spec.md` to formally ratify the "Structured JSON Comparison + Semantic Similarity" metric (Plan Override of FR-006) and the Baseline Visual Input strategy (Plan Override of FR-008). **Content**: Add section "Metric Definition: Structured JSON + Semantic Similarity" and update FR-008/FR-006. **Verification**: Ensure the Spec update is completed and ratified. **Depends on T033c.** (Parallel to T034 implementation based on Plan).
- [X] T034 [US3] Implement `code/scorer.py` to calculate "Memory Gap" using Structured JSON comparison + Semantic Similarity (Plan Override of FR-006). **Library**: `sentence-transformers/all-MiniLM-L6-v2`. **Formula**: `score = (1 - semantic_similarity) + (penalty * missing_items)`. **Verification**: Include a step to confirm the new metric satisfies the *intent* of FR-006 (measuring state retention) and explicitly tags the deviation as 'Plan Override' in the code comments and logs. **Depends on T033, T007, T033c.**
 - [ ] **Verification**: Run `tests/unit/test_scorer.py` to validate the new metric.
- [X] T035 [US3] Implement `code/scorer.py` logic to apply a penalty for missing critical items in hidden ground truth (FR-007). **Penalty**: 1.0 per critical item (key, door) missing from agent's mental map. **Logic**: Identify critical items in `masked_ground_truth` and compare with `agent_mental_map`. **Verify masking logic is applied to Baseline agent comparison.** (Depends on T007 contract). **Depends on T034.**
- [ ] T037 [US3] Implement `code/stats.py` to perform one-tailed Mann-Whitney U test (FR-005).
- [ ] T038 [US3] Implement `code/main.py` to orchestrate Text Agent and Baseline runs, aggregate results into `results/statistical_summary.json`, and trigger `utils/checksum.py` on `data/processed/`. **Aggregation**: Calculate mean, std, p-value. **Schema**: `{"text_mean": float, "baseline_mean": float, "p_value": float, "conclusion": "string"}`. **Command**: `python utils/checksum.py --input data/processed/ --output state/checksums.yaml`. **Depends on T034, T035, T037.**

**Checkpoint**: Scoring and Statistics implementation complete.

---

## Phase 5: Execution, Finalization & Polish

**Purpose**: Run final experiments, finalize artifacts, and validate.

- [ ] T039c [US3] Execute full experiment batch (Text Agent + Baseline) for **N=20** (Pilot) and generate `results/statistical_summary.json`. **Command**: `python code/main.py --mode pilot --seeds 1..20`. **Depends on T041 pass.**
- [ ] T039c-1 [US3] Perform Power Analysis on Pilot results. **Method**: G*Power (effect size calculation). **Input**: `results/statistical_summary.json`. **Artifact**: `results/power_analysis_report.json`. **Depends on T039c.**
- [ ] T039d [US3] **Conditional**: If Power Analysis requires scaling (power < 0.8), execute full experiment batch for **N=64** and update `results/statistical_summary.json`. **Command**: `python code/main.py --mode full --seeds 1..64`. **Depends on T039c-1 (Decision Gate).**
- [ ] T040a [P] Documentation: Update `docs/methodology.md` with the Structured Metric definition and Baseline Visual Input strategy. **Content**: Add sections "Metric: Structured JSON + Semantic Similarity" and "Baseline: Visual Input Strategy".
- [ ] T040b [P] Documentation: Update `docs/quickstart.md` with exact execution commands. **Commands**: `python code/main.py --mode pilot`, `python code/main.py --mode full`.
- [ ] T040c [P] Documentation: Update `docs/api.md` with new module signatures. **Modules**: `code/renderer.py`, `code/agent_loop.py`, `code/scorer.py`, `code/stats.py`.
- [ ] T042a [P] Add edge case tests for `code/stats.py` Mann-Whitney edge cases in `tests/unit/test_stats.py`: **empty input**, **single sample**, **identical values**. **Test Names**: `test_mann_whitney_empty`, `test_mann_whitney_single`, `test_mann_whitney_identical`.
- [ ] T042b [P] Add integration tests for full loop in `tests/integration/test_full_loop.py`. **Test Name**: `test_full_loop_integration`. **Input**: `data/processed/seeds_1.ascii`. **Expected**: `results/statistical_summary.json` generated.
- [ ] T043 [Phase 5] Run `utils/checksum.py` on `data/processed/` and update `state/...yaml`. **Command**: `python utils/checksum.py --input data/processed/ --output state/checksums.yaml`. **Depends on T039c/T039d.**
- [ ] T046 [Phase 5] Run `utils/hasher.py` to finalize artifact versions (Constitution V). **Command**: `python utils/hasher.py --input data/processed/ --output state/artifact_hashes.yaml`. **Depends on T039c/T039d and T043. Serial final step.**
- [ ] T044 [Phase 5] Execute all commands in `docs/quickstart.md` in a fresh virtualenv and verify exit code 0 for all steps, logging output to `results/quickstart_validation.log`. **Command**: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python code/main.py --mode pilot`.

**Checkpoint**: Project complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational Design (Phase 2)**: Depends on Setup - BLOCKS implementation
- **Implementation (Phase 3)**: Depends on Design - Generates Data
- **Scoring (Phase 4)**: Depends on Data Generation (Phase 3) AND Kickback Submission (T033c) - Calculates Metrics
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
- **Kickback Process**: T033c (Kickback Submission) must be completed before T033b (Spec Update) and T034 (Scorer Implementation) can be considered fully ratified.