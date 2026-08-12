# Tasks: Evaluating Robustness of Statistical Methods to Non-Independence

**Input**: Design documents from `/specs/001-evaluating-the-robustness-of-statistical-methods-to-non-independence/`
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

- [ ] T001 Create project structure by explicitly creating directories: `src/`, `src/data/`, `src/synthesis/`, `src/analysis/`, `src/viz/`, `src/utils/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `data/raw/`, `data/processed/`, `data/results/`, `specs/`, `state/`. **Output**: Generate `state/structure_manifest.json` listing all created paths to verify completion.
- [X] T002 Initialize Python project with pinned `requirements.txt` (numpy, pandas, scipy, statsmodels, arch, yfinance, requests, pyyaml, matplotlib, seaborn, xarray)
- [X] T003 [P] Create `ruff.toml` configuration file with strict linting rules (E, F, W, I, N, C, UP) and `black` integration.
- [X] T004 [P] Create `pytest.ini` configuration file with test paths, markers, and verbosity settings.
- [X] T005 [P] Implement `src/utils/config.py` for random seed management and global constants. **Dependency**: Required by T007 and T008.
- [X] T006 [P] Implement `src/utils/logging.py` with structured logging for warnings and errors, including log file rotation. **Dependency**: Required by T007 and T008.
- [X] T007 Create base data schemas in `src/data/schemas.py` using Pydantic: `TimeSeries`, `SyntheticData`, `TestResult`, `ErrorRateSummary` with all required fields defined in the spec.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Implement `src/data/ingestion.py` with strict URL validation and checksumming logic (FR-001)
- [X] T009 [US1] Implement `src/data/preprocessing.py` with FULL implementation of ADF logic AND linear regression residuals for detrending. **Constraint**: Spec FR-002 mandates linear regression residuals for stationary series; DO NOT use DFA. **Implementation Detail**: 1) Implement ADF loop: run ADF; if p < 0.05, difference data and repeat until p >= 0.05; 2) Implement Detrending: if p >= 0.05, fit linear regression y = mx + c to the series, calculate residuals (y - (mx + c)), and use residuals as the processed series. **Output**: `src/data/preprocessing.py` with working functions for `process_series(series)` returning processed data and metadata (stationarity_status, differencing_count, detrending_status).
- [X] T010 [P] Implement `src/data/metrics.py` utility functions (ACF, Hurst, Spectral Density) to be called by T010a and T010b. **Note**: This task provides the functions, not the execution flow.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest diverse public time series, handle missing values, ensure stationarity (ADF/differencing or detrending), and compute initial metrics.

**Independent Test**: Can be fully tested by running the data ingestion and preprocessing module against a fixed set of public URLs and verifying that the output is a clean, stationary (or differenced), detrended time series with no missing values and a documented preprocessing path.

### Tests for User Story 1

- [X] T011 [P] [US1] Unit test for `src/data/ingestion.py` verifying checksums and error on missing files in `tests/unit/test_ingestion.py`. **Test Cases**: `test_ingestion_handles_missing_checksum`, `test_ingestion_validates_url`.
- [X] T012 [P] [US1] Unit test for `src/data/preprocessing.py` verifying ADF logic and differencing loops in `tests/unit/test_preprocessing.py`
- [X] T013 [P] [US1] Integration test for full NOAA/Yahoo/UK Grid pipeline in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement `src/data/ingestion.py` to download multiple distinct public datasets from authorized sources.:
 1. NOAA Global Summary (URL: `)
 2. Yahoo Finance (yfinance package for AAPL/SPY)
 3. UK National Grid Load (URL: `https://www.nationalgrideso.com/document/174276/download`)
 4. NOAA Station USW00014895 (URL: `)
 5. NOAA Station USW00014833 (URL: `)
 **Constraint**: Must fail loudly on download error; no synthetic fallbacks.
- [X] T015 [US1] Implement linear interpolation for missing values in `src/data/preprocessing.py` (FR-002).
- [X] T016 [US1] **Refine** `src/data/preprocessing.py` logic to explicitly call the ADF loop and linear regression residuals logic implemented in T009. **Constraint**: Explicitly exclude DFA for detrending; use linear regression residuals only. **Dependency**: T009.
- [X] T018a [US1] Add logic to resample datasets to a **consistent frequency (e.g., hourly, daily) based on the dataset's native resolution** before stationarity testing (US1-AC3). **Rule**: Detect native frequency by calculating median time delta between rows; resample to hourly if native frequency < 1h, else daily. **Output**: Write to `data/processed/resampled_{source}.csv`.
- [X] T010a [US1] Compute ACF, Hurst, and Spectral Density **peak ratio** for **REAL series only** (post-preprocessing) and store in `data/processed/metrics_real.json`. **Input**: Reads from `data/processed/resampled_*.csv` after T018a. **Dependency**: T018a. **Output Schema**: JSON list of objects with keys: `source`, `length`, `hurst`, `acf_max_lag1`, `acf_max_lag20`, `spectral_peak_ratio`. **Constraint**: Must run BEFORE T019a to ensure metrics exist before shuffling. **Algorithm**: Spectral Density Peak Ratio = (max peak in low-freq band) / (mean floor in high-freq band).
- [X] T019a [US1] Implement shuffling (permutation) logic in `src/data/preprocessing.py` to generate and store **multiple shuffled versions** for **every real time series** to create a null distribution (FR-003, Constitution Principle VII). **Constraint**: Must run after T010a; output to `data/processed/null_distributions/real/`.
- [X] T020 [US1] Add edge case handling: skip datasets < 25 points with a warning log (Edge Case 1). **Log Format**: `WARNING: Skipping dataset {id}: length < 25`.
- [X] T021 [US1] Add edge case handling: detect unit roots that cannot be detrended and log the differencing count (Edge Case). **Log Format**: `WARNING: Dataset {id} required {count} differences to achieve stationarity`.
- [X] T022 [US1] Add edge case handling: fallback to variance-based metric if spectral density **peak ratio** calculation fails due to numerical instability (Edge Case: numerical instability). **Log Format**: `WARNING: Spectral density failed for {id}, using variance-based fallback`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synthetic Ground-Truth Generation and Autocorrelation Quantification (Priority: P2)

**Goal**: Generate synthetic fGn/ARFIMA data with known H and mean=0, compute metrics, and create shuffled null distributions.

**Independent Test**: Can be fully tested by generating a synthetic fGn series with H=0.8 and mean=0, verifying that the generated series has H ≈ 0.8 (within 0.05) and mean ≈ 0 (within 0.01), and confirming that the shuffled versions exhibit an average ACF lag statistically indistinguishable from zero.

### Tests for User Story 2

- [X] T023 [P] [US2] Unit test for `src/synthesis/generators.py` verifying H=0.5, 0.7, 0.8, 0.9 generation accuracy in `tests/unit/test_synthesis.py`. **Test Cases**: `test_fgn_generation_accuracy`, `test_arima_generation_accuracy`.
- [X] T024 [P] [US2] Unit test for shuffling logic ensuring ACF lag-1 is zero in `tests/unit/test_synthesis.py`
- [X] T025 [P] [US2] Baseline validity test: Run [deferred] trials on H=0.5 data and verify rejection rate is within 95% Clopper-Pearson CI of 0.05 in `tests/integration/test_baseline_validity.py`

### Implementation for User Story 2

- [X] T026 [US2] Implement `src/synthesis/generators.py` to generate fractional Gaussian noise (fGn) or ARFIMA processes with H ∈ {0.5, 0.7, 0.8, 0.9} and mean=0 (FR-007).
- [X] T027 [US2] Implement logic to generate synthetic series with varying lengths for the N-variation grid: a range from small to large scales (Plan). **Output**: Write to `data/processed/synthetic_grid.csv` with columns: `hurst`, `length`, `file_path`.
- [X] T010b [US2] Compute ACF, Hurst, and Spectral Density **peak ratio** for **SYNTHETIC series only** and store in `data/processed/metrics_synthetic.json`. **Input**: Reads from `data/processed/` after T026. **Dependency**: T026. **Output Schema**: JSON list of objects with keys: `source`, `length`, `hurst`, `acf_max_lag1`, `acf_max_lag20`, `spectral_peak_ratio`. **Constraint**: Must run after T026. **Algorithm**: Spectral Density Peak Ratio = (max peak in low-freq band) / (mean floor in high-freq band).
- [X] T019b [US2] Implement shuffling logic in `src/synthesis/generators.py` to generate and store **a sufficient number of shuffled versions** for **every synthetic series** to create a null distribution (FR-003, Constitution Principle VII). **Constraint**: Must run after T010b; output to `data/processed/null_distributions/synthetic/`.
- [X] T029 [US2] Implement `src/synthesis/validation.py` to run the **[deferred]-trial** baseline check on H=0.5 data **before proceeding** to Hurst analysis (FR-008, US2-AC7). **GATE**: This task must write `data/results/baseline_status.json` with a "PASS" status if the rejection rate is within the Clopper-Pearson CI. **Output Schema**: JSON with keys: `status`, `rejection_rate`, `ci_lower`, `ci_upper`. Phase tasks (T037a) MUST NOT start until this file exists with "PASS".
- [X] T030 [US2] [P] Read metrics from T010b output for synthetic series; verify ACF, Hurst, and spectral density **peak ratio** are computed (FR-002).
- [X] T031 [US2] Implement calculation of theoretical VIF and N_eff for synthetic series in `src/synthesis/generators.py` (FR-007).
- [X] T032 [US2] Add logic to verify generated series mean is within 0.01 of 0 and H is within 0.05 of target (US2-AC1..4).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5a: User Story 3 - Hypothesis Testing (Priority: P3)

**Goal**: Apply t-tests/F-tests and calculate Type I error rates.

**Independent Test**: Can be fully tested by running the analysis on synthetic data with H=0.5 (independent-like) and verifying the error rate is within the [deferred]-trial Clopper-Pearson binomial confidence interval of 0.05.

### Tests for User Story 3

- [X] T033 [P] [US3] Unit test for `src/analysis/hypothesis_tests.py` verifying one-sample t-test and F-test logic in `tests/unit/test_hypothesis.py`. **Test Cases**: `test_ttest_logic`, `test_ftest_logic`.
- [X] T034 [P] [US3] Unit test for `src/analysis/regression.py` verifying VIF and N_eff calculation in `tests/unit/test_regression.py`. **Test Cases**: `test_vif_calculation`, `test_n_eff_calculation`.
- [X] T035 [P] [US3] Integration test for full Monte Carlo loop (multiple trials) and regression output in `tests/integration/test_pipeline.py`. **Test Cases**: `test_monte_carlo_orchestration`, `test_regression_output`.

### Implementation for User Story 3 (Tests)

- [X] T036 [US3] Implement `src/analysis/hypothesis_tests.py` to apply one-sample t-tests and F-tests to synthetic series (mean=0) (FR-004). **Constraint**: Explicitly exclude two-sample t-test.
- [X] T037 [US3] Implement Monte Carlo loop orchestration to run a sufficient number of trials per configuration to ensure statistical robustness (H, N) and calculate observed rejection rate at α=0.05 (US3-AC1). **Dependency**: Requires T036. **Dependency**: Requires T029 (Baseline Gate) to pass.
- [X] T038 [US3] Implement logic to compare observed test statistics against the null distribution from shuffled versions (generated in T019a/T019b) to isolate inflation (US3-AC5).

**Checkpoint**: Hypothesis testing logic is ready; Analysis phase blocked by T029 Gate.

---

## Phase 5b: User Story 3 - Regression & Analysis (Priority: P3)

**Goal**: Perform regression analysis and visualizations.

**Dependency**: This phase is BLOCKED until T029 (Baseline Gate) passes.

### Implementation for User Story 3 (Analysis)

- [X] T037b [US3] Implement explicit feature filtering logic in `src/analysis/regression.py` to **exclude** Max_ACF_Lag and spectral density metrics from the input features. **Output**: Write filtered feature list to `data/results/filtered_features.json`.
- [X] T037a [US3] Implement **Linear Regression** model in `src/analysis/regression.py` to regress error rate vs. Hurst exponent (synthetic) or estimated Hurst (real). **Input**: Read error rates from `data/results/error_rates.csv` and filtered features from `data/results/filtered_features.json`. **Dependency**: Requires T029 (Gate) and T037b (Filtering). **Constraint**: Must wait for T029 (Gate) and T037b (Filtering). **Note**: Spec FR-005 mandates Linear Regression. **Mandated by FR-005: Use Linear Regression (not GLM or non-linear)**. **Output**: Save regression coefficients and VIF/N_eff to `data/results/regression_model.json`. **Output Schema**: JSON with keys: `slope`, `intercept`, `p_value`, `vif`, `n_eff`, `r_squared`, `slope_per_01_unit`. **Logic**: Calculate `slope_per_01_unit` = `slope` * 0.1 to satisfy SC-002.
- [X] T037c [US3] Implement calculation of Variance Inflation Factor (VIF) and Effective Sample Size (N_eff) in the regression model (FR-005).
- [X] T039 [US3] Implement visualization logic in `src/viz/plots.py` for ACF plots, scatter plots (rejection rate vs. H), and QQ-plots (FR-006).
- [X] T039b [US3] Implement visualization logic in `src/viz/plots.py` specifically for **VIF curves** (FR-006).
- [X] T040 [US3] Implement performance validation and runtime enforcement: Measure and log total pipeline runtime to ensure it fits within the GitHub Actions time limit (SC-004). **Logic**: If runtime > 6h, exit with code 1. **Output**: Write results to `data/results/performance_validation.json`. **Output Schema**: JSON with keys: `total_runtime_seconds`, `peak_memory_mb`, `dataset_count`, `status`. **Unit**: Runtime measured in seconds.
- [X] T041 [US3] Implement output of results to `data/results/final_summary.json` including regression slopes, p-values, VIF, N_eff, and error rates. **Schema**: Must be a single JSON file with defined keys for all metrics (US3-AC2, US3-AC3).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042 [P] Documentation updates: Generate `quickstart.md` and update `README.md` with pipeline usage instructions
- [X] T043 Code cleanup and refactoring for memory efficiency (ensure < 7 GB RAM usage)
- [X] T044 Performance optimization: Vectorize Monte Carlo loops where possible to meet h runtime goal
- [X] T045 [P] Run full contract test suite in `tests/contract/` to verify schema compliance
- [X] T046 Security hardening: Verify no API keys are hardcoded; ensure `.env` usage for any secrets
- [X] T047 Run quickstart.md validation to ensure end-to-end reproducibility

---

## Phase O: Review Resolution & Final Validation (Revision Pass)

**Goal**: Address specific reviewer concerns regarding data flow, metric definitions, and edge case handling identified in the latest analysis.

- [ ] T048 [US1] **Fix Data Flow**: Ensure `src/data/ingestion.py` explicitly validates that the downloaded file size is > 0 bytes and contains at least 25 data points before saving to `data/raw/`. If validation fails, raise a `ValueError` immediately to prevent downstream processing of empty/invalid files. **Rationale**: Addresses reviewer concern that edge case T020 (skip < 25 points) might be triggered too late if ingestion saves a truncated file.
- [ ] T049 [US2] **Clarify Shuffling Logic**: Update `src/synthesis/generators.py` and `src/data/preprocessing.py` to explicitly document the number of shuffled versions generated per series in a configuration constant `NUM_NULL_PER_SERIES` (default 1000). Ensure this constant is used consistently in both real and synthetic shuffling tasks (T019a, T019b). **Rationale**: Addresses reviewer concern that the "sufficient number" of shuffled versions was ambiguous.
- [ ] T050 [US3] **Verify Regression Inputs**: Add a pre-computation check in `src/analysis/regression.py` (before T037a runs) that verifies the input `error_rates.csv` and `filtered_features.json` have matching dataset IDs and that no `NaN` or `Inf` values exist in the Hurst or error rate columns. Log a critical error and exit if mismatches are found. **Rationale**: Prevents silent regression failures due to misaligned data frames.
- [ ] T051 [US1] **Enhance Spectral Density Fallback**: Refine T022 logic to explicitly calculate the variance of the residuals as the fallback metric and store it in a separate field `variance_fallback` in `metrics_real.json` if the peak ratio calculation fails. **Rationale**: Ensures that even when the primary metric fails, a valid statistical measure is recorded for debugging and potential alternative analysis.
- [ ] T052 [US2] **Validate Synthetic Mean**: Add a post-generation assertion in `src/synthesis/generators.py` (T032) that checks the mean of the generated series is exactly 0 (within floating point tolerance) and raises an error if the deviation exceeds 0.01. **Rationale**: Strengthens the ground-truth guarantee required for accurate Type I error measurement.
- [ ] T053 [US3] **Document Exclusion of Two-Sample T-Test**: Add a prominent comment and a runtime log message in `src/analysis/hypothesis_tests.py` (T036) explicitly stating that the two-sample t-test is excluded per Spec FR-004 and explaining the reason (invalid for detrended residuals with long-range dependence). **Rationale**: Ensures transparency and prevents accidental re-introduction of the excluded test.
