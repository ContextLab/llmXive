# Feature Specification: Statistical Modeling of Temporal Dependence in Cryptocurrency Price Fluctuations

**Feature Branch**: `feat/001-crypto-regime-switching`  
**Created**: 2026-10-13  
**Status**: Draft  
**Input**: User description: “What is the time‑varying structure of serial correlation in Bitcoin and Ethereum returns across different market regimes, and how does cross‑asset dependence evolve during periods of high volatility compared to stable conditions?”  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Quantify regime‑dependent dependence (US-1) (Priority: P1)

A researcher wants a reproducible analysis that identifies low‑volatility and high‑volatility regimes in BTC‑ETH returns and reports the serial‑correlation coefficients and cross‑asset correlation matrices for each regime.

**Why this priority**: This story directly answers the core research question and provides the primary empirical evidence required for the study.

**Independent Test**: Execute the provided Jupyter notebook on a fresh CI runner; the notebook must complete, output the regime‑specific parameters, and generate the statistical test results without manual intervention.

**Acceptance Scenarios**  

1. **Given** a clean daily OHLCV dataset for BTC and ETH covering the past several years, **when** the notebook is run end‑to‑end, **then** it produces (a) a 2‑state regime label series, (b) regime‑specific VAR coefficient tables, and (c) a cross‑asset correlation matrix for each regime.  
2. **Given** the output from (1), **when** the likelihood‑ratio test is consulted, **then** the p‑value is reported and, if p < 0.05, the notebook declares the RS‑VAR model statistically preferred over a single‑regime VAR.

### User Story 2 – Baseline comparison and robustness (US-2) (Priority: P2)

A researcher wants to confirm that the regime‑switching model provides a genuine improvement over a stationary VAR and that results are not sensitive to the choice of regime number or volatility proxy.

**Why this priority**: Provides methodological validation and guards against over‑fitting, fulfilling the panel’s requirement for sound inference.

**Independent Test**: Run the notebook with the default 2‑state HMM, then re‑run with a 3‑state HMM and with an alternative volatility proxy; compare information‑criterion scores and test statistics.

**Acceptance Scenarios**  

1. **Given** the default 2‑state analysis, **when** a stationary VAR is fitted on the same data, **then** the notebook reports a likelihood‑ratio test p‑value < 0.05 (or notes failure to reject).  
2. **Given** the 2‑state and 3‑state RS‑VAR fits, **when** the Bayesian Information Criterion (BIC) is computed, **then** the ΔBIC ≤ 2, indicating that adding a third regime does not meaningfully improve fit.

### User Story 3 – Failure handling (US-3) (Priority: P3)

A researcher needs clear diagnostics when data acquisition or model estimation fails, so the study can be rerun after remedial action.

**Why this priority**: Ensures the workflow is robust to common operational issues and maintains reproducibility.

**Independent Test**: Intentionally corrupt the input CSV (e.g., introduce NaNs) and run the notebook; it must raise a descriptive error and halt gracefully.

**Acceptance Scenarios**  

1. **Given** missing days in the OHLCV feed, **when** the data‑loading step executes, **then** the notebook aborts with a message “Data gap detected: X consecutive missing days – aborting analysis.”  

### Edge Cases

- API request to CoinGecko fails (HTTP ≥ 500) – notebook retries three times with exponential back‑off, then aborts with a clear error.  
- HMM fails to converge within 100 EM iterations – notebook reports “HMM convergence not achieved” and falls back to a single‑regime VAR for comparison.  
- RS‑VAR estimation yields a singular covariance matrix – notebook detects the condition, drops the problematic regime, and logs the issue.  
- Input CSV contains duplicate timestamps – notebook de‑duplicates by keeping the first occurrence and logs the count of duplicates removed.  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download daily OHLCV data for Bitcoin (BTC) and Ethereum (ETH) covering the most recent 5 years from the CoinGecko public API. *(See US-1)*  
- **FR-002**: The system MUST compute log‑returns for each asset and construct a realized‑volatility proxy (e.g., squared returns) for every day. *(See US-1)*  
- **FR-003**: The system MUST fit a 2‑state Hidden Markov Model (HMM) to the joint return series using the volatility proxy as the emission feature, and assign a regime label to each observation. *(See US-1)*  
- **FR-004**: The system MUST fit a Regime‑Switching Vector Autoregression (RS‑VAR) where both the autoregressive coefficient matrices and the error‑covariance matrices are allowed to differ between the HMM‑derived regimes. *(See US-1)*  
- **FR-005**: The system MUST compare the RS‑VAR to a stationary VAR using (a) Bayesian Information Criterion (BIC) and (b) a parametric bootstrap likelihood‑ratio test (10 000 resamples) to assess statistical significance at α = 0.05. *(See US-1)*  
- **FR-006**: The system MUST extract and report, for each regime, (a) the lag‑1 autocorrelation coefficients for BTC and ETH, and (b) the cross‑asset correlation (Pearson) between BTC and ETH residuals. *(See US-1)*  
- **FR-007**: The system MUST fit alternative RS‑VAR models with 3 regimes and with an alternative volatility proxy (e.g., 10‑day rolling standard deviation), compute Bayesian Information Criterion (BIC) for each, and report ΔBIC relative to the baseline 2‑regime model. *(See US-2)*  
- **FR-008**: The system MUST generate a single Jupyter notebook that executes the entire pipeline from data acquisition to final tables/figures, and the notebook MUST run end‑to‑end on a standard CI runner without errors. *(See US-1)*  
- **FR-009**: The system SHOULD log all major steps (data download, preprocessing, HMM convergence, VAR fitting, statistical tests) with timestamps to a plain‑text log file for auditability. *(See US-3)*  
- **FR-010**: The system MUST validate that the identified regimes correspond to statistically distinct volatility levels by performing a bootstrap likelihood‑ratio test between a 1‑state and 2‑state HMM (5 000 resamples) at α = 0.05. *(See US-1)*  

### Key Entities

- **AssetReturnSeries**: Daily log‑return vectors for BTC and ETH (attributes: date, btc_return, eth_return).  
- **RegimeLabelSeries**: Integer series (1 = Low‑Vol, 2 = High‑Vol) aligned with AssetReturnSeries.  
- **RSVARModel**: Set of regime‑specific VAR coefficient matrices and error‑covariance matrices.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Data acquisition yields ≥ 1 800 daily observations for each asset with no missing dates. *(See US-1)*  
- **SC-002**: The HMM converges (log‑likelihood change < 1e‑4) within 100 EM iterations, improves log‑likelihood by at least 10 points over a single‑state baseline, **and** a bootstrap likelihood‑ratio test (5 000 resamples) rejects the 1‑state model at α = 0.05, confirming distinct regimes. *(See US-1)*  
- **SC-003**: The bootstrap LRT (10 000 resamples) for the RS‑VAR versus stationary VAR yields p < 0.05, indicating the RS‑VAR provides a statistically significant improvement. *(See US-1)*  
- **SC-004**: A Wald test (or bootstrap difference test with 2000 resamples) shows that the lag‑1 autocorrelation coefficients for BTC (and ETH) differ between regimes at α = 0.05. *(See US-1)*  
- **SC-005**: A permutation‑based Fisher‑z test that accounts for regime‑classification uncertainty indicates that the cross‑asset correlation in the high‑volatility regime differs from that in the low‑volatility regime at α = 0.05 **or** the absolute difference ≥ 0.20. *(See US-1)*  
- **SC-006**: Adding a third regime does not improve BIC by more than 2 points (ΔBIC ≤ 2), supporting the parsimonious 2‑regime specification. *(See US-2)*  
- **SC-007**: The notebook completes on the GitHub Actions free‑tier runner within the typical execution window ([deferred]) and produces the expected output files (log, parameter tables, figures). *(See US-1)*
- **SC-008**: All log messages are written to `analysis.log` and include timestamps for each major step. *(See US-3)*  
- **SC-009**: The bootstrap likelihood‑ratio test for regime distinctness (FR‑010) reports p < 0.05, satisfying Constitution Principle VI. *(See US-1)*  

## Assumptions

- The CoinGecko public API provides uninterrupted daily OHLCV data for BTC and ETH for the full multi-year window; no API key or rate‑limit exemption is required.  
- Daily log‑returns are approximately stationary within each regime, satisfying the VAR modelling assumptions.  
- A volatility proxy based on squared daily returns (or a 10‑day rolling standard deviation) is sufficient to capture regime structure for the HMM.  
- The dataset (~1 800 rows × 2 assets) comfortably fits into memory on the CI runner (≤ 6 GB RAM).  
- All statistical inference is associative; the study does **not** claim causal effects of volatility on correlation.  
- Significance thresholds are fixed at α = 0.05 for all hypothesis tests, a conventional choice in econometrics.  
- No GPU or specialized hardware is required; all computations rely on CPU‑only libraries (`pandas`, `numpy`, `statsmodels`, `hmmlearn`).  
- The free‑tier GitHub Actions environment provides at least 2 CPU cores, 7 GB RAM, and 14 GB of disk space, matching the resource budget stated in the methodology sketch.  
- Resource usage (CPU time, memory) will be measured via the Unix `time -v` command within the CI job; the CI script will fail if the notebook exceeds the typical free‑tier limits ([deferred], ≤ 2 CPU cores, ≤ 6 GB RAM).
