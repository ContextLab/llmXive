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

- [ ] T050b [S] [Plan] **Verify Plan & Spec Alignment**:  
  **Action**: Write a Python script `src/utils/verify_alignment.py` that loads `specs/001-bird-migration-climate-correlation/spec.md` and `plan.md`. The script MUST first verify that both files exist and are non-empty. It scans for contradictory statements (e.g., data source mismatches) and writes a JSON report `reports/plan_spec_alignment.json` with keys `{ "contradictions": [ { "spec_line": int, "plan_line": int, "description": str } ] }`.  
  **Requirement**: Fail loudly with `RuntimeError` if the report contains any contradictions. If files are missing, raise `FileNotFoundError` with a clear message.  
  **Output**: `reports/plan_spec_alignment.json`.  
  **Dependency**: None (runs before any other task).

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
- [X] T003a_2 [P] **Create Ruff Config**: The Ruff configuration is included above in `pyproject.toml`.
- [ ] T003b [P] **Create Pre-commit Config**: Create `.pre-commit-config.yaml` with hooks for `black` and `ruff` and add installation instructions to `README.md`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes runtime optimization to meet SC‑005.

- [ ] T005a [S] **Verify Data Availability**:  
  **Action**: Write script `src/data/verify_dataset.py` that attempts to load the verified eBird sample (`vvud/eb-data`) and Daymet climate data using `datasets.load_dataset`.  
  - eBird: `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)`  
  - Daymet: `datasets.load_dataset("daymet/annual", split="train", streaming=True)`  
  **Output**: Write `data/provenance/data_availability_report.json` with keys `{ "ebird_available": bool, "daymet_available": bool }`. Raise `RuntimeError` with clear message if either dataset is missing.  
  **Dependency**: None.
- [ ] T005b [S] **Download Verified eBird Sample**:  
  **Action**: Stream the verified eBird sample (`vvud/eb-data`) via `datasets.load_dataset(..., streaming=True)`, write raw files to `data/raw/ebird_sample/` preserving original file names. Compute SHA‑256 checksums for each downloaded shard and store in `data/raw/ebird_sample/checksums.sha256`.  
  **Requirement**: No synthetic fallback; abort on any download error.  
  **Dependency**: Depends on T005a.
- [ ] T005c1 [S] **Download Daymet Climate Data**:  
  **Action**: Use the `datasets.load_dataset("daymet/annual", ...)` to download climate variables, write to `data/raw/daymet/` as Parquet files (`daymet_2020_2024.parquet`).  
  **Requirement**: Must be the exact Daymet source as per Plan's scope note; explicitly document deviation from Spec FR-001 (NOAA/PRISM) in T005c3.  
  **Dependency**: Depends on T005a.
- [ ] T005c2 [S] **Verify Daymet Checksums**: Compute SHA‑256 checksums of the downloaded Parquet files and write to `data/raw/daymet/checksums.sha256`. Abort on mismatch.  
  **Dependency**: Depends on T005c1.
- [ ] T005c3 [S] **Document Data Source Deviation**: Write JSON `data/provenance/spec_plan_deviation.json` with `{ "spec_requirement": "NOAA/PRISM (FR-001)", "plan_implementation": "Daymet (Plan Critical Data Scope Note)", "reason": "Plan explicitly substitutes NOAA/PRISM with Daymet for verified open-source availability. Spec FR-001 interpreted as 'download full available verified dataset'.", "timestamp": "<ISO8601>" }`.  
  **Dependency**: Depends on T005c2.
- [ ] T005d [P] **Archive Raw Data & Checksums**: Copy all raw files from `data/raw/ebird_sample/` and `data/raw/daymet/` to `data/raw/archive/` and include both checksum files.  
  **Dependency**: Depends on T005b and T005c2.
- [X] T005e [S] **Update State File**: Insert the new artifact hashes and `updated_at` timestamp into `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml`.  
  **Dependency**: Depends on T005d.
- [X] T006 [P] **Schema Test for eBird Columns**: `tests/contract/test_schemas.py::test_ebird_schema_columns` asserts that the eBird DataFrame contains columns `[species, lat, lon, date, count, checklist_id]` with correct dtypes.  
- [X] T007 [S] **Implement `src/data/impute.py` for Spatial Interpolation** (unchanged).  
- [X] T009 [S] **Create Base Data Entities** (unchanged).  
- [X] T010a [S] **Define Constants** (unchanged).  
- [X] T010b [S] **Implement Logging** (unchanged).  
- [X] T010c [S] **Test Logging Format** (unchanged).  
- [ ] T051 [P] **Stream Verified Full eBird Data**: Implement `src/data/stream_utils.py` that uses `datasets.load_dataset(..., streaming=True)` to yield records in chunks of 100 000 rows, ensuring memory usage < 6 GB.  
  **Dependency**: Depends on T005a.  
- [X] T057a [S] **Implement Chunked Permutation Utility** (unchanged).  
- [X] T058a [S] **Implement Streaming Trajectory Utility** (unchanged).  

## Phase 3: User Story 1 – Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

- [X] T013 [P] **Integration Test for Data Ingestion Flow** (unchanged).  
- [X] T015a [S] **Retrieve CLO Migratory List** (unchanged).  
- [ ] T015b [S] **Implement Preprocessing Pipeline**:  
  **Action**: Write `src/data/preprocess.py` to stream eBird data (using T051), filter for migratory species (2020-2024), aggregate to 0.5° grid cells, and compute phenology metrics.  
  **Dependency**: Depends on T051 (Streaming), T015a (Species List), T005b (Data Download).  
  **Output**: `data/processed/preprocessed_data.parquet`.
- [ ] T016 [S] **Generate Provenance Mapping**: Implement `src/data/preprocess.py::generate_provenance` that creates `data/provenance/row_mapping.json` mapping each processed row ID to its original `checklist_id`. Schema: `{ "processed_row_id": str, "original_checklist_id": str, "species": str, "grid_cell": str }`.  
  **Dependency**: Depends on T015b (Preprocessing must complete first to generate rows to map).  
- [X] T017a [S] **Compute Phenology Metrics** (unchanged).  
- [X] T017b [S] **Calculate Seasonal Climate Averages & Impute Missing Values** (unchanged).  
- [ ] T017d [P] **Verify Imputation Metadata**: Write unit test `tests/unit/test_imputation_metadata.py::test_imputation_metadata_exists` that checks for file `data/processed/imputation_metadata.json`, validates JSON schema, and asserts that every record with `is_imputed = true` has a non‑null `imputation_source`.  
  **Dependency**: Depends on T017b.  
- [X] T018 [S] **Mark Insufficient Data Cells** (unchanged).  

## Phase 4: User Story 2 – Phenology‑Climate Correlation Modeling (Priority: P2)

- [X] T021 [P] **Test GAMM Output Schema** (unchanged).  
- [X] T022 [P] **Integration Test for GAMM Convergence** (unchanged).  
- [ ] T023a [S] **Fit GAMM with Mandatory GP**:  
  **Library**: Use `pygam` for smooth terms and `statsmodels` (`MixedLM`) for random effects. Implement Matérn GP random effect via `statsmodels.regression.mixed_linear_model.GaussianProcess`. Formula:  
  `phenology_metric ~ s(temp) + s(precip) + s(extreme_weather_index) + (1 + temp | species)`  
  **Lock**: Acquire `data/interim/pipeline.lock` (via `filelock.FileLock`) before writing model results.  
  **Output**: `data/processed/model_results_base.parquet`.  
  **Dependency**: Depends on T015b (preprocessed data) and T016 (provenance).  
- [X] T023b [S] **Compute Moran’s I Diagnostic** (unchanged).  
- [X] T025a [S] **Benchmark Permutation Test** (unchanged).  
- [X] T025b [S] **Permutation Test Loop** (unchanged).  
- [ ] T025c [S] **Apply FDR Correction**: Implement `src/models/utils.py::apply_fdr_correction` that takes the permutation test output, applies Benjamini‑Hochberg across all species‑climate coefficient p‑values, adds a `q_value` column, and writes `data/processed/model_results_fdr.parquet`.  
  **Dependency**: Depends on T025b.  
- [ ] T027 [S] **Implement Convergence Error Handling**: Wrap GAMM fitting in `try/except`. On convergence failure, log `"Convergence failed for species {species}: {error}"` to `logs/modeling.log` and skip that species. Add unit test `tests/unit/test_convergence_handling.py` verifying log format.  
  **Dependency**: Depends on T023a.  

## Phase 5: User Story 3 – Route Shift Analysis and Uncertainty Quantification (Priority: P3)

- [ ] T028 [P] **Test Trajectory Output Schema**: `tests/contract/test_trajectory_schemas.py::test_trajectory_output_schema` validates `data/processed/trajectory_results.json` contains keys `{ "species", "year", "shift_magnitude", "shift_direction", "p_value" }`.  
- [ ] T029 [P] **Integration Test for Route Shift Detection**: `tests/integration/test_trajectory_analysis.py::test_route_shift_detection` runs the full trajectory pipeline on a synthetic null dataset and asserts `p_value > 0.05`.  
- [ ] T030 [S] **Compute Weekly Migration Centroids**: Implement `src/models/trajectory.py::compute_weekly_centroids` that aggregates preprocessed observations per species‑year per week, calculates the geodesic (great‑circle) mean latitude/longitude for each week, and writes `data/interim/weekly_centroids.parquet`.  
  **Dependency**: Depends on T015b (preprocessed data).  
- [ ] T031c [S] **Riemannian Manifold Trajectory Analysis**:  
  **Library**: `geomstats>=2.5.0`. **NO FALLBACK ALLOWED**. If `geomstats` cannot be imported, raise `ImportError` and abort the pipeline immediately.  
  **Action**: For each species, compare trajectories across years using `geomstats.geometry.sphere.Sphere` geodesic distances and compute a shift vector (magnitude, direction). Write results to `data/processed/trajectory_results.json`.  
  **Dependency**: Depends on T030.  
- [ ] T032a [S] **Benchmark Trajectory Permutation Test**: Run a small number of shuffles to estimate runtime, store estimate in `data/processed/trajectory_permutation_benchmark.json`.  
  **Dependency**: Depends on T031c.  
- [ ] T032b [S] **Trajectory Permutation Test Loop**: Execute full 10 000 permutations (config.PERMUTATIONS) in chunks of 1 000 using `src/models/utils.run_permutation_chunked`. Acquire `data/interim/pipeline.lock` before writing results. Output to `data/processed/trajectory_permutation_results.json`.  
  **Dependency**: Depends on T031c and T032a.  
- [ ] T033a [S] **Generate Phenology Confidence Intervals**: Implement block bootstrap (preserving weekly autocorrelation) on phenology predictions, produce `ci_lower` and `ci_upper` columns in `data/processed/model_results_fdr.parquet`.  
  **Dependency**: Depends on T023a (model fits).  
- [ ] T033b [S] **Generate Trajectory Confidence Intervals**: Apply block bootstrap to shift magnitudes from `trajectory_results.json`, append `ci_lower`/`ci_upper` to each record, and write to `data/processed/trajectory_results_ci.json`.  
  **Dependency**: Depends on T032b.  
- [ ] T033a1 [S] **Calculate CI Width Metrics**: Compute `ci_width = ci_upper - ci_lower` for each phenology and trajectory CI, compare against `config.DEFAULT_CI_WIDTH_TARGET` (for reporting only), and write summary to `data/processed/ci_width_report.json`.  
  **Dependency**: Depends on T033a and T033b.  

## Phase 6: Orchestration & Validation (SC‑001 to SC‑005)

- [ ] T043 [S] **Calculate and Report All Success Criteria**:  
  **Logic**:  
  1. **SC‑001 (Power)** – Call `src/analysis/power_analysis.py` (to be implemented) and store result in `data/processed/power_report.json`.  
  2. **SC‑002 (Insufficient Data)** – Compute proportion of grid cells flagged `data_quality="insufficient"` from `data/processed/metadata_insufficient_cells.json`. Store in `data/processed/insufficient_data_report.json`. **If target is undefined, report raw proportion and note "Target undefined in spec".**  
  3. **SC‑003 (Convergence)** – Calculate GAMM convergence rate from `logs/modeling.log` (count of successful fits vs attempts) and store in `data/processed/convergence_report.json`. **If target is undefined, report raw rate and note "Target undefined in spec".**  
  4. **SC‑004 (CI Width)** – Use output from T033a1 (`ci_width_report.json`). **If target is undefined, report raw width and note "Target undefined in spec".**  
  5. **SC‑005 (Runtime)** – Run `src/analysis/runtime_validation.py` to ensure total pipeline runtime < 6 h; store result in `data/processed/runtime_report.json`.  
  **Aggregated Output**: Combine all five JSON reports into a single `data/processed/final_success_report.json`.  
  **Requirement**: No comparison to placeholder targets; simply report raw values and document any undefined targets.  
  **Dependency**: Depends on T025c, T027, T033a1, and all preceding analysis tasks.  

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T036 [P] **Update README** with installation instructions and `python -m src.cli.run_pipeline --help`.  
- [ ] T037 [P] **Create docs/api.md** with docstrings for all public functions in `src/data/preprocess.py`.  
- [ ] T038a [P] **Run Ruff Auto‑Fix** on `src/`.  
- [ ] T038b [P] **Add Pre‑commit Hook for Docstring Validation**.  
- [ ] T039a1 [P] **Vectorize pandas operations in `src/data/preprocess.py`** (requires T018 to be complete).  
- [ ] T039a2 [P] **Vectorize model operations in `src/models/gamm_fit.py`** (requires T023a to be complete).  
- [ ] T039b1 [P] **Parallelize permutation tests with joblib** (requires T025b).  
- [ ] T039b2 [P] **Parallelize trajectory permutation tests with joblib** (requires T032b).  
- [ ] T040a [P] **Add unit test for empty input in `src/data/preprocess.py`**.  
- [ ] T040b [P] **Add unit test for single species in `src/models/gamm_fit.py`**.  
- [ ] T040c [P] **Add unit test for missing data handling in `src/data/impute.py`**.  
- [ ] T041a [P] **Create `.github/workflows/ci.yml`**.  
- [ ] T041b [P] **Define `validate_quickstart` job in CI workflow**.  
- [ ] T041c [P] **Add runtime assertion (< 6 h) to `validate_quickstart` job**.  

## Phase 7: Locking Infrastructure (Cross‑Cutting)

- [ ] T045a [S] **Create File‑Based Lock**: Implement `src/utils/locks.py` exposing `pipeline_lock = filelock.FileLock("data/interim/pipeline.lock")`.  
- [ ] T045b [S] **Integrate Lock into Heavy Tasks**: Modify `src/models/gamm_fit.py`, `src/models/utils.py` (permutation), and `src/models/trajectory.py` to acquire `pipeline_lock` before any write to shared `data/interim/` resources.  
- [ ] T045c [S] **Document Lock Usage**: Add section to `docs/locking.md` describing when and how the lock is used, and update any relevant README sections.  