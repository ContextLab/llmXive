# Tasks: Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records

**Input**: Design documents from `/specs/001-predict-plant-disease-severity/`
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

- [ ] T001a [P] Create `projects/PROJ-405/` root directory structure
- [ ] T001b [P] Create `projects/PROJ-405/code/`, `data/`, `tests/`, `artifacts/` subdirectories
- [ ] T001c [P] Create `projects/PROJ-405/specs/001-predict-plant-disease-severity/` subdirectories

- [X] T002 Initialize Python 3.11 project with dependencies (`requirements.txt`: `opencv-python`, `scikit-learn`, `pandas`, `numpy`, `requests`, `datasets`, `matplotlib`, `seaborn`, `pyyaml`)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` for paths, seeds, API keys, and constant definitions
- [X] T005 [P] Setup logging infrastructure in `code/__init__.py` and `code/utils/logging_config.py`
- [ ] T006a [P] Create `dataset.schema.yaml` in `specs/001-predict-plant-disease-severity/contracts/` defining fields: `image_path`, `disease_label`, `lesion_area_ratio`, `necrosis_color_index`, `texture_entropy`, `location_lat`, `location_lon`, `image_date`.
- [ ] T006b [P] Create `weather.schema.yaml` in `specs/001-predict-plant-disease-severity/contracts/` defining fields: `location_lat`, `location_lon`, `date_start`, `date_end`, `mean_temp`, `mean_humidity`, `total_precipitation`.
- [ ] T006c [P] Create `model_output.schema.yaml` in `specs/001-predict-plant-disease-severity/contracts/` defining fields: `baseline_r2`, `baseline_mae`, `augmented_r2`, `p_value`, `sensitivity_analysis`.
- [X] T007 Implement state management utility in `code/utils/state_manager.py` to handle SHA-256 hashing for `state/*.yaml` updates
- [ ] T008 [P] Setup unit test framework (`pytest`) and integration test structure in `tests/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Constructing the Weather-Integrated Visual Severity Dataset (Priority: P1) 🎯 MVP

**Goal**: Ingest PlantVillage images, extract OpenCV visual features, link to 7-day weather history, and produce a unified analysis-ready table.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script on a representative subset of images and verifying the output CSV contains non-null values for image features, weather variables, and the computed 7-day aggregates.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for OpenCV feature extraction logic in `tests/unit/test_feature_extraction.py` (verify lesion area ratio, color index, entropy calculations)
- [X] T010 [P] [US1] Unit test for weather linker in `tests/unit/test_weather_linker.py` (verify 7-day aggregation and date arithmetic)
- [X] T011 [P] [US1] Integration test for data ingestion pipeline on a small subset in `tests/integration/test_data_ingestion.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data_ingestion.py`: PlantVillage download, checksum verification, and metadata parsing (location/date extraction from filenames)
- [X] T013 [US1] Implement `code/data_ingestion.py`: OpenCV pipeline to extract lesion area ratio, necrosis color index, and texture entropy (FR-001).
- [X] T014 [US1] Implement `code/weather_linker.py`: Open-Meteo API integration for 7-day historical weather (FR-002). Implement exponential backoff for rate limits.
- [X] T015 [US1] Implement `code/weather_linker.py`: NOAA API fallback mechanism if Open-Meteo fails (FR-002). If both APIs fail, exclude the record with a specific log flag. **Do not use local CSVs or synthetic data.**
- [ ] T016 [US1] Implement `code/data_ingestion.py`: Merge image features and weather data into `data/processed/unified_analysis.csv` (US-1).
- [X] T017 [US1] Implement `code/main.py` (Data Stage): Orchestrate the full data pipeline (Download -> Extract -> Link -> Merge) with memory-mapped/batched processing to stay within 7GB RAM (FR-008).
- [X] T018 [US1] Implement `code/data_ingestion.py`: Exclude records with missing location metadata (US-1 AC-2). Log a warning for each excluded record and ensure they are NOT present in the final `unified_analysis.csv`.
- [X] T019 [US1] Implement `code/utils/validity_check.py`: Construct validity check on a random subset (n=50). **Since the study is observational with no ground truth (Spec Assumptions), skip the correlation check against expert scores.** Instead, log "Associational Only" if no ground truth is available. Do NOT generate synthetic proxies. Flag the study as "Associational Only" in `results.json` if the check is skipped or correlation < 0.5 (if ground truth were hypothetically available).
- [ ] T020 [US1] **REMOVED**: Hard gating task removed. Pipeline continues execution regardless of validity check result, flagging "Associational Only" as per US-2 AC-3.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Unified Dataset ready). **Note**: US2/US3 depend on T016 (Unified Dataset) and T019 (Logging), not the validity check result.

---

## Phase 4: User Story 2 - Validating the Environmental Modulation Hypothesis (Priority: P2)

**Goal**: Train baseline RF, calculate residuals, train augmented RF on residuals, and perform paired permutation test to validate weather impact.

**Independent Test**: The analysis can be fully tested by running the modeling script on the prepared dataset and verifying that the permutation test returns a p-value for the R² difference of the residual prediction and an R² metric.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for residual calculation and calibration logic in `tests/unit/test_modeling.py`
- [X] T022 [P] [US2] Unit test for permutation test logic in `tests/unit/test_modeling.py` (verify null distribution generation)
- [X] T023 [P] [US2] Integration test for full modeling pipeline on the unified dataset in `tests/integration/test_modeling.py`

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement `code/modeling.py`: Data Splitting (Train/Test) for final evaluation.
- [X] T025 [US2] Implement `code/modeling.py`: Baseline Random Forest training using K-Fold Cross-Validation (`n_jobs=-1`) to generate Out-of-Fold (OOF) predictions for the entire dataset (Step 2.2).
- [X] T026 [US2] Implement `code/modeling.py`: Calculate Raw Residuals (Actual - OOF Prediction) and apply isotonic regression/mean-centering for Residual Calibration (Step 2.3, 2.4).
- [X] T027 [US2] Implement `code/modeling.py`: Train Augmented Random Forest using Weather variables + Interaction Terms to predict **Calibrated Residuals** (FR-004).
- [X] T028 [US2] Implement `code/modeling.py`: Paired Permutation Test with a sufficient number of iterations to compare Augmented R² vs Null R² [FR-005] [SC-001].
 - **Algorithm**:
 1. Train Augmented Model on real data -> `R2_aug`.
 2. Train Null Model (predicting zero residuals) on real data -> `R2_null`.
 3. Compute observed `R2_diff = R2_aug - R2_null`.
 4. Loop 1000 times: **Shuffle the Weather feature columns** in the Training set (keep target fixed), retrain Augmented and Null models, compute `null_R2_diff`.
 5. Calculate p-value: `(count(null_R2_diff >= R2_diff) + 1) / 1001`.
 - **Output**: `p_value`, `iterations`, `null_distribution_mean` (FR-005, Step 3.2).
- [X] T029 [US2] Implement `code/main.py` (Model Stage - Orchestration): Orchestrate Baseline -> Residual -> Augmented pipeline (T025-T027).
- [X] T030 [US2] Implement `code/main.py` (Model Stage - Permutation): Orchestrate the Paired Permutation Test (T028) and output `results.json` with R², MAE, and p-value (SC-001, SC-004).
- [X] T031 [US2] Implement `code/utils/reporting.py`: Logic to explicitly flag "Null Result" in `results.json.hypothesis_test.null_result_flag` (boolean) if p-value >= 0.05, ensuring the outcome is recorded as a valid scientific finding (US-2, AC-3).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Hypothesis validated or invalidated)

---

## Phase 5: User Story 3 - Visualizing Interaction Effects and Threshold Sensitivity (Priority: P3)

**Goal**: Generate partial dependence plots and perform sensitivity analysis on classification thresholds.

**Independent Test**: The analysis can be fully tested by generating the plots and verifying that the output files exist and show distinct trends for different weather bins, and that the sensitivity report lists the variation in key metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [P] [US3] Unit test for sensitivity analysis threshold sweeping logic in `tests/unit/test_visualization.py`
- [X] T033 [P] [US3] Integration test for plot generation and sensitivity report in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [X] T034 [P] [US3] Implement `code/visualization.py`: Generate Partial Dependence Plots for interaction effects between humidity/temperature and image features on predicted residual severity (FR-006, Step 4.1).
- [X] T035 [US3] Implement `code/visualization.py`: Sensitivity Analysis logic sweeping thresholds at absolute deviations {, 0.05, 0.1} from the 90th percentile baseline (FR-007, Step 4.2).
- [X] T036 [US3] Implement `code/visualization.py`: Calculate and report F1 scores and False Positive Rates for the swept thresholds (AC-2).
- [X] T037 [US3] Implement `code/main.py` (Visual Stage): Orchestrate plot generation and sensitivity report creation. Append results to `results.json` (SC-002).
- [X] T038 [US3] Implement `code/utils/reporting.py`: Final report generation logic that explicitly states whether headline findings hold across the swept threshold range (AC-3).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Reporting (Polish)

**Purpose**: Final validation, state updates, and artifact generation

- [X] T039 [P] [US1, US2, US3] Verify all metrics against acceptance criteria in `tests/integration/test_full_pipeline.py`
- [ ] T040 [P] Generate final `artifacts/results.json` with all metrics (R², MAE, p-value, sensitivity data)
- [ ] T041 Compute SHA-256 hashes for `results.json` and `data/processed/unified_analysis.csv`
- [ ] T042 Update `state/*.yaml` with the computed hashes and timestamps to satisfy Constitution Principle V (Step 5.2)
- [ ] T043a [P] Generate `quickstart.md` content: Include exact paths, commands, and seed values for reproduction.
- [ ] T043b [P] Generate `quickstart.md` verification: Add steps to verify that the `state/*.yaml` hashes match the generated artifacts.
- [ ] T043c [P] Finalize `quickstart.md`: Ensure documentation aligns with the exact hashes recorded in the state file.
- [ ] T044 [P] Instrument resource usage: Add logging to `code/main.py` to capture RAM peak and total runtime during execution.
- [ ] T045 [P] Verify resource limits: Run `quickstart.md` (T043) and verify logged RAM < 7GB and Runtime < 6h. Update `results.json` with `resource_usage` block (SC-003).
- [ ] T046 Code cleanup: Remove temporary files, ensure all logs are clean, and verify no synthetic data fallbacks were triggered

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (Unified Dataset) AND T019 (Logging)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (Model Results)

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
Task: "Unit test for OpenCV feature extraction logic in tests/unit/test_feature_extraction.py"
Task: "Unit test for weather linker in tests/unit/test_weather_linker.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py: PlantVillage download and metadata parsing"
Task: "Implement code/weather_linker.py: Open-Meteo API integration"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including T019 logging)
4. **STOP and VALIDATE**: Test User Story 1 independently (Unified Dataset ready, Validity Check logged)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Hypothesis Test)
4. Add User Story 3 → Test independently → Deploy/Demo (Visualization)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Modeling) - *Note: Can start once US1 data schema is defined*
 - Developer C: User Story 3 (Visualization) - *Note: Can start once US2 model schema is defined*
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
- **Critical Constraint**: Do NOT use synthetic data fallbacks. If real data fetch fails, the script must fail loudly (FR-002 Edge Case).
- **Critical Constraint**: Ensure all OpenCV and ML operations are optimized for CPU-only execution within 7GB RAM (FR-008).
- **Critical Constraint**: T028 MUST implement the "paired permutation test" (Augmented vs Null) by shuffling **weather features**, not residuals, as defined in FR-005.
- **Critical Constraint**: T044/T045 must explicitly log and verify RAM/Runtime limits.
- **Plan Root Cause Note**: The implementation plan (plan.md) contains contradictory requirements in Step 0.4 (expert labels) and Step 1.3 (pre-processed NOAA CSV) that violate the Spec's assumptions. These have been addressed in tasks.md by removing the unsupported dependencies, but the plan.md itself requires a "kickback" to be corrected.