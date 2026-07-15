# Tasks: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

**Input**: Design documents from `/specs/001-bird-migration-climate-correlation/`
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

- [ ] T001 Create project structure per implementation plan by executing: `mkdir -p src/data src/models src/analysis data/raw data/processed data/interim tests/contract tests/unit tests/integration docs`
- [ ] T003a Create `pyproject.toml` at repository root with `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (lint.select=['E','F','W','I'], lint.ignore=[]) configuration sections
- [ ] T003b Create `.pre-commit-config.yaml` with hooks for `black` and `ruff` and configure pre-commit installation instructions in `README.md`
- [ ] T004 Create empty `src/data/download.py` file at repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement `src/data/download.py` to:
 1. Check for real eBird/NOAA files in `data/raw/ebird/` and `data/raw/climate/`.
 2. **Production Mode**: If real data is missing, ABORT with exit code 1 and error message "Real data required for production run".
 3. **Development Mode**: If real data is missing, generate synthetic data using `numpy.random` with seed 42, writing `data/raw/synthetic_ebird.csv` and `data/raw/synthetic_climate.parquet` matching `contracts/dataset.schema.yaml`.
 4. Archive real files unchanged (copy to `data/raw/archive/`) and compute SHA-256 checksums.
 5. Write checksums to `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml` under keys `artifact_hashes` and `updated_at`.
- [ ] T006 [P] Add `tests/contract/test_schemas.py::test_ebird_schema_columns` asserting `df.columns` equals [species, lat, lon, date, count, checklist_id] and `df.dtypes` match expected types (TDD: Write before implementation)
- [X] T007 [P] Implement `src/data/impute.py` for spatial interpolation of missing climate data.
 - **Input**: Read from `data/raw/climate.parquet` (DataFrame with columns: lat, lon, temp, week, precip).
 - **Logic**: Use `scipy.interpolate.griddata` with a 1° radius neighbor search in **degrees** (lat/lon).
 - **Output**: Write imputed data to `data/interim/climate_imputed.parquet` and update metadata with flagged cells.
- [ ] T008 [P] Setup `src/models/utils.py` with statistical helpers (Benjamini-Hochberg FDR, bootstrapping logic, early stopping for permutations)
- [X] T009 Create base data entities: `MigrationRecord`, `PhenologyMetric`, `ClimateVariable` classes in `src/models/entities.py`
- [~] T010 [P] Configure logging infrastructure to record "insufficient data" events and model convergence failures.
 - **Artifact**: Create `logs/pipeline.log`.
 - **Policy**: Max 5 files, 10MB each, rotate on size.
 - **Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.
- [~] T011 [P] Setup environment configuration management for random seeds and sampling parameters.
 - **Artifact**: Create `src/lib/config.py`.
 - **Variables**: Define `SEED=42`, `GRID_RES=0.5` (linked to T015 grid assignment), `SAMPLE_SIZE`, `PERMUTATIONS=10000`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eBird/NOAA (or synthetic) data, filter to migratory species (recent years), aggregate to coarse grid cells, and compute phenology metrics.

**Independent Test**: The pipeline can be fully tested by running `src/data/preprocess.py` on a subset (one species, one region) and verifying the output CSV contains expected columns (`species`, `grid_cell`, `week`, `phenology_metric`, `climate_temp`, `climate_precip`) with no missing values in critical fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T013 [P] [US1] Add `tests/integration/test_data_pipeline.py` with function `test_data_ingestion_flow` verifying end-to-end flow (TDD: write before T014)

### Implementation for User Story 1

- [~] T014 [P] [US1] Call the download functions from T005 in `src/data/preprocess.py` to ensure data is available before processing; verify file presence and checksums
- [ ] T015 [P] [US1] Implement `src/data/preprocess.py` to filter eBird records to migratory species using CLO list and aggregate to weekly counts per 0.5° × 0.5° grid cell (Use `GRID_RES=0.5` from T011 config)
- [ ] T017 [US1] Implement phenology metric computation (`first_arrival`, `median_arrival`, `stopover_duration`) in `src/data/preprocess.py`
- [~] T018 [US1] Add logic to mark grid cells as "insufficient data" when observation density is too low, excluding them from downstream modeling (Depends on **completion** of T007 - file creation, not just module import)
- [ ] T019 [P] [US1] Add observer effort covariates calculation to `src/data/preprocess.py` to control for sampling bias (per Plan Complexity Tracking)
- [ ] T019b [P] [US1] Implement **Tail-Preserving Stratified Sampling** (FR-002-S) in `src/data/preprocess.py`:
 1. Quantile-bin `first_arrival` into deciles.
 2. Oversample cells in the lowest decile by a moderate factor.
 3. Assign inverse-probability weights (`weight = 0.5` for oversampled, `1.0` otherwise).
 4. Output weights to `data/interim/sampling_weights.parquet`.
- [X] T020 [S] [US1] Integrate `src/data/impute.py` (from T007) to fill missing climate values via spatial interpolation and flag imputed cells in metadata (Note: **Sequential** - depends on T007 completion, NOT parallel-safe)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Phenology-Climate Correlation Modeling (Priority: P2)

**Goal**: Fit Generalized Additive Mixed Models (GAMMs) with conditional spatial correction, compute p-values with FDR correction, and handle convergence failures.

**Independent Test**: The modeling step can be tested by running `src/models/gamm_fit.py` on a synthetic dataset with known correlation parameters and verifying output includes coefficient estimates and fit statistics matching known parameters within 5% tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Add `tests/contract/test_output_schemas.py` with function `test_gamm_output_schema` verifying coefficient and p-value columns
- [X] T022 [P] [US2] Add `tests/integration/test_modeling.py` with function `test_gamm_convergence` verifying fit on synthetic data

### Implementation for User Story 2

- [X] T023 [P] [US2] Implement `src/models/gamm_fit.py` to fit a **Unified Spatial Model**.
 - **Model**: `phenology_metric ~ s(temp) + s(precip) + s(effort) + (1 + temp | species) + GP_spatial(lon, lat; kernel=Matérn(nu=1.5))`.
 - **Requirement**: The Gaussian Process (GP) **MUST ALWAYS be applied** (per Plan Phase 3).
 - **Diagnostic**: Compute Moran's I on residuals and log it, but do NOT use it to conditionally skip the GP. The implementation must follow the Plan's "Unified Spatial Model" regardless of the Spec's conditional wording.
- [X] T024 [US2] Implement species-year random intercepts and slopes logic in `src/models/gamm_fit.py`
- [ ] T025 [US2] Implement permutation test in `src/models/utils.py` with `n_shuffles=10000`.
 - **Logic**: Run 100 shuffles, check interim p < 0.001, set `early_stop_flag=True`, but **CONTINUE** to full [deferred] shuffles. The flag is for reporting only; the full [deferred] shuffles MUST complete.
 - **Optimization**: Use `joblib` parallelization to ensure full shuffles complete within the 5.5h CI budget.
 - **Output**: Write to `data/processed/permutation_results.json` with schema: `{ "species": str, "coefficient": str, "p_value": float, "n_shuffles": int, "early_stop_flag": bool, "final_p_value": float }`.
- [ ] T026 [US2] Apply Benjamini–Hochberg FDR correction to all species-climate coefficients in `src/models/utils.py`
- [ ] T027 [US2] Add error handling in `src/models/gamm_fit.py` to log convergence failures (collinearity) and skip affected species without halting pipeline

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Route Shift Analysis and Uncertainty Quantification (Priority: P3)

**Goal**: Represent weekly migration centroids as trajectories, detect spatial route shifts using geodesic distances, and generate bootstrapped uncertainty intervals.

**Independent Test**: The route analysis can be tested by running `src/models/trajectory.py` on a synthetic dataset with randomized labels and verifying the permutation test correctly identifies no significant shift (p > 0.05) in the absence of true signal.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Add `tests/contract/test_trajectory_schemas.py` with function `test_trajectory_output_schema`
- [ ] T029 [P] [US3] Add `tests/integration/test_trajectory_analysis.py` with function `test_route_shift_detection`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `src/models/trajectory.py` to compute weekly migration centroids per species-year
- [ ] T031 [US3] Implement trajectory analysis using **Riemannian manifold** statistics via the `geomstats` library (Spec FR-006, US-3).
 - Calculate shift vectors (magnitude/direction) based on centroid displacement on the manifold.
 - Do NOT use standard geodesic distances as a substitute.
- [ ] T032 [US3] Implement permutation test in `src/models/trajectory_utils.py` with `n_shuffles=10000` (as per US-3) to generate null distribution of shift magnitudes.
 - **Function Name**: `run_trajectory_permutation_test` (distinct from T025's GAMM function to avoid shared state).
 - **Logic**: Run 100 shuffles, check interim p < 0.001, set `early_stop_flag=True`, but **CONTINUE** to full [deferred] shuffles. The flag is for reporting only; the full [deferred] shuffles MUST complete.
 - **Optimization**: Use `joblib` parallelization to ensure full shuffles complete within the 5.5h CI budget.
 - **Output**: Write to `data/processed/trajectory_permutation_results.json` with schema: `{ "species": str, "shift_magnitude": float, "p_value": float, "n_shuffles": int, "early_stop_flag": bool, "final_p_value": float }`.
- [ ] T033 [US3] Implement bootstrapped confidence interval generation for phenology shift predictions in `src/models/utils.py`
- [ ] T034 [US3] Integrate uncertainty quantification with model predictions to output confidence interval widths

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `README.md` with installation instructions and `python run_pipeline.py --help` output
- [ ] T037 [P] Create `docs/api.md` with docstrings for `src/data/preprocess.py` functions
- [ ] T038a [P] Execute `ruff check src/ --fix` to remove unused imports and fix all linting errors automatically.
- [ ] T038b [P] Verify docstring compliance: Run `ruff check src/ --select=D100,D101,D102` to ensure module/function docstrings exist, then manually verify that all public functions follow Google-style formatting.
- [ ] T039a [P] Vectorize pandas operations in `src/data/preprocess.py` to reduce loop overhead
- [ ] T039b [P] Implement `joblib` parallelization for permutation tests in `src/models/utils.py` to utilize multiple CPU cores
- [ ] T040 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T041 [P] Add `.github/workflows/ci.yml` job `validate_quickstart` that runs `python -m pytest tests/integration/test_quickstart.py` and asserts runtime < 4h

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Integration test for data ingestion flow in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/preprocess.py to filter eBird records"
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
- [S] tasks = Sequential (must wait for predecessor completion)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence