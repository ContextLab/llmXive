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
- [X] T003a Create `pyproject.toml` at repository root with `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (lint.select=['E','F','W','I'], lint.ignore=[]) configuration sections
- [ ] T003b Create `.pre-commit-config.yaml` with hooks for `black` and `ruff` and configure pre-commit installation instructions in `README.md`
- [X] T004 Create empty `src/data/download.py` file at repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes runtime optimization to meet SC-005.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `src/data/download.py` to:
 1. Check for real eBird/NOAA files in `data/raw/ebird/` and `data/raw/climate/`.
 2. **Production Mode (DEFAULT)**: If real data is missing, ABORT with exit code 1 and error message "Real data required for production run. Set --mode=synthetic for development only."
 3. **Development Mode**: Triggered ONLY by CLI flag `--mode=synthetic`. If real data is missing AND flag is present, generate synthetic data using `numpy.random` with seed 42, writing `data/raw/synthetic_ebird.csv` and `data/raw/synthetic_climate.parquet` matching `contracts/dataset.schema.yaml`. The synthetic data MUST preserve 'natural phenology' distribution patterns (matching mean/variance of real data) to avoid bias.
 4. **CONSTRAINT**: If `CI=true` environment variable is set, synthetic mode is FORBIDDEN. The script MUST abort if `--mode=synthetic` is passed in CI.
 5. Archive real files unchanged (copy to `data/raw/archive/`) and compute SHA-256 checksums.
 6. Write checksums to `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml` under keys `artifact_hashes` and `updated_at`.
- [X] T006 [P] Add `tests/contract/test_schemas.py::test_ebird_schema_columns` asserting `df.columns` equals [species, lat, lon, date, count, checklist_id] and `df.dtypes` match expected types (TDD: Write before implementation)
- [X] T007 Implement `src/data/impute.py` for spatial interpolation of missing climate data.
 - **Input**: Read from `data/raw/climate.parquet` (DataFrame with columns: lat, lon, temp, week, precip).
 - **Logic**: Use `scipy.interpolate.griddata` with a 1° radius neighbor search in **degrees** (lat/lon).
 - **Output**: Write imputed data to `data/interim/climate_imputed.parquet` and update metadata with flagged cells.
- [X] T009 Create base data entities: `MigrationRecord`, `PhenologyMetric`, `ClimateVariable` classes in `src/models/entities.py`
- [ ] T010a [P] [Foundation] Create logging configuration file `logging.conf` with file rotation policy.
 - **Policy**: Max 5 files, 10MB each.
 - **Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.
- [ ] T010b [P] [Foundation] Implement rotation logic in `src/lib/config.py` using `logging.handlers.RotatingFileHandler`.
- [ ] T010c [P] [Foundation] Verify log format by writing a test log entry and parsing it.
- [ ] T011a [P] [Foundation] Create `src/lib/config.py` file.
- [ ] T011b [P] [Foundation] Define and export specific constants: `SEED=42`, `GRID_RES=0.5`, `SAMPLE_SIZE`, `PERMUTATIONS=10000`.
- [ ] T016 [P] [US1] Implement **Tail-Preserving Stratified Sampling** (FR-002-S) in `src/data/preprocess.py`.
 - **Logic**:
 1. Quantile-bin `first_arrival` into deciles.
 2. Oversample cells in the lowest [deferred] decile by a moderate factor.
 3. Assign inverse-probability weights (`weight = 0.5` for oversampled cells, `1.0` otherwise).
 4. Weights are passed to the GAMM via `sample_weight`.
 - **⚠️ PLAN MISMATCH**: This task implements a Plan requirement not authorized by Spec. Flagged for Spec update.
 - **Artifact**: Output dataset includes `weight` column.
- [ ] T018 [S] [US1] Add logic to mark grid cells as "insufficient data" when observation density is too low (< 5 observations per Plan Phase 2), **EXCLUDING** them from downstream modeling. **Depends on T015**.
 - **Logic**: If count < 5, set `data_quality="insufficient"` and filter out rows before modeling.
 - **Artifact**: Log species, grid cell, and reason to `logs/pipeline.log`. Write metadata to `data/processed/metadata_insufficient_cells.json`.
 - **Dependency**: Must be completed before T023, T025, T032.
- [ ] T019 [P] [US1] Add observer effort covariates calculation to `src/data/preprocess.py` to control for sampling bias (per Plan Complexity Tracking)
- [ ] T020 [S] [US1] Integrate `src/data/impute.py` (from T007) to fill missing climate values via spatial interpolation and flag imputed cells in metadata. **Depends on T007**.
 - **Logic**: Impute missing climate values.
 - **Output**: Update `data/processed/climate_data.parquet` with `imputed_flag` column.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eBird/NOAA (or synthetic) data, filter to migratory species (recent years), aggregate to coarse grid cells, and compute phenology metrics.

**Independent Test**: The pipeline can be fully tested by running `src/data/preprocess.py` on a subset (one species, one region) and verifying the output CSV contains expected columns (`species`, `grid_cell`, `week`, `phenology_metric`, `climate_temp`, `climate_precip`) with no missing values in critical fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T013 [P] [US1] Add `tests/integration/test_data_pipeline.py` with function `test_data_ingestion_flow` verifying end-to-end flow (TDD: write before T014)

### Implementation for User Story 1

- [X] T014 [P] [US1] Call the download functions from T005 in `src/data/preprocess.py` to ensure data is available before processing; verify file presence and checksums. **Depends on T005**.
- [X] T015 [P] [US1] Implement `src/data/preprocess.py` to filter eBird records to migratory species using CLO list and aggregate to weekly counts per 0.5° × 0.5° grid cell (Use `GRID_RES=0.5` from T011 config)
- [X] T017a [US1] Implement phenology metric computation (`first_arrival`, `median_arrival`, `stopover_duration`) in `src/data/preprocess.py`
- [X] T017b [US1] Implement **seasonal climate average calculation** (March–May temperature, precipitation) in `src/data/preprocess.py` to satisfy **FR-003**.
 - **Logic**: Compute mean temperature and total precipitation for the March–May period per grid cell and year.
 - **Output**: Append `climate_temp_avg`, `climate_precip_total` to the output dataset.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Phenology-Climate Correlation Modeling (Priority: P2)

**Goal**: Fit Generalized Additive Mixed Models (GAMMs) with conditional spatial correction, compute p-values with FDR correction, and handle convergence failures.

**Independent Test**: The modeling step can be tested by running `src/models/gamm_fit.py` on a synthetic dataset with known correlation parameters and verifying output includes coefficient estimates and fit statistics matching known parameters within 5% tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Add `tests/contract/test_output_schemas.py` with function `test_gamm_output_schema` verifying coefficient and p-value columns
- [X] T022 [P] [US2] Add `tests/integration/test_modeling.py` with function `test_gamm_convergence` verifying fit on synthetic data

### Implementation for User Story 2

- [X] T023 [S] [US2] Implement `src/models/gamm_fit.py` to fit a **Conditional Spatial Model** per Spec FR-004.
 - **Model**: `phenology_metric ~ s(temp) + s(precip) + s(effort) + (1 + temp | species)`.
 - **Logic**:
 1. Fit base model.
 2. Compute Moran's I on residuals.
 3. **IF** Moran's I > 0.15: Re-fit with a Gaussian Process (GP) random effect using a Matérn kernel (nu=1.5).
 4. **ELSE**: Proceed with the base model (diagnostic satisfied).
 5. **LOG**: Record Moran's I value and whether GP was applied.
 6. **CONSTRAINT**: Follow Spec FR-004. Override Plan Phase 3 ("Unified Model") if conflict exists.
 - **Output**: Write results to `data/processed/model_results.parquet` including `moran_i`, `gp_applied` (bool), coefficients, p-values.
 - **Dependency**: Depends on T015, T016, T018, T020.
- [X] T024 [US2] Implement species-year random intercepts and slopes logic in `src/models/gamm_fit.py`
- [X] T025 [S] [US2] Implement permutation test in `src/models/utils.py` with `n_shuffles=config.PERMUTATIONS` (defaulting to a sufficiently large number of shuffles to ensure statistical robustness).
 - **Logic**: Run 100 shuffles, write interim results to `data/interim/permutation_interim.json`, check interim p < 0.001, set `early_stop_flag=True`, but **CONTINUE** to full 10000 shuffles. The flag is for reporting only; the full 10000 shuffles MUST complete.
 - **Optimization**: Use `joblib` parallelization with `n_jobs=1` and `batch_size=100` to ensure full shuffles complete within the CI budget (relying on T042 optimizations).
 - **Output**: Write to `data/processed/permutation_results.json` with schema: `{ "species": str, "coefficient": str, "p_value": float, "n_shuffles": int, "early_stop_flag": bool, "final_p_value": float }`.
 - **Dependency**: Depends on T023.
- [X] T026a [US2] Implement Benjamini-Hochberg FDR correction function in `src/models/utils.py`.
 - **Input**: List of p-values from T025 results.
 - **Output**: List of adjusted p-values.
 - **Dependency**: Depends on T025.
- [X] T026b [US2] Apply FDR correction to all species-climate coefficients in `src/models/utils.py` and write to `data/processed/model_results_fdr.parquet`.
 - **Logic**: Apply the function from T026a to the p-values generated in T025.
 - **Output**: Updated results file with `q_value` column.
 - **Dependency**: Depends on T026a.
- [X] T027a [US2] Implement try/except block in `src/models/gamm_fit.py` to catch convergence failures.
- [X] T027b [US2] Define log message format for convergence failures in `src/models/gamm_fit.py`.
 - **Format**: "Convergence failed for species {species}: {error}".
- [X] T027c [US2] Verify log output for convergence failures in `tests/unit/test_models.py`.
 - **Test**: Assert log contains expected message format.
- [X] T042 [S] [Foundation] **Runtime Optimization**: Profile and implement chunked I/O and vectorization to ensure pipeline meets SC-005 (< 4h runtime).
 - **Artifact**: Implement chunked reading in `src/data/preprocess.py` and `src/models/gamm_fit.py`.
 - **Logic**: Use `pandas.read_csv(..., chunksize=...)` for large files. Vectorize all `apply` loops in preprocessing.
 - **Benchmark**: Measure time on a synthetic dataset of substantial scale.; target < 4h total.
 - **Dependency**: Depends on T023, T015. (Refinement task after implementation).

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
- [ ] T031 [US3] Implement trajectory analysis using **Riemannian manifold statistics** on the 2-sphere (S^2) via `scipy` and `geopy`.
 - **Algorithm**: Implement Fréchet mean via iterative gradient descent:
 1. Initialize mean as centroid.
 2. Compute gradients of squared geodesic distance on S².
 3. Update using exponential map: `mu_new = exp_mu(mu_old, -eta * gradient)`.
 4. Repeat until convergence (delta < 1e-6 or max 100 iterations).
 - **Constraint**: Do NOT use `geomstats`. Use `scipy.spatial` and `geopy.distance.geodesic` to implement the manifold metric.
 - **Output**: Write `shift_magnitude` and `shift_direction` to `data/processed/trajectory_results.json`.
- [ ] T032 [S] [US3] Implement permutation test in `src/models/trajectory_utils.py` with `n_shuffles=config.PERMUTATIONS` (default 10000) (as per US-3) to generate null distribution of shift magnitudes.
 - **Function Name**: `run_trajectory_permutation_test` (distinct from T025's GAMM function to avoid shared state).
 - **Logic**: Run 100 shuffles, check interim p < 0.001, set `early_stop_flag=True`, but **CONTINUE** to full 10000 shuffles. The flag is for reporting only; the full 10000 shuffles MUST complete.
 - **Optimization**: Use `joblib` parallelization with `n_jobs=1` and `batch_size=100` to ensure full shuffles complete within the 4h CI budget.
 - **Output**: Write to `data/processed/trajectory_permutation_results.json` with schema: `{ "species": str, "shift_magnitude": float, "p_value": float, "n_shuffles": int, "early_stop_flag": bool, "final_p_value": float }`.
 - **Dependency**: Depends on T030, T031.
- [ ] T033a [US3] Implement bootstrapped confidence interval generation for **phenology shift predictions** in `src/models/utils.py`.
 - **Logic**: Resample the centroid estimation process to generate confidence intervals.
 - **Output**: Append `ci_lower`, `ci_upper` to the trajectory results file.
- [ ] T033b [US3] Implement bootstrapped confidence interval generation for **trajectory shift magnitudes** in `src/models/utils.py`.
 - **Logic**: Resample the trajectory shift magnitude from T032.
 - **Output**: Append `ci_lower`, `ci_upper` to the trajectory results file.
 - **Note**: This is an enhancement beyond FR-007.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Orchestration & Validation (SC-002, SC-003, SC-005)

**Purpose**: Ensure sequential execution of heavy tasks and validate success criteria.

- [ ] T045 [S] **Orchestration**: Implement a file-based lock or sequential runner to serialize T025 and T032.
 - **Logic**: Ensure T025 and T032 do not run concurrently. T025 runs, completes, then T032 runs.
 - **Output**: Log execution order and total time for these two tasks.
 - **Dependency**: T025 and T032 depend on this task for execution order, but T045 depends on T025 and T032 completion.
- [ ] T043 [US1] Calculate SC-002: Proportion of "insufficient data" cells.
 - **Logic**: Count cells marked "insufficient" / Total cells.
 - **Output**: Log ratio. (Target is deferred, but metric must be calculated).
- [ ] T044 [US2] Calculate SC-003: GAMM Convergence Rate.
 - **Logic**: Count successful fits / Total attempts.
 - **Output**: Log ratio. (Target is deferred, but metric must be calculated).
- [ ] T046 [S] [US1] Implement **Sensitivity Analysis Loop** per Plan Phase 2.
 - **Logic**: Re-run the pipeline with varying thresholds to assess bias.
 - **Output**: Compare results and log bias assessment.
 - **Dependency**: Depends on T018.
- [ ] T050 [S] [Plan] **Reconcile Plan with Spec**.
 - **Action**: Update `plan.md` to align with `spec.md` regarding FR-002-S (Sampling) and Unified Model (GP).
 - **Output**: Document changes required in `docs/plan_reconciliation.md`.
 - **Dependency**: Depends on all implementation tasks.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `README.md` with installation instructions and `python run_pipeline.py --help` output
- [ ] T037 [P] Create `docs/api.md` with docstrings for `src/data/preprocess.py` functions
- [ ] T038a [P] Execute `ruff check src/ --fix` to remove unused imports and fix all linting errors automatically.
- [ ] T038b [P] Verify docstring compliance: Run `ruff check src/ --select=D100,D101,D102` to ensure module/function docstrings exist, then manually verify that all public functions follow Google-style formatting.
- [ ] T039a1 [P] Vectorize pandas operations in `src/data/preprocess.py` to reduce loop overhead (Ensure T042 is complete first)
- [ ] T039a2 [P] Vectorize model operations in `src/models/gamm_fit.py` to reduce loop overhead (Ensure T042 is complete first)
- [ ] T039b1 [P] Implement `joblib` parallelization for permutation tests in `src/models/utils.py` to utilize multiple CPU cores (Ensure T042 is complete first)
- [ ] T039b2 [P] Implement `joblib` parallelization for other heavy tasks (Ensure T042 is complete first)
- [ ] T040a [P] Add unit test for empty input in `tests/unit/test_preprocess.py`.
- [ ] T040b [P] Add unit test for single species in `tests/unit/test_models.py`.
- [ ] T040c [P] Add unit test for missing data in `tests/unit/test_data.py`.
- [ ] T041a [P] Create `.github/workflows/ci.yml` file.
- [ ] T041b [P] Define `validate_quickstart` job in `.github/workflows/ci.yml`.
- [ ] T041c [P] Add runtime assertion (< 4h) to `validate_quickstart` job.

---

## Plan Mismatch Notice

**⚠️ CRITICAL**: The following items in `plan.md` contradict `spec.md` and are **NOT** implemented in this tasks file. **These mismatches block project advancement until the plan is reconciled with the spec.**

1. **FR-002-S (Tail-Preserving Stratified Sampling)**: `plan.md` Phase 2 mandates oversampling the lowest decile of arrival times. `spec.md` does not authorize this. **Task T016 implements this requirement, but the spec must be updated to authorize it.**
2. **Unified Spatial Model (GP Always)**: `plan.md` Phase 3 mandates a GP random effect regardless of Moran's I. `spec.md` FR-004/FR-005 requires conditional GP application. **T023 implements the conditional logic per spec, overriding the plan.**
3. **Runtime Budget**: `plan.md` estimates 5.5h, but `spec.md` SC-005 and CI constraint require < 4h. **T042 is added to optimize for 4h, overriding the plan's 5.5h estimate.**

**Action Required**: `plan.md` must be updated to align with `spec.md` before this project can advance.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Orchestration (Phase 6)**: Depends on US2 and US3 implementation
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

## Global Execution Constraint

**⚠️ IMPORTANT**: Tasks T025 (US2 permutation test) and T032 (US3 permutation test) both require significant CPU resources. They MUST be serialized via **T045** (Orchestration) to ensure they do not run concurrently and exceed the 2-core CI limit.

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