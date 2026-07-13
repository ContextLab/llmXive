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

- [ ] T001a Create root project directory: `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/`
- [ ] T001b Create code subdirectories: `code/`, `code/agents`, `code/dataset`, `code/analysis`, `code/utils`
- [ ] T001c Create data subdirectories: `data/`, `data/raw`, `data/derived`, `data/logs`, `data/results`
- [ ] T001d Create test subdirectories: `tests/`, `tests/unit`, `tests/integration`
- [ ] T001b Create `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/requirements.txt` with pinned versions: `datasets==2.14.0`, `transformers==4.35.0`, `torch==2.1.0`, `scikit-learn==1.3.0`, `pandas==2.1.0`, `pytest==7.4.0`, `requests==2.31.0`
- [ ] T001c Create `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/.gitignore` to exclude `data/`, `*.pyc`, `__pycache__`, `venv/`, `*.log`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure AND synthetic data preparation that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This includes the creation of the synthetic "implicit failure" subset.

- [ ] T002 [P] Initialize Python virtual environment and install dependencies from `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/requirements.txt`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/`
- [ ] T004 [P] Implement deterministic configuration loader in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/utils/config.py` (seeds, hyperparameters, CPU-only flags)
- [ ] T005 [P] Implement structured logging utility in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/utils/logger.py` (JSONL format for execution logs)
- [ ] T006 Create base abstract agent class in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/agents/base.py`
- [ ] T007 [P] Setup data directory structure (`data/raw`, `data/derived`, `data/logs`, `data/results`) and `.gitignore` for large artifacts

### Synthetic Data Preparation (Phase 2 Sub-phase)

**Goal**: Create the "implicit failure" subset and signature index required for US1 and US2.

- [ ] T008 [P] Implement data loader in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/loader.py` to download PlanBench-XL from the official HuggingFace repository or GitHub source and save raw parquet to `data/raw/`
- [ ] T009a [P] Implement synthetic failure injection in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/injector.py`: Load raw data, select a subset of tasks with "success" ground truth (using random seed 42, targeting a significant proportion of success tasks), inject deterministic error patterns (append 'ERROR: silent_tool_failure' to tool outputs) **ONLY** (do NOT modify the ground_truth field), and save to `data/derived/implicit_failure_subset.jsonl`. Output schema: JSONL with original fields + `injected_error` boolean flag.
- [ ] T009b [P] Implement failure signature index construction in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/indexer.py`: Parse `data/derived/implicit_failure_subset.jsonl`, extract the injected error patterns, map them to tool identifiers, and save to `data/derived/failure_signatures.json`. JSON Schema: `{"tool_id": "pattern", "recovery_strategy": "replan"}`.

### Prerequisite Tests (Phase 2 Sub-phase)

**Goal**: Ensure data generation logic is correct before implementation.

- [ ] T010 [P] [US1] Contract test for data loader in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/unit/test_loader.py` (verifies PlanBench-XL subset loading from `data/derived/implicit_failure_subset.jsonl`)
- [ ] T011 [P] [US1] Integration test for baseline agent execution in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/integration/test_baseline_agent.py` (verifies log generation without signature index)
- [ ] T015 [P] [US2] Unit test for synthetic failure injection logic in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/unit/test_injector.py` (verifies deterministic pattern injection)
- [ ] T016 [P] [US2] Unit test for signature index construction in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/unit/test_indexer.py` (verifies static JSON index creation)

**Checkpoint**: Foundation and Synthetic Data ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Agent Implementation (Priority: P1) 🎯 MVP

**Goal**: Execute baseline agent on implicit failure subset to establish performance baseline.

**Independent Test**: The system generates a JSON execution log containing the final task status (success/failure) for each task in the subset, validated against the ground truth.

### Implementation for User Story 1

- [ ] T012 [US1] Implement baseline agent in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/agents/baseline.py` using internal LLM reasoning only (no external index access). **Model**: Llama-3-8B-Quantized (4-bit if available on CPU, else 8-bit), **Params**: max_tokens=512, temperature=0.7.
- [ ] T013 [US1] Implement baseline execution runner in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/run_baseline.py` to process `data/derived/implicit_failure_subset.jsonl` and write logs to `data/logs/baseline_execution.jsonl`
- [ ] T014 [US1] Add validation to ensure baseline agent does NOT access `data/derived/failure_signatures.json` (enforces isolation) - **Note**: This task depends on T012/T013 completion.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Augmented Agent Implementation (Priority: P1)

**Goal**: Execute augmented agent with signature retrieval on the same subset.

**Independent Test**: The system detects known implicit failures via the JSON index, triggers recovery, and logs the outcome with a flag indicating signature usage.

### Implementation for User Story 2

- [ ] T018 [US2] Implement augmented agent in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/agents/augmented.py` with string-matching check against `data/derived/failure_signatures.json` post-invocation. **Matching**: Exact string match or regex if pattern contains wildcards. **Threshold**: 100% match required to trigger recovery.
- [ ] T019 [US2] Implement recovery strategy logic in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/agents/augmented.py` (re-plan or tool substitution, NOT returning ground truth directly)
- [ ] T020 [US2] Implement augmented execution runner in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/run_augmented.py` to process `data/derived/implicit_failure_subset.jsonl` and write logs to `data/logs/augmented_execution.jsonl`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison (Priority: P2)

**Goal**: Compute success rates and perform statistical significance testing.

**Independent Test**: The system outputs a summary report with success rates, test statistic, p-value, and a conclusion on hypothesis validity.

### Implementation for User Story 3

- [ ] T021 [P] [US3] Unit test for statistical analysis in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/unit/test_stats.py` (verifies z-test and Fisher calculation logic)
- [ ] T022 [P] [US3] Integration test for report generation in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/integration/test_analysis_report.py`
- [ ] T023 [P] [US3] Implement statistical analysis module in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/analysis/stats.py`: **Logic**: Count events from logs. If n < 30, use `scipy.stats.fisher_exact`; otherwise, use `scipy.stats.proportions_ztest`. Output p-value and test type.
- [ ] T024 [US3] Implement log parser in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/analysis/log_parser.py` to aggregate success/failure counts from `data/logs/baseline_execution.jsonl` and `data/logs/augmented_execution.jsonl` for input to the statistical test (conditional logic in T023).
- [ ] T025 [US3] Implement report generator in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/analysis/report.py` to output final results (success rates, difference, p-value, test type, conclusion) to `data/results/final_report.json`
- [ ] T026 [US3] Implement main experiment runner in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/run_experiment.py` to orchestrate: Load -> Inject/Index -> Baseline Run -> Augmented Run -> Analysis -> Report

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Documentation updates in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/README.md` and `quickstart.md`
- [ ] T029a [P] Code cleanup: Replace hardcoded paths in `code/agents/` with config loader keys from `code/utils/config.py`
- [ ] T029b [P] Code cleanup: Replace hardcoded paths in `code/analysis/` with config loader keys from `code/utils/config.py`
- [ ] T029c [P] Code cleanup: Verify all paths in `code/` use config loader; run linting (flake8, black)
- [ ] T030a [P] Performance optimization: Set LLM inference batch size to a minimal value to ensure memory safety on a constrained RAM limit (CPU-only)
- [ ] T030b [P] Performance optimization: Verify memory usage stays within acceptable limits during execution via monitoring script
- [ ] T031 [P] Additional unit tests for edge cases (corrupted data, API timeout handling) in `tests/unit/`
- [ ] T032 Run `quickstart.md` validation to ensure end-to-end reproducibility within 6 hours

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1 & 2

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for data loader in tests/unit/test_loader.py"
Task: "Integration test for baseline agent execution in tests/integration/test_baseline_agent.py"

# Launch all tests for User Story 2 together:
Task: "Unit test for synthetic failure injection logic in tests/unit/test_injector.py"
Task: "Unit test for signature index construction in tests/unit/test_indexer.py"
Task: "Integration test for augmented agent detection in tests/integration/test_augmented_agent.py"
```

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
- **CRITICAL**: Do NOT fabricate data. All tasks must consume the real PlanBench-XL dataset (downloaded via `loader.py`) and the synthetically injected patterns (deterministic via `injector.py`). The "implicit failure" subset must be derived from the real dataset's ground truth, not simulated from `random` values.
- **CRITICAL**: Ensure the LLM used for agents is CPU-tractable (e.g., quantized 4-bit/8-bit if available on CPU, or a smaller model like Llama-3-8B on CPU) to fit within 7GB RAM and 6-hour runtime. Avoid CUDA-specific code.
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: The statistical analysis MUST use a conditional test: Fisher's Exact if n < 30, otherwise two-proportion z-test.