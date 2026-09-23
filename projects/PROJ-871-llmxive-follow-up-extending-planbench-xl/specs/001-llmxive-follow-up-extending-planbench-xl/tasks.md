# Tasks: llmXive follow-up: extending "PlanBench-XL: Evaluating Long-Horizon Planning of LLM Tool-Use Agents "

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-planbench-xl/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are REQUIRED - included here to ensure the "deterministic fabrication guard" and statistical rigor are verified before full execution.

**Organization**: Tasks are grouped by phase to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root (adjusted to `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/` per plan.md)
- Paths shown below assume single project structure - adjusted to plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Initialize Project Structure: Create root directory `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/` and all subdirectories (`code/`, `data/`, `tests/`) with their respective subfolders as defined in `plan.md`.
- [ ] T001b [P] Create `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/requirements.txt` with pinned versions: `datasets==2.14.0`, `transformers==4.35.0`, `torch==2.1.0`, `scikit-learn==1.3.0`, `pandas==2.1.0`, `pytest==7.4.0`, `requests==2.31.0`, `scipy==1.11.0`, `bitsandbytes==0.41.0`
- [ ] T001c [P] Create `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/.gitignore` to exclude `data/`, `*.pyc`, `__pycache__`, `venv/`, `*.log`, `*.jsonl`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure AND real data preparation that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This includes the synthetic injection of the "implicit failure" subset.

- [ ] T002a [P] Create Python virtual environment in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/venv/`
- [ ] T002b [P] Install dependencies from `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/requirements.txt` into the venv
- [ ] T002c [P] Activate venv and verify `python --version` and `pip list`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/`
- [X] T004 [P] Implement deterministic configuration loader in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/utils/config.py` (seeds, hyperparameters, CPU-only flags)
- [X] T005 [P] Implement structured logging utility in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/utils/logger.py` (JSONL format for execution logs)
- [X] T006 [P] Create base abstract agent class in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/agents/base.py`
- [ ] T007 Setup data directory structure (`data/raw`, `data/derived`, `data/logs`, `data/results`) and `.gitignore` for large artifacts. **Constraint**: Must be executed before T008 and T009a.

### Data Preparation (Phase 2 Sub-phase)

**Goal**: Download PlanBench-XL and synthetically construct the "implicit failure" subset and signature index required for US1 and US2, as the original dataset lacks these labels.

- [X] T008 [P] Implement data loader in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/loader.py` to download PlanBench-XL from the official HuggingFace repository `PlanBench/planbench-xl`. **Constraint**: Must use `datasets.load_dataset(..., streaming=True)` to handle large datasets within RAM limits. **Retry Logic**: Implement exponential backoff retry (max a limited number of attempts) before failing loudly. If all retries fail, raise a clear error message indicating the dataset source is unreachable. **Note**: The execution environment must provide access to this verified real data source. Save raw parquet to `data/raw/`.
- [ ] T009a [~] Implement synthetic failure injection in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/injector.py`: Load raw data from `data/raw/` (buffering only the selected subset), select the first N tasks (N=50) where `ground_truth == success` using a fixed random seed and deterministic iteration order, and programmatically inject specific error patterns (e.g., `ERROR: silent_tool_failure`) into their tool outputs to create the "implicit failure" subset. Save to `data/derived/implicit_failure_subset.jsonl`. **Constraint**: Do NOT attempt to extract "real" failures; the subset is created by injection to simulate the condition, as the dataset lacks explicit 'implicit failure' labels. Output schema: JSONL with original fields + `injected_error_pattern` flag. **Dependency**: Must run after T008.
- [ ] T009b [~] Implement failure signature index construction in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/indexer.py`: Parse `data/derived/implicit_failure_subset.jsonl`, extract the *injected* failure patterns, map them to tool identifiers, and save to `data/derived/failure_signatures.json`. JSON Schema: `{"tool_id": "pattern_string", "recovery_strategy": "replan"}`. **Constraint**: Ensure all entries use a consistent `recovery_strategy` (e.g., "replan"). **Dependency**: Must run after T009a. <!-- FAILED: unspecified -->

### Prerequisite Tests (Phase 2 Sub-phase)

**Goal**: Ensure data generation logic is correct before implementation.

- [X] T010 [P] [US1] Contract test for data loader in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/unit/test_loader.py`. **Constraint**: The test must download a minimal real subset of the PlanBench-XL dataset (via T008 logic) to verify loading logic and schema compliance. It must also verify that a fake URL raises an exception immediately after retries. No mock files. <!-- ATOMIZE: requested -->
- [ ] T011 [P] [US1] Integration test for baseline agent execution in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/integration/test_baseline_agent.py` (verifies log generation without signature index). **Constraint**: Must use `data/derived/implicit_failure_subset.jsonl` generated by T009a as the test data source. <!-- FAILED: unspecified -->
- [X] T014 [P] [US1] Implement isolation validation test in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/unit/test_isolation.py::test_no_signature_access`. **Constraint**: This unit test must assert that the baseline agent code does not import or access `data/derived/failure_signatures.json`. **Dependency**: Must run after T009b ensures the file exists.
- [X] T015 [P] [US2] Unit test for synthetic injection logic in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/unit/test_injector.py` (verifies deterministic error injection into success tasks)
- [X] T016 [P] [US2] Unit test for signature index construction in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/unit/test_indexer.py` (verifies static JSON index creation with consistent schema)

**Checkpoint**: Foundation and Synthetic Data ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Agent Implementation (Priority: P1) 🎯 MVP

**Goal**: Execute baseline agent on synthetic "implicit failure" subset to establish performance baseline.

**Independent Test**: The system generates a JSON execution log containing the final task status (success/failure) for each task in the subset, validated against the ground truth.

### Implementation for User Story 1

- [X] T012 [US1] Implement baseline agent in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/agents/baseline.py` using internal LLM reasoning only (no external index access). **Model**: `meta-llama/Meta-Llama-3-8B` with `bitsandbytes` quantization (`load_in_bit=True`) for CPU feasibility. **Params**: max_tokens=512, temperature=0.7. **Constraint**: Must run on CPU; do not include CUDA device checks.
- [ ] T013 [US1] Implement baseline execution runner in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/run_baseline.py` to process `data/derived/implicit_failure_subset.jsonl` and write logs to `data/logs/baseline_execution.jsonl`. **Constraint**: Must process tasks sequentially or in small batches to respect GB RAM limit.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Augmented Agent Implementation (Priority: P1)

**Goal**: Execute augmented agent with signature retrieval on the same subset.

**Independent Test**: The system detects known implicit failures via the JSON index, triggers recovery, and logs the outcome with a flag indicating signature usage.

### Implementation for User Story 2

- [ ] T018 [US2] Implement augmented agent in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/agents/augmented.py` with string-matching check against `data/derived/failure_signatures.json` post-invocation. **JSON Schema**: `{"tool_id": "pattern_string", "recovery_strategy": "replan"}`. **Matching**: Use Python `re` module. If `pattern_string` contains `*`, treat as wildcard (e.g., `*failure*`); otherwise, perform exact string match. **Threshold**: A perfect match (or wildcard match) is required to trigger recovery.
- [ ] T019 [US2] Implement recovery strategy logic in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/agents/augmented.py` (re-plan or tool substitution, NOT returning ground truth directly). **Constraint**: Recovery must involve a new LLM call; do not hardcode the correct answer.
- [ ] T020 [US2] Implement augmented execution runner in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/run_augmented.py` to process `data/derived/implicit_failure_subset.jsonl` and write logs to `data/logs/augmented_execution.jsonl`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison (Priority: P2)

**Goal**: Compute success rates and perform statistical significance testing.

**Independent Test**: The system outputs a summary report with success rates, test statistic, p-value, and a conclusion on hypothesis validity.

### Implementation for User Story 3

- [ ] T021 [P] [US3] Unit test for statistical analysis in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/unit/test_stats.py` (verifies Fisher's Exact and z-test calculation logic). **Note**: Write before implementation; execution depends on logs from Phase 3/4.
- [ ] T022 [P] [US3] Integration test for report generation in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/integration/test_analysis_report.py`. **Note**: Write before implementation; execution depends on logs from T026 (which runs T013/T020).
- [ ] T023 [P] [US3] Implement statistical analysis module in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/analysis/stats.py`: **Logic**: Count events from logs. Let `n` = total number of tasks in the subset. **IF** `n < 30`, perform **Fisher's Exact Test** using `scipy.stats.fisher_exact`. **ELSE**, perform **two-proportion z-test** using `scipy.stats.proportions_ztest`. Output p-value, test type, and conclusion. **Constraint**: Must implement the conditional logic as per FR-006; do NOT use z-test exclusively.
- [ ] T024 [US3] Implement log parser in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/analysis/log_parser.py` to aggregate success/failure counts from `data/logs/baseline_execution.jsonl` and `data/logs/augmented_execution.jsonl` for input to the statistical test.
- [ ] T025 [US3] Implement report generator in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/analysis/report.py` to output final results (success rates, difference, p-value, test type, conclusion) to `data/results/final_report.json`.
- [ ] T026a [US3] Implement main experiment orchestrator in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/run_experiment.py`: Orchestrate the full pipeline (Load -> Inject/Index -> Baseline Run -> Augmented Run -> Analysis -> Report). **Constraint**: This task must *execute* T013 and T020 to generate the logs required by T024/T025. **Timing**: Must measure total duration, log it, and compare against the 6-hour SC-004 limit.
- [ ] T026b [US3] Implement data pipeline execution within T026a: Call T008, T009a, T009b.
- [ ] T026c [US3] Implement agent execution pipeline within T026a: Call T013, T020.
- [ ] T026d [US3] Implement analysis pipeline within T026a: Call T024, T023, T025.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Documentation updates in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/README.md` and `quickstart.md`
- [ ] T029a [P] Code cleanup: Replace hardcoded paths in `code/agents/` with config loader keys from `code/utils/config.py`
- [ ] T029b [P] Code cleanup: Replace hardcoded paths in `code/analysis/` with config loader keys from `code/utils/config.py`
- [ ] T029c [P] Code cleanup: Verify all paths in `code/` use config loader; run linting (flake8, black)
- [ ] T030a [P] Performance optimization: Write memory monitoring script in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/utils/memory_monitor.py` to log peak RAM usage during execution. **Constraint**: Must explicitly measure peak memory, log the specific value (e.g., "Peak RAM: 6.2 GB"), and validate against the 7GB SC-005 limit.
- [ ] T030b [P] Performance optimization: Integrate memory monitor into `run_experiment.py` to verify memory usage stays within 7GB limit and report the result.
- [ ] T031 [P] Additional unit tests foredge cases (corrupted data, API timeout handling) in `tests/unit/` (specifically `test_timeout_handler.py`).
- [ ] T032 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility within 6 hours (Wikipedia: Rhythm 0, https://en.wikipedia.org/wiki/Rhythm_0) and measure total compute time.
- [ ] T033 [P] [SC-004] Implement compute time measurement: Add a timer wrapper to `run_experiment.py` (T026a) that logs the total duration of the experiment start-to-finish, compares it against the 6-hour SC-004 limit, and records the result in `data/results/final_report.json`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**. Includes data loading, synthetic injection, and prerequisite tests.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (Phase 3)**: Depends on `data/derived/implicit_failure_subset.jsonl` and `data/derived/failure_signatures.json` (generated in Phase 2) for data loading and validation.
 - **User Story 2 (Phase 4)**: Depends on `data/derived/implicit_failure_subset.jsonl` and `data/derived/failure_signatures.json` (generated in Phase 2).
 - **User Story 3 (Phase 5)**: Depends on execution logs from US1 and US2.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Phase 2 (specifically T009a `implicit_failure_subset.jsonl` and T009b `failure_signatures.json` existence for validation).
- **User Story 2 (P1)**: Depends on Phase 2 (specifically T009a and T009b).
- **User Story 3 (P2)**: Depends on execution logs from US1 and US2.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services/agents
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT** T009a/T009b which depend on T008
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Critical Ordering Notes

- **T007** must precede **T008** and **T009a**.
- **T009a** and **T009b** are **NOT** parallel to **T008**; they depend on T008 completion.
- **T014** depends on **T009b** (file must exist).
- **T026** (Orchestrator) produces logs consumed by **T024/T025**; T024/T025 depend on T026's *output*, not its execution step. T026 must precede T024/T025 in the execution order.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Baseline Execution)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify log generation and ground truth comparison)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Augmented logic)
4. Add User Story 3 → Test independently → Deploy/Demo (Statistical conclusion)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Baseline)
 - Developer B: User Story 2 (Augmented + Injection)
 - Developer C: User Story 3 (Analysis + Reporting)
3. Stories complete and integrate independently via `run_experiment.py`

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- **CRITICAL**: Do NOT fabricate data. All tasks must consume the real PlanBench-XL dataset (downloaded via `loader.py`) and the *synthetically injected* failure patterns (deterministic via `injector.py`). The "implicit failure" subset is created by injection from real data, not pre-existing.
- **CRITICAL**: Ensure the LLM used for agents is CPU-tractable (e.g., quantized 4-bit/8-bit if available on CPU, or a smaller model like Llama-3-8B on CPU) to fit within 7GB RAM and 6-hour runtime. Avoid CUDA-specific code.
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: The statistical analysis MUST implement the conditional logic: Fisher's Exact Test if n < 30, otherwise two-proportion z-test, as per FR-006.
- **CRITICAL**: Data loader (T008) must stream the dataset to avoid OOM errors; do not load the full dataset into memory at once.
- **CRITICAL**: If the real dataset download fails, the task must fail loudly; do not implement a fallback to synthetic data. (Retry logic is allowed for transient network issues).
- **CRITICAL**: Tasks T009a and T009b must use a deterministic selection rule (seed=42) to ensure reproducibility.
- **CRITICAL**: T033 and T030b must explicitly measure and validate against SC-004 (6h) and SC-005 (7GB) limits.
- **Dependency Note**: T009a depends on T008 completion. T026 produces logs for T024/T025.