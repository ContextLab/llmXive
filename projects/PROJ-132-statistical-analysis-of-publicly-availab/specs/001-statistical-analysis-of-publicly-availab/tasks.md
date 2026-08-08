---
description: "Task list template for feature implementation"
---

# Tasks: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

**Input**: Design documents from `/specs/001-bird-migration-climate-correlation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must wait for predecessor completion)
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

**Purpose**: Verify plan/spec alignment and document scope limitations without editing the plan until verification is complete.

- [ ] T050b [S] [Plan] **Verify Plan Alignment**: Scan `plan.md` and `spec.md` for specific contradictions. <!-- FAILED: unspecified -->
 - **Action**: Write a script `src/plan/verify_alignment.py` that scans `plan.md` and `spec.md`.
 - **Logic**:
 1. Check if `plan.md` contains "mandatory a priori GP" (matches spec US-2).
 2. Check if `plan.md` contains "Critical Data Scope Note" regarding the sample dataset.
 3. Check for specific text patterns: 'NOAA/PRISM' in `spec.md` vs 'Daymet' in `plan.md`. If found, flag as "DATA_SOURCE_MISMATCH".
 4. Check for any terms in `plan.md` that do not exist in `spec.md` (e.g., "FR-002-S").
 - **Output**: Write findings to `data/provenance/plan_conflicts.json` with keys: `{"contradictions": [{"location": "string", "spec_req": "string", "plan_text": "string", "type": "DATA_SOURCE_MISMATCH"|"SCOPE_NOTE"|"OTHER"}]}`.
 - **Requirement**: If no contradictions, log "No contradictions found". Do NOT edit `plan.md`.
 - **Dependency**: None.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T002a [P] **Create Project Structure**: Execute `mkdir -p src/data src/models src/analysis data/raw data/processed data/interim tests/contract tests/unit tests/integration docs`.
 - **Action**: Execute the `mkdir` command to create the project structure.
 - **Requirement**: Ensure all directories are created as specified.
 - **Dependency**: None.
- [X] T002b [P] **Verify Project Structure**: Write a unit test `tests/unit/test_setup.py::test_directory_structure_exists` that asserts the existence of specific paths: `src/data`, `src/models`, `data/raw`, `data/processed`, `data/interim`, `tests/contract`, `tests/unit`, `tests/integration`.
 - **Action**: Implement `tests/unit/test_setup.py` with assertions for directory existence.
 - **Requirement**: Ensure all directories are present as specified.
 - **Dependency**: Depends on T002a.
- [X] T003a Create `pyproject.toml` at repository root with `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (lint.select=['E','F','W','I'], lint.ignore=[]) configuration sections
- [ ] T003b [P] **Create Pre-commit Config**: Create `.pre-commit-config.yaml` with hooks for `black` and `ruff` and configure pre-commit installation instructions in `README.md`.
 - **Action**: Create `.pre-commit-config.yaml` with hooks for `black` and `ruff`.
 - **Requirement**: Ensure the hooks are configured correctly.
 - **Dependency**: None.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes runtime optimization to meet SC-005.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005a [S] [Foundation] **Verify Data Availability**: Check for the existence of the verified sample dataset (`vvud/eb-data`) and climate dataset (`daymet/annual`).
 - **Action**: Write a script `src/data/verify_dataset.py` that attempts to list `vvud/eb-data` and `daymet/annual` using `datasets.load_dataset`.
 - **Logic**:
 1. If `vvud/eb-data` exists, set `sample_scope_adopted = True` and `full_ebd_available = False`.
 2. If `daymet/annual` exists, set `climate_data_available = True`.
 3. If either is missing, raise `RuntimeError`.
 - **Output**: Write `data/provenance/data_availability_report.json` with keys: `{"full_ebd_available": bool, "sample_scope_adopted": bool, "climate_data_available": bool, "source": "vvud/eb-data"|"daymet/annual"|"unknown"}`.
 - **Requirement**: Do NOT attempt to download full EBD first. The Plan's scope note explicitly adopts the sample.
 - **Dependency**: None.
- [ ] T005b [S] [Foundation] **Download and Verify eBird Sample Data**: Download the verified sample data from HuggingFace (`vvud/eb-data`) and verify checksums.
 - **Action**: Use `datasets.load_dataset("vvud/eb-data", split="train", trust_remote_code=True)` to fetch the data. Compute SHA-256 checksums of the downloaded files.
 - **Requirement**: Ensure data is downloaded from the canonical source. Do NOT fall back to synthetic data.
 - **Dependency**: Depends on T005a.
- [ ] T005c1 [S] [Foundation] **Download Daymet Climate Data**: Download the Daymet climate data for North America for a recent multi-year period.
 - **Action**: Use `datasets.load_dataset("daymet/annual",...)` to fetch the data from the verified public URL. Note: Daymet is used as a verified substitute for NOAA/PRISM per the Plan's "Critical Data Scope Note".
 - **Requirement**: Ensure data is downloaded from the canonical source.
 - **Dependency**: Depends on T005a.
- [ ] T005c2 [S] [Foundation] **Verify Daymet Checksums**: Verify checksums of the downloaded Daymet climate data.
 - **Action**: Compute SHA-256 checksums of the downloaded files.
 - **Requirement**: Ensure data integrity.
 - **Dependency**: Depends on T005c1.
- [ ] T005c3 [S] [Foundation] **Document Spec/Plan Data Deviation**: Document the deviation between Spec FR-001 (NOAA/PRISM) and Plan/Tasks (Daymet).
 - **Action**: Write a JSON file `data/provenance/spec_plan_deviation.json` with keys: `{"spec_requirement": "NOAA/PRISM", "plan_substitute": "Daymet", "reason": "Verified open-source availability", "timestamp": "ISO8601"}`.
 - **Requirement**: Ensure this deviation is explicitly recorded. Do NOT edit `spec.md`.
 - **Dependency**: Depends on T005c2.
- [ ] T005d [P] [Foundation] **Archive and Checksum**: Archive the downloaded files unchanged (copy to `data/raw/archive/`) and compute SHA-256 checksums.
 - **Action**: Copy files to `data/raw/archive/`. Compute checksums. Write results to `data/raw/archive/checksums.sha256`.
 - **Requirement**: Ensure data integrity.
 - **Dependency**: Depends on T005b, T005c2.
- [X] T005e [S] [Foundation] **Update State File**: Write checksums to `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml` under keys `artifact_hashes` and `updated_at`.
 - **Action**: Update the state file with checksums.
 - **Requirement**: Ensure state file is up to date.
 - **Dependency**: Depends on T005d.
- [X] T006 [P] Add `tests/contract/test_schemas.py::test_ebird_schema_columns` asserting `df.columns` equals [species, lat, lon, date, count, checklist_id] and `df.dtypes` match expected types (TDD: Write before implementation)
- [X] T007 [S] [Foundation] **Implement `src/data/impute.py` for spatial interpolation of missing climate data.**
 - **Input**: Read from `data/raw/climate.parquet` (DataFrame with columns: lat, lon, temp, week, precip).
 - **Logic**: Use `scipy.spatial.cKDTree` or `scipy.interpolate.griddata` with a neighbor search explicitly constrained to a **1° radius** around the target cell.
 - **Output**: Write imputed data to `data/interim/climate_imputed.parquet` and update metadata with flagged cells (`is_imputed` flag).
 - **Requirement**: Ensure the `is_imputed` flag is explicitly set for all imputed cells in the output metadata.
 - **Dependency**: Depends on T005c2.
- [X] T009 Create base data entities: `MigrationRecord`, `PhenologyMetric`, `ClimateVariable` classes in `src/models/entities.py`
- [X] T010a [S] [Foundation] **Define Constants**: Create `src/config.py` file and define constants.
 - **Constants**: Define and export `SEED: int = 42`, `GRID_RES: float = 0.5`, `PERMUTATIONS: int = 10000`.
 - **Targets**: Define `DEFAULT_POWER_TARGET: float = 0.80`, `DEFAULT_CI_WIDTH_TARGET: float = 5.0`, `DEFAULT_CONVERGENCE_TARGET: float = 0.90`, `DEFAULT_INSUFFICIENT_DATA_TARGET: float = 0.20`.
 - **Note**: These are provisional defaults. They are used for estimation and reporting. Validation of their suitability happens in T011a (Phase 6).
 - **Dependency**: None.
- [X] T010b [S] [Foundation] **Implement Logging**: Implement logging configuration in `src/config.py`.
 - **Logging**: Implement logging configuration with format `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.
 - **Rotation Policy**: Max files, each limited to `maxBytes=10485760` (10MB).
 - **Dependency**: Depends on T010a.
- [X] T010c [S] [Foundation] **Test Logging**: Write a unit test `tests/unit/test_config.py::test_logging_format` to ensure format compliance.
 - **Verification**: Write a test log entry and parse it to ensure format compliance. Assert log line contains ISO8601 timestamp.
 - **Dependency**: Depends on T010b.
- [ ] T051a [P] [Foundation] **Verify Verified Sample Dataset**: Verify the existence of the `vvud/eb-data` dataset on HuggingFace as specified in the plan's "Critical Data Scope Note".
 - **Action**: Write a script `src/data/verify_dataset.py` that attempts to list the `vvud/eb-data` dataset using `datasets.load_dataset`.
 - **Requirement**: If the dataset is not found, raise a `RuntimeError` with a clear message referencing the plan's scope note.
 - **Dependency**: Depends on T005a.
- [X] T051 [P] [Foundation] **Stream Verified Sample Data**: Implement `src/data/stream_utils.py` to stream the verified sample eBird dataset in chunks.
 - **Action**: Use `datasets.load_dataset("vvud/eb-data", streaming=True)` to fetch data in chunks.
 - **Requirement**: Ensure the pipeline processes the available sample dataset without loading it all into memory.
 - **Dependency**: Depends on T051a.
- [X] T057a [S] [Foundation] **Implement Chunked Permutation Utility**: Implement `src/models/utils.py` to provide chunked permutation test logic.
 - **Action**: Create a function `run_permutation_chunked(data, n_shuffles, chunk_size=1000)` that splits the permutation shuffles into smaller batches to avoid memory overflow.
 - **Error Handling**: Raise `MemoryError` if chunk size is too large for available RAM.
 - **Requirement**: Ensure the full permutation shuffles are completed within the CI budget.
 - **Dependency**: Depends on T051.
- [X] T058a [S] [Foundation] **Implement Streaming Trajectory Utility**: Implement `src/models/trajectory_utils.py` to provide streaming logic for trajectory data.
 - **Action**: Create a function `stream_trajectory_data(dataset_name, streaming=True)` that uses `datasets.load_dataset` with `streaming=True` to fetch trajectory data in chunks.
 - **Error Handling**: Raise `MemoryError` if chunk size is too large for available RAM.
 - **Requirement**: Ensure the manifold analysis processes the full dataset without loading it all into memory.
 - **Dependency**: Depends on T051.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eBird/NOAA (or synthetic) data, filter to migratory species (2020-2024), aggregate to coarse grid cells, and compute phenology metrics.

**Independent Test**: The pipeline can be fully tested by running `src/data/preprocess.py` on a subset (one species, one region) and verifying the output CSV contains expected columns (`species`, `grid_cell`, `week`, `phenology_metric`, `climate_temp`, `climate_precip`) with no missing values in critical fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T013 [P] [US1] Add `tests/integration/test_data_pipeline.py` with function `test_data_ingestion_flow` verifying end-to-end flow (TDD: write before T014)

### Implementation for User Story 1

- [X] T015a [S] [US1] **Retrieve CLO Migratory List**: Implement `src/data/download.py::get_clo_migratory_list` to fetch and cache the Cornell Lab of Ornithology list of migratory species.
 - **Action**: Download the official CLO list (or a verified mirror) and cache it in `data/raw/clo_migratory_list.csv`.
 - **Requirement**: Ensure the list is used for filtering in T015b.
 - **Dependency**: Depends on T005e.
- [X] T015b [S] [US1] **Implement Preprocessing Pipeline**: Implement `src/data/preprocess.py` to filter eBird records to migratory species using the CLO list from Ta and the 2020-2024 period, and aggregate to weekly counts per spatial grid cell (Use `GRID_RES=0.5` from T010 config).
 - **Logic**: Call `mark_insufficient_cells` (T018) *after* aggregation to ensure invalid cells are excluded.
 - **Dependency**: Depends on T015a, T051, T005e.
- [ ] T016 [S] [US1] **Generate Provenance Mapping**: Implement `src/data/preprocess.py::generate_provenance` to create `data/provenance/row_mapping.json`.
 - **Logic**: Map processed rows back to original `checklist_id`s from the raw eBird data.
 - **Output**: Write `data/provenance/row_mapping.json`.
 - **Requirement**: Ensure the mapping integrity is verified (e.g., assert all `checklist_id`s in processed data exist in raw data).
 - **Dependency**: Depends on T015b.
- [X] T017a [US1] Implement phenology metric computation (`first_arrival`, `median_arrival`, `stopover_duration`) in `src/data/preprocess.py`.
 - **Logic**: `stopover_duration` = High percentile DOY - Low percentile DOY.
- [X] T017b [US1] Implement **seasonal climate average calculation** (March–May temperature, precipitation, extreme weather indices) in `src/data/preprocess.py` to satisfy **FR-003** and **Imputation Flagging**.
 - **Logic**: Compute mean temperature and total precipitation for the March–May period per grid cell and year. Calculate extreme weather indices (e.g., heatwaves, heavy precipitation events) from Daymet data.
 - **Imputation**: If missing, use `src/data/impute.py` (T007) to interpolate.
 - **Output**: Append `climate_temp_avg`, `climate_precip_total`, `extreme_weather_index`, and `is_imputed` (bool) to the output dataset.
 - **Metadata**: Write a separate `data/processed/imputation_metadata.json` listing all imputed cells and their sources. **Explicitly flag imputed cells in this metadata**.
 - **Dependency**: Depends on T007, T015b.
- [ ] T017d [S] [US1] **Verify Imputation Metadata**: Write a test `tests/unit/test_preprocess.py::test_imputation_metadata_exists` to verify that `data/processed/imputation_metadata.json` exists and is readable.
 - **Action**: Check file existence and JSON validity. Assert schema validation.
 - **Requirement**: Ensure downstream models can consume this metadata.
 - **Dependency**: Depends on T017b.
- [X] T018 [S] [US1] **Mark Insufficient Data Cells**: Implement `src/data/preprocess.py::mark_insufficient_cells`.
 - **Logic**: Scan aggregated grid cells. If count < 5, set `data_quality="insufficient"` and exclude from downstream modeling.
 - **Artifact**: Log species, grid cell, and reason to `logs/pipeline.log`. Write metadata to `data/processed/metadata_insufficient_cells.json`.
 - **Dependency**: Depends on T015b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Phenology-Climate Correlation Modeling (Priority: P2)

**Goal**: Fit Generalized Additive Mixed Models (GAMMs) with mandatory GP, compute p-values with FDR correction, and handle convergence failures.

**Independent Test**: The modeling step can be tested by running `src/models/gamm_fit.py` on a synthetic dataset with known correlation parameters and verifying output includes coefficient estimates and fit statistics matching known parameters within % tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Add `tests/contract/test_output_schemas.py::test_gamm_output_schema` with function `test_gamm_output_schema` verifying coefficient and p-value columns.
 - **Action**: Add `tests/contract/test_output_schemas.py::test_gamm_output_schema` with function `test_gamm_output_schema` verifying coefficient and p-value columns.
 - **Requirement**: Ensure the output schema is correctly verified.
 - **Dependency**: None.
- [X] T022 [P] [US2] Add `tests/integration/test_modeling.py::test_gamm_convergence` with function `test_gamm_convergence` verifying fit on synthetic data.
 - **Action**: Add `tests/integration/test_modeling.py::test_gamm_convergence` with function `test_gamm_convergence` verifying fit on synthetic data.
 - **Requirement**: Ensure the fit on synthetic data is correctly verified.
 - **Dependency**: None.

### Implementation for User Story 2

- [ ] T045a [P] **Implement Lock Wrapper**: Implement a file-based lock mechanism using `filelock.FileLock`.
 - **Logic**: Lock file path: `data/interim/pipeline.lock`. Timeout: A predefined duration.
 - **Output**: Log execution order.
 - **Dependency**: Depends on T010a.
- [ ] T045b [P] **Integrate Lock**: Integrate the lock into T023a and T032b.
 - **Logic**: Ensure T023a and T032b acquire the lock before running.
 - **Dependency**: Depends on T045a.
- [ ] T045c [P] **Test Lock Contention**: Write a test for lock contention.
 - **Dependency**: Depends on T045b.
- [X] T023a [S] [US2] **Fit GAMM with Mandatory GP**: Implement `src/models/gamm_fit.py` to fit a GAMM per Spec FR-004 with a **mandatory a priori** GP random effect. **Depends on T016, T018, T017d**.
 - **Model**: `phenology_metric ~ s(temp) + s(precip) + s(extreme_weather_index) + (1 + temp | species) + gp(lat, lon, kernel="matern")`.
 - **Logic**:
 1. Implement species-year random intercepts and slopes (temperature slope variation) as defined in the formula `(1 + temp | species)`.
 2. Fit the model for each species-year combination.
 3. Log and output results to `data/processed/model_results.parquet`.
 - **Output**: Write base model results to `data/processed/model_results_base.parquet`.
 - **Dependency**: Depends on T015b, T016, T018, T017d.
- [X] T023b [S] [US2] **Compute Moran's I Diagnostic**: Implement `src/models/gamm_fit.py::compute_morans_i` to compute Moran's I on residuals.
 - **Action**: Compute Moran's I on residuals of the final model.
 - **Output**: Write structured output to `data/provenance/morans_i.json` with keys: `{"species": str, "morans_i": float, "p_value": float, "trigger_refit": bool}`.
 - **Logic**: If `morans_i > 0.15`, set `trigger_refit` to `True`. This flag is read by T023b_refit to initiate the mandatory re-fit.
 - **Requirement**: Write the structured JSON output. Do NOT perform the re-fit here; only flag it.
 - **Dependency**: Depends on T023a.
- [X] T025a [S] [US2] **Benchmark Permutation Test**: Implement `src/models/utils.py::benchmark_permutation` to estimate runtime.
 - **Action**: Run multiple shuffles and measure time.
 - **Requirement**: Use this to estimate the time for full shuffles.
 - **Dependency**: Depends on T057a.
- [X] T025b [S] [US2] **Permutation Test Loop**: Implement `src/models/utils.py::run_permutation_test` with `n_shuffles=10000` (hard constraint) and `config.PERMUTATIONS`.
 - **Logic**: Run full shuffles in chunks (batch size 1000) using the utility from T057a.
 - **Output**: Write to `data/processed/permutation_results.json` with schema: `{ "species": str, "coefficient": str, "p_value": float, "n_shuffles": int, "final_p_value": float }`.
 - **Requirement**: Ensure the [deferred] shuffles requirement is explicitly stated in the task logic.
 - **Dependency**: Depends on T023a, T025a, T057a, T045b.
- [ ] T025c [S] [US2] **Apply FDR Correction**: Implement `src/models/utils.py::apply_fdr_correction` to adjust p-values.
 - **Action**: Apply Benjamini-Hochberg FDR correction to the p-values from T025b.
 - **Output**: Write to `data/processed/model_results_fdr.parquet` with `q_value` column.
 - **Dependency**: Depends on T025b.
- [ ] T027 [S] [US2] **Implement Convergence Error Handling**: Implement try/except block in `src/models/gamm_fit.py` to catch convergence failures, log specific message format, and verify log output.
 - **Format**: "Convergence failed for species {species}: {error}".
 - **Test**: Assert log contains expected message format.
 - **Dependency**: Depends on T023a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Route Shift Analysis and Uncertainty Quantification (Priority: P3)

**Goal**: Represent weekly migration centroids as trajectories, detect spatial route shifts using geodesic distances, and generate bootstrapped uncertainty intervals.

**Independent Test**: The route analysis can be tested by running `src/models/trajectory.py` on a synthetic dataset with randomized labels and verifying the permutation test correctly identifies no significant shift (p > 0.05) in the absence of true signal.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Add `tests/contract/test_trajectory_schemas.py::test_trajectory_output_schema` with function `test_trajectory_output_schema` verifying trajectory output schema.
 - **Action**: Add `tests/contract/test_trajectory_schemas.py::test_trajectory_output_schema` with function `test_trajectory_output_schema` verifying trajectory output schema.
 - **Requirement**: Ensure the output schema is correctly verified.
 - **Dependency**: None.
- [ ] T029 [P] [US3] Add `tests/integration/test_trajectory_analysis.py::test_route_shift_detection` with function `test_route_shift_detection` verifying route shift detection.
 - **Action**: Add `tests/integration/test_trajectory_analysis.py::test_route_shift_detection` with function `test_route_shift_detection` verifying route shift detection.
 - **Requirement**: Ensure the route shift detection is correctly verified.
 - **Dependency**: None.

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `src/models/trajectory.py` to compute weekly migration centroids per species-year
- [ ] T031c [S] [US3] Implement trajectory analysis using **Riemannian Manifold Statistics** on the 2-sphere (S^2) via `geomstats`. **Depends on T058a**.
 - **Algorithm**:
 1. Compute weekly centroids for each species-year.
 2. Calculate geodesic distances on S² using `geomstats.geometry.sphere.Sphere` (or equivalent Riemannian metric). **PRIMARY METHOD**.
 3. Detect route shifts by comparing trajectory distances between years using **Riemannian Manifold Statistics** as the primary method.
 4. **Fallback**: If `geomstats` is unavailable, use `scipy` with explicit geodesic formula `acos(sin(lat1)*sin(lat2) + cos(lat1)*cos(lat2)*cos(lon2-lon1))` as a secondary validation step only.
 - **Constraint**: Use `geomstats` for correct Riemannian math. If `geomstats` is unavailable, use `scipy` with explicit geodesic formula `acos(sin(lat1)*sin(lat2) + cos(lat1)*cos(lat2)*cos(lon2-lon1))` as a fallback with a warning.
 - **Output**: Write `shift_magnitude` and `shift_direction` to `data/processed/trajectory_results.json`.
 - **Dependency**: Depends on T058a.
- [ ] T032a [S] [US3] **Benchmark Trajectory Permutation Test**: Implement `src/models/trajectory_utils.py::benchmark_trajectory_permutation` to estimate runtime.
 - **Action**: Run a series of shuffles and measure time.
 - **Requirement**: Use this to estimate the time for full shuffles.
 - **Dependency**: Depends on T058a.
- [ ] T032b [S] [US3] **Trajectory Permutation Test Loop**: Implement `src/models/trajectory_utils.py::run_trajectory_permutation_test` with `n_shuffles=config.PERMUTATIONS`.
 - **Logic**: Run full shuffles in chunks (batch size 1000) using the utility from T058a.
 - **Output**: Write to `data/processed/trajectory_permutation_results.json` with schema: `{ "species": str, "shift_magnitude": float, "p_value": float, "n_shuffles": int, "final_p_value": float }`.
 - **Dependency**: Depends on T030, T031c, T032a, T058a, T045b.
- [ ] T033a [S] [US3] **Generate Phenology Confidence Intervals**: Implement `src/models/utils.py::generate_phenology_ci` to generate confidence intervals for model predictions (FR-007).
 - **Logic**: Resample the centroid estimation process and model predictions using **Block Bootstrap** to preserve temporal autocorrelation.
 - **Output**: Append `ci_lower`, `ci_upper` to the phenology results file.
 - **Requirement**: Ensure the CI level is explicitly stated as [deferred] and traceable to FR-007.
 - **Dependency**: Depends on T023a.
- [ ] T033b [S] [US3] **Generate Trajectory Confidence Intervals**: Implement `src/models/utils.py::generate_trajectory_ci` to generate confidence intervals for trajectory shift magnitudes (US-3).
 - **Logic**: Resample the trajectory shift magnitudes using **Block Bootstrap** to preserve temporal autocorrelation.
 - **Output**: Append `ci_lower`, `ci_upper` to the trajectory results file.
 - **Requirement**: Ensure the CI level is explicitly stated as [deferred] and traceable to US-3 uncertainty quantification.
 - **Dependency**: Depends on T032b.
- [ ] T033a1 [P] [US3] **Calculate CI Width**: Implement `src/analysis/ci_width.py` to calculate the width of 95% CIs from T033a/T033b.
 - **Action**: Compute `ci_upper - ci_lower` for each species and compare against `config.DEFAULT_CI_WIDTH_TARGET`.
 - **Output**: Write CI width metrics to `data/processed/ci_width_report.json`.
 - **Requirement**: Satisfy SC-004 measurement.
 - **Dependency**: Depends on T033a, T033b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Orchestration & Validation (SC-001 to SC-005)

**Purpose**: Ensure sequential execution of heavy tasks and validate success criteria.

- [ ] T043 [S] **Calculate and Report All Success Criteria**: Consolidate all SC calculations into a single orchestration task.
 - **Logic**:
 1. **SC-001 (Power)**: Call `src/analysis/power_analysis.py` (T011a) to compute statistical power and effect size stability.
 2. **SC-002 (Insufficient Data)**: Call `src/analysis/insufficient_data.py` (T018 logic) to calculate the proportion of grid cells marked "insufficient data".
 3. **SC-003 (Convergence)**: Call `src/analysis/convergence_rate.py` (T027 logic) to calculate the GAMM convergence rate.
 4. **SC-004 (CI Width)**: Call `src/analysis/ci_width.py` (T033a1 logic) to calculate the width of 95% CIs.
 5. **SC-005 (Runtime)**: Call `src/analysis/runtime_validation.py` (T046 logic) to verify total runtime < 6h.
 - **Output**: Aggregate results from all sub-calculations into `data/processed/final_success_report.json`.
 - **Requirement**: Ensure all deferred targets are reported with actual values. If any target is not met, flag the result and include the specific MDES or limitation in the report.
 - **Dependency**: Depends on T011a, T018, T027, T033a, T033b, T025b, T032b, T045c.

**Checkpoint**: All success criteria calculated and reported

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `README.md` with installation instructions and `python run_pipeline.py --help` output
- [ ] T037 [P] Create `docs/api.md` with docstrings for `src/data/preprocess.py` functions
- [ ] T038a [P] Execute `ruff check src/ --fix` to remove unused imports and fix all linting errors automatically.
- [ ] T038b [P] Add a pre-commit hook for docstring validation.
 - **Action**: Add a script to check for missing docstrings and configure pre-commit.
 - **Dependency**: Depends on T038a.
- [ ] T039a1 [P] Vectorize pandas operations in `src/data/preprocess.py` to reduce loop overhead (Ensure T042d is complete first)
- [ ] T039a2 [P] Vectorize model operations in `src/models/gamm_fit.py` to reduce loop overhead (Ensure T042d is complete first)
- [ ] T039b1 [P] Implement `joblib` parallelization for permutation tests in `src/models/utils.py` to utilize multiple CPU cores (Ensure T042d is complete first)
- [ ] T039b2 [P] Implement `joblib` parallelization for other heavy tasks (Ensure T042d is complete first)
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2, EXCLUDING those dependent on T051)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: Tasks T057a and T058a are marked [S] and depend on T051; they cannot run in parallel with T051, but can run in parallel with each other once T051 is complete.

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

**⚠️ NEW CONSTRAINT**: Tasks T051a (Verify Dataset Existence) and T051 (Real Data Streaming) MUST be completed before T015b (Preprocessing) to ensure no synthetic data is ever processed.

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

- [ ] T059 [S] [US2] **Implement GPU Offload Fallback for GAMM**: Implement `src/models/gamm_fit.py` to detect `CUDA_ERROR` or `RuntimeError` during GP fitting and automatically retry on Kaggle GPU environment if available, ensuring `device="cuda"` and `load_in_8bit` are used for the retry.
 - **Action**: Wrap GAMM fitting in a try/except block that catches CUDA/Memory errors. If caught, check for Kaggle GPU environment variables. If present, re-run with `device="cuda"` and `load_in_8bit=True`.
 - **Requirement**: This ensures the "Real GPU" requirement is met when CPU fails, without fabricating a CPU-only approximation of the GP kernel.
 - **Dependency**: Depends on T061.
- [ ] T060 [S] [US3] **Implement GPU Offload Fallback for Manifold**: Implement `src/models/trajectory.py` to detect memory errors during Riemannian trajectory analysis and automatically retry on Kaggle GPU environment if available.
 - **Action**: Wrap trajectory analysis in a try/except block. If memory error occurs, check for Kaggle GPU. If present, re-run with GPU-accelerated `geomstats` backend.
 - **Requirement**: Ensures the Riemannian manifold analysis uses real GPU acceleration when needed, avoiding synthetic simplifications.
 - **Dependency**: Depends on T061.
- [ ] T061 [S] [Plan] **Update Plan.md with GPU Strategy**: Append a section to `plan.md` explicitly documenting the GPU offload strategy for T059 and T060.
 - **Action**: Add a "GPU Offload Strategy" section to `plan.md` detailing the auto-detection and retry logic for GAMM and Manifold tasks.
 - **Requirement**: Ensures the plan reflects the actual execution path for heavy computations.
 - **Dependency**: Depends on T059, T060.
- [ ] T062 [S] [US1] **Verify Data Streaming Limits**: Implement a check in `src/data/stream_utils.py` to verify that the streaming chunk size does not exceed RAM limit

The specific value to remove/generalize: 'RAM limit'

Rewritten passage:
exceed available RAM capacity.
 - **Action**: Add a runtime check that calculates estimated memory usage per chunk. If > 6 GB, raise a `MemoryError` with a suggestion to reduce chunk size.
 - **Requirement**: Prevents OOM crashes on the CI runner while ensuring real data is processed.
 - **Dependency**: Depends on T051.
- [ ] T063 [S] [US2] **Validate FDR Correction on Sparse Data**: Implement a test in `src/models/utils.py` to verify that FDR correction handles sparse data (many zeros) correctly without crashing.
 - **Action**: Run `apply_fdr_correction` on a synthetic sparse dataset with a high proportion of zeros. Assert that the output is valid and no `ZeroDivisionError` occurs.
 - **Requirement**: Ensures robustness of the statistical pipeline for species with limited data.
 - **Dependency**: Depends on T025c.
- [ ] T064 [S] [US3] **Validate Block Bootstrap Block Size**: Implement a check in `src/models/utils.py` to ensure the block size for block bootstrap is appropriate for the time series length.
 - **Action**: Add a validation step that warns if `block_size > 0.5 * time_series_length`.
 - **Requirement**: Prevents invalid bootstrapping results due to inappropriate block sizes.
 - **Dependency**: Depends on T033a.
- [ ] T065 [S] [Plan] **Document Power Analysis Limitations**: Add a section to `plan.md` explicitly stating the power limitations of the `vvud/eb-data` sample size for detecting small effect sizes.
 - **Action**: Append a "Power Analysis Limitations" section to `plan.md` referencing the sample size and expected MDES.
 - **Requirement**: Ensures transparency about the study's statistical power as required by SC-001.
 - **Dependency**: Depends on T011a.