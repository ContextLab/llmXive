# Tasks: Statistical Analysis of Publicly Available Weather Data for Extreme Event Prediction

**Input**: Design documents from `/specs/001-extreme-weather-spatial-analysis/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure: Execute `mkdir -p src/{data,models,evaluation,visualization,pipeline,scripts,cli} tests/{unit,integration,contract} data/{raw,processed} outputs/{plots,metrics} state`. Create empty `__init__.py` files in all `src` and `tests` directories. <!-- ATOMIZE: requested -->
- [ ] T002 Initialize Python 3.11 project with requirements.txt (`pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `pyyaml`, `geopandas`, `pytest`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `src/config.py` to load hyperparameters, paths, seeds, and the 6-hour compute limit
- [ ] T005 [P] Implement `src/scripts/validate_citations.py` to verify NOAA GHCN-Daily URL availability before execution
- [ ] T005-exec [P] Execute `src/scripts/validate_citations.py` as a blocking gate; HALT pipeline if validation fails (Depends on T005)
- [ ] T006 Implement `src/scripts/hygiene_check.py` to compute SHA-256 hashes for raw data and write to `state/projects/...yaml` (Depends on T005-exec success to ensure valid data is hashed)
- [ ] T006-exec [P] Execute `src/scripts/hygiene_check.py` as a blocking gate; HALT pipeline if hash verification fails (Depends on T006)
- [~] T007 Create base `src/data/loaders.py` for HuggingFace/NOAA dataset fetching with checksum verification
- [~] T008 Configure error handling and logging infrastructure in `src/pipeline/logging_config.py`
- [~] T009 Setup `src/pipeline/config.py` to enforce a predefined wall-clock time limit and trigger fallback logic

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Extreme Event Definition (Priority: P1) 🎯 MVP

**Goal**: Ingest NOAA GHCN-Daily data for Northeast USA, handle missing values, and define extreme events using a peaks-over-threshold approach on the 2000–2015 training set.

**Independent Test**: Run the pipeline on 2000–2015 data; verify output contains time-series of exceedances for 90–110 stations with <1% missing data, excluding stations with >15% missing or >30 day gaps.

### Implementation for User Story 1

- [~] T010 [US1] Implement `src/data/ingestion.py` to download NOAA GHCN-Daily CSVs for Northeast USA (2000–2020)
- [ ] T011 [US1] Implement station filtering in `src/data/preprocessing.py`: exclude stations with >15% total missing OR >30 day contiguous gaps (Depends on T010)
- [ ] T012 [US1] Implement linear interpolation for short gaps in `src/data/preprocessing.py` (Depends on T011)
- [ ] T013 [US1] Calculate high percentile thresholds strictly on 2000–2015 training data in `src/data/preprocessing.py` (Depends on T012)
- [ ] T013b [US1] Implement sensitivity analysis: Re-run the full model comparison (US-2) for thresholds {90th, 95th, 99th} and generate robustness report of predictive gain in `src/data/preprocessing.py` (Depends on T013 logic, runs in parallel with T014b)
- [ ] T014 [US1] Implement extreme event flagging: mark days > threshold as exceedances with magnitude in `src/data/preprocessing.py` (Depends on T013)
- [ ] T014b [US1] Implement `ExtremeEvent` entity mapping logic: Create function to map raw data to the `ExtremeEvent` schema (station_id, date, magnitude, threshold_value) defined in spec.md (Depends on T014)
- [ ] T015 [US1] Generate `data/processed/extreme_events.parquet` containing station_id, date, magnitude, threshold_value (Depends on T014b)
- [ ] T016 [US1] Add summary statistics reporter in `src/data/summary.py` (exceedance count per station, average magnitude, sensitivity report) (Depends on T015)
- [ ] T017 [US1] Unit test: Verify station exclusion logic for >30 day gaps in `tests/unit/test_ingestion.py`
- [ ] T018 [US1] Unit test: Verify threshold calculation is isolated to training data in `tests/unit/test_preprocessing.py`

**Checkpoint**: User Story 1 (Data Layer) is fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline vs. Spatial Model Comparison (Priority: P2)

**Goal**: Fit an independent GPD baseline and a Spatial-GPD (Gaussian Copula) model, then compare Brier scores and RMSE on the 2019–2020 test set.

**Independent Test**: Execute training on 2000–2015 and evaluation on 2019–2020; verify `outputs/metrics.json` contains Brier/RMSE for both models and logs fallback if spatial fit exceeds time limit.

### Implementation for User Story 2

- [ ] T021 [US2] Implement time-monitoring wrapper in `src/pipeline/run_analysis.py` to enforce 6-hour limit, estimate remaining time, and trigger subsampling/fallback if estimated time exceeds threshold (Must precede T019/T020 execution)
- [ ] T020b [US2] Implement time-series subsampling logic in `src/pipeline/run_analysis.py`: Sample every 3rd day if fit time > 2 hours, as a fallback branch before hard limit (Depends on T021)
- [ ] T019 [US2] Implement `src/models/gpd_baseline.py`: Fit independent GPD for each station using `scipy.stats` (Depends on T021)
- [ ] T019a [US2] Document Methodological Pivot: Create `docs/pivot_validation.md` explaining the deviation from FR-004 (Brown-Resnick) to Spatial-GPD and validating scientific soundness (Depends on T019 logic)
- [ ] T020 [US2] Implement `src/models/spatial_model.py`: Fit Spatial-GPD with Gaussian Copula dependence structure (Depends on T021, T020b)
- [ ] T022 [US2] Implement probabilistic exceedance prediction logic for Brier score calculation in `src/evaluation/metrics.py`
- [ ] T023 [US2] Implement RMSE calculation for intensity prediction in `src/evaluation/metrics.py`
- [ ] T024b [US2] Estimate correlation length: Implement function in `src/evaluation/metrics.py` to calculate correlation length from the variogram of extremes (Depends on T020)
- [ ] T024c [US2] Implement block bootstrap sampling logic: Create function `src/evaluation/metrics.py::block_bootstrap` to resample residuals with block size equal to the estimated correlation length from T024b (Depends on T024b)
- [ ] T024d [US2] Calculate empirical coverage: Implement `src/evaluation/metrics.py::calculate_coverage` to compare nominal vs. empirical coverage of % CIs (Depends on T024c)
- [ ] T024 [US2] Generate `outputs/metrics.json` with Brier score, RMSE, model_type, fallback flags, and CI coverage (Depends on T022, T023, T024c, T024d)
- [ ] T025 [US2] Unit test: Verify independent GPD parameters are station-specific in `tests/unit/test_gpd.py`
- [ ] T026 [US2] Unit test: Verify Brier score derivation from probabilistic predictions in `tests/unit/test_metrics.py`
- [ ] T027 [US2] Integration test: Verify fallback to independent GPD if spatial model exceeds time threshold in `tests/integration/test_pipeline.py`

**Checkpoint**: User Story 2 (Modeling & Evaluation) is fully functional and testable independently

---

## Phase 5: User Story 3 - Cross-Validation and Diagnostic Visualization (Priority: P3)

**Goal**: Perform Leave-One-Station-Out (LOSO) cross-validation using "Global Dependence, Local Prediction" and generate diagnostic plots (variograms, QQ-plots, maps).

**Independent Test**: Run LOSO loop; verify output includes diagnostic plots and a summary of error reduction compared to baseline, with time-limit monitoring.

### Implementation for User Story 3

- [ ] T028 [US3] Implement "Global Dependence, Local Prediction" logic in `src/evaluation/cross_validation.py` (fit dependence once, predict locally)
- [ ] T029 [US3] Implement LOSO loop to predict extremes for held-out stations using neighbor data in `src/evaluation/cross_validation.py` (Depends on T028)
- [ ] T028a [US3] Document LOSO Strategy: Create `docs/loso_validation.md` validating the "Global Dependence, Local Prediction" strategy against the intent of FR-006 (Depends on T028, T029)
- [ ] T030 [US3] Implement variogram of extremes calculation in `src/models/utils.py` (Depends on T029)
- [ ] T031 [US3] Generate variogram plot of extremes in `src/visualization/plots.py` (Depends on T030)
- [ ] T032 [US3] Generate QQ-plots for marginal GPD fits in `src/visualization/plots.py`
- [ ] T033 [US3] Implement regional exceedance probability mapping in `src/visualization/maps.py` using `geopandas`
- [ ] T034 [US3] Generate `outputs/plots/` directory containing variogram, QQ-plots, and regional maps
- [ ] T035 [US3] Unit test: Verify LOSO prediction uses only neighbor data for the held-out station in `tests/unit/test_cross_validation.py`
- [ ] T036 [US3] Integration test: Verify 6-hour limit is monitored during LOSO and fallback is logged in `tests/integration/test_pipeline.py`

**Checkpoint**: All user stories are independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates: Update `README.md` with CLI usage examples and data hygiene instructions; update `docs/pivot_validation.md` (T019a) and `docs/loso_validation.md` (T028a) with final results; ensure all spec deviations are documented
- [ ] T038 Code cleanup and refactoring of `src/pipeline`: Refactor `src/pipeline/run_analysis.py` to reduce cyclomatic complexity to < 15 and extract fallback logic into a separate function
- [ ] T039 Performance optimization for spatial model fitting: Refactor `src/models/spatial_model.py` to use numpy vectorization for the covariance matrix calculation, targeting a [deferred] reduction in fit time on the 2000-2015 dataset
- [ ] T040 [P] Additional unit tests for edge cases: Add `tests/unit/test_edge_cases.py` with tests for empty datasets (`test_empty_dataset_handling`) and single station scenarios (`test_single_station_handling`)
- [ ] T041 Run `scripts/hygiene_check.py` on final artifacts
- [ ] T043 Audit outputs: Verify `outputs/metrics.json` schema against `contracts/output.schema.yaml` and audit fallback logs for correctness (Depends on T024, T036)
- [ ] T042 Verify `quickstart.md` execution end-to-end

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires data from US1 and models from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) except T006 which depends on T005
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test: Verify station exclusion logic for >30 day gaps in tests/unit/test_ingestion.py"
Task: "Unit test: Verify threshold calculation is isolated to training data in tests/unit/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement station filtering in src/data/preprocessing.py"
Task: "Implement linear interpolation for short gaps in src/data/preprocessing.py"
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

- [P] tasks = different files, no dependencies (except T006 which depends on T005)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All data ingestion tasks MUST use real NOAA GHCN-Daily URLs; no synthetic data generation.
- **CRITICAL**: Spatial model fitting MUST respect a strict computational time constraint to ensure feasibility within the allocated resources.; fallback to independent GPD is mandatory if exceeded.
- **CRITICAL**: Sensitivity analysis (T013b) and CI coverage (T024c, T024d) are mandatory per Spec Assumptions and SC-003.
- **CRITICAL**: Methodological pivot (T019a) and LOSO strategy validation (T028a) are mandatory to ensure traceability of spec deviations AND require creating documentation in `docs/`.