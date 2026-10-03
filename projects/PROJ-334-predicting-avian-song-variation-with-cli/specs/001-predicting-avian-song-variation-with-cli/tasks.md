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
- [X] T004 [P] Setup data directory structure (`data/raw/`, `data/processed/`, `data/logs/`) and initialize `data/checksums.txt` with a CSV header (`filename,sha256_hash`). Initialize the project state file `state/projects/PROJ-334-predicting-avian-song-variation-with-cli.yaml` with an empty `artifact_hashes` map and `updated_at: "1970-01-01T00:00:00Z"`. **Depends on T001a.**
- [X] T004b [P] Implement `code/utils.py` function `update_state_file()` to dynamically update `artifact_hashes` and `updated_at` in the project state YAML file on every artifact change. **Depends on T004.**
- [ ] T005 [P] Create base configuration loader for environment variables and paths, including a configurable `join_radius_km` parameter with a **default value of 10km** (justified as a spatial buffer for GPS error relative to ~1km WorldClim resolution) to ensure reproducibility without manual intervention.
- [ ] T007 [P] Create schema definition files `contracts/song_record.schema.yaml` (fields: species_id, lat, lon, song_metric_1, song_metric_2), `contracts/climate_snapshot.schema.yaml` (fields: lat, lon, temperature, precipitation, elevation), `contracts/analysis_dataset.schema.yaml` (fields: all above merged)
- [X] T008 [P] Implement schema validation utilities (`code/utils.py`) for `SongRecord`, `ClimateSnapshot`, and `AnalysisDataset`. **Depends on T007.**
- [X] T009 [P] Create `code/data_sources.yaml` defining Xeno-Canto API (https://www.xeno-canto.org/explore) and WorldClim v2.1 (https://www.worldclim.org/data/worldclim21.html) URLs, sample paths, and version pinning logic. **Must use verified URLs; remove any unresolved claim references.**
- [X] T010 [P] Create `code/main.py` orchestration entry point with argument parsing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Variable Alignment (Priority: P1) 🎯 MVP

**Goal**: Load real avian acoustic data (Xeno-Canto) and climate data (WorldClim v2.1), align by location/species, and produce a unified `AnalysisDataset`.

**Independent Test**: Can be fully tested by executing `code/ingestion.py` against the provided sample CSVs or real fetch and verifying the output schema contains required columns with no duplicate rows.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `fetch_xeno_canto.py` to load real metadata (species_id, lat, lon) from Xeno-Canto API (referencing T009 for URL/version). **STRICT PRODUCTION MODE: Attempt to fetch real data ONLY. If fetch fails, the script MUST abort with a clear error. Local sample CSVs (`data/raw/xeno_canto_sample.csv`) are permitted ONLY for local development/testing and MUST NOT be used as a fallback in production/CI runs. If a sample is used for testing, a pinned sample version hash must be recorded to ensure reproducibility.** Record SHA256 checksum immediately to `data/checksums.txt` AND update `state/projects/PROJ-334-predicting-avian-song-variation-with-cli.yaml` `artifact_hashes` by invoking `update_state_file()` (T004b). **Depends on T009, T004, T004b.**
- [ ] T012 [US1] Implement `fetch_worldclim.py` to load real climate variables (temp, precip, elev) from WorldClim v2.1 (referencing T009 for URL/version). **STRICT PRODUCTION MODE: Attempt to fetch real data ONLY. If fetch fails, the script MUST abort with a clear error. Local sample CSVs (`data/raw/worldclim_sample.csv`) are permitted ONLY for local development/testing and MUST NOT be used as a fallback in production/CI runs. If a sample is used for testing, a pinned sample version hash must be recorded.** Record SHA256 checksum immediately to `data/checksums.txt` AND update `state/projects/PROJ-334-predicting-avian-song-variation-with-cli.yaml` `artifact_hashes` by invoking `update_state_file()` (T004b). **Depends on T009, T004, T004b.**
- [ ] T013 [US1] Implement `code/ingestion.py` to load raw CSVs (from T011/T012) and validate against `contracts/*.schema.yaml` (using T008 utilities). **CRITICAL: Do NOT assume CRS or reproject here.** **Depends on T007, T008, T005, T011, T012.**
- [ ] T013b [US1] Implement CRS detection and reprojection logic in `code/ingestion.py`. **Check metadata for CRS. If non-WGS84 (e.g., NAD83), reproject to WGS84 (EPSG:4326) using `pyproj.Transformer`. If metadata is absent, assume WGS84 but log a warning. Do NOT proceed to join without ensuring data is in WGS84.** **Depends on T013.**
- [ ] T014 [US1] Implement spatial join logic in `code/ingestion.py` to merge `SongRecord` and `ClimateSnapshot`. **Perform a vector-vector spatial join on the reprojected CSV point data (from T013b) within the `join_radius_km` (defined in T005 config, derived from WorldClim raster resolution). This step operates on the validated, reprojected CSV points.** **Depends on T013b.**
- [ ] T015 [US1] Calculate and log match rate (matched/total) and verify no duplicates in `code/ingestion.py`
- [ ] T016 [US1] Implement exclusion logic for unmatched species and logging of warnings in `code/ingestion.py`. **Output:** Write a JSON file `data/logs/excluded_species.json` with schema `{ "excluded_ids": ["..."], "count": 0, "reason": "..." }`. **Depends on T014.**
- [ ] T017 [US1] Save the unified `AnalysisDataset` to `data/processed/analysis_dataset.csv` and update `data/checksums.txt` **and state file** using `update_state_file()` (T004b). **Must complete after T016.** **Depends on T015, T016, T004b.**

### Tests for User Story 1

- [X] T018 [US1] Unit test for coordinate reprojection logic in `tests/test_ingestion.py` (depends on T013b implementation)
- [X] T019 [US1] Unit test for schema validation and join logic in `tests/test_ingestion.py` (depends on T013/T014 implementation)
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
- [ ] T024 [US2] Implement Variance Inflation Factor (VIF) calculation for all predictors in `code/eda.py` **AND implement pairwise correlation checks to identify specific *pairs* of predictors with high collinearity (r > 0.8). Flag any pair exceeding this threshold in the report, explicitly listing the `pair: [var1, var2]` and correlation value.** **Depends on T021.**
- [ ] T026 [US2] Generate and save EDA report (`data/eda_report.json`) containing `correlation_matrix`, `summary_stats`, `vif_flags`, and `pairwise_correlation_flags`. Ensure correlation matrix values are strictly within [-1.0, 1.0] and include a validation step to assert this. **Depends on T024.**

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
- [ ] T031a [US3] **Explicitly aggregate p-values**: Extract p-value vectors from the outputs of Model A and Model B (from T029) for both `song_metric_1` and `song_metric_2`, **flatten them into a single list of floats**, and save to `data/aggregated_pvalues.json` with metadata. **Schema:** `[{ "metric": "...", "threshold": "...", "p_value": float, "raw_p_value": float }, ...]`. **Depends on T029.**
- [ ] T031b [US3] Implement sensitivity analysis: sweep p-value thresholds across {0.01, 0.05, 0.10}, track significant predictors, calculate Jaccard index (J = |A∩B| / |A∪B|) comparing sets of significant predictors at **every** threshold pair, and **save the full list of per-pair Jaccard values** (not just aggregate) to `data/sensitivity_report.json`. Calculate and report a single aggregate stability metric (mean Jaccard and min Jaccard) as well. **Depends on T031a.**
- [ ] T031c [US3] Implement Benjamini-Hochberg procedure using `statsmodels.stats.multitest.multipletests` with `method='fdr_bh'` in `code/modeling.py` to adjust p-values using the **flattened single list of p-values** from T031a. **Algorithm:** Sort p-values, calculate rank, apply BH formula, save adjusted p-values. **Depends on T031a.**
- [ ] T032 [US3] Apply FDR correction to p-values in `code/modeling.py` using the procedure from T031c and save adjusted p-values to the sensitivity report. **Depends on T031c.**
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
- [ ] T039b [P] Target cyclomatic complexity < 10 across all functions using tool: ruff
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
 - T004 must complete before T004b
 - T004b must complete before T011/T012/T017
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T007->T008)
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