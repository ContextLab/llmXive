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

**Purpose**: Verify plan/spec alignment and document scope limitations before any implementation begins.

- [ ] T050a [S] [Plan] **Define Deviation Whitelist Schema**:
 **Action**: Create `data/provenance/spec_plan_deviation_schema.json` defining the structure for whitelisted deviations.
 **Schema**: `{ "spec_requirement": string, "implemented_source": string, "reason": string, "timestamp": string }`.
 **Requirement**: Must be valid JSON schema.
 **Output**: `data/provenance/spec_plan_deviation_schema.json`.
 **Dependency**: None.

- [ ] T050b [S] [Plan] **Implement Plan & Spec Verification Script**:
 **Action**: Write a Python script `src/utils/verify_alignment.py` that loads `specs/001-bird-migration-climate-correlation/spec.md` and `plan.md`. The script MUST first verify that both files exist and are non-empty. It scans for contradictory statements (e.g., data source mismatches). **CRITICAL**: Before failing, the script MUST load `data/provenance/spec_plan_deviation.json` (if it exists) and treat any contradiction listed there as a "whitelisted deviation".
 **Requirement**: Fail loudly with `RuntimeError` ONLY if contradictions exist that are NOT in the deviation whitelist. If files are missing, raise `FileNotFoundError`.
 **Output**: `reports/plan_spec_alignment.json` (or failure).
 **Dependency**: T050a (Schema must exist).

## Phase 0.5: Data Source & Spec Reconciliation

**Purpose**: Explicitly document the data source substitution via a formal Spec Deviation Amendment before implementation begins.

- [ ] T005c4 [S] [Spec] **Generate Spec Deviation Amendment**:
 **Action**: Write a formal amendment document `specs/001-bird-migration-climate-correlation/amendments/FR-001-data-substitution.md` that ratifies the substitution of NOAA/PRISM with Daymet and the full eBird archive with the verified `vvud/eb-data` sample.
 **Content**: Must include: (1) Original FR-001 text, (2) Implemented source (Daymet + vvud/eb-data), (3) Justification (verified open-source availability), (4) Impact on downstream tasks, (5) Ratification timestamp (use `datetime.utcnow().isoformat()`).
 **Requirement**: This document serves as the official record of the deviation, preserving the integrity of the original spec.
 **Output**: `specs/001-bird-migration-climate-correlation/amendments/FR-001-data-substitution.md`.
 **Dependency**: None.

- [ ] T005c3 [S] **Document Data Source Deviation**: Write JSON `data/provenance/spec_plan_deviation.json` with the following EXACT structure:
 ```json
 {
 "spec_requirement": "NOAA/PRISM (FR-001)",
 "implemented_source": "Daymet",
 "reason": "Plan explicitly substitutes NOAA/PRISM with Daymet for verified open-source availability. Spec deviation ratified in FR-001-data-substitution.md (T005c4).",
 "timestamp": "<ISO8601>"
 }
 ```
 **Requirement**: Must reflect which data source was actually used; timestamp must be generated using `datetime.utcnow().isoformat()`.
 **Dependency**: T005c4 (Spec Deviation Amendment must exist).

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T002a [P] **Create Project Structure**: Execute `mkdir -p src/data src/models src/analysis src/utils src/cli data/raw data/processed data/interim tests/contract tests/unit tests/integration docs`.
- [X] T002b [P] **Verify Project Structure**: Write unit test `tests/unit/test_setup_structure.py` asserting existence of all required directories: `src/data`, `src/models`, `src/analysis`, `data/raw`, `data/processed`, `data/interim`, `tests/contract`, `tests/unit`, `tests/integration`, `docs`.
- [X] T003a_1 [P] **Create Pyproject.toml**: Create `pyproject.toml` at repository root with the following content:
```toml
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
select = ["E","F","W","I"]
ignore = []
```
- [X] T003a_2 [P] **Verify Ruff Config Syntax**: Execute `ruff check --config pyproject.toml` to verify the Ruff configuration is syntactically correct. If the command fails, the task fails.
 **Output**: Exit code 0 on success.
- [X] T003c [P] **Add Geomstats Dependency**: Append `geomstats>=2.4.0` to the `dependencies` list in `pyproject.toml` under `[project]`.
 **Requirement**: Ensure `geomstats` is available for T030/T031a/T031b/T031c.
 **Dependency**: T003a_1.
- [ ] T003b [P] **Create Pre-commit Config**: Create `.pre-commit-config.yaml` with hooks for `black` and `ruff` and add installation instructions to `README.md`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes runtime optimization to meet SC‑005 and Locking Infrastructure.

- [X] T045a [S] **Create File-Based Lock**: Implement `src/utils/locks.py` exposing `pipeline_lock = filelock.FileLock("data/interim/pipeline.lock")`.
 **Requirement**: Must be available for T023a, T025b, T031c.
 **Dependency**: None.
- [X] T045b [S] **Integrate Lock into Heavy Tasks**: Modify `src/models/gamm.py`, `src/models/utils.py` (permutation), and `src/models/trajectory.py` to acquire `pipeline_lock` before any write to shared `data/interim/` resources.
 **Requirement**: Must be integrated before T023a/T025b/T031c run.
 **Dependency**: T045a.
- [ ] T005a [S] **Verify Data Availability**:
 **Action**: Write script `src/data/verify_dataset.py` that attempts to load the verified eBird sample (`vvud/eb-data`) using `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)` and checks for Daymet availability.
 **Output**: Write `data/provenance/data_availability_report.json` with keys `{ "ebird_available": bool, "daymet_available": bool }`. Raise `RuntimeError` with clear message if eBird is missing.
 **Dependency**: None.
- [ ] T005b [S] **Download Verified eBird Sample**:
 **Action**: Stream the verified eBird sample (`vvud/eb-data`) via `datasets.load_dataset(..., streaming=True)`, write raw files to `data/raw/ebird_sample/` preserving original file names. Compute SHA‑ checksums for each downloaded shard and store in `data/raw/ebird_sample/checksums.sha256`.
 **Requirement**: No synthetic fallback; abort on any download error.
 **Dependency**: T005a.
- [ ] T005c1 [S] **Download Daymet Climate Data**:
 **Action**: Use `datasets.load_dataset("daymet/annual",...)` to download climate variables. **Action**: First verify the dataset exists via `datasets.get_dataset_names()`. If it does not exist, raise `FileNotFoundError` with message **"Daymet not available; aborting pipeline"** and exit with code 1. Write to `data/raw/daymet/` as Parquet files (`daymet_*.parquet`). Compute SHA‑256 checksums.
 **Requirement**: This is the primary and only source per updated Spec FR-001 (via T005c4). Abort if missing.
 **Dependency**: T005a.
- [ ] T005d [P] **Archive Raw Data & Upload to CI**: Copy all raw files from `data/raw/ebird_sample/` and `data/raw/daymet/` to `data/raw/archive/`. **Action**: Upload this archive to CI artifacts for provenance.
 **Requirement**: Depends on **Data Download Completion** (T005b and T005c1).
 **Dependency**: T005b, T005c1.
- [X] T005e [S] **Update State File**: Insert the new artifact hashes and `updated_at` timestamp into `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml`.
 **Dependency**: T005d.
- [X] T006 [P] **Schema test for eBird Columns**: `tests/contract/test_schemas.py::test_ebird_schema_columns` asserts that the eBird DataFrame contains columns `[species, lat, lon, date, count, checklist_id]` with correct dtypes.
- [X] T007 [S] **Implement Spatial Imputation Utility**: Write `src/data/impute.py` containing function `impute_spatial_missing(df, column, radius=1.0)`. Logic: For each missing value in `column`, find neighbors within `radius` degrees, compute weighted average (inverse distance), and fill. Return a DataFrame with an `is_imputed` boolean column.
 **Output**: `src/data/impute.py`.
 **Dependency**: None.
- [X] T009 [S] **Create Base Data Entities**: Write `src/data/entities.py` defining Pydantic models: `MigrationRecord` (species, lat, lon, date, count, checklist_id), `PhenologyMetric` (species, grid_cell, week, first_arrival_date, median_arrival_date, stopover_duration), `ClimateVariable` (grid_cell, week, mean_temperature, total_precipitation, extreme_weather_index), `Trajectory` (species, year, weekly_centroids, shift_vector).
 **Output**: `src/data/entities.py`.
- [X] T010a [S] **Define Constants**: Write `src/config.py` defining `GRID_RES=0.5`, `MIN_OBSERVATIONS=10`, `RANDOM_SEED=42`, `PERMUTATIONS=10000`, `CI_WIDTH_TARGET=7`.
 **Output**: `src/config.py`.
- [X] T010b [S] **Implement Logging**: Write `src/utils/logging.py` exposing `get_logger(name)` which returns a `logging.Logger` configured to write to `logs/pipeline.log` with JSON formatting.
 **Output**: `src/utils/logging.py`.
- [X] T010c [S] **Test Logging Format**: Write `tests/unit/test_logging.py` asserting that `get_logger('test').info(...)` writes a valid JSON line to `logs/pipeline.log`.
 **Output**: `tests/unit/test_logging.py`.
- [X] T051 [P] **Stream Verified Full eBird Data**: Implement `src/data/stream_utils.py` that uses `datasets.load_dataset(..., streaming=True)` to yield records in chunks of 100 000 rows, ensuring memory usage < 6 GB.
 **Dependency**: T005a.
- [X] T057a [S] **Implement Chunked Permutation Utility**: Write `src/models/utils.py::run_permutation_chunked` that accepts a function, iterates in chunks, and aggregates results to avoid memory overflow.
 **Output**: `src/models/utils.py`.
- [X] T058a [S] **Implement Streaming Trajectory Utility**: Write `src/models/trajectory_utils.py::stream_centroids` that yields weekly centroids from a stream of observations.
 **Output**: `src/models/trajectory_utils.py`.

## Phase 3: User Story 1 – Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

- [X] T013 [P] **Integration Test for Data Ingestion Flow**: Write `tests/integration/test_data_ingestion.py::test_end_to_end_ingestion` that mocks the download step, runs the preprocessing pipeline on a small synthetic dataset, and asserts the output schema matches `data/processed/preprocessed_data.parquet` requirements.
 **Output**: `tests/integration/test_data_ingestion.py`.
- [X] T015a [S] **Retrieve CLO Migratory List**: Write `src/data/fetch_species.py` to download the Cornell Lab of Ornithology migratory species list from the official URL, cache it in `data/raw/migratory_list.json`, and return a set of valid species names.
 **Output**: `src/data/fetch_species.py`, `data/raw/migratory_list.json`.
- [ ] T015b [S] **Implement Preprocessing Pipeline**:
 **Action**: Write `src/data/preprocess.py` to stream eBird data (using T051), filter for migratory species (recent years), aggregate to coarse-resolution grid cells, and compute phenology metrics.
 **Logic**: Use `polars` for efficient streaming. Compute `first_arrival` (min date), `median_arrival` (median date), `stopover_duration` (high quantile - low quantile). **Output column name must be `stopover_duration`**.
 **Dependency**: T051 (Streaming), T015a (Species List), T005b (Data Download).
 **Output**: `data/processed/preprocessed_data.parquet`.
- [ ] T016 [S] **Generate Provenance Mapping**:
 **Action**: Implement `src/data/preprocess.py::generate_provenance` that creates `data/provenance/row_mapping.json` mapping each processed row ID to its original `checklist_id`.
 **Schema**: `{ "processed_row_id": "SHA256(checklist_id + row_index)", "original_checklist_id": str, "species": str, "grid_cell": str }`.
 **Requirement**: Explicitly references **Constitution Principle VI (Ecological Data Provenance)** and **FR-003**. The `processed_row_id` MUST be a unique cryptographic hash of the concatenation of the original `checklist_id` and the row index within the chunk.
 **Output**: `data/provenance/row_mapping.json`.
 **Dependency**: T015b (Preprocessing must complete first to generate rows to map).
- [X] T017a [S] **Compute Phenology Metrics**: Write `src/data/preprocess.py::compute_phenology` that takes the aggregated grid data and calculates `first_arrival_date`, `median_arrival_date`, and `stopover_duration` using the logic defined in T015b.
 **Output**: `data/processed/preprocessed_data.parquet` (updated).
- [X] T017b [S] **Calculate Seasonal Climate Averages & Impute Missing Values**: Write `src/data/preprocess.py::calculate_climate_averages` to join with climate data, compute seasonal averages (Mar-May), and use `src/data/impute.py` (T007) to fill missing values. Flag imputed rows.
 **Dependency**: T007 (Imputation Utility).
 **Output**: `data/processed/preprocessed_data.parquet` (updated).
- [X] T017d [P] **Verify Imputation Metadata**: Write unit test `tests/unit/test_imputation_metadata.py::test_imputation_metadata_exists` that checks for file `data/processed/imputation_metadata.json`, validates JSON schema, and asserts that every record with `is_imputed = true` has a non‑null `imputation_source`.
 **Dependency**: T017b.
- [X] T018 [S] **Mark Insufficient Data Cells**: Write `src/data/preprocess.py::flag_insufficient_data` to mark grid cells with fewer than `MIN_OBSERVATIONS` as `data_quality="insufficient"` and exclude them from downstream modeling.
 **Output**: `data/processed/preprocessed_data.parquet` (updated).

## Phase 4: User Story 2 – Phenology‑Climate Correlation Modeling (Priority: P2)

- [X] T021 [P] **Test GAMM Output Schema**: `tests/contract/test_gamm_schemas.py::test_gamm_output_schema` validates `data/processed/model_results_final.parquet` contains keys `{ "species", "temp_coef", "precip_coef", "p_value", "converged" }`.
 **Output**: `tests/contract/test_gamm_schemas.py`.
- [X] T022 [P] **Integration Test for GAMM Convergence**: `tests/integration/test_gamm_convergence.py::test_gamm_convergence` runs GAMM on a small synthetic dataset and asserts the `converged` flag is True for known parameters.
 **Output**: `tests/integration/test_gamm_convergence.py`.
- [ ] T023a [S] **Fit GAMM with Mandatory GP Random Effect**:
 **Action**: Write `src/models/gamm.py::fit_gamm` that reads `data/processed/preprocessed_data.parquet`.
 **Library**: `pygam`.
 **Formula**: `phenology_metric ~ s(temp) + s(precip) + s(extreme_weather_index) + (1 + temp | species_year) + gp(spatial)`.
 **Logic**: 
 1. Generate `species_year` identifiers by combining species and year columns.
 2. Fit GAMM **with** Gaussian Process (GP) random effect (Matérn kernel) **a priori** for all fits.
 3. Acquire `data/interim/pipeline.lock` (via `filelock.FileLock`) before writing model results.
 **Output**: `data/processed/model_results_final.parquet` (always includes GP).
 **Dependency**: T015b (preprocessed data), T045a (Lock).
- [X] T023d [S] **Compute Moran’s I Diagnostic (Non-Blocking)**:
 **Action**: Write `src/models/gamm.py::compute_morans_i` that takes the preprocessed data and the results from T023a to compute Moran's I for spatial autocorrelation of residuals.
 **Requirement**: This is a diagnostic only; it does NOT gate the model fit.
 **Output**: `data/interim/morans_i_result.json` with schema `{"value": float}`.
 **Dependency**: T023a (GAMM fit must complete first to provide residuals).
- [X] T025a [S] **Benchmark Permutation Test**: Write `src/models/utils.py::benchmark_permutation` to run multiple shuffles and estimate runtime per 1000 shuffles. Store in `data/processed/permutation_benchmark.json`.
 **Output**: `data/processed/permutation_benchmark.json`.
- [ ] T025b [S] **Permutation Test Loop**: Execute a substantial number of permutations (config.PERMUTATIONS) in chunks of 1 000 using `src/models/utils.run_permutation_chunked`. Acquire `data/interim/pipeline.lock` before writing results. **Use `config.RANDOM_SEED` for all shuffles**. Output to `data/processed/permutation_results.json`.
 **Output**: `data/processed/permutation_results.json`.
 **Dependency**: T023a (Final model output).
- [ ] T025c [S] **Apply FDR Correction**: Implement `src/models/utils.py::apply_fdr_correction` that takes the **permutation test output** (T025b), aggregates **all species-climate coefficient p-values**, applies Benjamini‑Hochberg, adds a `q_value` column, and writes `data/processed/model_results_fdr.parquet`.
 **Dependency**: T025b and T023a.
- [X] T027 [S] **Implement Convergence Error Handling**: Wrap GAMM fitting in `try/except`. On convergence failure, log `"Convergence failed for species {species}: {error}"` to `logs/modeling.log` and skip that species. Add unit test `tests/unit/test_convergence_handling.py` verifying log format.
 **Dependency**: T023a.

## Phase 5: User Story 3 – Route Shift Analysis and Uncertainty Quantification (Priority: P3)

- [ ] T028 [P] **Test Trajectory Output Schema**: `tests/contract/test_trajectory_schemas.py::test_trajectory_output_schema` validates `data/processed/trajectory_results.json` contains keys `{ "species", "year", "shift_magnitude", "shift_direction", "p_value" }`.
 **Output**: `tests/contract/test_trajectory_schemas.py`.
- [X] T029 [P] **Integration Test for Route Shift Detection**: `tests/integration/test_trajectory_analysis.py::test_route_shift_detection` runs the full trajectory pipeline on a synthetic null dataset and asserts `p_value > 0.05`.
 **Output**: `tests/integration/test_trajectory_analysis.py`.
- [ ] T030 [S] **Compute Weekly Migration Centroids (Fréchet Mean)**:
 **Action**: Implement `src/models/trajectory.py::compute_weekly_centroids` that aggregates preprocessed observations per species‑year per week.
 **Library**: **MANDATORY** `import geomstats`. If `geomstats` is not available, raise `ModuleNotFoundError`.
 **Algorithm**: Use `geomstats.geometry.sphere.Sphere(dim=2, metric='intrinsic')`. Compute the **Fréchet mean** (geodesic mean) for each week's coordinates using iterative optimization (e.g., `sphere.mean()`) rather than simple arithmetic mean.
 **Output**: `data/interim/weekly_centroids.parquet`.
 **Dependency**: T015b (preprocessed data), T003c (geomstats dependency).
- [ ] T031a [S] **Compute Manifold-Based Trajectory Statistics**:
 **Library**: **MANDATORY** `import geomstats`. If `geomstats` is not available, raise `ModuleNotFoundError`.
 **Action**: Use `geomstats.geometry.sphere.Sphere(dim=2, metric='intrinsic')` to compute trajectory-level statistics on the Riemannian manifold.
 **Logic**: 
 1. Compute **Fréchet variance** for each species-year trajectory using the centroids from T030.
 2. Perform **geodesic regression** to model trajectory evolution over time.
 3. Calculate **parallel transport** of velocity vectors between years to detect non-linear shifts.
 **Output**: `data/interim/trajectory_statistics.json` containing `fréchet_variance`, `geodesic_regression_coefficients`, `parallel_transport_vectors`.
 **Dependency**: T030 (weekly centroids).
- [ ] T031b [S] **Detect Spatial Route Shifts Using Manifold Statistics**:
 **Library**: **MANDATORY** `import geomstats`.
 **Action**: Use the manifold statistics computed in T031a (Fréchet variance, geodesic regression coefficients) to detect spatial route shifts.
 **Logic**: 
 1. Compare trajectories across years using the geodesic regression coefficients and parallel transport vectors from T031a.
 2. Calculate the **shift vector** (magnitude and direction) based on the difference in geodesic regression parameters.
 3. Prepare the data structure for the permutation test in T031c.
 **Output**: `data/interim/shift_candidates.json` containing `species`, `year`, `shift_vector`, `magnitude`, `direction`.
 **Dependency**: T031a (Manifold Statistics).
- [ ] T031c [S] **Riemannian Manifold Trajectory Analysis & Permutation**:
 **Library**: **MANDATORY** `import geomstats`. If `geomstats` is not available, raise `ModuleNotFoundError`.
 **Action**: Use `geomstats.geometry.sphere.Sphere(dim=2, metric='intrinsic')` for geodesic distances. For each species, perform **a sufficient number of permutation shuffles** on the **shift vectors** generated in T031b to derive the p-value.
 **Test**: Use `geomstats.learning.frechet_mean` for trajectory comparison and `geomstats.stats` for permutation testing. **Explicitly use manifold-based trajectory statistics from T031a and shift candidates from T031b to detect spatial route shifts**.
 **Output**: `data/processed/trajectory_results.json` containing `shift_vector`, `magnitude`, `direction`, and `p_value`.
 **Dependency**: T030, T031a, T031b.
- [ ] T033a [S] **Generate Phenology Confidence Intervals**: Implement block bootstrap (preserving weekly autocorrelation) on **GAMM model predictions**, produce `ci_lower` and `ci_upper` columns in `data/processed/model_results_fdr.parquet`.
 **Dependency**: T023a (model fits).
- [ ] T033b [S] **Generate Trajectory Confidence Intervals**: Apply block bootstrap to shift magnitudes from `trajectory_results.json`, append `ci_lower`/`ci_upper` to each record, and write to `data/processed/trajectory_results_ci.json`.
 **Dependency**: T031c.
- [ ] T033a1 [S] **Calculate CI Width Metrics**: Compute `ci_width = ci_upper - ci_lower` for each phenology and trajectory CI, compare against `config.DEFAULT_CI_WIDTH_TARGET` (for reporting only), and write summary to `data/processed/ci_width_report.json`.
 **Dependency**: T033a and T033b.

## Phase 6: Orchestration & Validation (SC‑001 to SC‑005)

- [ ] T043a [S] **Define Success Criteria Targets**: Write `src/analysis/targets.py::define_targets` to read `plan.md` fallback criteria (**Input: plan.md**) and write `data/processed/target_definitions.json` with concrete thresholds for `sc002_target` ([deferred]), `sc003_target` ([deferred]), and `sc004_target` (7 days). **Note**: These targets resolve the `[deferred]` placeholders in the spec.
 **Dependency**: None.
- [ ] T043b [S] **Implement Power Analysis Script**: Write `src/analysis/power_analysis.py` to calculate statistical power and effect size stability (SC-001) based on the total number of migratory species and model results. Output `data/processed/power_report.json`.
 **Dependency**: T023a (model fits).
- [ ] T043c1 [S] **Measure SC-002 (Insufficient Data Proportion)**:
 **Action**: Read `data/processed/preprocessed_data.parquet` (from T018), count rows with `data_quality="insufficient"`, and calculate the proportion of total grid cells. Compare against `data/processed/target_definitions.json` (SC-002 target).
 **Output**: `data/processed/insufficient_data_report.json` containing `total_cells`, `insufficient_cells`, `proportion`, `target`, `pass/fail`.
 **Requirement**: Explicitly generates the `metadata_insufficient_cells.json` artifact referenced by T043.
 **Dependency**: T018, T043a.
- [ ] T043c2 [S] **Measure SC-003 (Convergence Rate)**:
 **Action**: Read `logs/modeling.log` and `data/processed/model_results_final.parquet` to compute convergence rate (successful fits / total attempts). Compare against `data/processed/target_definitions.json` (SC-003 target).
 **Output**: `data/processed/convergence_report.json` containing `total_attempts`, `successful_fits`, `convergence_rate`, `target`, `pass/fail`.
 **Dependency**: T027, T043a.
- [ ] T043d [S] **Calculate CI Width Metrics**: Read `data/processed/ci_width_report.json` and compare against `data/processed/target_definitions.json`. Store in `data/processed/ci_width_target_report.json`.
 **Dependency**: T033a1 and T043a.
- [ ] T043 [S] **Calculate and Report All Success Criteria**:
 **Logic**:
 1. **SC‑001 (Power)** – Use output from T043b.
 2. **SC‑002 (Insufficient Data)** – Use output from T043c1 (which generates `data/processed/metadata_insufficient_cells.json`).
 3. **SC‑003 (Convergence)** – Use output from T043c2.
 4. **SC‑004 (CI Width)** – Use output from T043d.
 5. **SC‑005 (Runtime)** – Run `src/analysis/runtime_validation.py` to ensure total pipeline runtime < 6 h; store result in `data/processed/runtime_report.json`.
 **Aggregated Output**: Combine all five JSON reports into a single `data/processed/final_success_report.json`.
 **Requirement**: All targets are now defined in `target_definitions.json`.
 **Dependency**: T043a, T043b, T043c1, T043c2, T043d, T025c, T027, T033a1, and all preceding analysis tasks.

## Phase 7: Polish & Cross‑Cutting Concerns

- [ ] T036 [P] **Update README** with installation instructions and `python -m src.cli.run_pipeline --help`.
- [ ] T037 [P] **Create docs/api.md** with docstrings for all public functions in `src/data/preprocess.py`.
- [ ] T038a [P] **Run Ruff Auto‑Fix** on `src/`.
- [ ] T038b [P] **Add Pre‑commit Hook for Docstring Validation**.
- [ ] T039a1 [P] **Vectorize pandas operations in `src/data/preprocess.py`**: Target: **reduce runtime** for aggregation steps. **Verification**: Verify runtime < 6h and stop when no further improvement > 1% is observed.
 **Dependency**: T018.
- [ ] T039a2 [P] **Vectorize model operations in `src/models/gamm_fit.py`**: Target: **reduce runtime by %** per species fit. **Verification**: Verify runtime < 6h and stop when no further improvement > 1% is observed.
 **Dependency**: T023a.
- [ ] T039b1 [P] **Parallelize permutation tests with joblib**: Target: **achieve < 500ms per chunk**.
 **Dependency**: T025b.
- [ ] T039b2 [P] **Parallelize trajectory permutation tests with joblib**: Target: **achieve < 1000ms per species**.
 **Dependency**: T031c.
- [ ] T040a [P] **Add unit test for empty input in `src/data/preprocess.py`**.
- [ ] T040b [P] **Add unit test for single species in `src/models/gamm_fit.py`**.
- [ ] T040c [P] **Add unit test for missing data handling in `src/data/impute.py`**.
- [ ] T041a [P] **Create `.github/workflows/ci.yml`**.
- [ ] T041b [P] **Define `validate_quickstart` job in CI workflow**.
- [ ] T041c [P] **Add runtime assertion (< 6 h) to `validate_quickstart` job**.

## Phase 8: Reporting & Documentation (Moved from Phase 7)

**Purpose**: Final reporting and documentation updates.

- [ ] T045c [S] **Document Lock Usage**: Add section to `docs/locking.md` describing when and how the lock is used, and update any relevant README sections.
 **Dependency**: T045b.