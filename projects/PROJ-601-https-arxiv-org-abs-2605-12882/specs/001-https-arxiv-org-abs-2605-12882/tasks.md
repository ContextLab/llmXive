# Tasks: CiteVQA Reproduction & Validation

**Input**: Design documents from `/specs/601-reproduce-citevqa/`
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

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with `transformers`, `torch`, `Pillow`, `datasets`, `pytest` dependencies
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup `external/CiteVQA` submodule initialization and verification script
- [X] T005 [P] Implement CPU-only model loading wrapper (enforcing `device_map="cpu"`, no CUDA)
- [X] T006 [P] Setup memory-efficient data streaming utilities (batching < 7 GB RAM)
- [X] T007 Create base data models for `InferenceResult` and `GroundTruth`
- [X] T008 Configure error handling and logging infrastructure for OOM and missing data
- [X] T009 Setup environment configuration management for `--sample-size` and dataset paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute End-to-End Inference Pipeline (Priority: P1) 🎯 MVP

**Goal**: Trigger `infer/run.py` against a subset of CiteVQA in CPU mode and generate raw prediction artifacts.

**Independent Test**: The CI job runs `infer/run.py` with `--sample-size 10`. The test passes if the script exits with code 0 and generates `outputs/infer_results.jsonl` with valid JSON objects.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for `InferenceResult` schema in `tests/contract/test_inference_schema.py`
- [X] T011 [P] [US1] Integration test for CPU-only inference execution in `tests/integration/test_pipeline_e2e.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement CPU-only model loader in `data/load_model.py` (enforce `device_map="cpu"`)
- [X] T013 [US1] Configure `infer/run.py` to accept `--sample-size` and stream data without OOM
- [X] T014 [US1] Implement prompt engineering for spatial output (bounding boxes) in `infer/prompt_templates.py`
- [X] T015 [US1] Execute inference loop and write `outputs/infer_results.jsonl`
- [X] T016 [US1] Add OOM catch-and-log logic for model loading failures
- [X] T017 [US1] Add logging for skipped records due to missing images or malformed data

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Evaluation & Scoring Pipeline (Priority: P2)

**Goal**: Feed inference artifacts into `eval/run.py` to compute Strict Attributed Accuracy (SAA) and distinguish attribution hallucinations.

**Independent Test**: The CI job runs `eval/run.py` against `outputs/infer_results.jsonl`. The test passes if `outputs/evaluation_report.json` is generated containing the SAA metric.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for `EvaluationReport` schema in `tests/contract/test_evaluation_schema.py`
- [X] T019 [P] [US2] Integration test for SAA calculation logic in `tests/integration/test_saa_calculation.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement IoU calculation utility with [0,1] normalization in `eval/metrics.py`
- [X] T021 [US2] Implement SAA logic distinguishing "Answer Correct/Region Wrong" vs "Answer Wrong" in `eval/saa_scoring.py`
- [X] T022 [US2] Implement `eval/run.py` to load `infer_results.jsonl` and generate report
- [X] T023 [US2] Integrate skipped record counts from `validation_log.json` into the final report
- [X] T024 [US2] Add specific logging for "Attribution Hallucination" cases (correct answer, wrong region)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Dataset Integrity & Variable Fit (Priority: P3)

**Goal**: Verify dataset structure, variable presence, and memory footprint before processing.

**Independent Test**: A script `data/validate_dataset.py` runs to check structure/size. The test passes if all required columns exist and size < 7 GB.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [X] T026 [P] [US3] Integration test for memory-efficient streaming in `tests/integration/test_memory_streaming.py`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `data/validate_dataset.py` to check `question`, `answer`, `ground_truth_bbox`, `image_path`
- [X] T028 [US3] Implement streaming loader to handle large datasets in batches (FR-006)
- [X] T029 [US3] Generate `outputs/validation_log.json` listing skipped records and reasons
- [X] T030 [US3] Add logic to handle missing ground-truth bounding boxes (skip and log)
- [X] T031 [US3] Add logic to handle missing PDF downloads (skip and log)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Bias Mitigation (Addressing Kahneman Review)

**Goal**: Explicitly address the "WYSIATI" bias concern by ensuring the evaluation probes the *quality* of evidence selection, not just presence.

**Independent Test**: Verification that the evaluation report explicitly separates "Coherence Errors" (correct answer, wrong region) from "Truth Errors" (wrong answer).

### Implementation for Revision Concerns

- [X] T032 [US2] Refine `eval/saa_scoring.py` to explicitly tag "Availability Heuristic" cases (high confidence, wrong region)
- [X] T033 [US2] Add a specific metric `attribution_hallucination_rate` to `outputs/evaluation_report.json`
- [X] T034 [US2] Ensure `eval/run.py` logs a warning when `answer_correct` count is high but `region_correct` is low (WYSIATI indicator)
- [X] T035 [US3] Update `data/validate_dataset.py` to flag records where ground-truth regions are ambiguous or missing (preventing false positives)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Documentation updates in `docs/` regarding CPU constraints and SAA definition
- [X] T037 Code cleanup and refactoring
- [X] T038 Performance optimization for CPU inference (batch size tuning)
- [X] T039 [P] Additional unit tests in `tests/unit/`
- [X] T040 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`infer_results.jsonl`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Provides input validation for US1/US2
- **Revision Concerns (Phase 6)**: Must be implemented alongside US2 to ensure metrics are calculated correctly

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US3 can start in parallel (US2 waits for US1 output)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for `InferenceResult` schema in `tests/contract/test_inference_schema.py`"
Task: "Integration test for CPU-only inference execution in `tests/integration/test_pipeline_e2e.py`"

# Launch all models for User Story 1 together:
Task: "Implement CPU-only model loader in `data/load_model.py`"
Task: "Implement prompt engineering for spatial output in `infer/prompt_templates.py`"
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
3. Add User Story 3 → Test independently → Deploy/Demo (Data Integrity)
4. Add User Story 2 → Test independently → Deploy/Demo (Evaluation)
5. Add Phase 6 (Revision) → Refine metrics for WYSIATI bias
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Inference)
   - Developer B: User Story 3 (Data Validation)
3. Once US1 is done:
   - Developer C: User Story 2 (Evaluation) + Phase 6 (Bias Mitigation)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
