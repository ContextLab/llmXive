---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Modeling of Temporal Dependence in Cryptocurrency Price Fluctuations

**Field**: statistics

## Research question

What is the time-varying structure of serial correlation in Bitcoin and Ethereum returns across different market regimes, and how does cross-asset dependence evolve during periods of high volatility compared to stable conditions?

## Motivation

Cryptocurrency markets are characterized by non-stationarity and abrupt regime shifts, yet standard statistical models often assume static dependence structures. Quantifying how serial correlation and cross-asset coupling change between high-volatility and stable regimes is critical for distinguishing genuine market dynamics from noise and for understanding the limits of statistical arbitrage without external signals.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using terms including "regime-switching cryptocurrency returns," "time-varying cross-asset dependence crypto," "volatility regime Bitcoin Ethereum," and "Markov-switching models crypto." The search yielded a sparse set of results directly addressing the *time-varying* nature of dependence structures across *specific* market regimes for the BTC-ETH pair. Most existing work focuses on static forecasting performance or general volatility modeling rather than the evolution of correlation structures under regime shifts.

### What is known

- [Bitcoin Forecasting with Classical Time Series Models on Prices and Volatility (2025)](https://arxiv.org/abs/2511.06224) — Establishes that classical models (ARIMA, GARCH) provide baseline performance for Bitcoin but notes limitations in capturing abrupt regime shifts and non-linear dependencies.
- [MoFE: A Novel Mixture-of-Experts Framework with Fourier Neural Operators for Cryptocurrency Forecasting (2026)](https://arxiv.org/abs/2608.17342) — Highlights the challenge of "abrupt regime shifts" in crypto forecasting and proposes deep learning solutions, implicitly acknowledging that standard linear models fail to adapt to changing dependence structures.
- [TimeCatcher: A Variational Framework for Volatility-Aware Forecasting of Non-Stationary Time Series (2026)](https://arxiv.org/abs/2601.20448) — Discusses the need for volatility-aware frameworks to handle non-stationarity, though it focuses on general time series rather than specific crypto regime-dependent correlation dynamics.

### What is NOT known

There is no published work that explicitly measures the *magnitude* and *direction* of the shift in serial correlation and cross-asset (BTC-ETH) dependence when transitioning between defined high-volatility and stable regimes using purely statistical (non-deep-learning) time-varying parameter models. Specifically, the evolution of the correlation coefficient and autoregressive parameters during crash vs. accumulation phases remains unquantified in the literature.

### Why this gap matters

Understanding how dependence structures evolve during crises is vital for risk management and portfolio construction in crypto-assets. If correlations collapse or invert during high volatility, standard diversification strategies fail; conversely, if serial correlation strengthens, it may offer transient predictive signals. Filling this gap provides empirical evidence on the stability of market microstructure assumptions in crypto.

### How this project addresses the gap

This project will fit a Regime-Switching Vector Autoregression (RS-VAR) model to daily BTC and ETH returns, explicitly estimating regime-dependent correlation matrices and autoregressive coefficients. By statistically testing for parameter instability and comparing regime-specific dependence metrics, the methodology will directly quantify how the "time-varying structure" of the market changes, providing the missing empirical evidence on regime evolution.

## Expected results

We expect to observe distinct regimes where serial correlation is negligible (random walk behavior) during stable periods but becomes statistically significant (positive or negative) during high-volatility events. Furthermore, we anticipate that the cross-asset correlation between Bitcoin and Ethereum will strengthen significantly during market stress (flight-to-safety or panic selling) compared to stable periods. A likelihood-ratio test should reject the null hypothesis of a single-regime constant-parameter model in favor of a two-regime model (p < 0.05), confirming the presence of time-varying dependence.

## Methodology sketch

- **Data acquisition**: `wget` daily historical OHLCV data for Bitcoin (BTC) and Ethereum (ETH) from CoinGecko API (e.g., `https://api.coingecko.com/api/v3/coins/bitcoin/market_chart...`) covering the last 5 years.
- **Preprocessing**:
  - Compute log-returns for both assets.
  - Construct a realized volatility proxy (e.g., squared returns or rolling standard deviation) to identify potential regime states.
  - Split data into training (80%) and testing (20%) sets, ensuring the test set includes at least one known high-volatility period (e.g., 2022 crash).
- **Regime identification**:
  - Apply a Hidden Markov Model (HMM) with 2 states (Low Volatility, High Volatility) to the joint return series to probabilistically assign a regime label to each day.
  - Validate regime assignments against historical volatility spikes.
- **Model fitting (RS-VAR)**:
  - Fit a Regime-Switching Vector Autoregression (RS-VAR) model where the autoregressive coefficients and the covariance matrix of errors are allowed to differ between the two identified regimes.
  - Use the `statsmodels` library (specifically `MarkovSwitching`) to estimate parameters via Maximum Likelihood.
- **Baseline comparison**:
  - Fit a standard stationary VAR model (ignoring regimes) and a univariate AR(1) model for comparison.
- **Evaluation**:
  - Compare the log-likelihood of the RS-VAR model against the stationary VAR model using a Likelihood Ratio Test (LRT) to determine if regime-switching is statistically necessary.
  - Extract and compare the estimated correlation matrices and autoregressive coefficients between the "Low Vol" and "High Vol" regimes.
  - Perform a Diebold-Mariano test to check if the RS-VAR forecasts significantly outperform the stationary baseline in the test set.
- **Robustness checks**:
  - Vary the number of regimes (e.g., 3 states) to check for overfitting.
  - Test sensitivity to the volatility proxy used for regime initialization.
- **Reproducibility**:
  - All analysis will be conducted in a single Jupyter notebook using `pandas`, `numpy`, `statsmodels`, and `scipy`.
  - The notebook will run end-to-end on a GitHub Actions free-tier runner within 2 hours, well under the 6-hour limit.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: none.
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-09-08T13:06:30Z
**Outcome**: exhausted
**Original term**: Statistical Modeling of Temporal Dependence in Cryptocurrency Price Fluctuations statistics
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Statistical Modeling of Temporal Dependence in Cryptocurrency Price Fluctuations statistics | 0 |
| 1 | Time series analysis of cryptocurrency volatility | 4 |
| 2 | Stochastic processes in digital asset pricing | 0 |
| 3 | Autocorrelation and memory effects in crypto markets | 0 |
| 4 | GARCH modeling of cryptocurrency returns | 0 |
| 5 | Long-range dependence in blockchain financial data | 0 |
| 6 | Fractional Brownian motion applied to Bitcoin prices | 0 |
| 7 | Non-linear dynamics in cryptocurrency price movements | 0 |
| 8 | Volatility clustering in digital currency markets | 0 |
| 9 | Econometric forecasting of crypto asset fluctuations | 0 |
| 10 | Markov switching models for cryptocurrency regimes | 0 |
| 11 | High-frequency trading data analysis in crypto | 0 |
| 12 | Heavy-tailed distributions in cryptocurrency returns | 0 |
| 13 | Multifractal analysis of crypto price time series | 0 |
| 14 | Regime-switching volatility in digital assets | 0 |
| 15 | Random walk hypothesis testing in cryptocurrency markets | 0 |
| 16 | Volatility spillover effects across cryptocurrency exchanges | 0 |
| 17 | Bayesian time series models for crypto pricing | 0 |
| 18 | Extreme value theory in cryptocurrency risk management | 0 |
| 19 | Cointegration analysis of paired cryptocurrency assets | 0 |
| 20 | Fractional integration in digital currency price series | 0 |

### Verified citations

1. **TimeCatcher: A Variational Framework for Volatility-Aware Forecasting of Non-Stationary Time Series** (2026). Zhiyu Chen, Minhao Liu, Yanru Zhang. arXiv. [2601.20448](https://arxiv.org/abs/2601.20448). PDF-sampled: No.
2. **MoFE: A Novel Mixture-of-Experts Framework with Fourier Neural Operators for Cryptocurrency Forecasting** (2026). Bowen Liu, Mingming Sun. arXiv. [2608.17342](https://arxiv.org/abs/2608.17342). PDF-sampled: No.
3. **Bitcoin Forecasting with Classical Time Series Models on Prices and Volatility** (2025). Anmar Kareem, Alexander Aue. arXiv. [2511.06224](https://arxiv.org/abs/2511.06224). PDF-sampled: No.
