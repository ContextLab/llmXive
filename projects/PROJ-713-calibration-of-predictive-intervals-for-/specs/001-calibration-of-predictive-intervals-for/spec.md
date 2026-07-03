# Feature Specification: Calibration of Predictive Intervals for Time‑Series Forecasts

**Feature Branch**: `001-calibration-of-predictive-intervals`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "Calibration of Predictive Intervals for Time‑Series Forecasts"

## User Scenarios & Testing

### User Story 1 - Empirical Coverage Assessment on Standard Benchmarks (Priority: P1)

The researcher must be able to load the M4 and UCI Electricity datasets, split them into the first [deferred] of observations as the training window and the final [deferred] as the hold-out test window, fit ARIMA, Prophet, and a lightweight LSTM model (trained for max 50 epochs or until early stopping with patience=5), and compute the empirical coverage of their 0.80 and 0.95 predictive intervals against the actual test values.

**Why this priority**: This is the core research question. Without establishing whether current methods achieve nominal coverage, no further analysis of calibration quality or post-hoc correction is possible. It defines the baseline performance of off-the-shelf methods.

**Independent Test**: The system can be tested by running the analysis pipeline on a single series from the M4 dataset and verifying that the script outputs a coverage deviation table showing the difference between nominal (e.g., 0.95) and empirical coverage.

**Acceptance Scenarios**:

1. **Given** the M4 dataset is downloaded and pre-processed, **When** the ARIMA, Prophet, and LSTM models are fitted and intervals generated, **Then** the system outputs a table showing empirical coverage rates for 0.80 and 0.95 nominal levels for each model.
2. **Given** the UCI Electricity dataset is loaded, **When** the analysis is run, **Then** the system correctly handles the multivariate nature of the data by processing individual series or aggregated load profiles and reports coverage metrics.

### User Story 2 - Distributional Calibration via PIT and CRPS (Priority: P2)

The researcher must be able to generate Probability Integral Transform (PIT) histograms for the forecast errors and calculate the Continuous Ranked Probability Score (CRPS) to assess the sharpness and reliability of the predictive distributions beyond simple coverage. The PIT analysis must explicitly validate the distributional shape (e.g., detecting heavy tails) independent of the interval width construction method.

**Why this priority**: While coverage (US-1) checks if the interval is "wide enough," PIT and CRPS (US-2) assess the *shape* and *quality* of the entire predictive distribution. This provides a more granular view of calibration (e.g., detecting if intervals are too wide on one side and too narrow on the other).

**Independent Test**: The system can be tested by generating a PIT histogram for a single model on a single series and verifying that the histogram is approximately uniform if the model is well-calibrated, or skewed if mis-calibrated.

**Acceptance Scenarios**:

1. **Given** a set of forecasts and observations, **When** the Probability Integral Transform is calculated, **Then** the system generates a histogram of PIT values and performs a Ljung-Box test against a uniform distribution (accounting for autocorrelation), reporting the p-value.
2. **Given** the same forecasts, **When** the CRPS is calculated using `properscoring.crps_ensemble`, **Then** the system outputs a scalar score for each model, allowing for ranking based on proper scoring rules.

### User Story 3 - Statistical Significance and Conformal Baseline (Priority: P3)

The researcher must be able to perform paired bootstrap tests to determine if differences in calibration metrics between models are statistically significant (p < 0.05) and optionally run a conformal prediction wrapper to see if post-hoc adjustment improves calibration.

**Why this priority**: This addresses the "Expected results" requirement for statistical rigor. It moves from descriptive statistics to inferential claims, allowing the researcher to falsify the hypothesis that "intervals are calibrated." The conformal baseline serves as a proof-of-concept for correction.

**Independent Test**: The system can be tested by comparing the coverage deviation of ARIMA vs. Prophet on a held-out set and verifying that the bootstrap test returns a p-value indicating whether the difference is significant.

**Acceptance Scenarios**:

1. **Given** coverage deviations for two models (e.g., ARIMA and Prophet), **When** a paired bootstrap test is executed with 1000 resamples at the *time series* level, **Then** the system outputs a p-value determining if the difference in calibration is statistically significant at the α=0.05 level.
2. **Given** a baseline model (e.g., LSTM), **When** a conformal prediction wrapper is applied using the "Self-Calibrating Conformal Prediction" method, **Then** the system reports the new empirical coverage and compares it to the baseline to quantify the improvement.

### Edge Cases

- What happens when a specific time series in the M4 dataset has zero variance or constant values, causing ARIMA or LSTM to fail to converge? The system must catch the exception, log the series ID, and skip it without crashing the entire pipeline.
- How does the system handle the computational limit of the GitHub Actions runner (7 GB RAM) when loading the full UCI Electricity dataset? The system must implement a streaming or chunked loading strategy to process series sequentially rather than loading all data into memory at once.
- What if the LSTM model fails to produce valid predictive intervals due to numerical instability? The system must detect `NaN` or `Inf` values in the interval bounds, flag the run, and retry with a reduced learning rate or different initialization, up to 2 attempts before marking the series as "failed."

## Requirements

### Functional Requirements

- **FR-001**: System MUST load the M4 and UCI Electricity datasets, split each series into the first [deferred] of observations as the training window and the final [deferred] as the hold-out test window, and standardize to zero mean and unit variance (See US-1).
- **FR-002**: System MUST fit ARIMA (using `statsmodels`), Prophet, and a lightweight LSTM (single hidden layer, 32 units, max 50 epochs or early stopping with patience=5) on the training data for every series in the benchmark datasets (See US-1).
- **FR-003**: System MUST generate 0.80 and 0.95 predictive intervals for all models: ARIMA via conditional variance, Prophet via `uncertainty_samples` combined with explicit residual simulation to capture observation noise, and LSTM via Gaussian residuals or conformal wrapper (See US-1).
- **FR-004**: System MUST compute empirical coverage, PIT histograms with Ljung-Box tests for uniformity (to account for autocorrelation), and CRPS scores for all generated forecasts. PIT analysis must explicitly validate distributional shape independent of interval construction (See US-2).
- **FR-005**: System MUST perform paired bootstrap tests (1000 resamples) at the *time series* level to compare calibration metrics across models and report p-values for significance at α=0.05 (See US-3).
- **FR-006**: System MUST implement a conformal prediction wrapper based on the "Self-Calibrating Conformal Prediction" method to assess post-hoc calibration improvements (See US-3).
- **FR-007**: System MUST handle dataset-variable fit by explicitly checking that M4 and UCI datasets contain the necessary time-series structure (timestamp, value). If required variables are missing, the pipeline MUST fail immediately with a descriptive error code (See US-1).

### Key Entities

- **TimeSeries**: A single univariate time series containing a sequence of timestamps and observed values, split into training and test sets.
- **PredictiveInterval**: A tuple (lower_bound, upper_bound) associated with a specific forecast horizon and nominal coverage level (e.g., 0.95).
- **CalibrationMetric**: A record containing empirical coverage, PIT uniformity p-value, and CRPS score for a specific model-series pair.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Empirical coverage deviation from nominal levels (0.80 and 0.95) is measured against the nominal target to determine if the hypothesis "intervals are calibrated" is falsified (See US-1).
- **SC-002**: Uniformity of PIT histograms is measured against the Ljung-Box test statistic (p < 0.05) to assess distributional calibration, accounting for autocorrelation (See US-2).
- **SC-003**: Predictive accuracy and sharpness are measured against the Continuous Ranked Probability Score (CRPS) to rank models (See US-2).
- **SC-004**: Statistical significance of coverage differences is measured against a paired bootstrap test with 1000 resamples at the *time series* level and α=0.05 threshold (See US-3).
- **SC-005**: The impact of post-hoc calibration is measured by comparing the empirical coverage of the baseline model vs. the conformal wrapper (See US-3).

## Assumptions

- The M4 and UCI Electricity datasets are accessible via `wget` from the provided URLs and do not require authentication or API keys.
- The LSTM model will be implemented with a single hidden layer of 32 units and trained for a fixed number of epochs (max 50) or until early stopping (patience=5), ensuring it runs within the 6-hour CI limit on CPU.
- The analysis will treat the time series as independent for the purpose of coverage calculation, acknowledging that while individual series are independent, the models may capture temporal dependencies within each series.
- The "Self-Calibrating Conformal Prediction" method will be implemented using a simplified version suitable for CPU execution, assuming the method's computational overhead does not exceed the 6-hour limit when applied to the sampled dataset.
- No GPU accelerators (CUDA) are available; all models (including LSTM) must run in default precision on CPU.
- The datasets are sufficiently small to fit within ~7 GB RAM when processed sequentially or in small batches; if a single series is too large, it will be subsampled.
- The `properscoring` library is available in the environment or can be installed via `pip` without conflicts.
- The research design is observational; findings will be framed as associational regarding model performance, not causal claims about the data generation process.
- The threshold for statistical significance (α=0.05) is a community-standard default for hypothesis testing in this domain.
- The sample size for the bootstrap test is fixed at 1000 resamples to balance computational cost and statistical power.
- If the LSTM model produces unstable intervals, a fallback to a simpler residual-based Gaussian interval will be used for that specific series.