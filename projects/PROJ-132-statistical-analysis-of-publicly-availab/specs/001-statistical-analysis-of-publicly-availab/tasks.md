# Tasks: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

**Input**: Design documents from `/specs/001-bird-migration-climate-correlation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must wait for predecessor completion)
- **[M]**: Manual (requires human intervention)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0: Pre-Implementation & Spec Alignment

**Purpose**: Verify plan/spec alignment and document scope limitations before any implementation begins.

- [X] T005c4 [M] [Spec] **Document Plan Deviation from Spec**:
 **Action**: A human developer MUST manually write a formal deviation document `specs/001-bird-migration-climate-correlation/amendments/PLAN-DEVIATION-DATA-SOURCES.md` that documents the Plan's explicit substitution of NOAA/PRISM with Daymet and the full eBird archive with the verified `vvud/eb-data` sample.
 **Content**: Must include: (1) Original Spec FR-001 text, (2) Plan's implemented source (Daymet + vvud/eb-data), (3) Justification (Plan states verified open-source availability), (4) Impact on downstream tasks, (5) Ratification timestamp (manually inserted), AND (6) A JSON field `{"status": "ratified"}` to indicate formal ratification.
 **Requirement**: This document serves as the official record of the Plan's deviation from the Spec. The Spec remains unchanged and is the single source of truth for implementation. The task MUST be completed by a human developer; no script may auto-generate or auto-update this file.
 **Output**: `specs/001-bird-migration-climate-correlation/amendments/PLAN-DEVIATION-DATA-SOURCES.md`.
 **Dependency**: None.

- [X] T005c3 [M] **Document Data Source Deviation**: Write JSON `data/provenance/spec_plan_deviation.json` with the following EXACT structure:
 ```json
 {
 "spec_requirement": "NOAA/PRISM (FR-001)",
 "implemented_source": "Daymet",
 "reason": "Plan explicitly substitutes NOAA/PRISM with Daymet for verified open-source availability. Spec deviation ratified in PLAN-DEVIATION-DATA-SOURCES.md (T005c4).",
 "timestamp": "YYYY-MM-DDTHH:MM:SSZ"
 }
 ```
 **Requirement**: Must reflect which data source was actually used; timestamp must be generated manually by the human developer at the time of writing. This JSON file is used by T005c1_validate to determine which climate data source to use. It serves as the single source of truth for the data source decision throughout the pipeline.
 **Output**: `data/provenance/spec_plan_deviation.json`.
 **Dependency**: T005c4.

- [X] T005c1_validate [S] **Validate Deviation Document**:
 **Action**: Verify the existence of `specs/001-bird-migration-climate-correlation/amendments/PLAN-DEVIATION-DATA-SOURCES.md` AND `data/provenance/spec_plan_deviation.json`. Check if the Markdown file contains a valid ratification timestamp AND a JSON field `{"status": "ratified"}`. Check if the JSON file exists and has valid structure.
 **Output**: Write `data/provenance/deviation_validation.json` with `{ "is_ratified": bool, "message": str }`.
 **Requirement**: This task must run before T005c1_fetch. It explicitly reads the JSON file from T005c3 to determine the data source.
 **Dependency**: T005c4, T005c3.

- [X] T005c5 [S] **Pre-Execution Ordering Validator**:
 **Action**: Write script `src/cli/validate_task_order.py` that parses `tasks.md` and verifies that all "verify" or "test" tasks (e.g., T013, T021) appear AFTER their producer tasks (e.g., T015b, T023a) in the dependency graph.
 **Logic**: Parse the `Dependency` field in each task header. Verify that for every task `T_x`, all tasks listed in its `Dependency` field appear earlier in the file than `T_x`. If any verify task depends on a task that has not been executed (or is listed after it in the file), raise `RuntimeError` with message "Task ordering violation: <task_id> must run after <producer_id>".
 **Requirement**: This task runs in the CI workflow (T041b) as a check, not as a Phase 0 execution task. It prevents the pipeline from starting if `tasks.md` is malformed.
 **Output**: Exit code 0 on success, 1 on failure.
 **Dependency**: T002a (Project Structure).

- [X] T005a [S] **Verify Data Availability**:
 **Action**: Write script `src/data/verify_dataset.py` that attempts to load the verified eBird sample (`vvud/eb-data`) using `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)` and checks for NOAA/PRISM and Daymet availability.
 **Output**: Write `data/provenance/data_availability_report.json` with keys `{ "ebird_available": bool, "noaa_available": bool, "daymet_available": bool }`. Raise `RuntimeError` with clear message if eBird is missing.
 **Dependency**: None.

- [X] T005b [S] **Download Verified eBird Sample**:
 **Action**: Stream the verified eBird sample (`vvud/eb-data`) via `datasets.load_dataset(..., streaming=True)`, write raw files to `data/raw/ebird_sample/` preserving original file names. Compute SHA‑ checksums for each downloaded shard and store in `data/raw/ebird_sample/checksums.sha256`.
 **Requirement**: No synthetic fallback; abort on any download error.
 **Dependency**: T005a.

- [X] T005c1_fetch [S] **Download Climate Data (Spec Primary with Ratified Deviation Fallback)**:
 **Action**: Implement `src/data/download.py::fetch_climate_data` to download climate data.
 **Logic**:
 1. **Check Validation**: Read `data/provenance/deviation_validation.json`. If `is_ratified` is False, proceed to Primary Fetch. If True, proceed to Fallback Fetch.
 2. **Primary Fetch (NOAA/PRISM)**: If deviation is NOT ratified, attempt to download NOAA/PRISM data from the official NOAA/PRISM API or verified mirror. Write to `data/raw/noaa_prism/` as NetCDF or Parquet files. Compute SHA‑ checksums. If download fails, raise `RuntimeError` with message "NOAA/PRISM download failed; unable to proceed with Spec FR-001 primary requirement" and exit.
 3. **Fallback Fetch (Daymet)**: If deviation IS ratified, use `datasets.load_dataset("daymet/annual", variables=["prcp", "tmin", "tmax", "srad", "vp"], state="ALL", year=["2021", "2022", "2023", "2024"])` to download climate variables. Write to `data/raw/daymet/` as Parquet files (`daymet_*.parquet`). Compute SHA‑ checksums.
 4. **Logging**: Use `src.utils.logging.get_logger(__name__).info("Plan deviation ratified; using Daymet as per ratified amendment")` if using Daymet.
 **Requirement**: This is the primary task for climate data as per Spec FR-001. It only skips NOAA/PRISM if the Plan's deviation is ratified with all validation checks passing.
 **Output**: `data/raw/noaa_prism/` (if successful) or `data/raw/daymet/` (if deviation ratified) or error log.
 **Dependency**: T005a, T005c1_validate.

- [X] T005d_state_sync [S] **State Synchronization & Archive**:
 **Action**: Atomic task that: (1) Copies all raw files from `data/raw/ebird_sample/`, `data/raw/daymet/` (if exists), and `data/raw/noaa_prism/` (if exists) to `data/raw/archive/`. (2) Generates CI workflow snippet for uploading `data/raw/archive/` as artifacts to `ci/upload_artifacts.yml`. (3) Inserts the new artifact hashes and `updated_at` timestamp into `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml`.
 **Requirement**: All three steps must complete atomically. If any step fails, the task fails. Must wait for T005b and T005c1_fetch to complete successfully before running.
 **Output**: `data/raw/archive/`, `ci/upload_artifacts.yml`, updated `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml`.
 **Dependency**: T005b, T005c1_fetch.

- [X] T006 [P] **Schema test for eBird Columns**: `tests/contract/test_schemas.py::test_ebird_schema_columns` asserts that the eBird DataFrame contains columns `[species, lat, lon, date, count, checklist_id]` with correct dtypes.
 **Dependency**: T005b.

- [X] T007 [P] **Implement Spatial Imputation Utility**: Write `src/data/impute.py` containing function `impute_spatial_missing(df, column, radius=1.0)`. Logic: For each missing value in `column`, find neighbors within `radius` degrees, compute weighted average (inverse distance), and fill. Return a DataFrame with an `is_imputed` boolean column.
 **Output**: `src/data/impute.py`.
 **Dependency**: None.

- [X] T009 [P] **Create Base Data Entities**: Write `src/data/entities.py` defining Pydantic models: `MigrationRecord` (species, lat, lon, date, count, checklist_id), `PhenologyMetric` (species, grid_cell, week, first_arrival_date, median_arrival_date, stopover_duration), `ClimateVariable` (grid_cell, week, mean_temperature, total_precipitation, extreme_weather_index), `Trajectory` (species, year, weekly_centroids, shift_vector).
 **Output**: `src/data/entities.py`.

- [X] T010a [P] **Define Constants**: Write `src/config.py` defining `GRID_RES=0.5`, `MIN_OBSERVATIONS=10`, `RANDOM_SEED=42`, `PERMUTATIONS=10000`, `CI_WIDTH_TARGET=7`, `MAX_PERMUTATION_RUNTIME_HOURS=6`.
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

- [X] T003b [P] **Create Pre-commit Config**: Create `.pre-commit-config.yaml` with hooks for `black` and `ruff` and add installation instructions to `README.md`.
 **Action**: If `README.md` does not exist, create a minimal one first. Add "python (Wikidata Q115911873, https://www.wikidata.org/wiki/Q115911873) -m src.cli.run_pipeline --help" to the installation section.
 **Dependency**: T003a_1, T002a.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes runtime optimization to meet SC‑005 and Locking Infrastructure.

- [X] T045a [S] **Create File-Based Lock**: Implement `src/utils/locks.py` exposing `pipeline_lock = filelock.FileLock("data/interim/pipeline.lock")`.
 **Requirement**: Must be available for T023a_gamm_gp, T025d, T031c_permutation.
 **Dependency**: None.

- [X] T045b [S] **Integrate Lock into Heavy Tasks**: Modify `src/models/gamm.py`, `src/models/utils.py` (permutation), and `src/models/trajectory.py` to acquire `pipeline_lock` before any write to shared `data/interim/` resources.
 **Requirement**: Must be integrated before T023a_gamm_gp/T025d/T031c_permutation run.
 **Dependency**: T045a.

## Phase 3: User Story 1 – Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

- [ ] T015a [S] [US1] **Retrieve CLO Migratory List**:
 **Action**: Write `src/data/fetch_species.py` to download the verified eBird migratory species list from the HuggingFace dataset `vvud/eb-migratory-list`, cache it in `data/raw/migratory_list.json`, and return a set of valid species names.
 **Schema**: The JSON file must contain a list of objects with `species_name` (str).
 **Verification**: On first run, compute the SHA-256 checksum of the file and write it to `data/provenance/ebird_checksums.json`. On subsequent runs, verify against the recorded checksum. If the download fails or the list is empty, raise `RuntimeError` with message "Failed to fetch verified real data from vvud/eb-migratory-list. Aborting pipeline to prevent fabrication."
 **Output**: `src/data/fetch_species.py`, `data/raw/migratory_list.json`, `data/provenance/ebird_checksums.json`.
 **Requirement**: Must include verification mechanism (URL, schema, checksum recording). Must fail loudly if the list cannot be fetched.
 **Dependency**: T005a.

- [X] T015b [S] [US1] **Implement Preprocessing Pipeline**:
 **Action**: Write `src/data/preprocess.py` to stream eBird data (using T051), filter for migratory species (using T015a), aggregate to a regular grid resolution, and compute phenology metrics.
 **Logic**: Use `polars` for efficient streaming.
 1. **Binning**: Use `numpy.floor(lat / 0.5) * 0.5` and `numpy.floor(lon / 0.5) * 0.5` to create `grid_cell` strings (e.g., "45.0_-120.5") ensuring EXACT 0.5° x 0.5° resolution for BOTH dimensions.
 2. **Aggregation**: Group by `species`, `grid_cell`, `year`, `week`.
 3. **Phenology Metrics**: Compute `first_arrival` (min date), `median_arrival` (median date), `stopover_duration` (inter-percentile range of dates).
 4. **Mark Insufficient**: Mark grid cells with fewer than `MIN_OBSERVATIONS` as `data_quality="insufficient"` immediately after aggregation.
 5. **Intermediate Output**: Write intermediate grid-binned data to `data/interim/grid_binned.parquet`.
 6. **Phenology Output**: Write intermediate phenology data to `data/interim/phenology_raw.parquet` with schema: `[species, grid_cell, year, week, first_arrival_date, median_arrival_date, stopover_duration]`.
 7. **Climate Join**: Join with NOAA/PRISM (or Daymet if deviation exists) data on `grid_cell` and `week`.
 8. **Imputation**: Use `src/data/impute.py` (T007) to fill missing climate values. Flag imputed rows.
 9. **Provenance**: Generate `data/provenance/row_mapping.json` mapping each processed row ID to its original `checklist_id` (hash: `SHA256(checklist_id + ":::" + species + ":::" + grid_cell + ":::" + week)`).
 10. **Final Output**: Write final processed data to `data/processed/preprocessed_data.parquet`.
 **Requirement**: Must handle edge cases (e.g., grid cells with < MIN_OBSERVATIONS) by marking them as `data_quality="insufficient"` and generating provenance for all rows (including insufficient ones) before exclusion. Must wait for T051, T015a, T005b, T005c1_fetch to complete and produce outputs before starting.
 **Output**: `data/processed/preprocessed_data.parquet`, `data/provenance/row_mapping.json`.
 **Dependency**: T051 (Streaming), T015a (Species List), T005b (Data Download), T005c1_fetch (Climate Data).

- [X] T013 [S] [US1] **Integration Test for Data Ingestion Flow**:
 **Action**: Write `tests/integration/test_data_ingestion.py::test_end_to_end_ingestion`.
 **Mock Strategy**: Use `pytest-mock` to patch `datasets.load_dataset` and `src.data.download.fetch_climate_data` to return a small, synthetic JSON fixture with multiple rows of eBird data and 1 row of climate data.
 **Fixture Schema**: Create fixture file `tests/fixtures/mock_ebird_climate.json` with the following structure: `{"records": [{"species": str, "lat": float, "lon": float, "date": str (YYYY-MM-DD), "count": int, "checklist_id": str},...], "climate": [{"grid_cell": str, "week": int, "mean_temperature": float, "total_precipitation": float},...]}`. Use a limited number of eBird records and one climate record for the mock.
 **Logic**: Run the preprocessing pipeline (T015b) on this mocked data.
 **Assertion**: Assert that the output `data/processed/preprocessed_data.parquet` exists and contains the exact schema: `[species, grid_cell, week, first_arrival_date, median_arrival_date, stopover_duration, mean_temperature, total_precipitation, data_quality]` with correct dtypes and no missing values in critical fields.
 **Requirement**: This task is Sequential [S] as it depends on the completed T015b artifact. It satisfies the US-1 Independent Test by verifying the pipeline on a subset. Must wait for T015b to complete and produce outputs before starting.
 **Output**: `tests/integration/test_data_ingestion.py`.
 **Dependency**: T015b.

- [X] T017d [P] **Verify Imputation Metadata**: Write unit test `tests/unit/test_imputation_metadata.py::test_imputation_metadata_exists` that checks for file `data/processed/imputation_metadata.json`, validates JSON schema, and asserts that every record with `is_imputed = true` has a non‑null `imputation_source`.
 **Dependency**: T015b.

## Phase 4: User Story 2 – Phenology‑Climate Correlation Modeling (Priority: P2)

- [X] T021 [P] **Test GAMM Output Schema**: `tests/contract/test_gamm_schemas.py::test_gamm_output_schema` validates `data/processed/model_results_final.parquet` contains keys `{ "species", "temp_coef", "precip_coef", "p_value", "converged" }`.
 **Output**: `tests/contract/test_gamm_schemas.py`.
 **Dependency**: T023a_gamm_gp.

- [X] T022 [P] **Integration Test for GAMM Convergence**: `tests/integration/test_gamm_convergence.py::test_gamm_convergence` runs GAMM on a small synthetic dataset and asserts the `converged` flag is True for known parameters.
 **Output**: `tests/integration/test_gamm_convergence.py`.
 **Dependency**: T023a_gamm_gp.

- [X] T023a_gamm_gp [S] [US2] **Fit GAMM with Species-Specific Random Slopes and Mandatory A Priori Gaussian Process**:
 **Action**: Write `src/models/gamm.py::fit_gamm_gp` that reads `data/processed/preprocessed_data.parquet`.
 **Library**: `pyMC` (PyMC).
 **Logic**:
 1. **Base Fit**: Fit model with formula `phenology_metric ~ s(temp) + s(precip) + s(extreme_weather_index) + (1 + temp | species + year)`.
 2. **Random Effects**: Include species-year random intercepts and species-specific random slopes for temperature as per Spec FR-004. **Formula Syntax**: Use `(1 + temp | species + year)` to specify random intercepts and slopes for `species` and `year`.
 3. **GP Random Effect**: Integrate a **mandatory a priori** Gaussian Process (GP) random effect with Matérn covariance function (nu=2.5) directly into the model fitting process using `pm.gp.Matern52` to account for spatial autocorrelation. Do NOT fit as a post-hoc step.
 4. **Locking**: Acquire `data/interim/pipeline.lock` (via `filelock.FileLock`) before writing model results.
 **Output**: `data/processed/model_results_final.parquet` (includes random effects and GP).
 **Requirement**: Random effect MUST be `(1 + temp | species + year)` AND GP MUST be included a priori in the initial fit using `pyMC`. Must wait for T015b to complete and produce outputs before starting.
 **Dependency**: T015b (preprocessed data), T045a (Lock).

- [X] T023d [S] **Compute Moran's I Diagnostic (Non-Blocking)**:
 **Action**: Write `src/models/gamm.py::compute_morans_i` that takes the preprocessed data and the results from T023a_gamm_gp to compute Moran's I for spatial autocorrelation of residuals.
 **Requirement**: This is a diagnostic only; it does NOT gate the model fit or GP inclusion. The GP is mandatory a priori (T023a_gamm_gp).
 **Output**: `data/interim/morans_i_result.json` with schema `{"value": float}`.
 **Dependency**: T023a_gamm_gp (GAMM fit must complete first to provide residuals).

- [X] T025a [P] **Benchmark Permutation Test**: Write `src/models/utils.py::benchmark_permutation` to run multiple shuffles and estimate runtime per batch of shuffles using a a benchmark dataset of sufficient size from `data/processed/preprocessed_data.parquet`. Store in `data/processed/permutation_benchmark.json`.
 **Output**: `data/processed/permutation_benchmark.json`.
 **Dependency**: T023a_gamm_gp.

- [X] T025d [S] [US2] **Permutation Test for GAMM Coefficients**: Execute **exactly 10,000** permutation shuffles (as mandated by Spec FR-005) on **species-climate coefficients**. Use `src/models/utils.run_permutation_chunked`. Acquire `data/interim/pipeline.lock`. If runtime exceeds `config.MAX_PERMUTATION_RUNTIME_HOURS` (default 6), the pipeline logs the failure, reduces the shuffle count to **1000**, flags the result as "fallback" in the output, and continues (no pipeline failure).
 **Logic**: Shuffle response variables (phenology metrics) relative to climate predictors. Test statistic: Absolute value of the coefficient for temperature/precip. Perform permutation tests on species-climate coefficients (temperature and precipitation) extracted from the fitted GAMM (T023a_gamm_gp). This tests the association between phenology metrics and climate variables as specified in Spec FR-005 and US-2 Acceptance Scenario 1. The permutation is performed by shuffling the response variable (phenology metric) relative to the predictors (climate variables).
 **Input**: `data/processed/model_results_final.parquet` (T023a_gamm_gp).
 **Output**: `data/processed/permutation_results_coefficients.json`.
 **Schema**: `{ "species": str, "coefficient": str, "shuffle_id": int, "p_value": float, "raw_stat": float, "fallback": bool, "reduced_n": int }`.
 **Requirement**: Must attempt 10000 shuffles. If `config.MAX_PERMUTATION_RUNTIME_HOURS` is exceeded, reduce to 1000 shuffles and set `fallback=true`, `reduced_n=1000`. No pipeline failure.
 **Dependency**: T023a_gamm_gp (Model fits), T025a (Benchmark), T045a (Lock).

- [X] T025b_spatial [S] [US3] **Permutation Test for Spatial Shift Vectors**: Execute **exactly 10,000** permutation shuffles (as mandated by Spec FR-005) in chunks of a fixed size using `src/models/utils.run_permutation_chunked`. Acquire `data/interim/pipeline.lock` before writing results. **Use `config.RANDOM_SEED` for all shuffles**. If runtime exceeds `config.MAX_PERMUTATION_RUNTIME_HOURS` (default 6), the pipeline logs the failure, reduces the shuffle count to **1000**, flags the result as "fallback" in the output, and continues (no pipeline failure).
 **Logic**: Shuffle species-year labels relative to shift vectors. Test statistic: Euclidean distance between mean shift vector of observed data and mean shift vector of permuted data.
 **Input**: `data/processed/shift_vectors.json` (output of T031b_manifold).
 **Output**: `data/processed/permutation_results_spatial.json`.
 **Schema**: `{ "species": str, "shuffle_id": int, "p_value": float, "raw_stat": float, "fallback": bool, "reduced_n": int }`.
 **Requirement**: Must attempt 10000 shuffles. If `config.MAX_PERMUTATION_RUNTIME_HOURS` is exceeded, reduce to 1000 shuffles and set `fallback=true`, `reduced_n=1000`. No pipeline failure.
 **Dependency**: T023a_gamm_gp (Final model output), T025a (Benchmark), T045a (Lock), T031b_manifold (Shift vectors must be generated first).

- [X] T025c [S] [US2] **Apply FDR Correction**: Implement `src/models/utils.py::apply_fdr_correction` that takes the **permutation test output** (T025d and T031c_permutation), aggregates **all species-climate coefficient p-values and spatial shift p-values**, applies Benjamini‑Hochberg, adds a `q_value` column, and writes `data/processed/model_results_fdr.parquet`.
 **Logic**: Read p-values from `data/processed/permutation_results_coefficients.json` (T025d) and `data/processed/trajectory_results.json` (T031c_permutation). Apply FDR to the combined set.
 **Output**: `data/processed/model_results_fdr.parquet`.
 **Requirement**: Must wait for T025d and T031c_permutation to complete and produce outputs before starting.
 **Dependency**: T025d, T031c_permutation, T023a_gamm_gp.

- [X] T025e [S] **Calculate Effective Power with Fallback**:
 **Action**: Implement `src/analysis/power_analysis.py::calculate_effective_power` that reads `data/processed/permutation_results_coefficients.json` and `data/processed/permutation_results_spatial.json`. If any record has `fallback=true`, calculate the "Effective Power" metric based on the reduced n (1000) and log a warning. Output `data/processed/power_with_fallback.json`.
 **Requirement**: Ensures SC-001 remains measurable even if fallback triggers.
 **Dependency**: T025d, T025b_spatial.

- [X] T027 [S] **Implement Convergence Error Handling**: Wrap GAMM fitting in `try/except`. On convergence failure, log `"Convergence failed for species {species}: {error}"` to `logs/modeling.log` and skip that species. Add unit test `tests/unit/test_convergence_handling.py` verifying log format and that the pipeline continues without crashing.
 **Dependency**: T023a_gamm_gp.

## Phase 5: User Story 3 – Route Shift Analysis and Uncertainty Quantification (Priority: P3)

- [X] T028 [P] **Test Trajectory Output Schema**: `tests/contract/test_trajectory_schemas.py::test_trajectory_output_schema` validates `data/processed/trajectory_results.json` contains keys `{ "species", "year", "shift_magnitude", "shift_direction", "p_value" }`.
 **Output**: `tests/contract/test_trajectory_schemas.py`.
 **Dependency**: T031c_permutation.

- [X] T029 [P] **Integration Test for Route Shift Detection**: `tests/integration/test_trajectory_analysis.py::test_route_shift_detection` runs the full trajectory pipeline on a synthetic null dataset and asserts `p_value > 0.05`.
 **Output**: `tests/integration/test_trajectory_analysis.py`.
 **Dependency**: T031c_permutation.

- [X] T030 [S] [US3] **Compute Weekly Migration Centroids on Riemannian S² Manifold**:
 **Action**: Implement `src/models/trajectory.py::compute_weekly_centroids` that aggregates preprocessed observations per species‑year per week.
 **Logic**:
 1. Project lat/lon to **S2 manifold** coordinates using `geomstats.geometry.hypersphere.Hypersphere`.
 2. Compute the **Fréchet mean** of the weekly points on the manifold using geomstats' manifold-based statistics.
 3. Convert mean back to lat/lon.
 **Output**: `data/interim/weekly_centroids.parquet`.
 **Requirement**: Use `geomstats` for S2 manifold operations. Do NOT use Euclidean distance or linear regression. This implements the Spec's requirement for Riemannian manifold operations (FR-006). Must wait for T015b to complete and produce outputs before starting.
 **Dependency**: T015b (preprocessed data).

- [X] T031a_manifold [S] [US3] **Compute Riemannian Trajectory Statistics on S² Manifold**:
 **Action**: Use the centroids from T030 to compute trajectory-level statistics on the S2 manifold.
 **Logic**:
 1. Compute the variance of weekly centroids using geodesic distance on the manifold.
 2. Perform trajectory analysis using manifold-based statistics: parallel transport, geodesic regression.
 3. Calculate shift vectors based on the difference in manifold parameters between years.
 **Output**: `data/interim/trajectory_statistics.json` containing `variance`, `regression_coefficients`, `shift_vectors`.
 **Requirement**: Use `geomstats` for manifold operations. This implements the Spec's requirement for manifold-based trajectory statistics (FR-006).
 **Dependency**: T030 (weekly centroids).

- [X] T031b_manifold [S] [US3] **Detect Spatial Route Shifts Using Riemannian Statistics**:
 **Action**: Use the trajectory statistics computed in T031a_manifold to detect spatial route shifts.
 **Logic**:
 1. Compare trajectories across years using the manifold regression coefficients.
 2. Calculate the **shift vector** (magnitude and direction) based on the difference in manifold parameters.
 3. Prepare the data structure for the permutation test in T031c_permutation.
 **Output**: `data/interim/shift_candidates.json` containing `species`, `year`, `shift_vector`, `magnitude`, `direction`.
 **Requirement**: Use `geomstats` for manifold operations. Must wait for T031a_manifold to complete and produce outputs before starting.
 **Dependency**: T031a_manifold (Trajectory Statistics).

- [X] T031c_permutation [S] [US3] **Riemannian Trajectory Analysis & Permutation**:
 **Action**: For each species, perform **exactly 10,000** permutation shuffles (as mandated by Spec FR-005) on the **shift vectors** generated in T031b_manifold to derive the p-value. If runtime exceeds `config.MAX_PERMUTATION_RUNTIME_HOURS` (default 6), the pipeline logs the failure, reduces the shuffle count to **1000**, flags the result as "fallback" in the output, and continues (no pipeline failure).
 **Test**:
 1. **Shuffling Strategy**: Shuffle species-year labels relative to the observed shift vectors while preserving the temporal structure of the trajectory.
 2. **Test Statistic**: Euclidean distance between the mean shift vector of the observed data and the mean shift vector of the permuted data.
 3. **P-value**: Proportion of permuted statistics >= observed statistic.
 4. **Error Handling**: If T031b_manifold produces no valid candidates, log a warning and skip.
 **Output**: `data/processed/trajectory_results.json` containing `shift_vector`, `magnitude`, `direction`, and `p_value`, and `fallback` flag, `reduced_n`.
 **Requirement**: Must attempt 10000 shuffles. If `config.MAX_PERMUTATION_RUNTIME_HOURS` is exceeded, reduce to 1000 shuffles and set `fallback=true`, `reduced_n=1000`. No pipeline failure. Must wait for T030, T031a_manifold, T031b_manifold to complete and produce outputs before starting.
 **Dependency**: T030, T031a_manifold, T031b_manifold, T045a (Lock).

- [X] T033a [S] **Generate Unified 95% Confidence Intervals**:
 **Action**: Implement `src/analysis/bootstrap.py::generate_unified_ci` that:
 1. Performs block bootstrap (preserving temporal autocorrelation) on **GAMM model predictions** (from T023a_gamm_gp) to generate 95% CIs.
 2. Performs block bootstrap on the **centroid estimation process** (resampling weekly observations) to generate 95% CIs for trajectory shifts.
 3. **Aggregation Logic**: Combine GAMM prediction intervals and centroid estimation intervals into a single schema. For model predictions, use the **Union of intervals** (min lower, max upper) to ensure coverage. For trajectory shifts, use the **Bootstrap distribution of centroid shifts** to generate the final CI.
 4. Output `data/processed/uncertainty_quantification.json` with unified CI schema.
 **Logic**: Use **moving block bootstrap** with **block_size=4 weeks**.
 **Dependency**: T023a_gamm_gp (model fits), T030 (weekly centroids), T045a (Lock), T045b (Lock Integration).
 **Requirement**: Must use block bootstrap, not simple permutation. Must explicitly define aggregation logic (Union of intervals).

- [X] T033b [S] **Calculate CI Width Metrics**:
 **Action**: Compute `ci_width = ci_upper - ci_lower` for each phenology and trajectory CI from `data/processed/uncertainty_quantification.json` (from T033a), compare against `config.DEFAULT_CI_WIDTH_TARGET` (for reporting only), and write summary to `data/processed/ci_width_report.json`.
 **Requirement**: Must wait for T033a and T025c to complete and produce outputs before starting.
 **Dependency**: T033a, T025c.

## Phase 6: Orchestration & Validation (SC‑001 to SC‑005)

- [X] T043a [S] **Define Success Criteria Targets**:
 **Action**: Read plan.md "Success Criteria & Fallbacks" section and write `data/processed/target_definitions.json` with concrete thresholds. Use these concrete values: sc002_target = 0.95, sc003_target = 0.90, sc004_target = 7. **Explicitly document the source**: The Spec defines these targets as '[deferred]' (unknown). The Plan provides fallback values. The output JSON MUST include `spec_status: "deferred"` and `plan_fallback_source: "Plan Success Criteria & Fallbacks section"`. Do NOT hardcode values without this context.
 **Output**: `data/processed/target_definitions.json`.
 **Dependency**: None.

- [X] T043b [S] **Implement Power Analysis Script**: Write `src/analysis/power_analysis.py` to calculate statistical power and effect size stability (SC-001) based on the total number of migratory species and model results. Output `data/processed/power_report.json`.
 **Dependency**: T023a_gamm_gp (model fits).

- [X] T043c1 [S] **Measure SC-002 (Insufficient Data Proportion)**:
 **Action**: Read `data/processed/preprocessed_data.parquet` (from T018), count rows with `data_quality="insufficient"`, and calculate the proportion of total grid cells. Compare against `data/processed/target_definitions.json` (SC-002 target). Explicitly report the spec's '[deferred]' target vs the plan's fallback.
 **Output**: `data/processed/insufficient_data_report.json` containing `total_cells`, `insufficient_cells`, `proportion`, `target`, `pass/fail`, `spec_target_note`.
 **Requirement**: Explicitly generates the `metadata_insufficient_cells.json` artifact referenced by T043. Must flag if the spec's '[deferred]' target is not explicitly resolved.
 **Dependency**: T015b, T043a.

- [X] T043c2 [S] **Measure SC-003 (Convergence Rate)**:
 **Action**: Read `logs/modeling.log` and `data/processed/model_results_final.parquet` to compute convergence rate (successful fits / total attempts). Compare against `data/processed/target_definitions.json` (SC-003 target).
 **Output**: `data/processed/convergence_report.json` containing `total_attempts`, `successful_fits`, `convergence_rate`, `target`, `pass/fail`.
 **Dependency**: T027, T043a.

- [X] T043d [S] **Calculate CI Width Metrics**: Read `data/processed/ci_width_report.json` (from T033a3) and compare against `data/processed/target_definitions.json`. Store in `data/processed/ci_width_target_report.json`.
 **Dependency**: T033b and T043a.

- [X] T043 [S] **Calculate and Report All Success Criteria**:
 **Logic**:
 1. **SC‑001 (Power)** – Use output from T043b and T025e.
 2. **SC‑002 (Insufficient Data)** – Use output from T043c1 (which generates `data/processed/metadata_insufficient_cells.json`).
 3. **SC‑003 (Convergence)** – Use output from T043c2.
 4. **SC‑004 (CI Width)** – Use output from T043d.
 5. **SC‑005 (Runtime)** – Run `src/analysis/runtime_validation.py` to ensure total pipeline runtime < 6 h; store result in `data/processed/runtime_report.json`. If runtime exceeds 6 hours, the pipeline fails (no fallback).
 **Aggregated Output**: Combine all five JSON reports into a single `data/processed/final_success_report.json`.
 **Requirement**: All targets are now defined in `target_definitions.json` with explicit Spec/Plan distinction. Must wait for T043a, T043b, T043c1, T043c2, T043d, T025c, T027, T033b to complete and produce outputs before starting.
 **Dependency**: T043a, T043b, T043c1, T043c2, T043d, T025c, T027, T033b, and all preceding analysis tasks.

## Phase 7: Polish & Cross‑Cutting Concerns

- [X] T036 [P] **Update README** with installation instructions and `python -m src.cli.run_pipeline --help`.
 **Dependency**: T002a.

- [X] T037 [P] **Create docs/api.md** with docstrings for all public functions in `src/data/preprocess.py`.
 **Dependency**: T015b.

- [X] T038a [P] **Run Ruff Auto‑Fix** on `src/`.
 **Dependency**: T003a_2.

- [X] T038b [P] **Add Pre‑commit Hook for Docstring Validation**.
 **Dependency**: T003b.

- [X] T040a [P] **Add unit test for empty input in `src/data/preprocess.py`**.
 **Dependency**: T015b.

- [X] T040b [P] **Add unit test for single species in `src/models/gamm_fit.py`**.
 **Dependency**: T023a_gamm_gp.

- [X] T040c [P] **Add unit test for missing data handling in `src/data/impute.py`**.
 **Dependency**: T007.

- [X] T041a [P] **Create `.github/workflows/ci.yml`**.
 **Dependency**: T002a.

- [X] T041b [P] **Define `validate_quickstart` job in CI workflow**.
 **Action**: Include a pre-check step to validate task ordering in `tasks.md` (ensuring verify tasks follow their producers).
 **Dependency**: T041a.

- [X] T041c [P] **Add runtime assertion (< 6 h) to `validate_quickstart` job**.
 **Dependency**: T041b.

- [X] T005c5 [S] **Pre-Execution Ordering Validator**:
 **Action**: Write script `src/cli/validate_task_order.py` that parses `tasks.md` and verifies that all "verify" or "test" tasks (e.g., T013, T021) appear AFTER their producer tasks (e.g., T015b, T023a) in the dependency graph.
 **Logic**: Parse the `Dependency` field in each task header. Verify that for every task `T_x`, all tasks listed in its `Dependency` field appear earlier in the file than `T_x`. If any verify task depends on a task that has not been executed (or is listed after it in the file), raise `RuntimeError` with message "Task ordering violation: <task_id> must run after <producer_id>".
 **Requirement**: This task runs in the CI workflow (T041b) as a check, not as a Phase 0 execution task. It prevents the pipeline from starting if `tasks.md` is malformed.
 **Output**: Exit code 0 on success, 1 on failure.
 **Dependency**: T002a.

- [X] T045c [S] **Document Lock Usage**: Add section to `docs/locking.md` describing when and how the lock is used, and update any relevant README sections.
 **Dependency**: T045b.

## Phase 8: Reporting & Documentation (Moved from Phase 7)

**Purpose**: Final reporting and documentation updates.

- [X] T052 [S] **Enforce Real Data Fetch Failing Loudly**:
 **Action**: Review `src/data/download.py` and `src/data/fetch_species.py`. Ensure there are NO `try/except` blocks that catch download errors and fall back to `generate_synthetic_*()` or mock data. If a real fetch fails, the script MUST raise `DataFetchError` with a clear message: "Failed to fetch verified real data from [URL]. Aborting pipeline to prevent fabrication." The pipeline must NOT proceed with synthetic data.
 **Requirement**: A silent synthetic fallback is fabrication. The execution stage must fail loudly to discover a verified real source. Must wait for T005a, T005b, T005c1_fetch to complete and produce outputs before starting.
 **Dependency**: T005a, T005b, T005c1_fetch.

- [X] T054 [S] **Implement Block Bootstrap for Uncertainty**:
 **Action**: Ensure `src/analysis/bootstrap.py` implements block bootstrap (preserving temporal autocorrelation) for both GAMM predictions and centroid estimation as required by FR-007 and US-3. Do NOT use simple random resampling.
 **Requirement**: Simple permutation destroys the temporal structure of migration routes, leading to invalid p-values.
 **Dependency**: T023a_gamm_gp, T030.

- [X] T055 [S] **Verify NOAA/PRISM Dataset Availability**:
 **Action**: Update T005c1_fetch to explicitly check for the NOAA/PRISM dataset availability using official API endpoints. If not found, raise a clear error and halt (unless deviation is ratified). Do NOT attempt to download from unverified URLs.
 **Requirement**: Ensures the pipeline does not proceed with missing or incorrect climate data.
 **Dependency**: T005a.

- [X] T060 [S] [US1] **Verify Task Ordering for Phenology Metrics**:
 **Action**: Update `src/cli/validate_task_order.py` to explicitly check that the task `T015b` (Preprocessing) which computes phenology metrics appears BEFORE any task that consumes them (e.g., `T023a_gamm_gp`, `T030`).
 **Logic**: Add a specific rule: "Phenology metrics must be computed before modeling". If a modeling task depends on a phenology metric that is not produced by a preceding task, raise `RuntimeError`.
 **Requirement**: This ensures the data flow is strictly respected: `T015b` (Producer) -> `T023a_gamm_gp` (Consumer). Must wait for T005c5 to complete and produce outputs before starting.
 **Dependency**: T005c5.

- [X] T061 [S] [US1] **Explicitly Document Streaming Strategy for Large Datasets**:
 **Action**: Update `src/data/stream_utils.py` and `src/data/preprocess.py` docstrings to explicitly state the streaming strategy: "Uses `datasets.load_dataset(..., streaming=True)` to process data in chunks, never loading the full dataset into RAM. Chunk size is dynamically adjusted based on available memory (target < 6 GB)."
 **Requirement**: This addresses the concern that large datasets must be streamed, not shrunk to a toy set. The code must be explicit about this strategy.
 **Dependency**: T051.

- [X] T062 [S] [US2] **Verify FDR Correction Application Scope**:
 **Action**: Review `src/models/utils.py::apply_fdr_correction` to ensure it aggregates p-values from **both** `T025d` (GAMM coefficients) and `T031c_permutation` (Spatial shifts) before applying Benjamini-Hochberg.
 **Logic**: The function must accept a list of p-values from both sources, apply FDR, and return a unified table. It must NOT apply FDR separately to each source.
 **Requirement**: This ensures the false discovery rate is controlled across the entire set of hypothesis tests (phenology-climate and spatial shifts) as per Spec FR-005.
 **Dependency**: T025c.

- [X] T063 [S] [US3] **Add Explicit Timeout Handling for Manifold Calculations**:
 **Action**: Wrap `T030` (Centroids) and `T031a_manifold` (Trajectory Statistics) in a timeout mechanism (e.g., `signal.alarm` on Unix or `multiprocessing` with timeout on Windows). If the calculation exceeds a significant duration, log a warning, save partial results if possible, and mark the task as "deferred" or "timeout".
 **Requirement**: This addresses the runtime constraint for heavy manifold calculations. It prevents the pipeline from hanging indefinitely.
 **Dependency**: T030, T031a_manifold.

- [X] T064 [S] [US3] **Validate Manifold Coordinate System**:
 **Action**: Add a unit test `tests/unit/test_manifold_coords.py` that verifies the conversion from lat/lon to S2 manifold coordinates (unit sphere) and back preserves the original location within a small tolerance (e.g., a sufficiently small degree).
 **Logic**: Test: `lat, lon` -> `S2` -> `lat', lon'`. Assert `abs(lat - lat') < tol` and `abs(lon - lon') < tol`.
 **Requirement**: This ensures the Riemannian geometry operations are performed on the correct manifold and that coordinate transformations are accurate.
 **Dependency**: T030.

- [X] T065 [S] [US3] **Document Block Bootstrap Block Size Selection**:
 **Action**: Update `src/analysis/bootstrap.py` to include a comment explaining the choice of `block_size=4 weeks`. Reference the assumption that migration phenology has a temporal autocorrelation scale of approximately 4 weeks.
 **Requirement**: This provides transparency for the statistical method used in uncertainty quantification.
 **Dependency**: T033a.