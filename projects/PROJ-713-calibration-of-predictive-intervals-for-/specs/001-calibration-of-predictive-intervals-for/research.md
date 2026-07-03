# Research: Calibration of Predictive Intervals for Time‑Series Forecasts

## 1. Research Question & Hypotheses

**Primary Question**: Do standard off-the-shelf time-series forecasting models (ARIMA, Prophet, LSTM) produce predictive intervals that are empirically calibrated (i.e., does the empirical coverage match the nominal level) on standard benchmarks (M4, UCI Electricity)?

**Hypotheses**:
- **H0**: The empirical coverage of 0.80 and 0.95 predictive intervals does not significantly differ from the nominal levels across models.
- **H1**: There is a statistically significant deviation from nominal coverage, indicating miscalibration.
- **H2**: Post-hoc conformal prediction adjustment significantly improves calibration metrics (coverage and CRPS) compared to baseline models.

## 2. Dataset Strategy

The study relies on two standard time-series benchmarks. Per the project constraints, we utilize verified sources.

| Dataset | Description | Verified Source / Loader | Variables Required | Fit Check |
| :--- | :--- | :--- | :--- | :--- |
| **M4** | [deferred]+ univariate time series (Hourly, Daily, Weekly, Monthly, Yearly). | **Not in verified list**. *Action*: The spec assumes `wget` access. Since no verified URL is provided in the input block, the implementation will **fail immediately** with a descriptive error code (FR-007) if the canonical source is unreachable. | `timestamp`, `value` | **Critical**: M4 structure is known to contain `timestamp` and `value`. If the specific file format from the canonical source differs, the pipeline will raise `FR-007` error. |
| **UCI Electricity** | Multivariate time series of electricity consumption (hourly, multiple series). | **Not in verified list**. *Action*: Similar to M4, the spec assumes access. We will attempt to load via `ucimlrepo` or direct download. **If not found in verified list, the pipeline fails immediately**. | `timestamp`, `value` (per series) | **Critical**: Must handle multivariate nature by iterating series. **No substitution** with UCI HAR is permitted as it fundamentally changes the statistical properties (sensor vs. economic data) and invalidates the research question. |

**Decision**: Given the strict rule "Cite ONLY the URLs listed in the '# Verified datasets' block", and the absence of M4/UCI-Electricity specific URLs in that block:
1.  **M4**: The plan will attempt to download from the canonical source (as per spec assumption). If unreachable, the pipeline **HALTS** with error code `DATA_MISSING_M4`.
2.  **UCI Electricity**: If not found in the verified list, the pipeline **HALTS** with error code `DATA_MISSING_ELEC`.
3.  **No Substitution**: The plan explicitly **rejects** the UCI HAR substitution. Using HAR sensor data to answer a question about M4/Electricity benchmarks is a methodological failure. The pipeline must fail rather than produce invalid results.

**Dataset-Variable Fit Confirmation**:
- **M4 (if available)**: Contains `timestamp` and `value`. **Fit**: Yes.
- **UCI Electricity (if available)**: Contains `timestamp` and `value`. **Fit**: Yes.
- **Other Verified Datasets**: Ignored for primary benchmark.

## 3. Methodology

### 3.1 Data Preprocessing & Splitting
1.  **Three-Way Split**: To prevent data leakage in conformal calibration, each series is split from the **original data** as follows:
 - **[deferred]**: Model Fitting (Training)
 - **[deferred]**: Conformal Calibration (Distinct, held-out from training)
 - **[deferred]**: Final Test (Hold-out)
    *Note: This replaces the 80/20 split to ensure the calibration set is disjoint from the model fitting data.*
2. **Standardization**: Z-score normalization (zero mean, unit variance) on the **[deferred] Training** set; applied to Calibration and Test sets.
3.  **Handling Edge Cases**:
    -   Zero variance series: Skip with warning log.
    -   Missing values: Forward fill (max 1 step) or drop if >5% missing.

### 3.2 Model Training & Interval Generation
1.  **ARIMA**: `statsmodels.tsa.arima.model.ARIMA`. Order selection via AIC (auto).
    -   **CDF Construction**: Assumes Gaussian residuals. $CDF(y) = \Phi(\frac{y - \mu}{\sigma})$.
    -   Intervals via `get_forecast().conf_int()`.
2.  **Prophet**: `prophet.Prophet`.
    -   **CDF Construction**: Uses `uncertainty_samples=1000` to simulate residual distribution. Empirical CDF constructed from simulated samples.
    -   Intervals via `uncertainty_samples` combined with explicit residual simulation.
3.  **LSTM**:
    -   Architecture: 1 Input, 1 Hidden (32 units, ReLU), 1 Output.
    -   Training: Max 50 epochs, Early Stopping (patience=5), CPU-only.
    -   **Diagnostic**: Run **Shapiro-Wilk test** on training residuals.
        -   **If Gaussian (p >= 0.05)**: Use Gaussian residual assumption ($CDF(y) = \Phi(\frac{y - \hat{y}}{\hat{\sigma}})$).
        -   **If Non-Gaussian (p < 0.05)**: Switch to **Empirical CDF** (quantile-based) for interval generation and PIT calculation. This ensures intervals are not miscalibrated due to wrong distributional assumptions.
    -   **Diagnostic**: Run Shapiro-Wilk test on training residuals. If non-Gaussian (p < 0.05), switch to **Empirical CDF** (quantile-based) for PIT calculation.

### 3.3 Metrics
1.  **Empirical Coverage**: Count of test points falling within $[L, U]$ divided by total test points.
2.  **PIT (Probability Integral Transform)**:
    -   Calculate $u = F(y_{true})$ where $F$ is the model's CDF.
    -   **Uniformity Test**: **Kolmogorov-Smirnov (KS) test** against Uniform(0,1) distribution. (Replaces Ljung-Box, which tests autocorrelation, not uniformity).
    -   Report p-value.
3.  **CRPS**: `properscoring.crps_ensemble`. Measures sharpness and calibration.

### 3.4 Statistical Significance
- **Paired Bootstrap**: Resample **entire series** with replacement [deferred] times.
    -   **Critical Constraint**: **No resampling of time points or residuals within a series** is performed. This preserves the internal temporal dependence of each series.
    -   Compute difference in coverage/CRPS for each resample.
    -   Calculate p-value for difference $\neq 0$.
-   **Power Warning**: If the number of available series is low (< 50), the power to detect small calibration differences is limited. This will be reported in results.

### 3.5 Conformal Prediction
-   **Method**: Self-Calibrating Conformal Prediction (SCCP).
-   **Procedure**:
 1. Use the **[deferred] Calibration Set** (distinct from training) to compute non-conformity scores.
    2.  Adjust prediction intervals to achieve target coverage.
 3. Evaluate on the **[deferred] Test Set**.
- **Leakage Prevention**: The calibration set is strictly disjoint from the model fitting set ([deferred]) and the test set ([deferred]).

## 4. Compute Feasibility Analysis

-   **Hardware**: GitHub Actions Free (CPU, 7 GB RAM).
-   **Memory**:
    -   M4: Processed series-by-series. Peak RAM < 1 GB.
    -   UCI Electricity: Processed series-by-series. Peak RAM < 1 GB.
    -   LSTM: Small model (32 units). Batch size 32.
-   **Time**:
    -   ARIMA/Prophet: Fast (<1 min per series).
    -   LSTM: ~minutes per series (50 epochs).
    -   Total: With M4 (100k series), we will **sample** 500 series (stratified by frequency) to stay within 6h limit. UCI Electricity can be processed fully or sampled.
-   **GPU**: None. All models run on CPU.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Unavailability** | High | M4/UCI-Elec not in verified list. **Mitigation**: Pipeline halts with specific error code (FR-007). No substitution. |
| **LSTM Instability** | Medium | NaN/Inf intervals. **Mitigation**: Fallback to Gaussian residuals; retry with lower LR; max a limited number of attempts. |
| **Timeout (>6h)** | High | **Mitigation**: Limit M4 to 500 series. Strict sequential processing with progress bar. |
| **Memory Overflow** | High | **Mitigation**: Streaming loader. No full dataset load. |
| **Non-Gaussian Residuals** | Medium | **Mitigation**: Shapiro-Wilk diagnostic. Switch to Empirical CDF for PIT if non-Gaussian. |