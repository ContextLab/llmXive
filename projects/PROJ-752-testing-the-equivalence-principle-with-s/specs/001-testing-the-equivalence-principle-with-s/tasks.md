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

- [X] T004 Implement `config.py` to load paths, hyperparams, and `verified_dataset_urls` keys
- [X] T005 [P] Create `contracts/normal_point.schema.yaml` defining the SLR observation schema
- [X] T006 [P] Create `contracts/orbit_solution.schema.yaml` defining the fit results schema
- [ ] T007 [P] Create `contracts/eotvos_result.schema.yaml` defining the final metric schema
- [ ] T008 Implement `utils/logging.py` for standardized error handling and progress logging
- [ ] T009 [US1] **Initialize and implement gate/fetch logic in `data/ingestion.py`**. **Requirement**: 
    1. Initialize `data/ingestion.py` file.
    2. Implement `validate_config()` to read `config.paths.verified_datasets` and ensure `data/verified_datasets.yaml` exists. Raise `DataUnavailableError` if missing.
    3. Implement `fetch_satellite_data(satellite_id: str)` with exponential backoff retry (attempts).
    4. **Do NOT** implement parsing or aggregation logic here.
- [X] T010 Setup `pytest` framework: create `tests/conftest.py`, `pytest.ini`, and `requirements-dev.txt`
- [ ] T024a [P] [US2] **Interface Definition**: Define the interface for `JointLeastSquaresSolver` in `models/estimator.py`. This interface must accept residuals from both satellites and return a joint solution object with a shared composition-dependent parameter ($a_c$). **Note**: This task defines the signature only; implementation follows in T024b.
- [ ] T048.1 [Spec] **Generate Spec Amendment Artifact**: Create `specs/001-testing-the-equivalence-principle-with-s/spec_amendment_FR-003.md`. **Content Template**: 
    1. Header: "Spec Amendment FR-003: Joint vs Separate Fits"
    2. Section "FR-003 Supersession": Explicitly state FR-003 is superseded by "Joint Weighted Least-Squares Estimation".
    3. Section "Rationale": Explain collinearity and numerical instability of separate fits.
    4. Section "Consistency Check": Define the 2-sigma validation requirement.
    **Requirement**: This artifact must exist before T024b3 can proceed.
- [ ] T048.0 [P] [Research] **Populate Benchmark Config**: Create or update `config.yaml` to include `benchmark_values: { etvos_limit: <float> }`. **Requirement**: 
    1. Research current state-of-the-art benchmarks for Eötvös parameter precision (e.g., Müller et al.).
    2. Populate `etvos_limit` in `config.yaml` under `benchmark_values`.
    3. **Verify** `etvos_limit` exists in `config.yaml` and is a positive float before marking complete.
    **Note**: This task must complete before T049 runs.
- [ ] T048.0b [Research] **Research and Populate Eötvös Benchmark Value**. **Requirement**: 
    1. Conduct research to identify the current state-of-the-art benchmark for the Eötvös parameter ($\eta$) precision from peer-reviewed literature (e.g., Müller et al., 2010; Schlamminger et al., 2008).
    2. Create or update `config.yaml` to include the specific numerical value under `benchmark_values.etvos_limit`.
    3. Add a comment in `config.yaml` citing the specific source (author, year, value) for this limit.
    4. **Verify** that `config.yaml` contains a valid float for `etvos_limit` and that the source citation is present.
    **Dependency**: Must complete before T049 runs.
    **Note**: This task explicitly resolves the missing data requirement for SC-002 verification.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Orbit Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Download and clean SLR normal-point series for LAGEOS, Etalon, and Starlette.

**Independent Test**: Execute ingestion pipeline and verify output CSV contains ≥ 95% of available points with no NaN values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Unit test for URL validation and backoff retry logic in `tests/test_ingestion.py`
- [X] T012 [P] [US1] Unit test for quality filtering (>2cm residual exclusion) in `tests/test_preprocessing.py`
- [X] T013 [P] [US1] Integration test: Verify end-to-end download and CSV generation for LAGEOS-1 in `tests/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T014b [US1] **Add `parse_slr_file` function to `data/ingestion.py`**. **Requirement**: Implement `parse_slr_file(raw_content: bytes) -> list[NormalPoint]`. Parse raw SLR files into `NormalPoint` objects. **Dependency**: Requires T009 (file initialization).
- [ ] T014c [US1] **Add `aggregate_satellites` function to `data/ingestion.py`**. **Requirement**: Implement `aggregate_satellites(satellite_ids: list[str]) -> pd.DataFrame`. Orchestrate the loop over all relevant satellites, fetch (using T009's fetch logic), parse (using T014b), and aggregate results. **Dependency**: Requires T009 and T014b.
- [ ] T016 [US1] Implement `data/preprocessing.py` to filter residuals > 2cm and handle sparse satellites
- [ ] T017 [US1] Implement time-alignment logic in `data/preprocessing.py` to merge multi-satellite datasets
- [ ] T018 [US1] Add error handling for 403 errors and "Insufficient Data" (<500 points) warnings
- [ ] T019 [US1] Write output to `data/processed/cleaned_slr_data.csv` with checksum verification; record checksum in `state/projects/PROJ-752-testing-the-equivalence-principle-with-s.yaml` under the `artifact_hashes` map (as per Constitution Principle III). Ensure raw data is preserved unchanged. **Requirement**: Verify `cleaned_slr_data.csv` exists and is non-empty before checksumming.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Differential Acceleration Parameter Estimation (Priority: P2)

**Goal**: Run **joint** weighted least-squares orbit determination to estimate $a_c$ and $\eta$.

**Independent Test**: Verify **joint** solver convergence (residuals < 1e-5m) and correct calculation of $\eta$ with 95% CI.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for dynamical model components (geopotential, drag, SRP) in `tests/test_dynamics.py`. **Dependency**: Requires T023 (Implementation).
- [ ] T021 [US2] Unit test for **joint** least-squares solver convergence in `tests/test_estimator.py`. **Dependency**: Requires T024a (Interface) and T024b3 (Implementation).
- [ ] T022 [US2] Unit test for $\eta$ calculation and covariance propagation in `tests/test_eotvos.py`. **Dependency**: Requires T024a (Interface) and T024b3 (Implementation).

### Implementation for User Story 2

- [ ] T023 [US2] Implement `models/dynamics.py` with GGM geopotential, Jacchia drag, and SRP models; input: state vector, output: acceleration vector (ITRS coordinates, using `astropy.coordinates`)
- [ ] T024b1 [US2] Implement `models/estimator.py` function `stack_residuals(residuals_sat1: np.array, residuals_sat2: np.array) -> np.array`. **Requirement**: Stack residuals of both satellites into a single vector.
- [ ] T024b2 [US2] Implement `models/estimator.py` function `estimate_parameters(stacked_residuals: np.array, model_params: dict) -> OrbitSolution`. **Requirement**: Implement the parameter estimation loop for the joint solver.
- [ ] T024b3 [US2] Implement `models/estimator.py` class `JointLeastSquaresSolver`. **Requirement**: Integrate T024b1 and T024b2 into the solver class. **Dependency**: Requires T048.1 (Spec Amendment Artifact) to be present.
- [ ] T025 [US2] Implement function `extract_joint_parameters(solution: OrbitSolution) -> dict` to **extract** the differential acceleration $a_c$ and local gravity $g$ **directly from the joint solution vector** and joint covariance matrix. **Requirement**: 
    1. Extract position vector `r` from `solution.state` (OrbitSolution object).
    2. Calculate `g = GM / |r|^2` using `r` from the joint solution state.
    3. Extract `ac` and `covariance` from the joint solution.
    4. Return dictionary `{'ac': float, 'g': float, 'covariance': np.array}`.
    **Note**: This extracts the *differential* parameter directly as defined in `spec_amendment_FR-003.md`.
- [ ] T026 [US2] Implement `analysis/eotvos.py` to compute $\eta = |a_c| / g$ and 95% CI. **Dependency**: Must consume the output dictionary of T025. **Note**: The calculation uses the `ac` and `g` values extracted by T025 and propagates the joint covariance matrix.
- [ ] T027 [US2] Implement fallback logic for non-convergence (relax tolerance, log warning, output best-fit) as authorized by plan robustness requirements
- [ ] T028 [US2] Save `OrbitSolution` and `EotvosResult` to `data/results/orbit_solutions.json` and `data/results/eotvos_metrics.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Robustness Analysis (Priority: P3)

**Goal**: Perform F-test/BIC comparison and geopotential sensitivity analysis.

**Independent Test**: Verify sensitivity plot generation and correct application of multiple-comparison corrections.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for F-test and BIC calculation logic in `tests/test_validation.py`
- [X] T030 [P] [US3] Unit test for Bonferroni/Holm-Bonferroni correction logic in `tests/test_validation.py`
- [X] T031 [P] [US3] Integration test: Verify sensitivity sweep across multiple geopotential models in `tests/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement `analysis/validation.py` for F-test and BIC model comparison (Null vs Alternative). **Requirement**: 
    1. Calculate $\chi^2$ for Null model ($\chi^2_{null}$) and Alternative model ($\chi^2_{alt}$).
    2. Calculate F-statistic and p-value.
    3. **Output**: Return a `ValidationResult` object containing `chi2_null`, `chi2_alt`, `F_statistic`, `p_value`, and `BIC`.
- [ ] T033a [US3] Implement `analysis/validation.py` function `iterate_geopotential_models(models: list[str]) -> Iterator[str]`. **Requirement**: Implement the iteration logic over GGM05C, EGM2008, and GOCO06s.
- [ ] T033b [US3] Implement `analysis/validation.py` function `run_sensitivity_per_model(model: str, data: pd.DataFrame) -> EotvosResult`. **Requirement**: Run the estimator per model and collect results.
- [ ] T033c [US3] Implement `analysis/validation.py` function `aggregate_sensitivity_results(results: list[EotvosResult]) -> SensitivityReport`. **Requirement**: Aggregate and report the sensitivity sweep results.
- [ ] T034 [US3] Implement `analysis/validation.py` function `apply_correction(p_values: list[float], method: str) -> list[float]` to support Bonferroni, Holm-Bonferroni, and Benjamini-Hochberg methods, returning corrected p-values.
- [ ] T035 [US3] Implement logic to flag "Unreliable" if Z-score variation > 20% across models
- [ ] T036 [US3] Generate sensitivity plot and save to `data/results/sensitivity_analysis.png`
- [ ] T037 [US3] Implement `analysis/report.py` to generate diagnostic report. **Requirement**: 
    1. Consume `ValidationResult` from T032.
    2. **Explicitly calculate** $\Delta \chi^2 = \chi^2_{null} - \chi^2_{alt}$.
    3. Include $\Delta \chi^2$, F-statistic, p-value, and $\eta$ limit in the report.
    4. Output residuals CSV.
- [ ] T049 [US3] **Validate SC-002**: Implement logic in `analysis/report.py` to retrieve "current state-of-the-art benchmarks" for the Eötvös parameter precision from `config.paths.benchmark_values.etvos_limit`. **Requirement**: 
    1. Compare the calculated 95% CI width (from T026) against `etvos_limit`.
    2. Report the result in the final diagnostic report, fulfilling SC-002 validation.
    3. If `etvos_limit` is missing from config, fail loudly with `ERROR: Benchmark 'etvos_limit' not found in config. Research phase (Task T048.0b) must populate this value before running validation.`.
    **Dependency**: Must depend on T048.0b completion.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Compute Feasibility & Resource Validation (Priority: P4)

**Goal**: Validate pipeline execution within GitHub Actions free-tier constraints (time limits, CPU, and RAM).

**Independent Test**: Run full pipeline on subset and verify completion time < 6 hours.

### Implementation for User Story 4

- [ ] T038 [P] [US4] Implement `main.py` entry point with CLI arguments, runtime monitoring, and memory profiling. **Requirement**: Use `psutil.Process().memory_info().rss` to monitor RAM. Log a warning if RAM > 6GB AND **exit with code 1** if the limit is exceeded to prevent runner hangs. Error message must be: `CRITICAL: Memory limit (6GB) exceeded. Current RSS: {rss_mb}MB`. **Constraint**: Verify CPU-only execution (no GPU imports).
- [ ] T040 [US4] Create `tests/test_feasibility.py` to run pipeline on 1-year subset and assert time < 6h
- [ ] T041 [US4] Document performance benchmarks and resource usage in `docs/performance.md`

**Checkpoint**: Feasibility validated for CI environment

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `docs/` (README, API reference)
- [ ] T043 Code cleanup and refactoring of `models/dynamics.py` for readability
- [ ] T044 Performance optimization: Vectorize `data/preprocessing.py` operations using NumPy
- [ ] T045 [P] Add unit tests for edge cases (missing data, empty results) in `tests/unit/`
- [ ] T046 Run `quickstart.md` validation to ensure reproducibility
- [ ] T047 Verify all artifacts have content hashes and versioning discipline applied

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Spec Amendment (Phase 2)**: Must be completed early to unblock T024/T025 logic.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T017, T019)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 results
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US1, US2, US3 integration

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
- **CRITICAL**: T024b depends on T048.1 (Spec Amendment) - do not mark as [P] relative to Phase 2.
- **CRITICAL**: T021/T022 depend on T024a (Interface) AND T024b3 (Implementation) - do not mark as [P] relative to Phase 4 implementation.
- **CRITICAL**: T024a and T024b must implement **joint** estimation, not separate fits, to align with the plan's methodology and the updated spec.md (FR-003, FR-004) via the amendment artifact.
- **CRITICAL**: Spec.md has been updated to reflect the 'joint' methodology via T048.1 (generated artifact); no tasks exist to modify the spec text directly.
- **CRITICAL**: T019 MUST write to `state/projects/...yaml` not local JSON files.
- **CRITICAL**: T038 MUST implement a hard exit on memory limit exceeded using `psutil` RSS.
- **CRITICAL**: T009 MUST NOT hardcode URLs; it must enforce the blocking gate by reading `data/verified_datasets.yaml`.
- **CRITICAL**: T009 initializes `data/ingestion.py`; T014b and T014c add specific functions to it. Do not overwrite T009's gate logic.
- **CRITICAL**: T032 must output `chi2_null`, `chi2_alt`, and `F_statistic` for T037 to calculate $\Delta \chi^2$.
- **CRITICAL**: T048.0b must populate `config.yaml` under `benchmark_values.etvos_limit` with a cited source. T049 reads from `config.paths.benchmark_values.etvos_limit`.
- **CRITICAL**: T025 must extract `r` from `OrbitSolution.state` to calculate `g = GM/r^2`.
- **CRITICAL**: T049 depends on T048.0b. If T048.0b is not complete, T049 will fail.
- **CRITICAL**: T048.0b is a mandatory research task to resolve SC-002 verification block.