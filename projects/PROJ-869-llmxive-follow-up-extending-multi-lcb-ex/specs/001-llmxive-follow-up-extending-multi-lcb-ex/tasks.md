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
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `code/config.py` to manage paths, random seeds, and model configurations
- [ ] T005 [P] Implement `code/dataset.py` for loading Multi-LCB parquet files from HuggingFace and verifying checksums
- [ ] T006 [P] Implement `code/dataset.py` stratification logic (Difficulty, Topic, Language Pair) per FR-006
- [ ] T007 Create `data/raw/` and `data/processed/` directory structure with checksum tracking
- [ ] T008 [P] Setup error logging infrastructure in `code/utils/logger.py`
- [ ] T009 [P] Implement `code/sandbox.py` skeleton with subprocess execution and 10s timeout enforcement (FR-003)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Logic Anchor Inference (Priority: P1) 🎯 MVP

**Goal**: Extract Partial Logic Traces from Python ground truth and construct guided prompts for target languages.

**Independent Test**: The system can be tested by running the inference pipeline on a single, **pre-filtered or mocked** task from the dataset, verifying that the model outputs a syntactically valid code snippet in the target language when provided the Partial Logic Trace. (Note: The full filtering logic is implemented in Phase 4).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Unit test for AST parsing logic in `tests/unit/test_logic_anchor.py`
- [ ] T011 [P] [US1] Unit test for prompt construction in `tests/unit/test_prompt_builder.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/logic_anchor.py`: Parse ground-truth Python solutions into AST and extract first 3 algorithmic steps (FR-001.1)
- [ ] T013 [P] [US1] Implement `code/logic_anchor.py`: Serialize extracted steps into pseudo-code/Python anchor strings
- [ ] T014 [US1] Implement `code/prompt_builder.py`: Construct few-shot prompts including problem statement, failed output, and Partial Logic Trace (FR-001)
- [ ] T015 [US1] Implement `code/inference.py`: Load **standard CPU quantization model (e.g., GGUF q4_0 via llama-cpp-python)** and generate target language code given the prompt. **NO bitsandbytes/8-bit/4-bit CUDA quantization allowed.**

**Checkpoint**: At this point, User Story 1 (excluding the stochasticity filter) should be fully functional and testable with mocked data

---

## Phase 4: User Story 2 - Automated Execution & Pass@1 Verification (Priority: P2)

**Goal**: Execute generated code in a sandboxed environment, apply the stochasticity filter, and verify correctness against test suites.

**Independent Test**: The system can be tested by feeding a known correct Rust solution into the execution harness and verifying that the test suite passes, and conversely, that a syntactically broken solution fails the harness.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for timeout enforcement in `tests/unit/test_sandbox.py`
- [ ] T019 [P] [US2] Unit test for error log parsing (Syntax, Runtime, Library) in `tests/unit/test_sandbox.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/sandbox.py`: Full execution harness for Rust/Kotlin/Go with strict 10s timeout per test case (FR-003)
- [ ] T021 [US2] Implement `code/sandbox.py`: Parse execution logs to detect "Compile Error", "Runtime Error", "Timeout", "Segmentation fault"
- [ ] T016 [US2] Implement `code/dataset.py`: **Full filtering logic (Static + Stochastic)** - Select tasks where model failed in target language but succeeded in Python, then **re-run blind condition 3 times** and include only if fails **≥2/3 runs** (FR-006, FR-006.2)
- [ ] T017 [US2] Implement `code/dataset.py`: **Stochasticity Filter Execution** - Orchestrate the 3 blind runs and apply the ≥2/3 failure filter logic to produce the final task set (FR-006.2)
- [ ] T039 [US2] Implement `code/stats.py`: **Record empirical baseline Pass@1** metrics for the filtered dataset to `data/blind_baseline.yaml` (FR-006.1, SC-001)
- [ ] T022 [US2] Implement `code/sandbox.py`: Logic Transfer Failure detection: Verify generated code implements anchor steps via **keyword/control-flow matching** against the Partial Logic Trace artifact produced by **T012/T013** (FR-004)
- [ ] T023 [US2] Implement `code/stats.py`: Binary Pass/Fail determination logic based on test suite outcomes
- [ ] T024 [US2] Implement `code/main.py` orchestration: Run blind and guided conditions on the **final filtered dataset** (from T016/T017) (200 tasks target)
- [ ] T025 [US2] Implement `code/main.py`: Parallelize execution using `joblib` to maximize CPU usage within 6h limit
- [ ] T040 [US2] Implement `code/main.py`: **Orchestration logic for time/resource management** (dynamic task skipping, resource monitoring, parallelization tuning) to ensure ≤6h runtime (SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Error Categorization (Priority: P3)

**Goal**: Compare Pass@1 rates using paired statistical tests and categorize failure modes.

**Independent Test**: The system can be tested by feeding it a pre-computed dataset of paired Pass/Fail results and verifying that the statistical test returns a p-value and that error categories are assigned based on the failure logs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for McNemar's test implementation in `tests/unit/test_stats.py`
- [ ] T027 [P] [US3] Unit test for error categorization logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/stats.py`: Categorize failures into Syntax, Library Misuse, Runtime Error, Logic Transfer Failure (FR-004)
- [ ] T029 [US3] Implement `code/stats.py`: Perform paired McNemar's test on blind vs. guided Pass/Fail outcomes (FR-005)
- [ ] T030 [US3] Implement `code/stats.py`: Calculate LC-Pass@1 metrics (Passes / Total) excluding Logic Transfer Failures
- [ ] T031 [US3] Implement `code/main.py`: Generate `data/statistical_report.yaml` with p-values, metrics, and error distribution
- [ ] T032 [US3] Implement `code/main.py`: Generate `data/results.csv` mapping task IDs to blind/guided status and error types
- [ ] T033 [US3] Validate execution time: Verify total pipeline runtime ≤ 6 hours on GitHub Actions free-tier (SC-004) (Depends on T040)

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
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (uses **mocked/pre-filtered** data for initial test)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for prompt generation and logic anchor artifacts (T012/T013) and **includes the filtering logic** (T016/T017)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for execution results and baseline metrics

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
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (using **mocked/pre-filtered** data)
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
- **Critical Data Flow**: T012/T013 (Anchor) -> T020/T021 (Harness) -> **T016/T017 (Filter)** -> T024 (Final Runs) -> **T039 (Baseline Record)** -> T029 (Stats)