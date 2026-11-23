# Research: Evaluating Robustness of Statistical Methods to Non-Independence

## Problem Statement

Standard statistical tests (e.g., one-sample t-test) assume independent observations. Time series data often exhibits long-range dependence (autocorrelation), which violates this assumption and inflates Type I error rates. This project quantifies that inflation across real-world datasets and synthetic ground-truth data. Crucially, the study distinguishes between **synthetic verification** (where H is known, used to validate the t-test implementation and theoretical VIF curve) and **empirical robustness** (where H is estimated from noisy real data, used to test the correlation between *estimated* H and observed error inflation). This avoids the tautology of regressing a known function against itself.

## Dataset Strategy

The project uses only **open, directly-downloadable** datasets to ensure CI feasibility. Access-gated data (e.g., ADNI, UK Biobank) is excluded. The plan prioritizes datasets with programmatic access (Hugging Face, `yfinance`, `xarray`).

### Verified Datasets

| Dataset Name | Source Type | Verified URL / Loader | Usage |
|--------------|-------------|-----------------------|-------|
| NOAA GHCN-Daily | `xarray` / Direct CSV | ` (or verified HuggingFace mirror for raw CSV) | Raw environmental time series (temperature/precipitation) with >10k points. |
| Yahoo Finance (AAPL, MSFT, GOOGL, AMZN, TSLA) | `yfinance` library | `yf.Ticker("AAPL").history(period="max")` (and 4 others) | Financial price series (unit root expected). Specific tickers selected for >10 years of data. |
| UK National Grid Load | Hugging Face (JSONL) | ` | Energy load time series. |
| UCI Electricity Load Diagrams | Hugging Face (CSV) | `https://huggingface.co/datasets/UCI-ML/UCI_Electricity_Load_Diagrams_20112014_20140801/resolve/main/ElectricityLoadDiagrams20112014.csv` | Continuous power load time series (long duration, suitable for Hurst). |
| Internet Traffic (Maurice) | Hugging Face (CSV) | `https://huggingface.co/datasets/maurice/traffic/resolve/main/traffic.csv` | Long-range dependent network traffic data. |

*Note: No verified source found for "ErrorRateSummary" (synthetic output). This is expected as it is a derived result, not an input.*

### Data Availability & Feasibility

- **Download**: All datasets are accessible via `requests`, `datasets`, `yfinance`, or `xarray` without authentication.
- **Size**: The selected datasets are well under the available RAM limit. Streaming is used for Hugging Face datasets.
- **Preprocessing**: Missing values will be filled via linear interpolation (FR-002).
- **Stationarity**: Dual-path strategy: ADF for unit roots; DFA for long-memory preservation.

## Statistical Methodology

### 1. Preprocessing Pipeline (FR-001, FR-002)
- **Missing Values**: Linear interpolation.
- **Dual-Path Stationarity Check**:
 - **Path A (Unit Root)**: Perform Augmented Dickey-Fuller (ADF) test.
 - If `p < 0.05`: Difference data **once** to remove stochastic trend (I(1) → I(0)). Re-check ADF.
 - If `p >= 0.05`: **DO NOT DIFFERENCE**. Proceed to Path B.
 - **Path B (Long Memory)**: If ADF `p >= 0.05`, assume stationarity but check for long-range dependence.
 - Apply **Detrended Fluctuation Analysis (DFA)** to estimate Hurst exponent (H) *without* differencing.
 - If H > 0.5, the series is long-memory. **Do not difference** (differencing destroys long-memory).
 - If a linear trend is present, apply linear detrending to residuals only.
- **Dependence Quantification**:
 - **ACF**: Computed up to lag 20.
 - **Hurst Exponent**: Estimated via DFA (robust to trends) for real data; known for synthetic.
 - **Spectral Density**: Peak ratio calculated to identify dominant frequencies.

### 2. Synthetic Ground Truth (FR-003, FR-007)
- **Models**: Fractional Gaussian Noise (fGn) and ARFIMA.
- **Parameters**: Mean=0, Hurst ∈ {0.7, 0.8, 0.9}, **Length N ∈ {, 500, 1000, 5000, 10000}**.
- **Null Distribution**: **[deferred] shuffled (permuted) versions per series** (for every real and synthetic series) to break temporal dependence (Constitution Principle VII).
- **Validation**: Baseline validity check on H=0.5 data ([deferred] trials) to ensure rejection rate ≈ 0.05 (Clopper-Pearson CI). This validates the *implementation*, not the empirical claim.

### 3. Hypothesis Testing (FR-004)
- **Tests**: One-sample t-test, F-test.
- **Exclusion**: Two-sample t-test is excluded (invalid for detrended residuals with long-range dependence).
- **Metric**: Observed Type I error rate at α=0.05.

### 4. Regression & Mechanism Validation (FR-005)
- **Model**: **Non-linear / GLM Regression** of Observed Error Rate vs. Hurst Exponent and log(N_eff).
 - **Formula**: `logit(ErrorRate) ~ H + log(N_eff) + (H * log(N_eff))` (or power-law fit).
 - **Predictors**: Hurst exponent, log(N_eff), and their interaction. `Max_ACF_Lag1` and `Spectral Density` are descriptive only.
 - **Diagnostics**:
 - **VIF**: Variance Inflation Factor to check collinearity (though only one predictor, this validates the method).
 - **N_eff**: Effective Sample Size to quantify the reduction in independent information.
- **Empirical vs. Synthetic**:
 - **Synthetic**: Used to verify the theoretical VIF curve (known H vs. observed error).
 - **Real**: Used to test the correlation between *estimated* H and observed error (non-trivial empirical finding).

## Compute Feasibility

- **CPU-First**: All methods (ADF, DFA, fGn generation, t-tests, GLM) are CPU-tractable.
- **Memory**: [deferred] trials × N levels × H levels × Several real datasets

The specific value to remove/generalize: 'Several'

Rewritten passage: ≈ 1M tests. Memory efficient via streaming and batch processing.
- **Runtime**: Estimated < 4 hours for full pipeline (ingestion + N-variation grid + regression).
- **GPU**: Not required. No transformer or diffusion models are used.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Bonferroni correction applied if comparing t-test vs F-test results.
- **Power**: 10,000 Monte Carlo trials provide high power to detect deviations from α=0.05.
- **Causal Inference**: Observational study on real data; claims framed as associational. Synthetic data provides causal ground truth (known H) for implementation validation.
- **Measurement Validity**: Hurst exponent estimation methods (DFA) are standard and validated for long-memory processes.
- **Collinearity**: ACF and Spectral Density are excluded from regression to avoid multicollinearity with Hurst (they are functionally related). N_eff is explicitly included to avoid misspecification.

## Decision Rationale

- **Why fGn/ARFIMA?**: They provide precise control over long-range dependence (Hurst exponent), essential for ground truth.
- **Why Shuffling?**: Creates a valid null distribution that preserves marginal distribution but breaks temporal dependence, isolating the effect of autocorrelation. **[deferred] iterations per series** ensures stability of the null distribution.
- **Why Exclude Two-Sample t-test?**: The spec explicitly excludes it due to invalidity with detrended residuals; the plan adheres to this constraint.
- **Why CPU?**: The statistical methods are lightweight; no GPU acceleration is needed, ensuring compatibility with GitHub Actions free tier.
- **Why N-Variation?**: To properly estimate the interaction between H and N, avoiding the 4-point regression pitfall.
- **Why Non-Linear/GLM?**: The relationship between H and Type I error is non-linear; a linear model would be biased.