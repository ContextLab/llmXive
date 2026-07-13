# Tasks: llmXive follow-up: extending "CiteVQA"

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001a Create directory structure per implementation plan (`code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `data/logs/`, `scripts/`)
- [ ] T001b Create `code/__init__.py`, `tests/__init__.py`, `data/.gitkeep`, `scripts/.gitkeep`
- [ ] T002a Create `requirements.txt` with pinned versions: `torch-cpu`, `transformers`, `sentence-transformers`, `pdfplumber`, `scikit-learn`, `pandas`, `pytest`, `memory-profiler`, `numpy`, `matplotlib`
- [ ] T002b Set up Python virtual environment (`python -m venv venv`) and install requirements <!-- FAILED: unspecified -->
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for paths, seeds, and hyperparameters
- [X] T005a [Research] Identify and verify a real, reachable URL for the CiteVQA dataset (e.g., HuggingFace `datasets.load_dataset("citevqa")` or raw GitHub CSVs). Document the verified URL in `data/verified_sources.json`. If no verified URL is found, document the block and halt.
- [~] T005b [Research] Read the CiteVQA paper and extract the scalar SAA mean value. Document this value in `data/baseline_saa_raw.json` with source citation. <!-- FAILED: unspecified -->
- [~] T006 [Depends T005a] Fetch the verified CiteVQA dataset using the URL from `data/verified_sources.json`. Parse PDFs with `pdfplumber` to extract text chunks and bounding boxes. Save to `data/raw/` and `data/processed/`.
- [~] T007 [Depends T005b] Implement `code/baseline_ref.py` to load the immutable CiteVQA baseline SAA scalar from `data/baseline_saa.json` (populated from T005b output). Define the JSON schema: `{"baseline_saa": <value>, "source": "paper_ref"}`.
- [~] T008 Implement `code/metrics.py` with core functions: `calculate_iou`, `semantic_similarity` (L2 normalized), `compute_saa` (Answer Correctness: Exact Match OR Semantic Similarity >= 0.85), `compute_vla`.
- [~] T009 Setup environment configuration management for CPU-only execution constraints
- [~] T010 [P] Create unit tests for `metrics.py` (mocked IoU and similarity calculations) in `tests/unit/test_metrics.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Text-Only Retrieval and Reasoning Pipeline (Priority: P1) 🎯 MVP

**Goal**: Implement the two-stage pipeline (Retrieval + Reasoning) using `all-MiniLM-L6-v2` and `Phi-3-mini` (4-bit quantized) on the held-out test set.

**Independent Test**: The pipeline processes a query and pre-processed text JSON, outputting an answer and chunk ID without crashing or requiring GPU.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T011 [P] [US1] Integration test for text-only pipeline on a single sample query in `tests/integration/test_text_pipeline.py`
- [~] T012 [P] [US1] Contract test verifying output format (answer string + chunk ID) in `tests/contract/test_output_schema.py`

### Implementation for User Story 1

- [~] T013 [P] [US1] Implement `code/retriever.py`: Encode text chunks with `all-MiniLM-L6-v2` and retrieve top-k for a query
- [~] T014 [US1] Implement `code/reasoning.py`: Load `Phi-3-mini` (CPU-tractable, 4-bit quantized) and generate answer + predicted chunk ID from retrieved text on the held-out test set. Run `memory_profiler` and save output to `data/logs/memory_profile.log`. Ensure memory usage < 7GB.
- [~] T015 [US1] Create `code/main.py` orchestration script to run the full text-only evaluation loop on the held-out test set
- [~] T016 [US1] Implement error handling for missing chunk IDs (log error, assign IoU=0.0) in `code/reasoning.py`
- [~] T017 [US1] Add logging for runtime and memory usage per query to verify that the system operates within the defined time and memory constraints.
- [~] T018a [US1] Run pilot evaluation on [deferred] of the held-out test set to measure per-query runtime.
- [~] T018b [US1] Extrapolate total runtime based on pilot results and record in `data/results/runtime_estimate.json`. Verify it fits within the 6-hour limit (SC-004).
- [~] T019 [US1] Save intermediate results (answers, predicted IDs) to `data/results/text_pipeline_results.json`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Modal Spatial Grounding Evaluation (Priority: P2)

**Goal**: Evaluate Strict Attributed Accuracy (SAA) by mapping predicted chunk IDs to bounding boxes and calculating IoU.

**Independent Test**: Given predicted IDs and ground-truth boxes, the system computes SAA and distribution plots.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T020 [P] [US2] Contract test for SAA calculation logic in `tests/contract/test_saa_metric.py`
- [~] T021 [P] [US2] Integration test for the full SAA evaluation loop in `tests/integration/test_saa_evaluation.py`

### Implementation for User Story 2

- [~] T022 [US2] Extend `code/main.py` to compute SAA (Answer Correctness: Exact Match OR Semantic Similarity >= 0.85 AND Spatial Correctness: IoU > 0.5) for the text-only results. <!-- FAILED: unspecified -->
- [~] T023 [US2] Implement supplementary statistical analysis: Bootstrap CI (Confidence Interval) to compare the mean SAA against the fixed baseline.
- [~] T023a [US2] Implement mandatory statistical analysis: one-sample t-test comparing mean SAA against the baseline scalar (from FR-007/SC-002) with p < 0.05 threshold. Save results to `data/results/statistical_test.json`.
- [~] T024 [US2] Generate distribution plot of IoU scores and SAA failure modes (Attribution Hallucination) in `data/results/saa_analysis.png`
- [~] T024b [US2] Calculate and report the 'Attribution Hallucination' failure rate metric (count of hallucinations / total correct answers) as required by SC-003. Save to `data/results/hallucination_rate.json`.
- [~] T025 [US2] Save final SAA metrics and statistical test results to `data/results/saa_summary.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visual-Only Localization Control Experiment (Priority: P3)

**Goal**: Execute control experiment where a model receives only full-page images to predict bounding boxes.

**Independent Test**: The system feeds full-page images to a vision model and records predicted boxes/IDs against ground truth.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T026 [P] [US3] Contract test for visual-only input/output schema in `tests/contract/test_visual_input.py`
- [~] T027 [P] [US3] Integration test for visual localization pipeline in `tests/integration/test_visual_control.py`

### Implementation for User Story 3

- [~] T028 [P] [US3] Implement `code/visual_control.py`: Load `microsoft/phi-3-vision-128k-instruct` (4-bit quantized). Run `python scripts/profile_vision_memory.py` to verify memory usage < 7GB. If memory exceeds limit, flag research blocker.
- [~] T029 [US3] Implement logic to predict bounding box/chunk ID from visual input only (no text context). Compute **Visual Localization Accuracy (VLA)** and **Strict Attributed Accuracy (SAA)** for the visual-only pipeline.
- [~] T030 [US3] Compute VLA and SAA for Visual-Only pipeline and compare against Text-Only SAA results. Clarify relationship between VLA and SAA in the report.
- [~] T031 [US3] Generate comparative report highlighting the performance delta between Text-Only and Visual-Only modalities in `data/results/modality_comparison.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `quickstart.md` and `README.md`
- [ ] T033 Code cleanup and refactoring to ensure no GPU imports remain in `code/`
- [ ] T034 Performance optimization to ensure total runtime < 6 hours on CI
- [ ] T035 [P] Additional unit tests for data loading edge cases (corrupted PDFs, malformed boxes) in `tests/unit/test_data_loader.py`
- [ ] T036 Run `quickstart.md` validation to verify end-to-end execution

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS** all user stories (specifically T005a/T006 dataset fetch)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T019 (text results) to compute SAA
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent modality test

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
- **CRITICAL**: T005a MUST use a real, reachable URL for CiteVQA. No synthetic data.
- **CRITICAL**: T014 MUST use CPU-tractable model (4-bit quantized, no CUDA) and profile memory.
- **CRITICAL**: T023a MUST implement the one-sample t-test as per FR-007.
- **CRITICAL**: T028 MUST use `microsoft/phi-3-vision-128k-instruct` and profile memory.