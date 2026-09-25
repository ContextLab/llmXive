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
- [X] T011c [P] [US1] **Define Classification Thresholds**: Define the constants for "Hot Jupiter" and "Temperate Super-Earth" in `code/config.py` **based on temperature and metallicity ONLY**. **Logic**: Set `T_EQ_HOT_JUPITER_MIN = 1000`, `T_EQ_HOT_JUPITER_MAX = 2500`, `T_EQ_SUPER_EARTH_MAX = 1000`, `METALLICITY_HOT_JUPITER_MIN = -0.5`, `METALLICITY_HOT_JUPITER_MAX = 0.5`, `METALLICITY_SUPER_EARTH_MAX = 0.2`. **DO NOT** use radius. **Deliverable**: Constants defined in `code/config.py`. **Depends on T008**.
- [X] T015a [US1] **Download ALL**: Implement `download_all_spectra` in `code/download.py` to fetch **ALL** available spectra matching the criteria **without any resolution or radius filtering**. **Logic**: Use `requests` to paginate through the NASA Exoplanet Archive API results until no more data is returned. **Deliverable**: Unfiltered raw data in `data/raw/`. **Depends on T011b, T011c**.
- [X] T011d [US1] **Implement Classification Logic**: Implement `classify_planets` in `code/download.py` using thresholds from T011c. **Logic**: Tag planets as "Hot Jupiter" or "Temperate Super-Earth" based on T_eq and [Fe/H]. **Deliverable**: In-memory dataframe with `planet_category` column populated. **Depends on T011c, T015a**. <!-- FAILED: unspecified -->
- [X] T012 [US1] **Save Metadata**: Implement `save_metadata_csv` in `code/download.py`. **Logic**:
 1. Load raw data from T015a.
 2. **Extract Required Fields**: For each spectrum, explicitly parse or calculate `wavelength_range` (min/max wavelength), `snr`, and `resolution` from the raw data or metadata if not already present in T011b.
 3. Combine with metadata (including `planet_category` from T011d) and write to `data/processed/metadata.csv`.
 4. **Audit, Do Not Exclude**: If any required field is truly unparseable (missing after all extraction attempts), DO NOT exclude the row. Instead, log the row ID, reason, and raw data snippet to `data/processed/exclusion_audit.json` and include the row in the CSV with a `parse_error` flag set to `True`.
 **Deliverable**: `data/processed/metadata.csv` with columns [planet_name, temperature, metallicity, snr, resolution, planet_category, instrument, wavelength_range, parse_error]. **Deliverable**: `data/processed/exclusion_audit.json`. **Depends on T011d, T015a**.
 - **Verification**: Run `pandas.read_csv('data/processed/metadata.csv')` and assert all required columns exist and row count > 0.
- [ ] T013a [US1] **Count**: Implement `count_unique_planets` in `code/download.py` to count unique planets from the saved `metadata.csv`. **Logic**: Count unique values in the `planet_name` column. **Deliverable**: `data/processed/count_report.json` with {count}. **Depends on T012**.
- [X] T013b [US1] **Report Count**: Implement `report_sample_size` in `code/download.py`. **Logic**:
 1. Read count from T013a.
 2. **Testability**: Check if `30 <= count <= 45`. Set `test_failure = True` if outside range.
 3. Log an informational message: "Sample size [count] reported. Pipeline proceeds regardless of count per FR-001."
 4. Write `data/processed/sample_size_report.json` with {count, count_within_range (boolean), test_failure (boolean), note: "Sample size reported; pipeline proceeds regardless."}. **Logic for boolean**: `count_within_range = (30 <= count <= 45)`. **Deliverable**: `data/processed/sample_size_report.json`. **Depends on T013a**.
- [X] T014 [US1] Add logging for download progress and API response handling. **Logic**: Log 'API request start', 'response status', and 'download completion' events in JSON format. **Deliverable**: Log file `logs/download.log` containing JSON lines with timestamp, event_type, and status. **Depends on T011b**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Atmospheric Retrieval and Water Abundance Derivation (Priority: P2)

**Goal**: Run `petitRADTRANS` in CPU-optimized mode on each spectrum to derive water vapor mixing ratios with uncertainty estimates, handling low S/N data as censored upper limits using SNR/Resolution metadata.

**Independent Test**: The system can be tested by running the retrieval on a single, known test spectrum and verifying that the output includes a water vapor mixing ratio value (or an upper limit flag) and a 1-sigma uncertainty interval.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for retrieval output schema in `tests/contract/test_retrieval_schema.py`
- [X] T017 [P] [US2] Integration test for retrieval on sample spectrum in `tests/integration/test_retrieval.py` <!-- FAILED: unspecified -->

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
 2. Compute **Kendall's tau** for censored data using `scikit-survival`'s `concordance_index_censored` adapted for correlation or a custom rank-based algorithm that handles censored observations directly. **Do NOT** use Akritas-Theil-Sen for this.
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
 3. Check VIF > 5 using `statsmodels`' `variance_inflation_factor`. If VIF > 5, fall back to **Censored Regression using `lifelines.CoxPHFitter`** (adapted for continuous outcomes via proportional hazards assumption on the water abundance) or standard Tobit with a note on collinearity, as standard libraries may not support Penalized Tobit. Document this fallback.
 4. **Save Results**: Write `data/processed/regression_results.json` (coefficients, p-values, fallback_triggered) in a single atomic operation.
 **Deliverable**: `data/processed/regression_results.json`. **Depends on T020, T033**.
- [X] T029 [US3] Generate all diagnostic plots. **Deliverables**: `results/plots/water_vs_temp.png`, `results/plots/residuals.png`, `results/plots/correlation_matrix.png`, `results/plots/noise_vs_signal.png`. **Depends on T020, T025b, T027**.
- [X] T030a [US3] **Output MDC Stats**: Implement `save_mdc_stats` in `code/analysis.py`. **Logic**:
 1. Load `retrieval_results.csv` (from T020).
 2. Aggregate `min_detectable_concentration` (MDC) values: calculate median, mean, and 95th percentile.
 3. Save results to `data/processed/mdc_stats.json` with {median_mdc, mean_mdc, p95_mdc}.
 **Deliverable**: `data/processed/mdc_stats.json`. **Depends on T020**.
- [ ] T030b [US3] **Aggregate Stats**: Implement `generate_analysis_results` in `code/analysis.py`. **Logic**: Load data from `correlation_stats.json` (T025b), `regression_results.json` (T027), `mdc_stats.json` (T030a), `robustness_report.json` (T028); aggregate into a single object; save to `data/processed/analysis_results.json`. **Deliverable**: `data/processed/analysis_results.json` combining T025b, T027, T030a, T028. **Depends on T025b, T027, T030a, T028**.
- [X] T031 [US3] **Power Analysis**: Implement `calculate_statistical_power` in `code/analysis.py` using a **simulation-based power estimator** for Kendall's tau. **Logic**:
 1. Generate 1000 synthetic datasets with a known true tau of 0.3 (moderate correlation) and sample size N equal to the actual dataset size.
 2. Add noise consistent with the observed data distribution.
 3. Run the censored Kendall's tau analysis on each synthetic dataset.
 4. Estimate power = (count of synthetic samples where null hypothesis is rejected at alpha=0.05) / 1000.
 5. Report `power_estimate` (float) and `power_sufficient` (boolean) if power >= 0.8.
 6. **Deliverable**: `results/power_analysis.json` MUST contain the key `power_estimate` with the calculated float value (e.g., 0.75) and `power_sufficient` (boolean). **CRITICAL**: The `power_estimate` float is required for SC-004 verification.
 **Deliverable**: `results/power_analysis.json` with {power_estimate (float), power_sufficient (boolean)} and `results/quality_report.md` with resolved vs. upper limits count and power verification. **Depends on T020, T025b**.
- [X] T034 [US3] [SC-001] [SC-003] **Review Response**: Implement explicit "Confidence Interval Reporting" per Marie Curie's demand for "quantity of data" and "uncertainty". **Logic**: Ensure `analysis_results.json` explicitly reports the 95% CI for the correlation coefficient (tau) and the regression coefficients. **CRITICAL**: Verify the CI width of the **water mixing ratio distribution** (bootstrapped means) as per SC-003. Generate a `results/uncertainty_summary.md` that interprets these intervals in the context of the sample size (N). **Deliverable**: `results/uncertainty_summary.md`. **Depends on T025b, T027, T028, T030b**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Final Synthesis & Verification

**Purpose**: Consolidate all evidentiary reports into a single verifiable conclusion and ensure the pipeline is reproducible.

- [ ] T054a [US3] **Report Validation**: Implement `validate_reports` in `code/main.py` to check existence and schema of all required reports. **Logic**: Verify `correlation_stats.json`, `regression_results.json`, `robustness_report.json`, `power_analysis.json`, `uncertainty_summary.md` exist and contain required fields. **Deliverable**: Validation log or error if missing. **Depends on T025b, T027, T028, T031, T034**.
- [ ] T054b [US3] **Final Synthesis**: Implement `generate_final_report` in `code/main.py` to aggregate all reports into a single `results/final_evidentiary_report.md`. **Logic**:
 1. Load all reports (validated by T054a).
 2. Synthesize a narrative conclusion addressing the specific concerns of the spec (correlation significance, detection limits).
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
- [ ] T040 [P] **Code Quality & Documentation**: Refactor `code/utils.py`, `code/analysis.py`, `code/retrieval.py` to remove duplicates and update docstrings. **Verification**: Run `ruff check.` (pass) and ensure docstring coverage > 90%. **Depends on T012, T020, T027**.
- [ ] T041 [P] **Performance Optimization**: Refactor `code/retrieval.py` for batch processing and add caching to `code/download.py`. **Verification**: Memory usage < 6GB in profiling; redundant API calls eliminated. **Depends on T012, T020**.
- [X] T042 [P] Additional unit tests (if requested) in `tests/unit/`
- [X] T043 Run quickstart.md validation
- [ ] T053 [US3] **Create Pipeline Orchestrator**: Implement `code/main.py`. **Logic**: Create a Python script that:
 1. Imports `download`, `retrieval`, `analysis` modules.
 2. Parses command-line arguments: `--stage {download,retrieval,analysis,all}`, `--config path`, `--seed int`.
 3. Executes the pipeline stages in order: Download -> Retrieval -> Analysis -> Reports.
 4. Handles errors and logging via `utils.py`.
 5. **Orchestrates Robustness Checks** (T028) and **Power Analysis** (T031) when `--stage all` is selected.
 6. Returns exit code 0 on success, non-zero on failure.
 7. **Dependency Check**: Verify existence of `data/processed/metadata.csv`, `data/processed/retrieval_results.csv`, `data/processed/analysis_results.json`, and all required report files in `results/` before proceeding with the full pipeline.
 **Deliverable**: `code/main.py` with a `main()` function and entry point `if __name__ == "__main__":`. **Depends on T012, T020, T027, T030b, T034** (via file existence checks).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Final Synthesis (Phase 7)**: Requires all Phase 5 reports to be complete
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1 (T012)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires data from US1 (T012) and US2 (T020)
- **Final Synthesis (Phase 7)**: Requires all Phase 5 reports to be complete
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
- Phase 7 tasks can be implemented in parallel as they are independent validations

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
- **Download Policy**: The system MUST download ALL available spectra. No resolution-based filtering (R>=50) is applied before analysis.
- **Sample Size**: The pipeline reports the actual sample size regardless of count. No validation halts occur, but the count is verified against the 30-45 range in the output report.
- **Revision Compliance**: Phase 7 and Phase 8 tasks explicitly define the quantitative evidentiary standards (SNR, Resolution, Detection Limits) requested by reviewers to distinguish a scientific correlation from qualitative pattern recognition.
- **Methodological Consistency**: Kendall's tau is used for all correlation analyses (per Spec FR-003), ensuring alignment with the functional requirement.
- **Quantitative Standards**: Phase 6 tasks (T045-T052, T059) are critical for addressing the specific quantitative demands from Marie Curie and Rosalind Franklin reviews, ensuring that the correlation claim is backed by rigorous evidentiary standards.
