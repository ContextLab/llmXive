---
description: "Task list for feature implementation: Cosmic Ray Composition and Solar Activity Cycles"
---

# Tasks: Exploring the Relationship Between Cosmic Ray Composition and Solar Activity Cycles

**Input**: Design documents from `/specs/001-cosmic-ray-composition-solar-cycle/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.,g, US1, US2, US3)
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

- [X] T001a [P] Create `code/` directory structure
- [X] T001b [P] Create `tests/` directory structure
- [X] T001c [P] Create `data/` directory structure (`data/raw/`, `data/processed/`, `data/checksums.txt`)
- [X] T002 [P] Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `scikit-learn`, `scipy`, `matplotlib`, `requests`, `pyyaml`, `statsmodels`, `pytest`, `psutil`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Data Fetching Strategy.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/utils/config.py` to manage dataset URLs (AMS-02, NOAA) and run parameters
- [X] T005 [P] Implement `code/utils/logging.py` for structured logging of data gaps and fetch errors. **Constraint**: Must output JSON-formatted logs to `logs/pipeline.log` (NOT `data/logs/`) with levels `INFO`, `WARNING`, `ERROR`. Must include a `DataFetchError` exception class. Logs must reside outside the `data/` hierarchy to comply with Constitution Principle III (Data Hygiene).
- [X] T006 [P] Create `docs/protocol_lag_analysis.md` documenting the lag analysis protocol (±12 months) and gap handling rules to satisfy Constitution Principle VII.
- [X] T007a [P] Create `code/data/models.py` entity `CosmicRayFlux` with explicit `rigidity` (float) attribute to support Constitution Principle VI.
- [X] T007b [P] Create `code/data/models.py` entity `SolarActivityIndex` with `date`, `sunspot_number`, `solar_wind_speed`.
- [X] T007c [P] Create `code/data/models.py` entity `CompositionRatio` with `date`, `numerator_species`, `denominator_species`, `ratio_value`.
- [X] T008 [P] Implement checksum verification script `code/utils/verify_checksums.py`
- [X] T043 [P] Refactor `code/data/fetch_ams02.py` to implement **streaming** for large AMS-02 datasets using `requests` and chunked HTTP iteration. **Constraint**: Use `psutil` to check available RAM. Chunk data until a significant portion of available RAM is reached or a predefined data threshold is processed, whichever comes first.. **Requirement**: The task must explicitly state the streaming rule and ensure the final unified dataset is accumulated online.
- [X] T044 [P] Update `code/data/fetch_ams02.py` to adopt any **verified real data source** (package + access recipe) if provided by the execution stage. **Constraint**: If a "VERIFIED REAL DATA SOURCE" block is detected in execution feedback, replace the current URL-based fetch logic with the exact package/recipe provided. If no verified source is provided, this task is a no-op. Do not keep hand-rolled URLs alongside verified sources.
- [X] T053 [P] [US1] **Verification of Fail Loudly**: Implement a dedicated test script `tests/test_fail_loudly.py` that mocks the AMS-02/NOAA API to return a connection error or 404, then asserts that `fetch_ams02.py` and `fetch_noaa.py` raise a specific exception (e.g., `DataFetchError`) immediately without attempting to generate synthetic data. **Constraint**: This task is marked [X] to indicate the verification logic is implemented and the requirement is verified. **Rationale**: Explicitly validates FR-001 and the "Fail Loudly" constraint, closing the traceability loop.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Preprocess Multi-Species Cosmic Ray Flux Data (Priority: P1) 🎯 MVP

**Goal**: Download daily averaged, rigidity-binned differential flux data for protons, helium, and heavier nuclei (CNO/Fe) from AMS and align with NOAA sunspot numbers (recent solar cycles).

**Independent Test**: A script can be run that downloads the specified AMS-02 and NOAA/SWPC data, performs the time-alignment, and outputs a single CSV file containing columns for date, rigidity bin, proton flux, helium flux, iron flux, and sunspot number. The test passes if the file exists, contains no missing dates in the specified historical range (or explicitly flags gaps), and the row count matches the expected daily resolution.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for date alignment logic in `tests/test_data_alignment.py`
- [X] T010 [P] [US1] Unit test for missing data flagging (gaps > 30 days) in `tests/test_data_alignment.py`

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `code/data/fetch_ams02.py` to download daily averaged, rigidity-binned differential fluxes for protons, helium, and CNO/Fe from the public AMS repository (-2024). **Constraint**: Use `requests` with explicit error handling. **CRITICAL**: If the public API or verified mirror fails, raise an exception immediately (Fail Loudly) to prevent data fabrication. Do NOT implement any fallback to synthetic, mock, or unverified data sources. **Note**: This task includes the "Fail Loudly" logic previously associated with T041.
- [X] T012 [P] [US1] Implement `code/data/fetch_noaa.py` to download daily sunspot numbers from NOAA/SWPC (e.g., `) or verified CSV mirror.
- [X] T013 [US1] Implement `code/data/align_data.py` to merge flux and solar data, handling time zones and date formats. **Logic**: 1) Identify continuous valid blocks of data. 2) Flag any gaps > 30 days as "Data Gap" by setting flux values to `NaN` and adding a `gap_flag` column (True/False) in the output dataset. **DO NOT remove rows**; the output must maintain the continuous daily resolution row count. 3) Handle missing data points < 5 days by interpolation, but log them. **Output**: Must generate `data/processed/data_gap_report.csv` listing all flagged gap periods with start/end dates and duration. **Constraint**: The output `unified_timeseries.csv` must contain `NaN` for fluxes in gap periods, not be missing rows.
- [X] T014 [US1] Implement `code/data/preprocess.py` to calculate composition ratios: explicitly calculate **He/p** and **Fe/p**. For any row where the denominator flux (proton) is zero or missing, log the event as "Below Detection Limit" and exclude it from the ratio calculation, as required by FR-003. Ensure the output artifact explicitly lists the calculated ratios for both He/p and Fe/p species. **Note**: CNO data is retrieved but CNO/p ratios are not calculated in this scope per FR-003.
- [X] T015 [US1] Create `code/main.py` entry point to orchestrate the full data pipeline and output `data/processed/unified_timeseries.csv`. **Implementation**: 1) Parse CLI arguments using `argparse`. 2) Call `fetch_ams02.py` and `fetch_noaa.py`. 3) Call `align_data.py`. 4) Call `preprocess.py`. 5) Save `unified_timeseries.csv`. 6) Handle errors via `logging` module. 7) Exit with code 0 on success, 1 on failure.
 - **Completion Criteria**: The script must successfully generate `data/processed/unified_timeseries.csv` with the following exact columns: `date` (datetime), `rigidity_bin` (float), `proton_flux` (float), `helium_flux` (float), `iron_flux` (float), `sunspot_number` (int), `gap_flag` (boolean). The file must exist after execution. **Note**: `helium_flux` and `iron_flux` are distinct columns to support separate He/p and Fe/p analysis.
- [X] T016b [P] [US1] **Threshold Definition**: Implement `code/utils/config.py` to define a function `calculate_coverage_threshold(data_df, expected_effect_size)` that accepts the unified dataframe and a **mandatory** `expected_effect_size` parameter, returning a float. **Logic**: The function must calculate the threshold based on statistical power analysis (95% power, alpha=0.05) for the provided effect size using `statsmodels.stats.power`. **Constraint**: The `expected_effect_size` must be a parameter (no hardcoded default in logic flow) and passed from CLI or config to allow deferred definition.
- [X] T016a [US1] [US1] **Data Coverage Validation**: Implement `code/main.py` validation logic. **Pre-requisite**: T015 and T016b. **Logic**: 1) Load the raw aligned data (including NaN gaps) *before* final gap-flagging output is locked. 2) Call `config.calculate_coverage_threshold(data_df, effect_size=...)` with the loaded dataframe and a configurable effect size. 3) Calculate the percentage of days with valid data coverage (non-NaN fluxes). 4) If coverage < calculated threshold, exit with code 1 and log a critical error. If coverage >= threshold, proceed. **Constraint**: Do NOT silently relax the time-series requirement.
- [X] T049 [US1] **Gap Handling Validation**: Validate that `code/data/align_data.py` correctly flags gaps > 30 days as `NaN` and sets `gap_flag=True` in the output dataset, without removing rows. **Constraint**: This task validates the implementation of T013. **Logic**: Run the alignment script on a synthetic dataset with known gaps and verify the output maintains the original row count, has `NaN` values for fluxes in gap periods, and `gap_flag=True` for those rows. **Pre-requisite**: T013 must be complete. **Rationale**: Ensures that the "Data Gap" periods are flagged for exclusion in statistical analysis while preserving the continuous daily resolution required by the spec's test.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Composition Ratios and Correlation with Solar Activity (Priority: P2)

**Goal**: Compute composition ratios and perform time-lagged Pearson/Spearman correlation analyses against sunspot numbers (±12 months lag) per rigidity bin, including a control analysis for absolute fluxes.

**Independent Test**: The system generates a correlation matrix and a set of time-lag plots for both ratios and absolute fluxes. [UNRESOLVED-CLAIM: c_cb30acd2 — status=not_enough_info] The test passes if the output includes correlation coefficients for lags ranging from negative to positive months for both He/p and Fe/p ratios AND absolute fluxes against sunspot numbers, calculated per rigidity bin, and if the statistical significance (p-value) is calculated for each.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for lag calculation logic in `tests/test_correlation.py`
- [X] T018 [P] [US2] Unit test for rigidity-bin specific analysis in `tests/test_correlation.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/analysis/correlation.py` function `calculate_lagged_correlations` supporting Pearson and Spearman methods with a lag window spanning a range of months in integer month steps. (i.e., iterate through every integer lag value from -12, -11,..., 0,..., +11, +12).
- [X] T020a [US2] Implement `code/analysis/correlation.py` to iterate over **all rigidity bins** and perform two distinct correlation sets in a single loop: 1) **Composition Ratios**: Calculate Pearson/Spearman correlations for He/p and Fe/p against sunspot numbers. 2) **Control Analysis**: Calculate correlations for **absolute, rigidity-normalized fluxes** against sunspot numbers. **MUST**: Derive **baseline modulation amplitudes** (peak-to-trough difference from a sinusoidal fit) for the absolute fluxes in each rigidity bin. **CRITICAL**: Save all results (coefficients, p-values) to `data/processed/correlation_results.json` and `data/processed/correlation_summary.csv`. **MUST**: Save the derived baseline modulation amplitudes to `data/processed/modulation_amplitudes_baseline.csv` for use in T029 and T020b. **Output Schema**: `modulation_amplitudes_baseline.csv` must contain columns: `rigidity_bin`, `amplitude`, `method`. **Constraint**: Do NOT defer the amplitude derivation; it is required for the trend analysis in T020b.
- [X] T020b [US2] **Trend Analysis**: Implement `code/analysis/correlation.py` to load `data/processed/modulation_amplitudes_baseline.csv` (output of T020a) and perform a trend analysis (linear regression or visualization) of these baseline amplitudes against rigidity. **MUST**: Save the results (slope, intercept, R²) to `data/processed/trend_analysis.json`. **Rationale**: Explicitly fulfills FR-008 requirement to "analyze the trend of these baseline amplitudes against rigidity".
- [X] T022 [P] [US2] Implement `code/analysis/visualization.py` to generate time-lag plots and correlation heatmaps.
 - **Input Schema**: Must consume `data/processed/correlation_results.csv` (output of T020a).
 - **Pre-requisite**: T015 must be executed to ensure the pipeline has run and generated necessary intermediate artifacts if required by the full flow, but specifically T020a must have completed to generate the CSV.
 - **Output**: Generate 'Time-lag correlation plots for He/p and Fe/p' and 'Time-lag correlation plots for absolute fluxes'.
 - **Dependency**: This task MUST consume the merged results from `data/processed/correlation_results.csv` (output of T020a) to ensure both ratio and absolute flux plots are generated correctly.
- [X] T024 [US2] Validate that p-values are calculated for all correlations.
 - **Input**: `data/processed/correlation_results.csv` (output of T020a).
 - **Output**: Append a new column `is_significant` (boolean) to `data/processed/correlation_summary.csv` based on the p-value threshold.
 - **Logic**: Flag a result as significant only if the p-value of the **maximum correlation coefficient** found for that rigidity bin is < threshold (read from `config.py`, default significance level). If multiple comparisons are performed, explicitly log the correction method (e.g., Bonferroni) or state if none is applied. Do not flag every single lag point as significant without this context.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Results via Bootstrap Resampling and Model Fitting (Priority: P3)

**Goal**: Validate statistical robustness via bootstrap resampling (n=1000) and fit a rigidity-dependent diffusion model to modulation amplitudes.

**Independent Test**: The system outputs confidence intervals for the correlation coefficients derived from 1000 bootstrap iterations and generates a fitted curve for the diffusion model. The test passes if the confidence intervals are calculated and the model fitting converges within a practical compute limit.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for bootstrap resampling logic in `tests/test_bootstrap.py`
- [X] T026 [P] [US3] Unit test for diffusion model fitting convergence in `tests/test_model_fitting.py`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `code/analysis/bootstrap.py` function `run_bootstrap_resampling` with n=1000 iterations to estimate confidence intervals for max correlation coefficients. **Constraint**: Use **Moving Block Bootstrap (MBB)** with an **appropriately selected block size** to preserve temporal autocorrelation inherent in solar cycle data. Use `scipy.stats` or `numpy` vectorization to ensure this completes within the time limit on CPU-only runners. Avoid heavy parallelization overhead; use chunked processing if memory is tight.
- [X] T028 [US3] Implement `code/analysis/model_fitting.py` to derive modulation amplitudes: perform a sinusoidal fit to the time-series for each rigidity bin, calculate the **peak-to-trough difference** explicitly using the formula `max(fit) - min(fit)`, and save these intermediate values to `data/processed/modulation_amplitudes.csv`. **Constraint**: Use `scipy.optimize.curve_fit` with the function `A*sin(2*pi*t/T + phi) + C` and specific bounds for A, T, phi, C.
 - **Output Schema**: `modulation_amplitudes.csv` must contain columns: `rigidity_bin`, `amplitude`, `method` (e.g., 'sinusoidal_fit').
 - **Traceability**: This artifact is required for traceability (Constitution Principle IV) before the model fit.
- [X] T029 [US3] Implement `code/analysis/model_fitting.py` to fit a rigidity-dependent diffusion model to the amplitudes. **Input**: Load **modulation amplitudes derived from composition ratios** (He/p, Fe/p) from `data/processed/modulation_amplitudes.csv` (output of T028) for the primary hypothesis test. **Pre-requisite**: T028 must be complete. **Logic**: 1) Load the ratio-derived amplitudes. 2) Fit a rigidity-dependent diffusion model to these amplitudes using least-squares optimization (`scipy.optimize.curve_fit`). 3) **Analyze the trend** of these amplitudes against rigidity to validate the species-dependent modulation hypothesis (FR-006). **Model**: Use a simplified physics-based parameterization (e.g., `Amplitude = A / (Rigidity + B)`) to ensure convergence without GPU acceleration. **Output**: Derive the **modulation amplitude trend** against rigidity from the fitted model parameters and save to `data/processed/model_trend.json`.
- [X] T030 [US3] Calculate and report the R² value for the diffusion model fit.
 - **Constraint**: Perform an F-test (or equivalent hypothesis test) on the R² value to determine if the model explains a statistically significant portion of the variance. Read the significance threshold from `config.py` (default). Calculate the p-value and report it.
 - **Output Schema**: Save the results to `data/processed/model_fit_results.json` with keys: `r_squared`, `f_statistic`, `p_value`, `degrees_of_freedom`.
- [X] T031 [US3] Add error handling to ensure model fitting does not exceed the designated runtime limit on CPU-only runners.
- [X] T032 [US3] Generate final validation report in `data/processed/validation_report.md` summarizing bootstrap CIs and model fit quality (including the F-test result).
 - **Structure**: Must include sections for 'Bootstrap Confidence Intervals', 'Model Fit Quality', and 'F-test Results'.
- [X] T033 [US3] Calculate the width of the 95% confidence interval derived from bootstrap resampling and perform a stability check against the null hypothesis (check if the interval includes zero). **Logic**: 1) Calculate the width of the CI. 2) Calculate the stability metric as `width / abs(max_correlation_coefficient)`. 3) Save the width, stability metric, and a `stability_status` (e.g., `stable` if ratio < 0.5, `unstable` otherwise) to `data/processed/bootstrap_stability.json`. **Constraint**: This satisfies SC-003 by measuring the width against the stability of the correlation coefficient.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T051 [P] Documentation updates in `docs/` and `README.md`
- [X] T034 Code cleanup and refactoring for efficiency
- [X] T035 Performance optimization for bootstrap iterations (vectorization where possible)
- [X] T036 [P] Run `quickstart.md` validation and ensure all scripts execute without GPU
- [X] T037 Verify all data gaps > 30 days are correctly flagged and excluded from final statistical analysis
- [X] T038 [US1] **Schema Validation**: Create `tests/validate_schema.py` to assert that `data/processed/unified_timeseries.csv` includes all expected columns (date, rigidity bin, proton flux, helium flux, iron flux, sunspot number, gap_flag) and column data types are correct (date: datetime, rigidity bin: float, fluxes: float, sunspot number: int, gap_flag: boolean). **Constraint**: Script must exit with code 0 on pass, 1 on fail.
- [X] T039 [US2] Implement a rigorous collinearity diagnostic (Variance Inflation Factor) to check for multicollinearity between He/p and Fe/p ratios if used in a joint model, as noted in Assumptions. Log the VIF values.
- [X] T050 [US2] **Solar Cycle Transition Handling**: Implement logic in `code/analysis/correlation.py` to dynamically identify the Solar Cycle 24/25 transition period. **Logic**: 1) Detect the date of the minimum sunspot number using a rolling minimum window. 2) Define the 'ambiguous boundary' as the interval where the rate of change of the sunspot number is below a defined threshold, which will be determined during the implementation phase. 3) Segment the time series to analyze this boundary period separately. 4) **Perform the separate lag analysis** for this specific phase and save results to `data/processed/transition_lag_analysis.json`. 5) Log a warning if the sample size (N) for this window is < 365 days, indicating reduced statistical power. **Constraint**: Do NOT use hardcoded date ranges (e.g., '2019-2024') or fixed window sizes (e.g., '±1 year'). The boundary must be determined by data characteristics. **Rationale**: Addresses the edge case of ambiguous cycle boundaries by isolating the low-power period based on scientific data characteristics and performing the required analysis.
- [X] T042 [US3] Add a sensitivity analysis task that sweeps lag windows in {12, 15} months and additional shorter intervals to ensure the robustness of the primary ±12 month findings, as justified in Assumptions. Save sensitivity results to `data/processed/sensitivity_analysis.json`.

---

## Phase O: Data Integrity & Streaming Enhancements (MOVED TO PHASE 2)

**Purpose**: Address execution-stage feedback regarding large dataset handling and verified data source adoption. (Note: These tasks have been moved to Phase 2 to ensure linear execution flow).

- [X] T046 [US2] Verify that `code/analysis/correlation.py` correctly handles the `rigidity_bin` as a float and groups by this bin without aggregation errors. **Constraint**: Ensure the correlation loop processes each unique rigidity bin individually to satisfy FR-004.
- [X] T047 [US3] Optimize `code/analysis/bootstrap.py` to handle memory constraints during 1000 iterations. **Constraint**: If memory usage approaches a high threshold, implement a chunked bootstrap approach. where iterations are split into batches, and confidence intervals are aggregated incrementally.

---

## Phase P: Review Resolution & Robustness (New)

**Purpose**: Address specific reviewer concerns regarding statistical power, data integrity, and edge case handling that were not fully resolved in previous phases.

- [X] T054 [US2] **Statistical Power Analysis for Lag Window**: Implement a power analysis routine in `code/analysis/correlation.py` to calculate the effective degrees of freedom (EDOF) for the time-lagged correlation given the autocorrelation of the sunspot and flux time series. **Logic**: 1) Calculate the autocorrelation time scale (tau) for both the sunspot number and the flux time series. 2) Compute the EDOF as `N / (1 + 2 * sum(rho_k^2))` where `rho_k` is the autocorrelation at lag `k`. 3) Adjust the p-values for the correlation coefficients using the calculated EDOF instead of the raw sample size `N`. 4) Log the EDOF values and the adjustment method used. **Constraint**: Do NOT use the standard `scipy.stats.pearsonr` or `spearmanr` p-values directly without this adjustment, as the data is highly autocorrelated. **Rationale**: Addresses the concern that standard p-values are overly optimistic for time-series data with high autocorrelation, ensuring the reported significance is robust.
- [X] T055 [US1] **Zero-Flux Event Handling Verification**: Create a dedicated test script `tests/test_zero_flux_handling.py` that injects rows with zero flux for heavy nuclei into a mock dataset and verifies that `preprocess.py` correctly logs these as "Below Detection Limit" and excludes them from ratio calculations without causing a division-by-zero error or skewing the mean. **Constraint**: The test must assert that the output ratio for the zero-flux row is `NaN` (or explicitly excluded) and that the log contains the specific "Below Detection Limit" message. **Rationale**: Validates the robustness of the "Fail Loudly" and "Zero Flux" edge case handling defined in FR-003 and the Edge Cases section.
- [ ] T056 [US3] **Bootstrap Block Size Sensitivity**: Implement a sensitivity analysis for the Moving Block Bootstrap (MBB) block size in `code/analysis/bootstrap.py`. **Logic**: 1) Run the bootstrap resampling with block sizes of varying durations. 2) Compare the resulting 95% confidence intervals for the maximum correlation coefficient. 3) Save the comparison results to `data/processed/bootstrap_block_sensitivity.json`. **Constraint**: If the confidence intervals vary significantly (>10% width difference) across block sizes, log a warning and flag the result as "sensitive to block size". **Rationale**: Ensures that the chosen 30-day block size is not arbitrary and that the confidence intervals are stable across reasonable block size choices.
- [ ] T057 [US2] **Rigidity Bin Edge Case Handling**: Implement logic in `code/analysis/correlation.py` to handle rigidity bins with insufficient data points (e.g., < 100 days of valid data) after gap exclusion. **Logic**: 1) Count the number of valid data points per rigidity bin after gap exclusion (ignoring NaNs). 2) If a bin has < 100 points, skip the correlation analysis for that bin and log a warning with the bin ID and point count. 3) Include a column `valid_data_points` in `data/processed/correlation_summary.csv`. **Constraint**: Do NOT perform the correlation on bins with insufficient data, as the statistical power would be too low to draw meaningful conclusions. **Rationale**: Prevents spurious correlations from bins with very few data points, ensuring the robustness of the rigidity-dependent analysis. <!-- FAILED: unspecified -->
- [ ] T058 [US3] **Model Fit Convergence Diagnostics**: Enhance `code/analysis/model_fitting.py` to provide detailed diagnostics for the diffusion model fit. **Logic**: 1) Report the number of iterations required for convergence. 2) Report the condition number of the Jacobian matrix at the solution. 3) If the fit fails to converge within the maximum iterations or the condition number is high (>1e6), log a warning and save the fit parameters as `NaN` with a `convergence_status` flag in `data/processed/model_fit_results.json`. **Constraint**: Do NOT silently accept a non-converged fit as a valid result. **Rationale**: Ensures that the reported diffusion model parameters are reliable and not artifacts of a failed optimization.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes T043, T044, T006, T053 for data fetching strategy, verified source adoption, and fail-loudly verification.**
- **User Stories (Phase 3+)**: All depend on Foundational (Phase 2) completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review Resolution (Phase P)**: **NEW**. Depends on completion of Phase 3, 4, and 5 to validate the statistical robustness and edge case handling.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **T016a** depends on **T016b** and **T015**
 - **T049** depends on **T013**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
 - **T020b** depends on **T020a**
 - **T029** depends on **T028** (ratio amplitudes)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 correlation results and T028 (ratio amplitudes)

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
- Phase N tasks (T050) can be implemented in parallel with Phase 4/5 implementation as they are mostly refactoring/optimization of existing logic.
- Phase P tasks (T054-T058) can be implemented in parallel as they are validation and diagnostic tasks that depend on the completion of the core analysis logic.

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
 - Developer D: Phase N (Polish)
 - Developer E: Phase P (Review Resolution)
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
- **Constraint**: All tasks must run on CPU-only CI (no GPU, ≤7GB RAM). No heavy model training or 8-bit quantization.
- **Data Integrity**: No synthetic data generation. All inputs must come from real URLs (AMS-02, NOAA). The "Fail Loudly" mechanism (T011, T053) ensures no synthetic fallbacks are used.
- **Streaming Requirement**: T043 mandates streaming for large datasets to prevent OOM errors on the free runner using `requests` chunking ([deferred] of available RAM or 10MB).
- **Verified Source Adoption**: T044 requires adopting verified data sources if provided by the execution stage.
- **Sampling Fallback**: T045 has been removed. The pipeline must fail if full data cannot be processed.
- **Rigidity Handling**: Every flux measurement must be tied to a specific rigidity bin. No aggregation across bins before correlation analysis.
- **Gap Handling**: Gaps > 30 days must be flagged (NaN) and excluded from statistical analysis, but the output file must maintain continuous daily resolution. T013 implements flagging. T049 validates this.
- **Real Data Only**: T011 ensures that if the real data fetch fails, the process halts rather than fabricating data.
- **Sensitivity Analysis**: T042 ensures the robustness of the lag window selection.
- **Collinearity Check**: T039 addresses the potential collinearity between He/p and Fe/p ratios.
- **Transition Handling**: T050 addresses the Solar Cycle 24/25 transition ambiguity using dynamic data characteristics and explicitly performs the lag analysis.
- **Bootstrap Validity**: T027 implements Moving Block Bootstrap (MBB) to ensure valid time-series confidence intervals.
- **Control Analysis**: T020a and T020b explicitly analyze the trend of baseline amplitudes from absolute fluxes as required by FR-008.
- **Configuration**: Thresholds for coverage, p-values, and significance are read from `config.py` to ensure configurability. T016b defines the coverage threshold function with a configurable effect size.
- **Task ID Cleanup**: T041 was removed as its logic was merged into T011. T051 was created to replace the duplicate T033 in the Polish phase.
- **Review Resolution**: Phase P (T054-T058) addresses specific reviewer concerns regarding statistical power, zero-flux handling, bootstrap sensitivity, rigidity bin edge cases, and model fit diagnostics to ensure the robustness and validity of the final results.
- **Schema Correction**: `unified_timeseries.csv` now includes distinct `helium_flux` and `iron_flux` columns to support separate He/p and Fe/p analysis.
- **Log Path Correction**: Logs are written to `logs/` directory to comply with Constitution Principle III.
- **Model Fitting Correction**: T029 now fits the diffusion model to ratio-derived amplitudes (He/p, Fe/p) to validate species-dependent transport.
