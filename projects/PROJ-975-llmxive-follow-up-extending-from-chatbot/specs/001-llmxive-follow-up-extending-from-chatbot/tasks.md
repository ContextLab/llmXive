# Tasks: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

**Input**: Design documents from `specs/001-llmxive-scaling/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `requirements.txt`)
- [ ] T002 Initialize Python 3.11 project with `scikit-learn`, `sentence-transformers`, `pandas`, `numpy`, `pytest`, `transformers` dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003.5 [P] Update `specs/001-llmxive-follow-up-extending-from-chatbot/spec.md` to formally document and apply the deviation for FR-004: Change pruning logic from `similarity > 0.85` to `similarity < 0.15 OR usage == 0` (per plan scientific correction)
- [ ] T003.6 [P] Update `specs/001-llmxive-follow-up-extending-from-chatbot/spec.md` to formally document and apply the deviation for SC-004: Change statistical method from `One-way ANOVA` to `Piecewise Regression` (per plan methodological correction)
- [ ] T003.7 [P] Update `specs/001-llmxive-follow-up-extending-from-chatbot/spec.md` to formally document the substitution of "human-annotated" labels with "Synthetic Oracle + LLM-as-a-Judge" proxy for FR-005/SC-002, including the verification step for proxy validity
- [ ] T004 Implement `code/config.py` with pinned random seeds, file paths, and experimental thresholds (similarity < 0.15, usage == 0) as updated in T003.5, referencing the spec deviation note
- [ ] T005 [P] Setup `data/` directory structure (`raw/`, `processed/`) and `data/checksums.txt` initialization
- [ ] T006 [P] Create base `code/__init__.py` and logging infrastructure in `code/logging_config.py`
- [ ] T007 Implement `code/validation/judge.py` (LLM-as-a-Judge) to generate independent ground truth relevance labels for validation sets, ensuring compliance with the proxy validation defined in T003.7
- [ ] T008 Implement `code/generators/synthetic_oracle.py` to generate deterministic "human-annotated" style labels for the validation subset, ensuring compliance with the proxy validation defined in T003.7
- [ ] T009 Setup `code/agents/retriever.py` skeleton with `sentence-transformers` (CPU-only) embedding loading logic

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Task Generation and Skill Library Construction (Priority: P1) 🎯 MVP

**Goal**: Generate a reproducible synthetic environment of a substantial set of multi-step tasks and a configurable library of overlapping Python skills.

**Independent Test**: Verify that the generated task CSV contains a sufficient volume of unique, executable multi-step instructions and the skill library contains a representative set of distinct functions with programmatically generated semantic overlap, independent of agent execution.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for task generator output schema in `tests/unit/test_task_generator.py`
- [ ] T011 [P] [US1] Contract test for skill library embedding distribution in `tests/unit/test_skill_generator.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/generators/task_generator.py` to produce 500 synthetic multi-step tasks (3-5 actions each) with deterministic action sequences and semantic obfuscation
- [ ] T013 [P] [US1] Implement `code/generators/skill_generator.py` to construct 100 Python functions with controlled semantic overlap (embedding similarity distribution)
- [ ] T014 [US1] Implement `code/agents/retriever.py` to compute embeddings for the generated skill library using `all-MiniLM-L6-v2` on CPU, calculate cosine similarity scores between tasks and skills, and ensure no bitwise identical functions exist (merges embedding computation and similarity calculation)
- [ ] T015 [US1] Add validation logic to `code/generators/task_generator.py` to ensure tasks are independent of the specific skill set used for training
- [ ] T016 [US1] Add logging for task and skill generation metrics in `code/logging_config.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Data generation complete)

---

## Phase 4: User Story 2 - Agent Execution and Metric Collection (Priority: P2)

**Goal**: Execute the "Digital Colleague" agent across the synthetic tasks using varying active skill library sizes (10, 30, 50, 100) and record performance metrics.

**Independent Test**: Run the agent with a fixed library size against the 500 tasks and verify a results log is produced containing success/failure flags, token counts, and execution timestamps.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for execution log schema in `tests/unit/test_executor.py`
- [ ] T018 [P] [US2] Integration test for full task suite execution with timeout handling in `tests/integration/test_execution_loop.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/agents/executor.py` to run the agent loop with a configurable active skill library size
- [ ] T020 [US2] Implement `code/agents/executor.py` to enforce a strict 120-second timeout per task and record timeout events as failures
- [ ] T021 [US2] Implement `code/agents/executor.py` to log task success rate, total token usage, and average latency per task for each configuration
- [ ] T022 [US2] Integrate `code/agents/retriever.py` with `code/agents/executor.py` to filter the active library based on the current workspace state
- [ ] T023 [US2] Implement `code/analysis/metrics.py` to calculate retrieval precision@k against the held-out validation set (generated by T007/T008)
- [ ] T024 [US2] Implement `code/agents/executor.py` to log "false prune" events when a removed skill was required for a subsequent task (by comparing removed skills against requirements of subsequent failing tasks)
- [ ] T025 [US2] Add error handling for "missing skill" failures (task has no matching skill) and implement logic to detect "false prune" events by comparing the set of removed skills against the required skills of subsequent failing tasks
- [ ] T026 [US2] Implement `code/main.py` orchestration to sweep library sizes (10, 30, 50, 100) and write aggregated results to `data/processed/`
- [ ] T027 [US2] Implement `code/analysis/visualizer.py` to generate plots comparing performance across library sizes

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Data generation and Execution complete)

---

## Phase 5: User Story 3 - Pruning Heuristic Evaluation (Priority: P3)

**Goal**: Implement and evaluate a "Skill Pruning" heuristic that removes unused or redundant skills, measuring performance recovery.

**Independent Test**: Run the agent with a large-scale skill library and pruning enabled, then compare success rates and latency against a non-pruned baseline.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for pruning logic output in `tests/unit/test_pruning.py`
- [ ] T029 [P] [US3] Integration test for pruning cycle and performance recovery in `tests/integration/test_pruning_heuristic.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `code/heuristics/pruning.py` to remove skills with usage count == 0 OR cosine similarity < 0.15 (Corrected logic per T003.5 and updated spec)
- [ ] T031 [US3] Implement `code/heuristics/pruning.py` to trigger pruning after every periodic batch of tasks and implement logic to detect "false prune" events by comparing the set of removed skills against the required skills of subsequent failing tasks
- [ ] T032 [US3] Implement `code/agents/executor.py` to log "false prune" events when a removed skill was required for a subsequent task (by comparing removed skills against requirements of subsequent failing tasks)
- [ ] T033 [US3] Implement `code/analysis/metrics.py` to perform Piecewise Regression (per T003.6 and updated spec) to identify the threshold of diminishing returns
- [ ] T034 [US3] Implement `code/analysis/metrics.py` to calculate performance recovery (success rate/latency) of the pruned condition vs. unpruned baseline
- [ ] T035 [US3] Implement `code/analysis/visualizer.py` to generate plots comparing pruned vs. unpruned performance
- [ ] T036 [US3] Add logging for pruning events and false-positive rates in `code/logging_config.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (quickstart.md, research.md)
- [ ] T038 Code cleanup and refactoring of `code/` modules
- [ ] T039 Performance optimization for embedding calculations and retrieval search space
- [ ] T040 [P] Additional unit tests for edge cases (timeout, missing skill) in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure full reproducibility
- [ ] T042 Verify `data/checksums.txt` integrity for all generated datasets

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T012/T013 (Data) being generated
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T019/T021 (Execution) being functional

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Generators before Services/Executors
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Generators for T012 and T013 can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for task generator output schema in tests/unit/test_task_generator.py"
Task: "Contract test for skill library embedding distribution in tests/unit/test_skill_generator.py"

# Launch all generators for User Story 1 together:
Task: "Implement code/generators/task_generator.py"
Task: "Implement code/generators/skill_generator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Verify data generation)
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
   - Developer A: User Story 1 (Data Generation)
   - Developer B: User Story 2 (Execution Engine)
   - Developer C: User Story 3 (Pruning Heuristic)
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
- **Critical Constraint**: All embedding and model operations MUST run on CPU (default float32) without CUDA.
- **Critical Constraint**: Pruning logic MUST use `similarity < 0.15 OR usage == 0` (Plan correction, updated in spec via T003.5).
- **Critical Constraint**: All metrics MUST use Piecewise Regression (Plan correction, updated in spec via T003.6).
- **Critical Constraint**: "Human-annotated" labels are satisfied by "Synthetic Oracle + LLM-as-a-Judge" proxy (updated in spec via T003.7).