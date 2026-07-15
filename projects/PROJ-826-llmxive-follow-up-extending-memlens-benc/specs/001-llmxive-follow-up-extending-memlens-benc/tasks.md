# Tasks: llmXive follow-up: extending "MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models"

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

- [ ] T001 [P] Create project directories: `data/raw`, `data/processed`, `code`, `tests/unit`, `state/projects` in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/`
- [ ] T002 [P] Create empty placeholder files: `code/__init__.py`, `tests/__init__.py`, `README.md`, `requirements.txt`
- [ ] T003 [P] Populate `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/requirements.txt` with pinned dependencies: torch-cpu, transformers, ultralytics, sentence-transformers, scipy, pandas, datasets, pytest

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/download.py` to fetch MemLens dataset from HuggingFace and compute SHA-256 checksums
- [ ] T005 Implement state update logic in `download.py` to write artifact hashes to `state/projects/PROJ-826-llmxive-follow-up-extending-memlens-benc.yaml`
- [ ] T006 Create base data loading utilities and schema validators in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/preprocessing.py`
- [X] T007 Configure logging infrastructure to track `detection_status` and fallback events in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/utils/logger.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Retrieval and Inference Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download MemLens, filter for MSR/TR, construct Coarse/Medium/Fine memory stores, and run CPU-optimized inference.

**Independent Test**: Run pipeline on a subset of questions and verify three distinct answer sets are generated without GPU.

### Implementation for User Story 1

- [X] T008 [P] [US1] Implement MSR/TR filtering logic in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/preprocessing.py` (FR-001)
- [X] T009 [P] [US1] Implement Coarse store construction (text summaries only) with sentence-transformer embeddings in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/preprocessing.py`
- [X] T010 [P] [US1] Implement Medium store construction (summaries + global CLIP embeddings) in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/preprocessing.py`
- [ ] T011 [US1] Implement YOLOv8-Tiny object detection and fallback logic; check for existence of ground-truth bounding boxes in MemLens dataset (log 'N/A' if missing); calculate Object Detection Recall (TP/(TP+FN)) only if GT exists; write results to `data/processed/metrics/detection_recall.json` (FR-008, FR-009, Edge Case)
- [ ] T011B [US1] Implement logic to explicitly set `detection_status` for ALL samples: 'success' if YOLO detects ≥1 object, 'zero_detection' if YOLO runs but detects 0 objects, 'fallback' if YOLO fails; ensure this flag is written to the Fine store for all entries (Edge Case, Plan Complexity Tracking)
- [X] T012 [US1] Implement LLM-based natural language captioning for detected objects (NO templates) in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/preprocessing.py` <!-- ATOMIZE: requested -->
- [~] T013 [US1] Implement Fine store construction (object captions + bounding boxes) ensuring coordinates are stored as metadata ONLY and explicitly excluded from similarity calculation (Plan Phase 2, FR-002)
- [ ] T013B [US1] Configure top-k retrieval parameter to `k=5` in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/config.py` (Spec Assumptions: fixed for fair comparison)
- [X] T014 [P] [US1] Implement retrieval logic using cosine similarity on text embeddings for Coarse/Medium in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/retrieval.py` (Depends: T009, T010)
- [X] T015 [US1] Implement retrieval logic using cosine similarity on text-only object captions for Fine store (coordinates stored as metadata but excluded from similarity vector per Plan Phase 2) in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/retrieval.py` (FR-003 corrected, Depends: T012, T013, T013B)
- [ ] T016 [US1] Implement CPU-optimized LLM inference (Phi-3-mini or Llama-3-8B 4-bit/16-bit CPU) in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/inference.py` (FR-004, US-3)
- [ ] T017 [US1] Implement context window management (truncation/sliding window) in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/inference.py` (Edge Case)
- [ ] T018 [US1] Implement resource monitoring (RAM, CPU time) and raw latency recording per strategy in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/evaluation.py` (FR-005)
- [ ] T019 [US1] Implement main orchestrator `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/main.py` to run Coarse, Medium, and Fine pipelines sequentially or in parallel (FR-001, Depends: T014, T015, T016)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Comparison and Significance Testing (Priority: P2)

**Goal**: Compare Fine vs. Coarse accuracy using Wilcoxon signed-rank test and validate visual fidelity.

**Independent Test**: Run analysis on generated answer sets and verify Wilcoxon test output (p-value, statistic).

### Implementation for User Story 2

- [ ] T020 [US2] Implement accuracy calculation against ground truth answers in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/evaluation.py` (Depends: T016)
- [ ] T021 [US2] Implement stratification logic to filter out `detection_status: fallback` AND `detection_status: zero_detection` samples for the primary test in the codebase.
- [ ] T022 [US2] Implement paired Wilcoxon signed-rank test for Fine vs. Coarse accuracy distributions in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/stats.py` (FR-006, Depends: T020)
- [ ] T024 [US2] Implement significance flagging (p < 0.05) and effect size calculation in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/stats.py`
- [ ] T025 [US2] Implement handling for insufficient sample size (n < 30) to report descriptive stats only in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/stats.py` (Edge Case)
- [ ] T026 [US2] Generate final comparison report (mean accuracy, std, p-value, effect size) in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/evaluation.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Computational Feasibility and Resource Monitoring (Priority: P3)

**Goal**: Verify pipeline runs within free-tier CI constraints (≤2 CPU, ≤7GB RAM, ≤6h).

**Independent Test**: Run full filtered subset on simulated CI limits and verify no OOM/timeout.

### Implementation for User Story 3

- [ ] T027 [US3] Integrate strict memory monitoring hooks in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/inference.py` to log peak RAM per inference (FR-005, Depends: T016)
- [ ] T028 [US3] Implement fallback logic to 16-bit precision or smaller model (TinyLlama) if 4-bit quantization exceeds RAM limits in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/inference.py`
- [ ] T029 [US3] Implement chunked processing for large datasets to prevent OOM in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/main.py` (Depends: T019)
- [ ] T030 [US3] Implement timeout guards and early exit if estimated runtime > 6 hours in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/main.py`
- [ ] T031 [US3] Generate resource usage report (CPU time, peak RAM, total duration) in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/evaluation.py` (FR-005, SC-003)
- [ ] T034 [US3] Compute retrieval latency relative to Coarse baseline (Fine/Medium - Coarse) / Coarse and flag deviations in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/code/evaluation.py` (SC-004, Depends: T018)
- [ ] T035 [US2] Calculate composite metric: (1) Relative improvement in accuracy (Fine vs Coarse) AND (2) Object Detection Recall; implement logic to check if Recall ≥ 0.6: if YES write status 'VALID', if NO write status 'INVALID' and HALT pipeline; write to `data/processed/metrics/composite_fidelity.json` (SC-005, FR-009, Depends: T020, T011)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/README.md`: Add CLI usage instructions, environment variables, and data flow diagram
- [ ] T033A [P] Refactor `stats.py` to reduce cyclomatic complexity of `run_wilcoxon` function to < 10
- [ ] T033B [P] Refactor `inference.py` to reduce cyclomatic complexity of `load_model` function to < 10
- [ ] T036A [P] Write unit tests for `preprocessing.py` (filtering, store construction) with >80% coverage
- [ ] T036B [P] Write unit tests for `retrieval.py` (cosine similarity logic) with >80% coverage
- [ ] T036C [P] Write unit tests for `stats.py` (stratification, Wilcoxon test) with >80% coverage
- [ ] T037 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data outputs (AnswerSets)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 implementation for monitoring hooks

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
# Launch all models for User Story 1 together:
Task: "Implement Coarse store construction..."
Task: "Implement Medium store construction..."
Task: "Implement YOLOv8-Tiny object detection..."
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
- **CRITICAL**: All tasks must run on CPU-only (minimal cores, standard RAM). No CUDA, no 8-bit quantization requiring GPU.
- **Dependencies**: Tasks without [P] tag explicitly depend on previous tasks in the same phase or previous phases.