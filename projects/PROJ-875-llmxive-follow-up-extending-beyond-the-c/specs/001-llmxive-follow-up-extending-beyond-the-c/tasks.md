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

- [ ] T001a [P] Re-create project directory structure in `projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c/`: Create directories `code/`, `utils/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/integration/`, `docs/`, `results/`, `config/`, `specs/contracts/`. Create `code/__init__.py`.
- [ ] T001b [P] Create empty `projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c/requirements.txt` and `.gitignore` (with standard Python patterns like `__pycache__`, `.env`, `*.pyc`).
- [ ] T002 [P] Update `projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c/requirements.txt` with pinned versions: `transformers`, `bitsandbytes`, `scikit-learn`, `sentence-transformers`, `numpy`, `pandas`, `pytest`, `pyyaml`, `datasets`, `sentencepiece`.
- [ ] T003a [P] Create `pyproject.toml` in project root with configuration for `black` and `ruff` (rules: E, F, W, I, N).
- [ ] T003b [P] Run initial lint/format check on empty codebase to verify tool configuration.
- [ ] T004 [P] Implement `utils/checksum.py` to generate SHA-256 checksums for `data/processed/` (Constitution Principle III).
- [ ] T005 [P] Implement `utils/hasher.py` to generate version hashes for artifacts (Constitution Principle V).
- [ ] T006 [P] Implement `utils/renderer_validator.py` to verify ASCII vs Visual ground truth consistency (SC-005).
- [ ] T007 [P] Create base `code/__init__.py` and data model contracts in `specs/contracts/`:
    - `state_snapshot.schema.yaml` (fields: `ascii_grid`, `event_log`, `ground_truth_state`, `masked_ground_truth`)
    - `metric_result.schema.yaml` (fields: `memory_gap_score`, `p_value`, `confidence_interval`, `run_id`)
- [ ] T008 [P] Implement `code/logger.py` with JSON-formatted rotating file handler (max limited size, multiple backups) and configure `code/main.py` to use it for all stdout/stderr redirection.
- [ ] T009 [P] Create `config/seeds.yaml` containing a list of integer seeds (e.g., [1, 2,..., 20]) and implement `code/config_loader.py` to load this file and export a global `SEEDS` list.

**Checkpoint**: Setup and Utilities ready.

---

## Phase 2: Foundational Design (Blocking Prerequisites)

**Purpose**: Design tasks and test definitions that block implementation.

- [ ] T017 [P] [US3 Design] Design test cases for "Hidden State Masking" logic in `tests/unit/test_hidden_masking.py` (define inputs: masked state, outputs: pass/fail, expected behavior based on Spec FR-007). **Depends on T007 contracts.**

**Checkpoint**: Design ready - implementation can now begin.

---

## Phase 3: User Story 1 & 2 Implementation (Data Generation)

**Goal**: Implement Renderer (US1), Agent (US2), and Baseline (US2) to generate data for scoring.

### Implementation for User Story 1 (Renderer)

- [ ] T014 [P] [US1] Implement `code/renderer.py` to convert RNG-Bench visual state to ASCII grid string.
- [ ] T015 [P] [US1] Implement `code/renderer.py` to generate JSON event logs for every time step (FR-001).
- [ ] T016 [US1] Implement validation for out-of-bounds states and standardized error blocks in `code/renderer.py`.
- [ ] T016b [US1] Unit test for out-of-bounds state validation in `tests/unit/test_renderer.py` (verify `ERROR: STATE_CORRUPT` output).
- [ ] T021 [P] [US1] Integration test for full renderer pipeline in `tests/integration/test_full_loop.py` (verify ASCII consistency). **Note: Uses `utils/renderer_validator.py` (T006).**
- [ ] T022 [US1] Execute `utils/renderer_validator.py` on generated `data/processed/*.ascii` and `data/processed/*.json` files to generate `results/validation_report.json` ensuring Levenshtein distance = 0 (SC-005). **Note: Implements Plan Override of SC-005.**

### Implementation for User Story 2 (Text Agent)

- [ ] T023 [P] [US2] Implement `code/agent_loop.py` to load quantized text-only LLM (≤3B params) using CPU-optimized engine (FR-002).
- [ ] T024 [P] [US2] Implement `code/agent_loop.py` inference cycle: receive ASCII/Log, output JSON action + updated mental map (FR-003).
- [ ] T025 [US2] Implement context window management (sliding window/truncation) to handle long event logs.
- [ ] T026 [US2] Implement a hard step limit to prevent hangs on stuck agents.
- [ ] T027 [US2] Implement error handling for inference failures (NaN output, OOM) with logging and run discard.
- [ ] T028 [US2] Implement `code/resource_monitor.py` to log peak RAM and CPU usage to `results/resource_profile.json` after every agent run (Constitution Principle VII).

### Implementation for User Story 2 (Baseline Agent)

- [ ] T039a [P] [US2] Implement `code/baseline_runner.py` to load a Vision-capable MLLM (e.g., Qwen-VL), process Visual inputs (raw frames), manage context, and output structured JSON mental maps. **Implements Plan Override of FR-008.**
- [ ] T039b [US2] Execute `code/baseline_runner.py` on seeds from `config/seeds.yaml` to generate baseline logs in `data/processed/`. **Depends on T039a.**

### Performance Verification (Blocking)

- [ ] T041 [US2] Refactor `code/agent_loop.py` to implement sliding window context truncation and verify batch of 20 game instances completes in <6 hours via `results/benchmark_log.json`. **Instrument `main.py` to measure and report total batch execution time. Reference SC-004.** **Must pass before Phase 4.**

**Checkpoint**: All data generation (US1, US2, Baseline) complete.

---

## Phase 4: User Story 3 Implementation (Scoring & Statistics)

**Goal**: Implement Scorer (US3) and Statistical Analysis.

### Tests for User Story 3 ⚠️

- [ ] T030 [P] [US3] Unit test for Structured JSON comparison in `tests/unit/test_scorer.py`.
- [ ] T031 [P] [US3] Unit test for Mann-Whitney U test in `tests/unit/test_stats.py`.
- [ ] T032 [P] [US3] Integration test for full scoring pipeline in `tests/integration/test_full_loop.py`.

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/baseline_adapter.py` to parse Baseline MLLM (Visual) output into structured JSON mental map. **Note: Implements Plan Override of FR-008 (Kickback Issue 1); defines new entity 'Baseline Adapter' required by Plan.** **Include validation step to confirm output matches the masked ground-truth format used by the Text Agent.**
- [ ] T034 [US3] Implement `code/scorer.py` to calculate "Memory Gap" using Structured JSON comparison + Semantic Similarity (Plan Override of FR-006). **Ensure Hidden State Masking is applied to BOTH Text Agent and Baseline Agent comparisons.** **Note: Implements Plan Override (Kickback Issue 2).** (Depends on T007 contract).
- [ ] T035 [US3] Implement `code/scorer.py` logic to apply a penalty for missing critical items in hidden ground truth (FR-007). **Verify masking logic is applied to Baseline agent comparison.** (Depends on T007 contract).
- [ ] T036 [US3] Unit test for Hidden State Masking in `tests/unit/test_hidden_masking.py` (verify visible items excluded). **Depends on T017 design.**
- [ ] T037 [US3] Implement `code/stats.py` to perform one-tailed Mann-Whitney U test (FR-005).
- [ ] T038 [US3] Implement `code/main.py` to orchestrate Text Agent and Baseline runs, aggregate results into `results/statistical_summary.json`, and trigger `utils/checksum.py` on `data/processed/`.

**Checkpoint**: Scoring and Statistics implementation complete.

---

## Phase 5: Execution, Finalization & Polish

**Purpose**: Run final experiments, finalize artifacts, and validate.

- [ ] T039c [US3] Execute full experiment batch (Text Agent + Baseline) for N=20 (or N=64 if power analysis requires) and generate `results/statistical_summary.json`. **Depends on T041 pass.**
- [ ] T040 [P] Documentation updates in `docs/` and `research.md`.
- [ ] T042a [P] Add edge case tests for `code/stats.py` Mann-Whitney edge cases in `tests/unit/test_stats.py`.
- [ ] T042b [P] Add integration tests for full loop in `tests/integration/test_full_loop.py`.
- [ ] T043 [Phase 5] Run `utils/checksum.py` on `data/processed/` and update `state/...yaml`. **Depends on T039c.**
- [ ] T046 [Phase 5] Run `utils/hasher.py` to finalize artifact versions (Constitution V). **Depends on T039c and T043. Serial final step.**
- [ ] T044 [Phase 5] Execute all commands in `docs/quickstart.md` in a fresh virtualenv and verify exit code 0 for all steps, logging output to `results/quickstart_validation.log`.

**Checkpoint**: Project complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational Design (Phase 2)**: Depends on Setup - BLOCKS implementation
- **Implementation (Phase 3)**: Depends on Design - Generates Data
- **Scoring (Phase 4)**: Depends on Data Generation - Calculates Metrics
- **Finalization (Phase 5)**: Depends on Scoring - Hashes & Validates

### User Story Dependencies

- **User Story 1 (P1)**: Phase 3 (T014-T022)
- **User Story 2 (P2)**: Phase 3 (T023-T039b, T041)
- **User Story 3 (P3)**: Phase 4 (T033-T038), Phase 5 (T039c)

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
