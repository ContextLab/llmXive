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

## Phase 0: Pre-Implementation & Plan Reconciliation

**Purpose**: Resolve conflicts between spec and plan, define concrete thresholds, and verify data sources before implementation begins.

- [ ] T050a [S] [Plan] **Reconcile Tail-Sampling Requirement**: Update `plan.md` to remove any mention of "FR-002-S" or "Tail-Preserving Stratified Sampling".
 - **Action**: Search `plan.md` for "FR-002-S" or "Tail-Preserving Stratified Sampling". If found, remove the text. If not found, log "Not found, no action needed".
 - **Requirement**: Ensure `plan.md` aligns with `spec.md` FR-002.
 - **Dependency**: None.
- [ ] T050b [S] [Plan] **Reconcile GP Requirement**: Update `plan.md` to change the "mandatory a priori Gaussian Process (GP)" requirement to a "conditional GP" based on Moran's I diagnostics, aligning with `spec.md` FR-004.
 - **Action**: Search `plan.md` for "mandatory a priori". Replace with "conditional (applied if Moran's I > 0.15)".
 - **Requirement**: Ensure `plan.md` aligns with `spec.md` FR-004.
 - **Dependency**: None.
- [ ] T050c [S] [Plan] **Update Runtime Budget**: Update `plan.md` to reflect the 6-hour runtime constraint (SC-005) instead of the 5.5-hour estimate.
 - **Action**: Edit `plan.md` to update the runtime estimate to < 6 hours.
 - **Requirement**: Ensure `plan.md` aligns with `spec.md` SC-005.
 - **Dependency**: None.
- [ ] T001 [S] [Plan] **Define Assumption Targets**: Update `plan.md` and `src/config.py` with concrete numeric values for SC-001 to SC-004 as *assumption targets* (not spec edits).
 - **Action**: Add the following to `plan.md` under "Success Criteria & Fallbacks" and to `src/config.py`:
   - `POWER_TARGET = 0.80`
   - `INSUFFICIENT_DATA_TARGET = 0.20`
   - `CONVERGENCE_TARGET = 0.90`
   - `CI_WIDTH_TARGET = 5.0`
 - **Note**: Do NOT edit `spec.md` to remove `[deferred]` placeholders; preserve spec integrity.
 - **Dependency**: Depends on T050a, T050b, T050c.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T002 Create project structure per implementation plan by executing: `mkdir -p src/data src/models src/analysis data/raw data/processed data/interim tests/contract tests/unit tests/integration docs`
- [ ] T003a Create `pyproject.toml` at repository root with `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (lint.select=['E','F','W','I'], lint.ignore=[]) configuration sections
- [ ] T003b Create `.pre-commit-config.yaml` with hooks for `black` and `ruff` and configure pre-commit installation instructions in `README.md`
- [ ] T004 Create empty `src/data/download.py` file at repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes runtime optimization to meet SC-005.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement `src/data/download.py` to:
 1. Check for real eBird/NOAA files in `data/raw/ebird/` and `data/raw/climate/`.
 2. **Real Data Mode**: If real data is missing, check for `DATA_PATH` environment variable. If present, use it. If absent, check for verified sample flags. If all fail, log error "Real data required but not found; check DATA_PATH or verified sample" and exit 1.
 3. **CONSTRAINT**: Remove all synthetic data generation logic. No fallback to `numpy.random`.
 4. Archive real files unchanged (copy to `data/raw/archive/`) and compute SHA-256 checksums.
 5. Write checksums to `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml` under keys `artifact_hashes` and `updated_at`.
 - **Dependency**: None.
- [ ] T006 [P] Add `tests/contract/test_schemas.py::test_ebird_schema_columns` asserting `df.columns` equals [species, lat, lon, date, count, checklist_id] and `df.dtypes` match expected types (TDD: Write before implementation)
- [ ] T007 Implement `src/data/impute.py` for spatial interpolation of missing climate data.
 - **Input**: Read from `data/raw/climate.parquet` (DataFrame with columns: lat, lon, temp, week, precip).
 - **Logic**: Use `scipy.interpolate.griddata` with a neighbor search in **degrees** (lat/lon) at an appropriate spatial scale.
 - **Output**: Write imputed data to `data/interim/climate_imputed.parquet` and update metadata with flagged cells.
- [ ] T009 Create base data entities: `MigrationRecord`, `PhenologyMetric`, `ClimateVariable` classes in `src/models/entities.py`
- [ ] T010 [P] [Foundation] **Configure Logging and Constants**: Create `src/config.py` file.
 - **Constants**: Define and export `SEED=42`, `GRID_RES=0.5`, `PERMUTATIONS=10000`. **Remove `SAMPLE_SIZE=1000`**.
 - **Targets**: Define `POWER_TARGET=0.80`, `CI_WIDTH_TARGET=5.0`, `CONVERGENCE_TARGET=0.90`, `INSUFFICIENT_DATA_TARGET=0.20`.
 - **Logging**: Implement logging configuration with format `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.
 - **Rotation Policy**: Max files, 10MB each.
 - **Verification**: Write a test log entry and parse it to ensure format compliance.
 - **Note**: This consolidates logging setup and constant definition into a single artifact to prevent ordering conflicts.
- [ ] T051a [S] [US1] **Verify Dataset Existence**: Verify the existence of the `vvud/eb-data` dataset on HuggingFace.
 - **Action**: Write a script `src/data/verify_dataset.py` that attempts to list the `vvud/eb-data` dataset using `datasets.load_dataset`.
 - **Requirement**: If the dataset is not found, raise a `RuntimeError` with a clear message.
 - **Dependency**: None.
- [ ] T051 [S] [US1] **Stream Full Dataset**: Implement `src/data/stream_utils.py` to stream the full eBird dataset in chunks.
 - **Action**: Use `datasets.load_dataset("vvud/eb-data", streaming=True)` to fetch data in chunks.
 - **Requirement**: Ensure the pipeline processes the full dataset without loading it all into memory.
 - **Dependency**: Depends on T051a, T005.
- [ ] T011 [P] [US1] **Report Actual Sample Size**: Implement `src/analysis/sample_size_report.py` to calculate and log the actual sample size.
 - **Action**: Count the number of records processed and log it to `logs/sample_size.log`.
 - **Requirement**: Ensure the sample size is reported for SC-001.
 - **Dependency**: Depends on T051.
- [ ] T011a [P] [US1] **Calculate Statistical Power**: Implement `src/analysis/power_analysis.py` to calculate post-hoc statistical power and effect size stability.
 - **Action**: Use `statsmodels.stats.power` to compute power based on sample size, effect size estimates from T023, and alpha=0.05.
 - **Output**: Write power metrics to `data/processed/power_analysis.json`.
 - **Requirement**: Satisfy SC-001 measurement.
 - **Dependency**: Depends on T023.
- [ ] T057a [P] [Foundation] **Implement Chunked Permutation Test**: Implement `src/models/utils.py` to run permutation tests in chunks.
 - **Action**: Split the permutation shuffles into smaller batches to avoid memory overflow.
 - **Requirement**: Ensure the full permutation shuffles are completed within the CI budget.
 - **Dependency**: Depends on T051.
- [ ] T058a [P] [Foundation] **Implement Streaming Manifold Analysis**: Implement `src/models/trajectory.py` to stream the trajectory data in chunks.
 - **Action**: Use `datasets.load_dataset` with `streaming=True` to fetch trajectory data in chunks.
 - **Requirement**: Ensure the manifold analysis processes the full dataset without loading it all into memory.
 - **Dependency**: Depends on T051.
- [ ] T047 [P] [Foundation] **Apply Thresholds to Config**: Update `src/config.py` with the concrete values defined in T001.
 - **Action**: Ensure `POWER_TARGET`, `CI_WIDTH_TARGET`, `CONVERGENCE_TARGET`, `INSUFFICIENT_DATA_TARGET` are present and exported.
 - **Requirement**: Ensure these values are used in validation tasks.
 - **Dependency**: Depends on T001.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eBird/NOAA (or synthetic) data, filter to migratory species (recent years), aggregate to coarse grid cells, and compute phenology metrics.

**Independent Test**: The pipeline can be fully tested by running `src/data/preprocess.py` on a subset (one species, one region) and verifying the output CSV contains expected columns (`species`, `grid_cell`, `week`, `phenology_metric`, `climate_temp`, `climate_precip`) with no missing values in critical fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T013 [P] [US1] Add `tests/integration/test_data_pipeline.py` with function `test_data_ingestion_flow` verifying end-to-end flow (TDD: write before T014)

### Implementation for User Story 1

- [ ] T014 [P] [US1] Call the download functions from T005 in `src/data/preprocess.py` to ensure data is available before processing; verify file presence and checksums. **Depends on T005**.
- [ ] T015a [S] [US1] **Retrieve CLO Migratory List**: Implement `src/data/download.py::get_clo_migratory_list` to fetch and cache the Cornell Lab of Ornithology list of migratory species.
 - **Action**: Download the official CLO list (or a verified mirror) and cache it in `data/raw/clo_migratory_list.csv`.
 - **Requirement**: Ensure the list is used for filtering in T015.
 - **Dependency**: Depends on T005.
- [ ] T015 [P] [US1] Implement `src/data/preprocess.py` to filter eBird records to migratory species using the CLO list from T015a and aggregate to weekly counts per spatial grid cell (Use `GRID_RES=0.5` from T010 config). **Depends on T015a, T051**.
 - **Logic**: Call `mark_insufficient_cells` (T018) *after* aggregation to ensure invalid cells are excluded.
- [ ] T017a [US1] Implement phenology metric computation (`first_arrival`, `median_arrival`, `stopover_duration`) in `src/data/preprocess.py`.
 - **Logic**: `stopover_duration` = High percentile DOY - Low percentile DOY.
- [ ] T017b [US1] Implement **seasonal climate average calculation** (March–May temperature, precipitation) in `src/data/preprocess.py` to satisfy **FR-003**.
 - **Logic**: Compute mean temperature and total precipitation for the March–May period per grid cell and year.
 - **Output**: Append `climate_temp_avg`, `climate_precip_total` to the output dataset.
- [ ] T016 [S] [US1] **Generate Provenance Mapping**: Implement `src/data/preprocess.py::generate_provenance` to create `data/provenance/row_mapping.json`.
 - **Logic**: Map processed rows back to original `checklist_id`s from the raw eBird data.
 - **Output**: Write `data/provenance/row_mapping.json`.
 - **Dependency**: Depends on T015.
- [ ] T018 [S] [US1] **Mark Insufficient Data Cells**: Implement `src/data/preprocess.py::mark_insufficient_cells`.
 - **Logic**: Scan aggregated grid cells. If count < 5, set `data_quality="insufficient"` and exclude from downstream modeling.
 - **Artifact**: Log species, grid cell, and reason to `logs/pipeline.log`. Write metadata to `data/processed/metadata_insufficient_cells.json`.
 - **Dependency**: Depends on T015.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Phenology-Climate Correlation Modeling (Priority: P2)

**Goal**: Fit Generalized Additive Mixed Models (GAMMs) with conditional spatial correction, compute p-values with FDR correction, and handle convergence failures.

**Independent Test**: The modeling step can be tested by running `src/models/gamm_fit.py` on a synthetic dataset with known correlation parameters and verifying output includes coefficient estimates and fit statistics matching known parameters within % tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Add `tests/contract/test_output_schemas.py` with function `test_gamm_output_schema` verifying coefficient and p-value columns
- [ ] T022 [P] [US2] Add `tests/integration/test_modeling.py` with function `test_gamm_convergence` verifying fit on synthetic data

### Implementation for User Story 2

- [ ] T023 [S] [US2] Implement `src/models/gamm_fit.py` to fit a **Conditional Spatial Model** per Spec FR-004. **Depends on T016, T018, T047**.
 - **Model**: `phenology_metric ~ s(temp) + s(precip) + s(effort) + (1 + temp | species)`.
 - **Logic**:
 1. Fit base model.
 2. Compute Moran's I on residuals.
 3. **IF** Moran's I > 0.15: Re-fit with a Gaussian Process (GP) random effect using a Matérn kernel (nu=1.5).
 4. **ELSE**: Proceed with the base model (diagnostic satisfied).
 5. **LOG**: Record Moran's I value and whether GP was applied.
 6. **CONSTRAINT**: Follow Spec FR-004. The plan has been reconciled in T050b to match this logic.
 - **Output**: Write results to `data/processed/model_results.parquet` including `moran_i`, `gp_applied` (bool), coefficients, p-values.
 - **Dependency**: Depends on T015, T016, T018, T047.
- [ ] T023b [S] [US2] **Post-hoc Moran's I Validation**: Implement `src/models/gamm_fit.py::validate_morans_i` to perform a post-hoc diagnostic on residuals *only* for logging/validation, not model selection.
 - **Action**: Compute Moran's I on residuals of the final model. Log the value. Do not trigger re-fitting.
 - **Requirement**: Satisfy Plan Phase 2.2 "validation only".
 - **Dependency**: Depends on T023.
- [ ] T024 [US2] Implement species-year random intercepts and slopes logic in `src/models/gamm_fit.py`
- [ ] T025a [S] [US2] **Benchmark Permutation Test**: Implement `src/models/utils.py::benchmark_permutation` to estimate runtime.
 - **Action**: Run multiple shuffles and measure time.
 - **Requirement**: Use this to estimate the time for full shuffles.
 - **Dependency**: Depends on T057a.
- [ ] T025b [S] [US2] **Permutation Test Loop**: Implement `src/models/utils.py::run_permutation_test` with `n_shuffles=config.PERMUTATIONS`.
 - **Logic**: Run full shuffles in chunks (batch size 1000) to avoid memory overflow.
 - **Output**: Write to `data/processed/permutation_results.json` with schema: `{ "species": str, "coefficient": str, "p_value": float, "n_shuffles": int, "final_p_value": float }`.
 - **Dependency**: Depends on T023, T025a, T047.
- [ ] T025c [S] [US2] **Apply FDR Correction**: Implement `src/models/utils.py::apply_fdr_correction` to adjust p-values.
 - **Action**: Apply Benjamini-Hochberg FDR correction to the p-values from T025b.
 - **Output**: Write to `data/processed/model_results_fdr.parquet` with `q_value` column.
 - **Dependency**: Depends on T025b.
- [ ] T027a [US2] Implement try/except block in `src/models/gamm_fit.py` to catch convergence failures.
- [ ] T027b [US2] Define log message format for convergence failures in `src/models/gamm_fit.py`.
 - **Format**: "Convergence failed for species {species}: {error}".
- [ ] T027c [US2] Verify log output for convergence failures in `tests/unit/test_models.py`.
 - **Test**: Assert log contains expected message format.
- [ ] T042 [S] [Foundation] **Runtime Optimization**: Profile and implement chunked I/O and vectorization to ensure pipeline meets SC-005 (< 6h runtime).
 - **Artifact**: Implement chunked reading in `src/data/preprocess.py` and `src/models/gamm_fit.py`.
 - **Logic**: Use `pandas.read_csv(..., chunksize=...)` for large files. Vectorize all `apply` loops in preprocessing.
 - **Benchmark**: Measure time on a synthetic dataset of substantial scale.; target < 6h total.
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
- [ ] T031 [US3] Implement trajectory analysis using **Riemannian Manifold Statistics** on the 2-sphere (S^2) via `geomstats`. **Depends on T047, T058a**.
 - **Algorithm**:
 1. Compute weekly centroids for each species-year.
 2. Calculate geodesic distances on S² using `geomstats.geometry.sphere.Sphere` (or equivalent Riemannian metric).
 3. Detect route shifts by comparing trajectory distances between years using Fréchet means or similar manifold statistics.
 - **Constraint**: Use `geomstats` for correct Riemannian math. If `geomstats` is unavailable, use `scipy` with explicit geodesic formula `acos(lat1*lat2 + lon1*lon2...)` as a fallback with a warning.
 - **Output**: Write `shift_magnitude` and `shift_direction` to `data/processed/trajectory_results.json`.
- [ ] T032a [S] [US3] **Benchmark Trajectory Permutation Test**: Implement `src/models/trajectory_utils.py::benchmark_trajectory_permutation` to estimate runtime.
 - **Action**: Run a series of shuffles and measure time.
 - **Requirement**: Use this to estimate the time for full shuffles.
 - **Dependency**: Depends on T058a.
- [ ] T032b [S] [US3] **Trajectory Permutation Test Loop**: Implement `src/models/trajectory_utils.py::run_trajectory_permutation_test` with `n_shuffles=config.PERMUTATIONS`.
 - **Logic**: Run full shuffles in chunks (batch size 1000) to avoid memory overflow.
 - **Output**: Write to `data/processed/trajectory_permutation_results.json` with schema: `{ "species": str, "shift_magnitude": float, "p_value": float, "n_shuffles": int, "final_p_value": float }`.
 - **Dependency**: Depends on T030, T031, T032a, T042, T047.
- [ ] T033 [US3] Implement bootstrapped confidence interval generation for **phenology shift predictions and trajectory shift magnitudes** in `src/models/utils.py`.
 - **Logic**: Resample the centroid estimation process and trajectory shift magnitudes using **Block Bootstrap** to preserve temporal autocorrelation.
 - **Output**: Append `ci_lower`, `ci_upper` to the trajectory results file.
 - **Note**: This task consolidates FR-007 requirements for both phenology and trajectory shifts.
 - **Dependency**: Depends on T032b.
- [ ] T033a [P] [US3] **Calculate CI Width**: Implement `src/analysis/ci_width.py` to calculate the width of 95% CIs from T033.
 - **Action**: Compute `ci_upper - ci_lower` for each species and compare against `config.CI_WIDTH_TARGET`.
 - **Output**: Write CI width metrics to `data/processed/ci_width_report.json`.
 - **Requirement**: Satisfy SC-004 measurement.
 - **Dependency**: Depends on T033.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Orchestration & Validation (SC-002, SC-003, SC-005)

**Purpose**: Ensure sequential execution of heavy tasks and validate success criteria.

- [ ] T045 [S] **Orchestration**: Implement a file-based lock mechanism to serialize T025b and T032b. **Depends on T047**.
 - **Logic**: Use `filelock` library. Lock file path: `data/interim/pipeline.lock`. Timeout: A predefined duration.
 - **Output**: Log execution order.
 - **Dependency**: Depends on T042.
- [ ] T046 [S] **Post-Run Validation**: Verify the lock mechanism worked and total runtime is within budget.
 - **Logic**: Run a benchmark of T025b and T032b sequentially (post-execution) to verify total time < 6h.
 - **Output**: Log total time and assertion result.
 - **Dependency**: Depends on T025b, T032b, T045.
- [ ] T043 [US1] Calculate SC-002, SC-001, SC-004: Proportion of "insufficient data" cells, Power, CI Width.
 - **Logic**: Count cells marked "insufficient" / Total cells. Calculate power from T011a. Calculate CI width from T033a.
 - **Output**: Write to `data/processed/success_criteria_report.json`.
 - **Dependency**: Depends on T047, T011a, T033a.
- [ ] T044 [US2] Calculate SC-003: GAMM Convergence Rate.
 - **Logic**: Count successful fits / Total attempts.
 - **Output**: Write to `data/processed/success_criteria_report.json`.
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
- [ ] T041c [P] Add runtime assertion (< 6h) to `validate_quickstart` job.

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
- **GPU Offload (Phase 8)**: Depends on US2/US3 implementation and CI workflow updates

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

1. Complete Phase 0: Pre-Implementation & Plan Reconciliation
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Global Execution Constraint

**⚠️ IMPORTANT**: Tasks T025b (US2 permutation test) and T032b (US3 permutation test) both require significant CPU resources. They MUST be serialized via **T045** (Orchestration) to ensure they do not run concurrently and exceed the CI limit. T046 (Post-Run Validation) will verify the runtime budget after execution.

**⚠️ NEW CONSTRAINT**: Tasks T051a (Verify Dataset Existence) and T051 (Real Data Streaming) MUST be completed before T015 (Preprocessing) to ensure no synthetic data is ever processed.

**⚠️ CPU CONSTRAINT**: Tasks T057a and T058a MUST be implemented to ensure heavy computations (Manifold, Permutation) are processed in chunks on CPU, preventing scientific fabrication or timeout failures.

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