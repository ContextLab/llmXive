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

- [ ] T001 Create project structure per implementation plan (directories: `code/`, `data/raw`, `data/processed`, `data/models`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (xgboost, scikit-learn, pandas, geopandas, rasterio, numpy, requests, pyyaml)
- [ ] T003 [P] Configure linting and formatting tools (ruff/black) in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` with paths, random seeds, thresholds, and `DATA_GAP_HALT` flag
- [X] T005 [P] Create `code/data_gap_report.py` to generate `data_gap_report.md` if verified sources are missing. **Success Criteria**: Script must check if any required dataset URL (e.g., `config.NOAA_URL`, `config.CORAL_TRAIT_URL`) is missing or invalid in `config.py` and, if so, generate `data_gap_report.md` listing the missing sources and a "HALT" flag. (Requires: T004)
- [ ] T012A [P] Execute Data Gap Verification: Run `code/data_gap_report.py` to generate `data_gap_report.md` if verification fails. **Blocking Gate**: If this task generates a report with missing sources, the pipeline MUST halt and NO subsequent ingestion tasks (T013+) may run. (Requires: T005)
- [X] T006 Create `code/ingest.py` skeleton for data download and merging logic (Requires: T004)
- [ ] T007 Create `code/features.py` skeleton for VIF and lagged feature logic (Requires: T004)
- [ ] T008 Create `code/train.py` skeleton for XGBoost training logic (Requires: T004)
- [~] T009 Create `code/evaluate.py` skeleton for importance and statistical tests (Requires: T004)
- [~] T010 Create `code/map.py` skeleton for GeoTIFF and threshold analysis (Requires: T004)
- [~] T011 Create `code/main.py` pipeline orchestrator (Requires: T004)
- [~] T012 Setup `tests/unit/` and `tests/integration/` directory structure

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Integration and Feature Construction (Priority: P1) 🎯 MVP

**Goal**: Aggregate heterogeneous data sources (NOAA, UNEP, Coral Trait DB, ReefBase) into a single, analysis-ready `reef-species` CSV with aligned environmental and trait features.

**Independent Test**: Running the ingestion pipeline produces a CSV where the row count matches the intersection of reefs and species, and critical columns (SST, DHW, thermal tolerance, bleaching label) have no nulls.

### Implementation for User Story 1

- [~] T020 [US1] Implement `tests/unit/test_ingest.py`: Verify row counts, column presence, and null handling in the unified dataset. (TDD: Write before implementation)
- [~] T021 [US1] Implement `tests/unit/test_features.py`: Verify lagged feature calculations and VIF filtering logic. (TDD: Write before implementation)

- [~] T013 [US1] Implement `code/ingest.py`: Download NOAA SST/DHW rasters, UNEP reef geometries, Coral Trait Database traits, and ReefBase bleaching events from URLs specified in `config.NOAA_URL`, `config.CORAL_TRAIT_URL`, etc. **Requires**: T012A (Data Gap Check must pass). (Requires: T012A)
- [~] T014 [US1] Implement `code/ingest.py`: Merge data into a unified `data/processed/reef_species_unified.csv` with 5-km grid resolution. (Requires: T013) <!-- ATOMIZE: requested -->
- [~] T015 [US1] Implement `code/ingest.py`: Handle missing values by imputing with nearest valid temporal neighbor or excluding rows if gaps exceed thresholds. (Requires: T014)
- [~] T016 [US1] Implement `code/ingest.py`: Flag rows where species trait data is missing (exclude or mark as "unknown" per edge case). (Requires: T015)
- [~] T017 [US1] Implement `code/features.py`: Compute lagged environmental variables (30-day rolling mean SST) and the specific interaction term: **DHW * thermal_tolerance**. (Requires: T016)
- [~] T018 [US1] Implement `code/features.py`: Perform Definitional Circularity Check (verify if DHW is derived from SST). **Action**: If derived, drop DHW or use residuals; otherwise, proceed. **Artifact**: Log the decision and flag in `data/processed/features.csv`. (Requires: T017)
- [~] T019 [US1] Implement `code/features.py`: Calculate Variance Inflation Factor (VIF) for all predictors; drop features with VIF > 5. **Output**: Save filtered feature list to `data/processed/filtered_features.csv`. (Requires: T018)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training, Spatial Generalization, and Statistical Validation (Priority: P2)

**Goal**: Train an XGBoost model that predicts bleaching susceptibility, generalizes to unseen regions (West vs. East Pacific), and provides statistically validated feature importance.

**Independent Test**: Executing the training script with a fixed seed and spatial split reports ROC-AUC on the held-out set and identifies top features with corrected p-values.

### Implementation for User Story 2

- [~] T022 [US2] Implement `code/train.py`: Split data spatially (Train: Western Pacific, Test: Eastern Pacific). **Requires**: T019 (VIF filtering must be complete to ensure training on uncorrelated features). (Requires: T019)
- [ ] T023 [US2] Implement `code/train.py`: Train XGBoost model with 5-fold cross-validation for hyperparameter tuning (max_depth, learning_rate, n_estimators). **Requires**: T022 (Spatial Split) and T019 (VIF Filtering). (Requires: T022, T019)
- [ ] T024 [US2] Implement `code/train.py`: Handle edge case where test set has zero positive events. **Action**: If zero positives, skip ROC-AUC calculation, write a warning to stdout, and set `ROC_AUC` to `null` in `results.json`. (Requires: T023)
- [ ] T025 [US2] Implement `code/evaluate.py`: Compute ROC-AUC score on the held-out geographic test set (SC-001). If real data missing, skip and warn. (Requires: T023)
- [ ] T026 [US2] Implement `code/evaluate.py`: Perform Permutation Importance analysis (1,000 permutations) to rank predictors. (Requires: T023)
- [ ] T027 [US2] Implement `code/evaluate.py`: Run 1,000 permutations to derive empirical p-values and apply Benjamini-Hochberg FDR correction (FR-007). (Requires: T026)
- [ ] T028 [US2] Implement `code/evaluate.py`: Perform Bootstrap Stability analysis (100 resamples) to measure ranking stability of top-3 predictors (SC-002).
- [ ] T029 [US2] Implement `tests/integration/test_pipeline.py`: End-to-end test of spatial split, training, and evaluation pipeline.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Risk Mapping, Interpretability, and Threshold Robustness (Priority: P3)

**Goal**: Generate a visual risk map (GeoTIFF), identify dominant drivers for specific zones, and analyze how classification thresholds impact risk predictions.

**Independent Test**: Generating the risk map produces a valid GeoTIFF with probabilities 0-1, and the threshold sensitivity analysis reports FP/FN rate variations.

### Implementation for User Story 3

- [ ] T031B [US3] Ingest 2024 Environmental Rasters: Download and verify 2024 environmental rasters (SST, DHW) from `config.RASTER_2024_URL` required for risk mapping. (Requires: T004)
- [ ] T030 [US3] Implement `code/map.py`: Load 2024 environmental rasters (from T031B) and generate `data/models/bleaching_risk_map.tif` (probability 0-1) (FR-005). (Requires: T023, T031B)
- [ ] T031A [US3] Verify Independent Reports: Fetch/verify existence of independent historical bleaching reports from `config.INDEPENDENT_BLEACHING_URL`. **Action**: If missing, log a warning and set `independent_data_available = false` in `metrics.json`; if present, proceed to T033. (Requires: T004)
- [ ] T031 [US3] Implement `code/map.py`: Use SHAP values to identify the dominant driver for the top 10 high-risk pixels (US-3 Acceptance Scenario 2). (Requires: T030)
- [ ] T032 [US3] Implement `code/map.py`: Perform threshold sensitivity analysis sweeping cutoffs {0.3, 0.5, 0.7}. **Action**: Calculate FP/FN rates and **generate** a `threshold_sensitivity.csv` table and a `sensitivity_report.md` summarizing the variation (delta/range) for the end-user. (Requires: T023)
- [ ] T033 [US3] Implement `code/map.py`: Validate map against independent historical bleaching reports (from T031A) by calculating and reporting AUPRC between predicted probability and observed severity. **Action**: If T031A found no data, mark as "N/A" in the report. (Requires: T031A, T030)
- [ ] T034 [US3] Implement `tests/integration/test_mapping.py`: Verify GeoTIFF generation and threshold analysis outputs.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Finalization

**Purpose**: Generate final artifacts and documentation

- [ ] T035 Generate final `research.md` report containing all metrics (ROC-AUC, AUPRC, stability scores) and data gap status. (Requires: T033, T025, T027, T028, T032)
- [ ] T036 Generate `data-model.md` documenting the final schema of the `reef-species` dataset.
- [ ] T037 Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` based on final artifacts.
- [ ] T038 Run `quickstart.md` validation: Log total runtime in seconds to `data/processed/runtime.log`. **Action**: If runtime > 21600s (6 hours), generate a `performance_report.md` alerting the team and detailing the bottleneck; otherwise, log success. (Requires: T035)

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