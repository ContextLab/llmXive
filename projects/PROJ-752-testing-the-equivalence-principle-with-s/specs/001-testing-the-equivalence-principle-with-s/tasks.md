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

- [X] T001 Create project structure per implementation plan: `mkdir -p code/data code/models code/analysis code/utils code/tests contracts data/raw data/processed data/results docs`
- [X] T002 Initialize a Python project with pinned dependencies in `requirements.txt` (copy list from plan.md Technical Context)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `config.py` to load paths, hyperparams, and `verified_dataset_urls` keys from `config.yaml` (the single source of truth for configuration).
- [X] T005 [P] Create `contracts/normal_point.schema.yaml` defining the SLR observation schema
- [X] T006 [P] Create `contracts/orbit_solution.schema.yaml` defining the fit results schema
- [ ] T007 [P] Create `contracts/eotvos_result.schema.yaml` defining the final metric schema
- [ ] T007a **Implement Python Dataclasses consuming schemas T005-T007**: Create file `src/models/entities.py` containing Python dataclasses for `NormalPoint`, `OrbitSolution`, and `EotvosResult`. **Requirement**:
 1. Define `NormalPoint` with fields: `timestamp` (datetime), `range` (float, meters), `satellite_id` (str), `station_id` (str), `quality_flag` (str).
 2. Define `OrbitSolution` with fields: `orbital_elements` (dict: keys 'semi_major_axis_m', 'eccentricity', 'inclination_rad', 'raan_rad', 'arg_perigee_rad', 'mean_anomaly_rad', all floats), `non_gravitational_acceleration` (float, m/s²), `covariance_matrix` (np.ndarray, shape N x N), `chi2` (float), `residuals` (np.ndarray, shape M), `state` (np.ndarray, shape (3,), position vector in meters). **Note**: The `state` field is critical for T025 to calculate local gravity.
 3. Define `EotvosResult` with fields: `eta_value` (float), `confidence_interval` (tuple of 2 floats), `p_value` (float), `sensitivity_sweep_data` (dict: model_name -> z_score).
 4. Ensure these classes are importable from `src.models.entities` and match the YAML schemas in T005-T007.
 **Dependency**: T005, T006, T007 (Schema definitions must exist first).
- [ ] T008 [P] **Implement Logging Module**: Create file `src/utils/logging.py`. **Requirement**:
 1. Implement standard logging configuration (file and console handlers).
 2. Define custom exception `DataUnavailableError` and `ModelError`.
 3. Ensure this module is imported by T009, T016, and T018.
 **Dependency**: None (foundational).
- [X] T009a **Generate Verified Datasets Artifact**: Create `data/verified_datasets.yaml`. **Requirement**:
 1. Populate the YAML with the canonical ILRS archive URLs for LAGEOS-1 (ID: 2200), LAGEOS-2 (ID: 2201), Etalon-1 (ID: 2045), Etalon-2 (ID: 2046), and Starlette (ID: 0685).
 2. Use the base URL pattern: ` (adjust year/month/day as needed) or the specific ILRS archive endpoint for normal points.
 3. Include metadata: satellite_id, source_url, version, and last_verified_date.
 4. **Gate**: Do NOT perform HEAD-request verification here. Verification is handled in T009.
 5. Ensure the file exists and is valid YAML before T009 runs.
 **Dependency**: None (foundational).
- [X] T010 Setup `pytest` framework: create `tests/conftest.py`, `pytest.ini`, and `requirements-dev.txt`
- [X] T023a [P] **Define Dynamics Specification**: Create `docs/dynamics_spec.md` detailing the exact mathematical formulation for GGM geopotential, Jacchia drag, SRP, and Relativity to be used in T023. **Requirement**:
 1. Document equations and constants.
 2. **Gate**: This document serves as the "Specification" for T020 and T023.
 **Dependency**: None (foundational).

**Checkpoint**: Foundation ready - research prerequisites must now be completed before user story implementation can begin

---

## Phase 2.5: Research Prerequisites (Blocking for US1-US3)

**Purpose**: Complete necessary research and configuration gating to ensure scientific rigor and prevent defaulting to conservative values.

**⚠️ CRITICAL**: No User Story implementation can begin until these research tasks are complete and `config.yaml` is updated.

- [ ] T048.0a [Research] **Search for Benchmark Papers**: Search for peer-reviewed papers defining state-of-the-art benchmarks for Eötvös parameter precision. **Requirement**:
 1. Search criteria: Papers published after 2010 with precision < 1e-13. Use ADS/arXiv database.
 2. Search query: "Eötvös parameter limit satellite laser ranging".
 3. **Deliverable**: Create `research/benchmarks.md` containing a table with columns: Author, Year, Value (95% CI width or upper bound), URL/DOI.
 4. Include at least 3 candidate papers.
 **Dependency**: None (foundational research).
- [ ] T048.0b [Spec] **Select and Cite Benchmark**: Select the most appropriate benchmark paper from T048.0a. **Requirement**:
 1. Choose one specific paper.
 2. Extract the specific numerical value (95% CI width or upper bound).
 3. **Deliverable**: Create `research/benchmark_selection.md` with rationale and update `config.yaml` under `benchmark_values.etvos_limit` with the float value and a citation string (DOI or URL).
 **Dependency**: T048.0a.
- [ ] T048.0c [Spec] **Populate Config with Benchmark & Gate**: Ensure `config.yaml` is updated. **Requirement**:
 1. Verify `config.yaml` contains `benchmark_values: { etvos_limit: <float> }` with a valid source citation (URL or DOI).
 2. **Gate**: If `etvos_limit` is missing or invalid, raise FileNotFoundError in T049. Do NOT proceed with a default value.
 **Dependency**: T048.0b.

**Checkpoint**: Research complete - pipeline can now proceed with validated scientific constraints

---

## Phase 3: User Story 1 - Data Ingestion and Orbit Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Download and clean SLR normal-point series for LAGEOS, Etalon, and Starlette.

**Independent Test**: Execute ingestion pipeline and verify output CSV contains ≥ 95% of available points with no NaN values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Unit test for URL validation and backoff retry logic in `tests/test_ingestion.py`
- [X] T012 [P] [US1] Unit test for quality filtering (>2cm residual exclusion) in `tests/test_preprocessing.py`
- [X] T013 [P] [US1] **Integration Test**: Create `tests/test_data_pipeline.py::test_lageos1_fetch`. **Requirement**: <!-- FAILED: unspecified -->
 1. Fetch LAGEOS data for the **latest available full year** (defined as the last calendar year where data for *all* target satellites is >90% complete, with a fallback to the previous year).
 2. Assert `data/processed/lageos1.csv` exists.
 3. **Gate**: If fetch fails, test must fail loudly (no synthetic fallback).
 4. **Conditional**: If data exists but has < 10,000 rows, log a warning "Insufficient data for year" but do NOT fail the test unless the count is < 500 (minimum for arc).
 **Dependency**: T009 (Ingestion), T014b (Parsing), Phase 2.5 (Config).

### Implementation for User Story 1

- [ ] T014b [US1] **Add `parse_slr_file` function to `src/data/ingestion.py`**. **Requirement**: Implement `parse_slr_file(raw_content: bytes) -> list[NormalPoint]`. Parse raw SLR files into `NormalPoint` objects (using T007a class). **Dependency**: Requires T009 (file initialization) and T007a (Entity class).
- [ ] T014c [US1] **Add `aggregate_satellites` function to `src/data/ingestion.py`**. **Requirement**: Implement `aggregate_satellites(satellite_ids: list[str]) -> pd.DataFrame`. Orchestrate the loop over all relevant satellites, fetch (using T009's fetch logic), parse (using T014b), and aggregate results. **Dependency**: Requires T009 and T014b.
- [ ] T016 [US1] Implement `src/data/preprocessing.py` to filter residuals > 2cm and handle sparse satellites. **Requirement**: Filter data and identify satellites with < 30 days arc length. **Dependency**: T014c.
- [ ] T017 [US1] Implement time-alignment logic in `src/data/preprocessing.py` to merge multi-satellite datasets. **Dependency**: T016.
- [ ] T018 [US1] **Implement Exclusion Logic**: Handle "Insufficient Data" (<30 days arc length) warnings. **Requirement**:
 1. Log a specific "Insufficient Data" warning for satellites with < 30 days of unique dates.
 2. **Explicitly exclude** the satellite from the downstream joint estimation (T024) and differential analysis.
 3. **Record** the list of excluded satellite IDs in a shared state file `data/processed/excluded_satellites.json` (or similar) that T037 can consume.
 4. Ensure T037 can read this file to flag the report as "Incomplete".
 5. **Align with Plan**: This logic implements the "Data Feasibility Gap" handling defined in the Plan, where missing data results in a report rather than a spurious result.
 **Dependency**: T017, T008.
- [ ] T019 [US1] Write output to `data/processed/cleaned_slr_data.csv` with checksum verification; record checksum in `state/projects/PROJ-752-testing-the-equivalence-principle-with-s.yaml` under the `artifact_hashes` map (as per Constitution Principle III). **Requirement**:
 1. Use **SHA-256** algorithm.
 2. Record under key `artifact_hashes.data/processed/cleaned_slr_data.csv`.
 3. Verify `cleaned_slr_data.csv` exists and is non-empty before checksumming.
 **Dependency**: T014c, T016, T017.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Differential Acceleration Parameter Estimation (Priority: P2)

**Goal**: Run **joint** weighted least-squares orbit determination to estimate $a_c$ and $\eta$.

**Independent Test**: Verify **joint** solver convergence (residuals < 1e-5m) and correct calculation of $\eta$ with 95% CI.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementing. Tests depend on Specifications (T023a), NOT Implementation Code.

- [ ] T020 [US2] Unit test for dynamical model components (geopotential, drag, SRP, relativity) in `tests/test_dynamics.py`. **Requirement**: Test the components implemented in T023. **Dependency**: Requires T023a (Specification Definition).
- [ ] T021 [US2] Unit test for **joint** least-squares solver convergence in `tests/test_estimator.py`. **Requirement**: Verify convergence logic. **Dependency**: Requires Plan.md "Critical Methodological Update" (Joint Fit), T007a.
- [ ] T022 [US2] Unit test for $\eta$ calculation and covariance propagation in `tests/test_eotvos.py`. **Requirement**: Verify math. **Dependency**: Requires Plan.md "Critical Methodological Update" (Joint Fit), T007a.

### Implementation for User Story 2

- [ ] T023 [US2] Implement `src/models/dynamics.py` with GGM geopotential, Jacchia drag, SRP, and relativistic corrections. **Requirement**:
 1. Input: state vector, output: acceleration vector (ITRS coordinates, using `astropy.coordinates`).
 2. **Explicitly implement** and document: GGM geopotential, Jacchia drag, Solar Radiation Pressure (SRP), and Relativistic corrections.
 3. **Parameterization**: Accept satellite-specific properties (mass, cross-sectional area, reflectivity) as input parameters to calculate forces.
 4. **Verification**: Add a test or log entry confirming all four components are active and functional.
 **Dependency**: T023a (Specification), T007a.
- [ ] T024 [US2] **Implement JointLeastSquaresSolver**: Create `src/models/estimator.py`. **Requirement**:
 1. Define class `JointLeastSquaresSolver` following the methodology in **Plan.md "Critical Methodological Update"** (Joint Weighted Least-Squares).
 2. Implement `stack_residuals(residuals_sat1: List[np.array], residuals_sat2: List[np.array]) -> np.array`.
 3. Implement `estimate_parameters(stacked_residuals: np.array, model_params: dict) -> OrbitSolution` (using T007a class).
 4. Use **Levenberg-Marquardt** algorithm with **tol=1e-8** convergence tolerance.
 5. **Mathematical Definition**: Implement the joint estimator that minimizes the stacked residual vector $R = [r_1, r_2]^T$ with respect to the combined parameter vector $\theta = [\theta_1, \theta_2, a_c]^T$, where $a_c$ is the differential acceleration term.
 6. **Initial Guess**: Use TLE data for initial orbital elements.
 7. **Weighting**: Use inverse variance weights derived from observation metadata.
 8. **Parameter Ordering**: [theta1, theta2, ac].
 9. **Gate**: Verify `plan.md` "Critical Methodological Update" reflects Joint methodology before proceeding. (Note: Spec FR-003 baseline is superseded by Plan for this implementation).
 10. Ensure the solver directly estimates the differential acceleration $a_c$ as defined in the Plan.
 **Dependency**: T007a, T023, Plan.md "Critical Methodological Update".
- [ ] T024b [US2] **Implement Pre-fit vs Post-fit RMS Comparison**: Create function `calculate_rms_comparison(solution: OrbitSolution) -> dict`. **Requirement**:
 1. Calculate Pre-fit residual RMS (from initial residuals).
 2. Calculate Post-fit residual RMS (from `solution.residuals`).
 3. Return dictionary `{'prefit_rms': float, 'postfit_rms': float, 'improvement': float}`.
 4. **Output**: Log this comparison as required by SC-001.
 **Dependency**: T024.
- [ ] T024a [US2] **Implement Separate Fit Baseline**: Create `src/models/estimator.py` (or separate module) to implement a standard separate least-squares fit for each satellite. **Requirement**:
 1. Implement `separate_fit_satellite(satellite_data: pd.DataFrame, model_params: dict) -> OrbitSolution`.
 2. Run this for both satellites in the pair.
 3. Calculate the difference in non-gravitational accelerations from these separate fits.
 4. **Output**: Store results in `data/results/separate_fits.json` as a standalone artifact required by FR-003 (as baseline).
 5. This is a primary deliverable required by FR-003 (baseline comparison).
 **Dependency**: T024 (Joint Estimator must be ready to compare against), T007a.
- [ ] T025 [US2] Implement function `extract_joint_parameters(solution: OrbitSolution) -> dict` to **extract** the differential acceleration $a_c$ and local gravity $g$ **directly from the joint solution vector** and joint covariance matrix. **Requirement**:
 1. **Input**: Consumes the `OrbitSolution` object returned by T024.
 2. Extract position vector `r` from `solution.state` (OrbitSolution object from T007a).
 3. Calculate `g = GM / |r|^2` using `r` from the joint solution state.
 4. Extract `ac` and `covariance` from the joint solution.
 5. Return dictionary `{'ac': float, 'g': float, 'covariance': np.array}`.
 **Note**: This extracts the *differential* parameter directly as defined in `Plan.md`. **Dependency**: T024, T007a.
- [ ] T025a [US2] **Implement Consistency Check**: Create `src/analysis/eotvos.py` (or extend) to verify the joint estimate against the separate-fit baseline. **Requirement**:
 1. Compare the joint estimate of $a_c$ (from T025) with the separate-fit difference (from T024a).
 2. **Explicitly calculate** the 2-sigma threshold using the joint covariance matrix from T024 and the separate covariance from T024a.
 3. Verify the difference is within this -sigma range.
 4. Log a warning if the consistency check fails.
 5. Include the consistency check result in the final report.
 **Dependency**: T024, T024a, T025, T007a.
- [ ] T026 [US2] Implement `src/analysis/eotvos.py` to compute $\eta = |a_c| / g$ and 95% CI. **Dependency**: Must consume the output dictionary of T025. **Note**: The calculation uses the `ac` and `g` values extracted by T025 and propagates the joint covariance matrix.
- [ ] T027 [US2] Implement fallback logic for non-convergence (relax tolerance, log warning, output best-fit) as authorized by plan robustness requirements
- [ ] T028 [US2] Save `OrbitSolution` and `EotvosResult` to `data/results/orbit_solutions.json` and `data/results/eotvos_metrics.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Robustness Analysis (Priority: P3)

**Goal**: Perform F-test/BIC comparison and geopotential sensitivity analysis.

**Independent Test**: Verify sensitivity plot generation and correct application of multiple-comparison corrections.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for F-test and BIC calculation logic in `tests/test_validation.py`
- [X] T030 [P] [US3] Unit test for Bonferroni/Holm-Bonferroni/Benjamini-Hochberg correction logic in `tests/test_validation.py`
- [X] T031 [P] [US3] Integration test: Verify sensitivity sweep across multiple geopotential models in `tests/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T032a [P] [US3] **Implement Validation Data Structures**: Create `src/analysis/validation.py` and define `ValidationResult` and `SensitivityReport` dataclasses. **Requirement**:
 1. Define `ValidationResult` with fields: `chi2_null`, `chi2_alt`, `F_statistic`, `p_value`, `BIC`.
 2. Define `SensitivityReport` with fields: `results_per_model`, `z_score_variation`, `final_flag`.
 **Dependency**: None (foundational for US3).
- [ ] T032 [P] [US3] Implement `src/analysis/validation.py` function for F-test and BIC model comparison (Null vs Alternative). **Requirement**:
 1. Calculate $\chi^2$ for Null model ($\chi^2_{null}$) and Alternative model ($\chi^2_{alt}$).
 2. Calculate F-statistic and p-value.
 3. **Output**: Return a `ValidationResult` object (from T032a) containing `chi2_null`, `chi2_alt`, `F_statistic`, `p_value`, and `BIC`.
 **Dependency**: T032a.
- [ ] T033a [US3] Implement `src/analysis/validation.py` function `iterate_geopotential_models(models: list[str]) -> Iterator[str]`. **Requirement**: Implement the iteration logic over GGM, EGM2008, and GOCO.
- [ ] T033b [US3] Implement `src/analysis/validation.py` function `run_sensitivity_per_model(model: str, data: pd.DataFrame) -> EotvosResult`. **Requirement**: Run the estimator per model and collect results.
- [ ] T033c [US3] Implement `src/analysis/validation.py` function `aggregate_sensitivity_results(results: list[EotvosResult]) -> SensitivityReport`. **Requirement**: Aggregate and report the sensitivity sweep results (using T032a class).
- [ ] T034 [US3] Implement `src/analysis/validation.py` function `apply_correction(p_values: List[float], method: str = 'bonferroni') -> List[float]`. **Requirement**:
 1. **Default**: Use Bonferroni if method is not specified.
 2. **Implement Logic**: Explicitly implement logic for **Bonferroni**, **Holm-Bonferroni**, and **Benjamini-Hochberg** methods as required by FR-006.
 3. **Error Handling**: Raise `ValueError` if method is not in ['bonferroni', 'holm-bonferroni', 'benjamini-hochberg'].
 4. **Input**: Accept unsorted p-values.
 5. Return corrected p-values.
 **Dependency**: T032.
- [ ] T035 [US3] Implement logic to flag "Unreliable" if Z-score variation > 20% across models
- [ ] T036 [US3] Generate sensitivity plot and save to `data/results/sensitivity_analysis.png`
- [ ] T037 [US3] Implement `src/analysis/report.py` to generate diagnostic report. **Requirement**:
 1. Consume `ValidationResult` from T032.
 2. **Explicitly calculate** $\Delta \chi^2 = \chi^2_{null} - \chi^2_{alt}$ (based on spec.md FR-007 definition).
 3. Include $\Delta \chi^2$, F-statistic, p-value, and $\eta$ limit in the report.
 4. Output residuals CSV.
 5. **Flagging**: Check the `excluded_satellites` list from `data/processed/excluded_satellites.json` (T018). If non-empty, explicitly set `report_status = "Incomplete"` in the report.
 6. **Align with Plan**: This implements the "Data Feasibility Gap" reporting logic defined in the Plan.
 7. **Dependency**: Consume `precision_goal_met` boolean from T049.
 **Dependency**: T032, T018, T049.
- [ ] T049 [US3] **Validate SC-002**: Implement logic in `src/analysis/report.py` to retrieve "current state-of-the-art benchmarks" for the Eötvös parameter precision from `config.paths.benchmark_values.etvos_limit`. **Requirement**:
 1. **Gate**: If `etvos_limit` is missing from config (i.e., Phase 2.5 not completed), **raise FileNotFoundError** with message "Benchmark value missing. Research task T048.0c must be completed first." **Do NOT default to a conservative value.**
 2. Compare the calculated 95% CI width (from T026) against `etvos_limit`.
 3. **Output**: Generate a definitive `precision_goal_met` boolean and a textual status ("Pass" or "Fail") based on the comparison.
 4. Report the result in the final diagnostic report, fulfilling SC-002 validation.
 **Dependency**: Phase 2.5 (T048.0c), T026.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Compute Feasibility & Resource Validation (Priority: P4)

**Goal**: Validate pipeline execution within GitHub Actions free-tier constraints (time limits, CPU, and RAM).

**Independent Test**: Run full pipeline on subset and verify completion time < 6 hours.

### Implementation for User Story 4

- [ ] T038 [P] [US4] Implement `src/cli/main.py` entry point with CLI arguments, runtime monitoring, and memory profiling. **Requirement**:
 1. Use `psutil.Process().memory_info().rss` to monitor RAM.
 2. **Polling Interval**: Check memory at regular intervals.
 3. Log a warning if RAM > 6GB AND **exit with code 1** if the limit is exceeded to prevent runner hangs.
 4. **Error Message**: Must be exactly: `CRITICAL: Memory limit (6GB) exceeded. Current RSS: {rss_mb}MB`.
 5. **Timing Gate**: Implement a global timer for the full pipeline. If total time > 6 hours, log warning and exit with code 124.
 6. **Constraint**: Verify CPU-only execution (no GPU imports).
 7. **Logging**: Log timing and memory data to `data/logs/resource_monitor.log` in CSV format (timestamp, rss_mb, elapsed_s).
 **Dependency**: None.
- [ ] T040 [US4] Create `tests/test_feasibility.py` to run pipeline on 1-year subset and assert time < 6h
- [ ] T041 [US4] Document performance benchmarks and resource usage in `docs/performance.md`

**Checkpoint**: Feasibility validated for CI environment

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `docs/` (README, API reference)
- [ ] T043 Code cleanup and refactoring of `src/models/dynamics.py` for readability
- [ ] T044 Performance optimization: Vectorize `src/data/preprocessing.py` operations using NumPy
- [ ] T045 [P] Add unit tests for edge cases (missing data, empty results) in `tests/unit/`
- [ ] T046 Run `quickstart.md` validation to ensure reproducibility
- [ ] T047 Verify all artifacts have content hashes and versioning discipline applied

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Research Prerequisites (Phase 2.5)**: Depends on Phase 2 completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational and Research Prerequisites completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Spec Amendment (Phase 2)**: Must be completed early to unblock T024/T025 logic. (Resolved by direct spec update).

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
- All Research tasks in Phase 2.5 can run in parallel (T048.0a can start immediately, T048.0b/0c depend on 0a)
- Once Foundational + Research Prerequisites phases complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for URL validation and backoff retry logic in tests/test_ingestion.py"
Task: "Unit test for quality filtering (>2cm residual exclusion) in tests/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement data/ingestion.py to fetch and aggregate SLR data for all target satellites"
Task: "Implement data/preprocessing.py to filter residuals > 2cm"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.5: Research Prerequisites (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational + Research → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Research together
2. Once Foundational + Research is done:
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Estimation)
 - Developer C: User Story 3 (Validation)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Ensure all data download tasks use verified, reachable URLs (ILRS/UCI) and never synthesize fake data.
- **CRITICAL**: All models must run on CPU-only (limited core count and memory) without GPU dependencies.
- **CRITICAL**: T024 depends on Plan.md "Critical Methodological Update" (Joint methodology) and T007a (Entities) - do not mark as [P] relative to Phase 2.
- **CRITICAL**: T021/T022 depend on Plan.md "Critical Methodological Update" (Joint methodology) and T007a (Entities) - do not mark as [P] relative to Phase 4 implementation.
- **CRITICAL**: T024 must implement **joint** estimation, not separate fits, to align with the plan's methodology and the updated spec.md (FR-003, FR-004).
- **CRITICAL**: T019 MUST write to `state/projects/...yaml` not local JSON files, using SHA-256.
- **CRITICAL**: T038 MUST implement a hard exit on memory limit exceeded using `psutil` RSS, polling every 10 seconds, and a 6-hour global timer gate.
- **CRITICAL**: T009 MUST NOT hardcode URLs; it must enforce the blocking gate by reading `data/verified_datasets.yaml` and performing HEAD-request verification (with graceful fallback to GET if HEAD fails).
- **CRITICAL**: T009a MUST generate `data/verified_datasets.yaml` before T009 runs.
- **CRITICAL**: T007a MUST implement the Python dataclasses before T014b, T024, T025 run.
- **CRITICAL**: T032a MUST define `ValidationResult` and `SensitivityReport` before T032 runs.
- **CRITICAL**: T048.0c must populate `config.yaml` under `benchmark_values.etvos_limit` with a cited source and act as a gate. T049 reads from `config.paths.benchmark_values.etvos_limit`.
- **CRITICAL**: T025 must extract `r` from `OrbitSolution.state` to calculate `g = GM/r^2`.
- **CRITICAL**: T049 depends on Phase 2.5 (T048.0c). If T048.0c is not complete, T049 will fail (FileNotFoundError).
- **CRITICAL**: T048.0c is a mandatory research task to resolve SC-002 verification block and acts as a gate.
- **CRITICAL**: T024 must follow the mathematical definitions in Plan.md "Critical Methodological Update".
- **CRITICAL**: T009a and Phase 2.5 are foundational tasks that must complete before their respective downstream tasks.
- **CRITICAL**: T024a and T025a must implement the Separate Fit Baseline and Consistency Check (2-sigma) as required by the spec.md FR-003 (as baseline).
- **CRITICAL**: T018 must explicitly exclude satellites from the joint estimation matrix and record the list in a shared state.
- **CRITICAL**: T037 must flag the report as "Incomplete" if satellites were excluded.
- **CRITICAL**: T049 must output a definitive "Pass" or "Fail" status for SC-002 and fail loudly if the benchmark is missing.
- **CRITICAL**: T020 (Test Dynamics) depends on T023a (Specification Definition), NOT T023 (Implementation). T023 depends on T023a.
- **CRITICAL**: T013 Integration Test requires a real ILRS data fetch; if the fetch fails, the test must fail loudly (no synthetic fallback) to trigger the "Missing Data" handling path in T018.
- **CRITICAL**: T025a Consistency Check must explicitly calculate the 2-sigma threshold using the joint covariance matrix from T024 and the separate-fit covariance from T024a.
- **CRITICAL**: T034 Default Correction Method must be configurable via `config.yaml` but default to Bonferroni if unspecified, as per FR-006, and must implement all three methods.
- **CRITICAL**: T009a must verify that the ILRS URLs are accessible (HEAD request) before marking the task complete; if a URL is dead, the task must fail and the plan must be updated to find an alternative verified source.
- **CRITICAL**: T019 Checksum must be computed on the *final* `cleaned_slr_data.csv` after all filtering (T016) and alignment (T017) are complete.
- **CRITICAL**: T023 must explicitly implement and verify relativistic corrections and SRP as per FR-002.
- **CRITICAL**: T024b must calculate and report Pre-fit vs Post-fit RMS as per SC-001.
- **CRITICAL**: T005, T006, T007, T007a are distinct tasks; T007 is for the Eotvos schema, T005/006 for NormalPoint/OrbitSolution schemas. No ID duplication exists.
- **CRITICAL**: T009a is NOT marked [P] to ensure strict ordering before T009.
- **CRITICAL**: T023a is a new task providing the specification for T020 and T023.
- **CRITICAL**: T048.4 is required to enforce the "Real Data + Real Results" rule regarding composition metadata.
- **CRITICAL**: T007a is NOT marked [P] as it depends on T007.
- **CRITICAL**: T020 and T021 are NOT marked [P] as they depend on T023a and Plan.md "Critical Methodological Update".
- **CRITICAL**: T024 must follow the mathematical definitions in Plan.md "Critical Methodological Update".
- **CRITICAL**: T037 must depend on T049 to include the benchmark validation status in the report.
- **CRITICAL**: T025a must depend on T025 to compare the joint estimate with the separate fit.