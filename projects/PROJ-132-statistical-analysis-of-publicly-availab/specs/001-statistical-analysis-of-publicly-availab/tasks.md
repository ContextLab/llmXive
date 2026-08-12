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

**Purpose**: Verify plan/spec alignment and document scope limitations before any implementation begins.

- [ ] T050b [S] [Plan] **Verify Plan & Spec Alignment (with Deviation Whitelist)**:
 **Action**: Write a Python script `src/utils/verify_alignment.py` that loads `specs/001-bird-migration-climate-correlation/spec.md` and `plan.md`. The script MUST first verify that both files exist and are non-empty. It scans for contradictory statements (e.g., data source mismatches). **CRITICAL**: Before failing, the script MUST load `data/provenance/spec_plan_deviation.json` (if it exists) and treat any contradiction listed there as a "whitelisted deviation".
 **Requirement**: Fail loudly with `RuntimeError` ONLY if contradictions exist that are NOT in the deviation whitelist. If files are missing, raise `FileNotFoundError`.
 **Output**: `reports/plan_spec_alignment.json` (or failure).
 **Dependency**: T005c3 (Deviation Documentation must exist to whitelist known issues).

## Phase 0.5: Data Source & Deviation Setup

**Purpose**: Establish data sources and document any deviations from the spec before Phase 1 begins.

- [ ] T005c3 [S] **Document Data Source Deviation**: Write JSON `data/provenance/spec_plan_deviation.json` with the following EXACT structure if a deviation occurs:
 ```json
 {
   "spec_requirement": "NOAA/PRISM (FR-001)",
   "implemented_source": "Daymet",
   "reason": "Plan explicitly substitutes NOAA/PRISM with Daymet for verified open-source availability if NOAA is unreachable. Spec FR-001 interpreted as 'download full available verified dataset'.",
   "timestamp": "<ISO8601>"
 }
 ```
 **Requirement**: Must reflect which data source was actually used. If NOAA/PRISM is used, this file may be skipped or contain `null`.
 **Dependency**: Depends on T005c1 (success) or T005c2 (success).

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T002a [P] **Create Project Structure**: Execute `mkdir -p src/data src/models src/analysis src/utils src/cli data/raw data/processed data/interim tests/contract tests/unit tests/integration docs`.
- [X] T002b_1 [P] **Verify Project Structure (Dirs 1-4)**: Write unit test `tests/unit/test_setup_structure_part1.py` asserting existence of `src/data`, `src/models`, `src/analysis`, `data/raw`.
- [X] T002b_2 [P] **Verify Project Structure (Dirs 5-8)**: Write unit test `tests/unit/test_setup_structure_part2.py` asserting existence of `data/processed`, `data/interim`, `tests/contract`, `tests/unit`, `tests/integration`, `docs`.
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
- [X] T003a_2 [P] **Verify Ruff Config Syntax**: Execute `ruff check --config pyproject.toml` to verify the Ruff configuration is syntactically correct. If the command fails, the task fails.
 **Output**: Exit code 0 on success.
- [ ] T003b [P] **Create Pre-commit Config**: Create `.pre-commit-config.yaml` with hooks for `black` and `ruff` and add installation instructions to `README.md`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes runtime optimization to meet SC‑005.

- [ ] T005a [S] **Verify Data Availability**:
 **Action**: Write script `src/data/verify_dataset.py` that attempts to load the verified eBird sample (`vvud/eb-data`) using `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)` and checks for NOAA/PRISM and Daymet availability.
 **Output**: Write `data/provenance/data_availability_report.json` with keys `{ "ebird_available": bool, "noaa_available": bool, "daymet_available": bool }`. Raise `RuntimeError` with clear message if eBird is missing.
 **Dependency**: None.
- [ ] T005b [S] **Download Verified eBird Sample**:
 **Action**: Stream the verified eBird sample (`vvud/eb-data`) via `datasets.load_dataset(..., streaming=True)`, write raw files to `data/raw/ebird_sample/` preserving original file names. Compute SHA‑256 checksums for each downloaded shard and store in `data/raw/ebird_sample/checksums.sha256`.
 **Requirement**: No synthetic fallback; abort on any download error.
 **Dependency**: Depends on T005a.
- [ ] T005c1 [S] **Download NOAA/PRISM Climate Data (Primary)**:
 **Action**: Use `datasets.load_dataset("noaa/prism",...)` to download climate variables. **Action**: First verify the dataset exists via `datasets.get_dataset_names()`. If it does not exist, raise `FileNotFoundError` with message "NOAA/PRISM not available; triggering fallback to Daymet (T005c2)" and **exit with code 1**. Write to `data/raw/noaa_prism/` as Parquet files (`noaa_2020_2024.parquet`). Compute SHA‑256 checksums.
 **Requirement**: Must be the primary source per Spec FR-001. Abort if missing to trigger fallback logic.
 **Dependency**: Depends on T005a.
- [ ] T005c2 [S] **Download Daymet Climate Data (Fallback)**:
 **Action**: **Only if T005c1 exits with code 1**. Use `datasets.load_dataset("daymet/annual",...)` to download climate variables, write to `data/raw/daymet/` as Parquet files (`daymet_2020_2024.parquet`). Compute SHA‑256 checksums.
 **Requirement**: This is a fallback only. If T005c1 succeeded, this task is skipped.
 **Dependency**: Depends on T005c1 (failure).
- [ ] T005d [P] **Archive Raw Data & Upload to CI**: Copy all raw files from `data/raw/ebird_sample/` and the active climate source (`noaa_prism` or `daymet`) to `data/raw/archive/`. **Action**: Upload this archive to CI artifacts for provenance.
 **Dependency**: Depends on T005b and (T005c1 or T005c2).
- [X] T005e [S] **Update State File**: Insert the new artifact hashes and `updated_at` timestamp into `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml`.
 **Dependency**: Depends on T005d.
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
 **Dependency**: Depends on T005a.
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
 **Action**: Write `src/data/preprocess.py` to stream eBird data (using T051), filter for migratory species (2020-2024), aggregate to 0.5° grid cells, and compute phenology metrics.
 **Logic**: Use `polars` for efficient streaming. Compute `first_arrival` (min date), `median_arrival` (median date), `stopover_duration` (90th - 10th percentile). **Output column name must be `stopover_duration`**.
 **Dependency**: Depends on T051 (Streaming), T015a (Species List), T005b (Data Download).
 **Output**: `data/processed/preprocessed_data.parquet`.
- [ ] T016 [S] **Generate Provenance Mapping**: Implement `src/data/preprocess.py::generate_provenance` that creates `data/provenance/row_mapping.json` mapping each processed row ID to its original `checklist_id`. Schema: `{ "processed_row_id": str, "original_checklist_id": str, "species": str, "grid_cell": str }`.
 **Dependency**: Depends on T015b (Preprocessing must complete first to generate rows to map).
- [X] T017a [S] **Compute Phenology Metrics**: Write `src/data/preprocess.py::compute_phenology` that takes the aggregated grid data and calculates `first_arrival_date`, `median_arrival_date`, and `stopover_duration` using the logic defined in T015b.
 **Output**: `data/processed/preprocessed_data.parquet` (updated).
- [X] T017b [S] **Calculate Seasonal Climate Averages & Impute Missing Values**: Write `src/data/preprocess.py::calculate_climate_averages` to join with climate data, compute seasonal averages (Mar-May), and use `src/data/impute.py` to fill missing values. Flag imputed rows.
 **Output**: `data/processed/preprocessed_data.parquet` (updated).
- [X] T017d [P] **Verify Imputation Metadata**: Write unit test `tests/unit/test_imputation_metadata.py::test_imputation_metadata_exists` that checks for file `data/processed/imputation_metadata.json`, validates JSON schema, and asserts that every record with `is_imputed = true` has a non‑null `imputation_source`.
 **Dependency**: Depends on T017b.
- [X] T018 [S] **Mark Insufficient Data Cells**: Write `src/data/preprocess.py::flag_insufficient_data` to mark grid cells with fewer than `MIN_OBSERVATIONS` as `data_quality="insufficient"` and exclude them from downstream modeling.
 **Output**: `data/processed/preprocessed_data.parquet` (updated).

## Phase 4: User Story 2 – Phenology‑Climate Correlation Modeling (Priority: P2)

- [X] T021 [P] **Test GAMM Output Schema**: `tests/contract/test_gamm_schemas.py::test_gamm_output_schema` validates `data/processed/model_results_base.parquet` contains keys `{ "species", "temp_coef", "precip_coef", "p_value", "converged" }`.
 **Output**: `tests/contract/test_gamm_schemas.py`.
- [X] T022 [P] **Integration Test for GAMM Convergence**: `tests/integration/test_gamm_convergence.py::test_gamm_convergence` runs GAMM on a small synthetic dataset and asserts the `converged` flag is True for known parameters.
 **Output**: `tests/integration/test_gamm_convergence.py`.
- [ ] T023a [S] **Fit GAMM with Mandatory GP**:
 **Action**: Write `src/models/gamm.py::fit_gamm` that reads `data/processed/preprocessed_data.parquet`.
 **Logic**: Fit GAMM with a **MANDATORY a priori** Gaussian Process (GP) random effect (Matérn 3/2 kernel, length_scale=1.0) regardless of any diagnostic.
 **Formula**: `phenology_metric ~ s(temp) + s(precip) + s(extreme_weather_index) + (1 + temp | species) + gp(spatial)`.
 **Lock**: Acquire `data/interim/pipeline.lock` (via `filelock.FileLock`) before writing model results.
 **Output**: `data/processed/model_results_base.parquet`.
 **Dependency**: Depends on T015b (preprocessed data).
- [ ] T023b [S] **Compute Moran’s I Diagnostic (Post-Hoc)**:
 **Action**: Write `src/models/gamm.py::compute_morans_i` that takes the preprocessed data and the results from T023a to compute Moran's I for spatial autocorrelation of residuals.
 **Output**: `data/interim/morans_i_result.json` with schema `{"value": float}`.
 **Dependency**: Depends on T023a (GAMM fit must complete first to provide residuals).
- [X] T025a [S] **Benchmark Permutation Test**: Write `src/models/utils.py::benchmark_permutation` to run 100 shuffles and estimate runtime per 1000 shuffles. Store in `data/processed/permutation_benchmark.json`.
 **Output**: `data/processed/permutation_benchmark.json`.
- [ ] T025b [S] **Permutation Test Loop**: Execute full 10 000 permutations (config.PERMUTATIONS) in chunks of 1 000 using `src/models/utils.run_permutation_chunked`. Acquire `data/interim/pipeline.lock` before writing results. **Use `config.RANDOM_SEED` for all shuffles**. Output to `data/processed/permutation_results.json`.
 **Output**: `data/processed/permutation_results.json`.
 **Dependency**: Depends on T023a (GAMM output).
- [ ] T025c [S] **Apply FDR Correction**: Implement `src/models/utils.py::apply_fdr_correction` that takes the permutation test output, aggregates **all species-climate coefficient p-values** from the GAMM output, applies Benjamini‑Hochberg, adds a `q_value` column, and writes `data/processed/model_results_fdr.parquet`.
 **Dependency**: Depends on T025b and T023a.
- [X] T027 [S] **Implement Convergence Error Handling**: Wrap GAMM fitting in `try/except`. On convergence failure, log `"Convergence failed for species {species}: {error}"` to `logs/modeling.log` and skip that species. Add unit test `tests/unit/test_convergence_handling.py` verifying log format.
 **Dependency**: Depends on T023a.

## Phase 5: User Story 3 – Route Shift Analysis and Uncertainty Quantification (Priority: P3)

- [ ] T028 [P] **Test Trajectory Output Schema**: `tests/contract/test_trajectory_schemas.py::test_trajectory_output_schema` validates `data/processed/trajectory_results.json` contains keys `{ "species", "year", "shift_magnitude", "shift_direction", "p_value" }`.
 **Output**: `tests/contract/test_trajectory_schemas.py`.
- [X] T029 [P] **Integration Test for Route Shift Detection**: `tests/integration/test_trajectory_analysis.py::test_route_shift_detection` runs the full trajectory pipeline on a synthetic null dataset and asserts `p_value > 0.05`.
 **Output**: `tests/integration/test_trajectory_analysis.py`.
- [ ] T030 [S] **Compute Weekly Migration Centroids**: Implement `src/models/trajectory.py::compute_weekly_centroids` that aggregates preprocessed observations per species‑year per week, calculates the geodesic (great‑circle) mean latitude/longitude for each week, and writes `data/interim/weekly_centroids.parquet`.
 **Dependency**: Depends on T015b (preprocessed data).
- [ ] T031c [S] **Riemannian Manifold Trajectory Analysis & Permutation**:
 **Library**: **MANDATORY** `import geomstats`. If `geomstats` is not available, raise `ModuleNotFoundError` with message "Riemannian manifold analysis requires 'geomstats'. Euclidean fallback is not permitted per FR-006."
 **Action**: Use `geomstats.geometry.sphere.Sphere` for geodesic distances and trajectory statistics. For each species, compare trajectories across years. Perform **10,000 permutation shuffles** within this task to derive the p-value.
 **Output**: `data/processed/trajectory_results.json` containing `shift_vector`, `magnitude`, `direction`, and `p_value`.
 **Dependency**: Depends on T030.
- [ ] T033a [S] **Generate Phenology Confidence Intervals**: Implement block bootstrap (preserving weekly autocorrelation) on **GAMM model predictions**, produce `ci_lower` and `ci_upper` columns in `data/processed/model_results_fdr.parquet`.
 **Dependency**: Depends on T023a (model fits).
- [ ] T033b [S] **Generate Trajectory Confidence Intervals**: Apply block bootstrap to shift magnitudes from `trajectory_results.json`, append `ci_lower`/`ci_upper` to each record, and write to `data/processed/trajectory_results_ci.json`.
 **Dependency**: Depends on T031c.
- [ ] T033a1 [S] **Calculate CI Width Metrics**: Compute `ci_width = ci_upper - ci_lower` for each phenology and trajectory CI, compare against `config.DEFAULT_CI_WIDTH_TARGET` (for reporting only), and write summary to `data/processed/ci_width_report.json`.
 **Dependency**: Depends on T033a and T033b.

## Phase 6: Orchestration & Validation (SC‑001 to SC‑005)

- [ ] T043a [S] **Define Success Criteria Targets**: Write `src/analysis/targets.py::define_targets` to read `plan.md` fallback criteria and write `data/processed/target_definitions.json` with: `{ "sc002_target": 0.95, "sc003_target": 0.90, "sc004_target": 7.0 }`.
 **Dependency**: None.
- [ ] T043b [S] **Implement Power Analysis Script**: Write `src/analysis/power_analysis.py` to calculate statistical power and effect size stability (SC-001) based on the total number of migratory species and model results. Output `data/processed/power_report.json`.
 **Dependency**: Depends on T023a (model fits).
- [ ] T043c [S] **Calculate GAMM Convergence Rate**: Read `logs/modeling.log` and `data/processed/model_results_base.parquet` to compute convergence rate. Compare against `data/processed/target_definitions.json`. Store in `data/processed/convergence_report.json`.
 **Dependency**: Depends on T027 and T043a.
- [ ] T043d [S] **Calculate CI Width Metrics**: Read `data/processed/ci_width_report.json` and compare against `data/processed/target_definitions.json`. Store in `data/processed/ci_width_target_report.json`.
 **Dependency**: Depends on T033a1 and T043a.
- [ ] T043 [S] **Calculate and Report All Success Criteria**:
 **Logic**:
 1. **SC‑001 (Power)** – Use output from T043b.
 2. **SC‑002 (Insufficient Data)** – Compute proportion of grid cells flagged `data_quality="insufficient"` from `data/processed/metadata_insufficient_cells.json`. Compare against `data/processed/target_definitions.json`. Store in `data/processed/insufficient_data_report.json`.
 3. **SC‑003 (Convergence)** – Use output from T043c.
 4. **SC‑004 (CI Width)** – Use output from T043d.
 5. **SC‑005 (Runtime)** – Run `src/analysis/runtime_validation.py` to ensure total pipeline runtime < 6 h; store result in `data/processed/runtime_report.json`.
 **Aggregated Output**: Combine all five JSON reports into a single `data/processed/final_success_report.json`.
 **Requirement**: All targets are now defined in `target_definitions.json`.
 **Dependency**: Depends on T043a, T043b, T043c, T043d, T025c, T027, T033a1, and all preceding analysis tasks.

## Phase 7: Polish & Cross‑Cutting Concerns

- [ ] T036 [P] **Update README** with installation instructions and `python -m src.cli.run_pipeline --help`.
- [ ] T037 [P] **Create docs/api.md** with docstrings for all public functions in `src/data/preprocess.py`.
- [ ] T038a [P] **Run Ruff Auto‑Fix** on `src/`.
- [ ] T038b [P] **Add Pre‑commit Hook for Docstring Validation**.
- [ ] T039a1 [P] **Vectorize pandas operations in `src/data/preprocess.py`** (requires T018 to be complete).
- [ ] T039a2 [P] **Vectorize model operations in `src/models/gamm_fit.py`** (requires T023a to be complete).
- [ ] T039b1 [P] **Parallelize permutation tests with joblib** (requires T025b).
- [ ] T039b2 [P] **Parallelize trajectory permutation tests with joblib** (requires T031c).
- [ ] T040a [P] **Add unit test for empty input in `src/data/preprocess.py`**.
- [ ] T040b [P] **Add unit test for single species in `src/models/gamm_fit.py`**.
- [ ] T040c [P] **Add unit test for missing data handling in `src/data/impute.py`**.
- [ ] T041a [P] **Create `.github/workflows/ci.yml`**.
- [ ] T041b [P] **Define `validate_quickstart` job in CI workflow**.
- [ ] T041c [P] **Add runtime assertion (< 6 h) to `validate_quickstart` job**.

## Phase 8: Locking Infrastructure (Cross‑Cutting)

- [ ] T045a [S] **Create File‑Based Lock**: Implement `src/utils/locks.py` exposing `pipeline_lock = filelock.FileLock("data/interim/pipeline.lock")`.
- [ ] T045b [S] **Integrate Lock into Heavy Tasks**: Modify `src/models/gamm_fit.py`, `src/models/utils.py` (permutation), and `src/models/trajectory.py` to acquire `pipeline_lock` before any write to shared `data/interim/` resources.
- [ ] T045c [S] **Document Lock Usage**: Add section to `docs/locking.md` describing when and how the lock is used, and update any relevant README sections.