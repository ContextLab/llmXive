# Tasks: OmniRetrieval Unified Validation

**Input**: Design documents from `/specs/644-omniretrieval-validation/`
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

- [X] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `results/`)
- [X] T002 Initialize Python 3.10+ project with dependencies: `torch` (CPU-only), `sentence-transformers`, `duckdb`, `rdflib`, `beir`, `datasets`, `pytest`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/utils/logger.py` for structured logging (FR-007)
- [X] T005 Implement `src/utils/retry.py` with exponential backoff (max 3 attempts, ≤60s total) for network timeouts (FR-006)
- [X] T006 Implement `src/utils/memory_monitor.py` to track RSS and enforce 6.5GB ceiling (FR-005)
- [X] T007 Implement `src/config.py` for configuration management and environment variables
- [X] T008 Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` per plan.md
- [X] T009 Implement `src/loaders/base_loader.py` with abstract methods for dataset fetching and checksum verification

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Pipeline Execution & Artifact Generation (Priority: P1) 🎯 MVP

**Goal**: Execute the vendored OmniRetrieval codebase end-to-end on a subset of available datasets to confirm initialization, processing, and artifact generation without crashes.

**Independent Test**: The CI runner executes `main.py` with a minimal config (single dataset). Test passes if exit code 0, `results.json` has ≥1 record, and logs have ≥10 lines.

### Tests for User Story 1

- [X] T010 [P] [US1] Contract test for output schema validation in `tests/contract/test_output_format.py`
- [X] T011 [P] [US1] Integration smoke test for end-to-end run in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `src/loaders/beir_loader.py` to fetch `beir/trec-covid` via `datasets` library (real URL)
- [X] T013 [P] [US1] Implement `src/loaders/spider_loader.py` to fetch Spider dataset and manual DB files (real URL)
- [X] T014 [P] [US1] Implement `src/loaders/quad_loader.py` to fetch `lc-quad-2` via `datasets` library
- [X] T015 [US1] Implement `src/engines/base.py` (Abstract engine interface)
- [X] T016 [US1] Implement `src/engines/text_engine.py` using `sentence-transformers/all-MiniLM-L6-v2` (CPU-optimized, 16-bit)
- [X] T017 [US1] Implement `src/main.py` entry point to orchestrate loaders and engines, handling missing datasets gracefully (US-1 Scenario 2)
- [X] T018 [US1] Add logic to `src/main.py` to write non-empty `results.json` and log files (US-1 Scenario 1)
- [X] T019 [US1] Add memory monitoring wrapper to `src/main.py` to enforce streaming mode if approaching 6GB (US-1 Scenario 3)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heterogeneous Source Dispatch Verification (Priority: P2)

**Goal**: Verify that the framework correctly identifies and dispatches queries to appropriate native execution engines (SQL, SPARQL, Text).

**Independent Test**: Run against mixed-benchmark subset. Logs must show distinct dispatch paths and generated queries must be syntactically valid.

### Tests for User Story 2

- [X] T020 [P] [US2] Automated Dispatch Oracle Test in `tests/integration/test_dispatcher_test.py` asserting `engine_type == source_type`
- [X] T021 [P] [US2] Unit test for SQL syntax validation in `tests/unit/test_sql_engine.py`
- [X] T022 [P] [US2] Unit test for SPARQL syntax validation in `tests/unit/test_sparql_engine.py`

### Implementation for User Story 2

- [X] T023 [P] [US2] Implement `src/engines/sql_engine.py` using `duckdb` to execute SQL queries
- [X] T024 [P] [US2] Implement `src/engines/sparql_engine.py` using `rdflib` to execute SPARQL queries
- [X] T025 [US2] Implement query type detection logic in `src/main.py` (or `src/config.py`) to route to specific engines (FR-003)
- [X] T026 [US2] Implement pre-dispatch syntax validation for SQL/SPARQL strings in respective engines (FR-004)
- [X] T027 [US2] Update `src/main.py` to log explicit "Dispatched to: [Engine Name]" messages (US-2 Scenario 1, 2, 3)
- [X] T028 [US2] Integrate `src/main.py` to handle malformed queries by logging error and skipping entry (Edge Case: Malformed queries)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Performance & Resource Constraint Validation (Priority: P3)

**Goal**: Ensure the pipeline completes within GitHub Actions free-tier constraints (≤6h, ≤7GB RAM, CPU-only).

**Independent Test**: Run full pipeline on sample. Passes if total time ≤4h and peak RSS ≤6.5GB.

### Tests for User Story 3

- [X] T029 [P] [US3] Resource usage integration test (wall-clock and RSS) in `tests/integration/test_resource_constraints.py`

### Implementation for User Story 3

- [X] T030 [US3] Update `src/main.py` to measure and log total execution time (FR-007)
- [X] T031 [US3] Update `src/main.py` to log peak memory usage summary at end of run (FR-007)
- [X] T032 [US3] Verify `src/engines/text_engine.py` uses CPU-only model loading (no `device_map="cuda"`, no 8-bit quantization)
- [X] T033 [US3] Implement streaming data loader logic in `src/loaders/base_loader.py` to prevent OOM on large corpora (US-3 Scenario 2)
- [X] T034 [US3] Add timeout handling for external LLM client (mock/local) with retry logic in `src/utils/retry.py` (Edge Case: Network timeout)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Update `quickstart.md` with instructions for running the smoke test and validating artifacts
- [X] T036 [P] Run `pytest` against full pipeline on sampled dataset to verify SC-001, SC-002, SC-003, SC-004
- [X] T037 [P] Code cleanup and refactoring
- [X] T038 [P] Documentation updates in `docs/` regarding dataset subsets and resource limits
- [X] T039 [P] Validate `results.json` contains at least one non-null `answer` field for every processed query (SC-004)

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
Task: "Contract test for output schema validation in tests/contract/test_output_format.py"
Task: "Integration smoke test for end-to-end run in tests/integration/test_full_pipeline.py"

# Launch all loaders for User Story 1 together:
Task: "Implement src/loaders/beir_loader.py"
Task: "Implement src/loaders/spider_loader.py"
Task: "Implement src/loaders/quad_loader.py"
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
   - Developer A: User Story 1 (Loaders, Main, Text Engine)
   - Developer B: User Story 2 (SQL/SPARQL Engines, Dispatch Logic)
   - Developer C: User Story 3 (Resource Monitoring, Optimization)
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
- **Constraint**: All models must be CPU-optimized (e.g., `all-MiniLM-L6-v2`), no GPU/CUDA, no 8-bit/4-bit quantization requiring `bitsandbytes`.
- **Constraint**: Dataset downloads must use explicit, reachable URLs or `datasets` library calls (no "download from UCI" without method).
