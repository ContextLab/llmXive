# Tasks: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

**Input**: Design documents from `/specs/001-visual-complexity-on-cognitive-load/`
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

## Phase 0: Specification Alignment (Critical Prerequisite)

**Purpose**: Resolve contradictions between Spec and Tasks before implementation begins.

- [ ] T000 [P] **Update Spec NFR-001**: Update `specs/001-visual-complexity-cognitive-load/spec.md` NFR-001 to explicitly state: "The system MUST process 10 input images at 1080p (1920x1080) by resizing them to 640x640 for inference to meet the 30s CPU constraint. The input is 1080p, but internal inference resolution is 640x640." This resolves the conflict between NFR-001 and the implementation strategy in T019.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create code directory structure (`src/lib/`, `src/metrics/`, `src/experiment/`, `src/analysis/`, `tests/`)
- [ ] T001b [P] Create data directory structure (`data/stimuli/`, `data/processed/`, `data/measurements/`, `data/raw/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies (`ultralytics`, `opencv-python-headless`, `statsmodels`, `scikit-learn`, `pandas`, `numpy`, `pillow`, `requests`, `flask`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `src/lib/utils.py` containing `set_global_seed()` and checksum utilities
- [ ] T005 [P] Create base directory structure for `data/stimuli/`, `data/processed/`, and `data/measurements/` with READMEs

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 - Conduct Human Pilot Study for Metric Validation (Priority: P0) 🎯 MVP

**Goal**: Recruit a small cohort (n=20) to rate background images for perceived visual complexity to validate automated metrics (SC-001).

**Independent Test**: Run the pilot study interface, collect 20 human ratings, and verify that the resulting dataset correlates (r > 0.5) with automated metrics computed on the same images.

### Tests for User Story 0

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T007 [P] [US0] Unit test for data ingestion of human ratings in `tests/test_metrics.py`
- [ ] T008 [P] [US0] Unit test for correlation calculation (Pearson's r) between human scores and automated metrics in `tests/test_metrics.py`
- [ ] T009 [P] [US0] Integration test for pilot study data flow (Rating -> Storage -> Correlation) in `tests/test_metrics.py`

### Implementation for User Story 0

- [ ] T014 [US0] **Fetch Real Stimuli**: Implement `src/metrics/fetch_stimuli.py` to Download a representative set of real background images from the NAB dataset. **Specific Source**: Fetch files matching `https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/artificial_anomaly.csv` or the associated image archive if available. If NAB images are not directly available as a zip, use the `ucimlrepo` package to fetch the `NAB` dataset images. Ensure no synthetic/fake data is used. **Dependency**: Must be completed before T010-T013 and T019.
- [ ] T014b [US0] **Verify Stimuli**: Implement `src/metrics/verify_stimuli.py` to compute and record the checksum of the downloaded NAB stimuli in `state/artifact_hashes`.
- [ ] T010 [US0] Implement `src/metrics/validate.py` to compute correlation between human ratings and automated metrics (entropy, variance, object count)
- [ ] T011 [US0] Implement `src/experiment/pilot_interface.py` (Flask) to present images and collect 1-10 complexity ratings from participants (Local UI only).
- [ ] T011b [US0] **Recruitment Logic**: Implement `src/experiment/recruitment.py` to facilitate participant recruitment (e.g., Prolific/MTurk integration logic, invitation email generation, participant management state) for the n=20 cohort.
- [ ] T011c [US0] **Data Ingestion**: Implement `src/experiment/ingest.py` to handle the data ingestion pipeline for external participants (parsing Prolific/MTurk exports) and saving to `data/measurements/human_ratings.csv`.
- [ ] T012 [US0] Implement data persistence for human ratings: save to `data/measurements/human_ratings.csv` with `image_id`, `participant_id`, `complexity_score`
- [ ] T013 [US0] Generate validation report (scatter plot + p-value) in `data/derived/pilot_validation_report.md`

**Checkpoint**: At this point, User Story 0 should be fully functional and testable independently

---

## Phase 4: User Story 1 - Compute Visual Complexity Metrics (Priority: P1)

**Goal**: Extract quantitative visual complexity metrics (image entropy, color variance, object detection counts) from background frames using a CPU-compatible pipeline.

**Independent Test**: Run the metric extraction script on a static set of diverse background images and verify that the output JSON contains valid numerical values without errors.

### Tests for User Story 1

- [ ] T015 [P] [US1] Unit test for entropy calculation in `tests/test_metrics.py`
- [ ] T016 [P] [US1] Unit test for color variance calculation in `tests/test_metrics.py`
- [ ] T017 [P] [US1] Integration test for YOLOv8n CPU inference on 1080p batch in `tests/test_metrics.py` (verify < 30s runtime, < 2GB RAM; MUST use isolated temporary directories and model cache isolation to ensure parallel safety)
- [ ] T018 [P] [US1] Contract test for "blank background" edge case (zero object count) in `tests/test_metrics.py` (MUST use isolated temporary directories to ensure parallel safety)
- [ ] T018a [P] [US1] Setup isolated test data directories in `tests/data/` and populate with dummy images for T017/T018 isolation

### Implementation for User Story 1

- [ ] T019 [US1] Implement `src/metrics/extract.py` to compute image entropy, color variance, and object detection counts using **YOLOv8n** on **CPU only**. **Acceptance Criteria**: Accept 1080p input images (1920x1080) but perform internal inference on a 640x640 resized copy to meet the updated NFR-001 (from T000). Verify that the **total** pipeline time (I/O + Resize + Inference) for 10 images is <30s and RAM <2GB. Explicitly enforce CPU-only execution and YOLOv8n usage.
- [ ] T019a [US1] **Performance Verification**: Implement `tests/test_metrics_performance.py` to explicitly verify the <30s total pipeline time and <2GB RAM for T019. This test MUST produce a log artifact `data/derived/performance_log.txt` containing the exact timing and memory usage metrics.
- [ ] T020 [US1] Add logic to handle images with no detectable objects gracefully (return 0 count, no crash)
- [ ] T021 [US1] Implement data persistence: save computed metrics to `data/processed/metrics.csv` with `frame_id`, `entropy`, `color_variance`, `object_count`
- [ ] T022 [US1] Implement `src/metrics/validate_against_human.py` to re-run correlation check on the full pilot dataset (US0) and flag if r < 0.5 (SC-001)
- [ ] T023 [US1] Implement fallback edge detection logic (Canny) in `src/metrics/extract.py` for cases where YOLO fails or is unavailable (FR-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 5: User Story 2 - Administer Cognitive Load Assessment (Priority: P2)

**Goal**: Present meeting clips to participants and capture their cognitive load response via the NASA-TLX self-report scale and a post-task reaction-time task.

**Independent Test**: Simulate a participant session where a clip is shown, the NASA-TLX form is submitted, and the reaction-time task is completed, verifying that the resulting data record links the participant ID, clip ID, and response metrics correctly.

### Tests for User Story 2

- [ ] T024 [P] [US2] Unit test for Latin Square counterbalancing logic in `tests/test_experiment.py`
- [ ] T025 [P] [US2] Integration test for baseline reaction-time task logic in `tests/test_experiment.py`
- [ ] T026 [P] [US2] Test for missing data flagging logic (exclusion vs. imputation) in `tests/test_experiment.py`

### Implementation for User Story 2

- [ ] T032 [US2] **Real Data Fetch**: Implement `src/experiment/fetch_clips.py` to download real meeting background clips from the **MeetingBench** dataset. **Specific Source**: Use the HuggingFace dataset `MeetingBench/meeting-clips-v` (or the specific verified version ID). Ensure the dataset ID is recorded in `research.md`. **Dependency**: Must be completed before T029.
- [ ] T032b [US2] **Verify Clips & Record Source**: Implement `src/experiment/verify_clips.py` to compute the SHA-256 checksum of the downloaded MeetingBench clips, record the specific dataset URL (`https://huggingface.co/datasets/MeetingBench/meeting-clips-v1`) and version ID in `state/artifact_hashes` and `research.md` to satisfy Constitution Principle II (Verified Accuracy). **Dependency**: Must run immediately after T032.
- [ ] T027 [US2] Implement `src/experiment/counterbalance.py` to generate Latin Square designs for clip ordering (FR-002c)
- [ ] T028 [US2] Implement `src/experiment/tasks.py` to handle the baseline reaction-time task (FR-002b) and experimental trials
- [ ] T029 [US2] Implement `src/experiment/server.py` (Flask) to present clips, capture NASA-TLX scores, and record reaction times (FR-002). **Dependency**: Requires T032 (clips) to be complete.
- [ ] T030 [US2] Add logic to flag incomplete records (missing TLX or RT) for exclusion in the generated dataset
- [ ] T031 [US2] Save generated participant sessions to `data/measurements/raw/participant_sessions.csv` with `participant_id`, `clip_id`, `nasa_tlx_score`, `reaction_time`, `accuracy`, `baseline_rt`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Execute linear mixed-effects models to correlate visual complexity metrics with cognitive load outcomes, controlling for task difficulty and participant ID, while applying multiple-comparison corrections and checking for multicollinearity.

**Independent Test**: Run the analysis script on a pre-generated synthetic dataset with known correlations and verify that the output report correctly identifies the significant predictors, reports adjusted p-values, and includes multicollinearity diagnostics.

### Tests for User Story 3

- [ ] T033 [P] [US3] Unit test for Benjamini-Hochberg correction implementation in `tests/test_analysis.py`
- [ ] T034 [P] [US3] Unit test for VIF calculation and threshold flagging (>5) in `tests/test_analysis.py`
- [ ] T035 [P] [US3] Integration test for full pipeline (Metrics + Participant Data -> Model -> Report) in `tests/test_analysis.py`

### Implementation for User Story 3

- [ ] T036 [US3] Implement data integration logic to merge `data/processed/metrics.csv` and `data/measurements/raw/participant_sessions.csv` into a single analysis-ready dataframe. **Dependency**: Must wait for T021 and T031 completion. Explicitly verify T021 and T031 outputs exist before proceeding.
- [ ] T037 [US3] Implement `src/analysis/models.py` to execute linear mixed-effects models with visual complexity as predictor and cognitive load as outcome (FR-003)
- [ ] T038 [US3] Implement VIF calculation in `src/analysis/models.py`; if VIF > 5, flag instability and trigger PCA fallback (FR-003)
- [ ] T039 [US3] Implement PCA fallback mechanism in `src/analysis/models.py`: If VIF > 5, combine predictors via PCA to reduce multicollinearity
- [ ] T040 [US3] Implement Benjamini-Hochberg correction for multiple hypothesis tests in `src/analysis/corrections.py` (FR-004)
- [ ] T041 [US3] Implement `src/analysis/sensitivity.py` to sweep p-value thresholds across a range of conventional significance levels and report effect size stability. **Output Requirement**: Must explicitly calculate and report the **standard deviation of effect sizes** across thresholds. This metric MUST be written to `data/derived/sensitivity_report.csv` in a column named `sd_effect_size`.
- [ ] T042 [US3] Implement `src/analysis/null_sim.py` to run a null-simulation (effect size = 0) to calculate and report the observed family-wise error rate (FWER) (FR-007)
- [ ] T043 [US3] Implement `src/analysis/report_gen.py` to generate the final report with fixed effect estimates, confidence intervals, adjusted p-values, VIF scores, and FWER

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Update `docs/quickstart.md` with specific CPU-only setup instructions and YOLOv8n installation steps
- [ ] T045 [P] Update `docs/data-model.md` with new entity attributes and metric definitions
- [ ] T046 [P] Update `docs/contracts/` with final API/Interface definitions
- [ ] T047 [P] Additional unit tests for edge cases (skewed distributions, attention check failures) in `tests/`
- [ ] T048a [P] **Automated Reproducibility Script**: Implement `src/cli/validate_quickstart.py`. This script MUST: 1) Spin up a fresh temp directory, 2) Install dependencies, 3) Run T014 (Fetch NAB), T019 (Extract Metrics), T036-T043 (Analysis) on a **pre-seeded mock dataset** (skipping US0 Human Pilot which requires real humans), and 4) Verify checksums of derived artifacts against `state/artifact_hashes`.
- [ ] T048b [P] **Automated Reproducibility Test**: Implement `tests/test_quickstart.py` to assert that T048a exits with code 0 and produces the expected artifacts (`data/derived/performance_log.txt`, `data/derived/sensitivity_report.csv`, etc.).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Phase 0 (Spec Alignment)**: Must be completed before Phase 1 to ensure spec/tasks consistency.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **US0 (P0)**: Must be completed first to validate metrics before US1/US2 proceed to main study.
  - **US1 (P1)**: Depends on US0 validation (metrics must be proven valid).
  - **US2 (P2)**: Can run in parallel with US1 (once US1 metrics logic is stable) but requires real stimuli (US0/US1 fetch).
  - **US3 (P3)**: Must wait for US1 (metrics) and US2 (data) to be generated before running the model.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 0 (P0)**: Can start after Foundational (Phase 2).
- **User Story 1 (P1)**: Can start after Foundational (Phase 2) + US0 validation passed.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) + US0/US1 stimuli fetch complete.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Must** wait for US1 (metrics) and US2 (data) to be generated before running the model.

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
Task: "Implement src/metrics/extract.py"
Task: "Implement src/metrics/validate_against_human.py"
```

---

## Implementation Strategy

### MVP First (User Story 0 & 1 Only)

1. Complete Phase 0: Spec Alignment (T000)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 0 (Pilot Validation)
5. Complete Phase 4: User Story 1 (Metric Extraction)
6. **STOP and VALIDATE**: Test US0/US1 independently on sample images and ensure metrics correlate with human ratings (r > 0.5).
7. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 0 (Pilot) → Validate metrics → Deploy/Demo (MVP!)
3. Add User Story 1 (Metrics) → Test independently → Deploy/Demo
4. Add User Story 2 (Data Collection) → Test independently → Deploy/Demo
5. Add User Story 3 (Analysis) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 0 (Pilot) & User Story 1 (Metrics)
   - Developer B: User Story 2 (Data Collection)
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
- **CRITICAL**: Dataset fetch tasks (T014, T032) must use real, reachable URLs or Python-package-based fetch (e.g., `ucimlrepo`, `datasets.load_dataset`), not "download from UCI" without specifics.
- **CRITICAL**: NFR-001 compliance is achieved by processing 1080p input but performing internal inference on 640x640 resized copies, with total pipeline time (I/O+Resize+Inference) <30s (per T000 update).
- **CRITICAL**: T048a must skip US0 (Human Pilot) and use mock data to ensure automated reproducibility.