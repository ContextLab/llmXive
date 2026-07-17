# Tasks: llmXive follow-up: extending "Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages"

**Input**: Design documents from `/specs/001-llmxive-multilingual-logic-transfer/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

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

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  
  The /speckit-tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/`
- [ ] T002 Initialize Python project with `requirements.txt` dependencies (llama-cpp-python, datasets, scipy, pandas, pyyaml, pytest, joblib)
- [ ] T003 [P] **Model Feasibility Gate**: Implement `code/feasibility_gate.py` to measure token throughput of the 1.1B GGUF model on the target runner. **Mandatory Fallback**: If throughput < 2 tokens/sec, the task MUST switch the configuration to the 3B model and reduce the target task set to 50 items. Output: `data/feasibility_log.json` with binary decision (proceed/fallback), measured throughput, and final configuration.
- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Data Preparation & Filtering (Blocking Prerequisites)

**Purpose**: Core data infrastructure, filtering, and baseline establishment. MUST be complete before ANY user story execution.

**⚠️ CRITICAL**: No user story work (Phase 3/4) can begin until this phase is complete. All downstream tasks depend on `data/final_tasks.json`.

- [ ] T005 [P] Create `code/config.py` to manage paths, random seeds, and model configurations
- [ ] T006 [P] Create `data/raw/` and `data/processed/` directory structure with checksum tracking
- [ ] T007 [P] Setup error logging infrastructure in `code/utils/logger.py`
- [ ] T008 [P] Implement `code/dataset.py` for loading Multi-LCB parquet files from HuggingFace and verifying checksums
- [ ] T009 [P] Implement `code/dataset.py` stratification logic (Difficulty, Topic, Language Pair) per FR-006
- [ ] T010 [P] Implement `code/sandbox.py` **full execution harness** with strict timeout enforcement per test case (FR-003). **Do not implement as a skeleton.**
- [ ] T016 [P] [US1] **Static Pool Selection**: Implement `code/dataset.py` to select the initial pool of tasks where the model previously failed in the target language (blind Pass@1 < 1.0) AND succeeded in Python. **Must include logic for sampling replacements** if the initial pool is insufficient to meet the final target after filtering. Output: `data/initial_pool.json`.
- [ ] T017 [P] [US1] **Stochasticity Filter Execution**: Implement `code/dataset.py` to orchestrate multiple blind runs per task in `data/initial_pool.json` and include only tasks that fail in ≥2 of 3 runs. Output: `data/filtered_tasks.json`.
- [ ] T018 [P] [US1] **Attrition Handling**: Implement `code/dataset.py` to sample replacements from the next available pool (excluding rejected tasks) if `data/filtered_tasks.json` contains < 200 items, maintaining stratification by Difficulty/Topic. **Explicitly implement the replacement sampling logic** to ensure the final set reaches the target count. Output: `data/final_tasks.json`.
- [ ] T039 [P] [US3] **Record Baseline Metrics**: Implement `code/stats.py` to calculate and write the empirical baseline Pass@1 for the **final filtered set** (`data/final_tasks.json` from T018) to `data/blind_baseline.yaml`. **Schema**: `{pass_count: int, total_count: int, pass_rate: float, filtered_task_ids: list}`. **Depends on T018**.

**Checkpoint**: Data ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Logic Anchor Inference (Priority: P1) 🎯 MVP

**Goal**: Extract Partial Logic Traces from Python ground truth and construct guided prompts for target languages.

**Independent Test**: The system can be tested by running the inference pipeline on a single, **pre-filtered** task from the dataset, verifying that the model outputs a syntactically valid code snippet in the target language when provided the Partial Logic Trace.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T011 [P] [US1] Unit test for AST parsing logic in `tests/unit/test_logic_anchor.py`
- [ ] T012 [P] [US1] Unit test for prompt construction in `tests/unit/test_prompt_builder.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `code/logic_anchor.py`: Parse ground-truth Python solutions into AST, extract first algorithmic steps (FR-001.1). **Mandatory Error Handling**: If the Python solution is too short to extract a sufficient number of steps, the task MUST skip the entry, log "Anchor Extraction Failed", and remove the task from the active processing list (Edge Case).
- [ ] T014 [P] [US1] Implement `code/logic_anchor.py`: Serialize extracted steps into pseudo-code/Python anchor strings.
- [ ] T015 [US1] Implement `code/prompt_builder.py`: Construct few-shot prompts including problem statement, failed output, and Partial Logic Trace (FR-001). **Dependency**: Model must be loaded successfully (T003 passed).
- [ ] T016 [US1] Implement `code/inference.py`: Load **standard CPU quantization model (e.g., GGUF quantized format via llama-cpp-python)** and generate target language code given the prompt. **NO bitsandbytes/8-bit/4-bit CUDA quantization allowed.** **Prerequisite**: T003 (Feasibility Gate) must have passed.

**Checkpoint**: At this point, User Story 1 (excluding the stochasticity filter) should be fully functional and testable with mocked data

---

## Phase 4: User Story 2 - Automated Execution & Pass@1 Verification (Priority: P2)

**Goal**: Execute generated code in a sandboxed environment, verify correctness, and categorize errors.

**Independent Test**: The system can be tested by feeding a known correct Rust solution into the execution harness and verifying that the test suite passes, and conversely, that a syntactically broken solution fails the harness.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for timeout enforcement in `tests/unit/test_sandbox.py`
- [ ] T018 [P] [US2] Unit test for error log parsing (Syntax, Runtime, Library) in `tests/unit/test_sandbox.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/sandbox.py`: Full execution harness for Rust/Kotlin/Go with strict timeout per test case (FR-003).
- [ ] T020 [US2] Implement `code/sandbox.py`: Parse execution logs to detect "Compile Error", "Runtime Error", "Timeout", "Segmentation fault".
- [ ] T021 [P] [US2] Implement `code/inference_runner.py`: Run blind and guided conditions on the **final filtered dataset** (`data/final_tasks.json` from T018). **Dependency**: T018 (Final Dataset), T016 (Inference).
- [ ] T022 [P] [US2] Implement `code/parallel_executor.py`: Parallelize execution using `joblib` to maximize CPU usage within 6h limit.
- [ ] T023 [US2] Implement `code/orchestrator.py`: **Orchestration logic** for time/resource management (dynamic task skipping, resource monitoring) to ensure ≤6h runtime (SC-004).
- [ ] T024 [US2] **Logic Transfer Failure Detection**: Implement `code/error_categorizer.py`. **Mandatory Valid Alternative Check**: Verify generated code implements anchor steps via **keyword/control-flow matching** against the Partial Logic Trace (from T013/T014). **Crucially, exclude cases where code passes tests but uses a standard library function encapsulating the anchor steps**; in such cases, mark as "Pass" or "Library Misuse", NOT "Logic Transfer Failure" (FR-004). **Depends on T021 (Guided Runs output)**.
- [ ] T025 [US2] Implement `code/stats.py`: Binary Pass/Fail determination logic based on test suite outcomes.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Error Categorization (Priority: P3)

**Goal**: Compare Pass@1 rates using paired statistical tests and categorize failure modes.

**Independent Test**: The system can be tested by feeding it a pre-computed dataset of paired Pass/Fail results and verifying that the statistical test returns a p-value and that error categories are assigned based on the failure logs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for McNemar's test implementation in `tests/unit/test_stats.py`
- [ ] T027 [P] [US3] Unit test for error categorization logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/stats.py`: Categorize failures into Syntax, Library Misuse, Runtime Error, Logic Transfer Failure (FR-004).
- [ ] T029 [US3] Implement `code/stats.py`: Perform paired McNemar's test on blind vs. guided Pass/Fail outcomes (FR-005).
- [ ] T030 [US3] Implement `code/stats.py`: Calculate primary Pass@1 metrics (Passes / Total) and Recovery Rate (SC-001). **Note**: This task calculates the primary metric defined in SC-001, distinct from derived metrics.
- [ ] T031 [US3] Implement `code/main.py`: Generate `data/statistical_report.yaml` with p-values, metrics, and error distribution.
- [ ] T032 [US3] Implement `code/main.py`: Generate `data/results.csv` mapping task IDs to blind/guided status and error types.
- [ ] T033 [US3] Validate execution time: Verify total pipeline runtime ≤ 6 hours on GitHub Actions free-tier (SC-004) (Depends on T023).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates: Update `README.md` with run instructions and fallback strategy details
- [ ] T035 Code cleanup and refactoring for `code/` directory
- [ ] T036 [P] Run full integration test suite in `tests/integration/test_pipeline.py`
- [ ] T037 Verify data hygiene: Ensure `data/raw/` checksums match source and `data/processed/` are derived correctly
- [ ] T038 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Data Prep (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Data Prep (Phase 2) completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Data Prep (Phase 2) - No dependencies on other stories (uses `data/final_tasks.json` for initial test)
- **User Story 2 (P2)**: Can start after Data Prep (Phase 2) - Depends on US1 for prompt generation and logic anchor artifacts (T013/T014) and consumes `data/final_tasks.json`
- **User Story 3 (P3)**: Can start after Data Prep (Phase 2) - Depends on US2 for execution results and baseline metrics

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Data Prep tasks marked [P] can run in parallel (within Phase 2)
- Once Data Prep phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for AST parsing logic in tests/unit/test_logic_anchor.py"
Task: "Unit test for prompt construction in tests/unit/test_prompt_builder.py"

# Launch all models for User Story 1 together:
Task: "Implement code/logic_anchor.py: Parse ground-truth Python solutions..."
Task: "Implement code/logic_anchor.py: Serialize extracted steps into pseudo-code..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Data Prep (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (using `data/final_tasks.json`)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Data Prep → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Data Prep together
2. Once Data Prep is done:
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
- **Critical Data Flow**: T003 (Feasibility) -> T016 (Static Pool) -> T017 (Stochastic Filter) -> T018 (Attrition) -> T039 (Baseline) -> T013/T014 (Anchor) -> T021 (Runs) -> T024 (Analysis) -> T029 (Stats)