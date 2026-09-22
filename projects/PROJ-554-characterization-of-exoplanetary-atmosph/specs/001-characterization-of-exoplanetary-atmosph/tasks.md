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

**Independent Test**: The system can be tested by verifying that the output directory contains a metadata CSV with non-null values for temperature, metallicity, SNR, Resolution, and planet category. **Note**: The total count of unique planets is a *target* range of several tens.; if the actual count is outside this range, the pipeline logs a warning but proceeds, as per FR-001's requirement to download ALL available spectra.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [US1] Contract test for metadata schema in `tests/contract/test_metadata_schema.py` implementing `validate_metadata_schema` function. **Depends on T007**.
- [X] T010 [US1] Integration test for API download in `tests/integration/test_download.py` implementing `test_download_returns_valid_metadata` with specific mock parameters. **Depends on T007**.

### Implementation for User Story 1

- [X] T011a [P] [US1] Create `code/api_config.py` defining `QUERY_PARAMS` dictionary for NASA Exoplanet Archive API (Hot Jupiters and Super-Earths filters)
- [X] T011b [US1] Implement `code/download.py` fetch logic to retrieve spectrum files and raw metadata using `QUERY_PARAMS`. **CRITICAL**: This task MUST explicitly extract `wavelength_range` (min/max wavelength from spectrum files), `snr`, and `resolution` from the raw API response or spectrum files. **Deliverable**: Raw data with these fields populated. **Depends on T008, T011a**.
- [X] T015a [US1] **Download ALL**: Implement `download_all_spectra` in `code/download.py` to fetch **ALL** available spectra matching the criteria **without any resolution or radius filtering**. **Logic**: Use `requests` to paginate through the NASA Exoplanet Archive API results until no more data is returned. **Deliverable**: Unfiltered raw data in `data/raw/`. **Depends on T011b**.
- [X] T011c [US1] **Define Classification Thresholds**: Define the constants for "Hot Jupiter" and "Temperate Super-Earth" in `code/config.py`. **Logic**: Set `T_EQ_HOT_JUPITER_MIN = 1000`, `R_SUPER_EARTH_MAX = 1.6`. **Deliverable**: Constants defined in `code/config.py`. **Depends on T015a**.
- [X] T011d [US1] **Implement Classification Logic**: Implement `classify_planets` in `code/download.py` using thresholds from T011c. **Logic**: Tag planets as "Hot Jupiter" or "Temperate Super-Earth". **Deliverable**: In-memory dataframe with `planet_category` column populated. **Depends on T011c, T015a**.
- [X] T012 [US1] **Save Metadata**: Implement `save_metadata_csv` in `code/download.py`. **Logic**:
 1. Load raw data from T015a.
 2. **Extract Required Fields**: For each spectrum, explicitly parse or calculate `wavelength_range` (min/max wavelength), `snr`, and `resolution` from the raw data or metadata if not already present in T011b.
 3. Combine with metadata (including `planet_category` from T011d) and write to `data/processed/metadata.csv`.
 4. **Verification**: Assert that `wavelength_range`, `snr`, `resolution`, `metallicity`, and `temperature` columns are present and non-null. **If any are missing, log a WARNING and exclude that specific row from the CSV ONLY if the field is truly unparseable. DO NOT raise an error, but log the row ID for audit.**
 **Deliverable**: `data/processed/metadata.csv` with columns [planet_name, temperature, metallicity, snr, resolution, planet_category, instrument, wavelength_range]. **Depends on T011d**.
 - **Verification**: Run `pandas.read_csv('data/processed/metadata.csv')` and assert all required columns exist and row count > 0.
- [X] T013a [US1] **Count**: Implement `count_unique_planets` in `code/download.py` to count unique planets from the saved `metadata.csv`. **Logic**: Count unique values in the `planet_name` column. **Deliverable**: `data/processed/count_report.json` with {count}. **Depends on T012**.
- [X] T013b [US1] **Report Count**: Implement `report_sample_size` in `code/download.py`. **Logic**:
 1. Read count from T013a.
 2. **Do Not Halt**: Log an informational message: "Sample size [count] reported. Pipeline proceeds regardless of count per FR-001."
 3. Write `data/processed/sample_size_report.json` with {count, count_within_range (boolean), note: "Sample size reported; pipeline proceeds regardless of count."}. **Logic for boolean**: `count_within_range = (30 <= count <= 45)`. **Deliverable**: `data/processed/sample_size_report.json`. **Depends on T013a**.
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

- [X] T018a [P] [US2] Configure `petitRADTRANS` for CPU-optimized mode in `code/retrieval.py`. **Logic**: Set `threads=1` and `max_memory_gb=6` explicitly. **Deliverable**: Config object with `threads=1`, `max_memory_gb=6`.
- [X] T018b [US2] Implement wrapper function `run_single_retrieval(spectrum_path: str, config: dict) -> dict` in `code/retrieval.py` to run retrieval on a single spectrum file. **CRITICAL**: This function MUST include error handling for non-convergent retrievals: catch `RetrievalError` and `ConvergenceError`, log failure, call `derive_upper_limit` (from T019), and proceed. **Deliverable**: Function returning a dict with {water_mixing_ratio, uncertainty, is_upper_limit, convergence_status}. **Depends on T018a**.
- [X] T018c [P] [US2] Define output schema mapping: log10 water mixing ratio, standard deviation, or upper limit flag. **Deliverable**: Create `contracts/retrieval.schema.yaml` with the defined fields.
- [X] T019 [US2] Implement logic to detect low S/N spectra using SNR/Resolution metadata and derive upper limits (censored values) instead of false precision. **Logic**: Calculate detection limit based on instrumental noise floor; if signal is low (based on noise floor analysis), flag as upper limit and record the limit value in mixing ratio units. Also calculate the minimum detectable concentration (MDC) based on SNR and resolution. **Deliverable**: `code/retrieval.py` updated with `derive_upper_limit` and `calculate_mdc` functions. **Depends on T012; Must precede T020**.
- [X] T020 [US2] **Save Retrieval Results**: Implement `save_retrieval_results` in `code/retrieval.py`. **Logic**:
 1. Iterate over all spectrum files listed in `data/processed/metadata.csv`.
 2. For each file, call `run_single_retrieval` (from T018b).
 3. Handle errors: if `run_single_retrieval` fails, log the error, attempt to derive an upper limit using T019, and record the result with `is_upper_limit=True`.
 4. Aggregate all results into a list of dictionaries.
 5. Write the list to `data/processed/retrieval_results.csv`.
 **Deliverable**: `data/processed/retrieval_results.csv` with columns [planet_name, water_mixing_ratio, uncertainty, is_upper_limit, detection_limit, min_detectable_concentration]. **Depends on T019, T018b**.
 - **Verification**: Run `pandas.read_csv('data/processed/retrieval_results.csv')` and assert columns exist and row count > 0.
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
- [X] T033 [US3] **Implement Quality Control Filter**: Implement `quality_control_filter` in `code/analysis.py` to flag low SNR spectra and include them as censored values per FR-002, ensuring the filter uses the SNR and Resolution metadata extracted in T012. **Logic**:
 1. Apply filter before finalizing analysis; uses T020 results and T012 metadata.
 2. **Handle Missing Metallicity**: If a planet has missing host star metallicity, **exclude it from the regression dataset** but **retain it in the bivariate correlation dataset**.
 3. **Deliverable**: Two datasets: `data/processed/filtered_correlation_data.csv` (all planets with temperature) and `data/processed/filtered_regression_data.csv` (planets with temperature AND metallicity).
 **Depends on T012, T020**.
- [X] T025b [US3] **Compute Kendall's Tau, Bootstrap, and Save Results**: Implement `compute_censored_kendall_and_bootstrap` in `code/analysis.py`. **Logic**:
 1. Load `filtered_correlation_data.csv` (from T033).
 2. Compute **Kendall's tau** for censored data using `statsmodels`'s `TheilSen` (for slope) or a custom implementation of censored Kendall's tau (e.g., using `lifelines` or `scikit-survival`'s `KaplanMeierFitter` for survival analysis adapted to correlation) to match FR-003. If a direct censored tau function is unavailable, implement the Akritas-Theil-Sen estimator for the slope and derive tau from the rank correlation of the residuals.
 3. Perform **exactly 1000 iterations** of bootstrap resampling (seed=42) on the raw water abundance data (treating upper limits as censored observations) to estimate 95% CI.
 4. **Save Results**: Write `data/processed/correlation_stats.json` (tau, p-value, ci) and `data/processed/bootstrap_ci.json` (iterations, ci_lower, ci_upper, tau_mean) in a single atomic operation.
 5. **Stratify** results explicitly by Hot Jupiter and Super-Earth.
 **Deliverable**: `data/processed/correlation_stats.json`, `data/processed/bootstrap_ci.json`. **Depends on T033**.
- [X] T028 [US3] **Robustness Check: CI Width Calculation and Report**: Implement `calculate_and_report_ci_width` in `code/analysis.py`. **Logic**:
 1. Calculate the 95% CI width of the **bootstrapped raw water mixing ratio distribution** (not the means) to match SC-003.
 2. Explicitly verify if the water mixing ratio CI width <= 0.2 (dex) for SC-003.
 3. Save results to `results/robustness_report.json` containing {ci_width_water, threshold_met_water (boolean), ci_width_tau, threshold_met_tau (boolean)}.
 **Deliverable**: `results/robustness_report.json`. **Depends on T025b**.
- [X] T027 [US3] **Tobit Regression with Fallback and Save**: Implement `fit_tobit_model_and_save` in `code/analysis.py`. **Logic**:
 1. Load `filtered_regression_data.csv` (from T033).
 2. Fit a Tobit regression model (using `lifelines` or `statsmodels`) with water abundance as dependent variable and temperature, mass, metallicity as predictors.
 3. Check VIF > 5 using `statsmodels`' `variance_inflation_factor`. If VIF > 5, automatically switch to **Penalized Tobit Regression** (using statsmodels with L2 regularization on the coefficients) to maintain censored-data compliance.
 4. **Save Results**: Write `data/processed/regression_results.json` (coefficients, p-values, fallback_triggered) in a single atomic operation.
 **Deliverable**: `data/processed/regression_results.json`. **Depends on T020, T033**.
- [X] T029 [US3] Generate all diagnostic plots. **Deliverables**: `results/plots/water_vs_temp.png`, `results/plots/residuals.png`, `results/plots/correlation_matrix.png`, `results/plots/noise_vs_signal.png`. **Depends on T020, T025b, T027**.
- [X] T030a [US3] **Output MDC Stats**: Implement `save_mdc_stats` in `code/analysis.py`. **Logic**:
 1. Load `retrieval_results.csv` (from T020).
 2. Aggregate `min_detectable_concentration` (MDC) values: calculate median, mean, and 95th percentile.
 3. Save results to `data/processed/mdc_stats.json` with {median_mdc, mean_mdc, p95_mdc}.
 **Deliverable**: `data/processed/mdc_stats.json`. **Depends on T020**.
- [X] T030b [US3] **Aggregate Stats**: Implement `generate_analysis_results` in `code/analysis.py`. **Logic**: Load data from `correlation_stats.json` (T025b), `regression_results.json` (T027), `mdc_stats.json` (T030a), `robustness_report.json` (T028); aggregate into a single object; save to `data/processed/analysis_results.json`. **Deliverable**: `data/processed/analysis_results.json` combining T025b, T027, T030a, T028. **Depends on T025b, T027, T030a, T028**.
- [X] T031 [US3] **Power Analysis**: Implement `calculate_statistical_power` in `code/analysis.py` using a **custom bootstrap power estimator** for Kendall's tau. **Logic**:
 1. Generate 1000 bootstrap samples of the censored data (using `SEED=42`) from raw data (T020) or samples (T025b).
 2. Compute Kendall's tau for each sample.
 3. Estimate power = (count of bootstrap samples with |tau| >= 0.3) / 1000.
 4. Report `power_estimate` (float) and `power_sufficient` (boolean) if power >= 0.8.
 5. **Deliverable**: `results/power_analysis.json` MUST contain the key `power_estimate` with the calculated float value (e.g., 0.75) and `power_sufficient` (boolean). **CRITICAL**: The `power_estimate` float is required for SC-004 verification.
 **Deliverable**: `results/power_analysis.json` with {power_estimate (float), power_sufficient (boolean)} and `results/quality_report.md` with resolved vs. upper limits count and power verification. **Depends on T020, T025b**.
- [X] T034 [US3] [SC-001] [SC-003] **Review Response**: Implement explicit "Confidence Interval Reporting" per Marie Curie's demand for "quantity of data" and "uncertainty". **Logic**: Ensure `analysis_results.json` explicitly reports the 95% CI for the correlation coefficient (tau) and the regression coefficients. **CRITICAL**: Verify the CI width of the **water mixing ratio distribution** (bootstrapped means) as per SC-003. Generate a `results/uncertainty_summary.md` that interprets these intervals in the context of the sample size (N). **Deliverable**: `results/uncertainty_summary.md`. **Depends on T025b, T027, T028, T030b**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Review Response & Evidentiary Standards (Revision)

**Purpose**: Address specific quantitative and evidentiary concerns raised by simulated reviewers (Marie Curie, Rosalind Franklin) regarding spectral resolution, signal-to-noise, and detection limits.

### Implementation for Review Response

- [X] T045a [US3] [SC-001] **Data Aggregation**: Implement `aggregate_spectral_resolution` in `code/analysis.py` to extract and aggregate spectral resolution (R) from `metadata.csv`. **Logic**: Calculate the **median of all R values** as the primary metric, plus min and max. **Handle Missing**: If R is missing, exclude from median calculation but count in a "missing_count" field. **Deliverable**: `data/processed/resolution_stats.json` containing {median_R, min_R, max_R, missing_count, instrument_breakdown: JSON}. **Depends on T012**.
- [X] T045b [US3] [SC-001] **Report Generation**: Implement `generate_spectral_resolution_report` in `code/analysis.py` to read `resolution_stats.json` and write a markdown report. **Deliverable**: `results/spectral_resolution_report.md` containing {median_R, min_R, max_R, instrument_breakdown: JSON}. **Depends on T045a**.
- [X] T046 [US3] [SC-003] **Review Response**: Implement **Minimum Detectable Concentration (MDC) Analysis** per Marie Curie's demand for "minimum quantity of atmospheric material". **Logic**: Use the `min_detectable_concentration` calculated in T019 for each planet. Aggregate these to determine the global sensitivity floor of the study. Report the 95th percentile MDC as the effective detection limit for the sample. **Deliverable**: `results/mdc_sensitivity_report.md` containing {global_95th_percentile_mdc, sample_coverage}. **Depends on T019, T020**.
- [X] T047 [US3] [SC-001] **Review Response**: Implement **Calibration & Noise Stability Analysis** per Marie Curie's concern about "quantity of photons and stability of the detector". **Logic**: Analyze the variance in the noise floor across the sample. Compute the coefficient of variation (CV) for the SNR across all spectra. Flag any instrument with high variance (>20%) as a potential confounding factor. **Deliverable**: `results/noise_stability_report.md` containing {snr_cv, instrument_stability_flags}. **Depends on T012**.
 - **Verification**: Assert `noise_stability_report.md` exists and contains snr_cv and instrument_stability_flags.
- [X] T049 [US3] [SC-001] [SC-003] **Review Response**: Implement **Quantitative Evidence Summary** per Marie Curie's demand for "evidentiary standard". **Logic**: Synthesize T045b, T046, T047, T034, and T028 into a single "Evidentiary Standard" table. Explicitly list: (1) Instrument resolution achieved, (2) Sample size N, (3) 95% CI for correlation, (4) Global MDC, (5) Power analysis result. **Deliverable**: `results/evidentiary_standard_summary.md`. **Depends on T045b, T046, T047, T034, T028**.
 - **Verification**: Assert `evidentiary_standard_summary.md` exists and contains all 5 required metrics.
- [X] T050 [US3] **Review Response**: Implement **Instrument-Specific Calibration Validation** per Marie Curie's demand for "what is the instrument?". **Logic**: Parse `metadata.csv` to group results by instrument (HST, Spitzer, etc.). For each instrument group, calculate and report the mean and standard deviation of the retrieved water abundances for planets with similar equilibrium temperatures (binned). This tests for systematic instrument biases. **Deliverable**: `results/instrument_calibration_report.md` containing {instrument_bias_analysis, systematic_error_flags}. **Depends on T012, T020**.
- [X] T051 [US3] **Review Response**: Implement **Detection Limit vs. Signal Separation Analysis** per Rosalind Franklin's demand to "define the detection limit... before asserting a correlation". **Logic**: Create a scatter plot and statistical table comparing the retrieved water abundance (or upper limit) against the calculated MDC for each planet. Explicitly count how many detections are >3-sigma above the MDC and how many are consistent with noise. **Deliverables**: `results/detection_limit_separation.md` (table and stats) and `results/plots/detection_limit_scatter.png`. **Depends on T019, T020, T025b**.
 - **Verification**: Assert `detection_limit_separation.md` contains the count of >3-sigma detections and `detection_limit_scatter.png` exists.
- [X] T052 [US3] **Review Response**: Implement **Noise Floor Stability & Calibration Verification** per Marie Curie's concern about "stability of the detector". **Logic**: Calculate the residual variance of the retrieval model for each spectrum. Group by instrument and observation date (if available) to detect temporal drifts in detector stability. Flag any instrument/date combination with residual variance > 2x the median. **Deliverable**: `results/detector_stability_report.md` containing {temporal_drift_analysis, detector_flags}. **Depends on T020, T047**.
 - **Verification**: Assert `detector_stability_report.md` exists and contains temporal_drift_analysis and detector_flags.

---

## Phase 7: Final Synthesis & Verification

**Purpose**: Consolidate all evidentiary reports into a single verifiable conclusion and ensure the pipeline is reproducible.

- [X] T054a [US3] **Report Validation**: Implement `validate_reports` in `code/main.py` to check existence and schema of all 8 input reports. **Logic**: Verify `spectral_resolution_report.md`, `mdc_sensitivity_report.md`, `noise_stability_report.md`, `evidentiary_standard_summary.md`, `instrument_calibration_report.md`, `detection_limit_separation.md`, `detector_stability_report.md`, `uncertainty_summary.md` exist and contain required fields (e.g., `median_R`, `global_95th_percentile_mdc`, `snr_cv`, etc.). **Deliverable**: Validation log or error if missing. **Depends on T045b, T046, T047, T049, T050, T051, T052, T034**.
- [X] T054b [US3] **Final Synthesis**: Implement `generate_final_report` in `code/main.py` to aggregate all Phase 6 reports into a single `results/final_evidentiary_report.md`. **Logic**:
 1. Load all reports (validated by T054a).
 2. Synthesize a narrative conclusion addressing the specific concerns of Marie Curie (quantitative standards) and Rosalind Franklin (detection limits vs. noise).
 3. Explicitly state whether the correlation is statistically significant and physically distinguishable from instrumental noise based on the aggregated metrics.
 4. Include a "Methodological Integrity" section confirming that no synthetic data was used and all pipelines were executed on real fetched data.
 5. **Template**: If CI width > 0.2 OR power < 0.8, state "Results are inconclusive due to [reason]". Otherwise, state "Results support [hypothesis] with [evidence]".
 **Deliverable**: `results/final_evidentiary_report.md`. **Depends on T054a**.
- [X] T055 [P] **Reproducibility Verification**: Implement `verify_reproducibility` in `tests/integration/test_reproducibility.py`. **Logic**:
 1. Simulate a fresh run of the pipeline (downloading, retrieving, analyzing) using a fixed seed.
 2. Compare the generated `final_evidentiary_report.md` and key statistical outputs (`correlation_stats.json`, `regression_results.json`) against a baseline run (if available) or verify internal consistency (e.g., CI width calculations match reported values).
 3. Assert that the pipeline completes without errors and produces consistent results for the same input seed.
 **Deliverable**: `tests/integration/test_reproducibility.py` passing all assertions. **Depends on T053, T012, T020, T025b**.
- [X] T056 [P] **Documentation Finalization**: Update `README.md` and `quickstart.md` to include a section on "Evidentiary Standards" summarizing the quantitative metrics (Resolution, SNR, MDC) required to validate the findings. **Deliverable**: Updated documentation files. **Depends on T054b**.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [US3] **Results Summary**: Generate `results/results_summary.md` aggregating SC-001 to SC-004 outcomes. **Content**: (1) Final sample size N, (2) Median spectral resolution achieved, (3) 95% CI width for the correlation (tau), (4) Minimum detectable water vapor concentration (derived from T019's detection limits). **Deliverable**: `results/results_summary.md` with required sections.
- [X] T039 [P] Documentation updates in `README.md` and `quickstart.md`
- [X] T040 [P] **Code Quality & Documentation**: Refactor `code/utils.py`, `code/analysis.py`, `code/retrieval.py` to remove duplicates and update docstrings. **Verification**: Run `ruff check.` (pass) and ensure docstring coverage > 90%. **Depends on T012, T020, T027**.
- [X] T041 [P] **Performance Optimization**: Refactor `code/retrieval.py` for batch processing and add caching to `code/download.py`. **Verification**: Memory usage < 6GB in profiling; redundant API calls eliminated. **Depends on T012, T020**.
- [X] T042 [P] Additional unit tests (if requested) in `tests/unit/`
- [X] T043 Run quickstart.md validation
- [X] T053 [US3] **Create Pipeline Orchestrator**: Implement `code/main.py`. **Logic**: Create a Python script that:
 1. Imports `download`, `retrieval`, `analysis` modules.
 2. Parses command-line arguments: `--stage {download,retrieval,analysis,all}`, `--config path`, `--seed int`.
 3. Executes the pipeline stages in order: Download -> Retrieval -> Analysis -> Reports.
 4. Handles errors and logging via `utils.py`.
 5. **Orchestrates Review Response tasks** (T045a-T052) and Robustness Checks (T028) when `--stage all` is selected.
 6. Returns exit code 0 on success, non-zero on failure.
 7. **Dependency Check**: Verify existence of `data/processed/metadata.csv`, `data/processed/retrieval_results.csv`, `data/processed/analysis_results.json`, and all required report files in `results/` before proceeding with the full pipeline.
 **Deliverable**: `code/main.py` with a `main()` function and entry point `if __name__ == "__main__":`. **Depends on T012, T020, T027, T030b, T034, T045a-T052** (via file existence checks).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review Response (Phase 6)**: Requires results from US1, US2, and US3 to address reviewer concerns
- **Final Synthesis (Phase 7)**: Requires all Phase 6 reports to be complete
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1 (T012)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires data from US1 (T012) and US2 (T020)
- **Review Response (Phase 6)**: Requires results from US1, US2, and US3 to address reviewer concerns
- **Final Synthesis (Phase 7)**: Requires all Phase 6 reports to be complete
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
- **Censored Data**: All statistical methods must handle upper limits correctly (Kendall's tau for correlation, Tobit for regression).
- **Constraint Preservation**: Do NOT remove Penalized Tobit Regression fallback for Tobit; do NOT proceed with biased sample sizes; **DO proceed with post-hoc power analysis**.
- **Review Compliance**: All tasks in Phase 6 and Phase 7 directly address the specific quantitative and evidentiary standards raised by Marie Curie and Rosalind Franklin simulated reviewers regarding spectral resolution, SNR, and detection limits.
- **Download Policy**: The system MUST download ALL available spectra. No resolution-based filtering (R>=50) is applied before analysis.
- **Sample Size**: The pipeline reports the actual sample size regardless of count. No validation halts occur, but the count is verified against the 30-45 range in the output report.
- **Revision Compliance**: Phase 7 tasks explicitly define the quantitative evidentiary standards (SNR, Resolution, Detection Limits) requested by reviewers to distinguish a scientific correlation from qualitative pattern recognition.
- **Methodological Consistency**: Kendall's tau is used for all correlation analyses (per Spec FR-003), ensuring alignment with the functional requirement.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->