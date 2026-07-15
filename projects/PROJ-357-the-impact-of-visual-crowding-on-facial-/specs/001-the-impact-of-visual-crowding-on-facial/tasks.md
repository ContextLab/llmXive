# Tasks: The Impact of Visual Crowding on Facial Emotion Recognition Accuracy

**Input**: Design documents from `/specs/001-visual-crowding-emotion-recognition/`
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

- [ ] T002 [P] Create `projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/` root directory and subdirectories: `code/`, `data/`, `tests/`, `artifacts/`, `state/projects/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement `code/utils/hygiene.py` to compute SHA256 checksums for `data/` and `artifacts/` and update `state/projects/PROJ-357-...yaml`
- [X] T007 Create `code/config.py` to manage environment variables and random seeds

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stimuli Generation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Programmatically generate controlled visual crowding stimuli from the RAVDESS dataset with parametric control over flanker count, eccentricity, and emotion.

**Independent Test**: Run the stimulus generation script and verify that output images exist with a manifest file containing emotion category, flanker count, and eccentricity values.

### Implementation for User Story 1

- [ ] T011a [P] [US1] **Verify RAVDESS Source**: Query the official HuggingFace API to validate the RAVDESS dataset URL. If `spec.md` FR-001 URL is empty, default to the verified canonical URL `parlance/RAVDESS` and document the resolution in `code/config.py`.
- [ ] T011 [P] [US1] Implement `code/utils/download.py` to fetch RAVDESS dataset from the verified URL (from T011a) and cache in `data/raw`.
- [ ] T012 [P] [US1] Implement `code/utils/frame_extractor.py` to extract frames from RAVDESS video files into `data/raw/frames`
- [X] T013 [US1] Implement `code/utils/stimulus_gen.py` to:
 - Load frames and filter by multiple emotion categories
 - **If an emotion category is missing from the dataset, log a warning, exclude it from generation, and proceed with available categories** (Edge Case)
 - Generate stimuli with varying flanker counts (≥3 levels) and eccentricities
 - Detect and exclude overlapping flankers (Edge Case)
 - **Explicitly record exact flanker count and eccentricity for every generated image**
 - **Write exclusion reasons to `data/interim/generation_errors.log`**
 - Output generated images to `data/interim/stimuli`
- [ ] T014 [US1] Generate `data/interim/stimuli_manifest.json` by:
 - **Reading `data/interim/generation_errors.log` (T013) to update 'status' fields for excluded items**
 - **Validating that every image in `data/interim/stimuli` has a corresponding entry with exact flanker count and eccentricity values**
 - Linking file paths to metadata (emotion, flanker count, eccentricity)
- [~] T015 [US1] **Validate manifest completeness**: Verify that every image in `data/interim/stimuli` has a corresponding entry in `stimuli_manifest.json` with exact parameter values (Constitution Principle VI)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T008 [P] [US1] Unit test for frame extraction logic in `tests/unit/test_frame_extractor.py`
- [X] T009 [P] [US1] Unit test for stimulus composition and overlap detection in `tests/unit/test_stimulus_gen.py`
- [X] T010 [P] [US1] Integration test for full pipeline in `tests/integration/test_pipeline.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Clutter Metric Computation (Priority: P2)

**Goal**: Compute visual clutter metrics (local contrast variance, spatial frequency energy) for each generated stimulus.

**Independent Test**: Run the metric computation script on a subset of stimuli and verify numeric values are produced for all entries with no missing data.

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/utils/clutter_metrics.py` to compute local contrast variance and spatial frequency energy for the flanker region of each stimulus **consuming `stimuli_manifest.json` (T014) and generated images from `data/interim/stimuli` (T013)**
- [ ] T020 [US2] Implement chunked processing in `code/utils/clutter_metrics.py` to ensure memory usage stays < 7 GB (Constraint)
- [ ] T021 [US2] **Implement sampling fallback mechanism**: Add logic to `code/utils/clutter_metrics.py` to automatically switch to dataset sampling if chunked processing still exceeds available memory capacity (Edge Case)
- [ ] T022 [US2] Generate `data/processed/clutter_metrics.csv` joining metrics to `stimuli_manifest.json` via file path

### Verification & Exploratory Analysis

- [ ] T023 [US2] **Mandatory Validation**: Generate `data/processed/validation_report.json` confirming that clutter metrics (spatial frequency energy) correlate with flanker count (p < 0.05). This is a blocking gate for Phase 4 completion.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 4 - Human Emotion-Judgment Data Collection (Priority: P2)

**Goal**: Collect human observer recognition accuracy data for the generated stimuli to serve as the outcome variable. **Note: Due to CI constraints, this will be satisfied by synthetic data generation that mimics real human pilot data.**

**Independent Test**: Run the synthetic pilot study with ≥5 simulated participants and verify that recognition accuracy is recorded for each stimulus with participant IDs and response labels.

### Implementation for User Story 4

- [ ] T025 [US4] Implement `code/analysis/synthetic_data_generator.py` (headless, batch-mode) to generate synthetic recognition responses for the stimuli in `stimuli_manifest.json`. The generator must simulate ≥5 unique participant IDs and produce realistic accuracy distributions (e.g., 60-90% accuracy depending on crowding) for 8-category classification.
- [ ] T026 [US4] Implement `code/analysis/pilot_runner.py` CLI script to orchestrate the synthetic pilot study, load `stimuli_manifest.json`, and manage the generation of raw response data.
- [ ] T028 [US4] Implement `code/analysis/data_loader.py` to load and validate raw synthetic judgment CSVs (Participant ID, Stimulus ID, True Label, Response Label, Timestamp)
- [ ] T029 [US4] Implement logic to compute `accuracy` (correct/incorrect) and aggregate by stimulus ID, emotion, and flanker count
- [ ] T027 [US4] **Execute Synthetic Pilot**: Run `pilot_runner.py` (T026) with `synthetic_data_generator.py` (T025) to generate raw synthetic response data for the generated stimuli.
- [ ] T030 [US4] Generate `data/processed/human_judgments.csv` with required fields: participant_id, stimulus_id, emotion_label, response_label, accuracy, flanker_count, eccentricity
- [ ] T031 [US4] Create a pilot data generation script `code/analysis/generate_synthetic_data.py` for *unit testing only* (not for research results) to simulate a small cohort of participants for pipeline validation

**Checkpoint**: At this point, User Stories 1, 2, and 4 should be functional with data ready for analysis

---

## Phase 6: User Story 3 - Associational Analysis & Reporting (Priority: P3)

**Goal**: Perform a Generalized Linear Mixed Model (GLMM) to correlate clutter metrics with human recognition accuracy.

**Independent Test**: Run the analysis script on sample data and verify that regression coefficients, p-values, and model diagnostics are produced.

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/analysis/glmm_model.py` to fit a binomial GLMM with clutter metrics as fixed effects and participant/stimulus as random effects
- [ ] T034 [US3] Implement fallback logic: if GLMM fails to converge, fit a fixed-effects only model and log the warning (Edge Case)
- [ ] T035 [US3] Implement multiple-comparison correction (Benjamini-Hochberg FDR ≤ 0.05) for hypothesis tests (FR-005)
- [ ] T036 [US3] Implement `code/analysis/reporting.py` to generate a final report framing findings as associational (FR-006)
- [ ] T037 [US3] Generate `artifacts/model_config.yaml` with hyperparameters, seeds, and model diagnostics
- [ ] T038 [US3] Generate `data/processed/regression_results.json` containing coefficients, confidence intervals, and p-values

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test for GLMM convergence and fallback logic in `tests/unit/test_glmm_fallback.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Run `code/utils/hygiene.py` to update state hashes for all final artifacts
- [ ] T040 [P] Documentation updates in `specs/001-visual-crowding-emotion-recognition/quickstart.md`
- [ ] T041 Run full pipeline integration test in `tests/integration/test_pipeline.py`
- [ ] T042 Verify all tasks complete within 6 hours on CPU-only runner (Constraint)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (stimuli)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (stimuli)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 (metrics) and US4 (human data)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US4 can start in parallel (US3 must wait for US2/US4 data)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for frame extraction logic in tests/unit/test_frame_extractor.py"
Task: "Unit test for stimulus composition and overlap detection in tests/unit/test_stimulus_gen.py"

# Launch all models for User Story 1 together:
Task: "Implement code/utils/download.py to fetch RAVDESS dataset"
Task: "Implement code/utils/frame_extractor.py to extract frames"
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
4. Add User Story 4 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Stimuli)
 - Developer B: User Story 2 (Metrics)
 - Developer C: User Story 4 (Human Data - Synthetic)
3. Once data is ready:
 - Developer A/B/C or D: User Story 3 (Analysis)
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
- **Constraint Reminder**: All tasks must run on free CPU-only CI with limited CPU resources and GB RAM (no GPU). No 8-bit quantization or large model training.
- **Data Integrity**: Do not fabricate data. Use real RAVDESS dataset and synthetic data (with statistical validity) for human judgment data as specified in US-4 and tasks.md T025-T030.