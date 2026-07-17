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
- [X] T002 Initialize Python 3.11 project with requirements.txt dependencies (pandas, numpy, scikit-learn, statsmodels, nltk, scipy)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Synthetic Data Generation to ensure downstream tasks have valid inputs.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup data directory structure: `data/raw/`, `data/derived/`, `data/processed/`
- [X] T005 [P] Implement `code/utils/data_loading.py` with functions to fetch eye-tracking data. **Constraint**: MUST fetch ONLY from the specific dataset ID listed in the '# Verified datasets' block of `research.md`. If no HuggingFace ID is listed, use the direct URL from the University of Dundee or Boston University repositories as documented there. **DO NOT** use generic 'nab', 'UCI', or unverified repositories. **Data Hygiene**: Upon download, the script MUST compute the SHA-256 checksum of the file and write it to `state/data_hashes.json` with the filename as the key (e.g., `{"raw_data.parquet": "sha256_hash..."}`) before the file is moved to `data/raw/`. If the checksum does not match a previous record (if any), the script MUST raise an error.
- [X] T006 [P] Implement `code/utils/fixation_detection.py` with I-VT and I-DT algorithms (CPU-optimized). **Config Requirement**: The code MUST attempt to read parameters from `code/config.yaml` first. If the keys `ivt_velocity_threshold` or `idt_dispersion_threshold` are missing, it MUST fall back to the hardcoded defaults of 30 deg/s and 100px respectively. The task description must explicitly state this fallback logic to avoid ambiguity.
- [ ] T007 [P] Create base data models in `code/models/`: `Participant` (id, crt_score, random_intercept), `Stimulus` (id, headline_text, valence, random_intercept), `GazeEvent` (timestamp, duration, roi, participant_id)
- [ ] T008 Configure logging infrastructure to capture data quality warnings and exclusion counts
- [ ] T009 Setup environment configuration and random seed management for reproducibility
- [X] T022 [P] [US2] Implement `code/05_synthetic_data_generator.py` to generate the unified synthetic dataset for simulation. **Mandatory Requirements**:
 1. Generate `belief_rating` (Likert scale, Uniform distribution) and `cognitive_reflection_score` (Normal distribution, mean=5, std=1.5).
 2. Generate ground truth variables for the **three-way interaction** with specific coefficients: `fixation_coef=0.5`, `valence_coef=0.3`, `crt_coef=-0.2`, `interaction_coef=0.1`.
 3. **DO NOT** generate `confidence_assignment_time` or any four-way interaction variables.
 4. Output `data/derived/synthetic_raw_data.csv`.
 5. **Note**: This task is strictly for raw synthetic generation. Outlier capping and merging are handled in T023.
- [ ] T023 [US2] Implement `code/03_data_merge.py` to merge the Gaze stream (`data/derived/preprocessed_gaze.csv` from T018) and the Synthetic stream (`data/derived/synthetic_raw_data.csv` from T022). **Logic**:
 1. Join on `participant_id` and `headline_id`.
 2. **Immediately apply** outlier capping to `cognitive_reflection_score` at the 1st and 99th percentiles within this script.
 3. Output `data/derived/merged_dataset.csv`.
 4. **Dependency**: Must run after T018 (Preprocessed Gaze) and T022 (Synthetic Gen).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eye-tracking data, apply I-VT fixation detection, filter low-quality participants, and map gaze to ROIs.

**Independent Test**: The pipeline can be fully tested by running the preprocessing script on a provided sample dataset and verifying that the output contains only participants with <20% data loss and that fixation events are correctly timestamped and mapped to Regions of Interest (ROIs).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data ingestion output schema in `tests/contract/test_ingestion_schema.py`
- [X] T011 [P] [US1] Integration test for I-VT algorithm on sample noisy data in `tests/integration/test_ivt_preprocessing.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/01_ingest_and_preprocess.py` to load raw CSV/Parquet eye-tracking data
- [X] T013 [P] [US1] Implement I-VT fixation detection logic in `code/utils/fixation_detection.py` (minimum duration threshold set to a configurable value)
- [X] T014 [US1] Implement data quality filter in `code/01_ingest_and_preprocess.py` to retain participants with <20% data loss (exclude those with >20% loss)
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

- [ ] T021 [US2] Implement `code/02_valence_calculation.py` using NRC Emotion Lexicon with automatic fallback to VADER if coverage < 50%. **Input**: `data/derived/merged_dataset.csv` (column `headline_text`) generated by T023. **Output**: `data/derived/valence_scores.csv`. **Depends on**: T023 completion. **Logic**: Calculate NRC coverage defined as the percentage of unique words in the headline that match the NRC lexicon. If coverage < 50%, switch to VADER. **Logging Requirement**: If a switch occurs, the script MUST create `output/runtime.log` if it does not exist, and append a single JSON line: `{"event": "lexicon_switch", "from": "NRC", "to": "VADER", "coverage": <value>}`. This ensures the 'Single Source of Truth' is maintained. (FR-003).
- [ ] T024 [US2] Implement `code/04_regression_analysis.py` using `statsmodels` for mixed-effects regression (random intercepts for Participant and Headline). **Input**: `data/derived/valence_scores.csv` (T021) and `data/derived/preprocessed_gaze.csv` (T018). **Output**: `data/derived/regression_results.csv`. **Model Formula**: `belief_rating ~ fixation_duration * valence * crt + (1|participant_id) + (1|headline_id)`. **Depends on**: T021.
- [ ] T025 [US2] Implement calculation of the three-way interaction term (fixation × valence × cognitive reflection) and verify it matches the ground truth from T022.
- [ ] T026 [US2] Apply multiple-comparison correction (Bonferroni or Holm-Bonferroni) for hypothesis testing.
- [ ] T027 [US2] Generate `data/derived/regression_results.csv` containing coefficients, p-values, CIs, and interaction terms.
- [ ] T028 [US2] Ensure the final report frames findings as causal per FR-006 regarding the simulated mechanism **AND** adheres to Outcome-Neutral Validation. **Instruction**: **Conditional Logic**: After regression, check the p-value of the three-way interaction term.
 1. **If p >= 0.05**: The script MUST write the full regression results to `output/regression_interim.json` (schema: `{"p_value": <float>, "interaction_term": <float>, "coefficients": {...}}`) and then call `code/09_null_result_report.py` passing this JSON file as an argument. The Null Result Report is the **only** output for this case.
 2. **If p < 0.05**: The script MUST generate a 'Causal Framing Statement' directly in the output, stating: "Within the controlled experimental design of this synthetic simulation, the data supports a causal link between [variables]."
 3. **Constraint**: The script must NOT generate a causal statement if p >= 0.05.
- [ ] T037 [US2] [P] Verify that the direction and significance of the main effect (three-way interaction) remain consistent using the capped `cognitive_reflection_score` data generated in T023. **Input**: `data/derived/regression_results.csv` (T027). **Note**: This task explicitly validates the three-way interaction only; no four-way interactions or `confidence_assignment_time` variables are involved. **Dependency**: Requires T023 completion to ensure capped data is used.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform robustness checks including alternative fixation thresholds and sensitivity analysis to ensure findings are not artifacts of parameter choices.

**Independent Test**: The robustness suite can be tested by running the analysis with modified parameters (e.g., 50ms vs 150ms thresholds) and verifying that the direction and significance of the main effect remain consistent across these variations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Contract test for robustness report schema in `tests/contract/test_robustness_schema.py`
- [ ] T030 [P] [US3] Integration test for threshold sweep stability in `tests/integration/test_sensitivity_analysis.py`

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement `code/robustness_analysis.py` to sweep fixation duration cutoffs across a range of values to evaluate sensitivity.
- [ ] T032 [US3] Implement robustness analysis to sweep the **fixation duration cutoff** (50ms, 100ms, 150ms) and measure the resulting variation in the mean belief rating. **Input**: `data/derived/preprocessed_gaze.csv` (T018), `data/derived/merged_dataset.csv` (T023), `data/derived/valence_scores.csv` (T021), and the regression logic from T024. **Action**: Re-run the regression model logic (T024) with each new threshold value. **Reproducibility**: **Before EACH threshold iteration, reset the random seed to the value defined in `code/config.yaml` (default 42)**. **Output**: `data/derived/robustness_report.csv`. **Note**: This task strictly addresses SC-003 (threshold sweep) and does not involve sweeping significance levels (alpha). **Dependency**: Must depend on T024 and T021 to ensure correct logic and data are used.
- [ ] T033 [US3] Implement controls for headline length in the regression model to rule out confounding.
- [ ] T034 [US3] Generate `data/derived/robustness_report.csv` showing variation in mean belief rating across thresholds.
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
 - **Critical**: T022 (Synthetic Data) and T023 (Data Merge) must complete before any US2 or US3 tasks.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires preprocessed data from US1. **Note**: T022 (Synthetic Data) must be completed before T023 (Merge). T023 must be completed before T021 (Valence) and T024 (Model). T021 depends on T023. T024 depends on T021.
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
- Polish tasks can run in parallel with final validation.

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
- **Scope Constraint**: Strictly implement the three-way interaction (FR-004). Do NOT implement four-way interactions or `confidence_assignment_time` variables. **Phase 6 has been removed.**
- **Causal Framing**: Adhere to FR-006 by framing findings as causal within the experimental design, without weakening disclaimers, while prioritizing Null Result Reports for non-significant findings.
- **Task Consolidation**: Task T023 (Data Merge) has been restored to ensure the producer-consumer chain is valid. T022 is now strictly for generation; T023 handles merge and capping.
- **Task Ordering**: T021 explicitly depends on T023. T037 explicitly depends on T023. T032 explicitly depends on T024 and T021.
- **Robustness Correction**: T032 has been corrected to re-run the regression model with new thresholds using raw data, rather than attempting to derive variation from static results.
- **Alpha Sweep Removal**: Tasks T035 and T036 have been removed as the alpha sweep was not authorized by the spec (FR-005).
- **WYSIATI Revision**: Phase 6 (T039-T044) has been **removed** to address the "Daniel Kahneman" research concern regarding the conflation of attention and susceptibility. The scope is strictly limited to the three-way interaction defined in FR-004.