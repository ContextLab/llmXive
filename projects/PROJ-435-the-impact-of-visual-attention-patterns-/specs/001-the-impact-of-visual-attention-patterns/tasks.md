# Tasks: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

**Input**: Design documents from `/specs/001-impact-of-visual-attention-patterns/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001 Create project structure per implementation plan: `code/`, `data/raw/`, `data/derived/`, `data/processed/`, `tests/`, `state/` (Reference: `scripts/init_project.py` template)
- [X] T002 Initialize Python 3.11 project with requirements.txt dependencies (pandas, numpy, scikit-learn, statsmodels, nltk, scipy)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Real Data Ingestion to ensure downstream tasks have valid inputs.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on plan.md):

- [ ] T004 [P] **Construct Validity Gate**: Implement `code/utils/validate_dataset_schema.py` to verify the raw dataset contains required columns (`headline_text`, `belief_rating`, `cognitive_reflection_score`, `fixation_duration`) AND pre-defined ROI bounding boxes (specifically "source_attribution" and "headline_body"). If ROI definitions or required columns are missing, the script MUST halt execution and log a `DataInvalidError` with specific missing items. **Input**: `data/raw/eye_tracking_raw.parquet` (from T005). **Output**: `state/schema_validation.json` with `status: "valid"` or `status: "invalid"`. **Dependency**: Runs after T005 download but before T018 preprocessing.
- [X] T005 [P] **Create Configuration & Fetch Data**: Create `code/config.yaml` with `random_seed: 42` and `dataset_url` (read from `research.md` "Verified datasets" block). Then implement `code/utils/data_loading.py` to fetch eye-tracking data from the configured URL. **Constraint**: MUST fetch data from the URL defined in `code/config.yaml`. **DO NOT** use generic 'nab', 'UCI', or unverified repositories. **Data Hygiene**: Upon download, the script MUST compute the SHA-256 checksum of the file and write it to `state/data_hashes.json` with the filename as the key. **Source Verification**: The script MUST internally verify that the downloaded URL matches the `dataset_url` in `config.yaml` before writing the file. **Output**: `data/raw/eye_tracking_raw.parquet`.
- [X] T006 [P] Implement `code/utils/fixation_detection.py` containing I-VT (or I-DT) fixation detection logic. **Constraint**: MUST support EITHER duration threshold (I-VT) OR dispersion threshold (I-DT) as primary. **Config Requirement**: The code MUST attempt to read parameters from `code/config.yaml` (created in T009b) first. If `ivt_duration_threshold` is missing but `ivt_dispersion_threshold` is present, use I-DT. If neither, use default I-VT 100ms. **Constraint**: Do NOT forbid dispersion thresholds; FR-001 authorizes I-DT. **Note**: I-DT is available as a valid implementation detail.
- [X] T006b [P] Implement config loading and validation in `code/utils/config_loader.py`. **Logic**: Load `code/config.yaml`. Validate that EITHER `ivt_duration_threshold` (I-VT) OR `ivt_dispersion_threshold` (I-DT) is present. If both are present, raise an error (ambiguous). If neither, set `ivt_duration_threshold` to 100ms. **Output**: Validated config object.
- [ ] T007a [P] [Foundational] Implement `Participant` data model in `code/models/participant.py` with attributes: `id`, `crt_score`, `random_intercept`.
- [ ] T007b [P] [Foundational] Implement `Stimulus` data model in `code/models/stimulus.py` with attributes: `id`, `headline_text`, `valence`, `random_intercept`.
- [ ] T007c [P] [Foundational] Implement `GazeEvent` data model in `code/models/gaze_event.py` with attributes: `timestamp`, `duration`, `roi`, `participant_id`.
- [ ] T008a [P] [Foundational] Create logging configuration file `code/config/logging_config.yaml` defining log format, level, and output file paths.
- [ ] T008b [P] [Foundational] Implement logging handler initialization in `code/utils/logging_init.py` to load `logging_config.yaml` and set up the global logger.
- [X] T004b [P] Implement `code/01_extract_empirical_outcome.py` to load the raw dataset (from T005) and extract the `belief_rating` and `headline_text` columns. **Constraint**: This task MUST extract the `belief_rating` column directly from the raw data fetched in T005. **DO NOT** generate synthetic values for `belief_rating`. **Logic**: Verify that `belief_rating` and `headline_text` exist in the dataset. If the exact column name `belief_rating` is missing, **attempt to map common column aliases** using the dictionary: `{'rating': 'belief_rating', 'response': 'belief_rating', 'belief_score': 'belief_rating', 'trust_score': 'belief_rating'}`. If no mapping is found, raise a `DataMissingError`. **Input**: `data/raw/eye_tracking_raw.parquet`. **Output**: `data/derived/empirical_outcomes.csv` containing `participant_id`, `headline_id`, `belief_rating`, and `headline_text`. **Dependency**: Depends on T005 completion.
- [ ] T021 [P] [Foundational] Implement `code/03_valence_calculation.py` using NRC Emotion Lexicon with automatic fallback to VADER if coverage < 50%. **Input**: `data/derived/empirical_outcomes.csv` (column `headline_text`) generated by T004b. **Output**: `data/derived/valence_scores.csv`. **Logic**: Calculate NRC coverage defined as the **percentage of unique words in the headline that match the NRC lexicon**. If the **global dataset average coverage** is < 50%, switch to VADER for **ALL** headlines. **Constraint**: The output schema of `data/derived/valence_scores.csv` MUST remain identical regardless of the lexicon used. **Logging Requirement**: If a switch occurs, the script MUST create `state/runtime_events.json` if it does not exist, and append a single JSON object: `{"event": "lexicon_switch", "from": "NRC", "to": "VADER", "coverage": <value>}`. This ensures the 'Single Source of Truth' is maintained in a verifiable state artifact (FR-003). **Dependency**: Depends on T004b.

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

- [X] T015 [P] [US1] Implement ROI mapping logic in `code/utils/roi_mapping.py` to assign gaze points to "source attribution" and other bounding boxes using point-in-polygon algorithm. **Input**: Raw gaze coordinates and bounding box definitions (polygons) from dataset. **Output**: `roi_type` column in `preprocessed_gaze.csv`. **Dependency**: Runs as part of T018.
- [X] T018 [P] [US1] Implement `code/02_preprocess_gaze.py` to ingest raw data, apply I-VT detection, ROI mapping, and edge case handling. **Input**: `data/raw/eye_tracking_raw.parquet` (from T005). **Output**: `data/derived/preprocessed_gaze.csv` AND `output/exclusion_log.txt`. **Schema**: Must include `participant_id`, `headline_id`, `fixation_duration`, `roi_type`. **Logic**:
 1. Apply I-VT with a minimum duration threshold of 100ms (or I-DT if configured).
 2. Filter participants with `data_loss_percent >= 20` (exclude them).
 3. Map gaze points to ROIs.
 4. **Edge Case**: If "source_attribution" ROI is missing for a trial, exclude that trial and log the exclusion count in `output/exclusion_log.txt`.
 5. **Edge Case**: If a participant has zero fixations on the source ROI, record `fixation_duration = 0` for that participant/headline combination in the output CSV (do not exclude).
 6. Log all exclusions to `output/exclusion_log.txt`.
 **Dependency**: Depends on T005, T006, T006b, T015.
- [ ] T007 [US1] Implement `code/02_data_quality_report.py` to generate a summary of excluded participants. **Input**: `output/exclusion_log.txt` (from T018) and `data/derived/preprocessed_gaze.csv`. **Output**: `output/data_quality_report.csv` containing counts of excluded participants, reasons for exclusion, and total data loss percentage per excluded participant. **Constraint**: This task satisfies SC-001. **Dependency**: Depends on T018 completion.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Mixed-Effects Regression Analysis (Priority: P2)

**Goal**: Execute a mixed-effects regression model testing the interaction between visual attention, headline valence, and cognitive reflection on belief susceptibility.

**Independent Test**: The model can be tested independently by running the regression script on a dataset with known interaction coefficients and verifying that the estimated coefficients match the truth within an acceptable margin of error., while correctly identifying the random intercepts for participants and headlines.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for regression output schema in `tests/contract/test_regression_schema.py`
- [ ] T020 [P] [US2] Integration test for coefficient recovery on synthetic data in `tests/integration/test_mixed_effects_recovery.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/04_data_merge.py` to merge the Gaze stream (`data/derived/preprocessed_gaze.csv` from T018), the Empirical stream (`data/derived/empirical_outcomes.csv` from T004b), and the Valence stream (`data/derived/valence_scores.csv` from T021). **Input Schemas**: `preprocessed_gaze.csv` (participant_id, headline_id, fixation_duration, roi_type), `empirical_outcomes.csv` (participant_id, headline_id, belief_rating, headline_text), `valence_scores.csv` (headline_id, valence_score). **Logic**:
 1. **Schema Validation**: Before merging, verify input files contain required columns. If missing, raise a `DataMissingError` with specific missing column names.
 2. Join on `participant_id` and `headline_id`.
 3. **Immediately apply** outlier capping to `cognitive_reflection_score` at the 1st and 99th percentiles within this script (Reference: Spec Edge Cases section).
 4. Output `data/derived/merged_dataset_full.csv`.
 5. **Dependency**: Must run after T018, T004b, and T021.
- [ ] T024 [US2] Implement `code/05_regression_analysis.py` using `statsmodels` for mixed-effects regression (random intercepts for Participant and Headline). **Input**: `data/derived/merged_dataset_full.csv` (T023). **Logic**:
 1. Calculate `headline_length` (word count) as a control variable.
 2. Fit model: `belief_rating ~ fixation_duration * valence * crt + headline_length + (1|participant_id) + (1|headline_id)`.
 3. Apply Holm-Bonferroni correction to **all p-values** of fixed effects and interaction terms.
 4. Output `data/derived/regression_results.csv` containing coefficients, p-values, **corrected p-values (`p_adj`)**, confidence intervals, and interaction terms.
 **Family**: Gaussian (default). **Variable Type**: `crt` is continuous. **Depends on**: T023. **Note**: The model strictly uses the three-way interaction and controls as defined in FR-004.
- [X] T017 [US2] Implement `code/06_measure_runtime.py` to record wall-clock time of the pipeline execution and compare it against the 300-minute limit. **Input**: Start/End timestamps from pipeline execution. **Output**: `state/runtime_metrics.json` containing `total_runtime_minutes`, `limit_minutes` (300), and `status` ("pass" or "fail"). **Constraint**: This task satisfies SC-005. **Dependency**: Runs after T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform robustness checks including alternative fixation thresholds and sensitivity analysis to ensure findings are not artifacts of parameter choices.

**Independent Test**: The robustness suite can be tested by running the analysis with modified parameters (e.g., 50ms vs 150ms thresholds) and verifying that the direction and significance of the main effect remain consistent across these variations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for robustness report schema in `tests/contract/test_robustness_schema.py`
- [ ] T030 [P] [US3] Integration test for threshold sweep stability in `tests/integration/test_sensitivity_analysis.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement `code/robustness_runner.py` (Parameterized Regression Runner). **Logic**: Refactor the regression logic from `code/05_regression_analysis.py` (T024) into a reusable function/class that accepts `fixation_duration_threshold` as a parameter. **Input**: `code/05_regression_analysis.py`. **Output**: `code/robustness_runner.py` (a module, not a data artifact). **Dependency**: Depends on T024 (code).
- [ ] T034 [US3] Implement controls for headline length in the regression model to rule out confounding (Reference: Plan Complexity Tracking Table). **Logic**: Ensure `code/05_regression_analysis.py` includes `headline_length` as a control variable. **Dependency**: Must be completed before T033.
- [ ] T033 [US3] Implement `code/robustness_sweep.py` to execute the sweep loop. **Input**: `code/robustness_runner.py` (T032), `data/derived/preprocessed_gaze.csv` (T018), `data/derived/merged_dataset_full.csv` (T023), `data/derived/valence_scores.csv` (T021). **Action**: Re-run the regression model logic with each new threshold value (50ms, 100ms, 150ms). **Reproducibility**: **Before EACH threshold iteration, reset the random seed to the value defined in `code/config.yaml`**. **Output**: `data/derived/robustness_report.csv`. **Note**: This task strictly addresses SC-003 (threshold sweep) by reporting the variation in mean belief rating. **Dependency**: Must depend on T032 (code), T018, T023, T021, and T034.
- [ ] T039 [US3] Implement `code/robustness_stability_check.py` to verify the direction and significance of the main effect remain consistent across threshold variations. **Input**: `data/derived/robustness_report.csv` (T033). **Logic**: Compare coefficient signs and CI overlaps across thresholds. **Output**: `output/stability_check.json` containing `consistent_direction`, `consistent_significance`, and `ci_overlap_summary`. **Dependency**: Depends on T033.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] Documentation updates in `docs/` and `paper/`
- [ ] T046 Code cleanup and refactoring
- [ ] T047 Performance optimization across all stories (ensure <300 min runtime)
- [ ] T048 [P] Additional unit tests in `tests/unit/`
- [ ] T049 Run `quickstart.md` validation
- [ ] T050 Verify all artifacts are checksummed in `state/`
- [ ] T028 [P] **Final Report Generation**: Implement `code/07_generate_causal_framing.py` to generate a 'Causal Framing Statement'. **Input**: `data/derived/regression_results.csv` (T024). **Logic**: Generate a statement that frames findings as causal **based on the experimental design** (controlled stimuli) AND **reports the observed interaction effect** (coefficient, p-value) from the data. **Constraint**: The statement MUST NOT be hardcoded; it MUST dynamically include the observed effect size and significance level from the regression results to satisfy Outcome-Neutral Validation (Constitution VII) and FR-006. **Output**: `output/causal_framing_statement.txt`. **Dependency**: Depends on T024.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Critical**: T005, T006, T006b, T004b, T021 must complete before T018 and T023. T018 and T021 must complete before T023. T023 must be completed before T024.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires preprocessed data from US1. **Note**: T004b (Empirical Outcome) and T021 (Valence) must be completed before T023 (Merge). T023 must be completed before T024. T024 depends on T023. **T055 (WYSIATI) has been removed**.
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
 - Developer B: User Story 2 (including T021 Valence)
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
- **Scope Constraint**: Strictly implement the three-way interaction (FR-004). **Phase 5b (WYSIATI Extension) has been REMOVED** as it attempted to implement unapproved scope (confidence_rating, override_time) not defined in the spec's FR-004 or data assumptions, violating Constitution Principle VI. **Correction**: Tasks T055, T056, and T057 have been removed to address the reviewer's concern by ensuring only approved variables are used.
- **Causal Framing**: Adhere to FR-006 by framing findings as causal within the experimental design, dynamically reporting observed effects (T028 in Phase N).
- **Task Consolidation**: Task T023 (Data Merge) is now strictly in Phase 4 (US2). T004b is now in Phase 2 (Foundational) for data extraction. T021 (Valence) is in Phase 2 (Foundational). T023 depends on T018, T004b, T021. T024 depends on T023. T032 depends on T024 (code). T033 depends on T032, T018, T023, T021, T034.
- **Robustness Correction**: T032 and T033 have been split to separate code refactoring from sweep execution. T032 creates a parameterized runner; T033 executes the sweep. T034 (Controls) now precedes T033.
- **Alpha Sweep Removal**: Tasks T035 and T036 have been removed as the alpha sweep was not authorized by the spec (FR-005).
- **T025 Removal**: Task T025 (Ground Truth Verification) has been removed as it is impossible to verify against ground truth for real empirical data, violating Outcome-Neutral Validation.
- **T013b Removal**: Task T013b (Control Variable Check) has been removed as it was redundant to T024 and T033.
- **T006 Consolidation**: Tasks T006a and T006c have been consolidated into a single Task T006 to avoid file conflicts.
- **T012 Removal**: Task T012 has been merged into T018 to resolve ambiguity.
- **T004b Relocation**: Task T004b has been moved to Phase 2 to correctly position data extraction as a foundational prerequisite.
- **T037 Tag Correction**: Task T037 has been retagged [US3] to correctly align with the Robustness user story.
- **WYSIATI Correction**: **Tasks T055, T056, and T057 have been REMOVED** to address the reviewer's concern about the WYSIATI effect. These tasks attempted to extract *empirical* confidence ratings and response latencies from the raw data (if available) as requested, but the spec (FR-004) strictly defines the outcome as `belief_rating`. Attempting to extract unapproved variables violates the spec's fixed-effects definition. The analysis will proceed with `belief_rating` only.
- **T005b Removal**: Task T005b has been removed as it was redundant to T005's internal validation logic.
- **T028 Relocation**: Task T028 (Causal Framing Statement) has been moved to Phase N (Polish) for clarity as a report artifact, and the duplicate entry in Phase 4 has been removed.
- **T026 Removal**: Task T026 (Holm-Bonferroni) has been removed and integrated into T024.
- **T027 Removal**: Task T027 (Generate regression_results.csv) has been removed and merged into T024.
- **T007 Atomization**: Task T007 has been split into T007a, T007b, T007c for independent verification.
- **T008 Split**: Task T008 has been split into T008a and T008b for independent verification.