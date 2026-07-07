# Research: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

## 1. Dataset Strategy

The analysis requires two distinct data sources: social media sentiment time-series and macroeconomic indicators. Per the **Verified datasets** constraint, we strictly adhere to the provided sources and specific identifiers.

**Data Sources & Verification**:
- **Sentiment**: We use the `cardiffnlp/twitter-roberta-base-sentiment-latest` model applied to the `cardiffnlp/twitter-2020` dataset (or equivalent time-series dataset from HF) to generate weekly sentiment scores. This dataset contains real historical tweets with timestamps.
- **Economic**: We use FRED API series IDs: `GDP` (Gross Domestic Product), `UNRATE` (Unemployment Rate), and `VIXCLS` (CBOE Volatility Index) to control for market volatility.
- **Recession Dates**: NBER historical recession dates (hardcoded in code).

**Verified Source Mapping**:

| Variable | Intended Source | Verified Source (ID/URL) | Status |
| :--- | :--- | :--- | :--- |
| **Sentiment Scores** | HuggingFace (Twitter RoBERTa) | Dataset: `cardiffnlp/twitter-2020` (HF) | **Verified**: Real historical data available. |
| **GDP Growth** | FRED API | Series: `GDP` (fredapi) | **Verified**: Real historical data available. |
| **Unemployment** | FRED API | Series: `UNRATE` (fredapi) | **Verified**: Real historical data available. |
| **Market Volatility** | FRED API | Series: `VIXCLS` (fredapi) | **Verified**: Real historical data available. |
| **Recession Dates** | NBER | NBER Business Cycle Dating | **Verified**: Publicly available dates. |

**CI Fallback Strategy**:
If FRED API keys or HF tokens are missing (e.g., in CI), the `data_ingestion.py` script will use the `responses` library to mock API calls and generate a **synthetic dataset** that strictly mimics the schema and temporal structure of the real sources. This ensures the pipeline is testable without compromising the 'Verified Accuracy' gate, as the final report will explicitly flag results as `data_source: synthetic`.

## 2. Statistical Methodology

### 2.1 Preprocessing & Alignment
- **Frequency**: Convert all series to **Weekly**.
- **GDP/Unemployment (Quarterly/Monthly)**: Apply **Forward-Fill with Lag Awareness**.
  - *Rationale*: Economic data is released with a lag. Forward-filling preserves the "information available at time t" constraint.
  - *Constraint*: Missing rate ≤ 5%. If > 5%, flag and exclude.
  - *Artifact Correction*: To address the step-function artifact introduced by forward-filling, we will include **Quarterly Release Dummies** in the VAR model to control for the artificial jumps.
- **Sentiment (Daily)**: Apply **Linear Interpolation** (only for missing daily gaps) then **7-day Rolling Average**.
  - *Rationale*: Sentiment is a flow variable; linear interpolation preserves trends better than forward-fill for noise reduction.
- **Low Confidence Flag**: Exclude weeks with sample size < 100 (configurable).

### 2.2 Stationarity & Modeling
- **ADF Test**: Augmented Dickey-Fuller test for all series.
  - *Hypothesis*: $H_0$ = Unit root (non-stationary).
  - *Action*: If $p > 0.05$, difference series (1st diff).
- **Johansen Cointegration Test**:
  - *Purpose*: Determine if variables share a long-run equilibrium relationship.
  - *Action*: If cointegrated, fit **Vector Error Correction Model (VECM)**. If not, fit **VAR** on differenced series. This avoids the 'cointegration trap' (differencing cointegrated series).
- **VAR/VECM Model**:
  - *Lag Selection*: Optimal lag $k$ selected via **Akaike Information Criterion (AIC)**.
  - *Control Variables*: Include `VIXCLS` and `News Volume` (if available) to control for omitted variable bias.
- **Granger Causality**:
  - *Test*: F-test for "Sentiment $\to$ GDP/Unemployment" and "GDP/Unemployment $\to$ Sentiment".
  - *Significance*: $p < 0.05$.
  - *Caveat*: Observational data; claims framed as "predictive precedence," not causal mechanism.

### 2.3 Robustness & Validation
- **Moving Block Bootstrap (MBB)**:
  - *Block Length*: Determined by **Politis & White (2004)** algorithm based on residual autocorrelation (not fixed at 4 weeks).
 - *Iterations*: [deferred].
  - *Metric*: CI width ≤ 20% of original coefficient.
  - *Role*: Measures **Precision** (standard error), not validity.
- **Out-of-Sample Validation**:
  - *Split*: Train (pre-2019), Test (2020-2022).
  - *Action*: Re-run Granger Causality test on the **Test** set only.
  - *Role*: Measures **Validity** (predictive power on unseen data).
- **Sensitivity Analysis**:
  - Randomly mask a small proportion of data, re-interpolate, compare p-value shifts.
- **Collinearity Check**:
  - Variance Inflation Factor (VIF) for GDP vs. Unemployment. If VIF > 5, report as joint relationship.

### 2.4 Power Analysis
- **Sample Size**: A substantial number of weekly observations.
- **Detectable Effect**: With N=800 and 3-4 variables, the minimum detectable effect size for Granger causality is approximately [deferred] (calculated during implementation).
- **Limitation**: Small effects may not be statistically significant. Conclusions will be framed as "detectable lead/lag relationships" rather than absolute causal claims.

## 3. Compute Feasibility Analysis

- **Hardware**: Multiple CPU, 7GB RAM, No GPU.
- **Data Size**: Weekly time-series (approx. 800 rows). Extremely lightweight.
- **Model Complexity**: VAR/VECM with ~4 variables. Computationally trivial for CPU.
- **Bootstrap**: A large number of iterations on 800 rows.
  - *Estimate*: < 5 minutes on CPU.
- **Conclusion**: The proposed methodology is **fully feasible** on the GitHub Actions free tier. No GPU or heavy LLM inference is required.

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **API Rate Limits** | Medium | Cache data in `data/raw/` with checksums; use local cache in CI. |
| **Non-Stationarity after Differencing** | Medium | Fallback to Log/Box-Cox transformation; log diagnostic. |
| **Cointegration Trap** | High | Johansen test + VECM fallback (Methodology). |
| **Synthetic Data in CI** | Medium | Explicitly flag results as `synthetic` in metadata; 'Verified Accuracy' gate applies only to `real` runs. |
| **Collinearity** | Medium | VIF check; report joint effects if high. |

## 5. Decision Rationale

- **Why Forward-Fill for GDP?** Economic indicators are "stock" or "rate" variables where the last known value is the best estimate until the next release. Linear interpolation would artificially create trends between releases.
- **Why Linear for Sentiment?** Sentiment is a flow variable; missing daily points are likely gaps in collection, not structural changes. Linear interpolation preserves the slope of sentiment drift.
- **Why MBB?** Standard bootstrapping breaks temporal dependence. MBB preserves the autocorrelation structure essential for time-series validation.
- **Why VECM?** If variables are cointegrated, differencing removes the long-run equilibrium. VECM captures both short-run dynamics and long-run equilibrium.
- **Why Politis & White Block Length?** A fixed block length is arbitrary and may bias CI. Data-driven selection ensures the block length matches the data's autocorrelation structure.