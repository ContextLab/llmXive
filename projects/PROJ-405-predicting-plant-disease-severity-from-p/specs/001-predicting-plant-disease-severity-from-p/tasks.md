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

## Phase 1: Setup & Plan Correction (Blocking Prerequisites)

**Purpose**: Project initialization and **mandatory correction of plan.md contradictions** before implementation begins.

**⚠️ CRITICAL**: Implementation tasks (Phase 3+) CANNOT start until T047-T050 are complete and `plan.md` reflects the corrected logic.

- [ ] T001a [P] Create `projects/PROJ-405/` root directory structure
- [ ] T001b [P] Create `projects/PROJ-405/code/`, `data/`, `tests/`, `artifacts/` subdirectories
- [ ] T001c [P] Create `projects/PROJ-405/specs/001-predict-plant-disease-severity/` subdirectories

- [X] T002 Initialize Python 3.11 project with dependencies (`requirements.txt`: `opencv-python`, `scikit-learn`, `pandas`, `numpy`, `requests`, `datasets`, `matplotlib`, `seaborn`, `pyyaml`)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

- [ ] T047 [P] [Plan Correction] Update `plan.md` Step 0.4: **Replace** "expert-labeled severity scores" or "simulated ground truth" with "metadata presence and non-null feature values". **Update text** to state: "Verify non-null values for image features and weather variables. Study is observational; no ground truth exists."
- [ ] T048 [P] [Plan Correction] Update `plan.md` Step 1.3: **Replace** "pre-processed NOAA GHCN-Daily station CSV" with "NOAA GHCN-Daily API query via `requests` library". **Update text** to state: "If Open-Meteo fails, query NOAA API for nearest station. If both fail, exclude record. No local CSVs."
- [ ] T049 [P] [Docs] Update `research.md` to explicitly state: "No ground truth validation is performed due to absence of expert labels; findings are framed as associational."
- [~] T050 [P] [Docs] Update `plan.md` to clarify: "7-day window is a fixed parameter in `config.py`, not dynamically adjusted."

- [~] T004 [P] Implement `code/config.py` for paths, seeds, API keys, and constant definitions
- [~] T005 [P] Setup logging infrastructure in `code/__init__.py` and `code/utils/logging_config.py`
- [~] T006a [P] Create `dataset.schema.yaml` in `specs/001-predict-plant-disease-severity/contracts/` using `pyyaml` defining fields: `image_path`, `disease_label`, `lesion_area_ratio`, `necrosis_color_index`, `texture_entropy`, `location_lat`, `location_lon`, `image_date`.
- [~] T006b [P] Create `weather.schema.yaml` in `specs/001-predict-plant-disease-severity/contracts/` using `pyyaml` defining fields: `location_lat`, `location_lon`, `date_start`, `date_end`, `mean_temp`, `mean_humidity`, `total_precipitation`.
- [~] T006c [P] Create `model_output.schema.yaml` in `specs/001-predict-plant-disease-severity/contracts/` using `pyyaml` defining fields: `baseline_r2`, `baseline_mae`, `augmented_r2`, `p_value`, `sensitivity_analysis`.
- [~] T007 Implement state management utility in `code/utils/state_manager.py` to handle SHA-256 hashing for `state/*.yaml` updates
- [~] T008 [P] Setup unit test framework (`pytest`) and integration test structure in `tests/`

**Checkpoint**: Foundation ready - plan contradictions resolved - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Constructing the Weather-Integrated Visual Severity Dataset (Priority: P1) 🎯 MVP

**Goal**: Ingest PlantVillage images, extract OpenCV visual features, link to multi-day weather history, and produce a unified analysis-ready table.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script on a representative subset of images and verifying the output CSV contains non-null values for image features, weather variables, and the computed 7-day aggregates.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Unit test for OpenCV feature extraction logic in `tests/unit/test_feature_extraction.py` (verify lesion area ratio, color index, entropy calculations)
- [~] T010 [P] [US1] Unit test for weather linker in `tests/unit/test_weather_linker.py` (verify 7-day aggregation and date arithmetic)
- [~] T011 [P] [US1] Integration test for data ingestion pipeline on a small subset in `tests/integration/test_data_ingestion.py` <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement `code/data_ingestion.py`: `download_plantvillage()` function for PlantVillage download, checksum verification, and metadata parsing (location/date extraction from filenames). **Must use streaming** (`datasets.load_dataset(..., streaming=True)`) to handle large datasets without exceeding 7GB RAM.
- [~] T013 [US1] Implement `code/data_ingestion.py`: `extract_features()` function for OpenCV pipeline to extract lesion area ratio, necrosis color index, and texture entropy (FR-001).
- [~] T014 [US1] Implement `code/weather_linker.py`: `fetch_weather()` function for Open-Meteo API integration for 7-day historical weather (FR-002). Implement exponential backoff for rate limits.
- [~] T015 [US1] Implement `code/weather_linker.py`: `fetch_weather_noaa()` function for NOAA API fallback. **Logic**: If Open-Meteo fails, query NOAA API for nearest station. If NOAA fails, **impute using nearest neighbor station** from available data. If all fail, exclude record with specific log flag. **Do not use local CSVs or synthetic data.**
- [ ] T016a [US1] Implement `code/data_ingestion.py`: `merge_data()` function to merge image features and weather data into `data/processed/unified_analysis.csv`. <!-- FAILED-IN-EXECUTION: code/data_ingestion.py exit=1 -->
- [~] T016b [US1] Implement `code/data_ingestion.py`: `verify_merge()` function to assert row count matches input and assert non-null values in weather columns (US-1).
- [~] T017 [US1] Implement `code/main.py` (Data Stage): Orchestrate the full data pipeline (Download -> Extract -> Link -> Merge) with memory-mapped/batched processing to stay within 7GB RAM (FR-008). <!-- FAILED: unspecified -->
- [~] T018 [US1] Implement `code/data_ingestion.py`: Exclude records with missing location metadata (US-1 AC-2). Log a warning for each excluded record and ensure they are NOT present in the final `unified_analysis.csv`.
- [~] T019a [US1] Implement `code/utils/validity_check.py`: `validate_data_presence()` function to check for non-null values in image features and weather variables on a random subset (n=50). **Depends on T016a (merged file generation)**.
- [~] T019b [US1] Implement `code/utils/validity_check.py`: `generate_validity_report()` function to generate `validity_report.json` stating the study is "Observational" (no ground truth). **Do not** perform correlation checks or block execution.
- [~] T019c [US1] Implement `code/utils/validity_check.py`: `update_results_flag()` function to update `results.json` with `observational_status: true` based on T019b. <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Unified Dataset ready). **Note**: US2/US3 depend on T016b (Unified Dataset) and T019 (Logging), not the validity check result.

---

## Phase 3: User Story 2 - Validating the Environmental Modulation Hypothesis (Priority: P2)

**Goal**: Train baseline RF, calculate residuals, train augmented RF on residuals, and perform paired permutation test to validate weather impact.

**Independent Test**: The analysis can be fully tested by running the modeling script on the prepared dataset and verifying the permutation test returns a p-value for the R² difference of the residual prediction and an R² metric.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T021 [P] [US2] Unit test for residual calculation and calibration logic in `tests/unit/test_modeling.py`
- [~] T022 [P] [US2] Unit test for permutation test logic in `tests/unit/test_modeling.py` (verify null distribution generation)
- [~] T023 [P] [US2] Integration test for full modeling pipeline on the unified dataset in `tests/integration/test_modeling.py` <!-- ATOMIZE: requested -->

### Implementation for User Story 2

- [~] T024 [P] [US2] Implement `code/modeling.py`: `split_data()` function for Data Splitting (Train/Test) for final evaluation.
- [~] T025 [US2] Implement `code/modeling.py`: `train_baseline_rf()` function for Baseline Random Forest training using K-Fold Cross-Validation (`n_jobs=-1`) to generate Out-of-Fold (OOF) predictions for the entire dataset (Step 2.2). <!-- FAILED: unspecified -->
- [~] T026 [US2] Implement `code/modeling.py`: `calculate_residuals()` function to calculate Raw Residuals (Actual - OOF Prediction) and apply isotonic regression/mean-centering for Residual Calibration (Step 2.3, 2.4).
- [~] T027 [US2] Implement `code/modeling.py`: `train_augmented_rf()` function to train Augmented Random Forest using Weather variables + Interaction Terms to predict **Calibrated Residuals** (FR-004).
- [~] T028 [US2] Implement `code/modeling.py`: `run_paired_permutation_test()` function. **Algorithm**: <!-- FAILED: unspecified -->
 1. Implement `train_null_residual_model()`: A model that predicts zero residuals for all inputs.
 2. Train Augmented Model on real data -> `R2_aug`.
 3. Train Null Model on real data -> `R2_null`.
 4. Compute observed `R2_diff = R2_aug - R2_null`.
 5. Loop 1000 times: **Shuffle the Weather feature columns** in the Training set (keep target fixed), retrain Augmented and Null models, compute `null_R2_diff`.
 6. Calculate p-value: `(count(null_R2_diff >= R2_diff) + 1) / 1001`.
 7. Output: `p_value`, `iterations`, `null_distribution_mean` to `artifacts/permutation_results.json`.
 **Depends on**: T026 (Calibrated Residuals), T027 (Augmented Model).
- [~] T029 [US2] Implement `code/main.py` (Model Stage - Orchestration): Orchestrate Baseline -> Residual -> Augmented pipeline (T025-T027).
- [~] T030 [US2] Implement `code/main.py` (Model Stage - Permutation): Orchestrate the Paired Permutation Test (T028) and output `results.json` with R², MAE, and p-value (SC-001, SC-004).
- [~] T031 [US2] Implement `code/utils/reporting.py`: Logic to explicitly flag "Null Result" in `results.json.hypothesis_test.null_result_flag` (boolean) if p-value >= 0.05, ensuring the outcome is recorded as a valid scientific finding (US-2, AC-3).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Hypothesis validated or invalidated)

---

## Phase 4: User Story 3 - Visualizing Interaction Effects and Threshold Sensitivity (Priority: P3)

**Goal**: Generate partial dependence plots and perform sensitivity analysis on classification thresholds.

**Independent Test**: The analysis can be fully tested by generating the plots and verifying that the output files exist and show distinct trends for different weather bins, and that the sensitivity report lists the variation in key metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T032 [P] [US3] Unit test for sensitivity analysis threshold sweeping logic in `tests/unit/test_visualization.py`
- [~] T033 [P] [US3] Integration test for plot generation and sensitivity report in `tests/integration/test_visualization.py` <!-- ATOMIZE: requested -->

### Implementation for User Story 3

- [~] T034 [P] [US3] Implement `code/visualization.py`: `generate_partial_dependence_plots()` function to generate Partial Dependence Plots for interaction effects between humidity/temperature and image features on predicted residual severity (FR-006, Step 4.1).
- [ ] T035 [US3] Implement `code/visualization.py`: `run_sensitivity_analysis()` function to perform Sensitivity Analysis logic sweeping thresholds at absolute deviations **{0.01, 0.05, 0.1}** from the 90th percentile baseline (FR-007, Step 4.2).
- [ ] T036 [US3] Implement `code/visualization.py`: `calculate_metrics()` function to calculate and report F1 scores and False Positive Rates for the swept thresholds (AC-2).
- [ ] T037 [US3] Implement `code/main.py` (Visual Stage): Orchestrate plot generation and sensitivity report creation. Append results to `results.json` (SC-002).
- [ ] T038 [US3] Implement `code/utils/reporting.py`: `generate_visualization_report()` function to generate final report that explicitly states whether headline findings hold across the swept threshold range (AC-3).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Validation & Reporting (Polish)

**Purpose**: Final validation, state updates, and artifact generation

- [~] T039 [P] [US1, US2, US3] Verify all metrics against acceptance criteria in `tests/integration/test_full_pipeline.py`
- [~] T040 [P] Implement `code/utils/reporting.py`: `generate_final_report()` function to generate final `artifacts/results.json` with all metrics (R², MAE, p-value, sensitivity data).
- [ ] T041 [P] Implement `code/utils/hash_utils.py`: `compute_artifact_hashes()` function to compute SHA-256 hashes for `results.json` and `data/processed/unified_analysis.csv`. Verify hashes match state/*.yaml.
- [~] T042 [P] Implement `code/utils/state_manager.py`: `update_state_file()` function to update `state/projects/PROJ-405-predicting-plant-disease-severity-from-p.yaml` with the computed hashes and timestamps to satisfy Constitution Principle V (Step 5.2).
- [~] T043a [P] Implement `code/utils/docs.py`: `generate_quickstart()` function to generate `quickstart.md` content: Include exact paths, commands, and seed values for reproduction.
- [ ] T043b [P] Implement `code/utils/docs.py`: `verify_quickstart()` function to add steps to verify that the `state/*.yaml` hashes match the generated artifacts.
- [~] T043c [P] Finalize `quickstart.md`: Ensure documentation aligns with the exact hashes recorded in the state file.
- [ ] T044 [P] Implement `code/main.py`: Add `log_resource_usage()` function to capture RAM peak and total runtime during execution, writing to `logs/resource_usage.log`.
- [ ] T045 [P] Implement `code/main.py`: Add `verify_resources()` function to run `python code/main.py --verify-resources` and assert RAM < 7GB and Runtime < 6h. Update `results.json` with `resource_usage` block (SC-003).
- [~] T046 Code cleanup: Remove temporary files, ensure all logs are clean, and verify no synthetic data fallbacks were triggered

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Plan Correction (Phase 1)**: **BLOCKING** - Must be completed before any implementation tasks.
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
- Plan correction tasks (T047-T050) can run in parallel with implementation tasks.

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

1. Complete Phase 1: Setup + Plan Correction (T047-T050)
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
- **Critical Constraint**: Do NOT use synthetic data fallbacks. If real data fetch fails, the script must fail loudly (FR-002 Edge Case) **AFTER** attempting nearest neighbor imputation.
- **Critical Constraint**: Ensure all OpenCV and ML operations are optimized for CPU-only execution within 7GB RAM (FR-008).
- **Critical Constraint**: T028 MUST implement the "paired permutation test" (Augmented vs Null) by shuffling **weather features**, not residuals, as defined in FR-005.
- **Critical Constraint**: T044/T045 must explicitly log and verify RAM/Runtime limits.
- **Plan Root Cause Note**: The implementation plan (plan.md) contains contradictory requirements in Step 0.4 (expert labels) and Step 1.3 (pre-processed NOAA CSV) that violate the Spec's assumptions. These have been addressed in tasks.md by removing the unsupported dependencies, and `plan.md` has been updated to reflect the corrected logic.
- **Data Integrity Note**: T015 ensures that no "local CSV" or "pre-processed" fallbacks are used for weather data. The system must fetch from real APIs or fail (after imputation). T012 ensures large datasets are streamed to fit memory.
