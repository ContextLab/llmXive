# Tasks: Predicting Avian Song Variation with Climatic and Geographic Factors

**Input**: Design documents from `/specs/001-predicting-avian-song-variation-with-cli/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this user story belongs to (e.g., US1, US2, US3)
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

- [ ] T001a [P] Create directory structure at `projects/PROJ-334-predicting-avian-song-variation-with-cli/{data,code,tests}` using `mkdir -p`
- [X] T001b [P] Create `requirements.txt` with dependencies: pandas, numpy, scikit-learn, statsmodels, scipy, matplotlib, seaborn, pyyaml, requests, rasterio, geopandas, pyproj, pytest; Create `.gitignore` with patterns for `data/raw/`, `data/processed/`, `__pycache__/`, `*.pyc`, `.env`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Initialize Python project with dependencies: pandas, numpy, scikit-learn, statsmodels, scipy, matplotlib, seaborn, pyyaml, requests, rasterio, geopandas, pyproj
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Setup data directory structure (`data/raw/`, `data/processed/`) and initialize `data/checksums.txt` with a CSV header (`filename,hash`) AND initialize the project state file `state/projects/PROJ-334-predicting-avian-song-variation-with-cli.yaml` with an empty `artifact_hashes` map to satisfy Constitution Principle III. **Depends on T001a.**
- [ ] T005 [P] Create base configuration loader for environment variables and paths, including a configurable `join_radius_km` parameter with a **default value of 10km ** (based on WorldClim resolution) to ensure reproducibility without manual intervention.
- [ ] T007 [P] Create schema definition files `contracts/song_record.schema.yaml` (fields: species_id, lat, lon, song_metric_1, song_metric_2), `contracts/climate_snapshot.schema.yaml` (fields: lat, lon, temperature, precipitation, elevation), `contracts/analysis_dataset.schema.yaml` (fields: all above merged)
- [X] T008 [P] Implement schema validation utilities (`code/utils.py`) for `SongRecord`, `ClimateSnapshot`, and `AnalysisDataset`, AND implement coordinate reprojection logic (WGS84/NAD83) in the same utility module
- [X] T009 [P] Create data source contracts (`contracts/data_sources.yaml`) defining {{claim:c_5ade1739}} ({{claim:c_b9be9184}}, {{claim:c_8865816b}}) and WorldClim v2.1 [UNRESOLVED-CLAIM: c_62d807c9 — status=not_enough_info] URLs, sample paths, and version pinning logic
- [X] T010 [P] Create `code/main.py` orchestration entry point with argument parsing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Variable Alignment (Priority: P1) 🎯 MVP

**Goal**: Load real avian acoustic data ({{claim:c_5ade1739}}) and climate data (WorldClim v2.1 [UNRESOLVED-CLAIM: c_62d807c9 — status=not_enough_info]), align by location/species, and produce a unified `AnalysisDataset`.

**Independent Test**: Can be fully tested by executing `code/ingestion.py` against the provided sample CSVs or real fetch and verifying the output schema contains required columns with no duplicate rows.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `fetch_xeno_canto.py` to download real metadata (species_id, lat, lon) from {{claim:c_5ade1739}} API (referencing T009 for URL/version), using `streaming=True` or `itertools.islice` to handle large datasets, record SHA256 checksum immediatelyto `data/checksums.txt` **AND update `state/projects/PROJ-334-predicting-avian-song-variation-with-cli.yaml` `artifact_hashes`**, and abort on fetch failure. **Depends on T009, T004.**
- [ ] T012 [US1 ({{claim:c_5797672a}}, {{claim:c_9b1f041a}})] Implement `fetch_worldclim.py` to download real climate variables (temp, precip, elev) from WorldClim v2.1 [UNRESOLVED-CLAIM: c_62d807c9 — status=not_enough_info] (referencing T009 for URL/version), using `streaming=True` or `itertools.islice` to handlelarge datasets, record SHA256 checksum immediately to `data/checksums.txt` **AND update `state/projects/PROJ-334-predicting-avian-song-variation-with-cli.yaml` `artifact_hashes`**, and abort on fetch failure. **Depends on T009, T004.** <!-- FAILED: unspecified -->
- [ ] T013 [US1] Implement `code/ingestion.py` to load raw CSVs (from T011/T012), validate against `contracts/*.schema.yaml` (using T008 utilities), and handle coordinate reprojection (WGS84) using T008 utilities. **Must explicitly detect CRS mismatch by reading CRS from GeoTIFF metadata or inferring from coordinate bounds before applying reprojection.** **Depends on T007, T008, T005, T011, T012.**
- [X] T014 [US1] Implement spatial join logic in `code/ingestion.py` to merge `SongRecord` and `ClimateSnapshot` by performing a spatial join within the `join_radius_km` (defined in T005 config). **Depends on T013.**
- [X] T015 [US1] Calculate and log match rate (matched/total) and verify no duplicates in `code/ingestion.py`
- [X] T016 [US1] Implement exclusion logic for unmatched species and logging of warnings in `code/ingestion.py`. **Output:** Write a JSON file `data/logs/excluded_species.json` with schema `{ "excluded_ids": ["..."], "count": 0, "reason": "..." }`. **Depends on T014.**
- [ ] T017 [US1] Save the unified `AnalysisDataset` to `data/processed/analysis_dataset.csv` and update `data/checksums.txt` **and state file**. **Must complete before T021.**

### Tests for User Story 1

- [ ] T018 [US1] Unit test for coordinate reprojection logic in `tests/test_ingestion.py` (depends on T013 implementation)
- [ ] T019 [US1] Unit test for schema validation and join logic in `tests/test_ingestion.py` (depends on T013/T014 implementation)
- [ ] T020 [US1] Integration test for full ingestion pipeline (fetch -> join -> save) in `tests/test_ingestion.py` (depends on T011-T017 implementation)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Exploratory Data Analysis and Correlation Matrix (Priority: P2)

**Goal**: Generate statistical summaries, correlation matrices, and multicollinearity diagnostics (VIF) to validate data quality and relationships.

**Independent Test**: Can be fully tested by running `code/eda.py` and verifying a JSON report is generated with a symmetric correlation matrix, valid ranges bounded by theoretical limits, and VIF flags.

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/eda.py` to load `AnalysisDataset` (validating against T007/T008 schemas), generate summary statistics (mean, std, range). **Depends on T017.**
- [ ] T022 [US2] Implement Pearson correlation matrix calculation between song metrics and environmental predictors in `code/eda.py`
- [ ] T023 [US2] Implement multicollinearity threshold check (default 0.8) and flagging in `code/eda.py`
- [ ] T024 [US2] Implement Variance Inflation Factor (VIF) calculation for all predictors in `code/eda.py`
- [ ] T024a [US2] Verify VIF output and generate flag report for any predictor with VIF > 5 in `code/eda.py`
- [ ] T026 [US2] Generate and save EDA report (`data/eda_report.json`) containing `correlation_matrix`, `summary_stats`, and `vif_flags` (keys explicitly required). Ensure correlation matrix values are strictly within [-1.0, 1.0] and include a validation step to assert this.

### Tests for User Story 2

- [ ] T027 [US2] Unit test for correlation matrix calculation and symmetry in `tests/test_eda.py`
- [ ] T028 [US2] Unit test for VIF calculation and threshold flagging in `tests/test_eda.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling with Sensitivity Analysis (Priority: P3)

**Goal**: Fit multiple linear regression models, perform sensitivity analysis on p-value thresholds, and apply FDR control.

**Independent Test**: Can be fully tested by running `code/modeling.py` and verifying model files, sensitivity reports, and FDR-adjusted p-values.

### Implementation for User Story 3

- [ ] T030a [US3] Implement `code/modeling.py` to fit a **Null Model** (intercept-only) for both `song_metric_1` and `song_metric_2`. **Depends on T026.**
- [ ] T029 [US3] Implement `code/modeling.py` to fit Model A (Climate Only) and Model B (Climate + Geo) using `statsmodels`, explicitly targeting song_metric_1/song_metric_2, consuming EDA report (T026) for multicollinearity diagnostics, and flagging analysis as 'associational' in output metadata. **Depends on T030a, T026.**
- [ ] T030b [US3] Calculate and report the **delta R²** (R²_model - R²_null) for both metrics in `code/modeling.py` and save to `data/model_performance.json`. **Depends on T029, T030a.**
- [ ] T031a [US3] **Explicitly aggregate p-values**: Extract p-value vectors from the outputs of Model A and Model B (from T029) for both `song_metric_1` and `song_metric_2`, concatenate them into a single list, and save to `data/aggregated_pvalues.json`. **Depends on T029.**
- [ ] T031 [US3] Implement sensitivity analysis: sweep p-value thresholds across {0.01, 0.05, 0.10}, track significant predictors, calculate Jaccard index (J = |A∩B| / |A∪B|) comparing sets of significant predictors at each threshold pair, and save results (including Jaccard values) to `data/sensitivity_report.json`. **Depends on T029.**
- [ ] T032a [US3] Implement {{claim:c_26c166a0}} (2607.12208, https://arxiv.org/abs/2607.12208) in `code/modeling.py` to adjust p-values using the **aggregated list** from T031a. **Depends on T031a.**
- [ ] T032 [US3] Apply FDR correction to p-values in `code/modeling.py` using the procedure from T032a and save adjusted p-values to the sensitivity report. **Depends on T032a.**
- [ ] T033 [US3] Save fitted models (`data/models/model_a.pkl`, `data/models/model_b.pkl`) and sensitivity report (`data/sensitivity_report.json`) including FDR-adjusted p-values
- [ ] T034 [US3] Add error handling for zero-variance predictors and abort with clear message in `code/modeling.py`

### Tests for User Story 3

- [ ] T035 [US3] Unit test for model fitting and R² calculation in `tests/test_modeling.py`
- [ ] T036 [US3] Unit test for sensitivity analysis sweep logic in `tests/test_modeling.py`
- [ ] T037 [US3] Unit test for Benjamini-Hochberg FDR procedure in `tests/test_modeling.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates: Update `README.md` with execution instructions and create `docs/api.md` with function signatures for `ingestion.py`, `eda.py`, and `modeling.py`.
- [ ] T039a [P] Lint and format check across all code files (ruff/black)
- [ ] T039b [P] target < 10 across all functions
- [ ] T040 [P] Performance optimization: Profile `ingestion.py` using `cProfile` and optimize spatial join using `geopandas.sindex` or `rtree` to reduce runtime.
- [ ] T041 [P] Additional unit tests for edge cases (missing data, coordinate mismatches)
- [ ] T042 [P] Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T007 must complete before T008
 - T008 must complete before T013
 - T005 must complete before T011/T012
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T017)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 diagnostics (T026)

### Within Each User Story

- Implementation tasks MUST be completed before Test tasks
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (within their respective test suites, after implementation)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement fetch_xeno_canto.py to download real metadata"
Task: "Implement fetch_worldclim.py to download real climate variables"

# Launch all tests for User Story 1 together (after implementation):
Task: "Unit test for coordinate reprojection logic in tests/test_ingestion.py"
Task: "Unit test for schema validation and join logic in tests/test_ingestion.py"
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

- [P] tasks = different files, no dependencies (except explicit implementation dependencies noted)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence