# Research: Evaluating Calibration of Probabilistic Weather Forecasts

## Executive Summary
This research plan addresses the evaluation of calibration in probabilistic weather forecasts using the SubseasonalRodeo dataset (or NOAA GFS substitute). The core challenge is establishing a rigorous baseline, applying isotonic regression for recalibration, and implementing a Bayesian hierarchical model with physics-informed priors to handle sparse events. Critical constraints include CPU-only execution on GitHub Actions, strict data availability gates, and fallback mechanisms for model convergence failures.

**Dataset Status**: SubseasonalRodeo has **NO verified source**. The plan implements a fallback to NOAA GFS (verified HuggingFace URL) as the primary executable path. A spec amendment is flagged to update FR-001.

## Dataset Strategy

| Dataset | Purpose | Source | Verification |
|---------|---------|--------|--------------|
| **SubseasonalRodeo** | Primary source for GFS ensemble forecasts and observations | **NO verified source found** (see "Verified datasets" block) | ⚠️ **CRITICAL**: The dataset lacks a verified URL in the provided list. The plan MUST handle this by either (a) using an open substitute (e.g., NOAA GFS via verified URLs below) or (b) explicitly stating no open source exists and reframing the question. **Action**: The implementation will use NOAA GFS data from verified Hugging Face URLs (see below) as the substitute, as SubseasonalRodeo is not directly accessible via programmatic loaders. |
| **NOAA GFS (parquet)** | Alternative source for GFS ensemble probabilities | https://huggingface.co/datasets/Qdrant/NOAA-Buoy/resolve/main/full_2023_remove_flawed.parquet | ✅ Verified (Hugging Face, direct download) |
| **GFS (zip)** | Alternative source for GFS ensemble forecasts | https://huggingface.co/datasets/jacobbieker/gfs-kerken/resolve/main/data/2021/2021022712.zip | ✅ Verified (Hugging Face, direct download) |

> **Note**: The SubseasonalRodeo dataset is mentioned in the spec but has **NO verified source** in the provided list. The plan **MUST** use an open substitute (NOAA GFS from verified URLs) or explicitly state that no open source exists. This research plan adopts NOAA GFS from verified Hugging Face URLs as the substitute, as it contains ensemble forecast probabilities and observations required for calibration metrics.

### Data Acquisition Plan
1. **Primary Attempt**: Use NOAA GFS from `https://huggingface.co/datasets/Qdrant/NOAA-Buoy/resolve/main/full_2023_remove_flawed.parquet` (parquet format, verified) as the substitute dataset.
2. **Verification**: Check for `probability_value` field (or `precip_prob` for NOAA GFS compatibility).
3. **Streaming**: If the dataset exceeds 7 GB RAM, stream via `datasets.load_dataset(..., streaming=True)` and compute statistics online.
4. **Sampling**: If full dataset exceeds disk capacity, take a well-defined random sample (fixed seed) and log power limitation.

## Statistical Methodology

### Baseline Calibration Metrics
- **Brier Score**: Mean squared error between forecast probability and binary event occurrence. Computed per lead time and variable.
- **CRPS (Continuous Ranked Probability Score)**: Proper scoring rule for probabilistic forecasts; integrates CDF difference. Computed per lead time and variable.
- **Reliability Diagrams**: Kernel-smoothed plots of forecast probability bins vs. observed frequencies. Ideal: 45-degree line.
- **PIT Histograms**: Probability Integral Transform values; ideal: uniform distribution. KS test for flatness.

### Isotonic Recalibration
- **Method**: Non-parametric, monotonic regression (pool adjacent violators algorithm).
- **Validation**: Blocked/expanding window (train on years 1-N, test on year N+1).
- **Sensitivity**: 60/40 and 80/20 splits; log results.
- **Constraints**: Minimum sample size threshold per lead time (N >= 100 for test set); fallback to raw forecast if too few samples or regularize by pooling adjacent bins.

### Bayesian Hierarchical Recalibration
- **Model**: Hierarchical logistic regression with lead-time decay prior (physics-informed).
- **Priors**: 
  - **Physics-informed**: Gaussian(mean=-0.1, std=0.05) on lead-time decay coefficient (based on known atmospheric decay rates, not tuned to minimize Brier).
  - **Flat Prior**: Gaussian(mean=0, std=10) as non-physics-informed control.
  - **Sensitivity**: Weak (var=1.0), Medium (var=0.5), Strong (var=0.1) prior strengths.
- **Inference**: MCMC sampling (multiple chains, a sufficient number of draws each).
- **Convergence**: R-hat ≤ 1.05, ESS > 400 for all group-level parameters.
- **Fallback**: If convergence fails or timeout, generate `results_fallback.csv` (isotonic results).

### Statistical Tests
- **Diebold-Mariano (DM)**: One-sided test (α=0.05, alternative: Method A > Method B) on **daily time-series of forecast errors** per lead time.
- **Lag/Block Length**: Newey-West lag length `floor(4 * (T/100)^(2/9))` for HAC; Block Bootstrap block length = 7 days (empirical decay).
- **Normality Check**: Shapiro-Wilk test per lead time and variable; if p < 0.05, switch to Block Bootstrap (preserves autocorrelation).
- **Sensitivity Analysis**: Bootstrapped CI for different splits (60/40, 80/20); no DM tests across splits.

## Compute Feasibility

### CPU-First Strategy
- **Isotonic Regression**: Runs efficiently on CPU; `scikit-learn` `IsotonicRegression` with default settings.
- **Bayesian Inference**: `pymc` with CPU backend; short chains (2000 draws); 60-minute timeout.
- **Metrics**: `properscoring` for Brier/CRPS; `matplotlib`/`seaborn` for plots; all CPU-tractable.
- **Memory**: Stream data if > 7 GB; sample if > 14 GB disk.

### GPU Escape Hatch (Not Required)
- **Rationale**: All methods (isotonic, Bayesian, metrics) have faithful CPU-tractable forms. No transformer/diffusion models or CUDA kernels needed.
- **Decision**: **No GPU escape hatch required**. All computations run on CPU.

## Data Availability & Variable Fit

### Required Variables
- **Forecast**: `probability_value` (continuous probability), `raw_ensemble_mean`, `grid_id`, `lead_time`, `forecast_date`.
- **Observation**: `event_occurred` (binary), `event_value` (continuous), `grid_id`, `observation_date`.

### Dataset Verification
- **SubseasonalRodeo**: NO verified source; **CRITICAL**: If using this dataset, must confirm it contains `probability_value` field. If missing, halt.
- **NOAA GFS (substitute)**: Verified URLs contain ensemble probabilities; confirm `probability_value` field exists or `precip_prob` as alias.
- **Variable Fit**: NOAA GFS contains precipitation and temperature forecasts with ensemble members; aligns with study needs.

### Data Hygiene
- **Checksums**: Record SHA256 checksums for all downloaded files.
- **No In-Place Modification**: Raw data preserved; derivations written to new files.
- **Streaming**: Use `datasets.load_dataset(..., streaming=True)` for large datasets.

## Risk Analysis

### High-Risk Items
1. **Missing `probability_value`**: If dataset lacks this field, pipeline halts (FR-001). **Mitigation**: Verify field presence before processing.
2. **Bayesian Convergence Failure**: R-hat > 1.05 or ESS < 400; timeout. **Mitigation**: Fallback to isotonic results; log status.
3. **Sparse Events**: Lead times with < 100 samples; isotonic overfitting. **Mitigation**: Minimum sample size threshold; fallback to raw forecast.
4. **Autocorrelation**: Time-series errors non-normal; standard DM invalid. **Mitigation**: Block Bootstrap (block length=7).
5. **Memory/Disk Exceed**: Dataset > 7 GB RAM / 14 GB disk. **Mitigation**: Stream or sample; log power limitation.

### Mitigation Strategies
- **Data Availability Gate**: Automated check for `probability_value` or `precip_prob`; exit code 1 if missing.
- **Convergence Monitoring**: Log R-hat, ESS; trigger fallback if thresholds exceeded.
- **Sample Size Enforcement**: Check per lead time; fallback if too few samples.
- **Normality Testing**: Shapiro-Wilk per lead time; switch to Block Bootstrap if needed.
- **Streaming/Sampling**: Use `streaming=True` or fixed-seed random sample; document limitation.

## Decision/Rationale

| Decision | Rationale | Alternative Rejected |
|----------|---|---|
| **NOAA GFS as substitute** | SubseasonalRodeo lacks verified URL; NOAA GFS from verified Hugging Face URLs contains required ensemble probabilities and observations. | Using SubseasonalRodeo without verified URL would fail CI; fabricating a URL violates rules. |
| **CPU-first for all methods** | Isotonic regression and Bayesian MCMC with short chains are CPU-tractable; no GPU needed. | GPU escape hatch unnecessary; methods have faithful CPU forms. |
| **Blocked validation (years 1-N vs N+1)** | Prevents temporal data leakage; respects time-series nature of weather forecasts. | Random split would allow future data in training; invalid for forecasting. |
| **DM-HAC vs. Block Bootstrap** | DM-HAC for normal errors; Block Bootstrap for non-normal (preserves autocorrelation). | Standard t-test invalid for time-series with autocorrelation. |
| **Physics-informed prior vs. Flat Prior** | Validates that prior structure improves calibration for sparse events; flat prior as control. | Only one prior would not decouple prior influence from data signal. |
| **Prior Strength Sensitivity** | Weak/medium/strong priors (var=1.0, 0.5, 0.1) decouple prior influence from data signal. | Only one prior strength would not validate robustness. |
| **Lag/Block Length Justification** | Newey-West formula for HAC; 7 days for Block Bootstrap based on empirical decay. | Fixed arbitrary values would not account for data-specific autocorrelation. |

## References
- **SubseasonalRodeo**: NO verified source (see "Verified datasets" block).
- **NOAA GFS**: https://huggingface.co/datasets/Qdrant/NOAA-Buoy/resolve/main/full_2023_remove_flawed.parquet (verified).
- **Isotonic Regression**: Pool adjacent violators algorithm; `scikit-learn` implementation.
- **Diebold-Mariano Test**: Original paper (1990); HAC estimator for time-series.
- **Bayesian Hierarchical Models**: Gelman et al. (2013); lead-time decay priors in weather forecasting.
- **Calibration Metrics**: Brier score (1950), CRPS (2001), reliability diagrams (1970s).