# Tasks: MCompassRAG: Topic Metadata as a Semantic Compass for Paragraph-Level Retrieval

**Input**: Design documents from `/specs/766-mcompassrag-topic-metadata-as-a-semantic/`
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

- [X] T001a [P] Create project directory structure: `src/`, `tests/`, `scripts/`, `data/`, `outputs/`
- [X] T001b [P] Create `.gitignore` and `README.md` skeleton
- [X] T002a [P] Create `requirements.txt` with CPU-only versions of `torch`, `transformers`, `scikit-learn`, `pandas`, `pyyaml`, `datasets`
- [X] T002b [P] Add script to verify Python 3.11+ environment availability

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/config.py` to enforce `device="cpu"` globally and handle dataset size sampling configuration
- [X] T005 [P] Implement `src/utils.py` with robust logging, error handling for missing APIs (OpenRouter fallback), and memory usage monitoring
- [X] T006a [P] Implement base data loading logic in `src/data_loader.py` (structure, interface)
- [X] T006b [P] Implement stratified sampling and "Dataset Too Large" error path in `src/data_loader.py` (satisfies FR-003)
- [X] T007a [P] Implement `src/topic_modeler.py` using CPU-optimized `scikit-learn` LDA as a fallback (no GPU/CUDA)
- [X] T007b [P] Implement model selection logic in `src/topic_modeler.py` to prioritize ETM/CWTM if available, fallback to LDA (satisfies FR-001)
- [X] T008 Implement `src/retriever.py` with two distinct classes: `BaselineRetriever` (control group) and `MCompassRetriever` (using topic metadata)
- [X] T009 Implement `src/metrics.py` to calculate Latency, Retrieval Score, and Query Count, ensuring no GPU calls
- [X] T010 Create `scripts/setup.sh` to install dependencies and verify CPU-only environment (no CUDA imports)
- [X] T011 Create `scripts/run_rag.sh` as the main entry point invoking `src/run.py` with default config

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End-to-End Execution on CPU-Only Runner (Priority: P1) 🎯 MVP

**Goal**: Verify the MCompassRAG pipeline executes successfully on a GitHub Actions free-tier runner with limited CPU and RAM resources without GPU errors.

**Independent Test**: Run `scripts/setup.sh` and `scripts/run_rag.sh` in a clean CI environment; verify exit code 0 and absence of `ImportError: No module named 'torch.cuda'` or OOM errors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write test scaffolds first. Execution depends on implementation.

- [X] T012 [P] [US1] Contract test for environment setup in `tests/contract/test_cpu_only.py` (verifies no CUDA imports)
- [X] T013 [US1] Create integration test scaffold in `tests/integration/test_end_to_end_cpu.py` (defines test harness; cannot execute until T014 is complete)

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement `src/run.py` main entry point that orchestrates the pipeline (Data Load → Topic Model → Retriever → Metrics)
- [X] T015 [US1] Implement logic in `src/run.py` to force `device="cpu"` for all model loading (transformers, torch)
- [X] T016 [US1] Add configuration trigger in `src/run.py` to invoke the sampling logic from T006b if dataset size exceeds 7 GB
- [X] T017a [US1] Implement local cache lookup logic in `src/utils.py` for OpenRouter data (satisfies FR-005)
- [X] T017b [US1] Implement "skip with warning" logic in `src/utils.py` if cache is missing (NO dummy data)
- [X] T018 [US1] Add logging in `src/run.py` to explicitly print "Running on CPU" and verify no "cuda:0" logs appear

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Artifact Generation and Validation (Priority: P2)

**Goal**: Generate concrete, non-placeholder artifacts (JSON logs, metrics) proving the system processes real data.

**Independent Test**: Run pipeline and verify `outputs/retrieval_results.json` (or similar) exists with >100 bytes of valid numerical data (scores, IDs).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for artifact schema in `tests/contract/test_retrieval_artifact_schema.py`
- [X] T020 [P] [US2] Integration test for artifact content validation in `tests/integration/test_artifact_validity.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Extend `src/retriever.py` to output raw retrieval results (query_id, doc_id, score) to a list structure
- [X] T022 [US2] Implement `src/metrics.py` to serialize results to `outputs/retrieval_results.json` with proper JSON formatting
- [X] T023 [US2] Implement `src/run.py` to log the number of queries processed and documents retrieved upon completion
- [X] T024 [US2] Add validation in `src/utils.py` to ensure generated artifacts contain no nulls or placeholder strings (e.g., "N/A", "0.0")
- [X] T025 [US2] Ensure `src/data_loader.py` fetches real data (e.g., from NAB or HuggingFace datasets) rather than generating fake input data
- [X] T026a [US2] Implement generation of `outputs/topic_embeddings.pt` containing topic vectors for the semantic compass
- [X] T026b [US2] Implement generation of `outputs/topic_model_config.json` containing model parameters and metadata

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Performance Baseline Reporting (Priority: P3)

**Goal**: Output latency and retrieval efficiency metrics to enable preliminary comparison with paper claims (directional improvement).

**Independent Test**: Execute pipeline on 50-query subset; verify logs contain "Average Latency" and "Retrieval Score" as finite numbers < 60s.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for metric schema in `tests/contract/test_metrics_schema.py`
- [X] T027 [P] [US3] Integration test for metric calculation accuracy in `tests/integration/test_metric_reporting.py`

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `src/metrics.py` to calculate and format "Average Latency" (ms/s) and "Retrieval Score" (e.g., Hit Rate or NDCG)
- [X] T029 [US3] Implement `src/run.py` to append a summary table to the final log output containing Query Count, Latency, and Score
- [X] T030 [US3] Implement `src/retriever.py` to measure execution time per query using `time.perf_counter()`
- [X] T031c [US3] Implement logic in `src/metrics.py` to compare MCompass vs. Baseline: Log "Directional Improvement" if (MCompass Latency < Baseline Latency) AND (MCompass Score >= Baseline Score)
- [X] T032 [US3] Ensure all metric calculations are CPU-only and do not involve heavy model inference that exceeds a reasonable time window.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates in `README.md` and `docs/` regarding CPU-only constraints and sampling strategies
- [X] T034 Code cleanup and refactoring of `src/utils.py` to ensure consistent error handling across all modules
- [X] T035 Performance optimization in `src/data_loader.py` to minimize memory footprint during stratified sampling
- [X] T036 [P] Additional unit tests in `tests/unit/` for `topic_modeler.py` (convergence fallback) and `retriever.py` (device enforcement)
- [X] T037 Run `scripts/run_rag.sh` locally to validate `quickstart.md` instructions (if available)
- [X] T038 Create `constitution.md` in `.specify/memory/` to formalize the reproducibility principles used in this plan

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
Task: "Contract test for environment setup in tests/contract/test_cpu_only.py"
Task: "Create integration test scaffold in tests/integration/test_end_to_end_cpu.py"

# Launch all models for User Story 1 together:
Task: "Implement src/run.py main entry point..."
Task: "Implement logic in src/data_loader.py to auto-sample dataset..."
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
- **Critical Constraint**: NO GPU/CUDA dependencies. All tasks must run on CPU, 7 GB RAM.
- **Critical Constraint**: NO data fabrication. All data must be from real sources or valid local caches.