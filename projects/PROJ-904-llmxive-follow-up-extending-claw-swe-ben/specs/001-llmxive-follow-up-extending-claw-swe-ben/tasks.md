# Tasks: llmXive Follow-up: Context Fidelity vs. Model Scaling Trade-offs

**Input**: Design documents from `/specs/001-context-fidelity-scaling-tradeoff/`
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

- [ ] T001 Create directory structure per implementation plan in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/`: `data/`, `models/`, `experiments/`, `analysis/`, `tests/`.
- [ ] T002 Create `__init__.py` files for all new directories in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/`.
- [ ] T003 Initialize Python 3.11 project with `transformers`, `datasets`, `scikit-learn`, `statsmodels`, `networkx`, `pytest`, and `huggingface_hub` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/requirements.txt`.
- [ ] T004 Create `.ruff.toml` and `pyproject.toml` with black settings in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` for linting and formatting.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Configure random seeds to be hardcoded in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/config.py` (Constitution Principle I).
- [X] T004b [P] [US1, US2, US3] Implement explicit random seed pinning in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_baseline.py` and `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_high_fidelity.py` (Constitution Principle I) to ensure reproducibility even if config is decoupled.
- [X] T005 [P] Implement deterministic logging and error handling infrastructure in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/__init__.py`
- [X] T006a Create base data models (Python classes for Task Instance, Context Configuration, Execution Result) in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/config.py`
- [ ] T006b Create entity schemas (YAML files) for Task Instance, Context Configuration, Execution Result in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/specs/001-context-fidelity-scaling-tradeoff/contracts/`
- [X] T007 Setup environment variable management for model paths and HF token in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/config.py`
- [X] T008a [P] [US1, US2, US3] **Define** the schema validation logic and aggregation schema in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/merge_results.py`. **Constraint**: This task must ONLY define the logic and schema; it must NOT execute the merge until Phase 5 (T008b). This ensures format compatibility (FR-005) before data generation tasks (T016, T023, T027) run.
- [ ] T008b [US3] **Execute** `merge_results.py` to aggregate all JSONL files (`baseline_run.jsonl`, `hf_run_1b.jsonl`, `hf_run_7b.jsonl`) into a single `data/results.csv` (Single Source of Truth) (FR-005). **Constraint**: This task must run AFTER all data generation tasks (T016, T023, T027) are complete. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Context-Bound Task Filtering and Baseline Execution (Priority: P1) 🎯 MVP

**Goal**: Filter Claw-SWE-Bench for high-complexity instances (>500 lines) and execute a naive baseline with a large-scale model.

**Independent Test**: Run the filtering script on the raw dataset and verify the output contains only instances with >500 lines of relevant file history, then execute a single instance with the baseline model.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Note: T010 depends on logic in T013.**

- [X] T010 [P] [US1] Unit test for import graph traversal logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_loader.py`
- [X] T011 [P] [US1] Integration test for baseline execution timeout in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/integration/test_baseline_execution.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `ClawSweBenchLoader` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py` using `datasets.load_dataset(..., streaming=True)` to fetch from Hugging Face. **Rule**: Fail loudly if fetch fails; do NOT generate synthetic data.
- [ ] T012b [US1] Implement logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py` to write the *filtered* dataset (instances >500 lines) to a versioned file (e.g., `data/filtered_swe_bench_v1.parquet`) and record its checksum in `state/` (Constitution Principle III).
- [X] T013 [US1] Implement static analysis logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py` to calculate "relevant file history" lines: 1) Parse Python imports to build a dependency graph using `networkx`, 2) Perform BFS/DFS traversal from the issue target files, 3) Filter for instances where the The total lines in the traversed graph exceed a significant threshold. (FR-001).
- [X] T014 [US1] Implement "first-N-lines" naive truncation strategy in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` (FR-002).
- [X] T015 [US1] Implement `ModelRunner` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/runner.py` to load a parameter-scaled model (e.g., Llama-3) with Q4_K_M quantization on CPU (FR-002).
- [ ] T016 [US1] Implement `run_baseline.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` to execute the filtered dataset with the 1B model and naive strategy. **Constraint**: Enforce -minute runtime budget per instance via `batch_executor.py`. Output `data/intermediate/baseline_run.jsonl` (US-1).
- [ ] T016b [P] [US1] Implement `batch_executor.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` with logic to enforce: 1) A hard timeout per instance, and 2) A hard total wall-clock duration limit of ≤72 hours for the full experiment (FR-007).
- [ ] T017 [US1] Implement `failure_classifier.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/` to detect "missing context" vs "reasoning error" via sandbox log parsing (FR-008).
- [ ] T017b [US1] Apply `failure_classifier.py` to the baseline results (`data/intermediate/baseline_run.jsonl`) to annotate failure modes for US1 results. <!-- ATOMIZE: requested -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - High-Fidelity Context Strategy Integration (Priority: P2)

**Goal**: Implement and integrate three context compression modules (TF-IDF, Diff-Aware, Semantic Summarization) and execute them with the 1B model.

**Independent Test**: Run a single high-fidelity strategy (e.g., TF-IDF) on a subset and verify the context differs from baseline and produces a different output.

### Shared Model Update

- [X] T026 [US3] Update `ModelRunner` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/models/runner.py` to support loading a large-scale model (e.g., Llama-3-8B) with Q4_K_M quantization, handling memory pressure via aggressive quantization or termination flags (FR-004, Edge Case). *Note: This must complete before T023/T027 execution tasks.*

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for TF-IDF/BM25 retrieval logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_context_processors.py`
- [X] T019 [P] [US2] Unit test for diff-aware sliding window logic in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_context_processors.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement TF-IDF/BM25 relevance retrieval module in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` using `scikit-learn` (FR-003).
- [X] T021 [P] [US2] Implement diff-aware sliding window module in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` using standard diff libraries (FR-003).
- [X] T022 [P] [US2] Implement rule-based semantic summarization module in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/context_processors.py` as defined in FR-003 (rule-based extraction of relevant code blocks/paragraphs).
- [ ] T023 [US2] Implement `run_high_fidelity.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` to execute the 1B model against all three high-fidelity strategies. **Constraint**: Enforce 60-minute runtime budget per instance and use parallel batching. Output `data/intermediate/hf_run_1b.jsonl` (US-2).
- [ ] T024 [US2] Implement fallback logic in `context_processors.py` to revert to naive truncation if a high-fidelity strategy returns zero snippets, logging the event to `data/audit_logs/fallbacks.jsonl` (Edge Case Handling).
- [ ] T017c [US2] Apply `failure_classifier.py` to the high-fidelity results (`data/intermediate/hf_run_1b.jsonl`) to annotate failure modes for US2 results. <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Scaling Comparison and Interaction Analysis (Priority: P3)

**Goal**: Repeat experiments with a 7B model and perform GLM analysis to test for interaction effects.

**Independent Test**: Run the 7B model on baseline and high-fidelity configurations, compare Pass@1 curves, and verify the GLM analysis runs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Write test scaffolding for GLM interaction effect calculation in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_glm_analyzer.py`.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `run_high_fidelity.py` logic (or new script) to execute the 7B model against all strategies (Baseline, TF-IDF, Diff-Aware, Summarization). **Constraint**: Enforce 60-minute runtime budget per instance and use parallel batching. Output `data/intermediate/hf_run_7b.jsonl` (US-3). *Dependency: Must complete T026 first.*
- [ ] T028 [US3] Execute `merge_results.py` (T008b) to aggregate all JSONL files (`baseline_run.jsonl`, `hf_run_1b.jsonl`, `hf_run_7b.jsonl`) into a single `data/results.csv` (Single Source of Truth) (FR-005). *Note: Logic was implemented in Phase 2 (T008a); this task executes the merge.*
- [ ] T029 [US3] Implement `glm_analyzer.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/` to perform a Generalized Linear Model (GLM) with binomial link to test for interaction effects between "context strategy" and "model size" (FR-006, US-3).
- [ ] T030 [US3] Implement post-hoc pairwise comparison logic in `glm_analyzer.py`. **Requirement**: Explicitly calculate the difference in Pass@1 rates between the 1B-model (high-fidelity) and 7B-model (baseline) for each strategy; identify if any strategy shows a margin ≥5% with p < 0.05 (SC-004).
- [ ] T017d [US3] Apply `failure_classifier.py` to the 7B results (`data/intermediate/hf_run_7b.jsonl`) to annotate failure modes for US3 results.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`.
- [ ] T036 Code cleanup and refactoring of `context_processors.py`.
- [ ] T037 [P] Performance optimization: Fine-tune parallel batching parameters in `batch_executor.py` in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/` to ensure robustness of the 72h total wall-clock budget (FR-007).
- [ ] T038 [P] Additional unit tests for edge cases (empty context, timeout) in `tests/unit/`.
- [ ] T039 [P] Run checksum generation and recording for ALL data artifacts: `data/results.csv`, `data/intermediate/baseline_run.jsonl`, `data/intermediate/hf_run_*.jsonl`, and the filtered dataset. Record hashes in `state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml` (Constitution Principle III).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Relies on `context_processors.py` structure but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Relies on `ModelRunner` updates (T026) and `merge_results.py` (T008a/T008b) but independently testable

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
Task: "Write test scaffolding for import graph traversal logic in projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/unit/test_loader.py"
Task: "Write test scaffolding for baseline execution timeout in projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/tests/integration/test_baseline_execution.py"

# Launch all models for User Story 1 together:
Task: "Implement ClawSweBenchLoader in projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py"
Task: "Implement issue description parsing logic in projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py"
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