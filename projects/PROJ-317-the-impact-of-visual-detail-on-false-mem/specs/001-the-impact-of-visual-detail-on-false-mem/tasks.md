# Tasks: Visual Detail and False Memory Susceptibility

**Input**: Design documents from `/specs/001-visual-detail-false-memory/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in `projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/` by running: `mkdir -p data/stimuli data/stimuli_metadata data/responses data/processed data/ethics data/assets code/data code/stimuli code/participants code/analysis tests/unit tests/integration tests/contract docs/ethics`.

- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup data directory structure: `data/stimuli/`, `data/responses/`, `data/processed/`, `data/stimuli_metadata/`, `data/ethics/`, `data/assets/`
- [X] T005 [P] Implement data checksum utilities in `code/data/checksum.py`
- [X] T013 [P] [US1] Implement Image Entity class in `code/data/image.py`: Define `Image` class with attributes `id`, `path`, `complexity_score`, `metadata_path`.
- [X] T014 [P] [US1] Implement Participant and Response Entity classes in `code/data/participant.py`: Define `Participant` (id, condition, timestamp) and `Response` (id, question_id, value, timestamp) classes.
- [X] T008 Configure logging infrastructure in `code/utils/logging.py`
- [X] T009 [P] Setup environment configuration management in `code/config.py`
- [ ] T010 [P] [US1] Generate ethics artifacts: Create `data/ethics/informed_consent.md` and `data/ethics/irb_placeholder.md` using the template `docs/ethics/gdpr_consent_template.md` as the base. **Mandatory Clauses**: Must include 'Data Usage', 'Right to Withdraw', 'Contact Info', and 'GDPR-compliant Anonymization Workflow' (referencing GDPR Art. 6 & 7). **Verification**: Must include a verification step to ensure a real IRB approval document exists before recruitment begins; if no IRB doc is found, the task must fail. Must integrate the specific project ID (PROJ-317) into the consent workflow.
- [ ] T012 [US1] Implement Power Analysis in `code/analysis/stats.py`: Calculate required sample size for alpha=0.05, power=0.80, effect_size=medium (Cohen's f=0.25) using `statsmodels.stats.power.FTestAnovaPower`. **Output**: Write results to `data/analysis/power_report.json` with keys `n_per_group`, `total_n`, `effect_size`, `power`, `alpha`. **Constraint**: If calculated N < 50, the task MUST raise an error and halt the pipeline. [UNRESOLVED-CLAIM: c_0ef6956b — status=not_enough_info] **Dependency**: None.
- [ ] T012.1 [US1] [Gate] Verify Power Analysis Gate: **Action**: Check for existence of `data/analysis/power_report.json` and validate that `total_n >= 50`. **Constraint**: If the file is missing or N < 50, the task MUST fail and halt the entire pipeline start. **Dependency**: T012.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Image Manipulation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Researcher uploads baseline images and receives two manipulated versions per image (enhanced and reduced detail).

**Independent Test**: Can be fully tested by running the image manipulation script on multiple sample images and verifying output files exist with correct detail modifications.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T050 [P] [US1] Unit test for image enhancement logic in `tests/unit/test_stimuli_manipulator.py`: Implement `test_add_minor_objects()`. Assert that `output_image.shape == (512, 512, 3)` (fixed dimensions) and `object_count == 5` after calling `add_minor_objects()`.
- [ ] T051 [P] [US1] Unit test for image reduction logic in `tests/unit/test_stimuli_manipulator.py`: Implement `test_remove_minor_elements()`. Assert that `std_dev(output_region) < 0.1 * std_dev(input_region)` where `input_region` is the masked area of the original image and `output_region` is the same area after blurring.
- [ ] T052 [P] [US1] Integration test for full pipeline (generate → manipulate → metadata) in `tests/integration/test_stimuli_pipeline.py`: Implement `test_full_pipeline()`. Assert that at least 1 metadata file and 2 manipulated images (enhanced/reduced) are created for each input image.

### Implementation for User Story 1

- [ ] T006.1 [US1] Implement Real Dataset Fetcher and Filter (COCO 2017) in `code/stimuli/downloader.py`: **Algorithm**: Stream images from COCO 2017 using `datasets.load_dataset('coco_2017', split='train', streaming=True)`. **Filtering**: Calculate object density/complexity for each image and select a representative sample spanning Q1-Q3 (range >= 0.3). **Constraint**: Must NOT fallback to synthetic data. **Error Handling**: If fetch fails for an *individual image*, skip the image and log the error to `data/logs/manipulation_errors.log`. If the *entire* dataset fetch fails, raise a critical error. Output filtered images to `data/stimuli/raw/` and log stats to `data/processed/complexity_stats.json`. **Dependency**: None.
- [ ] T006.2 [US1] Implement complexity score calculation and calibration in `code/stimuli/filter.py`: Calculate `baseline_complexity_score` for downloaded images. **Algorithm**: Filter the fetched image set to ensure the Q1-Q3 range is >= 0.3 (target mean=0.5, std=0.15). **Constraint**: Complexity is derived from existing image annotations; do NOT adjust generation parameters. Output stats to `data/processed/complexity_stats.json`. **Dependency**: T006.1.
- [ ] T015.1 [P] [US1] Generate minor object assets: Create a script in `code/stimuli/asset_generator.py` to generate a set of 20 minor object PNG assets (circles, squares, triangles) with random colors and save them to `data/assets/minor_objects/`.
- [ ] T015 [US1] Implement enhanced detail compositing with error handling in `code/stimuli/manipulator.py`: Use PIL/Pillow to overlay a small number of minor object PNG assets (generated by T015.1) onto baseline images (from T006.1). **Source**: Assets loaded from `data/assets/minor_objects/`. **Selection**: Randomly select a small number of assets per image. **Error Handling**: If manipulation fails for an image, skip the image, log the error to `data/logs/manipulation_errors.log`, and continue processing the remaining images. Do NOT abort the pipeline. **Dependency**: T015.1.
- [ ] T016 [US1] Implement reduced detail manipulation with error handling in `code/stimuli/manipulator.py`: Use Gaussian blur (radius=5) or masking to remove minor elements from baseline images. **Error Handling**: If manipulation fails for an image, skip the image, log the error to `data/logs/manipulation_errors.log`, and continue processing the remaining images. Do NOT abort the pipeline. **Dependency**: T015.1.
- [ ] T017 [US1] Implement stimulus metadata generation (YAML) per Constitution VII in `code/stimuli/metadata.py`.
- [ ] T019 [P] [US1] Add error handling for missing metadata and failed fetches in `code/data/loader.py`: If a real dataset fetch (if implemented) fails or metadata is missing, skip the image and log the error.
- [ ] T020 [P] [US1] Add CLI entry point for running the manipulation pipeline in `code/cli.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Participant Testing Interface (Priority: P2)

**Goal**: Participant views baseline image, completes distractor task, and answers recognition questions (true vs. false details).

**Independent Test**: Can be fully tested by simulating a single participant session end-to-end and verifying that all responses are recorded correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Unit test for session state management in `tests/unit/test_session.py`
- [ ] T023 [P] [US2] Unit test for response generation logic in `tests/unit/test_interface.py`
- [ ] T024 [P] [US2] Integration test for simulated session flow in `tests/integration/test_session_flow.py`

### Implementation for User Story 2

- [ ] T027.1 [P] [US2] Generate mock object pool: Create `data/assets/mock_objects.json` containing a list of 50 distinct object names and categories (e.g., `[{ "object_name": "red car", "category": "vehicle" }]`).
- [ ] T025 [P] [US2] Implement simulated participant interface logic (image display, timing) in `code/participants/interface.py`: Enforce 10-second display duration (±0.5s) for baseline images as per US-2.
- [ ] T026 [US2] Implement distractor task logic (arithmetic questions) in `code/participants/interface.py`: Enforce 2-minute duration (±10s) for the distractor task as per US-2. **Verification**: Implement an assertion or check to ensure the task duration is within [110s, 130s] (2 min ± 10s).
- [ ] T027.2 [US2] Implement recognition question generator logic in `code/participants/interface.py`: Extract true details from `data/stimuli_metadata/{id}.yaml`. Generate false/lure details by selecting from the predefined mock object pool (`data/assets/mock_objects.json` generated by T027.1) and **filtering out any items present in the baseline metadata (set difference on 'object_name')** to ensure they never appeared. **Constraint**: Must ensure false details are absent from the baseline. **Hard Constraint**: If the set difference yields an insufficient number of unique items, the task MUST raise an error; do NOT fallback to synthetic or overlapping items. **Verification Loop**: After regeneration, re-check against `stimuli_metadata.yaml` to ensure the new items are not present in the baseline. If overlap is detected, regenerate again until unique items are found. **Schema**: `data/assets/mock_objects.json` must contain keys: 'object_name', 'category', 'visual_features'. **Dependency**: T017, T027.1.
- [ ] T027.3 [US2] Implement response capture and timestamp logging in `code/participants/session.py`
- [ ] T029 [US2] Implement local caching and retry logic for network timeouts in `code/participants/session.py`
- [ ] T030 [US2] Implement partial session recording and flagging for dropouts in `code/participants/session.py`
- [ ] T031 [US2] Add CLI entry point for running simulated participant sessions in `code/cli.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Results Generation (Priority: P3)

**Goal**: System executes repeated-measures ANOVA and generates visualization with confidence intervals.

**Independent Test**: Can be fully tested by running the analysis script on synthetic/mock participant data and verifying ANOVA results and visualization are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test for ANOVA calculation in `tests/unit/test_stats.py`
- [ ] T033 [P] [US3] Unit test for multiple-comparison correction in `tests/unit/test_stats.py`
- [ ] T034 [P] [US3] Integration test for full analysis pipeline on mock data in `tests/integration/test_analysis_pipeline.py`

### Implementation for User Story 3

- [ ] T038 [US3] Implement dataset-variable fit check (compare mock distribution to target) in `code/analysis/stats.py`: **Dependency**: Must run before T035 to ensure data validity.
- [ ] T035 [US3] Implement repeated-measures ANOVA using scipy.stats in `code/analysis/stats.py`. **Output**: Write results to `data/analysis/anova_results.json` with keys `f_statistic`, `p_value`, `effect_size`, `degrees_of_freedom`. **Dependency**: T038, T012.1.
- [ ] T036 [US3] Implement multiple-comparison correction (Bonferroni) in `code/analysis/stats.py`. **Dependency**: T035.
- [ ] T037 [US3] Implement visualization generation (mean false memory rates with confidence intervals) in `code/analysis/viz.py`. **Dependency**: T035.
- [ ] T039 [US3] Add CLI entry point for running analysis in `code/cli.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Scope Boundary & Reviewer Response (Revision Response)

**Goal**: Address reviewer concerns regarding the lack of a biological mechanism while strictly adhering to the project's "associational" scope and Constitution VI (Human Subjects Ethics).

**Context**: The reviewer (Eric Kandel-simulated) requested a hypothesis linking visual detail to synaptic changes (e.g., CREB, PKA). However, the project spec explicitly defines the scope as **behavioral only** (associational, not causal) and Constitution VI explicitly **excludes** biological mechanism mapping tasks. The project cannot measure synaptic changes in human subjects; it can only measure behavioral correlates.

**Strategy**: Instead of implementing untestable biological claims, we will:
1. Explicitly document the **Scope Boundary** in `docs/ethics/scope_boundary.md` and `research.md`.
2. Add a **Theoretical Framework** task that cites established literature (e.g., Loftus, Schacter) to explain the *behavioral* mechanism (constructive memory) without making unverified claims about specific synaptic pathways in humans.
3. Ensure the analysis output frames results as "associational evidence" rather than "mechanistic proof".
4. Provide a formal response to the reviewer acknowledging the biological question while explaining the methodological constraints of human behavioral research.

- [ ] T060.1 [US3] **Scope Boundary Documentation (Create)**: Create `docs/ethics/scope_boundary.md`. **Content**: Explicitly state that this study measures *behavioral* false memory rates and does not measure or infer specific molecular/cellular mechanisms (e.g., CREB activation, synaptic weight changes) in humans. Cite Constitution VI and the "Associational vs. Causal" constraint.
- [ ] T060.2 [US3] **Scope Boundary Documentation (Write)**: Write the content for `docs/ethics/scope_boundary.md` detailing the exclusion of biological mechanism mapping.
- [ ] T061.1 [US3] **Citation Validation**: Run the 'Reference-Validator Agent' on new citations (Loftus, Schacter) before updating `research.md` to satisfy Constitution II.
- [ ] T061.2 [US3] **Theoretical Framework Update (Documentation Only)**: Update `research.md` to include a section "Theoretical Framework: Constructive Memory vs. Biological Mechanism". **Content**: Cite Loftus et al. (misinformation effect) and Schacter (seven sins of memory) to explain the *psychological* mechanism of false memory. Explicitly contrast this with the *biological* mechanisms (e.g., Kandel's Aplysia work) to clarify that while the latter inspires the former, this study does not claim to measure synaptic changes. **Constraint**: This task is for documentation purposes only; no biological mechanism mapping is implemented.
- [ ] T062 [US3] **Analysis Output Framing**: Update `code/analysis/stats.py` (T035) and `code/analysis/viz.py` (T037) to ensure all printed outputs and plot titles use language such as "Associational Evidence," "Behavioral Correlate," or "Statistical Association" rather than "Mechanism," "Cause," or "Synaptic Change".
- [ ] T063 [US3] **Reviewer Response Artifact**: Create `docs/reviews/review_response_001.md`. **Content**: A formal response to the Eric Kandel-simulated review, acknowledging the importance of the biological question, explaining the scope constraints (Constitution VI), and detailing how the project remains scientifically rigorous within its behavioral bounds.

**Checkpoint**: Scope is explicitly defined, biological claims are removed/clarified, and reviewer concerns are formally addressed in documentation.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in `docs/` (including ethics placeholders and scope boundary)
- [ ] T045 [Summary] Code cleanup and refactoring across `code/` (Summary task only; see sub-tasks below)
- [ ] T045.1 [P] Refactor error handling logic into a utility module in `code/utils/error_handling.py`
- [ ] T045.2 [P] Extract magic numbers and constants to `code/config.py`
- [ ] T046 Performance optimization for image manipulation (ensure < 30s/image)
- [ ] T047 [P] Additional unit tests for edge cases (dropout, network timeout) in `tests/unit/`
- [ ] T048 Security hardening (ensure no PII leakage in logs)
- [ ] T049 [P] Run quickstart.md validation: **Blocked**: Requires T060, and T046 to be resolved first.

**Note on Removed Phase 6**: Phase 6 (Mechanism Mapping) and tasks T040-T042 from the *previous* iteration were removed. The new T060-T063 in this revision are specifically for *documenting* the scope boundary and *responding* to the reviewer, not for implementing the biological mechanism itself.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Scope Clarification (Phase 6)**: Depends on Foundational phase; can be done in parallel with US3 implementation.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 (uses manipulated images) but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data generation
- **Scope Clarification (Phase 6)**: Can start after Foundational; depends on US3 for analysis framing.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Critical Task Dependencies

- **T012/T012.1 (Power Analysis)**: T012 is independent. T012.1 is a blocking gate for the entire pipeline.
- **T027.2 (Recognition Question Generator)**: Blocked by **T017** (Stimulus Metadata Generation) and **T027.1** (Mock Object Pool).
- **T015/T016 (Manipulation)**: Blocked by **T006.1** (Data Fetch) and **T015.1** (Asset Generation). T015/T016 include the skip/log logic internally.
- **T038 (Dataset-variable fit check)**: Must run before **T035** (ANOVA).
- **T060-T063 (Scope Clarification)**: Blocked by T012.1 (Power Analysis Gate) and T035/T037 (Analysis implementation) to ensure the documentation accurately reflects the final analysis capabilities.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Scope Clarification (Phase 6) can be worked on in parallel with US3 implementation.

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
 - Developer D: Scope Clarification (Phase 6)
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
- **Critical Revision Note**: Tasks T060-T063 are added in direct response to the Eric Kandel-simulated review. They clarify the scope boundary and ensure the project does not overclaim biological mechanisms, adhering to Constitution VI.
- **Critical Revision Note**: T006.1 now implements the COCO 2017 fetch and filtering, resolving the Visual Genome deviation. T018 is removed and its logic integrated into T015/T016.
- **Critical Revision Note**: T012 is now independent of T006.2 and uses fixed effect size assumptions. T012.1 is the blocking gate.
- **Critical Revision Note**: Test tasks for US1 are renumbered to T050-T052 to avoid ID collisions.
- **Critical Revision Note**: T015 and T016 are no longer marked [P] as they depend on T015.1.
- **Critical Revision Note**: T006.1 is no longer marked [P] in the context of the phase to avoid confusion with T006.2.