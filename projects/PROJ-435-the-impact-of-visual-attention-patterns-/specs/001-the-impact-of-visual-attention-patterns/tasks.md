# Tasks: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

**Input**: Design documents from `/specs/001-impact-of-visual-attention-patterns/`
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

- [ ] T001 Create project structure per implementation plan: `code/`, `data/raw/`, `data/derived/`, `data/processed/`, `tests/`, `state/`
- [ ] T002 Initialize Python 3.11 project with requirements.txt dependencies (pandas, numpy, scikit-learn, statsmodels, nltk, scipy)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Synthetic Data Generation to ensure downstream tasks have valid inputs.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup data directory structure: `data/raw/`, `data/derived/`, `data/processed/`
- [ ] T005 [P] Implement `code/utils/data_loading.py` with functions to fetch eye-tracking data from verified sources using `datasets.load_dataset` (e.g., HuggingFace dataset `nab` or specific UCI repository URL with revision tag `v1.0.0`)
- [ ] T006 [P] Implement `code/utils/fixation_detection.py` with I-VT (velocity threshold = 30 deg/s) and I-DT (dispersion = 100px) algorithms (CPU-optimized, no GPU dependencies)
- [ ] T007 [P] Create base data models in `code/models/`: `Participant` (id, crt_score, random_intercept), `Stimulus` (id, headline_text, valence, random_intercept), `GazeEvent` (timestamp, duration, roi, participant_id)
- [ ] T008 Configure logging infrastructure to capture data quality warnings and exclusion counts
- [ ] T009 Setup environment configuration and random seed management for reproducibility
- [ ] T022 [P] [US2] Implement `code/05_synthetic_data_generator.py` to generate the unified dataset for simulation. **Mandatory Requirements**: 
    1. Generate `belief_rating` (Likert scale, Uniform distribution) and `cognitive_reflection_score` (Normal distribution, mean=5, std=1.5).
    2. **Immediately apply** outlier capping to `cognitive_reflection_score` at the 1st and 99th percentiles within this script before saving.
    3. Merge with `headline_text` from the raw dataset (fetched in T005).
    4. Generate ground truth variables for the **three-way interaction** with specific coefficients: `fixation_coef=0.5`, `valence_coef=0.3`, `crt_coef=-0.2`, `interaction_coef=0.1`.
    5. **DO NOT** generate `confidence_assignment_time` or any four-way interaction variables.
    6. Output `data/derived/synthetic_unified_data.csv`.
    7. **Note**: This task consolidates the logic previously split between T022 and T023. Capping is performed atomically within this generation step to ensure data integrity before downstream consumption.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eye-tracking data, apply I-VT fixation detection, filter low-quality participants, and map gaze to ROIs.

**Independent Test**: The pipeline can be fully tested by running the preprocessing script on a provided sample dataset and verifying that the output contains only participants with <20% data loss and that fixation events are correctly timestamped and mapped to Regions of Interest (ROIs).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data ingestion output schema in `tests/contract/test_ingestion_schema.py`
- [ ] T011 [P] [US1] Integration test for I-VT algorithm on sample noisy data in `tests/integration/test_ivt_preprocessing.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/01_ingest_and_preprocess.py` to load raw CSV/Parquet eye-tracking data
- [ ] T013 [P] [US1] Implement I-VT fixation detection logic in `code/utils/fixation_detection.py` (minimum duration threshold set to a configurable value)
- [ ] T014 [US1] Implement data quality filter in `code/01_ingest_and_preprocess.py` to retain participants with <20% data loss (exclude those with >20% loss)
- [ ] T015 [US1] Implement ROI mapping logic to assign gaze points to "source attribution" and other bounding boxes
- [ ] T016 [US1] Handle edge cases: exclude trials with missing ROI coordinates and log exclusion counts
- [ ] T017 [US1] Handle edge cases: treat zero fixations on source ROI as valid data (duration=0) rather than missing
- [ ] T018 [US1] Generate `data/derived/preprocessed_gaze.csv` with filtered participants and mapped fixations

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Mixed-Effects Regression Analysis (Priority: P2)

**Goal**: Execute a mixed-effects regression model testing the interaction between visual attention, headline valence, and cognitive reflection on belief susceptibility.

**Independent Test**: The model can be tested independently by running the regression script on a synthetic dataset with known interaction coefficients and verifying that the estimated coefficients match the synthetic truth within an acceptable margin of error., while correctly identifying the random intercepts for participants and headlines.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for regression output schema in `tests/contract/test_regression_schema.py`
- [ ] T020 [P] [US2] Integration test for coefficient recovery on synthetic data in `tests/integration/test_mixed_effects_recovery.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/02_valence_calculation.py` using NRC Emotion Lexicon with automatic fallback to VADER if coverage < 50%. **Input**: `data/derived/synthetic_unified_data.csv` (column `headline_text`) generated by T022. **Output**: `data/derived/valence_scores.csv`. **Depends on**: T022 completion.
- [ ] T024 [US2] Implement `code/03_mixed_effects_model.py` using `statsmodels` for mixed-effects regression (random intercepts for Participant and Headline). **Input**: `data/derived/valence_scores.csv` (T021) and `data/derived/preprocessed_gaze.csv` (T018). **Output**: `data/derived/regression_results.csv`. **Depends on**: T021.
- [ ] T025 [US2] Implement calculation of the three-way interaction term (fixation × valence × cognitive reflection) and verify it matches the ground truth from T022.
- [ ] T026 [US2] Apply multiple-comparison correction (Bonferroni or Holm-Bonferroni) for hypothesis testing.
- [ ] T027 [US2] Generate `data/derived/regression_results.csv` containing coefficients, p-values, CIs, and interaction terms.
- [ ] T028 [US2] Ensure the final report frames findings as causal per FR-006 regarding the simulated mechanism. The report MUST assert the causal link within the controlled experimental design (synthetic ground truth) without weakening disclaimers that negate the causal framing.
- [ ] T037 [US2] [P] Verify that the direction and significance of the main effect (three-way interaction) remain consistent using the capped `cognitive_reflection_score` data generated in T022. **Input**: `data/derived/regression_results.csv` (T027). **Note**: This task explicitly validates the three-way interaction only; no four-way interactions or `confidence_assignment_time` variables are involved. **Dependency**: Requires T022 completion to ensure capped data is used.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform robustness checks including alternative fixation thresholds and sensitivity analysis to ensure findings are not artifacts of parameter choices.

**Independent Test**: The robustness suite can be tested by running the analysis with modified parameters (e.g., 50ms vs 150ms thresholds) and verifying that the direction and significance of the main effect remain consistent across these variations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Contract test for robustness report schema in `tests/contract/test_robustness_schema.py`
- [ ] T030 [P] [US3] Integration test for threshold sweep stability in `tests/integration/test_sensitivity_analysis.py`

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement `code/_robustness_analysis.py` to sweep fixation duration cutoffs {50ms, 100ms, 150ms}.
- [ ] T032 [US3] Implement robustness analysis to sweep the **fixation duration cutoff** (50ms, 100ms, 150ms) and measure the resulting variation in the mean belief rating. **Input**: `data/derived/regression_results.csv` (T027) or re-run regression with new thresholds. **Output**: `data/derived/robustness_report.csv`. **Note**: This task strictly addresses SC-003 (threshold sweep) and does not involve sweeping significance levels (alpha).
- [ ] T033 [US3] Implement controls for headline length in the regression model to rule out confounding.
- [ ] T034 [US3] Generate `data/derived/robustness_report.csv` showing variation in mean belief rating across thresholds.
- [ ] T035 [US3] Implement sensitivity analysis to sweep significance levels (alpha) over a range of conventional thresholds and measure the resulting false-positive rate variation.
- [ ] T036 [US3] Generate `data/derived/sensitivity_analysis.csv` showing false-positive rate variation across alpha levels.
- [ ] T038 [US3] [P] Verify that the direction and significance of the main effect remain consistent across threshold variations. **Note**: This task focuses on threshold stability.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] Documentation updates in `docs/` and `paper/`
- [ ] T046 Code cleanup and refactoring
- [ ] T047 Performance optimization across all stories (ensure <300 min runtime)
- [ ] T048 [P] Additional unit tests in `tests/unit/`
- [ ] T049 Run `quickstart.md` validation
- [ ] T050 Verify all artifacts are checksummed in `state/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - **Critical**: T022 (Synthetic Data) must complete before any US2 or US3 tasks.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires preprocessed data from US1. **Note**: T022 (Synthetic Data) must be completed before T021 (Valence) and T024 (Model) can execute. T021 depends on T022. T024 depends on T021.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires results from US2
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

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
- **Critical Constraint**: All tasks must be feasible on CPU-only CI with limited core counts and memory resources (no GPU).. No 8-bit quantization or large model loading.
- **Data Integrity**: All synthetic data generation must use pinned random seeds and be documented as "Simulation Mode" to distinguish from real empirical claims.
- **Scope Constraint**: Strictly implement the three-way interaction (FR-004). Do not implement four-way interactions or `confidence_assignment_time` variables unless explicitly authorized by a spec amendment.
- **Causal Framing**: Adhere to FR-006 by framing findings as causal within the experimental design, without weakening disclaimers.
- **Phase 6 Removal**: The "WYSIATI Mechanism" phase (Phase 6) and associated Task T039 from previous drafts have been removed as they introduced unapproved four-way interactions and variables not defined in `spec.md` (FR-004). All WYSIATI-related analysis is now contained within the three-way interaction verification in US2 (T037).
- **Task Consolidation**: Task T023 has been removed. Its functionality (outlier capping) is now integrated directly into T022 to ensure atomic data generation and prevent data leakage.
- **Task Ordering**: T021 explicitly depends on T022 to ensure headline text is available. T037 explicitly depends on T022 to ensure capped data is used.