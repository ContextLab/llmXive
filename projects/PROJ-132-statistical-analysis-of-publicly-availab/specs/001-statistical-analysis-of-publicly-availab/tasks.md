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
- [ ] T002 Create `requirements.txt` at repository root containing pinned versions: `pandas==2.1.0`, `numpy==1.24.0`, `scipy==1.11.0`, `statsmodels==0.14.0`, `geopandas==0.13.0`, `scikit-learn==1.3.0`, `requests==2.31.0`, `tqdm==4.66.0`, `geomstats==2.5.0`, `joblib==1.3.0`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Create empty `src/data/download.py` file at repository root
- [ ] T005 [P] Implement `src/data/download.py` to generate `data/raw/synthetic_ebird.csv` matching `contracts/dataset.schema.yaml` columns [species, lat, lon, date, count, checklist_id] when no real data exists; include gating mechanism to switch to real data fetcher upon availability (per Constitution VI)
- [ ] T006 [P] Add `tests/contract/test_schemas.py::test_ebird_schema_columns` asserting `df.columns` equals [species, lat, lon, date, count, checklist_id] and `df.dtypes` match expected types (TDD: Write before implementation)
- [ ] T007 [P] Implement `src/data/impute.py` for spatial interpolation of missing climate data (1° radius neighbor search)
- [ ] T008 [P] Setup `src/models/utils.py` with statistical helpers (Benjamini-Hochberg FDR, bootstrapping logic, early stopping for permutations)
- [ ] T009 Create base data entities: `MigrationRecord`, `PhenologyMetric`, `ClimateVariable` classes in `src/models/entities.py`
- [ ] T010 Configure logging infrastructure to record "insufficient data" events and model convergence failures
- [ ] T011 Setup environment configuration management for random seeds and sampling parameters

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eBird/NOAA (or synthetic) data, filter to migratory species (2020–2024), aggregate to 0.5° grid cells, and compute phenology metrics with tail-preserving sampling.

**Independent Test**: The pipeline can be fully tested by running `src/data/preprocess.py` on a subset (one species, one region) and verifying the output CSV contains expected columns (`species`, `grid_cell`, `week`, `phenology_metric`, `climate_temp`, `climate_precip`) with no missing values in critical fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (TDD), ensure they FAIL before implementation. Marked [P] for parallel execution against each other, but must precede implementation tasks.**

- [ ] T012 [P] [US1] Add `tests/contract/test_schemas.py::test_ebird_schema_columns` asserting `df.columns` equals [species, lat, lon, date, count, checklist_id] and `df.dtypes` match expected types (TDD: write before T013)
- [ ] T013 [P] [US1] Add `tests/integration/test_data_pipeline.py` with function `test_data_ingestion_flow` verifying end-to-end flow (TDD: write before T014)

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `src/data/download.py` to generate synthetic data using `numpy.random` with seed 42, producing [deferred] rows with columns [species, lat, lon, date, count, checklist_id] if `data/raw/` is empty; include gating mechanism to switch to real data fetcher when available
- [ ] T015 [P] [US1] Implement `src/data/preprocess.py` to filter eBird records to migratory species using CLO list and aggregate to weekly counts per 0.5° × 0.5° grid cell
- [ ] T016 [US1] Implement tail-preserving stratified sampling logic in `src/data/preprocess.py::stratify_cells`: stratify by observation density, create quantile-based bins on `first_arrival_date`, and apply oversampling factor of 2.0 for the bottom [deferred] quantile (per Plan Complexity Tracking)
- [ ] T017 [US1] Implement phenology metric computation (`first_arrival`, `median_arrival`, `stopover_duration`) in `src/data/preprocess.py`
- [ ] T018 [US1] Add logic to mark grid cells as "insufficient data" when observation density is too low, excluding them from downstream modeling (depends on T007 module existence, not execution order)
- [ ] T019 [US1] Add observer effort covariates calculation to `src/data/preprocess.py` to control for sampling bias (per Plan Complexity Tracking)
- [ ] T020 [US1] Integrate `src/data/impute.py` (from T007) to fill missing climate values via spatial interpolation and flag imputed cells in metadata (Note: depends on T007, not parallel-safe)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Phenology-Climate Correlation Modeling (Priority: P2)

**Goal**: Fit Generalized Additive Mixed Models (GAMMs) with Unified Spatial Model, compute p-values with FDR correction, and handle convergence failures.

**Independent Test**: The modeling step can be tested by running `src/models/gamm_fit.py` on a synthetic dataset with known correlation parameters and verifying output includes coefficient estimates and fit statistics matching known parameters within 5% tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Add `tests/contract/test_output_schemas.py` with function `test_gamm_output_schema` verifying coefficient and p-value columns
- [ ] T022 [P] [US2] Add `tests/integration/test_modeling.py` with function `test_gamm_convergence` verifying fit on synthetic data

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `src/models/gamm_fit.py` to fit GAMMs with phenology metrics as responses, climate variables as smooth fixed effects, AND Unified Spatial Model (default spatial smooth) to handle spatial autocorrelation without data snooping (per Plan CI Feasibility Strategy)
- [ ] T024 [US2] Implement species-year random intercepts and slopes logic in `src/models/gamm_fit.py` (Unified Spatial Model is the primary spatial approach; no conditional GP fallback)
- [ ] T025 [US2] Implement permutation test in `src/models/utils.py` with `n_shuffles=1000` (reduced from spec's [deferred]), early stopping if p-value < 0.001 after 100 shuffles, max runtime 1800s (per Plan CI Feasibility Strategy)
- [ ] T026 [US2] Apply Benjamini–Hochberg FDR correction to all species-climate coefficients in `src/models/utils.py`
- [ ] T027 [US2] Add error handling in `src/models/gamm_fit.py` to log convergence failures (collinearity) and skip affected species without halting pipeline

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Route Shift Analysis and Uncertainty Quantification (Priority: P3)

**Goal**: Represent weekly migration centroids as trajectories on a Riemannian manifold, detect spatial route shifts, and generate bootstrapped uncertainty intervals.

**Independent Test**: The route analysis can be tested by running `src/models/trajectory.py` on a synthetic dataset with randomized labels and verifying the permutation test correctly identifies no significant shift (p > 0.05) in the absence of true signal.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Add `tests/contract/test_trajectory_schemas.py` with function `test_trajectory_output_schema`
- [ ] T029 [P] [US3] Add `tests/integration/test_trajectory_analysis.py` with function `test_riemannian_shift_detection`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `src/models/trajectory.py` to compute weekly migration centroids per species-year
- [ ] T031 [US3] Implement Riemannian manifold representation using `geomstats` in `src/models/trajectory.py` for trajectory analysis
- [ ] T032 [US3] Implement manifold-based trajectory statistics to detect spatial route shifts and calculate shift vectors (magnitude/direction)
- [ ] T033 [US3] Implement permutation test in `src/models/utils.py` with `n_shuffles=1000` (reduced from spec's [deferred]), early stopping if p-value < 0.001 after 100 shuffles, max runtime 1800s for route shift significance
- [ ] T034 [US3] Implement bootstrapped confidence interval generation for phenology shift predictions in `src/models/utils.py`
- [ ] T035 [US3] Integrate uncertainty quantification with model predictions to output confidence interval widths

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `README.md` with installation instructions and `python run_pipeline.py --help` output
- [ ] T037 [P] Create `docs/api.md` with docstrings for `src/data/preprocess.py` functions
- [ ] T038 Code cleanup and refactoring of `src/` modules
- [ ] T039 Performance optimization for CPU-only execution (vectorization, joblib parallelization)
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
Task: "Contract test for data schema in tests/contract/test_schemas.py"
Task: "Integration test for data ingestion flow in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/download.py to fetch eBird Basic Dataset"
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
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence