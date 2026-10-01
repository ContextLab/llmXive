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
- [ ] T002 [P] Configure linting and formatting tools (ruff/black) in `code/`. (Requires: T001)

---

## Phase 2: Foundational (Blocking Prerequisites & Data Ingestion)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented, including immediate data ingestion if verified.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Implement `code/config.py` with paths, random seeds, thresholds, `DATA_GAP_HALT` flag, `IMPUTATION_THRESHOLD_DAYS` (default 30), `FULL_DATA_STREAMING` (default True), and verified URLs (NOAA_URL, UNEP_URL, CORAL_TRAIT_URL, REEFBASE_URL). **Requirement**: Must validate that all URLs are reachable; if any URL is unreachable, the script must raise an error. **Action**: Populate config.py with actual, working URLs. (Requires: T001)
- [ ] T004 [P] Create `code/data_gap_report.py` to generate `data_gap_report.md` if verified sources are missing. **Success Criteria**: Script must check if any required dataset URL is missing or invalid in `config.py` and, if so, generate `data_gap_report.md` listing the missing sources and a "HALT" flag. (Requires: T003)
- [ ] T005 [P] Execute Data Gap Verification: Run `code/data_gap_report.py`. **Success Criteria**: Generate `data_gap_status.json` with `status: PASS` if all data is present; generate `data_gap_report.md` and set `status: FAIL` if missing. **Blocking Gate**: If status is FAIL, the pipeline MUST halt and NO subsequent ingestion tasks may run. **Schema**: `data_gap_status.json` must contain keys `status` (string) and `missing_sources` (list). (Requires: T004)
- [ ] T006 [US1] Implement `code/ingest.py`: Download NOAA SST/DHW rasters, UNEP reef geometries, Coral Trait Database traits, and ReefBase bleaching events from URLs specified in `config.NOAA_URL`, `config.CORAL_TRAIT_URL`, etc. **Requirement**: Must compute and record checksums for all downloaded files. **Requires**: T005 (Data Gap Check must pass). (Requires: T003, T005)
- [ ] T007 [US1] Implement `code/ingest.py`: Merge data into a unified `data/processed/reef_species_unified.csv` with 5-km grid resolution. **Logic**: 
 1. **Streaming**: Use `datasets.load_dataset(..., streaming=True)` to process the full dataset in chunks. Do NOT select a subset.
 2. **Memory Management**: If RAM usage approaches 6GB, process in chunks and aggregate statistics online (e.g., running mean, count) to preserve the full dataset's integrity.
 3. **Imputation**: Impute missing values using the nearest valid temporal neighbor within `config.IMPUTATION_THRESHOLD_DAYS`; if no neighbor exists within threshold, exclude the row.
 4. **Output**: Ensure critical columns (SST, DHW, thermal tolerance, bleaching label) have no nulls.
 5. **Flagging**: Add a `trait_missing_flag` column to rows where species trait data was missing (excluded or marked as "unknown").
 **Verification**: Verify row count matches intersection of reefs and species (or stream count) and that critical columns are non-null. (Requires: T006)
- [ ] T008 [US1] Implement `code/features.py`: Compute lagged environmental variables (30-day rolling mean SST) and the specific interaction term: **DHW * thermal_tolerance**. (Requires: T007)
- [ ] T009 [US1] Implement `code/features.py`: Perform Definitional Circularity Check (verify if DHW is derived from SST). **Action**: If derived, compute residuals (DHW - mean(DHW)) and use residuals for the interaction term; do not use raw DHW. Log the decision and flag in `data/processed/features.csv`. (Requires: T008)
- [ ] T010 [US1] Implement `code/features.py`: Calculate Variance Inflation Factor (VIF) for all predictors; drop features with VIF > 5. **Output**: Save filtered feature list to `data/processed/filtered_features.csv` AND a `data/processed/feature_list.txt` containing the column names. (Requires: T009)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Integration and Feature Construction (Priority: P1) 🎯 MVP

**Goal**: Aggregate heterogeneous data sources (NOAA, UNEP, Coral Trait DB, ReefBase) into a single, analysis-ready `reef-species` CSV with aligned environmental and trait features.

**Independent Test**: Running the ingestion pipeline produces a CSV where the row count matches the intersection of reefs and species, and critical columns (SST, DHW, thermal tolerance, bleaching label) have no nulls.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `tests/unit/test_ingest.py`: Verify row counts, column presence, and null handling in the unified dataset. **TDD**: Write before implementation. **Requires**: T007 (Code implementation). (Requires: T007)
- [ ] T012 [US1] Implement `tests/unit/test_features.py`: Verify lagged feature calculations, circularity check logic, and VIF filtering logic. **TDD**: Write before implementation. **Requires**: T008, T009, T010 (Code implementations). (Requires: T008, T009, T010)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training, Spatial Generalization, and Statistical Validation (Priority: P2)

**Goal**: Train an XGBoost model that predicts bleaching susceptibility, generalizes to unseen regions (West vs. East Pacific), and provides statistically validated feature importance.

**Independent Test**: Executing the training script with a fixed seed and spatial split reports ROC-AUC on the held-out set and identifies top features with corrected p-values.

### Implementation for User Story 2

- [ ] T013 [US2] Implement `code/train.py`: Split data spatially (Train: Western Pacific, Test: Eastern Pacific). **Requires**: T010 (VIF filtering must be complete to ensure training on uncorrelated features). (Requires: T010)
- [ ] T014 [US2] Implement `code/train.py`: Train XGBoost model with 5-fold cross-validation for hyperparameter tuning (max_depth, learning_rate, n_estimators). **Requires**: T013 (Spatial Split) and T010 (VIF Filtering). (Requires: T013, T010)
- [ ] T015 [US2] Implement `code/train.py`: Handle edge case where test set has zero positive events. **Action**: If zero positives, skip ROC-AUC calculation, write a warning to stdout, and set `ROC_AUC` to JSON `null` in `results.json`. (Requires: T014)
- [ ] T016 [US2] Implement `code/evaluate.py`: Compute ROC-AUC score on the held-out geographic test set (SC-001). If real data missing, skip and warn. (Requires: T014)
- [ ] T017 [US2] **Constitutional Gate**: Evaluate ROC-AUC score from T016 against the 0.80 threshold mandated by Constitution Principle VII. **Action**: 
 1. Read `data_gap_status.json`. If `status: FAIL`, log "N/A" for ROC-AUC and proceed.
 2. If `status: PASS`, read `results.json` key `roc_auc`. If score < 0.80, generate `scope_amendment_report.md` detailing the failure and halt the pipeline; otherwise, proceed. (Requires: T016, T005)
- [ ] T018 [US2] **Convergence-Driven Permutation & FDR**: Implement a single atomic task in `code/evaluate.py` that:
 1. **Determines Sufficiency**: Runs a convergence loop to find the minimum permutation count `N` where feature ranking stability (Spearman correlation) stabilizes. **Algorithm**: Start with `batch_size=200`, increment by `200` per step, max `2000`. Convergence criterion: correlation delta < 0.01 over 2 consecutive increments. Log steps to `convergence_log.json`.
 2. **Executes Importance**: Performs the final permutation importance analysis using the determined `N`.
 3. **Calculates P-Values**: Derives empirical p-values for all features based on the `N` permutations.
 4. **Applies FDR**: Applies Benjamini-Hochberg correction to the p-values (FR-007).
 **Output**: Save `permutation_results.json` containing the final `N`, the ranking, and corrected p-values. **Requirement**: This task must succeed only if convergence is reached or `N` hits the max (log warning if max hit). (Requires: T014, T016, T017)
- [ ] T019 [US2] Implement `code/evaluate.py`: Perform Bootstrap Stability analysis (100 resamples) to measure ranking stability of top-3 predictors (SC-002). **Requires**: T014 (Model) and T018 (to ensure the base ranking is stable and sufficient). (Requires: T014, T018)
- [ ] T020 [US2] Implement `tests/integration/test_pipeline.py`: End-to-end test of spatial split, training, and evaluation pipeline. (Requires: T014, T016, T018)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Risk Mapping, Interpretability, and Threshold Robustness (Priority: P3)

**Goal**: Generate a visual risk map (GeoTIFF), identify dominant drivers for specific zones, and analyze how classification thresholds impact risk predictions.

**Independent Test**: Generating the risk map produces a valid GeoTIFF with probabilities 0-1, and the threshold sensitivity analysis reports FP/FN rate variations.

### Implementation for User Story 3

- [ ] T021 [US3] Acquire 2024 environmental rasters (SST, DHW) from `config.NOAA_URL` or local `data/raw/2024/`. **Requirement**: Verify file integrity and spatial alignment with the target region. **Output**: `data/raw/2024/sst.tif`, `data/raw/2024/dhw.tif`. (Requires: T003)
- [ ] T022 [US3] Implement `code/map.py`: Load 2024 environmental rasters (from T021) and generate `data/models/bleaching_risk_map.tif`. **Logic**: Use the trained model to predict probability of bleaching for each pixel. **Output**: A GeoTIFF file where pixel values represent the probability of bleaching (ranging from 0.0 to 1.0) as required by FR-005. **Verification**: Verify GeoTIFF exists and values are within [0, 1]. (Requires: T014, T021)
- [ ] T023 [US3] Implement `code/map.py`: Use SHAP values to identify the dominant driver for the top 10 high-risk pixels (US-3 Acceptance Scenario 2). (Requires: T022)
- [ ] T024 [US3] Implement `code/map.py`: Perform threshold sensitivity analysis sweeping cutoffs over a **continuous range [0.1, 0.9] with step 0.05**, explicitly including the SC-005 set {0.3, 0.5, 0.7}. **Action**: Calculate FP/FN rates for each threshold and **generate** a `threshold_sensitivity.csv` table and a `sensitivity_report.md` summarizing the variation (delta/range) for the end-user. (Requires: T014)
- [ ] T025 [US3] Implement `code/map.py`: Validate map against independent historical bleaching reports from `config.REEFBASE_URL`. **Action**: Fetch `2023_bleaching_events.csv` from REEFBASE_URL. If data is available, calculate and report AUPRC between predicted probability and observed severity. If no independent data exists, log a warning and set `independent_data_available = false` in `metrics.json`. (Requires: T022)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Finalization

**Purpose**: Generate final artifacts and documentation

- [ ] T026 [P] Generate final `research.md` report. **Structure**: Include sections for Data Gap Status, ROC-AUC (SC-001), AUPRC (SC-003), Stability Scores (SC-002), and Threshold Sensitivity (SC-005). **Data Sources**: Read `data_gap_status.json` for status, `results.json` for ROC-AUC, `metrics.json` for AUPRC, `permutation_results.json` for stability, `sensitivity_report.md` for threshold analysis. **Verification**: Verify `research.md` exists and contains all required metrics derived from these files. (Requires: T025, T016, T018, T019, T024)
- [ ] T027 [P] Generate `data-model.md` documenting the final schema of the `reef-species` dataset. (Requires: T007)
- [ ] T028 [P] Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` based on final artifacts. (Requires: T007, T022)
- [ ] T029 [P] Run `quickstart.md` validation: Log total runtime in seconds to `data/processed/runtime.log`. **Action**: If runtime > 21600s (6 hours), generate a `performance_report.md` alerting the team and detailing the bottleneck; otherwise, log success. (Requires: T026)

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