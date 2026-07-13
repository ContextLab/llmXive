# Tasks: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Input**: Design documents from `/specs/001-llmxive-memory-optimization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`)
- [ ] T002 Initialize Python project with dependencies (`pandas`, `numpy`, `scipy`, `networkx`, `requests`, `tqdm`, `pyyaml`, `llama-cpp-python`) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement robust graph construction and noise injection utilities in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/graph_utils.py`
- [ ] T005 [P] Implement core LLM inference engine wrapper using `llama-cpp-python` (CPU only) with a **quantized model (e.g., Phi-3-mini-Q4_K_M)** for **real inference** (NO mocks) and **logging token counts and latency** as primary metrics in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/engine.py`
- [ ] T006 Implement hard timeout enforcement logic (30 min/task) that logs the timeout event and **proceeds to the next task without hanging** in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/engine.py`
- [ ] T007 Create base data structures for Task, Memory Graph, and Execution Log in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/__init__.py`
- [ ] T008 [P] Setup unit test framework (`pytest`) and configure `tests/` directory structure

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Active Reconstruction Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the "Full" active reconstruction strategy on LoCoMo benchmark tasks to establish a ground-truth baseline.

**Independent Test**: The system runs the baseline algorithm on a fixed subset of LoCoMo tasks and outputs a CSV containing `task_id`, `accuracy`, `nodes_visited`, and `inference_time_seconds`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Unit test for "Full" traversal logic on a synthetic small graph in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_strategies.py`
- [ ] T010 [P] [US1] Integration test for baseline execution pipeline with timeout handling in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement data download script to fetch LoCoMo benchmark subset and synthetic noisy graph dataset from public URLs in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/download_data.py`
- [ ] T012 [US1] Implement "Full" active reconstruction algorithm (traverse entire relevant subgraph) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/full_reconstruction.py`
- [ ] T013 [US1] Implement baseline execution runner that logs `task_id`, `accuracy`, `nodes_visited`, `latency_ms` to `data/processed/baseline_results.csv`
- [ ] T014 [US1] Add robust error handling for disconnected graphs and degenerate inputs in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/full_reconstruction.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heuristic Strategy Comparison (Priority: P2)

**Goal**: Execute "Greedy" and "Lazy" traversal strategies on the same benchmark tasks to quantify efficiency/accuracy trade-offs.

**Independent Test**: The system runs the two heuristic implementations and generates a comparison report showing accuracy delta and efficiency gain relative to the P1 baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T015 [P] [US2] Unit test for "Lazy" traversal logic with evidence threshold in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_strategies.py`
- [ ] T016 [P] [US2] Unit test for "Greedy" traversal logic with top-k selection in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_strategies.py`

### Implementation for User Story 2

- [ ] T017 [US2] Implement "Lazy" traversal heuristic (defer edge expansion until threshold) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/lazy_traversal.py`
- [ ] T018 [US2] Implement "Greedy" traversal heuristic (select top-k confidence edges) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/greedy_traversal.py`
- [ ] T019 [US2] Implement execution runners for Lazy and Greedy strategies logging to `data/processed/lazy_results.csv` and `data/processed/greedy_results.csv`
- [ ] T020 [US2] Implement sensitivity analysis sweep for **Lazy heuristic evidence threshold** (values **0.5, 0.7, 0.9**) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/partial_traversal.py`
- [ ] T021 [US2] Add logic to handle "unreachable target" cases by defaulting to full traversal or flagging "unresolved" in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/lazy_traversal.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Threshold Analysis (Priority: P3)

**Goal**: Perform statistical hypothesis testing and correlation analysis to validate research hypotheses.

**Independent Test**: The system ingests results CSVs and generates a statistical report containing p-values, confidence intervals, and correlation coefficients.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US3] Unit test for paired t-test/Wilcoxon implementation on mock data in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_stats.py`
- [ ] T023 [P] [US3] Unit test for Pearson correlation calculation in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T024 [US3] Implement statistical analysis script (paired t-test/Wilcoxon) comparing heuristic vs. baseline accuracy on the LoCoMo dataset in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/analysis/stats.py`
- [ ] T024b [US3] Implement robustness check: paired t-test/Wilcoxon on the **synthetic noisy graph dataset** comparing heuristic vs. baseline to verify reduced-depth strategies do not fail under perturbation, outputting `data/processed/noisy_graph_stats.csv` in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/analysis/stats.py`
- [ ] T025 [US3] Implement correlation analysis script (Pearson) between traversal depth and success rate in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/analysis/stats.py`
- [ ] T026 [US3] Implement report generator to output p-values, test statistics, and inflection points to `docs/results.md`
- [ ] T027 [US3] Add logic to identify the specific complexity threshold where **accuracy drops below 95% of the baseline** (if statistically significant) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/analysis/stats.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T028 [P] Documentation updates in `docs/` and `README.md`
- [ ] T029 Code cleanup and refactoring of strategy modules
- [ ] T030 Performance optimization for graph traversal loops
- [ ] T031 [P] Additional unit tests for edge cases (zero edges, single node) in `tests/unit/`
- [ ] T032 Run `quickstart.md` validation and verify all results are reproducible

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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for 'Full' traversal logic on a synthetic small graph in projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_strategies.py"
Task: "Integration test for baseline execution pipeline with timeout handling in projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement data download script to fetch LoCoMo benchmark subset and synthetic noisy graph dataset from public URLs in projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/download_data.py"
Task: "Implement 'Full' active reconstruction algorithm (traverse entire relevant subgraph) in projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/full_reconstruction.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
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