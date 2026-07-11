# Tasks: llmXive follow-up: extending "MemLens"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-memlens-benc/`
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

- [ ] T001 Create project structure per implementation plan: `mkdir -p projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/{code,code/stores,data/raw,data/processed,tests/unit,tests/integration,outputs}` and create empty `__init__.py` files.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` dependencies: Execute `{{claim:c_02b12065}}` and write these exact pinned versions to `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/requirements.txt`. (Note: Do NOT use `pip freeze` to ensure reproducibility).
- [X] T003a [P] Configure linting: Create `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/.ruff.toml` with rules for E, F, W, I, N, UP, B, C4, T20, and ensure `line-length = 88 [UNRESOLVED-CLAIM: c_84459f86 — status=not_enough_info]`.
- [ ] T003b [P] Configure formatting: Create `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/.black` configuration in `pyproject.toml` setting `line-length = 88 [UNRESOLVED-CLAIM: c_84459f86 — status=not_enough_info]` and `target-version = ['py311']`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/config.py` defining: `SEED = 42`, `DATA_PATH = 'data/raw'`, `OUTPUT_PATH = 'outputs'`, `TOP_K = 5`, `BATCH_SIZE = 4 [UNRESOLVED-CLAIM: c_c1228638 — status=not_enough_info]`.
- [ ] T005 [P] Implement `code/data_loader.py` to download MemLens from HuggingFace and filter for `task_type` in ["Multi-Session Reasoning", "Temporal Reasoning"] (FR-001).
- [~] T006 [P] Create `code/stores/__init__.py` and base store interface.
- [~] T007 [P] Implement `code/stores/coarse_store.py` to load text summaries only, discarding all image data (Constitution VI).
- [~] T008 [P] Implement `code/stores/medium_store.py` to load summaries and compute frozen CLIP embeddings for images (Constitution VI).
- [~] T009 [P] Implement `code/stores/fine_store.py` to load summaries and run CPU-optimized YOLOv8n (seed=42) [UNRESOLVED-CLAIM: c_1b328aba — status=not_enough_info] for object captions/bboxes; if object list is empty, return context string "[No objects detected]" (Constitution VI).
- [~] T010 [P] Implement `code/retrieval.py` using `faiss-cpu` for cosine similarity search (FR-003).
- [ ] T011 [P] Implement `code/generator.py` to load a low-bit quantized Llama-3-8B-Instruct on CPU [UNRESOLVED-CLAIM: c_b4949b09 — status=not_enough_info] (no CUDA) for inference (FR-004).
- [ ] T012 [P] Implement `code/profiler.py` to log `latency_ms` and `peak_ram_mb` using `psutil` (FR-005).
- [ ] T013 [P] Implement `code/evaluator.py` to calculate exact match and semantic similarity scores (FR-005).
- [ ] T014 [P] Implement `code/statistics.py` to perform **Wilcoxon Signed-Rank Test** (paired) to compare accuracy distributions across the three store configurations. (Note: Deviates from spec FR-006's ANOVA/Friedman to align with Plan.md's Complexity Tracking which rejects ANOVA for deterministic systems). Implement checkpointing/resume logic and aggressive garbage collection (model unloading) between store runs to ensure peak RAM < 7GB [UNRESOLVED-CLAIM: c_31215486 — status=not_enough_info] (FR-006, SC-005).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Multi-Session Reasoning Evaluation (Priority: P1) 🎯 MVP

**Goal**: Process filtered MemLens dataset to generate answers using a retrieval-augmented generation pipeline.

**Independent Test**: Run evaluation script against a set of hardcoded MemLens queries and verify output JSON contains generated answers and ground truth labels.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US1] Unit test for `data_loader` filtering logic in `tests/unit/test_data_loader.py`: Implement `test_filter_multi_session_reasoning` asserting that only queries with `task_type` in ["Multi-Session Reasoning", "Temporal Reasoning"] are returned.
- [ ] T016 [P] [US1] Unit test for `generator` output format in `tests/unit/test_generator.py`.

### Implementation for User Story 1

- [ ] T017 [US1] Implement `code/run_pipeline.py` main orchestration to load queries and iterate through **all three store strategies (Coarse, Medium, Fine)** sequentially for each query to generate the comparison dataset (US-1, FR-002).
- [ ] T018 [US1] Integrate `data_loader` to fetch real MemLens data (no fabrication) and validate ground truth labels are read-only (FR-007).
- [ ] T019 [US1] Integrate `generator` to produce answers for the filtered subset (US-1).
- [ ] T020 [US1] Implement error handling for empty object detection in `fine_store.py` (fallback to "[No objects detected]") - *Note: Logic moved to T009; this task confirms integration.*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Indexing Strategy Execution (Priority: P2)

**Goal**: Execute the same evaluation loop across Coarse, Medium, and Fine memory store configurations.

**Independent Test**: Run pipeline on a representative sample of queries for each store type and verify logs contain distinct entries with non-identical context windows.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Integration test comparing context windows of Coarse vs Fine stores in `tests/integration/test_store_comparison.py`.

### Implementation for User Story 2

- [ ] T023 [US2] Extend `run_pipeline.py` to orchestrate the **multi-strategy runs** defined in T017, ensuring results are tagged with the store type (Coarse/Medium/Fine) and aggregated correctly (US-2).
- [ ] T024 [US2] Ensure `coarse_store` strictly discards image data and `fine_store` includes object-level captions (Constitution VI).
- [ ] T025 [US2] Aggregate results into a single `outputs/results.csv` linking query ID to accuracy for all three strategies; perform **Wilcoxon Signed-Rank Test** (paired) to compare accuracy distributions and write the p-value and decision (reject/fail to reject) to `results.csv` (Plan.md Complexity Tracking, US-2).
- [ ] T026 [US2] Implement logic to report distribution of excluded queries (missing metadata) by generating a JSON report to `outputs/exclusion_stats.json` **and verify that the exclusion is not correlated with specific session types or visual complexity** (FR-008).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Efficiency and Resource Profiling (Priority: P3)

**Goal**: Measure and record retrieval latency and peak RAM usage for each indexing strategy.

**Independent Test**: Instrument retrieval pipeline on a single query and verify logs contain numerical values for `latency_ms` and `peak_ram_mb`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for `profiler` logging accuracy in `tests/unit/test_profiler.py`.

### Implementation for User Story 3

- [ ] T029 [US3] Integrate `profiler` into `retrieval.py` to time cosine similarity search (US-3).
- [ ] T030 [US3] Integrate `profiler` into `run_pipeline.py` to monitor peak RAM for each strategy run (US-3).
- [ ] T031 [US3] Update `outputs/results.csv` schema to include `latency_ms` and `peak_ram_mb` columns (US-3).
- [ ] T032 [US3] Generate summary table in `run_pipeline.py` showing accuracy vs latency/RAM trade-off (US-3).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates: Update `quickstart.md` to include the command `python code/run_pipeline.py --store all` and the expected output schema (including `results.csv` and `exclusion_stats.json`).
- [ ] T034a [P] Refactor `code/stores/` modules: Implement a common abstract base class `MemoryStore` in `code/stores/base.py` and refactor `coarse_store.py`, `medium_store.py`, `fine_store.py` to inherit from it, ensuring consistent interface for `get_context()` and `build_index()`.
- [ ] T035 [P] Performance verification: Run `python code/run_pipeline.py --profile` locally to generate `outputs/profile_report.json` and verify total duration < 6 hours [UNRESOLVED-CLAIM: c_53004c57 — status=not_enough_info] on a simulated CI environment (SC-005).
- [ ] T036 [P] Additional unit tests for statistical analysis in `tests/unit/test_statistics.py`.
- [ ] T037 Run `quickstart.md` validation to ensure end-to-end reproducibility.
- [ ] T038 [P] **Statistical Method Alignment Check**: Verify that `code/statistics.py` implements **Wilcoxon Signed-Rank Test** (as per Plan.md) and that `plan.md` and `tasks.md` are consistent. Add a comment in `code/statistics.py` explaining the deviation from spec FR-006 (ANOVA) due to deterministic system constraints.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 pipeline structure to run comparative loops
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 pipeline to instrument metrics

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
Task: "Unit test for data_loader filtering logic in tests/unit/test_data_loader.py"
Task: "Unit test for generator output format in tests/unit/test_generator.py"

# Launch all models for User Story 1 together:
Task: "Implement code/run_pipeline.py main orchestration (multi-strategy)"
Task: "Integrate data_loader to fetch real MemLens data"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Multi-strategy loop)
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
- **CRITICAL**: All data must be real (MemLens); no fabrication. All models must run on CPU (no CUDA).
- **Statistical Method**: Tasks T014, T025, T038 implement **Wilcoxon Signed-Rank Test** per Plan.md Complexity Tracking, deviating from spec FR-006 (ANOVA) to accommodate deterministic system constraints.