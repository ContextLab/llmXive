# Tasks: Characterization of Exoplanetary Atmospheres through Advanced Spectroscopic Techniques

**Input**: Design documents from `/specs/001-characterization-of-exoplanetary-atmosph/`
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

- [X] T001a [P] Create project directory structure: `projects/PROJ-554-characterization-of-exoplanetary-atmosph/`, `code/`, `data/`, `tests/`, `results/`
- [X] T001b [P] Initialize `requirements.txt` with pinned versions: `petitRADTRANS`, `astropy`, `statsmodels`, `scipy`, `pandas`, `numpy`, `requests`, `tqdm`, `lifelines`, `synphot`, `scikit-survival`
- [X] T001c [P] Configure linting (ruff) and formatting (black) tools by creating `.ruff.toml` and `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `code/config.py` for configuration loading (paths, seeds, CPU thread limits)
- [X] T005a [P] Implement logging setup in `code/utils.py` (logging configuration, log levels)
- [X] T005b [P] Implement error handling wrapper in `code/utils.py` (custom exceptions, retry logic)
- [X] T005c [P] Implement censored data helpers in `code/utils.py` (upper limit handling functions)
- [X] T006a [P] Create data directories: `data/raw/`, `data/processed/`; verify existence
- [X] T006b [P] Create code and test directories: `code/`, `tests/unit/`, `tests/contract/`, `tests/integration/`; verify existence
- [X] T007 [P] Create base data models in `code/data_models.py` (Exoplanet Spectrum, Retrieval Result)
- [X] T008 [P] Configure environment variable handling for API keys (if needed) and random seeds. **Deliverable**: `code/config.py` updated to load API keys from env vars.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Download publicly available transmission spectra from NASA Exoplanet Archive for hot Jupiters and super-Earths, extracting metadata (temperature, metallicity, SNR, Resolution, Planet Category) and ensuring sample size targets are met strictly.

**Independent Test**: The system can be tested by verifying that the output directory contains a metadata CSV with non-null values for temperature, metallicity, SNR, Resolution, and planet category, and that the total count of unique planets falls within a moderate range.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [US1] Contract test for metadata schema in `tests/contract/test_metadata_schema.py` implementing `validate_metadata_schema` function. **Depends on T011b**.
- [X] T010 [US1] Integration test for API download in `tests/integration/test_download.py` implementing `test_download_returns_valid_metadata` with specific mock parameters. **Depends on T011b**.

### Implementation for User Story 1

- [X] T011a [P] [US1] Create `code/api_config.py` defining `QUERY_PARAMS` dictionary for NASA Exoplanet Archive API (Hot Jupiters and Super-Earths filters)
- [X] T011b [P] [US1] Implement `code/download.py` fetch logic to retrieve spectrum files and raw metadata using `QUERY_PARAMS`. **Depends on T008**.
- [X] T011c [P] [US1] Implement parsing logic in `code/download.py` to extract equilibrium temperature (K), host star metallicity ([Fe/H]), spectral resolution (R), and signal-to-noise ratio (SNR). **Logic for Planet Category**: Classify as "Hot Jupiter" if Radius > 0.8 R_Jup AND T_eq > 1000K; classify as "Temperate Super-Earth" if Radius < 1.6 R_E AND T_eq < 1000K. Extract instrument name and wavelength range from metadata headers. **Deliverable**: Populated in-memory dataframe with columns [planet_name, temperature, metallicity, snr, resolution, planet_category, instrument, wavelength_range].
- [X] T012 [US1] Save raw spectrum files to `data/raw/` and metadata CSV (including SNR, R, instrument, wavelength, and **planet_category**) to `data/processed/metadata.csv`. **Deliverable**: `data/processed/metadata.csv` with columns [planet_name, temperature, metallicity, snr, resolution, planet_category, instrument, wavelength_range].
- [ ] T013 [US1] Implement `validate_sample_size` in `code/download.py`. **Logic**: 1. Fetch ALL available pages from API. 2. Count unique planets. 3. Log a WARNING if count < 30 or > 45, but **DO NOT raise an error**. Proceed with ALL available data as per FR-001. **Deliverable**: `data/processed/sample_size_report.json` containing {count, validation_status: "proceed"}.
- [ ] T014 [US1] Add logging for download progress and API response handling. **Deliverable**: Log file `logs/download.log` with progress updates.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Atmospheric Retrieval and Water Abundance Derivation (Priority: P2)

**Goal**: Run `petitRADTRANS` in CPU-optimized mode on each spectrum to derive water vapor mixing ratios with uncertainty estimates, handling low S/N data as censored upper limits using SNR/Resolution metadata.

**Independent Test**: The system can be tested by running the retrieval on a single, known test spectrum and verifying that the output includes a water vapor mixing ratio value (or an upper limit flag) and a 1-sigma uncertainty interval.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for retrieval output schema in `tests/contract/test_retrieval_schema.py`
- [X] T017 [P] [US2] Integration test for retrieval on sample spectrum in `tests/integration/test_retrieval.py`

### Implementation for User Story 2

- [X] T018a [P] [US2] Configure `petitRADTRANS` for CPU-optimized mode (single-threaded, memory limit GB) in `code/retrieval.py`
- [X] T018b [P] [US2] Implement wrapper function in `code/retrieval.py` to run retrieval on a single spectrum file
- [ ] T018c [P] [US2] Define output schema mapping: log10 water mixing ratio, standard deviation, or upper limit flag. **Deliverable**: Create `contracts/retrieval.schema.yaml` with the defined fields.
- [X] T019 [US2] Implement logic to detect low S/N spectra using SNR/Resolution metadata and derive upper limits (censored values) instead of false precision. **Logic**: Calculate detection limit based on instrumental noise floor; if signal < 3-sigma above noise, flag as upper limit and record the limit value in mixing ratio units. Also calculate the minimum detectable concentration (MDC) based on SNR and resolution. **Deliverable**: `code/retrieval.py` updated with `derive_upper_limit` and `calculate_mdc` functions. **Depends on T012; Must precede T020**.
- [ ] T020 [US2] Implement output generation: save results to `data/processed/retrieval_results.csv`. **Deliverable**: `data/processed/retrieval_results.csv` with columns [planet_name, water_mixing_ratio, uncertainty, is_upper_limit, detection_limit, min_detectable_concentration].
- [ ] T021 [US2] Add error handling for non-convergent retrievals: log failure, attempt upper limit derivation, proceed without halting.
- [X] T022 [US2] Implement `test_upper_limit_flags_reflect_noise` in `code/validation.py` to verify upper limit flags reflect physical noise floors. **Depends on T019**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Regression Analysis (Priority: P3)

**Goal**: Compute Kendall's tau correlation for censored data (including upper limits), perform bootstrap resampling, and fit Tobit regression controlling for mass and metallicity.

**Independent Test**: The system can be tested by running the analysis on a mock dataset with known censored values and verifying that the calculated Kendall's tau matches the expected value within the bootstrap confidence interval.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py`
- [X] T024 [P] [US3] Integration test for correlation and regression on mock data in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [X] T025a [P] [US3] Import `scikit-survival` in `code/analysis.py` and verify import availability
- [X] T025b [US3] Implement `compute_censored_kendall_tau` in `code/analysis.py` using `scikit-survival`'s `kendall_tau` function for censored data (Hot Jupiters vs Super-Earths). **Logic**: Implements FR-003 requirement for censored correlation using the `scikit-survival` library. **Depends on T012, T020**.
- [ ] T025c [US3] Implement a bootstrap resampling loop to estimate confidence intervals. **Deliverable**: Write results to `data/processed/bootstrap_ci.json` containing {iterations: 1000, ci_lower, ci_upper}.
- [ ] T026 [US3] Compute and report the CI width of the water mixing ratio distribution as a measure of robustness per SC-003. **Deliverable**: `results/robustness_report.json` containing {ci_width, threshold_met (boolean)}. **Note**: Report the value; do NOT raise RuntimeError. The result is a measured outcome, not a pipeline gate.
- [ ] T027 [US3] Implement Tobit regression model (using `lifelines` or `statsmodels`) with water abundance as dependent variable and temperature, mass, metallicity as predictors. **Deliverable**: `data/processed/regression_results.json` with coefficients and p-values. **Depends on T020**.
- [ ] T028 [US3] **Constraint Preservation**: Implement Tobit regression with Ridge Regression Fallback for collinearity. **Logic**: If VIF > 5 for any predictor, automatically switch to Ridge-penalized Tobit regression to handle collinearity as per Plan.md Complexity Tracking. **Depends on T020**.
- [ ] T029 [US3] Implement diagnostic plot generation (water abundance vs. temperature with error bars/limits, residuals, correlation matrix, and **Instrumental Noise vs. Signal** plot) to `results/plots/`. **Deliverable**: `results/plots/water_vs_temp.png`, `results/plots/residuals.png`, `results/plots/correlation_matrix.png`, `results/plots/noise_vs_signal.png`.
- [ ] T030 [US3] Output final statistics: Kendall's tau, p-values, CI width, model fit statistics, and min detectable concentration to `data/processed/analysis_results.json`.
- [ ] T031 [US3] Implement `calculate_statistical_power` in `code/analysis.py` using a **conservative estimate (|tau| >= 0.3)** to verify power ≥ 0.8 per SC-004. **Deliverable**: `results/power_analysis.json` with {power_estimate, power_sufficient (boolean)} and `results/quality_report.md` with resolved vs. upper limits count and power verification.
- [ ] T033 [US3] **Constraint Preservation**: Implement `quality_control_filter` in `code/analysis.py` to flag low SNR spectra and include them as censored values per FR-002, ensuring the filter uses the SNR and Resolution metadata extracted in T012. **Logic**: Apply filter before finalizing analysis; uses T020 results and T012 metadata. **Depends on T012, T020**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [US3] **Results Summary**: Generate `results/results_summary.md` aggregating SC-001 to SC-004 outcomes. **Content**: (1) Final sample size N, (2) Median spectral resolution achieved, (3) 95% CI width for the correlation, (4) Minimum detectable water vapor concentration (derived from T019's detection limits). **Deliverable**: `results/results_summary.md` with required sections.
- [ ] T039 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T040a [P] Refactor `code/utils.py` to remove duplicate exception handling.
- [ ] T040b [P] Update docstrings in `code/analysis.py` for all public functions.
- [ ] T041a [P] Refactor `code/retrieval.py` to use batch processing for memory efficiency.
- [ ] T041b [P] Add caching to `code/download.py` to avoid redundant API calls.
- [ ] T042 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T043 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 6)**: Depends on completion of US1-US3 to generate initial results for review response

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1 (T012)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires data from US1 (T012) and US2 (T020)
- **Revision (Phase 6)**: Requires results from US1, US2, and US3 to address reviewer concerns

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
- All tests for a user story marked [P] can run in parallel **EXCEPT** T009 and T010, which depend on T011b and are NOT parallel-safe with implementation.
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **CPU Constraint**: All tasks must run on a limited number of CPU cores, constrained memory, and no GPU.. `petitRADTRANS` must be configured for single-threaded execution.
- **Data Integrity**: All data must be fetched programmatically; no static data commits.
- **Censored Data**: All statistical methods must handle upper limits correctly (Kendall's tau via scikit-survival, Tobit).
- **Constraint Preservation**: Do NOT remove Ridge Regression Fallback for Tobit; do NOT proceed with biased sample sizes; do NOT use post-hoc power analysis.
- **Review Compliance**: All tasks in Phase 6 directly address the specific quantitative and evidentiary standards raised by Marie Curie and Rosalind Franklin simulated reviewers regarding spectral resolution, SNR, and detection limits.
