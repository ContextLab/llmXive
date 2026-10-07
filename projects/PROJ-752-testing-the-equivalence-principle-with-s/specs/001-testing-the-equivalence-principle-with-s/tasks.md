# Tasks: Testing the Equivalence Principle with Satellite Laser Ranging

**Input**: Design documents from `/specs/001-testing-the-equivalence-principle-with-s/`
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

- [X] T001 Create project structure via Python script: Create `code/utils/setup_project.py` to initialize directories `code/data`, `code/models`, `code/analysis`, `code/utils`, `code/tests`, `contracts`, `data/raw`, `data/processed`, `data/results`, `docs`. **Requirement**: Use `os.makedirs` with `exist_ok=True`. Do NOT use shell commands.
 **Dependency**: None.

- [X] T002 Initialize a Python project with pinned dependencies in `requirements.txt` (copy list from plan.md Technical Context)
- [X] T003 [P] Configure linting (ruff) and formatting (black)

---

## Phase 2: Research Prerequisites (Blocking for US1-US3)

**Purpose**: Complete necessary research and configuration gating to ensure scientific rigor and prevent defaulting to conservative values. **This phase must complete BEFORE Phase 3 (Foundational) to ensure config.yaml is populated before T004 attempts to load it.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete and `config.yaml` is updated.

- [ ] T048.0a [Research] **Search ADS API**: Search for peer-reviewed papers defining state-of-the-art benchmarks for Eötvös parameter precision. **Requirement**:
 1. **Endpoint**: Use ADS API endpoint: `.
 2. **Search Query**: `"Eötvös parameter limit satellite laser ranging" AND date:[2010-01-01 TO *]`.
 3. **Criteria**: Papers published after 2010 with precision < 1e-13.
 4. **Extraction Logic**: Extract the 'precision' value from the paper's abstract or results section using a regex or NLP parser (e.g., `re.search(r'precision.*?(\d+\.?\d*)\s*e\s*-?(\d+)', abstract)`). If the value is not found in the abstract, skip the paper.
 5. **Fallback**: If automated extraction fails for a paper, log a warning and flag it for manual review in `research/benchmarks.md`.
 6. **Deliverable**: Create a temporary list of candidate papers (do not write to file yet).
 **Dependency**: None (foundational research).

- [ ] T048.0b [Spec] **Create Benchmarks Artifact**: Create `research/benchmarks.md` based on T048.0a results. **Requirement**:
 1. Populate the markdown file with a table of candidate papers.
 2. Columns: Author, Year, Value (confidence interval width or upper bound), URL/DOI.
 3. Ensure all URLs/DOIs are valid.
 **Dependency**: T048.0a.

- [ ] T048.0c [Spec] **Select and Cite Benchmark**: Select the most appropriate benchmark paper from T048.0a. **Requirement**:
 1. Choose one specific paper.
 2. Extract the specific numerical value (95% CI width or upper bound).
 3. **Deliverable**: Create `research/benchmark_selection.md` with rationale.
 **Dependency**: T048.0b.

- [ ] T048.0d [Spec] **Populate Config with Benchmark & Gate**: Ensure `config.yaml` is updated. **Requirement**:
 1. Update `config.yaml` under `benchmark_values.etvos_limit` with the float value and a citation string (DOI or URL).
 2. **Gate**: If `etvos_limit` is missing or invalid, **log a warning** "Benchmark value missing. Research task T048.0d must be completed first." and set `config.benchmark_values.etvos_limit = None`. **Do NOT raise FileNotFoundError.** The pipeline must proceed to T049 to report the gap.
 **Dependency**: T048.0c.

- [ ] T048.0e [Research] **Fallback Search**: If T048.0a yields no results (strict < 1e-13), search for papers with precision < 1e-12 or broader metrics (e.g., "upper bound"). **Requirement**:
 1. Modify search query to relax precision constraint.
 2. If found, update `research/benchmarks.md` and `config.yaml` with the new value and a note indicating it is an upper bound.
 3. **Gate**: If still no results, raise `DataUnavailableError` with message "No suitable benchmark found for SC-002."
 **Dependency**: T048.0a.

**Checkpoint**: Research complete - pipeline can now proceed with validated scientific constraints (T048.0d must be completed)

---

## Phase 3: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. **Depends on Phase 2 (Research) to ensure config.yaml is ready.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Phase 2 must be fully completed before T004 runs.

- [X] T004 Implement `config.py` to load paths, hyperparams, and `verified_dataset_urls` keys from `config.yaml` (the single source of truth for configuration). **Requirement**:
 1. Load `config.yaml` which must contain `benchmark_values.etvos_limit` (populated by T048.0d).
 2. **Gate**: If `benchmark_values.etvos_limit` is missing, log a warning "Benchmark value missing. Research task T048.0d must be completed first." and set `config.benchmark_values.etvos_limit = None`. **Do NOT raise FileNotFoundError.**
 3. Do NOT default to a conservative value.
 4. **Dependency Note**: This task runs AFTER Phase 2 completion. The dependency is on the Phase 2 artifact (T048.0d) being written, not on the success of the benchmark search. If T048.0d sets the value to None, T004 proceeds and sets the config to None.
 **Dependency**: T048.0d (Artifact Availability).

- [X] T005 [P] Create `contracts/normal_point.schema.yaml` defining the SLR observation schema. **Note**: Foundational schema; no upstream dependencies, but required by T007a.
 **Dependency**: None (foundational, prerequisite for T007a).

- [X] T006 [P] Create `contracts/orbit_solution.schema.yaml` defining the orbit solution schema. **Requirement**:
 1. Create file `contracts/orbit_solution.schema.yaml`.
 2. Define fields: `orbital_elements` (object), `non_gravitational_acceleration` (number), `covariance_matrix` (array), `chi2` (number), `residuals` (array), `state` (array).
 3. Include validation rules.
 **Dependency**: None (foundational, prerequisite for T007a).

- [X] T007 [X] **Create `contracts/eotvos_result.schema.yaml`**: Define the final metric schema. **Requirement**:
 1. Create file `contracts/eotvos_result.schema.yaml`.
 2. Define fields: `eta_value` (number), `confidence_interval` (array of 2 numbers), `p_value` (number), `sensitivity_sweep_data` (object mapping string to number).
 3. Include validation rules (e.g., `eta_value` must be non-negative).
 **Dependency**: None (foundational, prerequisite for T007a).

- [X] T008 [X] **Implement Logging Module**: Create file `code/utils/logging.py`. **Requirement**:
 1. Implement standard logging configuration (file and console handlers).
 2. Define custom exception `DataUnavailableError` and `ModelError`.
 3. Ensure this module is imported by T009, T016, and T018.
 **Dependency**: None (foundational).

- [X] T007a [P] **Implement Python Dataclasses consuming schemas T005-T007**: Create file `code/models/entities.py` containing Python dataclasses for `NormalPoint`, `OrbitSolution`, and `EotvosResult`. **Requirement**:
 1. Define `NormalPoint` with fields: `timestamp` (datetime), `range` (float, meters), `satellite_id` (str), `station_id` (str), `quality_flag` (str).
 2. Define `OrbitSolution` with fields: `orbital_elements` (dict: keys 'semi_major_axis_m', 'eccentricity', 'inclination_rad', 'raan_rad', 'arg_perigee_rad', 'mean_anomaly_rad', all floats), `non_gravitational_acceleration` (float, m/s²), `covariance_matrix` (np.ndarray, shape N x N), `chi2` (float), `residuals` (np.ndarray, shape M), `state` (np.ndarray, shape (3,), position vector in meters in ITRS frame). **Note**: The `state` field is critical for T025 to calculate local gravity. The `state` vector must be defined as `np.ndarray` with shape (3,) representing the position vector in meters at the reference epoch in the ITRS frame.
 3. Define `EotvosResult` with fields: `eta_value` (float), `confidence_interval` (tuple of 2 floats), `p_value` (float), `sensitivity_sweep_data` (dict: model_name -> z_score).
 4. Ensure these classes are importable from `code/models/entities` and match the YAML schemas in T005, T006, T007.
 **Dependency**: T005, T006, T007 (Schema definitions must exist first).

- [X] T009a [P] **Generate Verified Datasets Artifact**: Create `data/verified_datasets.yaml`. **Requirement**:
 1. Populate the YAML with the canonical ILRS archive URLs for LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, and Starlette.
 2. **Base URL**: Use `.
 3. **Query Parameters**: Include the satellite ID and year range in the URL (e.g., `?satellite=LAGEOS-1&year=2023`).
 4. Include metadata: satellite_id, source_url, version, and last_verified_date.
 5. **Gate**: Do NOT perform HEAD-request verification here. Verification is handled in T009d.
 6. Ensure the file exists and is valid YAML before T009 runs.
 **Dependency**: None (foundational).

- [X] T009d [P] **Verify ILRS Satellite URLs**: Perform HEAD-request verification on URLs in `data/verified_datasets.yaml` for the 5 specific satellites. **Requirement**:
 1. Iterate through all URLs in `data/verified_datasets.yaml` specifically for LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, and Starlette.
 2. Perform a HEAD request with a timeout of 10 seconds.
 3. **Action on Failure**: If a URL fails (403, 503, timeout), log a warning, update the `verified_datasets.yaml` to mark the URL as `status: stale`, and **generate a 'Data Feasibility Gap' report** (`data/feasibility_gap_report.json`) listing the missing satellite and the error reason.
 4. **Proceed**: Do NOT fail the pipeline. The pipeline must proceed with available data, and downstream tasks (T018, T037) must consume the gap report to flag the result as "Incomplete".
 5. **Explicit Verification**: This task explicitly verifies the specific ILRS archive URLs for the 5 satellites required by FR-001 before ingestion begins.
 **Dependency**: T009a.

- [X] T009c [P] **Validate ILRS URLs**: Perform HEAD-request verification on URLs in `data/verified_datasets.yaml`. **Requirement**:
 1. Iterate through all URLs in `data/verified_datasets.yaml`.
 2. Perform a HEAD request with a timeout of 10 seconds.
 3. **Action on Failure**: If a URL fails (403, 503, timeout), log a warning, update the `verified_datasets.yaml` to mark the URL as `status: stale`, and **generate a 'Data Feasibility Gap' report** (`data/feasibility_gap_report.json`) listing the missing satellite and the error reason.
 4. **Proceed**: Do NOT fail the pipeline. The pipeline must proceed with available data, and downstream tasks (T018, T037) must consume the gap report to flag the result as "Incomplete".
 **Dependency**: T009a.

- [X] T009b [P] **Create Satellite Metadata**: Create `data/satellite_metadata.yaml`. **Requirement**:
 1. Populate with mass (kg), cross-sectional area (m²), and optical properties (reflectivity) for LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, and Starlette.
 2. Source data from published mission specifications (cite source in YAML comments).
 3. **Dependency**: T009a (to know which satellites are targeted).
 **Dependency**: T009a.

- [X] T010 Setup `pytest` framework: create `tests/conftest.py`, `pytest.ini`, and `requirements-dev.txt`

- [X] T023a [P] **Define Dynamics Specification**: Create `docs/dynamics_spec.md` detailing the exact mathematical formulation for GGM geopotential, drag, SRP, and relativity to be used in T023. **Requirement**:
 1. Document equations and constants.
 2. **Gate**: This document serves as the "Specification" for T023 tasks.
 **Dependency**: None (foundational).

**Checkpoint**: Foundation ready - research prerequisites must now be completed before user story implementation can begin

---

## Phase 4: User Story 1 - Data Ingestion and Orbit Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Download and clean SLR normal-point series for LAGEOS, Etalon, and Starlette.

**Independent Test**: Execute ingestion pipeline and verify output CSV contains ≥ 95% of available points with no NaN values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. T013a is the "Write Test" step; it depends on the *specification* of T014b (from spec.md/plan.md), not the implementation. T013a will fail initially until T014b is implemented.

- [X] T011 [P] [US1] Unit test for URL validation and backoff retry logic in `tests/test_ingestion.py`
- [X] T012 [P] [US1] Unit test for quality filtering (>2cm residual exclusion) in `tests/test_preprocessing.py`
- [X] T013a [P] [US1] **Write Integration Test**: Create `tests/test_data_pipeline.py::test_lageos1_fetch`. **Requirement**:
 1. **Write** the test to fetch LAGEOS data for the latest available full year.
 2. **Algorithm for Year Selection**: Iterate backwards from `datetime.now().year` (e.g., 2026, 2025,...). For each year, check the metadata API (or parse filenames) to verify that data for *all* target satellites (LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, Starlette) is >90% complete. Select the first year that meets this criteria. If no year is found, use the previous year as a fallback.
 3. **Assertion**: Assert `data/processed/lageos1.csv` exists.
 4. **Dynamic Count**: Calculate `expected_count` by fetching metadata first, then assert `len(df) >= expected_count * 0.95`.
 5. **Gate**: If fetch fails, the test must fail loudly (no synthetic fallback).
 6. **Partial Success**: If data exists for some satellites but not others (e.g., Etalon-2 missing), the test must assert that the system logs a warning and proceeds with available data, matching Spec US-1 Scenario 3. It must NOT fail if one satellite is missing, but must fail if the main target (LAGEOS-1) is missing.
 7. **Conditional**: If data exists but has < 10,000 rows, log a warning "Insufficient data for year" but do NOT fail the test unless the count is < 500 (minimum for arc).
 **Dependency**: spec.md (US-1, FR-001), T048.0d (Config), T009a. Note: T013a (Write) depends on the specification in spec.md, not the implementation task T014b.

- [X] T013b [US1] **Run Integration Test**: Execute `tests/test_data_pipeline.py::test_lageos1_fetch`. **Requirement**:
 1. Run the test written in T013a against the implemented code.
 2. **Dependency**: T013a (Test must be written first), T014b (Implementation must exist).
 **Dependency**: T013a, T014b.

### Implementation for User Story 1

- [X] T014b [US1] **Add `parse_slr_file` function to `code/ingestion.py`**. **Requirement**: Implement `parse_slr_file(raw_content: bytes) -> list[NormalPoint]`. Parse raw SLR files into `NormalPoint` objects (using T007a class). **Dependency**: Requires T009a (Schema definitions must exist first) and T007a.

- [X] T014c [US1] **Add `aggregate_satellites` function to `code/ingestion.py`**. **Requirement**: Implement `aggregate_satellites(satellite_ids: list[str]) -> pd.DataFrame`. Orchestrate the loop over all relevant satellites, fetch (using T009a's fetch logic), parse (using T014b), and aggregate results. **Dependency**: Requires T009a and T014b.

- [X] T016 [US1] Implement `code/preprocessing.py` to filter residuals > 2cm and handle sparse satellites. **Requirement**:
 1. **Filter Logic**: Explicitly drop rows where `abs(residual) > 0.02` (2 cm).
 2. **Logging**: Log the exact count of points excluded due to the 2 cm residual threshold to the console and record it in the metadata of the output CSV.
 3. Identify satellites with < 30 days arc length.
 **Dependency**: T014c.

- [X] T017 [US1] Implement time-alignment logic in `code/preprocessing.py` to merge multi-satellite datasets. **Dependency**: T016.

- [X] T018 [US1] **Implement Exclusion Logic**: Handle "Insufficient Data" (<30 days arc length) warnings. **Requirement**:
 1. Log a specific "Insufficient Data" warning for satellites with < 30 days of unique dates.
 2. **Explicitly exclude** the satellite from the downstream joint estimation (T024) and differential analysis.
 3. **Record** the list of excluded satellite IDs in a shared state file `data/processed/excluded_satellites.json` (or similar) that T037 can consume.
 4. Ensure T037 can read this file to flag the report as "Incomplete".
 5. **Align with Plan**: This implements the "Data Feasibility Gap" handling defined in the Plan.
 **Dependency**: T017, T008, T009.

- [X] T019 [US1] Write output to `data/processed/cleaned_slr_data.csv` with checksum verification; record checksum in `state/projects/PROJ-752-testing-the-equivalence-principle-with-s.yaml` under the `artifact_hashes` map (as per Constitution Principle III). **Requirement**:
 1. Use **SHA-256 (Wikipedia: ZFS, https://en.wikipedia.org/wiki/ZFS)** algorithm.
 2. Record under key `artifact_hashes.data/processed/cleaned_slr_data.csv`.
 3. Verify `cleaned_slr_data.csv` exists and is non-empty before checksumming.
 **Dependency**: T014c, T016, T017.

- [X] T009 [US1] **Implement Fetch with Feasibility Gap Handling**: Create `code/ingestion/downloader.py`. **Requirement**:
 1. Implement fetch logic for ILRS URLs defined in T009a.
 2. **No Hard Fail**: Do NOT perform a HEAD-request verification that fails the pipeline.
 3. **Fetch Attempt**: Attempt to fetch data. If it fails (403, 503, timeout), log the error and proceed to the next satellite.
 4. **Gap Reporting**: If a fetch fails, trigger the generation of `data/feasibility_gap_report.json` (or update the existing one) listing the missing satellite and the error reason.
 5. **Alignment**: This alignes with Plan.md "Data Feasibility" strategy: if data is missing, generate a report and proceed with available data, rather than halting.
 6. **Consumption**: Read `data/feasibility_gap_report.json` generated by T009c to handle stale URLs gracefully.
 **Dependency**: T009a, T009c.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 5: User Story 2 - Differential Acceleration Parameter Estimation (Priority: P2)

**Goal**: Run **separate** weighted least-squares orbit determination to estimate $a_c$ and $\eta$ (Primary), with Joint Fit as comparison.

**Independent Test**: Verify **separate** solver convergence (residuals < 1e-5m) and correct calculation of $\eta$ with confidence interval.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [US2] Unit test for dynamical model components (geopotential, drag, SRP, relativity) in `tests/test_dynamics.py`. **Requirement**: Test the components implemented in T023. **Dependency**: Requires T023a (Specification).
- [X] T021 [US2] Unit test for **separate** least-squares solver convergence in `tests/test_estimator.py`. **Requirement**: Verify convergence logic. **Dependency**: Requires Plan.md "Critical Methodological Update" (Separate Fits), T007a.
- [X] T022 [US2] Unit test for $\eta$ calculation and covariance propagation in `tests/test_eotvos.py`. **Requirement**: Verify math. **Dependency**: Requires Plan.md "Critical Methodological Update" (Separate Fits), T007a.

### Implementation for User Story 2

- [X] T023b [US2] **Implement Geopotential Model**: Create `code/dynamics/models.py` (or separate module) to implement GGM geopotential. **Requirement**:
 1. Input: state vector, output: acceleration vector (ITRS coordinates, using `astropy.coordinates`).
 2. **Explicitly implement** GGM geopotential (e.g., GGM05C).
 3. **Parameterization**: Accept satellite-specific properties (mass, cross-sectional area, reflectivity) as input parameters.
 **Dependency**: T023a (Specification - docs/dynamics_spec.md), T007a.

- [X] T023c [US2] **Implement Drag Model**: Extend `code/dynamics/models.py` to include Jacchia drag. **Requirement**:
 1. Implement Jacchia drag model.
 2. **Verification**: Add a test or log entry confirming the component is active.
 **Dependency**: T023a, T007a, T009b (Metadata).

- [X] T023d [US2] **Implement SRP Model**: Extend `code/dynamics/models.py` to include Solar Radiation Pressure (SRP). **Requirement**:
 1. Implement SRP model using satellite optical properties.
 2. **Verification**: Add a test or log entry confirming the component is active.
 **Dependency**: T023a, T007a, T009b (Metadata).

- [X] T023e [US2] **Implement Relativistic Corrections**: Extend `code/dynamics/models.py` to include relativistic corrections. **Requirement**:
 1. Implement standard relativistic corrections (e.g., Schwarzschild, Lense-Thirring).
 2. **Verification**: Add a test or log entry confirming the component is active.
 **Dependency**: T023a, T007a.

- [X] T023f [US2] **Implement Force Calculator**: Create `code/dynamics/force_calculator.py`. **Requirement**:
 1. Implement function `calculate_expected_non_gravitational_forces(satellite_metadata: dict, state: np.ndarray) -> np.ndarray`.
 2. Use satellite metadata (from Tb) to compute composition-dependent forces (Drag, SRP).
 3. **Output**: Return the expected acceleration vector.
 4. **Critical Methodology**: This module must be used in T024a/T024 to subtract expected forces from observed differences to isolate the WEP signal.
 **Dependency**: T009b, T023b, T023c.

- [X] T024a [US2] **Implement Separate Fit Baseline (PRIMARY)**: Create `code/models/estimator.py` (or separate module) to implement a standard separate least-squares fit for each satellite. **Requirement**:
 1. Implement `separate_fit_satellite(satellite_data: pd.DataFrame, model_params: dict) -> OrbitSolution`.
 2. Run this for both satellites in the pair.
 3. **Output**: Store results in `data/results/separate_fits.json`. The JSON must contain `OrbitSolution` objects for each satellite.
 4. **Deliverable**: Ensure `separate_fits.json` exists, is valid JSON, and contains `OrbitSolution` objects.
 5. This is the **PRIMARY** implementation required by FR-003 (Separate Fits).
 6. **Do NOT calculate `ac_anomalous` here.** This task only estimates orbital elements and non-gravitational accelerations.
 **Dependency**: T007a, T023a, T023b, T023c, T023d.

- [X] T024b [US2] **Calculate Differential Acceleration from Separate Fits**: Create `code/analysis/eotvos.py` (or separate module). **Requirement**:
 1. **Input**: Consumes `OrbitSolution` objects from T024a.
 2. **Call T023e**: Use `force_calculator` (T023e) to compute expected non-gravitational forces for each satellite using the estimated orbital elements.
 3. **Calculate Anomaly**: Compute `ac_anomalous = (a_obs_1 - a_obs_2) - (a_expected_1 - a_expected_2)`.
 4. **Output**: Return dictionary `{'ac_anomalous': float, 'covariance': np.array}`.
 5. **Deliverable**: Save this dictionary to `data/results/separate_ac_anomalous.json`.
 6. **Critical Methodology**: This task explicitly derives the WEP signal from the difference in estimated non-gravitational accelerations as required by FR-003.
 **Dependency**: T024a, T023e.

- [X] T024 [US2] **Implement JointLeastSquaresSolver (Comparison)**: Create `code/models/estimator.py` (extend). **Requirement**:
 1. Define class `JointLeastSquaresSolver` following the methodology in **Plan.md "Critical Methodological Update"** (Joint Weighted Least-Squares).
 2. Implement `stack_residuals(residuals_sat1: List[np.array], residuals_sat2: List[np.array]) -> np.array`.
 3. Implement `estimate_parameters(stacked_residuals: np.array, model_params: dict) -> OrbitSolution` (using T007a class). **Note**: This is a secondary comparison to T024a.
 4. Use **Levenberg-Marquardt** algorithm with **tol=1e-8** convergence tolerance.
 5. **Mathematical Definition**: Implement the joint estimator that minimizes the stacked residual vector $R = [r_1, r_2]^T$ with respect to the combined parameter vector $\theta = [\theta_1, \theta_2, a_c]^T$, where $a_c$ is the differential acceleration term.
 6. **Initial Guess**: Use TLE data for initial orbital elements.
 7. **Weighting**: Use inverse variance weights derived from observation metadata.
 8. **Parameter Ordering**: [theta1, theta2, ac].
 9. **Gate**: Verify `plan.md` "Critical Methodological Update" reflects Joint methodology before proceeding.
 10. Ensure the solver directly estimates the differential acceleration $a_c$ as defined in the Plan.
 11. **Subtract Expected Forces**: Use `force_calculator` (T023e) to compute expected non-gravitational forces and subtract them from the observed difference.
 12. **Note**: This is a comparison method. It runs in parallel with T024a and does not block T025a or T025b.
 **Dependency**: T024a (Separate Fits must be ready first), T007a, T023a, T023b, T023c, T023d, T023e.

- [X] T025 [US2] **Extract Joint Parameters**: Create `code/analysis/eotvos.py` (or extend). **Requirement**:
 1. **Input**: Consumes the `OrbitSolution` object returned by T024 (Joint Fit).
 2. Extract position vector `r` from `solution.state` (OrbitSolution object from T007a).
 3. **Calculate `g` using instantaneous orbital radius**: For each epoch in the solution, calculate `r = |state|` (Euclidean norm of the position vector). Then calculate `g = GM / r^2` (where GM is `astropy.constants.GM_earth`). **Do NOT use a single mean orbital radius.** Average the resulting `g` values over the arc to get the final `g` for the calculation.
 4. Extract `ac` and `covariance` from the joint solution.
 5. **Output**: Return dictionary `{'ac': float, 'g': float, 'covariance': np.array}`.
 6. **Deliverable**: Save this dictionary to `data/results/joint_parameters.json`.
 **Note**: This extracts the *differential* parameter directly as defined in `Plan.md`. **Dependency**: T024, T007a.

- [X] T025a [US2] **Extract Separate Parameters**: Create `code/analysis/eotvos.py` (or extend). **Requirement**:
 1. **Input**: Consumes the `OrbitSolution` objects returned by T024a (Separate Fits).
 2. **Calculate `g`**: Compute `g` using the instantaneous orbital radius for each satellite (similar to T025: `g = GM / |state|^2` averaged over the arc). Use `astropy.constants.GM_earth`.
 3. **Extract `ac_anomalous`**: Retrieve the `ac_anomalous` value calculated in T024b.
 4. **Output**: Return dictionary `{'ac_anomalous': float, 'g': float, 'covariance': np.array}`.
 5. **Deliverable**: Save this dictionary to `data/results/separate_parameters.json`.
 **Dependency**: T024a, T024b, T007a.

- [X] T025b [US2] **Implement Consistency Check**: Create `code/analysis/eotvos.py` (or extend) to verify the joint estimate against the separate-fit baseline. **Requirement**:
 1. Compare the joint estimate of $a_c$ (from T025) with the separate-fit difference (from T024b).
 2. **Explicitly calculate** the 2-sigma threshold using the joint covariance matrix from T024 and the separate covariance from T024a.
 3. Verify the difference is within this -sigma range.
 4. Log a warning if the consistency check fails.
 5. Include the consistency check result in the final report.
 6. **Dependency Note**: This task depends on T024a and T025a (Separate method). T024 (Joint) is optional for this check; if T024 is not run, T025b can still proceed with the separate method results.
 **Dependency**: T024a, T024b, T025a, T007a. (T024 is optional).

- [X] T026 [US2] Implement `code/analysis/eotvos.py` to compute $\eta = |a_c| / g$ and 95% CI. **Requirement**:
 1. **Input**: Consumes the output dictionary of T025 (Joint) AND T025a (Separate).
 2. Calculate $\eta$ for both methods.
 3. Propagate covariance to calculate 95% CI.
 **Dependency**: T025, T025a.

- [X] T027 [US2] Implement fallback logic for non-convergence (relax tolerance, log warning, output best-fit) as authorized by plan robustness requirements. **Requirement**:
 1. Handle non-convergence for both Joint (T025) and Separate (T025a) methods.
 2. Log warning and output best-fit parameters.
 **Dependency**: T025, T025a, T026.

- [X] T028 [US2] Save `OrbitSolution` and `EotvosResult` to `data/results/orbit_solutions.json` and `data/results/eotvos_metrics.json`. **Requirement**:
 1. Save results for both Joint and Separate methods.
 **Dependency**: T027, T026, T025a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Statistical Validation and Robustness Analysis (Priority: P3)

**Goal**: Perform F-test/BIC comparison and geopotential sensitivity analysis.

**Independent Test**: Verify sensitivity plot generation and correct application of multiple-comparison corrections.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [US3] Unit test for F-test and BIC calculation logic in `tests/test_validation.py`
- [X] T030 [US3] Unit test for Bonferroni/Holm-Bonferroni/Benjamini-Hochberg correction logic in `tests/test_validation.py`
- [X] T031 [US3] Integration test: Verify sensitivity sweep across multiple geopotential models in `tests/test_sensitivity.py`

### Implementation for User Story 3

- [X] T032a [US3] **Implement Validation Data Structures**: Create `code/analysis/validation.py` and define `ValidationResult` and `SensitivityReport` dataclasses. **Requirement**:
 1. Define `ValidationResult` with fields: `chi2_null`, `chi2_alt`, `F_statistic`, `p_value`, `BIC`.
 2. Define `SensitivityReport` with fields: `results_per_model`, `z_score_variation`, `final_flag`.
 **Dependency**: None (foundational for US3).

- [X] T032d [US3] **Calculate Chi-Square Improvement**: Implement function `calculate_chi2_improvement(null_model: OrbitSolution, alt_model: OrbitSolution) -> float`. **Requirement**:
 1. Calculate $\Delta \chi^2 = \chi^2_{null} - \chi^2_{alt}$.
 2. Return the value.
 **Dependency**: T032a.

- [X] T032e [US3] **Compute F-test and p-value**: Implement function `compute_f_test(chi2_null, chi2_alt, dof_null, dof_alt) -> dict`. **Requirement**:
 1. Calculate F-statistic and p-value.
 2. Return dictionary with `F_statistic` and `p_value`.
 **Dependency**: T032a.

- [X] T032f [US3] **Compute BIC**: Implement function `compute_bic(chi2, dof, n) -> float`. **Requirement**:
 1. Calculate BIC.
 2. Return the value.
 **Dependency**: T032a.

- [X] T032 [US3] **Implement Validation Logic**: Combine T032a, T032d, T032e, T032f into `code/analysis/validation.py` function for F-test and BIC model comparison (Null vs Alternative). **Requirement**:
 1. Calculate $\chi^2$ for Null model ($\chi^2_{null}$) and Alternative model ($\chi^2_{alt}$).
 2. Calculate F-statistic and p-value.
 3. **Output**: Return a `ValidationResult` object (from T032a) containing `chi2_null`, `chi2_alt`, `F_statistic`, `p_value`, and `BIC`.
 **Dependency**: T032a, T032d, T032e, T032f.

- [X] T033a [US3] Implement `code/analysis/validation.py` function `iterate_geopotential_models(models: list[str]) -> Iterator[str]`. **Requirement**:
 1. **Enforce Required Models**: The default list MUST be `['GGM05C', 'EGM2008', 'GOCO06s']`.
 2. **Validation**: If the input list does not contain at least these three models, raise a `ValueError` with message "FR-005 violation: Required geopotential models (GGM05C, EGM2008, GOCO06s) missing."
 3. Implement the iteration logic over the validated list.
 **Dependency**: None (foundational for US3).

- [X] T033b [US3] Implement `code/analysis/validation.py` function `run_sensitivity_per_model(model: str, data: pd.DataFrame) -> EotvosResult`. **Requirement**: Run the estimator per model and collect results.
- [X] T033c [US3] Implement `code/analysis/validation.py` function `aggregate_sensitivity_results(results: list[EotvosResult]) -> SensitivityReport`. **Requirement**: Aggregate and report the sensitivity sweep results (using T032a class).
- [X] T034 [US3] Implement `code/analysis/validation.py` function `apply_correction(p_values: List[float], method: str = 'bonferroni') -> List[float]`. **Requirement**:
 1. **Default**: Use Bonferroni if method is not specified.
 2. **Implement Logic**: Explicitly implement logic for **Bonferroni**, **Holm-Bonferroni**, and **Benjamini-Hochberg** methods as required by FR-006.
 3. **Error Handling**: Raise `ValueError` if method is not in ['bonferroni', 'holm-bonferroni', 'benjamini-hochberg'].
 4. **Input**: Accept unsorted p-values.
 5. Return corrected p-values.
 **Dependency**: T032.

- [X] T035 [US3] Implement logic to flag "Unreliable" if Z-score variation > 20% across models
- [X] T036 [US3] Generate sensitivity plot and save to `data/results/sensitivity_analysis.png`. **Requirement**:
 1. Use aggregated sensitivity results from T033c.
 2. Plot Z-scores per geopotential model.
 **Dependency**: T035, T033c.
- [X] T037 [US3] Implement `code/analysis/report.py` to generate diagnostic report. **Requirement**:
 1. Consume `ValidationResult` from T032.
 2. **Explicitly calculate** $\Delta \chi^2 = \chi^2_{null} - \chi^2_{alt}$ (based on spec.md FR-007 definition).
 3. Include $\Delta \chi^2$, F-statistic, p-value, and $\eta$ limit in the report.
 4. Output residuals CSV.
 5. **Flagging**: Check the `excluded_satellites` list from `data/processed/excluded_satellites.json` (T018). If non-empty, explicitly set `report_status = "Incomplete"` in the report.
 6. **Align with Plan**: This implements the "Data Feasibility Gap" reporting logic defined in the Plan.
 **Dependency**: T032, T018, T049, T036.
- [X] T049 [US3] **Validate SC-002**: Implement logic in `code/analysis/report.py` to retrieve "current state-of-the-art benchmarks" for the Eötvös parameter precision from `config.paths.benchmark_values.etvos_limit`. **Requirement**:
 1. **Gate**: If `etvos_limit` is missing from config (i.e., Phase 2.5 not completed), **raise `DataUnavailableError`** with message "Benchmark value missing. Research task T048.0d must be completed first." **Do NOT log a warning and proceed.**
 2. Compare the calculated 95% CI width (from T026) against `etvos_limit`.
 3. **Output**: Generate a definitive `precision_goal_met` boolean and a textual status ("Pass" or "Fail") based on the comparison.
 4. Report the result in the final diagnostic report, fulfilling SC-002 validation.
 **Dependency**: Phase 2.5 (T048.0d), T026, T037.

- [X] T049b [US3] **Implement Precision Comparison Logic**: Create `code/analysis/report.py` function `compare_precision(ci_width: float, benchmark: float) -> dict`. **Requirement**:
 1. **Input**: `ci_width` (float), `benchmark` (float from config).
 2. **Logic**: If `ci_width <= benchmark`, set `status = "Pass"`, `precision_goal_met = True`. Else, set `status = "Fail"`, `precision_goal_met = False`.
 3. **Output**: Return dictionary with `status`, `precision_goal_met`, `ci_width`, `benchmark`.
 4. **Integration**: Call this function in T037 to generate the "Precision Status" flag required by SC-002.
 **Dependency**: T049.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: User Story 4 - Compute Feasibility & Resource Validation (Priority: P4)

**Goal**: Validate pipeline execution within GitHub Actions free-tier constraints (time limits, CPU, and RAM).

**Independent Test**: Run full pipeline on subset and verify completion time < 6 hours.

### Implementation for User Story 4

- [X] T038 [P] [US4] Implement `code/cli/main.py` entry point with CLI arguments, runtime monitoring, and memory profiling. **Requirement**:
 1. Use `psutil.Process().memory_info().rss` to monitor RAM.
 2. **Polling Interval**: Check memory every 5 seconds.
 3. Log a warning if RAM > 6GB AND **exit with code 1** if the limit is exceeded to prevent runner hangs.
 4. **Error Message**: Must be exactly: `CRITICAL: Memory limit (GB) exceeded. Current RSS: {rss_mb}MB`.
 5. **Timing Gate**: Implement a global timer for the full pipeline. If total time > 6 hours, log warning and exit with code 124.
 6. **Bottleneck Analysis**: If the 6-hour limit is exceeded, output a specific report identifying the stage with the longest duration and its percentage of total runtime.
 7. **Constraint**: Verify CPU-only execution (no GPU imports).
 8. **Logging**: Log timing and memory data to `data/logs/resource_monitor.log` in CSV format with header `timestamp, rss_mb, elapsed_s, memory_limit_exceeded` and comma delimiter.
 **Dependency**: None.

- [X] T040 [P] [US4] Create `tests/test_feasibility.py` to run pipeline on 1-year subset and assert time < 6h. **Requirement**:
 1. Write test to verify T038 functionality.
 2. **TDD**: This test is written based on the specification of T038, not its implementation.
 **Dependency**: None (specification of T038).

- [X] T041 [US4] Document performance benchmarks and resource usage in `docs/performance.md`. **Requirement**:
 1. Include results from T040.
 2. Include resource usage data from T038.
 **Dependency**: T038, T040.

**Checkpoint**: Feasibility validated for CI environment

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042a [P] **Documentation**: Create `README.md` with installation instructions, usage examples, and contribution guidelines. **Requirement**: Include badges for CI status and coverage.
 **Dependency**: Phase 6 (US3) complete.

- [ ] T042b [P] **Documentation**: Create `docs/API_REFERENCE.md` with docstrings for all public functions in `code/`. **Requirement**: Use Sphinx or MkDocs format.
 **Dependency**: Phase 6 (US3) complete.

- [ ] T042c [P] **Documentation**: Create `docs/QUICKSTART.md` with a step-by-step guide to run the pipeline from scratch. **Requirement**: Include a "Quick Start" section and a "Troubleshooting" section.
 **Dependency**: Phase 6 (US3) complete.

- [ ] T042d [P] **Documentation**: Update `docs/dynamics_spec.md` with final implementation notes and any deviations from the spec.
 **Dependency**: Phase 6 (US3) complete.

- [X] T043 Code cleanup and refactoring of `code/models/dynamics.py` for readability

- [X] T044 Performance optimization: Vectorize `code/data/preprocessing.py` operations using NumPy

- [ ] T045a [P] **Unit Tests**: Create `tests/unit/test_edge_cases.py` to test missing data, empty results, and invalid inputs. **Requirement**: Cover all edge cases listed in the spec.
 **Dependency**: Phase 6 (US3) complete.

- [ ] T045b [P] **Unit Tests**: Create `tests/unit/test_validation.py` to test F-test, BIC, and multiple comparison corrections.
 **Dependency**: Phase 6 (US3) complete.

- [ ] T045c [P] **Unit Tests**: Create `tests/unit/test_ingestion.py` to test URL validation, retry logic, and data parsing.
 **Dependency**: Phase 6 (US3) complete.

- [ ] T046a [P] **Validation**: Run `docs/QUICKSTART.md` validation to ensure reproducibility. **Requirement**: Execute the guide on a fresh environment and verify all steps succeed.
 **Dependency**: T042c.

- [ ] T047a [P] **Versioning**: Verify all artifacts have content hashes and versioning discipline applied. **Requirement**: Run `code/utils/versioning.py` and ensure `state/` is updated.
 **Dependency**: Phase 6 (US3) complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Research Prerequisites (Phase 2)**: No dependencies - can start immediately. **Must complete before Phase 3 (Foundational)**.
- **Foundational (Phase 3)**: Depends on Phase 2 (Research) - BLOCKS all user stories
- **User Stories (Phase 4+)**: All depend on Foundational and Research Prerequisites completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Spec Amendment (Phase 2)**: Must be completed early to unblock T024/T025 logic.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational + Research Prerequisites - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational + Research Prerequisites - Depends on US1 data output (T017, T019)
- **User Story 3 (P3)**: Can start after Foundational + Research Prerequisites - Depends on US2 results
- **User Story 4 (P4)**: Can start after Foundational + Research Prerequisites - Depends on US1, US2, US3 integration

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All Research tasks in Phase 2 can run in parallel (T048.0a can start immediately, T048.0b/0c/0d/0e depend on 0a)
- Once Foundational + Research Prerequisites phases complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Ensure all data download tasks use verified, reachable URLs (ILRS/UCI) and never synthesize fake data.
- **CRITICAL**: All models must run on CPU-only (limited core count and memory) without GPU dependencies.
- **CRITICAL**: T024 depends on T024a (Separate Fits must be ready first) and T007a (Entities) - do not mark as [P] relative to Phase 2.
- **CRITICAL**: T020 and T021 depend on T023a (Specification Definition) and Plan.md "Critical Methodological Update" - do not mark as [P] relative to Phase 4 implementation.
- **CRITICAL**: T024 must follow the mathematical definitions in Plan.md "Critical Methodological Update".
- **CRITICAL**: T009 must implement the "Data Feasibility Gap" reporting logic defined in the Plan (No hard fail on URL verification).
- **CRITICAL**: T038 must implement a hard exit on memory limit exceeded using `psutil` RSS, polling every 5 seconds, and a 6-hour global timer gate, and must report the specific stage causing the delay.
- **CRITICAL**: T009c must verify that the ILRS URLs are accessible (HEAD request) before marking the task complete.
- **CRITICAL**: T025 must extract `r` from `OrbitSolution.state` to calculate `g = GM/r^2` using the **instantaneous orbital radius** (|state|) at each epoch, averaged over the arc, using `astropy.constants.GM_earth`.
- **CRITICAL**: T048.0d is a mandatory research task to resolve SC-002 verification block and acts as a gate (but no longer a hard crash).
- **CRITICAL**: T024a -> T024 order must be strictly followed.
- **CRITICAL**: T025 depends on T024 and T025a.
- **CRITICAL**: Phase 2 must precede Phase 3 (specifically T004).
- **CRITICAL**: T023 must be split into T023b, T023c, T023d, T023e, T023f for independent testing.
- **CRITICAL**: T032 must be split into T032a, T032d, T032e, T032f for independent testing.
- **CRITICAL**: T009a and T009c must be split to separate artifact creation from URL validation.
- **CRITICAL**: T049 must handle missing benchmark gracefully (warning/report) instead of raising FileNotFoundError.
- **CRITICAL**: T023d (Force Calculator) is a prerequisite for T024a/T024 to implement the "Critical Methodological Update".
- **CRITICAL**: T025a and T025b are now distinct tasks (Extract Separate Parameters vs Consistency Check).
- **CRITICAL**: T024a -> T024b -> T024 order must be strictly followed to separate estimation from anomaly calculation.
- **CRITICAL**: T009d is a new task to explicitly verify the 5 required satellite URLs before ingestion.
- **CRITICAL**: T024 is a comparison method and does not block T025a or T025b. T025b depends on T024a and T025a.
- **CRITICAL**: T013a (Write) depends on spec.md, not T014b implementation. T013b (Run) depends on T013a and T014b.
- **CRITICAL**: T005 and T007 are foundational but are prerequisites for T007a.
- **CRITICAL**: T005 and T007 are marked as prerequisites for T007a.
- **CRITICAL**: T025 and T025a are parallel tasks (marked [P]) but T025b waits for both.

- [ ] T050 [P] [US1] **Implement Streamed Download for Large Arcs**: Create `code/ingestion/streaming_downloader.py`. **Requirement**:
 1. Implement a generator-based download function that processes SLR files in chunks if the file size exceeds a large threshold.
 2. Use `requests` with `stream=True` and iterate over `response.iter_content(chunk_size=8192)` to avoid loading the entire file into memory.
 3. Parse and yield `NormalPoint` objects one by one (or in small batches) to downstream processors.
 4. **Rationale**: Ensures compliance with the "Large real datasets: STREAM the real data" rule, preventing OOM errors on a constrained RAM runner.
 **Dependency**: T009a, T014b.

- [ ] T051 [P] [US2] **Implement Robust Covariance Propagation**: Extend `code/analysis/eotvos.py`. **Requirement**:
 1. Implement a function `propagate_covariance_to_eta(ac: float, cov_ac: np.ndarray, g: float, cov_g: np.ndarray) -> tuple[float, float]`.
 2. Use the Delta Method (first-order Taylor expansion) to calculate the variance of $\eta = |a_c| / g$.
 3. Ensure the calculation accounts for the covariance between $a_c$ and $g$ if they are correlated in the joint fit.
 4. **Rationale**: Addresses the "Statistical Rigor" requirement in the Constitution, ensuring the 95% CI for $\eta$ is mathematically sound and not just an approximation.
 **Dependency**: T024a, T024, T007a.

- [ ] T052 [P] [US3] **Implement Robustness Flagging Logic**: Extend `code/analysis/validation.py`. **Requirement**:
 1. Implement logic to calculate the coefficient of variation (CV) of the Z-scores across the geopotential models.
 2. If CV > 0.2, set `final_flag` to "Unreliable" and log a warning citing the specific models causing the drift.
 3. **Rationale**: Directly implements the Edge Case requirement: "if the Z-score varies by > 20% across models, it must flag the result as 'Unreliable due to geopotential uncertainty'".
 **Dependency**: T033c, T032a.

- [ ] T053 [P] [US4] **Implement Resource-Aware Subset Selection**: Create `code/utils/subset_selector.py`. **Requirement**:
 1. Implement a function to automatically select a representative 1-year subset of data if the full dataset would exceed the 6-hour time limit.
 2. Logic: Select the year with the highest data density (most normal points) to maximize statistical power within the time budget.
 3. **Rationale**: Ensures the pipeline completes within the "Compute Feasibility" constraints (US4) without manually hard-coding a year, adapting to the actual data availability.
 **Dependency**: T009, T038.