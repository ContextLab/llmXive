# Tasks: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

**Input**: Design documents from `/specs/001-visual-complexity-on-cognitive-load/`
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

- [ ] T001a [P] Create code directory structure (`code/stimuli/`, `code/experiments/`, `code/analysis/`, `code/utils/`, `code/tests/`)
- [ ] T001b [P] Create data directory structure (`data/stimuli/`, `data/processed/`, `data/measurements/`, `data/raw/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies (`ultralytics`, `opencv-python`, `statsmodels`, `scikit-learn`, `pandas`, `numpy`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/config.py` for seed management and path constants
- [ ] T005 Implement `code/utils/io_helpers.py` including `update_state_manifest` for checksumming and artifact tracking
- [ ] T005b [P] [Foundational] Implement a strict CPU-only enforcement check in `code/utils/config.py` or a pre-run hook to ensure no GPU-specific code paths (e.g., `device='cuda'`, `load_in_8bit`) are used in any subsequent script, addressing the CPU-only requirement early.
- [ ] T006 [P] Create base directory structure for `data/stimuli/`, `data/processed/`, and `data/measurements/` with READMEs

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Visual Complexity Metrics (Priority: P1) 🎯 MVP

**Goal**: Extract quantitative visual complexity metrics (entropy, color variance, edge density, object counts) from background frames using a CPU-compatible pipeline.

**Independent Test**: Run the metric extraction script on a static set of diverse background images and verify that the output JSON contains valid numerical values without errors.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Unit test for entropy calculation in `tests/test_metrics.py`
- [ ] T009 [P] [US1] Unit test for color variance calculation in `tests/test_metrics.py`
- [ ] T010 [P] [US1] Integration test for YOLOv8n CPU inference on 1080p batch in `tests/test_metrics.py` (verify < 30s runtime, < 2GB RAM; MUST use isolated temporary directories and model cache isolation to ensure parallel safety)
- [ ] T011 [P] [US1] Contract test for "blank background" edge case (zero object count) in `tests/test_metrics.py` (MUST use isolated temporary directories to ensure parallel safety)
- [ ] T011a [P] [US1] Setup isolated test data directories in `tests/data/` and populate with dummy images for T010/T011 isolation

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/stimuli/extract_metrics.py` to compute image entropy, color variance, edge density, and object detection counts using **YOLOv8n** on **CPU only**. **Acceptance Criteria**: Verify batch processing of 1080p images completes in <30s and RAM <2GB. Explicitly enforce CPU-only execution and YOLOv8n usage.
- [ ] T013 [US1] Add logic to handle images with no detectable objects gracefully (return 0 count, no crash)
- [ ] T014 [US1] Implement data persistence: save computed metrics to `data/processed/metrics.csv` with `metric_source` field tracking (YOLO vs. Edge)
- [ ] T014b [US1] Generate the n=20 pilot dataset of human-rated images (synthetic or sourced) with ground truth complexity scores for SC-001 validation
- [ ] T015 [US1] Implement `code/stimuli/validate_sensitivity.py` to compare automated metrics against the **n=20 pilot study** dataset; implement correlation validation logic to ensure metrics align with human ratings and avoid circular validation (SC-001).
- [ ] T007 [US1] Populate fallback edge detection logic (Canny) in `code/stimuli/extract_metrics.py` for cases where YOLO fails or is unavailable

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Administer Cognitive Load Assessment (Priority: P2)

**Goal**: Simulate participant sessions presenting clips in counterbalanced order and capturing NASA-TLX scores and reaction-time metrics.

**Independent Test**: Simulate a participant session where a clip is shown, the NASA-TLX form is submitted, and the reaction-time task is completed, verifying data record linkage.

### Tests for User Story 2

- [ ] T016 [P] [US2] Unit test for Latin Square counterbalancing logic in `tests/test_analysis.py`
- [ ] T017 [P] [US2] Integration test for synthetic data generation (Null vs. Signal modes) in `tests/test_analysis.py`
- [ ] T018 [P] [US2] Test for missing data flagging logic (exclusion vs. imputation) in `tests/test_analysis.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/experiments/counterbalance.py` to generate Latin Square designs for clip ordering
- [ ] T020 [US2] Implement `code/experiments/simulate_participants.py` to generate synthetic NASA-TLX scores and reaction times under Null and Signal hypotheses
- [ ] T021 [US2] Add logic to flag incomplete records (missing TLX or RT) for exclusion in the generated dataset
- [ ] T022 [US2] Save generated participant sessions to `data/measurements/raw/participant_sessions.csv` with `participant_id`, `clip_id`, and response metrics

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Execute linear mixed-effects models to correlate complexity with cognitive load, applying corrections and diagnostics.

**Independent Test**: Run the analysis script on a pre-generated synthetic dataset with known correlations and verify correct identification of significant predictors and diagnostics.

### Tests for User Story 3

- [ ] T023 [P] [US3] Unit test for Benjamini-Hochberg correction implementation in `tests/test_analysis.py`
- [ ] T024 [P] [US3] Unit test for VIF calculation and threshold flagging (>5) in `tests/test_analysis.py`
- [ ] T025 [P] [US3] Integration test for full pipeline (Metrics + Simulated Data -> Model -> Report) in `tests/test_analysis.py`

### Implementation for User Story 3

- [ ] T025b [US3] Implement data integration logic to merge `data/processed/metrics.csv` and `data/measurements/raw/participant_sessions.csv` into a single analysis-ready dataframe
- [ ] T026 [US3] Implement `code/analysis/run_model.py` to execute linear mixed-effects models with visual complexity as predictor and cognitive load as outcome
- [ ] T027a [US3] Implement VIF calculation in `code/analysis/run_model.py`; if VIF > 5, flag instability
- [ ] T027b [US3] Implement PCA fallback mechanism in `code/analysis/run_model.py`: If VIF > 5, combine predictors via PCA to reduce multicollinearity (FR-003 requirement)
- [ ] T028 [US3] Implement Benjamini-Hochberg correction for multiple hypothesis tests in `code/analysis/run_model.py`
- [ ] T029 [US3] Implement `code/analysis/sensitivity.py` to sweep p-value thresholds ({0.01, 0.05, 0.1}) and report effect size stability; **frame output explicitly as a "pipeline robustness check on synthetic data"** rather than a scientific finding (FR-005, Plan Scope Limitation).
- [ ] T030 [US3] Implement `code/analysis/report_gen.py` to generate the final report with fixed effect estimates, confidence intervals, adjusted p-values, and VIF scores

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033a [P] Update `docs/quickstart.md` with specific CPU-only setup instructions and YOLOv8n installation steps
- [ ] T033b [P] Update `docs/data-model.md` with new entity attributes and metric definitions
- [ ] T033c [P] Update `docs/contracts/` with final API/Interface definitions
- [ ] T034 [P] Additional unit tests for edge cases (skewed distributions, attention check failures) in `tests/`
- [ ] T035 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Must** wait for US1 (metrics) and US2 (data) to be generated before running the model

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- US3 (Analysis) depends on data generation from US1 and US2, so it must run sequentially after them

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for entropy calculation in tests/test_metrics.py"
Task: "Unit test for color variance calculation in tests/test_metrics.py"
Task: "Integration test for YOLOv8n CPU inference in tests/test_metrics.py"

# Launch all models for User Story 1 together:
Task: "Implement code/stimuli/extract_metrics.py"
Task: "Implement code/stimuli/validate_sensitivity.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Metric Extraction)
4. **STOP and VALIDATE**: Test US1 independently on sample images
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Metrics) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Simulation) → Test independently → Deploy/Demo
4. Add User Story 3 (Analysis) → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Metric Extraction)
   - Developer B: User Story 2 (Data Simulation)
   - Developer C: User Story 3 (Analysis - waits for A & B data)
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
- **CRITICAL**: Ensure all YOLO inference is CPU-only; do not use `load_in_8bit` or `device_map="cuda"`.
- **CRITICAL**: All data must be real or procedurally generated with verified seeds; no hardcoded fake values.