# Tasks: Characterization of Exoplanetary Atmospheres through Advanced Spectroscopic Techniques

**Input**: Design documents from `/specs/001-characterization-of-exoplanetary-atmosph/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
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

**Independent Test**: The system can be tested by verifying that the output directory contains a metadata CSV with non-null values for temperature, metallicity, SNR, Resolution, and planet category. **Note**: The total count of unique planets is a *target* range of several tens.; if the actual count is outside this range, the pipeline logs a warning but proceeds, as per FR-001's requirement to download ALL available spectra.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [US1] Contract test for metadata schema in `tests/contract/test_metadata_schema.py` implementing `validate_metadata_schema` function. **Depends on T007**.
- [X] T010 [US1] Integration test for API download in `tests/integration/test_download.py` implementing `test_download_returns_valid_metadata` with specific mock parameters. **Depends on T007**.

### Implementation for User Story 1

- [X] T011a [US1] Create `code/api_config.py` defining `QUERY_PARAMS` dictionary for NASA Exoplanet Archive API (Hot Jupiters and Super-Earths filters)
- [X] T011b [US1] Implement `code/download.py` fetch logic to retrieve spectrum files and raw metadata using `QUERY_PARAMS`. **CRITICAL**: This task MUST explicitly extract `wavelength_range` (min/max wavelength from spectrum files), `snr`, and `resolution` from the raw API response or spectrum files. **Deliverable**: Raw data with these fields populated. **Depends on T008**.
- [X] T015a [US1] **Download ALL**: Implement `download_all_spectra` in `code/download.py` to fetch **ALL** available spectra matching the criteria **without any resolution or radius filtering**. **Deliverable**: Unfiltered raw data in `data/raw/`. **Depends on T011b**.
- [X] T011c [US1] **Classification Logic**: Implement classification logic in `code/download.py` to tag planets as "Hot Jupiter" or "Temperate Super-Earth". **Logic**:
 - Apply standard literature definitions for "Hot Jupiter" (e.g., irradiated gas giants) and "Temperate Super-Earth" (rocky/mini-Neptune boundary).
 - **Use specific thresholds**: `T_eq > 1000K` for Hot Jupiters and `R < 1.6 R_E` (and `T_eq < 1000K`) for Super-Earths.
 - **Citation Logging**: Log the specific threshold and citation (e.g., "Fortney et al. 2008") in `logs/classification.log` as part of this task execution.
 - **Deliverable**: In-memory dataframe with `planet_category` column populated and `logs/classification.log` updated. **Depends on T015a**.
- [ ] T012 [US1] **Save Metadata**: Implement `save_metadata_csv` in `code/download.py`. **Logic**: Combine downloaded spectra with metadata (including SNR, R, instrument, wavelength, and `planet_category` from T011c) and write to `data/processed/metadata.csv`. **CRITICAL**: This task MUST verify that `wavelength_range`, `snr`, and `resolution` columns are present and non-null before writing. If missing, the task MUST fail. **Deliverable**: `data/processed/metadata.csv` with columns [planet_name, temperature, metallicity, snr, resolution, planet_category, instrument, wavelength_range]. **Depends on T011c**.
 - **Verification**: Run `pandas.read_csv('data/processed/metadata.csv')` and assert all required columns exist and row count > 0.
- [ ] T013a [US1] **Count**: Implement `count_unique_planets` in `code/download.py` to count unique planets from the saved `metadata.csv`. **Deliverable**: `data/processed/count_report.json` with {count}. **Depends on T012**.
- [ ] T013b [US1] **Report Count**: Implement `report_sample_size` in `code/download.py`. **Logic**:
 1. Read count from T013a.
 2. **DO NOT VALIDATE OR HALT**. Log an informational message: "Sample size [count] reported. Pipeline proceeds regardless of count per FR-001."
 3. Write `data/processed/sample_size_report.json` with {count, note: "Sample size reported; pipeline proceeds regardless of count."}.
 **Deliverable**: `data/processed/sample_size_report.json`. **Depends on T013a**.
- [X] T014 [US1] Add logging for download progress and API response handling. **Logic**: Log 'API request start', 'response status', and 'download completion' events in JSON format. **Deliverable**: Log file `logs/download.log` containing JSON lines with timestamp, event_type, and status. **Depends on T011b**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Atmospheric Retrieval and Water Abundance Derivation (Priority: P2)

**Goal**: Run `petitRADTRANS` in CPU-optimized mode on each spectrum to derive water vapor mixing ratios with uncertainty estimates, handling low S/N data as censored upper limits using SNR/Resolution metadata.

**Independent Test**: The system can be tested by running the retrieval on a single, known test spectrum and verifying that the output includes a water vapor mixing ratio value (or an upper limit flag) and a 1-sigma uncertainty interval.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for retrieval output schema in `tests/contract/test_retrieval_schema.py`
- [ ] T017 [P] [US2] Integration test for retrieval on sample spectrum in `tests/integration/test_retrieval.py`

### Implementation for User Story 2

- [ ] T018a [P] [US2] Configure `petitRADTRANS` for CPU-optimized mode (single-threaded, memory limit GB) in `code/retrieval.py`. **Deliverable**: Config object with `threads=1`, `max_memory_gb=6`.
- [ ] T018b [US2] Implement wrapper function `run_single_retrieval(spectrum_path: str, config: dict) -> dict` in `code/retrieval.py` to run retrieval on a single spectrum file. **CRITICAL**: This function MUST include error handling for non-convergent retrievals (T021 logic): catch `RetrievalError` and `ConvergenceError`, log failure, call `derive_upper_limit`, and proceed. **Deliverable**: Function returning a dict with {water_mixing_ratio, uncertainty, is_upper_limit, convergence_status}. **Depends on T018a**.
- [X] T018c [P] [US2] Define output schema mapping: log10 water mixing ratio, standard deviation, or upper limit flag. **Deliverable**: Create `contracts/retrieval.schema.yaml` with the defined fields.
- [ ] T019 [US2] Implement logic to detect low S/N spectra using SNR/Resolution metadata and derive upper limits (censored values) instead of false precision. **Logic**: Calculate detection limit based on instrumental noise floor; if signal is low (based on noise floor analysis), flag as upper limit and record the limit value in mixing ratio units. Also calculate the minimum detectable concentration (MDC) based on SNR and resolution. **Deliverable**: `code/retrieval.py` updated with `derive_upper_limit` and `calculate_mdc` functions. **Depends on T012; Must precede T020**.
- [ ] T020 [US2] **Save Retrieval Results**: Implement `save_retrieval_results` in `code/retrieval.py`. **Logic**: Iterate over all spectra, run `run_single_retrieval` (from T018b, which includes error handling), and aggregate results. **Deliverable**: `data/processed/retrieval_results.csv` with columns [planet_name, water_mixing_ratio, uncertainty, is_upper_limit, detection_limit, min_detectable_concentration]. **Depends on T019, T018b**.
 - **Verification**: Run `pandas.read_csv('data/processed/retrieval_results.csv')` and assert columns exist and row count > 0.
- [X] T022 [US2] Implement `test_upper_limit_flags_reflect_noise` in `code/validation.py` to verify upper limit flags reflect physical noise floors. **Depends on T019**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Regression Analysis (Priority: P3)

**Goal**: Compute Kendall's tau correlation for censored data (including upper limits), perform bootstrap resampling, and fit Tobit regression controlling for mass and metallicity.

**Independent Test**: The system can be tested by running the analysis on a mock dataset with known censored values and verifying that the calculated Kendall's tau matches the expected value within the bootstrap confidence interval.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T044 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py`
- [ ] T024 [P] [US3] Integration test for correlation and regression on mock data in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T025a [P] [US3] Import `scikit-survival` and `lifelines` in `code/analysis.py` and verify import availability
- [ ] T033 [US3] **Implement Quality Control Filter**: Implement `quality_control_filter` in `code/analysis.py` to flag low SNR spectra and include them as censored values per FR-002, ensuring the filter uses the SNR and Resolution metadata extracted in T012. **Logic**:
 1. Apply filter before finalizing analysis; uses T020 results and T012 metadata.
 2. **Handle Missing Metallicity**: If a planet has missing host star metallicity, **exclude it from the regression dataset** but **retain it in the bivariate correlation dataset**.
 3. **Deliverable**: Two datasets: `data/processed/filtered_correlation_data.csv` (all planets with temperature) and `data/processed/filtered_regression_data.csv` (planets with temperature AND metallicity).
 **Depends on T012, T020**.
- [ ] T025b [US3] **Compute Akritas-Theil-Sen**: Implement `compute_censored_ats` in `code/analysis.py` using `scikit-survival`'s `CensoredData` class and the **Akritas-Theil-Sen** estimator (specifically `scikit-survival`'s `censored_kendall_tau` or equivalent ATS method for censored data). **Logic**: Implements FR-003 requirement for censored correlation. **Stratify results explicitly by Hot Jupiter and Super-Earth**. **Deliverable**: ATS coefficient and p-value per category. **Depends on T012, T020, T033**.
- [ ] T025c [US3] **Bootstrap Resampling**: Implement `bootstrap_ats` in `code/analysis.py`. **Logic**: Run **exactly 1000 iterations** with random seed `SEED=42`. For each iteration, resample the **raw water abundance data** (from T020) with replacement and recompute ATS. **Deliverable**: Write results to `data/processed/bootstrap_ci.json` containing {iterations: 1000, ci_lower, ci_upper, tau_mean} and `data/processed/water_mixing_ratio_samples.npy` (numpy compressed array of bootstrapped mixing ratio distributions). **Depends on T025b, T020**.
 - **Verification**: Assert `bootstrap_ci.json` contains keys {iterations, ci_lower, ci_upper, tau_mean} and `iterations == 1000`. Assert `water_mixing_ratio_samples.npy` is loadable and has correct shape.
- [ ] T028a [US3] **Robustness Check (Variable) - Calculation**: Implement `calculate_ci_width_variable` in `code/analysis.py`. **Logic**: Calculate the 95% CI width of the **bootstrapped water mixing ratio means** (derived from the `water_mixing_ratio_samples` in T025c's bootstrap results). **Deliverable**: CI width value. **Depends on T025c**.
- [ ] T028b [US3] **Robustness Check (Variable) - Verification**: Implement `verify_ci_width_variable` in `code/analysis.py`. **Logic**: **Explicitly verify** if width <= 0.2 (dex). Set `threshold_met` boolean. **Deliverable**: Boolean flag. **Depends on T028a**.
- [ ] T028c [US3] **Robustness Check (Variable) - Report**: Implement `save_robustness_report_variable` in `code/analysis.py`. **Deliverable**: `results/robustness_report_variable.json` containing {ci_width, threshold_met (boolean)}. **Depends on T028b**.
- [ ] T029a [US3] **Robustness Check (Tau) - Calculation**: Implement `calculate_ci_width_tau` in `code/analysis.py`. **Logic**: Calculate the 95% CI width of the **ATS coefficient** itself (derived from the 1000 bootstrap tau values in T025c). **Deliverable**: CI width value. **Depends on T025c**.
- [ ] T029b [US3] **Robustness Check (Tau) - Verification**: Implement `verify_ci_width_tau` in `code/analysis.py`. **Logic**: **Explicitly verify** if width <= 0.2 (or report the width). **Deliverable**: Boolean flag. **Depends on T029a**.
- [ ] T029c [US3] **Robustness Check (Tau) - Report**: Implement `save_robustness_report_tau` in `code/analysis.py`. **Deliverable**: `results/robustness_report_tau.json` containing {ci_width_tau, threshold_met (boolean)}. **Depends on T029b**.
- [ ] T027 [US3] **Tobit Regression with Fallback**: Implement `fit_tobit_model` in `code/analysis.py`. **Logic**: Fit a Tobit regression model (using `lifelines` or `statsmodels`) with water abundance as dependent variable and temperature, mass, metallicity as predictors on the **filtered regression dataset** (from T033). **Check VIF > 5**. If VIF > 5, automatically switch to **Tobit Regression with Ridge Regularization** (implemented via custom likelihood or `statsmodels` with penalty) on the **full dataset including upper limits**. **Log the fallback trigger event**. **Note**: This task assumes T025b (ATS) has already handled the correlation requirement. **Deliverable**: `data/processed/regression_results.json` with coefficients, p-values, and `fallback_triggered` flag. **Depends on T020, T033**.
 - **Verification**: Assert `regression_results.json` exists and contains `fallback_triggered` boolean and coefficients.
- [X] T029 [US3] Generate all diagnostic plots. **Deliverables**: `results/plots/water_vs_temp.png`, `results/plots/residuals.png`, `results/plots/correlation_matrix.png`, `results/plots/noise_vs_signal.png`. **Depends on T020, T025b, T027**.
- [ ] T030a [US3] **Output Correlation Stats**: Implement `save_correlation_stats` in `code/analysis.py`. **Deliverable**: `data/processed/correlation_stats.json` with {tau, p_value, ci_lower, ci_upper}. **Depends on T025b, T025c**.
 - **Verification**: Assert `correlation_stats.json` contains keys {tau, p_value, ci_lower, ci_upper}.
- [ ] T030b [US3] **Output Regression Stats**: Implement `save_regression_stats` in `code/analysis.py`. **Deliverable**: `data/processed/regression_stats.json` with coefficients, p-values, model fit. **Depends on T027**.
- [ ] T030c [US3] **Output MDC Stats**: Implement `save_mdc_stats` in `code/analysis.py`. **Deliverable**: `data/processed/mdc_stats.json`. **Depends on T020**.
- [ ] T030d [US3] **Aggregate Stats (Part 1)**: Implement `load_analysis_inputs` in `code/analysis.py`. **Deliverable**: Loaded data objects. **Depends on T030a, T030b, T030c, T028c, T029c**.
- [ ] T030e [US3] **Aggregate Stats (Part 2)**: Implement `aggregate_analysis_data` in `code/analysis.py`. **Deliverable**: Aggregated data object. **Depends on T030d**.
- [ ] T030f [US3] **Aggregate Stats (Part 3)**: Implement `save_aggregated_analysis_results` in `code/analysis.py`. **Deliverable**: `data/processed/analysis_results.json` combining T030a, T030b, T030c, T028c, T029c. **Depends on T030e**.
- [ ] T031 [US3] **Power Analysis**: Implement `calculate_statistical_power` in `code/analysis.py` using a **custom bootstrap power estimator** for ATS. **Logic**: Generate 1000 bootstrap samples of the censored data, compute ATS for each, and estimate the power to detect |tau| >= 0.3 at alpha=0.05. **Calculate power = (count of bootstrap samples with |tau| >= 0.3) / 1000**. **Report power_sufficient (boolean)** if power >= 0.8. **Deliverable**: `results/power_analysis.json` with {power_estimate, power_sufficient (boolean)} and `results/quality_report.md` with resolved vs. upper limits count and power verification. **Depends on T030a**.
- [ ] T034 [US3] [SC-001] [SC-003] **Review Response**: Implement explicit "Confidence Interval Reporting" per Marie Curie's demand for "quantity of data" and "uncertainty". **Logic**: Ensure `analysis_results.json` explicitly reports the 95% CI for the correlation coefficient (tau) and the regression coefficients. **CRITICAL**: Verify the CI width of the **water mixing ratio distribution** (bootstrapped means) as per SC-003. Generate a `results/uncertainty_summary.md` that interprets these intervals in the context of the sample size (N). **Deliverable**: `results/uncertainty_summary.md`. **Depends on T030a, T030b, T029c, T030f**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Review Response & Evidentiary Standards (Revision)

**Purpose**: Address specific quantitative and evidentiary concerns raised by simulated reviewers (Marie Curie, Rosalind Franklin) regarding spectral resolution, signal-to-noise, and detection limits.

### Implementation for Review Response

- [ ] T045 [US3] [SC-001] **Review Response**: Implement **Spectral Resolution Reporting** per Marie Curie's demand for instrument parameters. **Logic**: Extract and aggregate spectral resolution (R) from `metadata.csv`. Calculate the **median of all R values** as the primary metric, plus min and max. Explicitly state the resolution range in the final report. **Deliverable**: `results/spectral_resolution_report.md` containing {median_R, min_R, max_R, instrument_breakdown: JSON}. **Depends on T012**.
 - **Verification**: Assert `spectral_resolution_report.md` exists and contains median, min, and max R values.
- [X] T046 [US3] [SC-003] **Review Response**: Implement **Minimum Detectable Concentration (MDC) Analysis** per Marie Curie's demand for "minimum quantity of atmospheric material". **Logic**: Use the `min_detectable_concentration` calculated in T019 for each planet. Aggregate these to determine the global sensitivity floor of the study. Report the 95th percentile MDC as the effective detection limit for the sample. **Deliverable**: `results/mdc_sensitivity_report.md` containing {global_95th_percentile_mdc, sample_coverage}. **Depends on T019, T020**.
- [X] T047 [US3] [SC-001] **Review Response**: Implement **Calibration & Noise Stability Analysis** per Marie Curie's concern about "quantity of photons and stability of the detector". **Logic**: Analyze the variance in the noise floor across the sample. Compute the coefficient of variation (CV) for the SNR across all spectra. Flag any instrument with high variance (>20%) as a potential confounding factor. **Deliverable**: `results/noise_stability_report.md` containing {snr_cv, instrument_stability_flags}. **Depends on T012**.
 - **Verification**: Assert `noise_stability_report.md` exists and contains snr_cv and instrument_stability_flags.
- [X] T049 [US3] [SC-001] [SC-003] **Review Response**: Implement **Quantitative Evidence Summary** per Marie Curie's demand for "evidentiary standard". **Logic**: Synthesize T045, T046, T047, T034, and T029c into a single "Evidentiary Standard" table. Explicitly list: (1) Instrument resolution achieved, (2) Sample size N, (3) 95% CI for correlation, (4) Global MDC, (5) Power analysis result. **Deliverable**: `results/evidentiary_standard_summary.md`. **Depends on T045, T046, T047, T034, T029c**.
 - **Verification**: Assert `evidentiary_standard_summary.md` exists and contains all 5 required metrics.
- [ ] T050 [US3] **Review Response**: Implement **Instrument-Specific Calibration Validation** per Marie Curie's demand for "what is the instrument?". **Logic**: Parse `metadata.csv` to group results by instrument (HST, Spitzer, etc.). For each instrument group, calculate and report the mean and standard deviation of the retrieved water abundances for planets with similar equilibrium temperatures (binned). This tests for systematic instrument biases. **Deliverable**: `results/instrument_calibration_report.md` containing {instrument_bias_analysis, systematic_error_flags}. **Depends on T012, T020**.
- [X] T051 [US3] **Review Response**: Implement **Detection Limit vs. Signal Separation Analysis** per Rosalind Franklin's demand to "define the detection limit... before asserting a correlation". **Logic**: Create a scatter plot and statistical table comparing the retrieved water abundance (or upper limit) against the calculated MDC for each planet. Explicitly count how many detections are >3-sigma above the MDC and how many are consistent with noise. **Deliverables**: `results/detection_limit_separation.md` (table and stats) and `results/plots/detection_limit_scatter.png`. **Depends on T019, T020, T025b**.
 - **Verification**: Assert `detection_limit_separation.md` contains the count of >3-sigma detections and `detection_limit_scatter.png` exists.
- [X] T052 [US3] **Review Response**: Implement **Noise Floor Stability & Calibration Verification** per Marie Curie's concern about "stability of the detector". **Logic**: Calculate the residual variance of the retrieval model for each spectrum. Group by instrument and observation date (if available) to detect temporal drifts in detector stability. Flag any instrument/date combination with residual variance > 2x the median. **Deliverable**: `results/detector_stability_report.md` containing {temporal_drift_analysis, detector_flags}. **Depends on T020, T047**.
 - **Verification**: Assert `detector_stability_report.md` exists and contains temporal_drift_analysis and detector_flags.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [US3] **Results Summary**: Generate `results/results_summary.md` aggregating SC-001 to SC-004 outcomes. **Content**: (1) Final sample size N, (2) Median spectral resolution achieved, (3) 95% CI width for the correlation (tau), (4) Minimum detectable water vapor concentration (derived from T019's detection limits). **Deliverable**: `results/results_summary.md` with required sections.
- [X] T039 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T040 [P] **Code Quality & Documentation**: Refactor `code/utils.py`, `code/analysis.py`, `code/retrieval.py` to remove duplicates and update docstrings. **Verification**: Run `ruff check .` (pass) and ensure docstring coverage > 90%. **Depends on T012, T020, T027**.
- [ ] T041 [P] **Performance Optimization**: Refactor `code/retrieval.py` for batch processing and add caching to `code/download.py`. **Verification**: Memory usage < 6GB in profiling; redundant API calls eliminated. **Depends on T012, T020**.
- [X] T042 [P] Additional unit tests (if requested) in `tests/unit/`
- [X] T043 Run quickstart.md validation
- [ ] T053 [US3] **Create Pipeline Orchestrator**: Implement `code/main.py`. **Logic**: Create a Python script that:
 1. Imports `download`, `retrieval`, `analysis` modules.
 2. Parses command-line arguments: `--stage {download,retrieval,analysis,all}`, `--config path`, `--seed int`.
 3. Executes the pipeline stages in order: Download -> Retrieval -> Analysis -> Reports.
 4. Handles errors and logging via `utils.py`.
 5. **Orchestrates Review Response tasks** (T045-T052) and Robustness Checks (T028, T029) when `--stage all` is selected.
 6. Returns exit code 0 on success, non-zero on failure.
 **Deliverable**: `code/main.py` with a `main()` function and entry point `if __name__ == "__main__":`. **Depends on T012, T020, T027, T030f, T034, T045-T052**.

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
- **Polish (Final Phase)**: Depends on all desired user stories being complete

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
- **Censored Data**: All statistical methods must handle upper limits correctly (Akritas-Theil-Sen for correlation, Tobit for regression).
- **Constraint Preservation**: Do NOT remove Ridge Regression Fallback for Tobit; do NOT proceed with biased sample sizes; **DO proceed with post-hoc power analysis**.
- **Review Compliance**: All tasks in Phase 6 directly address the specific quantitative and evidentiary standards raised by Marie Curie and Rosalind Franklin simulated reviewers regarding spectral resolution, SNR, and detection limits.
- **Download Policy**: The system MUST download ALL available spectra. No resolution-based filtering (R>=50) is applied before analysis.
- **Sample Size**: The pipeline reports the actual sample size regardless of count. No validation halts occur.
- **Revision Compliance**: Phase 7 tasks explicitly define the quantitative evidentiary standards (SNR, Resolution, Detection Limits) requested by reviewers to distinguish a scientific correlation from qualitative pattern recognition. **(Note: Phase 7 removed in this revision; thresholds are reported in Phase 6).**
- **Methodological Consistency**: Akritas-Theil-Sen is used for all correlation analyses (per Spec FR-003 and Plan Complexity Tracking), overriding Plan.md's mention of standard Kendall's tau.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->