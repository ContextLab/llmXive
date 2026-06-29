# Tasks: Map-Free Transit Route Generation with LLMs

**Input**: Design documents from `/specs/001-map-free-transit-route-generation/`
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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `specs/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (torch-cpu, transformers, datasets, networkx, scikit-learn, pydantic, gtfs)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement GTFS data fetcher in `src/lib/gtfs_fetcher.py` (handles NYC MTA feed with deterministic fallback)
- [ ] T005 [P] Create `src/lib/graph_utils.py` to convert GTFS `stops.txt`/`transfers.txt` to NetworkX graph (no coordinates)
- [ ] T006 [P] Implement checksumming and PII scanning in `src/lib/data_hygiene.py`
- [ ] T007 [P] Setup random seed configuration and logging infrastructure in `src/lib/config.py`
- [ ] T008 [P] Create executable schemas in `src/contracts/` (gtfs-graph.schema.yaml, route-sequence.schema.yaml, validation-result.schema.yaml) using Pydantic models; ensure these schemas are used to validate outputs from T004 and T005 before consumption by US3.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 3 - Dataset Construction & Variable Verification (Priority: P3)

**Goal**: Construct the "map-free" dataset by converting GTFS feeds into natural language sequences, ensuring no geographic coordinates or map topology are included.

**Independent Test**: Verify via regex scan that a representative set of random input prompts contains zero coordinate patterns or adjacency lists.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US3] Unit test for coordinate leakage detection in `tests/unit/test_text_utils_leakage.py`
- [ ] T010 [P] [US3] Contract test for GTFS-to-text conversion schema in `tests/contract/test_route_sequence_schema.py`

### Implementation for User Story 3

- [ ] T011 [US3] Implement GTFS-to-text converter in `src/lib/text_utils.py` (generates "Take Line X from Station A to Station B" sequences)
- [ ] T012 [US3] Implement "map-free" validation script in `src/analysis/verify_map_free.py` (regex scan for coordinates/graph topology)
- [ ] T013 [US3] Create dataset split logic in `src/lib/splitter.py` to generate path-disjoint training vs. held-out test sets
- [ ] T014 [US3] Generate `data/processed/train_sequences.txt` and `data/processed/test_od_pairs.json`

**Checkpoint**: Map-free dataset is constructed, validated, and split (training vs. held-out)

---

## Phase 4: User Story 1 - Map-Free Route Generation & Validation (Priority: P1) 🎯 MVP

**Goal**: Fine-tune a small CPU-tractable LLM (≤1.5B params) on the map-free sequences and validate generated routes against the ground-truth GTFS graph.

**Independent Test**: Run inference on held-out O-D pairs, validate against graph, compute Exact Match and Connectivity Validity scores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US1] Unit test for graph traversal oracle in `tests/unit/test_graph_validation.py`
- [ ] T016 [P] [US1] Integration test for end-to-end generation and validation pipeline in `tests/integration/test_route_generation.py`

### Implementation for User Story 1

- [ ] T017 [US1] Implement graph-traversal oracle in `src/models/validation.py` (returns Valid/Invalid, Exact Match score; consumes ground-truth graph)
- [ ] T018 [US1] Implement small LLM inference wrapper in `src/models/inference.py` (supports CPU-only, batch=1, memory monitoring)
- [ ] T019 [US1] Implement LoRA fine-tuning script in `src/analysis/train.py` (target model ≤1.5B, CPU-only, logs peak RSS)
- [ ] T020 [US1] Implement output parser in `src/lib/text_utils.py` to strip conversational filler and extract station sequences
- [ ] T021 [US1] Create end-to-end benchmark runner in `src/cli/run_benchmark.py` (orchestrates generation, parsing, validation)
- [ ] T022 [US1] Generate `data/results/validation_scores.json` for held-out set

**Checkpoint**: Route generation and validation pipeline is functional and produces metrics for the held-out set

---

## Phase 5: User Story 2 - Comparative Statistical Analysis (Priority: P2)

**Goal**: Compare fine-tuned model performance against zero-shot baselines using statistical tests to confirm significance.

**Independent Test**: Run statistical analysis script on validity scores; output p-value < 0.05 for significant improvement.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for statistical significance calculation in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement zero-shot baseline runner in `src/analysis/baseline.py` (use TinyLlama full precision/8-bit for CPU; run on same held-out set; log peak RSS memory)
- [ ] T025 [US2] Implement statistical analysis script in `src/analysis/stats.py` (McNemar's test on binary validity scores; output p-value)
- [ ] T026 [US2] Generate `data/results/statistical_report.md` with p-value and confidence intervals

**Checkpoint**: Statistical significance of the fine-tuned model's improvement is established

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Documentation updates in `docs/` (including `quickstart.md` validation)
- [ ] T028 Code cleanup and refactoring of `src/lib/` and `src/models/`
- [ ] T029 Performance optimization for inference batch processing (ensure N=100 completes <6h)
- [ ] T030 [P] Additional unit tests for edge cases (loops, hallucinated stations, disconnected O-D pairs) in `tests/unit/`
- [ ] T031 Security hardening (input sanitization for GTFS data)
- [ ] T032 Run `quickstart.md` validation and update if needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **US3 (P3)** MUST run first to generate the dataset required by US1 and US2.
  - **US1 (P1)** depends on US3 (data) and Foundational (graph).
  - **US2 (P2)** depends on US1 (results) and Foundational.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Must complete before US1.**
- **User Story 1 (P1)**: Can start after Foundational (Phase 2) AND US3 (Dataset) - Requires generated text sequences.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) AND US1 (Results) - Requires validation scores.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data processing (US3) before Model Training (US1) before Analysis (US2)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US3 can start immediately.
- US1 can start as soon as US3 produces the first batch of data (streaming approach) or wait for full dataset.
- US2 must wait for US1 completion.

---

## Parallel Example: Foundational Tasks

```bash
# Launch all foundational tasks together (if team capacity allows):
Task: "Implement GTFS data fetcher in src/lib/gtfs_fetcher.py"
Task: "Create src/lib/graph_utils.py to convert GTFS to NetworkX"
Task: "Implement checksumming and PII scanning in src/lib/data_hygiene.py"
Task: "Setup random seed configuration and logging in src/lib/config.py"
```

---

## Implementation Strategy

### MVP First (User Story 3 → User Story 1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 3 (Dataset) - **Critical Blocker**
4. Complete Phase 4: User Story 1 (Generation & Validation)
5. **STOP and VALIDATE**: Test US1 independently on held-out set
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 3 → Generate Map-Free Dataset → Test independently
3. Add User Story 1 → Train & Validate → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Statistical Analysis → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 3 (Dataset Construction)
   - Developer B: User Story 1 (Model & Validation) - can start on graph logic while waiting for data
3. Once Data is ready, Developer B completes US1.
4. Developer C (or A/B) performs US2 (Analysis).

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All model training/inference must run on CPU-only, ≤7GB RAM, ≤6h total time. No 4-bit quantization (unless explicitly stable for small models like TinyLlama) or GPU-specific code.
- **Statistical Note**: Use McNemar's test for binary validity scores; do not use t-tests.
- **Baseline Note**: Zero-shot baseline must be a local, CPU-tractable model (e.g., TinyLlama-1.1B full precision/8-bit), not an external API.