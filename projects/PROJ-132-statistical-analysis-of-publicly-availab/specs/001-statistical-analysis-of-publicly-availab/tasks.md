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
 2. **Real Data Mode**: If real data is missing, check for `DATA_PATH` environment variable. If present, use it as the source. If absent, ABORT with exit code 1 and error message "Real data required. Set DATA_PATH or provide real files in data/raw/".
 3. **CONSTRAINT**: Remove all synthetic data generation logic. No fallback to `numpy.random`.
 4. Archive real files unchanged (copy to `data/raw/archive/`) and compute SHA-256 checksums.
 5. Write checksums to `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml` under keys `artifact_hashes` and `updated_at`.
- [X] T006 [P] Add `tests/contract/test_schemas.py::test_ebird_schema_columns` asserting `df.columns` equals [species, lat, lon, date, count, checklist_id] and `df.dtypes` match expected types (TDD: Write before implementation)
- [X] T007 Implement `src/data/impute.py` for spatial interpolation of missing climate data.
 - **Input**: Read from `data/raw/climate.parquet` (DataFrame with columns: lat, lon, temp, week, precip).
 - **Logic**: Use `scipy.interpolate.griddata` with a neighbor search in **degrees** (lat/lon) at an appropriate spatial scale.
 - **Output**: Write imputed data to `data/interim/climate_imputed.parquet` and update metadata with flagged cells.
- [X] T009 Create base data entities: `MigrationRecord`, `PhenologyMetric`, `ClimateVariable` classes in `src/models/entities.py`
- [X] T010 [P] [Foundation] **Configure Logging and Constants**: Create `src/lib/config.py` file.
 - **Constants**: Define and export `SEED=42`, `GRID_RES=0.5`, `SAMPLE_SIZE=1000`, `PERMUTATIONS=10000`.
 - **Logging**: Implement logging configuration with format `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.
 - **Rotation Policy**: Max files, 10MB each.
 - **Verification**: Write a test log entry and parse it to ensure format compliance.
 - **Note**: This consolidates logging setup and constant definition into a single artifact to prevent ordering conflicts.
- [X] T018 [S] [US1] **Mark Insufficient Data Cells**: Implement `src/data/preprocess.py::mark_insufficient_cells`.
 - **Logic**: Scan aggregated grid cells. If count < 5, set `data_quality="insufficient"` and exclude from downstream modeling.
 - **Artifact**: Log species, grid cell, and reason to `logs/pipeline.log`. Write metadata to `data/processed/metadata_insufficient_cells.json`.
 - **Dependency**: Must be completed before T015, T023, T032.
- [X] T019 [P] [US1] Add observer effort covariates calculation to `src/data/preprocess.py` to control for sampling bias (per Plan Complexity Tracking)
- [X] T020 [S] [US1] Integrate `src/data/impute.py` (from T007) to fill missing climate values via spatial interpolation and flag imputed cells in metadata. **Depends on T007**.
 - **Logic**: Impute missing climate values.
 - **Output**: Update `data/processed/climate_data.parquet` with `imputed_flag` column.
- [X] T047 [S] [Foundation] **Define Success Criteria Thresholds**: Define concrete values for SC-001 to SC-004 in `src/lib/config.py`.
 - **Values**: `POWER_TARGET=0.80`, `CI_WIDTH_TARGET=5.0` (days), `CONVERGENCE_TARGET=0.90`, `INSUFFICIENT_DATA_TARGET=0.20`.
 - **Action**: Update `config.py` with these constants. Do NOT edit spec.md or plan.md (scope violation).
 - **Dependency**: Must be completed before T023, T025, T032, T043, T044, T056.
- [X] T056 [S] [Foundation] **Power Analysis**: Create `src/analysis/power_analysis.py` to calculate the statistical power of the permutation tests.
 - **Action**: Implement a function that takes `SAMPLE_SIZE` and `POWER_TARGET` to estimate power, logging the result to `logs/power_analysis.log`.
 - **Requirement**: Justify [deferred] shuffles based on power analysis.
 - **Dependency**: Depends on T047.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eBird/NOAA (or synthetic) data, filter to migratory species (recent years), aggregate to coarse grid cells, and compute phenology metrics.

**Independent Test**: The pipeline can be fully tested by running `src/data/preprocess.py` on a subset (one species, one region) and verifying the output CSV contains expected columns (`species`, `grid_cell`, `week`, `phenology_metric`, `climate_temp`, `climate_precip`) with no missing values in critical fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T013 [P] [US1] Add `tests/integration/test_data_pipeline.py` with function `test_data_ingestion_flow` verifying end-to-end flow (TDD: write before T014)

### Implementation for User Story 1

- [X] T014 [P] [US1] Call the download functions from T005 in `src/data/preprocess.py` to ensure data is available before processing; verify file presence and checksums. **Depends on T005**.
- [X] T015 [P] [US1] Implement `src/data/preprocess.py` to filter eBird records to migratory species using CLO list and aggregate to weekly counts per spatial grid cell (Use `GRID_RES=0.5` from T011 config). **Depends on T018**.
 - **Logic**: Call `mark_insufficient_cells` (T018) before final aggregation to ensure invalid cells are excluded.
- [X] T017a [US1] Implement phenology metric computation (`first_arrival`, `median_arrival`, `stopover_duration`) in `src/data/preprocess.py`.
 - **Logic**: `stopover_duration` = High percentile DOY - Low percentile DOY.
- [X] T017b [US1] Implement **seasonal climate average calculation** (March–May temperature, precipitation) in `src/data/preprocess.py` to satisfy **FR-003**.
 - **Logic**: Compute mean temperature and total precipitation for the March–May period per grid cell and year.
 - **Output**: Append `climate_temp_avg`, `climate_precip_total` to the output dataset.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Phenology-Climate Correlation Modeling (Priority: P2)

**Goal**: Fit Generalized Additive Mixed Models (GAMMs) with conditional spatial correction, compute p-values with FDR correction, and handle convergence failures.

**Independent Test**: The modeling step can be tested by running `src/models/gamm_fit.py` on a synthetic dataset with known correlation parameters and verifying output includes coefficient estimates and fit statistics matching known parameters within % tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Add `tests/contract/test_output_schemas.py` with function `test_gamm_output_schema` verifying coefficient and p-value columns
- [X] T022 [P] [US2] Add `tests/integration/test_modeling.py` with function `test_gamm_convergence` verifying fit on synthetic data

### Implementation for User Story 2

- [X] T023 [S] [US2] Implement `src/models/gamm_fit.py` to fit a **Conditional Spatial Model** per Spec FR-004. **Depends on T018, T047**.
 - **Model**: `phenology_metric ~ s(temp) + s(precip) + s(effort) + (1 + temp | species)`.
 - **Logic**:
 1. Fit base model.
 2. Compute Moran's I on residuals.
 3. **IF** Moran's I > 0.15: Re-fit with a Gaussian Process (GP) random effect using a Matérn kernel (nu=1.5).
 4. **ELSE**: Proceed with the base model (diagnostic satisfied).
 5. **LOG**: Record Moran's I value and whether GP was applied.
 6. **CONSTRAINT**: Follow Spec FR-004. Override Plan Phase 3 ("Unified Model") if conflict exists.
 - **Output**: Write results to `data/processed/model_results.parquet` including `moran_i`, `gp_applied` (bool), coefficients, p-values.
 - **Dependency**: Depends on T015, T018, T020, T042, T047.
- [X] T024 [US2] Implement species-year random intercepts and slopes logic in `src/models/gamm_fit.py`
- [X] T025 [S] [US2] Implement permutation test in `src/models/utils.py` with `n_shuffles=config.PERMUTATIONS` (a sufficiently large number of shuffles to ensure stable p-value estimation). **Depends on T045**.
 - **Logic**: Run A substantial number of shuffles, write interim results to `data/interim/permutation_interim.json`, check interim p < 0.001, set `early_stop_flag=True`, but **CONTINUE** to full 10000 shuffles. The flag is for reporting only; the full 10000 shuffles MUST complete.
 - **Optimization**: Use `joblib` parallelization with `n_jobs=1` and `batch_size=100` to ensure full shuffles complete within the CI budget (relying on T042 optimizations).
 - **Output**: Write to `data/processed/permutation_results.json` with schema: `{ "species": str, "coefficient": str, "p_value": float, "n_shuffles": int, "early_stop_flag": bool, "final_p_value": float }`.
 - **Dependency**: Depends on T023, T042, T047, T045.
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

- [X] T028 [P] [US3] Add `tests/contract/test_trajectory_schemas.py` with function `test_trajectory_output_schema`
- [X] T029 [P] [US3] Add `tests/integration/test_trajectory_analysis.py` with function `test_route_shift_detection`

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement `src/models/trajectory.py` to compute weekly migration centroids per species-year
- [X] T031 [US3] Implement trajectory analysis using **Riemannian manifold statistics** on the 2-sphere (S^2) via `scipy` and `geopy`. **Depends on T047**.
 - **Algorithm**: Implement Fréchet mean via iterative gradient descent:
 1. Initialize mean as centroid.
 2. Compute gradients of squared geodesic distance on S².
 3. Update using exponential map: `mu_new = exp_mu(mu_old, -eta * gradient)`.
 4. Repeat until convergence (delta < 1e-6 or a fixed, bounded number of iterations).
 - **Constraint**: Do NOT use `geomstats`. Use `scipy.spatial` and `geopy.distance.geodesic` to implement the manifold metric.
 - **Output**: Write `shift_magnitude` and `shift_direction` to `data/processed/trajectory_results.json`.
- [X] T032 [S] [US3] Implement permutation test in `src/models/trajectory_utils.py` with `n_shuffles=config.PERMUTATIONS` using a sufficiently large number of shuffles to ensure robust statistical significance. **Depends on T045**.
 - **Function Name**: `run_trajectory_permutation_test` (distinct from T025's GAMM function to avoid shared state).
 - **Logic**: Run 100 shuffles, check interim p < 0.001, set `early_stop_flag=True`, but **CONTINUE** to full 10000 shuffles. The flag is for reporting only; the full 10000 shuffles MUST complete.
 - **Optimization**: Use `joblib` parallelization with `n_jobs=1` and `batch_size=100` to ensure full shuffles complete within the CI budget.
 - **Output**: Write to `data/processed/trajectory_permutation_results.json` with schema: `{ "species": str, "shift_magnitude": float, "p_value": float, "n_shuffles": int, "early_stop_flag": bool, "final_p_value": float }`.
 - **Dependency**: Depends on T030, T031, T042, T047, T045.
- [X] T033 [US3] Implement bootstrapped confidence interval generation for **phenology shift predictions and trajectory shift magnitudes** in `src/models/utils.py`.
 - **Logic**: Resample the centroid estimation process and trajectory shift magnitudes to generate confidence intervals for both metrics.
 - **Output**: Append `ci_lower`, `ci_upper` to the trajectory results file.
 - **Note**: This task consolidates FR-007 requirements for both phenology and trajectory shifts.
 - **Dependency**: Depends on T032.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Orchestration & Validation (SC-002, SC-003, SC-005)

**Purpose**: Ensure sequential execution of heavy tasks and validate success criteria.

- [X] T045 [S] **Orchestration**: Implement a file-based lock mechanism to serialize T025 and T032. **Depends on T047**.
 - **Logic**: Use `filelock` library. Lock file path: `data/interim/pipeline.lock`. Timeout: A predefined duration.
 - **Output**: Log execution order.
 - **Dependency**: Depends on T042.
- [X] T046 [S] **Post-Run Validation**: Verify the lock mechanism worked and total runtime is within budget.
 - **Logic**: Run a benchmark of T025 and T032 sequentially (post-execution) to verify total time < 4h.
 - **Output**: Log total time and assertion result.
 - **Dependency**: Depends on T025, T032, T045.
- [X] T043 [US1] Calculate SC-002: Proportion of "insufficient data" cells.
 - **Logic**: Count cells marked "insufficient" / Total cells.
 - **Output**: Write to `data/processed/success_criteria_report.json`.
 - **Dependency**: Depends on T047.
- [X] T044 [US2] Calculate SC-003: GAMM Convergence Rate.
 - **Logic**: Count successful fits / Total attempts.
 - **Output**: Write to `data/processed/success_criteria_report.json`.
 - **Dependency**: Depends on T047.
- [X] T047 [S] **Define Success Criteria Thresholds**: Replace `[deferred]` placeholders in `src/lib/config.py` with concrete numeric values.
 - **Action**: Update `config.py` with `POWER_TARGET=0.80`, `CI_WIDTH_TARGET=5.0`, `CONVERGENCE_TARGET=0.90`, `INSUFFICIENT_DATA_TARGET=0.20`.
 - **Output**: Updated `config.py`.
 - **Dependency**: Must be completed before T023, T025, T032, T043, T044.
- [X] T050 [S] [Plan] **Reconcile Plan with Spec**.
 - **Action**: Update `plan.md` to remove "FR-002-S" (Tail-Preserving Stratified Sampling) and "Unified Spatial Model" (GP always) mandates. Align plan.md with Spec FR-004 (Conditional GP) and remove unverified sampling strategies.
 - **Output**: Corrected `plan.md` artifact.
 - **Dependency**: Depends on all implementation tasks.

---

## Phase 7: Revision & Analysis Resolution

**Purpose**: Address specific concerns raised by `/speckit.analyze` regarding data sourcing, model specification, and task ordering.

- [X] T051 [S] [US1] **Replace Synthetic Fallback with Real Data Streaming**: Update `src/data/download.py` to **remove** the `generate_synthetic_*` fallback path entirely.
 - **Action**: If real data (eBird/NOAA) is not found in `data/raw/`, the script MUST raise a `FileNotFoundError` and exit with code 1, UNLESS `DATA_PATH` env var is set (for CI reproducibility).
 - **Requirement**: Add a new function `stream_ebird_dataset` using `datasets.load_dataset("ebird", streaming=True)` to fetch real data in chunks if local files are missing, ensuring the pipeline never runs on fabricated data.
 - **Constraint**: This resolves the "Fabrication Gate" rejection risk by ensuring only real data flows into the pipeline.
 - **Dependency**: Replaces logic in T005.
- [X] T052 [S] [US1] **Implement Explicit Data Source Fetching**: Update `src/data/download.py` to use the verified HuggingFace `ebird` dataset ID.
 - **Action**: Replace any generic URL guessing with `load_dataset("ebird", split="train", streaming=True)`.
 - **Requirement**: Add a `try/except` block that catches network errors and re-tries 3 times, then raises `RuntimeError` with a clear message about verified source failure, rather than falling back to synthetic data.
 - **Dependency**: Depends on T051.
- [X] T053 [S] [US2] **Correct Model Specification per Spec FR-004**: Update `src/models/gamm_fit.py` to ensure the Gaussian Process (GP) is **conditional** on Moran's I > 0.15.
 - **Action**: Ensure the code explicitly checks `if moran_i > 0.15:` before instantiating the GP. If `moran_i <= 0.15`, the model must proceed without the GP term.
 - **Requirement**: This aligns the implementation strictly with `spec.md` FR-004 and overrides the `plan.md` "Unified Model" instruction.
 - **Dependency**: Refines T023.
- [X] T054 [S] [US3] **Refine Riemannian Manifold Implementation**: Update `src/models/trajectory.py` to correctly compute the Fréchet mean on the 2-sphere.
 - **Action**: Ensure the gradient descent step uses the correct exponential map for S² (great circle navigation).
 - **Requirement**: Verify that the `geopy.distance.geodesic` function is used for distance calculation, and that the iterative update respects the manifold constraint (norm=1).
 - **Dependency**: Refines T031.
- [X] T055 [S] **Update Task Ordering for Data Flow**: Ensure `T051` (Data Streaming) is listed as a strict prerequisite for `T015` (Preprocessing) and `T023` (Modeling) in the dependency graph.
 - **Action**: Update the "Dependencies & Execution Order" section to reflect that data acquisition must complete before any aggregation or modeling begins.
 - **Requirement**: Prevents the "verify-script runs before evaluation" failure mode.
- [X] T056 [S] **Add Power Analysis Task**: Create `src/analysis/power_analysis.py` to calculate the statistical power of the permutation tests.
 - **Action**: Implement a function that takes the sample size and effect size to estimate power, logging the result to `logs/power_analysis.log`.
 - **Requirement**: This addresses SC-001 and ensures the permutation shuffles are statistically justified.
 - **Dependency**: Depends on T047.

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

1. **FR-002-S (Tail-Preserving Stratified Sampling)**: `plan.md` Phase 2 mandates oversampling the lowest decile of arrival times. `spec.md` does not authorize this. **Task T016 was removed. Task T050 is responsible for updating plan.md to remove this requirement.**
2. **Unified Spatial Model (GP Always)**: `plan.md` Phase 3 mandates a GP random effect regardless of Moran's I. `spec.md` FR-004/FR-005 requires conditional GP application. **T023 implements the conditional logic per spec, overriding the plan. Task T050 is responsible for updating plan.md.**
3. **Runtime Budget**: `plan.md` estimates 5.5h, but `spec.md` SC-005 and CI constraint require < 4h. **T042 is added to optimize for 4h, overriding the plan's 5.5h estimate.**
4. **Synthetic Data Fallback**: `plan.md` Phase 1.2 allows synthetic data generation if real data is missing. `spec.md` and the "Real data + real results only" rule forbid this. **Task T051 removes the synthetic fallback and enforces real data streaming or failure.**

**Action Required**: `plan.md` must be updated to align with `spec.md` and the new task requirements before this project can advance.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Revision (Phase 7)**: Depends on Foundational and initial implementation of US1/US2/US3
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

**⚠️ IMPORTANT**: Tasks T025 (US2 permutation test) and T032 (US3 permutation test) both require significant CPU resources. They MUST be serialized via **T045** (Orchestration) to ensure they do not run concurrently and exceed the CI limit. T046 (Post-Run Validation) will verify the runtime budget after execution.

**⚠️ NEW CONSTRAINT**: Tasks T051 (Real Data Streaming) and T052 (Explicit Source) MUST be completed before T015 (Preprocessing) to ensure no synthetic data is ever processed.

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