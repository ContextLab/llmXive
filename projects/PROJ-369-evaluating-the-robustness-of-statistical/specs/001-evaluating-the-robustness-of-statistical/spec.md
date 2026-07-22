# Feature Specification: Evaluating Robustness of Statistical Methods to Non-Independence

**Feature Branch**: `001-evaluating-robustness-of-statistical-methods-to-non-independence`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Evaluating the Robustness of Statistical Methods to Non-Independence in Publicly Available Time Series"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system MUST successfully ingest 5–8 diverse public time series datasets (NOAA, Yahoo Finance, UCI), handle missing values via linear interpolation, and detrend the data using linear regression residuals to isolate stochastic components.

**Why this priority**: Without clean, standardized input data, no statistical analysis can proceed. This is the foundational step that enables all subsequent hypothesis testing and error rate calculations.

**Independent Test**: Can be fully tested by running the data ingestion module against a fixed set of public URLs and verifying that the output is a clean, detrended time series with no missing values and a documented trend removal.

**Acceptance Scenarios**:

1. **Given** a raw NOAA weather CSV with [deferred] missing values, **When** the preprocessing pipeline executes, **Then** the output series has 0 missing values (filled via interpolation) and the trend component is removed.
2. **Given** a Yahoo Finance price series with a clear upward trend, **When** the detrending step runs, **Then** the residuals have a mean close to zero and no significant linear trend remains (p-value > 0.10 for trend slope).
3. **Given** a UCI energy dataset with irregular timestamps, **When** the pipeline processes it, **Then** the data is resampled to a consistent frequency (e.g., daily) before detrending.

---

### User Story 2 - Autocorrelation Quantification and Null Distribution Generation (Priority: P2)

The system MUST compute the Autocorrelation Function (ACF) up to a sufficient lag., estimate the Hurst exponent, and calculate the spectral density peak ratio for each series. It must also generate [deferred] shuffled versions of each series to establish a baseline null distribution for type I error.

**Why this priority**: This step quantifies the "degree of long-range dependence" (the predictor variable) and creates the ground truth (shuffled data) against which the standard tests will be compared. It is essential for measuring error inflation.

**Independent Test**: Can be fully tested by processing a single synthetic AR(1) series with known autocorrelation and verifying that the computed Hurst exponent and ACF match theoretical expectations, and that the shuffled series shows no autocorrelation.

**Acceptance Scenarios**:

1. **Given** a synthetic time series with strong positive autocorrelation (Hurst exponent > 0.7), **When** the quantification module runs, **Then** the estimated Hurst exponent is within 0.1 of the theoretical value.
2. **Given** a processed time series, **When** the shuffling module executes [deferred] iterations, **Then** the resulting set of [deferred] series exhibits an average ACF lag-1 close to zero (|r| < 0.05).
3. **Given** a noisy financial time series, **When** the spectral density is calculated, **Then** the peak ratio metric correctly identifies the dominant frequency component relative to the noise floor.

---

### User Story 3 - Hypothesis Testing and Error Rate Analysis (Priority: P3)

The system MUST apply one-sample t-tests, two-sample t-tests, and F-tests to the original (unadjusted) series and the shuffled null series, then calculate the observed type I error rate at α=0.05. Finally, it must regress these error rates against the quantified autocorrelation metrics.

**Why this priority**: This is the core research output: measuring the discrepancy between nominal and actual error rates. It directly answers the research question about robustness.

**Independent Test**: Can be fully tested by running the analysis on a dataset known to be independent (shuffled) and verifying the error rate is ~0.05, then running it on a highly autocorrelated dataset and verifying the error rate > 0.05.

**Acceptance Scenarios**:

1. **Given** a set of [deferred] shuffled series (independent), **When** a one-sample t-test is applied [deferred] times, **Then** the observed rejection rate is between 0.04 and 0.06 (approximating α=0.05).
2. **Given** a set of highly autocorrelated series (Hurst > 0.8), **When** standard t-tests are applied without adjustment, **Then** the observed rejection rate is significantly higher than 0.05 (e.g., > 0.15).
3. **Given** the results of 8 datasets, **When** the regression analysis runs, **Then** a positive correlation is found between the Hurst exponent and the observed type I error rate (slope > 0).

---

### Edge Cases

- What happens when a downloaded dataset is shorter than the required lag for ACF calculation (e.g., < 25 points)? The system must skip that dataset and log a warning.
- How does the system handle a time series with a unit root (non-stationary) that cannot be detrended by simple linear regression? The system must detect the unit root (ADF test) and either difference the data or exclude the series, logging the action.
- What happens if the spectral density estimation fails due to numerical instability? The system must fall back to a simpler variance-based metric and log the failure.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and cache at least 5 distinct public time series datasets from NOAA, Yahoo Finance, and UCI Repository, ensuring the total dataset size fits within 7 GB RAM. (See US-1)
- **FR-002**: System MUST compute the Autocorrelation Function (ACF) up to a sufficient lag, the Hurst exponent, and the spectral density peak ratio for every loaded series. (See US-2)
- **FR-003**: System MUST generate a sufficient number of shuffled (permuted) versions of each time series to establish a baseline null distribution for type I error rates. (See US-2)
- **FR-004**: System MUST apply standard one-sample t-tests, two-sample t-tests, and F-tests to the original series and calculate the observed rejection rate at α=0.05. (See US-3)
- **FR-005**: System MUST perform a linear regression of the observed type I error rate against the Hurst exponent and max ACF lag-1 coefficient to quantify the relationship. (See US-3)
- **FR-006**: System MUST output visualizations including ACF plots, scatter plots of rejection rate vs. autocorrelation, and QQ-plots of test statistics. (See US-3)

### Key Entities

- **TimeSeries**: Represents a single dataset with attributes: `source`, `length`, `autocorrelation_metrics` (Hurst, ACF_max), `raw_values`, `detrended_values`.
- **TestResult**: Represents the outcome of a hypothesis test with attributes: `test_type` (t-test, F-test), `p_value`, `rejection` (boolean), `dataset_id`.
- **ErrorRateSummary**: Aggregates results for a dataset with attributes: `dataset_id`, `nominal_alpha`, `observed_error_rate`, `shuffled_error_rate`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The observed type I error rate for standard tests on shuffled (independent) data is measured against the nominal significance level (α=0.05) to verify the baseline validity of the testing framework. (See US-3)
- **SC-002**: The relationship between the Hurst exponent and the observed type I error inflation is measured against the theoretical expectation that higher dependence leads to higher error rates. (See US-3)
- **SC-003**: The magnitude of error inflation (observed rate minus nominal rate) is measured across multiple datasets to quantify the practical impact of non-independence. (See US-3)
- **SC-004**: The computational runtime of the full pipeline (ingestion, quantification, numerous tests, regression) is measured against the 6-hour limit for a single GitHub Actions free-tier job.. (See US-1, US-2, US-3)

## Assumptions

- The public datasets (NOAA, Yahoo Finance, UCI) are accessible via standard HTTP requests without requiring authentication or API keys that might expire during the CI run.
- The "long-range dependence" in the selected datasets is sufficient to cause measurable type I error inflation; if all datasets are effectively white noise, the study will yield a null result (which is still valid but limits the scope of the conclusion).
- The `scipy` and `statsmodels` libraries available in the default Python environment on GitHub Actions are sufficient for all statistical calculations (ACF, Hurst, t-tests, F-tests) without requiring heavy external dependencies or GPU acceleration.
- The time series lengths in the selected public datasets are sufficient (≥ 100 points) to reliably estimate the Hurst exponent and ACF up to lag 20.
- The "shuffling" method (random permutation) is an appropriate method for breaking temporal dependence to create a valid null hypothesis for this specific study design.
