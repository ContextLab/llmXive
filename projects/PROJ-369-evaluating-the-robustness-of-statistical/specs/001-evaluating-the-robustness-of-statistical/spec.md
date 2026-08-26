# Feature Specification: Evaluating Robustness of Statistical Methods to Non-Independence

**Feature Branch**: `001-evaluating-the-robustness-of-statistical-methods-to-non-independence`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Evaluating the Robustness of Statistical Methods to Non-Independence in Publicly Available Time Series"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system MUST successfully ingest multiple diverse public continuous time series datasets (NOAA, Yahoo Finance, UK National Grid Load), handle missing values via linear interpolation, and preprocess the data to isolate stochastic components. The system MUST first perform an Augmented Dickey-Fuller (ADF) test. If the ADF test indicates a unit root (p < 0.05), the system MUST difference the data until stationarity is achieved. If the series is stationary (ADF p ≥ 0.05), the system MUST then detrend the data using linear regression residuals. This ensures that observed error inflation is due to long-range dependence, not residual non-stationarity.

**Why this priority**: Without clean, standardized, and stationary input data, no statistical analysis can proceed. This is the foundational step that enables all subsequent hypothesis testing and error rate calculations.

**Independent Test**: Can be fully tested by running the data ingestion and preprocessing module against a fixed set of public URLs and verifying that the output is a clean, stationary (or differenced), detrended time series with no missing values and a documented preprocessing path (ADF result, differencing count, or detrending status).

**Acceptance Scenarios**:

1. **Given** a raw NOAA weather CSV with missing values (≥ 100 points), **When** the preprocessing pipeline executes, **Then** the output series has 0 missing values (filled via interpolation) and the series is either differenced (if ADF p < 0.05) or detrended (if ADF p ≥ 0.05).
2. **Given** a Yahoo Finance price series with a clear unit root, **When** the ADF test runs, **Then** the system detects the unit root (p < 0.05) and applies differencing, resulting in a stationary series (ADF p ≥ 0.05).
3. **Given** a UK National Grid Load dataset, **When** the pipeline processes it, **Then** the data is resampled to a consistent frequency (e.g., hourly) before stationarity testing and preprocessing.

---

### User Story 2 - Synthetic Ground-Truth Generation and Autocorrelation Quantification (Priority: P2)

The system MUST generate synthetic time series with known ground-truth parameters (mean=0, known autocorrelation structure) to serve as the primary validation target. Specifically, it MUST generate fractional Gaussian noise (fGn) or ARFIMA processes with Hurst exponents in the set {0.5, 0.7, 0.8, 0.9} and lengths ≥ 1,000 points. Additionally, the system MUST compute the Autocorrelation Function (ACF) up to a sufficient lag to capture relevant temporal dependencies, the Hurst exponent, and the spectral density peak ratio for every synthetic and real series to quantify the degree of dependence. To demonstrate the effect of breaking dependence, the system MUST generate [deferred] shuffled (permuted) versions of each series. These shuffled versions serve to create a specific null distribution for comparison against the observed test statistics on the original series, isolating the inflation caused by autocorrelation as required by Constitution Principle VII. The system MUST verify the baseline validity of the testing framework by confirming the observed rejection rate on H=0.5 synthetic data matches the nominal alpha (0.05) within a 95% Clopper-Pearson binomial confidence interval for 10,000 trials before proceeding to the Hurst analysis.

**Why this priority**: This step creates the essential "ground truth" (synthetic data with known mean=0 and known autocorrelation) required to measure Type I error inflation accurately. It also quantifies the "degree of long-range dependence" (the predictor variable). The shuffling is a mandatory step to create a null distribution for comparison, ensuring the isolation of inflation caused by dependence.

**Independent Test**: Can be fully tested by generating a synthetic fGn series with H=0.8 and mean=0, verifying that the generated series has H ≈ 0.8 (within 0.05) and mean ≈ 0 (within 0.01), and confirming that the [deferred] shuffled versions exhibit an average ACF lag-1 statistically indistinguishable from zero (p > 0.05 for a t-test of the mean ACF lag-1 against 0).

**Acceptance Scenarios**:

1. **Given** a request to generate synthetic data with H=0.5, **When** the generator runs, **Then** the output series has an estimated Hurst exponent within 0.05 of 0.5 and a mean within 0.01 of 0.
2. **Given** a request to generate synthetic data with H=0.7, **When** the generator runs, **Then** the output series has an estimated Hurst exponent within 0.05 of 0.7 and a mean within 0.01 of 0.
3. **Given** a request to generate synthetic data with H=0.8, **When** the generator runs, **Then** the output series has an estimated Hurst exponent within 0.05 of 0.8 and a mean within 0.01 of 0.
4. **Given** a request to generate synthetic data with H=0.9, **When** the generator runs, **Then** the output series has an estimated Hurst exponent within 0.05 of 0.9 and a mean within 0.01 of 0.
5. **Given** a processed time series, **When** the shuffling module executes [deferred] iterations, **Then** the resulting set of [deferred] series exhibits an average ACF lag-1 statistically indistinguishable from zero (p > 0.05 for a t-test of the mean ACF lag-1 against 0), and the system constructs a null distribution from these values to compare against the observed test statistic of the original series.
6. **Given** a noisy financial time series, **When** the spectral density is calculated, **Then** the peak ratio metric correctly identifies the dominant frequency component relative to the noise floor.
7. **Given** a set of 10,000 synthetic null trials (H=0.5, mean=0), **When** a one-sample t-test is applied, **Then** the observed rejection rate is within the [deferred] Clopper-Pearson binomial confidence interval of the nominal 0.05 rate.

---

### User Story 3 - Hypothesis Testing and Error Rate Analysis (Priority: P3)

The system MUST apply one-sample t-tests and F-tests to the synthetic (ground-truth) series and calculate the observed Type I error rate at α=0.05. The system MUST perform a sufficient number of Monte Carlo trials for each configuration to ensure statistical stability. The two-sample t-test is explicitly excluded from the analysis as it is invalid for detrended residuals with long-range dependence. Finally, the system must regress these error rates against the true Hurst exponent (for synthetic data) or the estimated Hurst exponent (for real data) to quantify the relationship. The regression model MUST calculate the Variance Inflation Factor (VIF) and Effective Sample Size (N_eff) to validate the mechanism of failure. The Max_ACF_Lag1 and spectral density metrics are for descriptive quantification ONLY and MUST NOT be used as predictors in the regression model. For real data, the system MUST compare the observed test statistics against the null distribution created from the [deferred] shuffled versions to isolate the inflation caused by non-independence.

**Why this priority**: This is the core research output: measuring the discrepancy between nominal and actual error rates against the known ground truth. It directly answers the research question about robustness.

**Independent Test**: Can be fully tested by running the analysis on synthetic data with H=0.5 (independent-like) and verifying the error rate is within the [deferred] Clopper-Pearson binomial confidence interval of 0.05, then running on H=0.9 data and reporting the regression slope and p-value.

**Acceptance Scenarios**:

1. **Given** a set of 10,000 synthetic null trials (H=0.5, mean=0), **When** a one-sample t-test is applied, **Then** the observed rejection rate is within the [deferred] Clopper-Pearson binomial confidence interval of the nominal 0.05 rate.
2. **Given** a set of highly autocorrelated synthetic series (H > 0.8, mean=0), **When** standard t-tests are applied without adjustment, **Then** the regression of rejection rate vs. Hurst exponent is performed, and the system reports the slope, p-value, VIF, and N_eff. A valid result includes both positive and null correlations.
3. **Given** the results of 8 datasets, **When** the regression analysis runs, **Then** a regression of rejection rate vs. estimated Hurst exponent is performed, and the system reports the slope, p-value, VIF, and N_eff. A valid result includes both positive and null correlations.
4. **Given** the synthetic data, **When** the regression analysis runs, **Then** the system confirms that Max_ACF_Lag1 is NOT used as a predictor in the model.
5. **Given** a real-world time series, **When** the analysis runs, **Then** the observed test statistic is compared against the null distribution generated from [deferred] shuffled versions of that series to isolate the inflation caused by non-independence.

---

### Edge Cases

- What happens when a downloaded dataset is shorter than the required lag for ACF calculation (e.g., < 25 points)? The system must skip that dataset and log a warning.
- How does the system handle a time series with a unit root (non-stationary) that cannot be detrended by simple linear regression? The system must detect the unit root (ADF test) and difference the data until stationarity is achieved, logging the action.
- What happens if the spectral density estimation fails due to numerical instability? The system must fall back to a simpler variance-based metric and log the failure.
- Why is the two-sample t-test excluded? The two-sample t-test is excluded from the analysis because applying it to detrended residuals with long-range dependence violates the independence assumption, leading to inflated Type I error that cannot be attributed solely to the intended long-range dependence metric.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and cache at least 5 distinct public continuous time series datasets from NOAA, Yahoo Finance, and UK National Grid Load, ensuring the total dataset size fits within 7 GB RAM. (See US-1)
- **FR-002**: System MUST perform an Augmented Dickey-Fuller (ADF) test on every loaded series. If the ADF test indicates a unit root (p < 0.05), the system MUST difference the data until stationarity is achieved. If the series is stationary (ADF p ≥ 0.05), the system MUST detrend the data using linear regression residuals. The system MUST also compute the Autocorrelation Function (ACF) up to a sufficient lag, the Hurst exponent, and the spectral density peak ratio for every loaded series. (See US-1)
- **FR-003**: System MUST generate [deferred] shuffled (permuted) versions of each time series to create a specific null distribution for comparison against the observed test statistics on the original series. These versions are used to isolate the inflation caused by non-independence as required by Constitution Principle VII. (See US-2)
- **FR-004**: System MUST apply standard one-sample t-tests and F-tests to the synthetic ground-truth series (mean=0) and calculate the observed rejection rate at α=0.05. The system MUST explicitly exclude the two-sample t-test from the analysis. (See US-3)
- **FR-005**: System MUST perform a linear regression of the observed type I error rate against the true Hurst exponent (for synthetic data) or the estimated Hurst exponent (for real data). The regression model MUST calculate the Variance Inflation Factor (VIF) and Effective Sample Size (N_eff) to validate the mechanism of failure. The Max_ACF_Lag1 and spectral density metrics MUST NOT be used as predictors in this regression model. (See US-3)
- **FR-006**: System MUST output visualizations including ACF plots, scatter plots of rejection rate vs. Hurst exponent, and QQ-plots of test statistics. (See US-3)
- **FR-007**: System MUST generate synthetic time series using fractional Gaussian noise (fGn) or ARFIMA models with known mean=0 and Hurst exponents in the set {0.5, 0.7, 0.8, 0.9} to serve as the primary ground-truth validation target. The system MUST also calculate the theoretical Variance Inflation Factor (VIF) and Effective Sample Size (N_eff) for these synthetic series to serve as the ground-truth mechanism for the regression analysis. (See US-2)
- **FR-008**: System MUST verify the baseline validity of the testing framework by confirming the observed rejection rate on H=0.5 synthetic data matches the nominal alpha (0.05) within the 95% Clopper-Pearson binomial confidence interval for 10,000 trials before proceeding to the Hurst analysis. (See US-2)

### Key Entities

- **TimeSeries**: Represents a single dataset with attributes: `source`, `length`, `autocorrelation_metrics` (Hurst, ACF_max), `raw_values`, `processed_values`, `stationarity_status` (ADF p-value, differencing count).
- **SyntheticData**: Represents a generated series with attributes: `model_type` (fGn, ARFIMA), `Hurst`, `mean`, `length`, `values`, `theoretical_VIF`, `theoretical_N_eff`.
- **TestResult**: Represents the outcome of a hypothesis test with attributes: `test_type` (t-test, F-test), `p_value`, `rejection` (boolean), `dataset_id`.
- **ErrorRateSummary**: Aggregates results for a dataset with attributes: `dataset_id`, `nominal_alpha`, `observed_error_rate`, `shuffled_null_distribution`, `regression_slope`, `regression_p_value`, `VIF`, `N_eff`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The observed type I error rate for standard tests on synthetic data (H=0.5, mean=0) is measured against the nominal significance level (α=0.05) to verify the baseline validity of the testing framework. (See US-3)
- **SC-002**: The relationship between the Hurst exponent and the observed type I error inflation is measured against the theoretical expectation that higher dependence leads to higher error rates. The slope of the regression line is measured, and its statistical significance (p < 0.05) is reported. The magnitude of the slope is reported as the change in error rate per unit increase in Hurst exponent. (See US-3)
- **SC-003**: The magnitude of error inflation (observed rate minus nominal rate) is measured across multiple datasets to quantify the practical impact of non-independence. (See US-3)
- **SC-004**: The computational runtime of the full pipeline (ingestion, quantification, numerous tests, regression) is measured against the 6-hour limit for a single GitHub Actions free-tier job. The full pipeline must complete in ≤ 6 hours on a standard GitHub Actions runner. (See US-1, US-2, US-3)

## Assumptions

- The public datasets (NOAA, Yahoo Finance, UK National Grid Load) are accessible via standard HTTP requests without requiring authentication or API keys that might expire during the CI run.
- The "long-range dependence" in the selected datasets is sufficient to cause measurable type I error inflation; if all datasets are effectively white noise, the study will yield a null result (which is still valid but limits the scope of the conclusion).
- The `scipy`, `statsmodels`, and `numpy` libraries available in the default Python environment on GitHub Actions are sufficient for all statistical calculations (ACF, Hurst, fGn/ARFIMA generation, t-tests, F-tests, ADF, differencing) without requiring heavy external dependencies or GPU acceleration.
- The time series lengths in the selected public datasets are sufficient (≥ 100 points) to reliably estimate the Hurst exponent and ACF up to lag 20.
- The "shuffling" method (random permutation) is an appropriate method for breaking temporal dependence to create a null distribution, and the comparison of observed statistics against this null distribution is a valid method for isolating the inflation caused by non-independence.