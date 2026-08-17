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

## Phase 0: Pre-Implementation & Spec Alignment

**Purpose**: Verify plan/spec alignment and document scope limitations before any implementation begins.

- [ ] T005c4 [S] [Spec] **Document Plan Deviation from Spec**:
 **Action**: Write a formal deviation document `specs/001-bird-migration-climate-correlation/amendments/PLAN-DEVIATION-DATA-SOURCES.md` that documents the Plan's explicit substitution of NOAA/PRISM with Daymet and the full eBird archive with the verified `vvud/eb-data` sample.
 **Content**: Must include: (1) Original Spec FR-001 text, (2) Plan's implemented source (Daymet + vvud/eb-data), (3) Justification (Plan states verified open-source availability), (4) Impact on downstream tasks, (5) Ratification timestamp (use `TIMESTAMP_PLACEHOLDER` and update at runtime via `python src/cli/update_ratification_timestamps.py --file specs/001-bird-migration-climate-correlation/amendments/PLAN-DEVIATION-DATA-SOURCES.md --timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)`).
 **Requirement**: This document serves as the official record of the Plan's deviation from the Spec. The Spec remains unchanged and is the single source of truth for implementation.
 **Output**: `specs/001-bird-migration-climate-correlation/amendments/PLAN-DEVIATION-DATA-SOURCES.md`.
 **Dependency**: None.

- [ ] T005c3 [S] **Document Data Source Deviation**: Write JSON `data/provenance/spec_plan_deviation.json` with the following EXACT structure:
 ```json
 {
 "spec_requirement": "NOAA/PRISM (FR-001)",
 "implemented_source": "Daymet",
 "reason": "Plan explicitly substitutes NOAA/PRISM with Daymet for verified open-source availability. Spec deviation ratified in PLAN-DEVIATION-DATA-SOURCES.md (T005c4).",
 "timestamp": "TIMESTAMP_PLACEHOLDER"
 }
 ```
 **Requirement**: Must reflect which data source was actually used; timestamp must be generated at runtime via Python script `src/data/generate_provenance.py` that calls `datetime.utcnow().isoformat()` at execution time, replacing `TIMESTAMP_PLACEHOLDER`. This generation MUST happen at runtime via a Python script. Do NOT hardcode the timestamp. The script will be invoked after T005c4 completes. This JSON file is used by T005c1b_primary and T005c1_daymet to determine which climate data source to use. It serves as the single source of truth for the data source decision throughout the pipeline.
 **Dependency**: T005c4 (Deviation document must exist first).

- [ ] T005c5 [S] **Pre-Execution Ordering Validator**:
 **Action**: Write script `src/cli/validate_task_order.py` that parses `tasks.md` and verifies that all "verify" or "test" tasks (e.g., T013, T021) appear AFTER their producer tasks (e.g., T015b, T023a) in the dependency graph.
 **Logic**: If any verify task depends on a task that has not been executed (or is listed after it in the file), raise `RuntimeError` with message "Task ordering violation: <task_id> must run after <producer_id>".
 **Requirement**: This task runs BEFORE any pipeline execution. It prevents the pipeline from starting if `tasks.md` is malformed.
 **Output**: Exit code 0 on success, 1 on failure.
 **Dependency**: None.

## Phase 0.5: Data Source & Spec Reconciliation

**Purpose**: Implement the Spec's primary data requirements (NOAA/PRISM) as the default path. The Plan's deviation (Daymet) is implemented only if the deviation document exists AND is ratified.

- [X] T005a [S] **Verify Data Availability**:
 **Action**: Write script `src/data/verify_dataset.py` that attempts to load the verified eBird sample (`vvud/eb-data`) using `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)` and checks for NOAA/PRISM and Daymet availability.
 **Output**: Write `data/provenance/data_availability_report.json` with keys `{ "ebird_available": bool, "noaa_available": bool, "daymet_available": bool }`. Raise `RuntimeError` with clear message if eBird is missing.
 **Dependency**: None.

- [X] T005b [S] **Download Verified eBird Sample**:
 **Action**: Stream the verified eBird sample (`vvud/eb-data`) via `datasets.load_dataset(..., streaming=True)`, write raw files to `data/raw/ebird_sample/` preserving original file names. Compute SHA‑ checksums for each downloaded shard and store in `data/raw/ebird_sample/checksums.sha256`.
 **Requirement**: No synthetic fallback; abort on any download error.
 **Dependency**: T005a.

- [ ] T005c1b_primary [S] **Download NOAA/PRISM Climate Data (Spec Primary)**:
 **Action**: Implement `src/data/download.py::fetch_noaa_prism` to download NOAA/PRISM climate data for North America (recent years). This is the Spec's primary requirement per FR-001.
 **Logic**:
 1. Verify the existence of `specs/001-bird-migration-climate-correlation/amendments/PLAN-DEVIATION-DATA-SOURCES.md` AND verify it contains a valid ratification timestamp (ISO format) AND verify it contains a 'status' field set to 'ratified'. Only if all three conditions are met, skip NOAA/PRISM download. If any condition fails, proceed with NOAA/PRISM download regardless.
 2. Attempt to download NOAA/PRISM data from the official NOAA/PRISM API or verified mirror.
 3. Write to `data/raw/noaa_prism/` as NetCDF or Parquet files. Compute SHA‑ checksums.
 4. If download fails, raise `RuntimeError` with message "NOAA/PRISM download failed; unable to proceed with Spec FR-001 primary requirement" and exit.
 5. Use `src.utils.logging.get_logger(__name__).info("Plan deviation ratified; skipping NOAA/PRISM primary fetch")` if skipping. The logging level is INFO.
 **Requirement**: This is the primary task for climate data as per Spec FR-001. It only skips if the Plan's deviation is ratified with all validation checks passing.
 **Output**: `data/raw/noaa_prism/` (if successful) or error log.
 **Dependency**: T005a, T005c4.

- [ ] T005c1_daymet [S] **Download Daymet Climate Data (Plan Deviation Fallback)**:
 **Action**: Use `datasets.load_dataset("daymet/annual", variables=["prcp", "tmin", "tmax", "srad", "vp"], state="ALL", year=["2021", "2022", "2023", "2024"])` to download climate variables.
 **Logic**:
 1. Check for the existence of file `specs/001-bird-migration-climate-correlation/amendments/PLAN-DEVIATION-DATA-SOURCES.md` AND verify it contains the JSON field `{"implemented_source": "Daymet"}`. Only proceed with Daymet download if both conditions are true AND T005c1b_primary has failed with a verified-unavailable status (i.e., NOAA/PRISM is confirmed unavailable from official sources).
 2. Write to `data/raw/daymet/` as Parquet files (`daymet_*.parquet`). Compute SHA‑ checksums.
 **Requirement**: This task runs ONLY if the Plan's deviation is ratified AND the primary source (NOAA/PRISM) is verified unavailable. It is not the primary source per Spec FR-001.
 **Output**: `data/raw/daymet/` (if successful) or error log.
 **Dependency**: T005a, T005c4, T005c1b_primary.

- [X] T005d1 [S] **Archive Raw Data (Local)**: Copy all raw files from `data/raw/ebird_sample/`, `data/raw/daymet/` (if exists), and `data/raw/noaa_prism/` (if exists) to `data/raw/archive/`.
 **Requirement**: Depends on **Data Download Completion** (T005b, T005c1_daymet, T005c1b_primary). If T005c1_daymet or T005c1b_primary produces no artifact, archive only existing directories.
 **Output**: `data/raw/archive/`.
 **Dependency**: T005b, T005c1_daymet, T005c1b_primary.

- [X] T005d2 [S] **Configure CI Artifact Upload**: Write `src/cli/upload_ci.py` to generate the CI workflow snippet for uploading `data/raw/archive/` as artifacts. This task creates the configuration, not the upload itself (which is handled by CI).
 **Requirement**: Must be executable locally to generate the YAML snippet.
 **Output**: `ci/upload_artifacts.yml` (snippet).
 **Dependency**: T005d1.

- [X] T005e [S] **Update State File**: Insert the new artifact hashes and `updated_at` timestamp into `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml`.
 **Dependency**: T005d1.

- [X] T006 [P] **Schema test for eBird Columns**: `tests/contract/test_schemas.py::test_ebird_schema_columns` asserts that the eBird DataFrame contains columns `[species, lat, lon, date, count, checklist_id]` with correct dtypes.
 **Dependency**: T005b.

- [X] T007 [P] **Implement Spatial Imputation Utility**: Write `src/data/impute.py` containing function `impute_spatial_missing(df, column, radius=1.0)`. Logic: For each missing value in `column`, find neighbors within `radius` degrees, compute weighted average (inverse distance), and fill. Return a DataFrame with an `is_imputed` boolean column.
 **Output**: `src/data/impute.py`.
 **Dependency**: None.

- [X] T009 [P] **Create Base Data Entities**: Write `src/data/entities.py` defining Pydantic models: `MigrationRecord` (species, lat, lon, date, count, checklist_id), `PhenologyMetric` (species, grid_cell, week, first_arrival_date, median_arrival_date, stopover_duration), `ClimateVariable` (grid_cell, week, mean_temperature, total_precipitation, extreme_weather_index), `Trajectory` (species, year, weekly_centroids, shift_vector).
 **Output**: `src/data/entities.py`.

- [X] T010a [P] **Define Constants**: Write `src/config.py` defining `GRID_RES=0.5`, `MIN_OBSERVATIONS=10`, `RANDOM_SEED=42`, `PERMUTATIONS=10000`, `CI_WIDTH_TARGET=7`.
 **Output**: `src/config.py`.

- [X] T010b [P] **Implement Logging**: Write `src/utils/logging.py` exposing `get_logger(name)` which returns a `logging.Logger` configured to write to `logs/pipeline.log` with JSON formatting.
 **Output**: `src/utils/logging.py`.

- [X] T010c [P] **Test Logging Format**: Write `tests/unit/test_logging.py` asserting that `get_logger('test').info(...)` writes a valid JSON line to `logs/pipeline.log`.
 **Output**: `tests/unit/test_logging.py`.
 **Dependency**: T010b.

- [X] T051 [P] **Stream Verified Full eBird Data**: Implement `src/data/stream_utils.py` that uses `datasets.load_dataset(..., streaming=True)` to yield records in chunks of rows, ensuring memory usage < 6 GB.
 **Dependency**: T005a.

- [X] T057a [P] **Implement Chunked Permutation Utility**: Write `src/models/utils.py::run_permutation_chunked` that accepts a function, iterates in chunks, and aggregates results to avoid memory overflow.
 **Output**: `src/models/utils.py`.
 **Dependency**: None.

- [X] T058a [P] **Implement Streaming Trajectory Utility**: Write `src/models/trajectory_utils.py::stream_centroids` that yields weekly centroids from a stream of observations.
 **Output**: `src/models/trajectory_utils.py`.
 **Dependency**: None.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T002a [P] **Create Project Structure**: Execute `mkdir -p src/data src/models src/analysis src/utils src/cli data/raw data/processed data/interim tests/contract tests/unit tests/integration docs`.
 **Requirement**: All directories MUST exist.
 **Output**: File system structure created.
 **Dependency**: None.

- [X] T002b [P] **Verify Project Structure**: Write unit test `tests/unit/test_setup_structure.py` asserting existence of all required directories: `src/data`, `src/models`, `src/analysis`, `data/raw`, `data/processed`, `data/interim`, `tests/contract`, `tests/unit`, `tests/integration`, `docs`.
 **Dependency**: T002a.

- [X] T003a_1 [P] **Create Pyproject.toml**: Create `pyproject.toml` at repository root with the following content:
```toml
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ["py"]

[tool.ruff]
select = ["E","F","W","I"]
ignore = []
```
 **Dependency**: None.

- [X] T003a_2 [P] **Verify Ruff Config Syntax**: Execute `ruff check --config pyproject.toml` to verify the Ruff configuration is syntactically correct. If the command fails, the task fails.
 **Output**: Exit code 0 on success.
 **Dependency**: T003a_1.

- [X] T003c [P] **Add Geomstats Dependency**: Append `geomstats>=2.4.0` to the `dependencies` list in `pyproject.toml` under `[project]`.
 **Requirement**: Ensure `geomstats` is available for T030/T031a_manifold/T031b_manifold/T031c_permutation (Riemannian manifold operations).
 **Dependency**: T003a_1.

- [ ] T003b [P] **Create Pre-commit Config**: Create `.pre-commit-config.yaml` with hooks for `black` and `ruff` and add installation instructions to `README.md`.
 **Action**: If `README.md` does not exist, create a minimal one first. Add "python -m src.cli.run_pipeline --help" to the installation section.
 **Dependency**: T003a_1, T002a.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes runtime optimization to meet SC‑005 and Locking Infrastructure.

- [X] T045a [S] **Create File-Based Lock**: Implement `src/utils/locks.py` exposing `pipeline_lock = filelock.FileLock("data/interim/pipeline.lock")`.
 **Requirement**: Must be available for T023a_gp, T025b_spatial, T025d, T031c_permutation.
 **Dependency**: None.

- [X] T045b [S] **Integrate Lock into Heavy Tasks**: Modify `src/models/gamm.py`, `src/models/utils.py` (permutation), and `src/models/trajectory.py` to acquire `pipeline_lock` before any write to shared `data/interim/` resources.
 **Requirement**: Must be integrated before T023a_gp/T025b_spatial/T025d/T031c_permutation run.
 **Dependency**: T045a.

## Phase 3: User Story 1 – Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

- [ ] T013 [S] [US1] **Integration Test for Data Ingestion Flow**:
 **Action**: Write `tests/integration/test_data_ingestion.py::test_end_to_end_ingestion`.
 **Mock Strategy**: Use `pytest-mock` to patch `datasets.load_dataset` and `src.data.download.fetch_noaa_prism` to return a small, synthetic JSON fixture with multiple rows of eBird data and 1 row of climate data.
 **Fixture Schema**: Create fixture file `tests/fixtures/mock_ebird_climate.json` with the following structure: `{"records": [{"species": str, "lat": float, "lon": float, "date": str (YYYY-MM-DD), "count": int, "checklist_id": str}, ...], "climate": [{"grid_cell": str, "week": int, "mean_temperature": float, "total_precipitation": float}, ...]}`. Use a limited number of eBird records and one climate record for the mock.
 **Logic**: Run the preprocessing pipeline (T015b) on this mocked data.
 **Assertion**: Assert that the output `data/processed/preprocessed_data.parquet` exists and contains the exact schema: `[species, grid_cell, week, first_arrival_date, median_arrival_date, stopover_duration, mean_temperature, total_precipitation, data_quality]` with correct dtypes and no missing values in critical fields.
 **Requirement**: This task is Sequential [S] as it depends on the completed T015b artifact.
 **Output**: `tests/integration/test_data_ingestion.py`.
 **Dependency**: T015b.

- [X] T015a [S] **Retrieve CLO Migratory List**: Write `src/data/fetch_species.py` to download the Cornell Lab of Ornithology migratory species list from the official URL, cache it in `data/raw/migratory_list.json`, and return a set of valid species names.
 **Output**: `src/data/fetch_species.py`, `data/raw/migratory_list.json`.
 **Dependency**: None.

- [ ] T015b [S] **Implement Preprocessing Pipeline**:
 **Action**: Write `src/data/preprocess.py` to stream eBird data (using T051), filter for migratory species (recent years), aggregate to a regular grid resolution, and compute phenology metrics.
 **Logic**: Use `polars` for efficient streaming.
 1. **Binning**: Use `numpy.floor(lat / bin_size) * bin_size` and `numpy.floor(lon / 0.5) * 0.5` to create `grid_cell` strings (e.g., "45.0_-120.5").
 2. **Aggregation**: Group by `species`, `grid_cell`, `year`, `week`.
 3. **Phenology Metrics**: Compute `first_arrival` (min date), `median_arrival` (median date), `stopover_duration` (90th percentile date - 10th percentile date of dates).
 4. **Intermediate Output**: Write intermediate grid-binned data to `data/interim/grid_binned.parquet`.
 5. **Phenology Output**: Write intermediate phenology data to `data/interim/phenology_raw.parquet` with schema: `[species, grid_cell, year, week, first_arrival_date, median_arrival_date, stopover_duration]`.
 6. **Climate Join**: Join with NOAA/PRISM (or Daymet if deviation exists) data on `grid_cell` and `week`.
 7. **Imputation**: Use `src/data/impute.py` (T007) to fill missing climate values. Flag imputed rows.
 8. **Final Output**: Write final processed data to `data/processed/preprocessed_data.parquet`.
 **Output**: `data/processed/preprocessed_data.parquet`.
 **Requirement**: Must handle edge cases (e.g., grid cells with < MIN_OBSERVATIONS) by marking them as `data_quality="insufficient"` but NOT excluding them yet.
 **Dependency**: T051 (Streaming), T015a (Species List), T005b (Data Download), T005c1b_primary (NOAA/PRISM) or T005c1_daymet (Daymet).

- [ ] T016 [S] **Generate Provenance Mapping**:
 **Action**: Implement `src/data/preprocess.py::generate_provenance` that creates `data/provenance/row_mapping.json` mapping each processed row ID to its original `checklist_id`.
 **Schema**: `{ "processed_row_id": "SHA256(checklist_id + row_index)", "original_checklist_id": str, "species": str, "grid_cell": str }`.
 **Hash Generation**: Compute `processed_row_id = hashlib.sha256((checklist_id + ":::" + str(row_index)).encode("utf-8")).hexdigest()`. The delimiter is two colons (::); encoding is UTF-8; byte order is native (no special handling required).
 **Requirement**: Explicitly references **Constitution Principle VI (Ecological Data Provenance)** and **FR-003**. The `processed_row_id` MUST be a unique cryptographic hash of the concatenation of the original `checklist_id` and the row index within the chunk.
 **Output**: `data/provenance/row_mapping.json`.
 **Dependency**: T015b (Preprocessing must complete first, BEFORE T018).

- [X] T018 [S] **Mark Insufficient Data Cells**: Write `src/data/preprocess.py::flag_insufficient_data` to mark grid cells with fewer than `MIN_OBSERVATIONS` as `data_quality="insufficient"` and exclude them from downstream modeling.
 **Output**: `data/processed/preprocessed_data.parquet` (updated).
 **Dependency**: T016 (Provenance must be generated first).

- [X] T017d [P] **Verify Imputation Metadata**: Write unit test `tests/unit/test_imputation_metadata.py::test_imputation_metadata_exists` that checks for file `data/processed/imputation_metadata.json`, validates JSON schema, and asserts that every record with `is_imputed = true` has a non‑null `imputation_source`.
 **Dependency**: T015b.

## Phase 4: User Story 2 – Phenology‑Climate Correlation Modeling (Priority: P2)

- [X] T021 [P] **Test GAMM Output Schema**: `tests/contract/test_gamm_schemas.py::test_gamm_output_schema` validates `data/processed/model_results_final.parquet` contains keys `{ "species", "temp_coef", "precip_coef", "p_value", "converged" }`.
 **Output**: `tests/contract/test_gamm_schemas.py`.
 **Dependency**: T023a.

- [X] T022 [P] **Integration Test for GAMM Convergence**: `tests/integration/test_gamm_convergence.py::test_gamm_convergence` runs GAMM on a small synthetic dataset and asserts the `converged` flag is True for known parameters.
 **Output**: `tests/integration/test_gamm_convergence.py`.
 **Dependency**: T023a.

- [ ] T023a [S] **Fit GAMM with Species-Specific Random Slopes**:
 **Action**: Write `src/models/gamm.py::fit_gamm` that reads `data/processed/preprocessed_data.parquet`.
 **Library**: `pygam` or `statsmodels`.
 **Logic**:
 1. **Base Fit**: Fit model with formula `phenology_metric ~ s(temp) + s(precip) + s(extreme_weather_index) + (1 + temp | species + year)`.
 2. **Random Effects**: Include species-year random intercepts and species-specific random slopes for temperature as per Spec FR-004.
 3. **Locking**: Acquire `data/interim/pipeline.lock` (via `filelock.FileLock`) before writing model results.
 **Output**: `data/processed/model_results_final.parquet` (includes random effects).
 **Requirement**: Random effect MUST be `(1 + temp | species + year)`.
 **Dependency**: T015b (preprocessed data), T045a (Lock).

- [ ] T023a_gp [S] **Fit GAMM with Mandatory A Priori Gaussian Process Random Effect**:
 **Action**: After T023a completes, enhance the fitted GAMM by adding a **mandatory a priori** Gaussian Process (GP) random effect with Matérn covariance function (nu=2.5) to the model. This is a hard requirement per Spec FR-004.
 **Logic**:
 1. Use `sklearn.gaussian_process.GaussianProcessRegressor` or `statsmodels` GP functionality.
 2. Fit the GP on the residuals from T023a.
 3. Include the GP as a random effect in the final model.
 4. Acquire `data/interim/pipeline.lock` before writing updated results.
 **Output**: `data/processed/model_results_final.parquet` (updated with GP).
 **Requirement**: GP MUST be included a priori for all models, not conditionally. This is a Spec MUST requirement.
 **Dependency**: T023a (GAMM fit must complete first), T045a (Lock).

- [X] T023d [S] **Compute Moran's I Diagnostic (Non-Blocking)**:
 **Action**: Write `src/models/gamm.py::compute_morans_i` that takes the preprocessed data and the results from T023a to compute Moran's I for spatial autocorrelation of residuals.
 **Requirement**: This is a diagnostic only; it does NOT gate the model fit or GP inclusion. The GP is mandatory a priori (T023a_gp).
 **Output**: `data/interim/morans_i_result.json` with schema `{"value": float}`.
 **Dependency**: T023a (GAMM fit must complete first to provide residuals).

- [X] T025a [P] **Benchmark Permutation Test**: Write `src/models/utils.py::benchmark_permutation` to run multiple shuffles and estimate runtime per 1000 shuffles. Store in `data/processed/permutation_benchmark.json`.
 **Output**: `data/processed/permutation_benchmark.json`.
 **Dependency**: T023a.

- [ ] T025b_spatial [S] **Permutation Test for Spatial Shift Vectors**: Execute **exactly 10,000** permutation shuffles (as mandated by Spec FR-005) in chunks of a fixed size using `src/models/utils.run_permutation_chunked`. Acquire `data/interim/pipeline.lock` before writing results. **Use `config.RANDOM_SEED` for all shuffles**. If runtime constraints are exceeded, apply the fallback mechanism defined in T053_fallback.
 **Logic**: Shuffle species-year labels relative to shift vectors. Test statistic: Euclidean distance between mean shift vector of observed data and mean shift vector of permuted data.
 **Input**: `data/processed/shift_vectors.json` (output of T031b_manifold).
 **Output**: `data/processed/permutation_results_spatial.json`.
 **Schema**: `{ "species": str, "shuffle_id": int, "p_value": float, "raw_stat": float }`.
 **Requirement**: Must perform 10000 shuffles as per Spec FR-005. If runtime exceeds 6 hours, apply T053_fallback.
 **Dependency**: T023a_gp (Final model output), T025a (Benchmark), T045a (Lock), T031b_manifold (Shift vectors must be generated first).

- [ ] T025d [S] **Permutation Test for GAMM Coefficients**: Execute **exactly 10,000** permutation shuffles (as mandated by Spec FR-005) on **species-climate coefficients**. Use `src/models/utils.run_permutation_chunked`. Acquire `data/interim/pipeline.lock`. If runtime constraints are exceeded, apply the fallback mechanism defined in T053_fallback.
 **Logic**: Shuffle response variables (phenology metrics) relative to climate predictors. Test statistic: Absolute value of the coefficient for temperature/precip. Perform permutation tests on species-climate coefficients (temperature and precipitation) extracted from the fitted GAMM (T023a). This tests the association between phenology metrics and climate variables as specified in Spec FR-005 and US-2 Acceptance Scenario 1. The permutation is performed by shuffling the response variable (phenology metric) relative to the predictors (climate variables).
 **Input**: `data/processed/model_results_final.parquet` (T023a_gp).
 **Output**: `data/processed/permutation_results_coefficients.json`.
 **Schema**: `{ "species": str, "coefficient": str, "shuffle_id": int, "p_value": float, "raw_stat": float }`.
 **Requirement**: Must perform 10000 shuffles as per Spec FR-005. If runtime exceeds 6 hours, apply T053_fallback.
 **Dependency**: T023a_gp (Model fits), T025a (Benchmark), T045a (Lock).

- [ ] T025c [S] **Apply FDR Correction**: Implement `src/models/utils.py::apply_fdr_correction` that takes the **permutation test output** (T025b_spatial and T025d), aggregates **all species-climate coefficient p-values and spatial shift p-values**, applies Benjamini‑Hochberg, adds a `q_value` column, and writes `data/processed/model_results_fdr.parquet`.
 **Dependency**: T025b_spatial, T025d, and T023a_gp.

- [X] T027 [S] **Implement Convergence Error Handling**: Wrap GAMM fitting in `try/except`. On convergence failure, log `"Convergence failed for species {species}: {error}"` to `logs/modeling.log` and skip that species. Add unit test `tests/unit/test_convergence_handling.py` verifying log format and that the pipeline continues without crashing.
 **Dependency**: T023a_gp.

## Phase 5: User Story 3 – Route Shift Analysis and Uncertainty Quantification (Priority: P3)

- [ ] T028 [P] **Test Trajectory Output Schema**: `tests/contract/test_trajectory_schemas.py::test_trajectory_output_schema` validates `data/processed/trajectory_results.json` contains keys `{ "species", "year", "shift_magnitude", "shift_direction", "p_value" }`.
 **Output**: `tests/contract/test_trajectory_schemas.py`.
 **Dependency**: T031c_permutation.

- [X] T029 [P] **Integration Test for Route Shift Detection**: `tests/integration/test_trajectory_analysis.py::test_route_shift_detection` runs the full trajectory pipeline on a synthetic null dataset and asserts `p_value > 0.05`.
 **Output**: `tests/integration/test_trajectory_analysis.py`.
 **Dependency**: T031c_permutation.

- [ ] T030 [S] **Compute Weekly Migration Centroids on Riemannian S² Manifold**:
 **Action**: Implement `src/models/trajectory.py::compute_weekly_centroids` that aggregates preprocessed observations per species‑year per week.
 **Logic**:
 1. Project lat/lon to **S2 manifold** coordinates using `geomstats.geometry.hypersphere.Hypersphere`.
 2. Compute the **Fréchet mean** of the weekly points on the manifold using geomstats' manifold-based statistics.
 3. Convert mean back to lat/lon.
 **Output**: `data/interim/weekly_centroids.parquet`.
 **Requirement**: Use `geomstats` for S2 manifold operations. Do NOT use Euclidean distance or linear regression. This implements the Spec's requirement for Riemannian manifold operations (FR-006).
 **Dependency**: T015b (preprocessed data).

- [ ] T031a_manifold [S] **Compute Riemannian Trajectory Statistics on S² Manifold**:
 **Action**: Use the centroids from T030 to compute trajectory-level statistics on the S2 manifold.
 **Logic**:
 1. Compute the variance of weekly centroids using geodesic distance on the manifold.
 2. Perform trajectory analysis using manifold-based statistics: parallel transport, geodesic regression.
 3. Calculate shift vectors based on the difference in manifold parameters between years.
 **Output**: `data/interim/trajectory_statistics.json` containing `variance`, `regression_coefficients`, `shift_vectors`.
 **Requirement**: Use `geomstats` for manifold operations. This implements the Spec's requirement for manifold-based trajectory statistics (FR-006).
 **Dependency**: T030 (weekly centroids).

- [ ] T031b_manifold [S] **Detect Spatial Route Shifts Using Riemannian Statistics**:
 **Action**: Use the trajectory statistics computed in T031a_manifold to detect spatial route shifts.
 **Logic**:
 1. Compare trajectories across years using the manifold regression coefficients.
 2. Calculate the **shift vector** (magnitude and direction) based on the difference in manifold parameters.
 3. Prepare the data structure for the permutation test in T031c_permutation.
 **Output**: `data/interim/shift_candidates.json` containing `species`, `year`, `shift_vector`, `magnitude`, `direction`.
 **Dependency**: T031a_manifold (Trajectory Statistics).

- [ ] T031c_permutation [S] **Riemannian Trajectory Analysis & Permutation**:
 **Action**: For each species, perform **exactly 10,000** permutation shuffles (as mandated by Spec FR-005) on the **shift vectors** generated in T031b_manifold to derive the p-value. If runtime constraints are exceeded, apply the fallback mechanism defined in T053_fallback.
 **Test**:
 1. **Shuffling Strategy**: Shuffle species-year labels relative to the observed shift vectors while preserving the temporal structure of the trajectory.
 2. **Test Statistic**: Euclidean distance between the mean shift vector of the observed data and the mean shift vector of the permuted data.
 3. **P-value**: Proportion of permuted statistics >= observed statistic.
 4. **Error Handling**: If T031b_manifold produces no valid candidates, log a warning and skip.
 **Output**: `data/processed/trajectory_results.json` containing `shift_vector`, `magnitude`, `direction`, and `p_value`.
 **Requirement**: Must perform 10000 shuffles as per Spec FR-005. If runtime exceeds 6 hours, apply T053_fallback.
 **Dependency**: T030, T031a_manifold, T031b_manifold, T045a (Lock).

- [ ] T033a1 [P] **Generate Phenology Confidence Intervals**: Implement block bootstrap (preserving weekly autocorrelation) on **GAMM model predictions**, specifically performing **bootstrapped resampling of the centroid estimation process** to generate 95% CIs for model predictions as per FR-007. Produce `ci_lower` and `ci_upper` columns in `data/processed/model_results_fdr.parquet`.
 **Logic**: Use **moving block bootstrap** with **block_size=4 weeks**.
 **Dependency**: T023a_gp (model fits), T045a (Lock), T045b (Lock Integration).
 **Requirement**: Must use block bootstrap, not simple permutation.

- [ ] T033a2 [P] **Generate Centroid-Based Confidence Intervals**: Implement block bootstrap on the **centroid estimation process** (resampling weekly observations) to generate 95% CIs for model predictions as per FR-007. Output `data/processed/centroid_ci.json`.
 **Logic**: Use **moving block bootstrap** with **block_size=4 weeks**.
 **Dependency**: T030 (weekly centroids), T045a (Lock), T045b (Lock Integration).
 **Requirement**: Must use block bootstrap, not simple permutation.

- [ ] T033b [P] **Generate Trajectory Confidence Intervals**: Apply block bootstrap to shift magnitudes from `trajectory_results.json` (output of T031c_permutation), append `ci_lower`/`ci_upper` to each record, and write to `data/processed/trajectory_results_ci.json`.
 **Dependency**: T031c_permutation, T045a (Lock), T045b (Lock Integration).
 **Requirement**: Must use block bootstrap, not simple permutation.

- [ ] T033a3 [S] **Calculate CI Width Metrics**: Compute `ci_width = ci_upper - ci_lower` for each phenology and trajectory CI, compare against `config.DEFAULT_CI_WIDTH_TARGET` (for reporting only), and write summary to `data/processed/ci_width_report.json`.
 **Dependency**: T033a1, T033a2, T033b.

## Phase 6: Orchestration & Validation (SC‑001 to SC‑005)

- [ ] T043a [S] **Define Success Criteria Targets**:
 **Action**: Read plan.md "Success Criteria & Fallbacks" section and write `data/processed/target_definitions.json` with concrete thresholds. Use these concrete values: sc002_target = 0.95 ([deferred] cells with sufficient data), sc003_target = 0.90 ([deferred] convergence rate), sc004_target = 7 (7 days CI width). If plan text is ambiguous, default to these values. Document the source (Plan section and line number) in the JSON output.
 **Output**: `data/processed/target_definitions.json`.
 **Dependency**: None.

- [ ] T043b [S] **Implement Power Analysis Script**: Write `src/analysis/power_analysis.py` to calculate statistical power and effect size stability (SC-001) based on the total number of migratory species and model results. Output `data/processed/power_report.json`.
 **Dependency**: T023a_gp (model fits).

- [ ] T043c1 [S] **Measure SC-002 (Insufficient Data Proportion)**:
 **Action**: Read `data/processed/preprocessed_data.parquet` (from T018), count rows with `data_quality="insufficient"`, and calculate the proportion of total grid cells. Compare against `data/processed/target_definitions.json` (SC-002 target). Explicitly report the spec's '[deferred]' target vs the plan's fallback.
 **Output**: `data/processed/insufficient_data_report.json` containing `total_cells`, `insufficient_cells`, `proportion`, `target`, `pass/fail`, `spec_target_note`.
 **Requirement**: Explicitly generates the `metadata_insufficient_cells.json` artifact referenced by T043. Must flag if the spec's '[deferred]' target is not explicitly resolved.
 **Dependency**: T018, T043a.

- [ ] T043c2 [S] **Measure SC-003 (Convergence Rate)**:
 **Action**: Read `logs/modeling.log` and `data/processed/model_results_final.parquet` to compute convergence rate (successful fits / total attempts). Compare against `data/processed/target_definitions.json` (SC-003 target).
 **Output**: `data/processed/convergence_report.json` containing `total_attempts`, `successful_fits`, `convergence_rate`, `target`, `pass/fail`.
 **Dependency**: T027, T043a.

- [ ] T043d [S] **Calculate CI Width Metrics**: Read `data/processed/ci_width_report.json` (from T033a3) and compare against `data/processed/target_definitions.json`. Store in `data/processed/ci_width_target_report.json`.
 **Dependency**: T033a3 and T043a.

- [ ] T043 [S] **Calculate and Report All Success Criteria**:
 **Logic**:
 1. **SC‑001 (Power)** – Use output from T043b.
 2. **SC‑002 (Insufficient Data)** – Use output from T043c1 (which generates `data/processed/metadata_insufficient_cells.json`).
 3. **SC‑003 (Convergence)** – Use output from T043c2.
 4. **SC‑004 (CI Width)** – Use output from T043d.
 5. **SC‑005 (Runtime)** – Run `src/analysis/runtime_validation.py` to ensure total pipeline runtime < 6 h; store result in `data/processed/runtime_report.json`. If runtime exceeds 6 hours and T053_fallback has been applied, document the adjusted shuffle count and Bonferroni correction applied.
 **Aggregated Output**: Combine all five JSON reports into a single `data/processed/final_success_report.json`.
 **Requirement**: All targets are now defined in `target_definitions.json`.
 **Dependency**: T043a, T043b, T043c1, T043c2, T043d, T025c, T027, T033a3, and all preceding analysis tasks.

## Phase 6.5: Runtime Constraint Fallback

**Purpose**: Address the conflict between the Spec's mandate for [deferred] shuffles and the 6-hour runtime constraint. Provide a spec-authorized fallback mechanism.

- [ ] T053_fallback [S] **Implement Runtime-Aware Shuffle Count Fallback**:
 **Action**: Write `src/analysis/runtime_fallback.py` to implement a spec-authorized fallback mechanism for permutation tests when runtime constraints are exceeded.
 **Logic**:
 1. After T025a benchmark completes, estimate the total runtime for [deferred] shuffles.
 2. If estimated time for a large number of shuffles exceeds several hours (leaving 0.5 hours buffer for other tasks), reduce the shuffle count to N = floor(5.5*3600 / (time_per_shuffle)).
 3. Log the reduction: `"Permutation shuffle count reduced from [deferred] to {N} due to runtime constraints. Applying Bonferroni correction: multiply p-values by {10000/N}."`.
 4. Apply Bonferroni correction to p-values: multiply each p-value by (10000/N) to adjust for the reduced number of shuffles.
 5. Update T025b_spatial and T031c_permutation to use the reduced shuffle count if this fallback is triggered.
 **Output**: `data/processed/runtime_fallback_report.json` containing `original_shuffles`, `adjusted_shuffles`, `bonferroni_factor`, `estimated_runtime`, `fallback_triggered`.
 **Requirement**: This fallback is spec-authorized because it preserves the intent of FR-005 (statistical testing with multiple-comparison correction) while respecting the SC-005 runtime constraint. The Bonferroni correction is a standard statistical adjustment for reduced sample sizes.
 **Dependency**: T025a (Benchmark must complete first).

## Phase 7: Polish & Cross‑Cutting Concerns

- [ ] T036 [P] **Update README** with installation instructions and `python -m src.cli.run_pipeline --help`.
 **Dependency**: T002a.

- [ ] T037 [P] **Create docs/api.md** with docstrings for all public functions in `src/data/preprocess.py`.
 **Dependency**: T015b.

- [ ] T038a [P] **Run Ruff Auto‑Fix** on `src/`.
 **Dependency**: T003a_2.

- [ ] T038b [P] **Add Pre‑commit Hook for Docstring Validation**.
 **Dependency**: T003b.

- [ ] T039b1 [P] **Parallelize permutation tests with joblib**: Target: **achieve < 500ms per chunk** using a benchmark dataset of large-scale rows.
 **Requirement**: Must be run after T025b_spatial/T025d completion.
 **Dependency**: T025b_spatial, T025d.

- [ ] T039b2 [P] **Parallelize trajectory permutation tests with joblib**: Target: **achieve < 1000ms per species** using a benchmark dataset of a substantial number of rows.
 **Requirement**: Must be run after T031c_permutation completion.
 **Dependency**: T031c_permutation.

- [ ] T040a [P] **Add unit test for empty input in `src/data/preprocess.py`**.
 **Dependency**: T015b.

- [ ] T040b [P] **Add unit test for single species in `src/models/gamm_fit.py`**.
 **Dependency**: T023a_gp.

- [ ] T040c [P] **Add unit test for missing data handling in `src/data/impute.py`**.
 **Dependency**: T007.

- [ ] T041a [P] **Create `.github/workflows/ci.yml`**.
 **Dependency**: T002a.

- [ ] T041b [P] **Define `validate_quickstart` job in CI workflow**.
 **Action**: Include a pre-check step to validate task ordering in `tasks.md` (ensuring verify tasks follow their producers).
 **Dependency**: T041a.

- [ ] T041c [P] **Add runtime assertion (< 6 h) to `validate_quickstart` job**.
 **Dependency**: T041b.

## Phase 8: Reporting & Documentation (Moved from Phase 7)

**Purpose**: Final reporting and documentation updates.

- [ ] T045c [S] **Document Lock Usage**: Add section to `docs/locking.md` describing when and how the lock is used, and update any relevant README sections.
 **Dependency**: T045b.

## Phase 9: Data Integrity & Optimization (Moved from Phase 9)

**Purpose**: Address specific reviewer concerns regarding data source fidelity, task ordering, and CI constraints. These tasks are now integrated into their respective phases.

- [X] T052 [S] **Enforce Real Data Fetch Failing Loudly**:
 **Action**: Review `src/data/download.py` and `src/data/verify_dataset.py`. Ensure there are NO `try/except` blocks that catch download errors and fall back to `generate_synthetic_*()` or mock data. If a real fetch fails, the script MUST raise `RuntimeError` or `FileNotFoundError` and exit.
 **Requirement**: A silent synthetic fallback is fabrication. The execution stage must fail loudly to discover a verified real source.
 **Dependency**: T005a, T005b, T005c1b_primary.

- [X] T053 [P] **Optimize Permutation Tests for CI Time Limit**:
 **Action**: Refactor T025b_spatial and T031c_permutation to use `joblib` parallelization with a strict timeout (e.g., a total duration for all permutation tasks sufficient to ensure the pipeline completes within the designated CI time limit) (SC-005). **Algorithm**: If the initial set of shuffles is estimated to exceed the 6-hour limit based on T025a benchmark, **log the estimated time and proceed with parallelization**. **Do NOT reduce the shuffle count** unless T053_fallback is triggered. If the timeout is hit, log the partial progress and report the limitation.
 **Requirement**: Must address SC-005 (Runtime) without compromising the integrity of the permutation test. If reduction occurs via T053_fallback, the p-value calculation must be adjusted or reported with the reduced N.
 **Dependency**: T025a, T025b_spatial, T025d, T031c_permutation.

- [X] T054 [S] **Implement Block Bootstrap for Uncertainty**:
 **Action**: Ensure `src/analysis/bootstrap.py` implements block bootstrap (preserving temporal autocorrelation) for both GAMM predictions and centroid estimation as required by FR-007 and US-3. Do NOT use simple random resampling.
 **Requirement**: Simple permutation destroys the temporal structure of migration routes, leading to invalid p-values.
 **Dependency**: T023a_gp, T030.

- [X] T055 [S] **Verify NOAA/PRISM Dataset Availability**:
 **Action**: Update T005c1b_primary to explicitly check for the NOAA/PRISM dataset availability using official API endpoints. If not found, raise a clear error and halt. Do NOT attempt to download from unverified URLs.
 **Requirement**: Ensures the pipeline does not proceed with missing or incorrect climate data.
 **Dependency**: T005a.