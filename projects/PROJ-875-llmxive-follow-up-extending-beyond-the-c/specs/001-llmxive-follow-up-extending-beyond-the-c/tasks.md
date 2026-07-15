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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c/`: Create directories `code/`, `utils/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/integration/`, `docs/`, `results/`, `config/`. Create files `code/__init__.py`, `requirements.txt`, `.gitignore`.
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` including `transformers`, `bitsandbytes`, `scikit-learn`, `sentence-transformers`, `numpy`, `pandas`, `pytest`, `pyyaml`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `utils/checksum.py` to generate SHA-256 checksums for `data/processed/` (Constitution Principle III)
- [ ] T005 [P] Implement `utils/hasher.py` to generate version hashes for artifacts (Constitution Principle V)
- [ ] T006 [P] Implement `utils/renderer_validator.py` to verify ASCII vs Visual ground truth consistency (SC-005)
- [ ] T007 Create base `code/__init__.py` and data model contracts in `specs/contracts/`
- [ ] T008 Implement `code/logger.py` with JSON-formatted rotating file handler (max limited size, multiple backups) and configure `code/main.py` to use it for all stdout/stderr redirection.
- [ ] T009 Create `config/seeds.yaml` containing a list of integer seeds. and implement `code/config_loader.py` to load this file and export a global `SEEDS` list.
- [ ] T010 [P] [US1] Unit test for ASCII grid generation in `tests/unit/test_renderer.py` (verify `#`, `.`, `M` mapping)
- [ ] T011 [P] [US1] Unit test for JSON event logging in `tests/unit/test_renderer.py` (verify `{"t": ..., "event": "saw_key"}` format)
- [ ] T012 [P] [US1] Unit test for error handling in `tests/unit/test_renderer.py` (verify `ERROR: STATE_CORRUPT` output)
- [ ] T013 [P] [US1] Integration test for full renderer pipeline in `tests/integration/test_full_loop.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - ASCII State Rendering and Environment Generation (Priority: P1) 🎯 MVP

**Goal**: Generate deterministic 3D Maze game instances where raw visual frames are converted into ASCII text representations and JSON event logs.

**Independent Test**: Run the renderer script on a fixed seed, capture output ASCII grid and JSON log, verify bit-identical output and 1:1 mapping to ground truth.

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `code/renderer.py` to convert RNG-Bench visual state to ASCII grid string
- [ ] T015 [P] [US1] Implement `code/renderer.py` to generate JSON event logs for every time step (FR-001)
- [ ] T016 [US1] Add validation for out-of-bounds states and standardized error blocks
- [ ] T016b [US1] Execute `utils/renderer_validator.py` on generated `data/processed/` files to generate `results/validation_report.json` ensuring Levenshtein distance = 0 (SC-005).
- [ ] T017 [US1] Integrate `utils/checksum.py` to record checksums for generated `data/processed/` files into `state/...yaml`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Text-Only Agent Inference Loop (Priority: P2)

**Goal**: Execute a text-only LLM in a long-horizon loop receiving ASCII state and event logs, updating an internal "mental map," and outputting actions within CPU constraints.

**Independent Test**: Run a short, fixed-sequence maze game, verify valid move sequence output and logical "mental map" evolution.

### Tests for User Story 2 ⚠️

- [ ] T019 [P] [US2] Unit test for model loading in `tests/unit/test_agent_loop.py` (verify quantized model loads under feasible RAM constraints)
- [ ] T020 [P] [US2] Unit test for prompt construction in `tests/unit/test_agent_loop.py` (verify ASCII + JSON history formatting)
- [ ] T021 [P] [US2] Unit test for sliding window logic in `tests/unit/test_agent_loop.py` (verify context truncation strategy)
- [ ] T022 [P] [US2] Integration test for full agent loop in `tests/integration/test_full_loop.py`

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `code/agent_loop.py` to load quantized text-only LLM (≤3B params) using CPU-optimized engine (FR-002)
- [ ] T024 [P] [US2] Implement `code/agent_loop.py` inference cycle: receive ASCII/Log, output JSON action + updated mental map (FR-003)
- [ ] T025 [US2] Implement context window management (sliding window/truncation) to handle long event logs
- [ ] T026 [US2] Implement a hard step limit to prevent hangs on stuck agents.
- [ ] T027 [US2] Implement error handling for inference failures (NaN output, OOM) with logging and run discard
- [ ] T028 [US2] Implement `code/resource_monitor.py` to log peak RAM and CPU usage to `results/resource_profile.json` after every agent run (Constitution Principle VII).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Memory Gap Metric Calculation and Statistical Comparison (Priority: P3)

**Goal**: Compute "Memory Gap" score by comparing agent's internal state description against masked ground-truth state and perform statistical comparison against baseline.

**Independent Test**: Feed agent output logs and ground-truth logs into scorer, verify numeric score and statistical test execution.

### Tests for User Story 3 ⚠️

- [ ] T029 [P] [US3] Unit test for "Hidden State Masking" logic in `tests/unit/test_hidden_masking.py` (verify visible items excluded) - Write test for T035.
- [ ] T030 [P] [US3] Unit test for Structured JSON comparison in `tests/unit/test_scorer.py`
- [ ] T031 [P] [US3] Unit test for Mann-Whitney U test in `tests/unit/test_stats.py`
- [ ] T032 [P] [US3] Integration test for full scoring pipeline in `tests/integration/test_full_loop.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/baseline_adapter.py` to parse Baseline MLLM (Visual) output into structured JSON mental map (Plan Override of FR-008). **Include validation step to confirm output matches the masked ground-truth format used by the Text Agent.**
- [ ] T034 [US3] Implement `code/scorer.py` to calculate "Memory Gap" using Structured JSON comparison + Semantic Similarity (Plan Override of FR-006). **Ensure Hidden State Masking is applied to BOTH Text Agent and Baseline Agent comparisons.** (Depends on T007 contract).
- [ ] T035 [US3] Implement `code/scorer.py` logic to apply a penalty for missing critical items in hidden ground truth (FR-007). **Verify masking logic is applied to Baseline agent comparison.**
- [ ] T036 [US3] Implement `code/stats.py` to perform one-tailed Mann-Whitney U test (FR-005)
- [ ] T037 [US3] Implement `code/main.py` to orchestrate Text Agent and Baseline runs, aggregate results into `results/statistical_summary.json`, and trigger `utils/checksum.py` on `data/processed/`.
- [ ] T038 [US3] Generate `results/statistical_summary.json` with p-values, confidence intervals, and **mean Memory Gap scores for both Text Agent and Baseline** (SC-001).
- [ ] T039 [US3] Execute Baseline MLLM on Visual inputs using seeds from `config/seeds.yaml` to generate the baseline distribution logs required for FR-005 and SC-001.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` and `research.md`
- [ ] T041 [US3] Refactor `code/agent_loop.py` to implement sliding window context truncation and verify batch of runs completes in <6 hours via `results/benchmark_log.json`. **Instrument `main.py` to measure and report total batch execution time.**
- [ ] T042 [P] Additional unit tests in `tests/unit/`
- [ ] T043 [US4] Run `utils/hasher.py` to finalize artifact versions (Constitution V). **Dependent on completion of all data generation tasks (T014-T017, T023-T028, T033-T039).** (Serial final step).
- [ ] T044 [US4] Execute all commands in `docs/quickstart.md` in a fresh virtualenv and verify exit code 0 for all steps, logging output to `results/quickstart_validation.log`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for ASCII grid generation in tests/unit/test_renderer.py"
Task: "Unit test for JSON event logging in tests/unit/test_renderer.py"
Task: "Unit test for error handling in tests/unit/test_renderer.py"

# Launch implementation for User Story 1:
Task: "Implement code/renderer.py to convert RNG-Bench visual state to ASCII grid string"
Task: "Implement code/renderer.py to generate JSON event logs for every time step"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify ASCII consistency)
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
   - Developer A: User Story 1 (Renderer & Validation)
   - Developer B: User Story 2 (Agent Loop & Quantization)
   - Developer C: User Story 3 (Scorer & Statistics)
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
- **Data Hygiene**: All data files in `data/processed/` MUST have checksums generated before use.
- **Modality Isolation**: Ensure Baseline runs on Visual inputs and Text Agent runs on ASCII inputs (Plan Override of FR-008).
- **Metric Validity**: Ensure "Memory Gap" uses Structured JSON comparison, not raw Levenshtein distance (Plan Override of FR-006).
- **Serial Final Step**: T043 is a serial final step dependent on all data generation tasks.