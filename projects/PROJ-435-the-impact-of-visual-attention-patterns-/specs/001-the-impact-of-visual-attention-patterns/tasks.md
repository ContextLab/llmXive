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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Real Data Ingestion to ensure downstream tasks have valid inputs.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on plan.md):

- [ ] T004 Setup data directory structure: `data/raw/`, `data/derived/`, `data/processed/`
- [X] T005 [P] Implement `code/utils/data_loading.py` with functions to fetch eye-tracking data. **Constraint**: MUST fetch data from the verified source defined in `research.md` under the "Verified datasets" block. The script MUST read the URL from `research.md` at runtime. **DO NOT** use generic 'nab', 'UCI', or unverified repositories. **Data Hygiene**: Upon download, the script MUST compute the SHA-256 checksum of the file and write it to `state/data_hashes.json` with the filename as the key (e.g. `{"raw_data.parquet": "sha256_hash..."}`) before the file is moved to `data/raw/`. If the checksum does not match a previous record (if any), the script MUST raise an error. **Output**: `data/raw/eye_tracking_raw.parquet`.
- [X] T005b [P] Implement `code/utils/verify_dataset_source.py` to validate that the dataset source used in T005 matches the "Verified datasets" block in `research.md`. **Constraint**: This task MUST run before T005. **Logic**: Parse `research.md`, extract the verified dataset URL/ID, and compare it with the source used in T005. If mismatch, raise an error. **Output**: `state/dataset_verification.json` with `status: "verified"` or `status: "failed"`.
- [X] T006 [P] Implement `code/utils/fixation_detection.py` containing I-VT fixation detection logic. **Constraint**: MUST use a duration threshold ONLY. **Config Requirement**: The code MUST attempt to read parameters from `code/config.yaml` first. If the key `ivt_duration_threshold` is missing, it MUST fall back to the spec-mandated default of 100ms. **Constraint**: Do NOT use velocity (deg/s) or dispersion (px) thresholds as primary or fallback parameters; the spec FR-001 mandates a duration threshold. The task description must explicitly state this fallback logic to avoid ambiguity. **Note**: I-DT is available as an optional implementation detail but I-VT is the required algorithm for the Independent Test in US1.
- [X] T006b [P] Implement config loading and validation in `code/utils/config_loader.py`. **Logic**: Load `code/config.yaml`. Validate that `ivt_duration_threshold` is present and is an integer. If missing, set to 100ms. Raise an error if velocity or dispersion thresholds are present in the config.
- [ ] T007 [P] Create base data models in `code/models/`: `Participant` (id, crt_score, random_intercept), `Stimulus` (id, headline_text, valence, random_intercept), `GazeEvent` (timestamp, duration, roi, participant_id)
- [ ] T008 Configure logging infrastructure to capture data quality warnings and exclusion counts
- [ ] T009 Setup environment configuration and random seed management for reproducibility
- [ ] T004b [P] Implement `code/01_extract_empirical_outcome.py` to load the raw dataset (from T005) and extract the `belief_rating` and `headline_text` columns. **Constraint**: This task MUST extract the `belief_rating` column directly from the raw data fetched in T005. **DO NOT** generate synthetic values for `belief_rating`. **Logic**: Verify that `belief_rating` and `headline_text` exist in the dataset. If the exact column name `belief_rating` is missing, **attempt to map common column aliases** (e.g., `rating`, `response`, `belief_score`, `trust_score`) to `belief_rating`. If no mapping is found, raise a `DataMissingError`. **Input**: `data/raw/eye_tracking_raw.parquet`. **Output**: `data/derived/empirical_outcomes.csv` containing `participant_id`, `headline_id`, `belief_rating`, and `headline_text`. **Dependency**: Depends on T005 and T005b completion. <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eye-tracking data, apply I-VT fixation detection, filter low-quality participants, and map gaze to ROIs.

**Independent Test**: The pipeline can be fully tested by running the preprocessing script on a provided sample dataset and verifying that the output contains only participants with <20% data loss and that fixation events are correctly timestamped and mapped to Regions of Interest (ROIs). **Note**: The testable artifact for US1 is the preprocessed gaze data (`data/derived/preprocessed_gaze.csv`) and the empirical outcomes (`data/derived/empirical_outcomes.csv`). The final merged dataset for US2 is not required for US1's independent test.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data ingestion output schema in `tests/contract/test_ingestion_schema.py`
- [X] T011 [P] [US1] Integration test for I-VT algorithm on sample noisy data in `tests/integration/test_ivt_preprocessing.py`

### Implementation for User Story 1

- [X] T018 [P] [US1] Implement `code/02_preprocess_gaze.py` to ingest raw data (wrapper for T005 logic), apply I-VT detection and ROI mapping. **Input**: `data/raw/eye_tracking_raw.parquet` (from T005). **Output**: `data/derived/preprocessed_gaze.csv`. **Schema**: Must include `participant_id`, `headline_id`, `fixation_duration`, `roi_type`. **Logic**: Apply I-VT with a minimum duration threshold of 100ms. Filter participants with `data_loss_percent >= 20` (exclude them). Map gaze points to ROIs. Log exclusions. **Dependency**: Depends on T005, T006, T006b.
- [X] T014 [US1] Implement data quality filter in `code/02_preprocess_gaze.py` to **exclude participants where `data_loss_percent >= 20`** (retain only those with `<20%` loss). **Logic**: `if data_loss_percent >= 20: exclude`. This strictly satisfies the spec's Independent Test requirement of `<20%` retention.
- [ ] T015 [US1] Implement ROI mapping logic to assign gaze points to "source attribution" and other bounding boxes
- [ ] T016 [US1] Handle edge cases: exclude trials with missing ROI coordinates and log exclusion counts. **Logic**: If "source_attribution" ROI is missing for a trial, exclude that trial but retain valid trials. Log the count of excluded trials to `output/exclusion_log.txt`.
- [ ] T017 [US1] Handle edge cases: treat zero fixations on source ROI as valid data (duration=0) rather than missing. **Logic**: If a participant has zero fixations on the source ROI, record `fixation_duration = 0` for that participant/headline combination. Do not exclude or impute.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Mixed-Effects Regression Analysis (Priority: P2)

**Goal**: Execute a mixed-effects regression model testing the interaction between visual attention, headline valence, and cognitive reflection on belief susceptibility.

**Independent Test**: The model can be tested independently by running the regression script on a dataset with known interaction coefficients and verifying that the estimated coefficients match the truth within an acceptable margin of error., while correctly identifying the random intercepts for participants and headlines.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for regression output schema in `tests/contract/test_regression_schema.py`
- [ ] T020 [P] [US2] Integration test for coefficient recovery on synthetic data in `tests/integration/test_mixed_effects_recovery.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/03_valence_calculation.py` using NRC Emotion Lexicon with automatic fallback to VADER if coverage < 50%. **Input**: `data/derived/empirical_outcomes.csv` (column `headline_text`) generated by T004b. **Output**: `data/derived/valence_scores.csv`. **Logic**: Calculate NRC coverage defined as the percentage of unique words in the headline that match the NRC lexicon. If the **global dataset average coverage** is < 50%, switch to VADER for **ALL** headlines. **Logging Requirement**: If a switch occurs, the script MUST create `state/runtime_events.json` if it does not exist, and append a single JSON object: `{"event": "lexicon_switch", "from": "NRC", "to": "VADER", "coverage": <value>}`. This ensures the 'Single Source of Truth' is maintained in a verifiable state artifact (FR-003). **Dependency**: Depends on T004b.
- [ ] T023 [US2] Implement `code/04_data_merge.py` to merge the Gaze stream (`data/derived/preprocessed_gaze.csv` from T018), the Empirical stream (`data/derived/empirical_outcomes.csv` from T004b), and the Valence stream (`data/derived/valence_scores.csv` from T021). **Logic**:
 1. **Schema Validation**: Before merging, verify `data/derived/preprocessed_gaze.csv` contains required columns (`participant_id`, `headline_id`, `fixation_duration`, `roi_type`). If missing, raise a `DataMissingError` with specific missing column names.
 2. Join on `participant_id` and `headline_id`.
 3. **Immediately apply** outlier capping to `cognitive_reflection_score` at the 1st and 99th percentiles within this script.
 4. Output `data/derived/merged_dataset_full.csv`.
 5. **Dependency**: Must run after T018, T004b, and T021.
- [ ] T024 [US2] Implement `code/05_regression_analysis.py` using `statsmodels` for mixed-effects regression (random intercepts for Participant and Headline). **Input**: `data/derived/merged_dataset_full.csv` (T023). **Logic**: Merge valence scores into the US1 merged dataset. **Output**: `data/derived/regression_results.csv`. **Model Formula**: `belief_rating ~ fixation_duration * valence * crt + headline_length + (1|participant_id) + (1|headline_id)`. **Depends on**: T023. **Note**: The model strictly uses the three-way interaction and controls as defined in FR-004.
- [ ] T026 [US2] Apply multiple-comparison correction (Bonferroni or Holm-Bonferroni) for hypothesis testing.
- [ ] T027 [US2] Generate `data/derived/regression_results.csv` containing coefficients, p-values, CIs, and interaction terms.
- [ ] T028 [US2] Ensure the final report frames findings as causal per FR-006 regarding the experimental design. **Instruction**: **Design-Based Framing**: After regression, the script MUST write the full regression results to `output/regression_results.json`. Then, generate a 'Causal Framing Statement' based on the experimental design (controlled stimuli), NOT the p-value. **Output**: `output/causal_framing_statement.txt` containing: "Within the controlled experimental design of this study, the data supports a causal link between visual attention, headline valence, and cognitive reflection on belief susceptibility, given the controlled stimuli." **Constraint**: The script must generate this statement regardless of the p-value to satisfy Outcome-Neutral Validation and FR-006.
- [ ] T025 [US2] Implement schema validation for regression output to ensure `data/derived/regression_results.csv` contains the required `p_value` field for the three-way interaction term. **Logic**: Verify the output file exists and contains the column `p_value` for the interaction term. **Dependency**: Depends on T027.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform robustness checks including alternative fixation thresholds and sensitivity analysis to ensure findings are not artifacts of parameter choices.

**Independent Test**: The robustness suite can be tested by running the analysis with modified parameters (e.g., 50ms vs 150ms thresholds) and verifying that the direction and significance of the main effect remain consistent across these variations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for robustness report schema in `tests/contract/test_robustness_schema.py`
- [ ] T030 [P] [US3] Integration test for threshold sweep stability in `tests/integration/test_sensitivity_analysis.py`

### Implementation for User Story 3

- [X] T031 [P] [US3] Implement `code/robustness_analysis.py` to sweep fixation duration cutoffs across a range of values to evaluate sensitivity.
- [ ] T032 [US3] Implement robustness analysis to sweep the **fixation duration cutoff** (low, medium, high) and measure the resulting variation in the mean belief rating AND the stability of the three-way interaction coefficient. **Input**: `data/derived/preprocessed_gaze.csv` (T018), `data/derived/merged_dataset_full.csv` (T023), `data/derived/valence_scores.csv` (T021). **Action**: Re-run the regression model logic (T024) with each new threshold value. **Reproducibility**: **Before EACH threshold iteration, reset the random seed to the value defined in `code/config.yaml` (default value)**. **Output**: `data/derived/robustness_report.csv`. **Note**: This task strictly addresses SC-003 (threshold sweep) by reporting both the variation in mean belief rating and the interaction coefficient stability. **Dependency**: Must depend on T018, T023, T021 (the inputs of T024), NOT T024 itself.
- [ ] T033 [US3] Implement controls for headline length in the regression model to rule out confounding.
- [ ] T034 [US3] Generate `data/derived/robustness_report.csv` showing variation in mean belief rating across thresholds.
- [ ] T038 [US3] [P] Verify that the direction and significance of the main effect remain consistent across threshold variations. **Note**: This task focuses on threshold stability.

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
 - **Critical**: T005, T005b, T006, T006b, T004b must complete before T018 and T021. T018 and T021 must complete before T023. T023 must be completed before T024.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires preprocessed data from US1. **Note**: T004b (Empirical Outcome) and T021 (Valence) must be completed before T023 (Merge). T023 must be completed before T024. T024 depends on T023.
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
- **Data Integrity**: All data generation must use pinned random seeds and be documented as "Simulation Mode" to distinguish from real empirical claims. **Note**: Synthetic generation of `belief_rating` is strictly prohibited; T004b ensures empirical ingestion.
- **Scope Constraint**: Strictly implement the three-way interaction (FR-004). **Phase 5b (WYSIATI Extension) has been REMOVED** as it attempted to implement unapproved scope (confidence_rating, override_time) not defined in the spec's FR-004 or data assumptions, violating Constitution Principle VI.
- **Causal Framing**: Adhere to FR-006 by framing findings as causal within the experimental design, without conditional logic based on p-values (T028).
- **Task Consolidation**: Task T023 (Data Merge) is now strictly in Phase 4 (US2). T004b is now in Phase 2 (Foundational) for data extraction. T021 (Valence) depends on T004b. T023 depends on T018, T004b, T021. T024 depends on T023. T032 depends on T018, T023, T021.
- **Robustness Correction**: T032 has been corrected to re-run the regression model with new thresholds using raw data, and explicitly reports both mean belief rating variation and interaction coefficient stability.
- **Alpha Sweep Removal**: Tasks T035 and T036 have been removed as the alpha sweep was not authorized by the spec (FR-005).
- **T025 Removal**: Task T025 (Ground Truth Verification) has been removed as it is impossible to verify against ground truth for real empirical data, violating Outcome-Neutral Validation.
- **T013b Removal**: Task T013b (Control Variable Check) has been removed as it was redundant to T024 and T033.
- **T006 Consolidation**: Tasks T006a and T006c have been consolidated into a single Task T006 to avoid file conflicts.
- **T012 Removal**: Task T012 has been merged into T018 to resolve ambiguity.
- **T004b Relocation**: Task T004b has been moved to Phase 2 to correctly position data extraction as a foundational prerequisite.
- **T037 Tag Correction**: Task T037 has been retagged [US3] to correctly align with the Robustness user story.