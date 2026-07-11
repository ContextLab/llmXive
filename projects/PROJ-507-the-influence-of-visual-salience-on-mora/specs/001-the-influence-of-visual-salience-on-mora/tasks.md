# Tasks: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Input**: Design documents from `/specs/001-visual-salience-moral-judgment/`
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
  
  Tasks MUST be organized by user story so each story can:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directory structure: `projects/PROJ-507-the-influence-of-visual-salience-on-mora/`, `code/`, `data/raw/`, `data/processed/`, `data/survey_responses/`, `tests/`
- [X] T001b [P] Create initial project files: `README.md`, `.gitignore`
- [X] T002a [P] Create `requirements.txt` with pinned versions: `opencv-python`, `Pillow`, `pandas`, `numpy`, `scipy`, `statsmodels`, `pingouin`, `flask`, `pytest`
- [X] T002b [P] Initialize a Python virtual environment (`python -m venv venv`) and install dependencies (`pip install -r requirements.txt`)

The research question, method, and references remain unchanged as they were not present in the original passage.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites & Data Acquisition)

**Purpose**: Core infrastructure, data acquisition, and curation that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase now includes Data Acquisition (formerly Phase O) to ensure correct data flow.

- [X] T004a [P] Create data directories: `data/raw`, `data/processed`, `data/survey_responses`
- [X] T004b [P] Create code and test directories: `code`, `tests`
- [X] T005 [P] Implement `code/config.py` with random seeds, path constants, and hyperparameters for manipulation
- [X] T006 [P] Setup `code/__init__.py` and package structure
- [X] T007 [P] Create base data models (Scenario, Stimulus, Response) in `code/data_models.py`
- [X] T008 [P] Configure logging infrastructure in `code/utils/logger.py`
- [X] T009 [P] Setup environment configuration management for local vs. CI paths

### Data Acquisition & Curation (Moved from Phase O to Phase 2)

- [X] T043 [P] [US1] Implement `code/dataset_loader.py` function to fetch a verified subset of COCO images from a specific HuggingFace dataset URL (e.g., `coco-2017`) and save raw metadata and images to `data/raw/coco_subset/`
- [X] T044 [US1] Implement `code/dataset_loader.py` to process the fetched COCO metadata and curate a list of multiple morally ambiguous scenarios (sufficient for power analysis) based on predefined semantic criteria, saving the list of IDs to `data/raw/curated_scenario_ids.json`
- [X] T045 [P] [US1] Add validation step in `code/dataset_loader.py` to verify that downloaded images exist and are readable before proceeding to manipulation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Salience Manipulation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Load curated scenarios from open datasets and generate manipulated stimuli with verified pixel statistics.

**Independent Test**: A script processes a sample set of images, generates multiple variants each, and outputs a manifest with pixel stats (mean brightness, SSIM) confirming manipulation without semantic alteration.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementing.**

- [X] T010 [P] [US1] Unit test for image loading and metadata parsing in `tests/unit/test_dataset_loader.py`
- [X] T011 [P] [US1] Unit test for pixel-statistics validation (SSIM, brightness delta) in `tests/unit/test_stimulus_gen.py`
- [X] T012 [P] [US1] Integration test for full pipeline (load -> manipulate -> save) in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/dataset_loader.py` to load the curated list from `data/raw/curated_scenario_ids.json` and parse metadata
- [X] T014 [US1] Implement curation logic in `code/annotation_pipeline.py` to filter the loaded COCO metadata into a final list of valid scenarios based on semantic criteria (input: `data/raw/coco_metadata.json`; output: `data/raw/curated_scenario_ids.json`), ensuring the system performs the curation itself rather than loading a pre-curated list.
- [X] T015 [US1] Implement `code/stimulus_gen.py` to apply contrast/brightness manipulation (low/medium/high) on target objects using OpenCV/PIL, explicitly **calculating and outputting the pixel-level similarity score (SSIM) for non-target regions** using the **COCO instance segmentation masks** to derive the non-target region mask, ensuring no visible artifacts are introduced
- [X] T016 [US1] Implement edge discontinuity and artifact detection checks in `code/stimulus_gen.py` to flag invalid manipulations and output a `valid` boolean
- [X] T017 [US1] Implement manifest generation in `code/stimulus_gen.py` outputting `data/processed/manifest.csv` with `scenario_id`, `salience_level`, `image_path`, `pixel_stats` (including SSIM), **consuming the 'valid' flag from T016** to ensure only verified stimuli are included
- [X] T018 [US1] Create script to run sample validation on a representative set of images and verify output stats match acceptance criteria

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Stimuli ready)

---

## Phase 4: User Story 2 - Survey Deployment and Data Collection (Priority: P2)

**Goal**: Deploy a survey interface to collect blame ratings (Likert scale) for manipulated stimuli with **Latin Square counterbalancing** (Repeated-Measures design).

**Independent Test**: A survey link opens in a browser, a test user views all three salience levels of a scenario in randomized order, submits ratings, and the system records the responses in a local JSON/CSV file linked to the stimulus ID and user ID.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for survey endpoint response schema in `tests/contract/test_survey_api.py`
- [X] T020 [P] [US2] Integration test for full survey flow (view -> rate -> submit -> save) in `tests/integration/test_survey_flow.py`
- [X] T021 [P] [US2] Validation test for linkage integrity (`user_id`, `stimulus_id`, `blame_rating`) in `tests/unit/test_linkage_validation.py`

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement survey server logic in `code/survey_server.py` (Flask app) with endpoints for image serving and response submission
- [X] T023 [US2] Implement **Latin Square counterbalancing logic** in `code/survey_server.py` to assign each user to a specific permutation of the three salience levels (low, medium, high) and present **all three conditions** to each user in the assigned order. Use **Flask sessions** for state management and a **seed-based deterministic assignment** algorithm to ensure consistent user assignments across refreshes.
- [X] T024 [US2] Implement response storage logic in `code/survey_server.py` to append to `data/survey_responses/responses.csv` with `user_id`, `scenario_id`, `salience_level`, `blame_rating`, and timestamp. Ensure **multiple rows per user** (one per condition) are stored to support repeated-measures analysis.
- [X] T025 [US2] Implement attention check logic (e.g., "select the red cone") and automatic exclusion flagging in `code/survey_server.py`
- [X] T026 [US2] Create static HTML/JS frontend template for survey presentation (embedded in Flask or separate `frontend/`)
- [X] T027 [US2] Implement data export function to generate clean CSV for statistical analysis

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Data collection ready)

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Execute **Repeated-Measures ANOVA**, post-hoc tests, power analysis (targeting medium effect size), and generate a comprehensive report.

**Independent Test**: A script runs on a synthetic dataset with known parameters, correctly identifying the effect, reporting F-statistic/p-value, and applying Bonferroni correction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for Repeated-Measures ANOVA calculation on known synthetic data in `tests/unit/test_analysis_stats.py`
- [X] T029 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_analysis_stats.py`
- [X] T030 [P] [US3] Integration test for full analysis pipeline (load -> analyze -> report) in `tests/integration/test_analysis_pipeline.py`

### Implementation for User Story 3

- [X] T031 [P] [US3] Implement `code/analysis.py` to load `data/survey_responses/responses.csv` and filter invalid/attention-failed participants
- [X] T032 [US3] Implement **Repeated-Measures ANOVA** in `code/analysis.py` to test the main effect of salience on blame ratings. **Optional**: Implement GLMM with ordinal link as a robustness check. The primary output must be the Repeated-Measures ANOVA results.
- [X] T033 [US3] Implement post-hoc pairwise comparisons with Bonferroni correction in `code/analysis.py`
- [X] T034 [US3] Implement power analysis (simulation-based) and effect size calculation (ηp²) with 95% confidence intervals in `code/analysis.py`, **explicitly targeting a medium effect size (Cohen's f = 0.25)** to satisfy SC-003.
- [X] T035 [US3] Implement report generation in `code/analysis.py` outputting a summary table (F-stat, df, p-value, adjusted p-values, CI) to `data/analysis_results/report.md`
- [X] T036 [US3] Create visualization scripts for effect plots and interaction plots in `code/analysis.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Edge Cases (Revision - Addresses Real Data & Edge Cases)

**Purpose**: Implement robust handling for invalid manipulations, semantic ambiguity, attention checks, and the 'pre-test panel' fallback.

- [X] T046 [US1] Update `code/stimulus_gen.py` to load only the images listed in `data/raw/curated_scenario_ids.json` and skip any missing files with a warning log
- [X] T047 [US1] Implement logic in `code/stimulus_gen.py` to calculate an "Edge Discontinuity Score" for manipulated regions; if the score exceeds a threshold, mark the stimulus as invalid and exclude it from `manifest.csv`
- [X] T048 [US1] Implement logic in `code/annotation_pipeline.py` to flag scenarios where the "non-causal" element is ambiguous (e.g., blocks a lane) based on pre-defined keyword rules in `config.py`; exclude these from the stimulus pool
- [X] T049 [US1] Implement logic in `code/annotation_pipeline.py` to generate a **human review queue** (JSON artifact) containing stimuli that failed the automated artifact detection metric. This queue serves as the **pre-test panel** option required by FR-007, allowing manual validation if automated metrics are inconclusive.
- [X] T050 [US2] Enhance `code/survey_server.py` to include a mandatory attention check question (e.g., "Select the color of the cone") before the final rating; if failed, mark the response as `attention_failed` in the database
- [X] T051 [US3] Update `code/analysis.py` to automatically filter out any participants with `attention_failed` flags or `invalid_manipulation` stimuli before running the ANOVA

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `docs/` and `README.md`
- [X] T038 Code cleanup and refactoring
- [X] T039 Performance optimization (ensure stimulus gen < 10 mins for 50 scenarios)
- [X] T040 [P] Additional unit tests for edge cases (invalid manipulation, semantic ambiguity) in `tests/unit/`
- [X] T041 Security hardening (ensure no PII storage in survey responses)
- [X] T042 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. Includes Data Acquisition (T043, T044).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 (needs stimuli) but should be independently testable with mock data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US2 (needs responses) but should be independently testable with synthetic data

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
Task: "Unit test for image loading and metadata parsing in tests/unit/test_dataset_loader.py"
Task: "Unit test for pixel-statistics validation (SSIM, brightness delta) in tests/unit/test_stimulus_gen.py"

# Launch all models for User Story 1 together:
Task: "Create base data models (Scenario, Stimulus, Response) in code/data_models.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Data Acquisition)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Stimuli generated and validated)
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
   - Developer B: User Story 2 (Survey)
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
- **Critical Constraint**: All image manipulation and statistical analysis MUST run on CPU-only CI (no GPU, no 8-bit quantization). Use standard PIL/OpenCV and scipy/statsmodels.
- **Design Note**: This project implements a **repeated-measures** design (Latin Square) as per `spec.md` (FR-003, FR-005). The Plan's previous mention of "between-subjects" was corrected to align with the Spec.
- **Data Flow**: T043/T044 (Acquisition) → T013/T014 (Curation) → T015-T017 (Stimuli) → T022-T027 (Survey) → T031-T036 (Analysis).
- **Test-First**: All test tasks (T010-T012, T019-T021, T028-T030) must be written and confirmed to FAIL before the corresponding implementation tasks are started.