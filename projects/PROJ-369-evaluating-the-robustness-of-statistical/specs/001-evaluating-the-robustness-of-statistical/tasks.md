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

- [X] T001_new [P] Create project structure by explicitly creating directories: `src/`, `src/data/`, `src/synthesis/`, `src/analysis/`, `src/viz/`, `src/utils/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `data/raw/`, `data/processed/`, `data/results/`, `specs/`, `state/`. Generate `state/structure_manifest.json` listing all created paths with content hashes (SHA-256) to verify completion and satisfy Constitution Principle V. **Output Schema**: JSON object with keys: `directories` (list of paths), `hashes` (map of path -> sha256_hash), `generated_at` (ISO8601 timestamp).
- [X] T002 [P] Initialize Python project by creating `requirements.txt` at the repository root. **Content**: Pin exact versions for: `numpy`, `pandas`, `scipy`, `statsmodels`, `arch`, `yfinance`, `requests`, `pyyaml`, `matplotlib`, `seaborn`, `xarray`, `psutil`. **Verification**: Run `pip install -r requirements.txt` and `pip freeze > requirements.lock` to verify all packages are installed and pinned.
- [X] T003 [P] Create `ruff.toml` configuration file with strict linting rules (E, F, W, I, N, C, UP) and `black` integration.
- [X] T004 [P] Create `pytest.ini` configuration file with test paths, markers, and verbosity settings.
- [X] T005 [P] Implement `src/utils/config.py` with explicit global constants: `SEED = 42` (int), `ALPHA = 0.05` (float), `NUM_NULL_PER_SERIES = 1000` (int, hardcoded constant for Constitution Principle VII compliance), `MAX_LAG = 20` (int). **Dependency**: Required by T007 and T008.
- [X] T006 [P] Implement `src/utils/logging.py` with structured logging for warnings and errors, including log file rotation. **Dependency**: Required by T007 and T008.
- [X] T007 [P] Create base data schemas in `src/data/schemas.py` using Pydantic: `TimeSeries`, `SyntheticData`, `TestResult`, `ErrorRateSummary` with all required fields defined in the spec.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 [P] Implement `src/data/ingestion.py` with strict URL validation and checksumming logic (FR-001). **Note**: This task provides the core ingestion functions; T014 and T048 use these functions.
- [X] T014 [US1] Implement `src/data/ingestion.py` to download multiple distinct public datasets from authorized sources. **Constraint**: Must fail loudly on download error; no synthetic fallbacks. **Size Check**: BEFORE downloading, estimate total size of all datasets. If estimated total > 7GB, raise `ValueError` with message "Total dataset size exceeds 7GB RAM limit. Aborting." to enforce Spec FR-001. **URLs**:
 1. NOAA Global Summary (URL: `) - Verified direct CSV
 2. Yahoo Finance (yfinance package for AAPL, SPY)
 3. UK National Grid Load (URL: `https://www.nationalgrideso.com/document/174276/download`) - Verified direct CSV
 4. NOAA Station USW00014833 (URL: `)
 5. NOAA Station USW00014895 (URL: `)
 **Note**: Ensure all 5 URLs are distinct and valid. **Dependency**: T048.
- [X] T015 [US1] Implement linear interpolation for missing values in `src/data/preprocessing.py` (FR-002). **Dependency**: T014 (Download). **Note**: Must run BEFORE T009a execution (T018a/T009a) to ensure valid input for ADF.
- [X] T009a [US1] Implement `src/data/preprocessing.py` with FULL implementation of ADF logic and linear regression residuals for detrending. **Constraint**: Per Spec FR-002, perform ADF; if p < 0.05, difference data and repeat until p >= 0.05; if p >= 0.05, fit linear regression y = mx + c, calculate residuals (y - (mx + c)), and use residuals as the processed series. **Output**: `src/data/preprocessing.py` with working functions for `process_series(series)` returning processed data and metadata (stationarity_status, differencing_count, detrending_status). **Note**: This task defines the functions. T015 is the execution task for real data.
- [X] T009b [US1/US2] Implement `src/data/metrics.py` utility functions to compute ACF (up to a sufficient lag), Hurst exponent (via DFA), and Spectral Density peak ratio for **ALL processed series (Real AND Synthetic)**. **Function Signatures**: `compute_acf(series: pd.Series, max_lag: int=20) -> np.ndarray`, `compute_hurst(series: pd.Series) -> float`, `compute_spectral_peak_ratio(series: pd.Series) -> float`. **Output**: `src/data/metrics.py` with these functions. **Dependency**: T009a (Preprocessing). **Note**: This task provides the functions. T010_real and T010_shuffled are the execution tasks.
- [X] T018a [US1] Add logic to resample **ONLY** the UK National Grid Load dataset to a **consistent frequency (hourly)** before stationarity testing (US1-AC3). **Rule**: Resample ONLY UK Grid to hourly. NOAA and Yahoo data are processed at their native frequency. **Output**: Write to `data/processed/resampled_{source}.csv` for UK Grid; native frequency for others. **Dependency**: T015 (Missing Value Fill). **Note**: Resampling must occur BEFORE stationarity testing (T009a execution).
- [X] T019a [US1/US2] [P] Implement shuffling (permutation) logic in `src/data/preprocessing.py` to generate and store **NUM_NULL_PER_SERIES (1000)** shuffled versions for **every real time series** to create a null distribution. (FR-003, Constitution Principle VII). **Constraint**: Must run even if metric calculation (T010_real) fails; output to `data/processed/null_distributions/real/`. **Implementation**: Loop exactly `NUM_NULL_PER_SERIES` (1000) times as mandated by Constitution Principle VII. The value 1000 is derived from Constitution Principle VII and the Plan's "Scale/Scope" requirement for a "sufficient number" of null distributions. **File Naming**: If `NUM_NULL_PER_SERIES` <= 100, output individual files `series_id_shuffle_001.csv` to `series_id_shuffle_{NUM}.csv`. If `NUM_NULL_PER_SERIES` > 100, output a single consolidated CSV file `series_id_shuffles.csv` with a `shuffle_id` column to avoid file system overhead. **Dependency**: T009a (Preprocessing). **Config**: Read `NUM_NULL_PER_SERIES` from `src/utils/config.py` (default 1000) for the loop count and file naming logic.
- [X] T019b [US2] [P] Implement shuffling logic in `src/synthesis/generators.py` to generate and store **NUM_NULL_PER_SERIES (1000)** shuffled versions for **every synthetic series** to create a null distribution (FR-003, Constitution Principle VII). **Constraint**: Must run even if metric calculation (T010_real) fails; output to `data/processed/null_distributions/synthetic/`. **Implementation**: Loop exactly `NUM_NULL_PER_SERIES` (1000) times as mandated by Constitution Principle VII. The value 1000 is derived from Constitution Principle VII and the Plan's "Scale/Scope" requirement for a "sufficient number" of null distributions. **File Naming**: If `NUM_NULL_PER_SERIES` <= 100, output individual files `series_id_shuffle_001.csv` to `series_id_shuffle_{NUM}.csv`. If `NUM_NULL_PER_SERIES` > 100, output a single consolidated CSV file `series_id_shuffles.csv` with a `shuffle_id` column. **Dependency**: T026 (Synthetic Generation), T032 (Verify Synthetic Ground Truth). **Config**: Read `NUM_NULL_PER_SERIES` from `src/utils/config.py` (default 1000) for the loop count and file naming logic.
- [X] T019c [P] [Gate] Verify existence and count of shuffled files. in `data/processed/null_distributions/real/` and `data/processed/null_distributions/synthetic/`. **Output**: Write `data/results/null_distribution_gate.json` with status "PASS" if counts match `NUM_NULL_PER_SERIES` (1000) per series. **Dependency**: T019a, T019b.
- [X] T010_real [US1/US2] Execute metric computation for all real datasets using T009b functions. **Algorithm**: Iterate over all CSV files in `data/processed/` matching pattern `*_processed.csv`. For each file, load data, compute ACF, Hurst, and Spectral Density Peak Ratio. If Spectral Density fails (ValueError or NaN), compute fallback metric `1/variance` and log warning. Store results in `data/processed/metrics.json`. **Dependency**: T009a, T009b, T018a. **Output Schema**: JSON list of objects with keys: `source`, `length`, `hurst`, `acf_vector`, `spectral_peak_ratio`, `is_shuffled` (boolean=false), `spectral_density_fallback` (optional).
- [X] T010_shuffled [US1/US2] Compute ACF (up to a selected lag), Hurst, and Spectral Density peak ratio for **ALL shuffled versions** (to verify US2-AC5) and store in `data/processed/metrics.json`. **Input**: Reads from `data/processed/null_distributions/*/*.csv` (shuffled) after T019a/b. **Dependency**: T019a, T019b. **Output Schema**: JSON list of objects with keys: `source`, `length`, `hurst`, `acf_vector` (list of floats, lags 0-20), `spectral_peak_ratio`, `is_shuffled` (boolean). **Constraint**: Must run AFTER T019a/b completes. **Algorithm**: Spectral Density Peak Ratio = (max peak in low-freq band) / (mean floor in high-freq band).
- [X] T030 [US2] [P] Read metrics from T010_real output (data/processed/metrics.json); verify ACF, Hurst, and spectral density **peak ratio** are computed (FR-002). **Dependency**: T010_real.
- [X] T048 [US1] Implement data validation logic in `src/data/ingestion.py` to validate downloaded file size > 0 bytes and point count >= 25 before saving to `data/raw/`. Raise `ValueError` on failure. **Dependency**: T001_new.
- [X] T020 [US1] Add edge case handling: skip datasets < 25 points with a warning log (Edge Case 1). **Log Format**: `WARNING: Skipping dataset {id}: length < 25`.
- [X] T021 [US1] Add edge case handling: detect unit roots that cannot be detrended and log the differencing count (Edge Case). **Log Format**: `WARNING: Dataset {id} required {count} differences to achieve stationarity`.
- [X] T022 [US1] Add edge case handling: fallback to variance-based metric if spectral density **peak ratio** calculation fails due to numerical instability (Edge Case: numerical instability). **Constraint**: Must write the fallback value to `metrics.json` under key `spectral_density_fallback`. **Algorithm**: If `compute_spectral_peak_ratio` raises ValueError or returns NaN, calculate `fallback_metric = 1.0 / series.variance()` and use this value. **Log Format**: `WARNING: Spectral density failed for {id}, using variance-based fallback (1/variance)`. **Dependency**: T009b (Metrics).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest diverse public time series, handle missing values, ensure stationarity (ADF/differencing or linear regression detrending), and compute initial metrics.

**Independent Test**: Can be fully tested by running the data ingestion and preprocessing module against a fixed set of public URLs and verifying that the output is a clean, stationary (or differenced), linear-regression-detrended time series with no missing values and a documented preprocessing path.

### Implementation for User Story 1

- [X] T011 [P] [US1] Unit test for `src/data/ingestion.py` verifying checksums and error on missing files in `tests/unit/test_ingestion.py`. **Test Cases**: `test_ingestion_handles_missing_checksum`, `test_ingestion_validates_url`.
- [X] T012 [P] [US1] Unit test for `src/data/preprocessing.py` verifying ADF logic, differencing loops, and linear regression detrending in `tests/unit/test_preprocessing.py`.
- [X] T013 [P] [US1] Integration test for full NOAA/Yahoo/UK Grid pipeline in `tests/integration/test_data_pipeline.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synthetic Ground-Truth Generation and Autocorrelation Quantification (Priority: P2)

**Goal**: Generate synthetic fGn/ARFIMA data with known H and mean=0, compute metrics, and create shuffled null distributions.

**Independent Test**: Can be fully tested by generating a synthetic fGn series with H=0.8 and mean=0, verifying that the generated series has H ≈ 0.8 (within 0.05) and mean ≈ 0 (within 0.01), and confirming that the shuffled versions exhibit an average ACF lag statistically indistinguishable from zero.

### Tests for User Story 2

- [X] T023 [P] [US2] Unit test for `src/synthesis/generators.py` verifying H=0.5, 0.7, 0.8, 0.9 generation accuracy in `tests/unit/test_synthesis.py`. **Test Cases**: `test_fgn_generation_accuracy`, `test_arima_generation_accuracy`.
- [X] T024 [P] [US2] Unit test for shuffling logic ensuring ACF lag-1 is zero in `tests/unit/test_synthesis.py`.
- [X] T025 [P] [US2] Baseline validity test: Run [deferred] trials on H=0.5 data and verify rejection rate is within the Clopper-Pearson confidence interval of the nominal significance level in `tests/integration/test_baseline_validity.py`.

### Implementation for User Story 2

- [X] T026 [US2] Implement `src/synthesis/generators.py` to generate fractional Gaussian noise (fGn) or ARFIMA processes with Hurst exponents in the set `{0.5, 0.7, 0.8, 0.9}` and mean=0 (FR-007). **Constraint**: Must use `arch` or `statsmodels` for ARFIMA generation. **Dependency**: T001_new.
- [X] T027 [US2] Implement logic to generate synthetic series with varying lengths for the N-variation grid spanning short to long time horizons. (Plan). **Output Schema**: `synthetic_grid.csv` with columns: `hurst`, `length`, `file_path`, `seed`. **Logic**: Map (H, length) pairs to unique file paths. **Sample Sizes**: Must include exactly: [a range of values spanning from low to high], [a moderate quantity], 5000, 10000. The specific values are chosen to satisfy the Spec's ≥1000 requirement and the Plan's 'N-variation' goal while remaining within the 6-hour runtime budget. **Constraint**: Do NOT generate series with length < 1000. **Dependency**: T026.
- [X] T029 [US2] 🛑 **GATE**: Implement `src/synthesis/validation.py` to run the **[deferred]-trial** baseline check on H=0.5 data **before proceeding** to Hurst analysis (FR-008, US2-AC7). **GATE**: This task must write `data/results/baseline_status.json` with a "PASS" status if the rejection rate is within the Clopper-Pearson CI. **Output Schema**: JSON with keys: `status`, `rejection_rate`, `ci_lower`, `ci_upper`. **Implementation**: Run [deferred] one-sample t-tests on H=0.5 synthetic data (mean=0). Calculate observed rejection rate. Use `statsmodels.stats.proportion.proportion_confint` to calculate Clopper-Pearson binomial confidence interval at a standard confidence level. If rejection rate is within the confidence interval of the nominal significance level, set status "PASS". **Dependency**: T026, T019b. **BLOCKING DEPENDENCY**: Phase 5a tasks (T037a_runner) MUST NOT start until this file exists with "PASS". **Note**: Real data metrics (T010_real) are not required for this gate.
- [X] T031 [US2] Implement calculation of theoretical VIF and N_eff for synthetic series in `src/synthesis/generators.py` (FR-007). **Note**: Use the approximation `VIF_theoretical ≈ N^(α), where α is a scaling exponent determined by the Hurst parameter H.` for long-memory processes.
- [X] T032 [US2] **Verify Synthetic Ground Truth**: Add logic to verify generated series mean is within 0.01 of 0 and Hurst is within 0.05 of target (US2-AC1..4). **Constraint**: For synthetic data, verify using the **known input parameters** (H, mean=0) provided to the generator, NOT by re-estimating Hurst. This ensures the ground truth is preserved. **Output**: Log verification status for each generated series. **Dependency**: T026, T027.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5a: User Story 3 - Hypothesis Testing & Regression Implementation (Priority: P3)

**Goal**: Apply t-tests/F-tests, calculate Type I error rates, and implement regression logic.

**Independent Test**: Can be fully tested by running the analysis on synthetic data with H=0.5 (independent-like) and verifying the error rate is within the sufficiently large-trial Clopper-Pearson binomial confidence interval at a standard significance level.

### Tests for User Story 3

- [X] T033 [P] [US3] Unit test for `src/analysis/hypothesis_tests.py` verifying one-sample t-test and F-test logic in `tests/unit/test_hypothesis.py`. **Test Cases**: `test_ttest_logic`, `test_ftest_logic`.
- [X] T034 [P] [US3] Unit test for `src/analysis/regression.py` verifying VIF and N_eff calculation in `tests/unit/test_regression.py`. **Test Cases**: `test_vif_calculation`, `test_n_eff_calculation`.
- [X] T035 [P] [US3] Integration test for full Monte Carlo loop (multiple trials) and regression output in `tests/integration/test_pipeline.py`. **Test Cases**: `test_monte_carlo_orchestration`, `test_regression_output`.

### Implementation for User Story 3 (Tests)

- [X] T036 [US3] Implement `src/analysis/hypothesis_tests.py` to apply one-sample t-tests and F-tests to synthetic series (mean=0) (FR-004). **Constraint**: Explicitly exclude two-sample t-test logic from the codebase. **Dependency**: T019c.
- [X] T037_profile [US3] Implement profiling and optimization of the Monte Carlo loop to ensure it meets the runtime constraint (SC-004). **Output**: Write `data/results/profile_report.json` with estimated runtime. **Dependency**: T036.
- [X] T037 [US3] Implement Monte Carlo loop orchestration to run **[deferred] trials** (or until Clopper-Pearson CI width < 0.01) per configuration (distinct from T029's baseline) to ensure statistical robustness (H, N) and calculate observed rejection rate at α=0.05 (US3-AC1). **Dependency**: Requires T036. **Dependency**: Requires T029 (Baseline Gate) to pass. **Note**: A sufficient number of trials balances robustness with the runtime constraint.
- [X] T038 [US3] Implement logic to compare observed test statistics against the null distribution from shuffled versions (generated in T019a/T019b) to isolate inflation (US3-AC5). **Dependency**: T019c, T010_shuffled.

### Implementation for User Story 3 (Regression Logic)

- [X] T037b [US3] Implement explicit feature filtering logic in `src/analysis/regression.py` to **exclude** Max_ACF_Lag and spectral density metrics from the input features. **Dependency**: T037 (Monte Carlo loop completion). **Output**: Write filtered feature list to `data/results/filtered_features.json`. **Implementation**: Define `allowed_features = ['hurst', 'log_n_eff']`. Filter input dataframe to include only these columns.
- [X] T037a_impl [US3] Implement **Non-Linear Regression** (e.g., Polynomial Regression or GLM with log-link) model code in `src/analysis/regression.py` to regress error rate vs. Hurst exponent (synthetic) or estimated Hurst (real). **Implementation**: Use `statsmodels` GLM or Polynomial features. **Constraint**: Must use **Non-Linear Regression** as explicitly required by Plan's Technical Context to validate the VIF mechanism, while satisfying Spec FR-005's requirement for regression analysis. **Mandatory Step**: Calculate Variance Inflation Factor (VIF) as a diagnostic for multicollinearity AND calculate the theoretical VIF (VIF_theoretical ≈ N^(2H-1)) from the Hurst exponent to validate the mechanism. **Output**: Save regression coefficients, VIF, N_eff, and `slope_per_01_unit` to `data/results/regression_model.json`. **Output Schema**: JSON with keys: `slope`, `intercept`, `p_value`, `vif`, `n_eff`, `r_squared`, `slope_per_01_unit`. **Logic**: Calculate `slope_per__unit` = `slope` * 0.1 to satisfy SC-002. **Explicit Step**: Calculate `slope_per__unit` as the change in error rate per 0.1 unit increase in Hurst exponent and record it in the output. **Dependency**: T037b (filtered features), T037 (error rates).
- [X] T037c [US3] **REMOVED**: VIF/N_eff calculation merged into T037a_impl.

**Checkpoint**: Hypothesis testing and regression logic are ready; Analysis phase blocked by T029 Gate.

---

## Phase 5b: User Story 3 - Regression Execution & Visualization (Priority: P3)

**Goal**: Execute regression and generate visualizations.

**Dependency**: This phase is BLOCKED until T029 (Baseline Gate) passes.

### Implementation for User Story 3 (Execution & Viz)

- [X] T037a_runner [US3] Execute the Non-Linear Regression model (T037a_impl) using inputs from T037 (error_rates.csv), T037b (filtered_features.json), and T029 (Gate). **Validation**: Before execution, verify `data/results/baseline_status.json` exists and contains `status: PASS`. If not, log critical error and exit. Also verify `error_rates.csv` and `filtered_features.json` have matching dataset IDs and no NaN/Inf values in Hurst or error rate columns. Log critical error and exit if mismatches found. **Dependency**: T037a_impl, T037, T037b, T029. **Note**: This is a CLI entry point script to run the regression. **Explicit Gate Check**: This task MUST verify T029 output file exists and has status "PASS" before proceeding.
- [X] T052 [US2] **Validate Synthetic Mean**: Add a post-generation assertion in `src/synthesis/generators.py` (T032) that checks the mean of the generated series is approximately zero (within 0.01 of 0) and raises an error if the deviation exceeds 0.01. **Rationale**: Strengthens the ground-truth guarantee required for accurate Type I error measurement per Spec US2-AC1.
- [X] T053 [US3] **Document Exclusion of Two-Sample T-Test**: Add a prominent comment and a runtime log message in `src/analysis/hypothesis_tests.py` (T036) explicitly stating that the two-sample t-test is excluded per Spec FR-004 and explaining the reason (invalid for detrended residuals with long-range dependence). **Rationale**: Ensures transparency and prevents accidental re-introduction of the excluded test.
- [X] T039 [US3] Implement visualization logic in `src/viz/plots.py` for ACF plots, scatter plots (rejection rate vs. H), and QQ-plots (FR-006).
- [X] T039b [US3] Implement visualization logic in `src/viz/plots.py` specifically for **VIF curves** (FR-006).
- [X] T040 [US3] Implement performance validation and runtime enforcement: Measure and log total pipeline runtime to ensure it fits within the GitHub Actions time limit (SC-004). **Logic**: If runtime > 6h, exit with code 1. **Output**: Write results to `data/results/performance_validation.json`. **Output Schema**: JSON with keys: `total_runtime_seconds`, `peak_memory_mb`, `dataset_count`, `status`. **Unit**: Runtime measured in seconds. **Implementation**: Use `psutil` for memory measurement. **Success Condition**: If runtime <= 6h, set `status: PASS`. If > 6h, set `status: FAIL` and exit.
- [X] T041 [US3] Implement output of results to `data/results/final_summary.json` including regression slopes, p-values, VIF, N_eff, and error rates. **Schema**: Must be a single JSON file with defined keys for all metrics (US3-AC2, US3-AC3).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042 [P] Documentation updates: Generate `quickstart.md` and update `README.md` with pipeline usage instructions
- [X] T043 Code cleanup and refactoring for memory efficiency (ensure < 7 GB RAM usage; **Constraint**: No streaming/sampling fallback logic allowed per FR-001).
- [X] T044 Performance optimization: Vectorize Monte Carlo loops where possible to meet runtime efficiency goals.
- [X] T045 [P] Run full contract test suite in `tests/contract/` to verify schema compliance
- [X] T046 Security hardening: Verify no API keys are hardcoded; ensure `.env` usage for any secrets
- [X] T047 Run quickstart.md validation to ensure end-to-end reproducibility
- [X] T050 [US3] **Verify Regression Implementation**: Implement verification logic in `tests/contract/test_schemas.py` to verify `src/analysis/regression.py` and `data/results/filtered_features.json` exist and contain the expected keys and values. **Dependency**: T037b, T037a_impl. **Rationale**: Ensures the regression implementation meets the spec requirements for feature exclusion and output schema.

## Phase O: Revision & Analysis Resolution (New)

**Purpose**: Address specific reviewer concerns from analysis phase regarding data integrity and task dependencies.

- [ ] T054 [US1/US2] **Resolve Data Source Ambiguity**: Explicitly define and implement a `src/data/sources.py` module that maps dataset names (e.g., "NOAA_GSWD", "UK_GRID") to their exact, verified URLs and expected file formats. **Constraint**: This module must be the SINGLE source of truth for all download tasks (T014) to prevent URL drift. **Output**: A Python dictionary in `src/data/sources.py` with keys `dataset_name`, `url`, `expected_format`, `checksum_url`. **Rationale**: Addresses review concern about hard-coded URLs in task descriptions; centralizes source management for maintainability and verification per Spec FR-001 (Verified Sources) and Constitution Principle II (Verified Accuracy).
- [ ] T055 [US1/US2] **Resolve Data Flow Dependency Gap**: Insert an explicit synchronization task between T014 (Download) and T015 (Preprocessing) to verify that ALL required datasets are present in `data/raw/` before any preprocessing begins. **Implementation**: Create `src/data/validator.py` with a function `verify_raw_datasets(required_datasets: List[str])` that checks file existence and size > 0. If any are missing, raise `FileNotFoundError` with a detailed list of missing files. **Dependency**: Must run AFTER T014 and BEFORE T015. **Rationale**: Addresses review concern about task ordering; ensures data availability before processing starts to prevent partial pipeline execution per Constitution Principle I (Reproducibility) and the 'Producer before Consumer' rule.
- [X] T056 [US3] **Resolve Regression Predictor Constraint**: Add a unit test in `tests/unit/test_regression.py` specifically verifying that `Max_ACF_Lag1` and `spectral_density_peak_ratio` are NOT present in the input features passed to the OLS model. **Test Case**: `test_regression_excludes_forbidden_predictors`. **Implementation**: Mock the input dataframe with these columns and assert that the regression function raises a `ValueError` or explicitly filters them out before model fitting. **Rationale**: Addresses review concern about spec compliance; ensures the regression model strictly adheres to Spec FR-005 by excluding forbidden predictors.
- [ ] T057 [US2] **Resolve Synthetic Data Verification Gap**: Implement a `src/synthesis/verification.py` module that performs a rigorous statistical check on generated synthetic data. **Requirements**: For each generated series, compute the mean and standard deviation, and perform a Kolmogorov-Smirnov test against the theoretical distribution (if available) or verify that the empirical Hurst exponent (via DFA) is within 0.05 of the target. **Output**: Write a verification report to `data/results/synthetic_verification.json` with status "PASS" only if all checks pass. **Dependency**: Must run AFTER T026 (Generation) and BEFORE T029 (Baseline Gate). **Rationale**: Addresses review concern about ground-truth validity; ensures synthetic data meets Spec US2-AC1..4 requirements before being used in hypothesis testing.