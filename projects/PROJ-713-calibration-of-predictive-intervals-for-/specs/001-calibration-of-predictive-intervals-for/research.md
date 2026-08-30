# Research: Calibration of Predictive Intervals for Time‑Series Forecasts

## Research Question

Do standard time-series forecasting models (ARIMA, Prophet, LSTM) produce calibrated predictive intervals on the M4 and UCI Electricity benchmarks, and can post-hoc conformal prediction improve calibration?

## Dataset Strategy

### Verified Datasets
The following datasets are selected based on the spec's requirement for M4 and UCI Electricity.
*Note: The user-provided "# Verified datasets" block in the prompt does not list M4 or UCI Electricity. This plan defines a verified fallback chain to ensure reproducibility.*

**Primary Sources (Hugging Face)**:
1. **M4 Forecasting Competition Dataset**:
 * *Source*: `datasets.load_dataset("m4-dataset")`
 * *Verification*: Pinned to commit hash `abc123...` (to be resolved at runtime).
 * *Fallback*: Direct download from `<freq>.csv` with SHA-256 checksum verification.
2. **UCI Electricity Load Diagrams**:
 * *Source*: `datasets.load_dataset("uci-electricity-load")`
 * *Verification*: Pinned to commit hash `def456...`.
 * *Fallback*: `ucimlrepo` package or direct download from ` with SHA-256 checksum verification.

**Dataset Variable Fit**:
* **M4**: Contains `timestamp` (year, quarter, month, week, day) and `value` (sales/energy). Sufficient for univariate forecasting.
* **UCI**: Contains `timestamp` and multiple `series` (load profiles). The pipeline will iterate over each series individually to handle the multivariate nature as requested in US-1.

### Data Processing Strategy
1. **Streaming**: Both datasets will be processed using a streaming approach (`datasets.load_dataset(..., streaming=True)` or chunked reading) to stay within 7 GB RAM.
2. **Splitting**: For each series, the **first [deferred]** of observations are allocated to training and the **final [deferred]** to test (Constitution Principle VII).
3. **Standardization**: Training data is standardized (zero mean, unit variance) and applied to test data.
4. **Sampling**: A stratified random sample of **500 series** (250 M4, 250 UCI) is selected to ensure statistical power while fitting the 6-hour runtime budget. Processing the full M4 dataset (100k+ series) would exceed the 6-hour limit.

## Methodology

### Models
1. **ARIMA**: Implemented via `statsmodels.tsa.arima.model.ARIMA`. Order selection via AIC or fixed `(1,1,1)` for stability.
2. **Prophet**: Implemented via `prophet`. `uncertainty_samples` set to 1000 to simulate posterior predictive intervals.
3. **LSTM**:
 * Architecture: Single hidden layer, 32 units.
 * Training: Max 50 epochs, early stopping (patience=5).
 * Intervals: Gaussian residual assumption (fit mean and variance on residuals) or Conformal wrapper.
 * Hardware: CPU only (default precision).

### Metrics
1. **Empirical Coverage**: Proportion of test values falling within the predicted **0.80** and **0.95** intervals.
2. **PIT (Probability Integral Transform)**:
 * Calculation: `PIT = CDF(observed | forecast_distribution)`.
 * Test: **Ljung-Box test** on PIT values to test for uniformity (accounting for autocorrelation). *Note: KS test is explicitly rejected per Spec FR-004 and Constitution Principle VI (with deviation).*
3. **CRPS (Continuous Ranked Probability Score)**: Calculated via `properscoring.crps_ensemble` to measure sharpness and reliability.

### Statistical Significance
* **Paired Bootstrap**: 1000 resamples at the **series level** (resampling the scalar coverage deviation metric for each of the N=500 series).
 * *Unit of Analysis*: The bootstrap operates on the **N series**, not the time-points within a series, to preserve the independence assumption.
* **Alpha**: 0.05.

### Conformal Prediction
* **Method**: Self-Calibrating Conformal Prediction (SCCP).
* **Goal**: Post-hoc adjustment of interval widths to achieve nominal coverage.

### Residual Diagnostics & Distributional Independence
* **Decoupling**: The Ljung-Box test is applied to the **empirical PIT values** regardless of the interval construction method (Gaussian or Conformal).
* **Diagnostic Step**: Before applying the Gaussian residual assumption for LSTM, a Shapiro-Wilk test is performed on residuals. If residuals are significantly non-Gaussian (p < 0.05), the Conformal wrapper is preferred for interval construction. However, the **Ljung-Box test remains the validity check** for calibration, independent of the construction assumption. This ensures that the test validates the *actual* distribution, not the assumed one.

## Decision Rationale: Compute Strategy

* **CPU-First**: The project runs on GitHub Actions (a standard CI/CD environment with multiple CPU cores and sufficient RAM). All models are designed to run here.
 * *ARIMA/Prophet*: Native CPU.
 * *LSTM*: Lightweight (32 units) and early-stopped to fit within the 6h window **on the sampled 500 series**.
* **No GPU Escape Hatch Needed**: The spec explicitly assumes "No GPU accelerators" and the LSTM is small enough. If the LSTM training exceeds 6h on the full dataset, the plan will fall back to a **sampled subset** (e.g., first 1000 series of M4) rather than fabricating results.
* **Data Streaming**: Essential to avoid OOM errors on the UCI dataset.

## Limitations & Risks
1. **Dataset Availability**: If M4 or UCI Electricity cannot be downloaded programmatically without credentials, the project cannot proceed. *Mitigation*: The pipeline will fail fast with a clear error message.
2. **LSTM Stability**: Numerical instability may occur. *Mitigation*: Fallback to Gaussian residuals or skip the series (logged).
3. **Power**: The sample size (N=500) is chosen to ensure [deferred] power for detecting [deferred] coverage deviations. Smaller samples may limit power. *Mitigation*: Report power limitations honestly.
4. **Runtime**: Processing the full M4 dataset (100k+ series) is infeasible on the 6-hour CI limit. The plan relies on the stratified sample of 500 series to ensure completion.