# Tasks: Visual Detail and False Memory Susceptibility

**Input**: Design documents from `/specs/001-visual-detail-false-memory/`
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

- [X] T001 Create project structure per implementation plan in `projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/` by running: `mkdir -p data/stimuli data/stimuli_metadata data/responses data/processed data/ethics code/data code/stimuli code/participants code/analysis tests/unit tests/integration tests/contract docs/ethics`.

- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup data directory structure: `data/stimuli/`, `data/responses/`, `data/processed/`, `data/stimuli_metadata/`, `data/ethics/`
- [X] T005 [P] Implement data checksum utilities in `code/data/checksum.py`
- [X] T006 [P] Implement Mock Visual Genome Generator in `code/data/loader.py`: Create a script that generates synthetic images with calibrated complexity scores (mean=0.5, std=0.15, ensuring Q1-Q3 range >= 0.3) using PIL. Default to mock as per plan.md; do NOT implement runtime URL checks for verified sources.
- [X] T012 [P] Implement Power Analysis in `code/analysis/stats.py`: Calculate required sample size for alpha=0.05, power=0.80, effect_size=medium (Cohen's f=0.25) using `statsmodels.stats.power.FTestAnovaPower`. Output result as JSON to `data/processed/power_analysis.json`. This MUST run before Phase 4.
- [X] T013 [P] Implement Image Entity class in `code/data/image.py`: Define `Image` class with attributes `id`, `path`, `complexity_score`, `metadata_path`.
- [X] T014 [P] Implement Participant and Response Entity classes in `code/data/participant.py`: Define `Participant` (id, condition, timestamp) and `Response` (id, question_id, value, timestamp) classes.
- [X] T008 Configure logging infrastructure in `code/utils/logging.py`
- [X] T009 [P] Setup environment configuration management in `code/config.py`
- [X] T010 [P] Generate ethics artifacts: Create `data/ethics/informed_consent.md` and `data/ethics/irb_placeholder.md` with GDPR-compliant templates and placeholders for IRB approval as required by Constitution VI.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Image Manipulation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Researcher uploads baseline images and receives two manipulated versions per image (enhanced and reduced detail).

**Independent Test**: Can be fully tested by running the image manipulation script on multiple sample images and verifying output files exist with correct detail modifications.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for image enhancement logic in `tests/unit/test_stimuli_manipulator.py`: Implement `test_add_minor_objects()`. Assert that `output_image.shape == (height, width, 3)` and `object_count == 5` after calling `add_minor_objects()`. <!-- FAILED: unspecified -->
- [ ] T012 [P] [US1] Unit test for image reduction logic in `tests/unit/test_stimuli_manipulator.py`: Implement `test_remove_minor_elements()`. Assert that `output_image` has reduced texture variance compared to input in the masked region. <!-- FAILED: unspecified -->
- [ ] T013 [P] [US1] Integration test for full pipeline (generate → manipulate → metadata) in `tests/integration/test_stimuli_pipeline.py`: Implement `test_full_pipeline()`. Assert that multiple manipulated images and 1 metadata file are created for each input. <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [ ] T015 [P] [US1] Implement enhanced detail compositing in `code/stimuli/manipulator.py`: Use PIL/Pillow to overlay a small number of minor object PNG assets onto baseline images. <!-- FAILED: unspecified -->
- [X] T016 [P] [US1] Implement reduced detail manipulation in `code/stimuli/manipulator.py`: Use Gaussian blur (radius=5) or masking to remove minor elements from baseline images.
- [~] T017 [US1] Implement stimulus metadata generation (YAML) per Constitution VII in `code/stimuli/metadata.py`.
- [~] T018 [US1] Implement 'skip and log' logic for manipulation failures in `code/stimuli/manipulator.py`: If manipulation fails for an image, skip the image entirely (do not attempt metadata generation) and log the error to `data/logs/manipulation_errors.log` as required by Edge Cases.
- [~] T019 [US1] Add error handling for missing metadata and failed fetches in `code/data/loader.py`: If a real dataset fetch (if implemented) fails or metadata is missing, skip the image and log the error.
- [~] T020 [US1] Add CLI entry point for running the manipulation pipeline in `code/cli.py`
- [~] T021 [P] [US1] Implement Real Dataset Fetcher (Optional) in `code/data/loader.py`: If a verified Visual Genome URL is provided in config, fetch real images. Handle 'missing metadata' edge case by skipping and logging.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Participant Testing Interface (Priority: P2)

**Goal**: Participant views baseline image, completes distractor task, and answers recognition questions (true vs. false details).

**Independent Test**: Can be fully tested by simulating a single participant session end-to-end and verifying that all responses are recorded correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T022 [P] [US2] Unit test for session state management in `tests/unit/test_session.py`
- [~] T023 [P] [US2] Unit test for response generation logic in `tests/unit/test_interface.py`
- [~] T024 [P] [US2] Integration test for simulated session flow in `tests/integration/test_session_flow.py`

### Implementation for User Story 2

- [~] T025 [P] [US2] Implement simulated participant interface logic (image display, timing) in `code/participants/interface.py`
- [~] T026 [US2] Implement distractor task logic (arithmetic questions) in `code/participants/interface.py`
- [~] T027 [US2] Implement recognition question generator in `code/participants/interface.py`: Extract true details from `data/stimuli_metadata/{id}.yaml`. Generate false/lure details by inverting true details using a predefined mock object pool (e.g., map 'red car' -> 'blue car', 'chair' -> 'table') or selecting random objects from the pool.
- [~] T028 [US2] Implement response capture and timestamp logging in `code/participants/session.py`
- [~] T029 [US2] Implement local caching and retry logic for network timeouts in `code/participants/session.py`
- [~] T030 [US2] Implement partial session recording and flagging for dropouts in `code/participants/session.py`
- [~] T031 [US2] Add CLI entry point for running simulated participant sessions in `code/cli.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Results Generation (Priority: P3)

**Goal**: System executes repeated-measures ANOVA and generates visualization with confidence intervals.

**Independent Test**: Can be fully tested by running the analysis script on synthetic/mock participant data and verifying ANOVA results and visualization are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T032 [P] [US3] Unit test for ANOVA calculation in `tests/unit/test_stats.py`
- [~] T033 [P] [US3] Unit test for multiple-comparison correction in `tests/unit/test_stats.py`
- [~] T034 [P] [US3] Integration test for full analysis pipeline on mock data in `tests/integration/test_analysis_pipeline.py`

### Implementation for User Story 3

- [~] T035 [US3] Implement repeated-measures ANOVA using scipy.stats in `code/analysis/stats.py`
- [~] T036 [US3] Implement multiple-comparison correction (Bonferroni) in `code/analysis/stats.py`
- [~] T037 [US3] Implement visualization generation (mean false memory rates with confidence intervals) in `code/analysis/viz.py`
- [~] T038 [US3] Implement dataset-variable fit check (compare mock distribution to target) in `code/analysis/stats.py`
- [~] T039 [US3] Add CLI entry point for running analysis in `code/cli.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T040 [P] Documentation updates in `docs/` (including ethics placeholders)
- [~] T041 Code cleanup and refactoring across `code/` <!-- FAILED: unspecified -->
- [~] T042 Performance optimization for image manipulation (ensure < 30s/image)
- [~] T043 [P] Additional unit tests for edge cases (dropout, network timeout) in `tests/unit/`
- [~] T044 Security hardening (ensure no PII leakage in logs)
- [~] T045 Run quickstart.md validation <!-- FAILED: unspecified -->

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 (uses manipulated images) but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data generation

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
Task: "Unit test for image enhancement logic in tests/unit/test_stimuli_manipulator.py"
Task: "Unit test for image reduction logic in tests/unit/test_stimuli_manipulator.py"

# Launch all models for User Story 1 together:
Task: "Implement enhanced detail compositing (add minor objects) in code/stimuli/manipulator.py"
Task: "Implement reduced detail manipulation in code/stimuli/manipulator.py"
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
 - Developer A: User Story 1 (Stimuli)
 - Developer B: User Story 2 (Session)
 - Developer C: User Story 3 (Analysis)
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
- **Revision Note**:
 1. Removed T011 (Cellular hypothesis) to eliminate scope creep.
 2. Moved Power Analysis to Phase 2 (T012) to satisfy SC-002 (pre-data collection).
 3. Fixed entity paths to `code/data/` (T013, T014) to match plan.md.
 4. Added specific calibration parameters to T006 and false-detail logic to T027 for executability.
 5. Split error handling: T019 for fetch, T018 for manipulation metadata (with explicit skip logic).
 6. Added T021 for optional real dataset fetcher.
 7. Refined test tasks (T011, T012, T013) with specific assertions.
 8. Renamed Phase 5 T034 (Power Analysis) to T039 (Integration test) to avoid ID collision with T012.
 9. Removed redundant T018.1 and clarified T018 to enforce 'skip entire image' logic.
 10. Removed ambiguous dependency text from T015.