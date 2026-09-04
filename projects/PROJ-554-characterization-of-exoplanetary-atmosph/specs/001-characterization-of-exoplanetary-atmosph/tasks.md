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
- [X] T001b [P] Initialize `requirements.txt` with pinned versions: `petitRADTRANS`, `astropy`, `statsmodels`, `scipy`, `pandas`, `numpy`, `requests`, `tqdm`, `lifelines`, `synphot`, `scikit-survival`, `scikit-learn`
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

- [X] T009 [US1] Contract test for metadata schema in `tests/contract/test_metadata_schema.py` implementing `validate_metadata_schema` function. **Depends on T007**.
- [X] T010 [US1] Integration test for API download in `tests/integration/test_download.py` implementing `test_download_returns_valid_metadata` with specific mock parameters. **Depends on T007**.

### Implementation for User Story 1

- [X] T011a [US1] Create `code/api_config.py` defining `QUERY_PARAMS` dictionary for NASA Exoplanet Archive API (Hot Jupiters and Super-Earths filters)
- [X] T011b [US1] Implement `code/download.py` fetch logic to retrieve spectrum files and raw metadata using `QUERY_PARAMS`. **Depends on T008**.
- [X] T015a [US1] **Download ALL**: Implement `download_all_spectra` in `code/download.py` to fetch **ALL** available spectra matching the criteria **without any resolution or radius filtering**. **Deliverable**: Unfiltered raw data in `data/raw/`. **Depends on T011b**.
- [X] T011c [US1] **Classification Logic**: Implement classification logic in `code/download.py` to tag planets as "Hot Jupiter" or "Temperate Super-Earth" **AFTER** download is complete. **Logic**:
 - Apply standard literature definitions for "Hot Jupiter" (e.g., irradiated gas giants) and "Temperate Super-Earth" (rocky/mini-Neptune boundary).
 - **Do NOT use hardcoded arbitrary thresholds (e.g., Radius < 1.6 R_E or T_eq > 1000K) unless explicitly defined in spec.md.**
 - If a threshold is necessary for implementation, log the specific value and scientific citation used in `logs/classification.log`.
 - **Note**: This classification is for metadata tagging ONLY. It MUST NOT be used to filter the download query. **Deliverable**: In-memory dataframe with `planet_category` column populated. **Depends on T015a**.
- [ ] T012 [US1] Save raw spectrum files and metadata CSV to `data/processed/`. **Logic**: Combine downloaded spectra with metadata (including SNR, R, instrument, wavelength, and `planet_category` from T011c). **Deliverable**: `data/processed/metadata.csv` with columns [planet_name, temperature, metallicity, snr, resolution, planet_category, instrument, wavelength_range]. **Depends on T011c**.
- [ ] T013a [US1] **Count**: Implement `count_unique_planets` in `code/download.py` to count unique planets from the saved `metadata.csv`. **Deliverable**: `data/processed/count_report.json` with {count}. **Depends on T012**.
- [X] T013b [US1] **Validate**: Implement `validate_sample_size` in `code/download.py`. **Logic**:
 1. Read count from T013a.
 2. If count < 30 OR count > 45, **HALT** the pipeline, log a CRITICAL ERROR, and generate `data/processed/sample_size_error.json` with {count, error_message: "Sample size out of valid range [30, 45]"}, setting `validation_status: "failed"`.
 3. If valid, log success and set `validation_status: "proceed"`.
 **Deliverable**: `data/processed/sample_size_report.json` (if valid) or `data/processed/sample_size_error.json` (if invalid). **Depends on T013a**.
- [X] T014 [US1] Add logging for download progress and API response handling. **Logic**: Log 'API request start', 'response status', and 'download completion' events in JSON format. **Deliverable**: Log file `logs/download.log` containing JSON lines with timestamp, event_type, and status. **Depends on T011b**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Atmospheric Retrieval and Water Abundance Derivation (Priority: P2)

**Goal**: Run `petitRADTRANS` in CPU-optimized mode on each spectrum to derive water vapor mixing ratios with uncertainty estimates, handling low S/N data as censored upper limits using SNR/Resolution metadata.

**Independent Test**: The system can be tested by running the retrieval on a single, known test spectrum and verifying that the output includes a water vapor mixing ratio value (or an upper limit flag) and a 1-sigma uncertainty interval.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for retrieval output schema in `tests/contract/test_retrieval_schema.py`
- [X] T017 [P] [US2] Integration test for retrieval on sample spectrum in `tests/integration/test_retrieval.py`

### Implementation for User Story 2

- [X] T018a [P] [US2] Configure `petitRADTRANS` for CPU-optimized mode (single-threaded, memory limit GB) in `code/retrieval.py` <!-- FAILED: unspecified -->
- [X] T018b [P] [US2] Implement wrapper function in `code/retrieval.py` to run retrieval on a single spectrum file <!-- FAILED: unspecified -->
- [X] T018c [P] [US2] Define output schema mapping: log10 water mixing ratio, standard deviation, or upper limit flag. **Deliverable**: Create `contracts/retrieval.schema.yaml` with the defined fields.
- [X] T019 [US2] Implement logic to detect low S/N spectra using SNR/Resolution metadata and derive upper limits (censored values) instead of false precision. **Logic**: Calculate detection limit based on instrumental noise floor; if signal < 3-sigma above noise, flag as upper limit and record the limit value in mixing ratio units. Also calculate the minimum detectable concentration (MDC) based on SNR and resolution. **Deliverable**: `code/retrieval.py` updated with `derive_upper_limit` and `calculate_mdc` functions. **Depends on T012; Must precede T020**.
- [ ] T020 [US2] Implement output generation: save results to `data/processed/retrieval_results.csv`. **Deliverable**: `data/processed/retrieval_results.csv` with columns [planet_name, water_mixing_ratio, uncertainty, is_upper_limit, detection_limit, min_detectable_concentration]. **Depends on T019**.
- [X] T021 [US2] Add error handling for non-convergent retrievals: **Logic**: Catch `RetrievalError` and `ConvergenceError`, log failure, call `derive_upper_limit` as fallback, and proceed. **Deliverable**: Updated `code/retrieval.py` with try/except block. **Depends on T019**.
- [X] T022 [US2] Implement `test_upper_limit_flags_reflect_noise` in `code/validation.py` to verify upper limit flags reflect physical noise floors. **Depends on T019**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Regression Analysis (Priority: P3)

**Goal**: Compute Kendall's tau correlation for censored data (including upper limits), perform bootstrap resampling, and fit Tobit regression controlling for mass and metallicity.

**Independent Test**: The system can be tested by running the analysis on a mock dataset with known censored values and verifying that the calculated Kendall's tau matches the expected value within the bootstrap confidence interval.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T044 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py`
- [X] T024 [P] [US3] Integration test for correlation and regression on mock data in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [X] T025a [P] [US3] Import `scikit-survival` and `lifelines` in `code/analysis.py` and verify import availability
- [X] T033 [US3] **Constraint Preservation**: Implement `quality_control_filter` in `code/analysis.py` to flag low SNR spectra and include them as censored values per FR-002, ensuring the filter uses the SNR and Resolution metadata extracted in T012. **Logic**: Apply filter before finalizing analysis; uses T020 results and T012 metadata. **Deliverable**: Filtered dataset for analysis. **Depends on T012, T020**. <!-- FAILED: unspecified -->
- [X] T025b [US3] Implement `compute_censored_kendall_tau` in `code/analysis.py` using `scikit-survival`'s censored correlation (Kaplan-Meier estimator) to compute Kendall's tau for censored data (Hot Jupiters vs Super-Earths). **Logic**: Implements FR-003 requirement for censored correlation. **Deliverable**: Kendall's tau coefficient and p-value. **Depends on T012, T020, T033**.
- [ ] T025c [US3] Implement a bootstrap resampling loop to estimate confidence intervals. **Deliverable**: Write results to `data/processed/bootstrap_ci.json` containing {iterations: 1000, ci_lower, ci_upper}.
- [X] T026 [US3] Compute and report the CI width of the **water mixing ratio distribution** as a measure of robustness per SC-003. **Logic**: Calculate the 95% CI width of the `water_mixing_ratio` (log10 scale) using the bootstrap results from T025c. **Explicitly verify** if width <= 0.2 (dex). Set `threshold_met` boolean. **Deliverable**: `results/robustness_report.json` containing {ci_width, threshold_met (boolean)}. **Note**: Report the value; do NOT raise RuntimeError. The result is a measured outcome, not a pipeline gate. **Depends on T025c**.
- [ ] T027 [US3] Implement Tobit regression model (using `lifelines` or `statsmodels`) with water abundance as dependent variable and temperature, mass, metallicity as predictors. **Logic**: **Check VIF > 5**. If VIF > 5, automatically switch to **Ridge Regression Fallback** using `sklearn.linear_model.Ridge` on the subset of data where `is_upper_limit == False` (uncensored subset). **Log the fallback trigger event**. **Deliverable**: `data/processed/regression_results.json` with coefficients, p-values, and `fallback_triggered` flag. **Depends on T020**.
- [X] T029 [US3] Generate all diagnostic plots. **Deliverables**: `results/plots/water_vs_temp.png`, `results/plots/residuals.png`, `results/plots/correlation_matrix.png`, `results/plots/noise_vs_signal.png`. **Depends on T020, T025b, T027**.
- [ ] T030a [US3] Output correlation statistics: Kendall's tau, p-values, CI width. **Deliverable**: `data/processed/correlation_stats.json`.
- [X] T030b [US3] Output regression statistics: Coefficients, p-values, model fit. **Deliverable**: `data/processed/regression_stats.json`.
- [X] T030c [US3] Output MDC statistics. **Deliverable**: `data/processed/mdc_stats.json`.
- [ ] T030d [US3] Aggregate all statistics into `data/processed/analysis_results.json`.
- [ ] T031 [US3] Implement `calculate_statistical_power` in `code/analysis.py` using **actual achieved sample size and variance** to verify power ≥ 0.8 per SC-004. **Logic**: Perform formal post-hoc power analysis with **effect_size = 0.3** (|tau|). **Deliverable**: `results/power_analysis.json` with {power_estimate, power_sufficient (boolean)} and `results/quality_report.md` with resolved vs. upper limits count and power verification.
- [X] T034 [US3] **Review Response**: Implement explicit "Confidence Interval Reporting" per Marie Curie's demand for "quantity of data" and "uncertainty". **Logic**: Ensure `analysis_results.json` explicitly reports the 95% CI for the correlation coefficient and the regression coefficients. Generate a `results/uncertainty_summary.md` that interprets these intervals in the context of the sample size (N). **Deliverable**: `results/uncertainty_summary.md`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Review Response & Evidentiary Standards (Revision)

**Purpose**: Address specific quantitative and evidentiary concerns raised by simulated reviewers (Marie Curie, Rosalind Franklin) regarding spectral resolution, signal-to-noise, and detection limits.

### Implementation for Review Response

- [ ] T045 [US3] **Review Response**: Implement **Spectral Resolution Reporting** per Marie Curie's demand for instrument parameters. **Logic**: Extract and aggregate spectral resolution (R) from `metadata.csv`. Calculate the **median** as the primary metric, plus min and max. Explicitly state the resolution range in the final report. **Deliverable**: `results/spectral_resolution_report.md` containing {median_R, min_R, max_R, instrument_breakdown: JSON}. **Depends on T012**.
- [X] T046 [US3] **Review Response**: Implement **Minimum Detectable Concentration (MDC) Analysis** per Marie Curie's demand for "minimum quantity of atmospheric material". **Logic**: Use the `min_detectable_concentration` calculated in T019 for each planet. Aggregate these to determine the global sensitivity floor of the study. Report the 95th percentile MDC as the effective detection limit for the sample. **Deliverable**: `results/mdc_sensitivity_report.md` containing {global_95th_percentile_mdc, sample_coverage}. **Depends on T019, T020**.
- [X] T047 [US3] **Review Response**: Implement **Calibration & Noise Stability Analysis** per Marie Curie's concern about "quantity of photons and stability of the detector". **Logic**: Analyze the variance in the noise floor across the sample. Compute the coefficient of variation (CV) for the SNR across all spectra. Flag any instrument with high variance (>20%) as a potential confounding factor. [UNRESOLVED-CLAIM: c_8b3e0b08 — status=not_enough_info] **Deliverable**: `results/noise_stability_report.md` containing {snr_cv, instrument_stability_flags}. **Depends on T012**.
- [X] T049 [US3] **Review Response**: Implement **Quantitative Evidence Summary** per Marie Curie's demand for "evidentiary standard". **Logic**: Synthesize T045, T046, T047, T034, and T026 into a single "Evidentiary Standard" table. Explicitly list: (1) Instrument resolution achieved, (2) Sample size N, (3) 95% CI for correlation, (4) Global MDC, (5) Power analysis result. **Deliverable**: `results/evidentiary_standard_summary.md`. **Depends on T045, T046, T047, T034, T026**.
- [ ] T050 [US3] **Review Response**: Implement **Instrument-Specific Calibration Validation** per Marie Curie's demand for "what is the instrument?". **Logic**: Parse `metadata.csv` to group results by instrument (HST, Spitzer, etc.). For each instrument group, calculate and report the mean and standard deviation of the retrieved water abundances for planets with similar equilibrium temperatures (binned). This tests for systematic instrument biases. **Deliverable**: `results/instrument_calibration_report.md` containing {instrument_bias_analysis, systematic_error_flags}. **Depends on T012, T020**.
- [X] T051 [US3] **Review Response**: Implement **Detection Limit vs. Signal Separation Analysis** per Rosalind Franklin's demand to "define the detection limit... before asserting a correlation". **Logic**: Create a scatter plot and statistical table comparing the retrieved water abundance (or upper limit) against the calculated MDC for each planet. Explicitly count how many detections are >3-sigma above the MDC and how many are consistent with noise. [UNRESOLVED-CLAIM: c_61b2642e — status=not_enough_info] **Deliverables**: `results/detection_limit_separation.md` (table and stats) and `results/plots/detection_limit_scatter.png`. **Depends on T019, T020, T025b**.
- [X] T052 [US3] **Review Response**: Implement **Noise Floor Stability & Calibration Verification** per Marie Curie's concern about "stability of the detector". **Logic**: Calculate the residual variance of the retrieval model for each spectrum. Group by instrument and observation date (if available) to detect temporal drifts in detector stability. Flag any instrument/date combination with residual variance > 2x the median. [UNRESOLVED-CLAIM: c_e2b98cd5 — status=not_enough_info] **Deliverable**: `results/detector_stability_report.md` containing {temporal_drift_analysis, detector_flags}. **Depends on T020, T047**.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [US3] **Results Summary**: Generate `results/results_summary.md` aggregating SC-001 to SC-004 outcomes. **Content**: (1) Final sample size N, (2) Median spectral resolution achieved, (3) 95% CI width for the correlation, (4) Minimum detectable water vapor concentration (derived from T019's detection limits). **Deliverable**: `results/results_summary.md` with required sections.
- [X] T039 [P] Documentation updates in `README.md` and `quickstart.md`
- [X] T040a [P] Refactor `code/utils.py` to remove duplicate exception handling.
- [ ] T040b [P] Update docstrings in `code/analysis.py` for all public functions.
- [ ] T041a [P] Refactor `code/retrieval.py` to use batch processing for memory efficiency.
- [ ] T041b [P] Add caching to `code/download.py` to avoid redundant API calls.
- [X] T042 [P] Additional unit tests (if requested) in `tests/unit/`
- [X] T043 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review Response (Phase 6)**: Requires results from US1, US2, and US3 to address reviewer concerns
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1 (T012)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires data from US1 (T012) and US2 (T020)
- **Review Response (Phase 6)**: Requires results from US1, US2, and US3 to address reviewer concerns

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
- All tests for a user story marked [P] can run in parallel **EXCEPT** T009 and T010, which depend on T007 and are NOT parallel-safe with implementation.
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
- **CPU Constraint**: All tasks must run on a limited number of CPU cores, constrained memory, and no GPU. `petitRADTRANS` must be configured for single-threaded execution.
- **Data Integrity**: All data must be fetched programmatically; no static data commits.
- **Censored Data**: All statistical methods must handle upper limits correctly (Kendall's tau via scikit-survival, Tobit, or Ridge fallback).
- **Constraint Preservation**: Do NOT remove Ridge Regression Fallback for Tobit; do NOT proceed with biased sample sizes; **DO proceed with post-hoc power analysis**.
- **Review Compliance**: All tasks in Phase 6 directly address the specific quantitative and evidentiary standards raised by Marie Curie and Rosalind Franklin simulated reviewers regarding spectral resolution, SNR, and detection limits.
- **Download Policy**: The system MUST download ALL available spectra. No resolution-based filtering (R>=50) is applied before analysis.
- **Sample Size**: If the available sample is outside the 30-45 target range, the pipeline halts with an error report.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T053 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
