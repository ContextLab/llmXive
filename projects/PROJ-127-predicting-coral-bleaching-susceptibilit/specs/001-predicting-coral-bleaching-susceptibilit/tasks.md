# Tasks: Predicting Coral Bleaching Susceptibility from Environmental Data

**Input**: Design documents from `/specs/001-predict-coral-bleaching/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/` at repository root
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

- [ ] T001 [P] Create project directory structure: `code/`, `data/raw`, `data/processed`, `data/models`, `tests/unit`, `tests/integration`, `results/`, and `state/`. Create `__init__.py` files in all Python directories. Create `.gitignore` and `requirements.txt` with pinned dependencies (xgboost, scikit-learn, pandas, geopandas, rasterio, numpy, requests, pyyaml, pytest). (Requires: None)
- [X] T002A [P] Create `ruff.toml` configuration file in the repository root with linting rules for the project (e.g., line length, ignored files). (Requires: T001)
- [X] T002B [P] Create `pyproject.toml` configuration file in the repository root with project metadata and build system configuration. (Requires: T001)

---

## Phase 2: Foundational (Blocking Prerequisites & Data Ingestion)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented, including immediate data ingestion if verified.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Implement `code/config.py` with paths, random seeds, thresholds, `DATA_GAP_HALT` flag, `IMPUTATION_THRESHOLD_DAYS` (default a predetermined threshold), `MAX_RAM_GB` (default 6), and verified URLs (NOAA_URL, UNEP_URL, CORAL_TRAIT_URL, REEFBASE_URL). **Requirement**: Must validate that all URLs are reachable; if any URL is unreachable, the script must raise an error. **Action**: Populate config.py with actual, working URLs. (Requires: T001)
- [X] T004 [P] Create `code/data_gap_report.py` to generate `data_gap_report.md` if verified sources are missing. **Success Criteria**: Script must check if any required dataset URL is missing or invalid in `config.py` and, if so, generate `data_gap_report.md` listing the missing sources and a "HALT" flag. (Requires: T003)
- [ ] T005 [P] Execute Data Gap Verification: Run `code/data_gap_report.py`. **Success Criteria**: Generate `data_gap_status.json` with `status: PASS` if all data is present; generate `data_gap_report.md` and set `status: FAIL` if missing. **Blocking Gate**: If status is FAIL, the pipeline MUST halt and NO subsequent ingestion tasks may run. **Schema**: `data_gap_status.json` must contain keys `status` (string) and `missing_sources` (list). (Requires: T004)
- [~] T006 [US1] Implement `code/ingest.py`: Download NOAA SST/DHW rasters, UNEP reef geometries, Coral Trait Database traits, and ReefBase bleaching events from URLs specified in `config.NOAA_URL`, `config.CORAL_TRAIT_URL`, etc. **Requirement**: Must compute and record checksums for all downloaded files. **Requires**: T005 (Data Gap Check must pass). (Requires: T003, T005)

### Phase 2.1: Data Ingestion & Merging (Atomic Tasks)

- [ ] T009A [US1] **Streaming & Chunking**: Implement `code/ingest.py` to stream the full dataset using `datasets.load_dataset(..., streaming=True)` or equivalent chunked reading. **Output**: Create `data/processed/streamed_chunks/` containing the raw data chunks. **Requirement**: Process in chunks to preserve data integrity and avoid memory overflow. (Requires: T006) <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 -->
- [ ] T009B [US1] **Imputation**: Implement `code/ingest.py` to impute missing values using the nearest valid temporal neighbor within `config.IMPUTATION_THRESHOLD_DAYS`; if no neighbor exists within threshold, exclude the row. **Output**: Create `data/processed/reef_species_unified.csv` with imputed values. **Verification**: Ensure critical columns (SST, DHW, thermal tolerance, bleaching label) have no nulls. (Requires: T009A)
- [ ] T009C [US1] **Flagging & Logging**: Implement `code/ingest.py` to add a `trait_missing_flag` column to rows where species trait data was missing (excluded or marked as "unknown"). **Output**: Final `data/processed/reef_species_unified.csv` with flags and a `data/processed/ingestion_log.json` containing the final row count and whether a spatial subset was used. **Requirement**: If the full dataset exceeds RAM, use a spatial subset (first N rows or geographic subset defined in config) WITHOUT a `SIMULATION_MODE` flag. (Requires: T009B)
- [~] T009 [US1] **Unified Dataset**: Verify `data/processed/reef_species_unified.csv` exists with the correct schema (columns: reef_id, species_id, SST, DHW, thermal_tolerance, bleaching_label, trait_missing_flag, etc.) and no nulls in critical fields. (Requires: T009C)

- [~] T010 [US1] Implement `code/features.py`: Compute lagged environmental variables (rolling mean SST) and the specific interaction term: **DHW * thermal_tolerance**. (Requires: T009)
- [~] T011 [US1] Implement `code/features.py`: Perform Definitional Circularity Check (verify if DHW is derived from SST). **Action**: If derived, log a warning and flag the feature for potential removal or note in `data/processed/features.csv`. Do NOT compute residuals unless explicitly authorized by a future spec amendment. (Requires: T010)
- [ ] T012 [US1] Implement `code/features.py`: Calculate Variance Inflation Factor (VIF) for all predictors; drop features with VIF > 5. **Output**: Save filtered feature list to `data/processed/filtered_features.csv` AND a `data/processed/feature_list.txt` containing the column names. (Requires: T011)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Integration and Feature Construction (Priority: P1) 🎯 MVP

**Goal**: Aggregate heterogeneous data sources (NOAA, UNEP, Coral Trait DB, ReefBase) into a single, analysis-ready `reef-species` CSV with aligned environmental and trait features.

**Independent Test**: Running the ingestion pipeline produces a CSV where the row count matches the intersection of reefs and species, and critical columns (SST, DHW, thermal tolerance, bleaching label) have no nulls.

### Implementation for User Story 1

- [~] T013 [US1] Implement `tests/unit/test_ingest.py`: Verify row counts, column presence, and null handling in the unified dataset. **TDD**: Write before implementation. **Requires**: T009 (Code implementation). (Requires: T009)
- [~] T014 [US1] Implement `tests/unit/test_features.py`: Verify lagged feature calculations, circularity check logic, and VIF filtering logic. **TDD**: Write before implementation. **Requires**: T010, T011, T012 (Code implementations). (Requires: T010, T011, T012)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training, Spatial Generalization, and Statistical Validation (Priority: P2)

**Goal**: Train an XGBoost model that predicts bleaching susceptibility, generalizes to unseen regions (West vs. East Pacific), and provides statistically validated feature importance.

**Independent Test**: Executing the training script with a fixed seed and spatial split reports ROC-AUC on the held-out set and identifies top features with corrected p-values.

### Implementation for User Story 2

- [ ] T015 [US2] **Spatial Split**: Implement `code/train.py` to split data spatially (Train: Western Pacific, Test: Eastern Pacific). **Requirement**: Strictly enforce this split. If the dataset does not contain distinct Western and Eastern Pacific regions, the task MUST HALT and report "Spatial Split Failed: Missing Pacific Regions". **NO Fallback** to random split is allowed. **Output**: Save `data/processed/train_split.csv` and `data/processed/test_split.csv`. (Requires: T012)
- [~] T016 [US2] **Model Training**: Implement `code/train.py` to train XGBoost model with 5-fold cross-validation for hyperparameter tuning (max_depth, learning_rate, n_estimators). **Requirement**: If T015 failed (no valid split), this task is skipped. **Output**: Save trained model to `data/models/xgboost_model.pkl` and results to `results.json` with key `roc_auc` (float) if successful. (Requires: T015, T012)
- [~] T017 [US2] **Constitutional Gate**: Implement `code/evaluate.py` to evaluate ROC-AUC score against the 0.80 threshold mandated by Constitution Principle VII. **Logic**:
 1. Check if `results.json` exists. If not, log "N/A (Model Training Failed)" and set `performance_status` to "N/A".
 2. If `results.json` exists, check for key `roc_auc`. If missing, log "N/A (No ROC-AUC Score)" and set `performance_status` to "N/A".
 3. If `roc_auc` exists:
 - If `roc_auc` < 0.80: HALT. Write `state/constitution_failure_report.md` detailing the failure. Set `performance_status` to "FAIL" in `results.json`.
 - If `roc_auc` >= 0.80: Log "PASS". Set `performance_status` to "PASS" in `results.json`.
 **Requirement**: This task MUST block all downstream tasks (T020, T025, etc.) if the threshold is not met or if the score is missing. (Requires: T016, T005)
- [ ] T019A [US2] **Permutation Importance**: Implement `code/evaluate.py` to perform permutation importance analysis with N=1000 permutations. **Output**: Save `permutation_importance_raw.json` containing the final N, the ranking, and raw p-values. (Requires: T016, T017)
- [ ] T019B [US2] **FDR Correction**: Implement `code/evaluate.py` to apply Benjamini-Hochberg FDR correction to the p-values from T019A. **Output**: Save `permutation_results.json` containing the corrected p-values and final ranking. (Requires: T019A)
- [~] T020 [US2] **Bootstrap Stability**: Implement `code/evaluate.py` to perform Bootstrap Stability analysis (100 resamples) to measure ranking stability of top-3 predictors (SC-002). **Requires**: T016 (Model) and T019B (to ensure the base ranking is stable). (Requires: T016, T019B)
- [~] T021 [US2] **Integration Test**: Implement `tests/integration/test_pipeline.py`: End-to-end test of spatial split, training, and evaluation pipeline. (Requires: T016, T019B, T020)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Risk Mapping, Interpretability, and Threshold Robustness (Priority: P3)

**Goal**: Generate a visual risk map (GeoTIFF), identify dominant drivers for specific zones, and analyze how classification thresholds impact risk predictions.

**Independent Test**: Generating the risk map produces a valid GeoTIFF with probabilities 0-1, and the threshold sensitivity analysis reports FP/FN rate variations.

### Implementation for User Story 3

- [ ] T022 [US3] **Acquire 2024 Rasters**: Acquire 2024 environmental rasters (SST, DHW) from `config.NOAA_URL` (the same version-locked source as training data). **Requirement**: Verify file integrity and spatial alignment with the target region. **Output**: `data/raw/2024/sst.tif`, `data/raw/2024/dhw.tif`. (Requires: T003)
- [ ] T024 [US3] **Risk Map Generation**: Implement `code/map.py` to load 2024 environmental rasters (from T022) and generate `data/models/bleaching_risk_map.tif`. **Logic**: Load the trained model from `data/models/xgboost_model.pkl` and use it to predict probability of bleaching for each pixel. **Output**: A GeoTIFF file where pixel values represent the probability of bleaching (ranging from 0.0 to 1.0) as required by FR-005. **Format**: CRS must be a standard geographic coordinate reference system, Data Type must be a floating-point format. **Verification**: Verify GeoTIFF exists and values are within [0, 1]. (Requires: T016, T022)
- [ ] T023 [US3] **Local Driver Analysis**: Implement `code/map.py` to identify the dominant driver for the top high-risk pixels using **local permutation importance**. **Logic**: For each of the top 10 high-risk pixels (from T024), compute permutation importance by permuting features *within a local subset* of similar pixels to determine the primary driver (e.g., "High DHW" or "Low Thermal Tolerance"). **Output**: `data/models/local_driver_analysis.json`. **Requirement**: Do NOT use SHAP. Use local permutation importance consistent with FR-006. (Requires: T024, T019B)
- [~] T025 [US3] **Threshold Sensitivity**: Implement `code/map.py` to perform threshold sensitivity analysis sweeping cutoffs over the **exact set {0.3, 0.5, 0.7}** as defined in SC-005. **Action**: Calculate FP/FN rates for each threshold and **generate** a `threshold_sensitivity.json` file (machine-readable) and a `sensitivity_report.md` summarizing the variation (delta/range) for the end-user. (Requires: T016)
- [ ] T027 [US3] **Map Validation**: Implement `code/map.py` to validate map against independent historical bleaching reports from `config.REEFBASE_URL`. **Action**: Load independent historical bleaching events from `data/processed/reef_species_unified.csv` (validated in T009) or a separate `data/processed/independent_bleaching_events.csv` if available. **Logic**: If independent data is missing, log "Not Applicable" and set `independent_data_available` to false. Do NOT halt the project. **Output**: `metrics.json` with schema `{'auprc': float | null, 'independent_data_available': bool}`. (Requires: T024)

---

## Phase 6: Reporting & Finalization

**Purpose**: Generate final artifacts and documentation

- [ ] T028 [P] Create `research.md` report template. **Structure**: Include sections for Data Gap Status, ROC-AUC (SC-001), AUPRC (SC-003), Stability Scores (SC-002), and Threshold Sensitivity (SC-005). (Requires: None) <!-- FAILED: unspecified -->
- [~] T029 [P] Populate `research.md` report with metrics. **Data Sources**: Read `data_gap_status.json` for status, `results.json` for ROC-AUC and `performance_status`, `metrics.json` for AUPRC, `permutation_results.json` for stability, `threshold_sensitivity.json` for threshold analysis. **Verification**: Verify `research.md` exists and contains all required metrics derived from these files. (Requires: T028, T027, T017, T019B, T025)
- [~] T030 [P] Generate `data-model.md` documenting the final schema of the `reef-species` dataset. (Requires: T009)
- [~] T031 [P] Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` based on final artifacts. **Note**: Moved to Phase 1 in plan, but creation task remains here for finalization if not done earlier. (Requires: T009, T024)
- [~] T032 [P] Run `quickstart.md` validation: Log total runtime in seconds to `data/processed/runtime.log`. **Action**: If runtime > 21600s (6 hours), log a **warning** (do not halt) noting that the subset logic (T009) should have been triggered earlier; otherwise, log success. (Requires: T029)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (TDD)
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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **T009A/T009B/T009C**: Split T009 into atomic tasks for streaming, imputation, and flagging.
- **T015**: Removed fallback to random split; strict halt if Pacific regions missing.
- **T017**: Added checks for `results.json` existence and `roc_auc` key to prevent false evaluation.
- **T019A/T019B**: Split T019 into Permutation Importance and FDR Correction tasks.
- **T023**: Replaced SHAP with local permutation importance for driver analysis.
- **T024**: Added explicit CRS (EPSG:4326) and data type (Float32) specifications.
- **T027**: Changed from HALT to 'mark as N/A' if independent data is missing.
- **T022**: Added explicit requirement to use version-locked NOAA source for 2024 rasters.