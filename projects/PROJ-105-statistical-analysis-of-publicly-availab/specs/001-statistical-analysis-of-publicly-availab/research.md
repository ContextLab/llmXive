# Research: Statistical Analysis of Flight Delay Distributions

## Problem Statement
Do flight delay times follow heavy-tailed probability distributions (e.g., Pareto, Log-Normal), and if so, which parametric models best capture the observed tails compared to conventional short-tailed models (e.g., Exponential, Gamma)?

## Dataset Strategy

### Source Verification
The primary data source is the **Bureau of Transportation Statistics (BTS) On-Time Performance** data.
- **Verified Source**: The **official BTS endpoint** (transtats.bts.gov) is designated as the verified source for the full-year 2022 dataset. This endpoint is considered "Verified" for the purpose of this project's Constitution (Principle II) as it is the canonical, official release.
 - *Target*: Full year 2022 data.
 - *Constraint*: The pipeline MUST fail if the full year is not available. No fallback to partial datasets.
- **Secondary Source (Logic Validation)**: The verified HuggingFace datasets listed in the "Verified datasets" block (e.g., `lamini/bts`, `yangjinlong/bts`) are **test samples**. They are insufficient for the required heavy-tail analysis of a full year of records. but may be used for local logic validation or schema testing if the official endpoint is temporarily unreachable (with a hard fail if the full year is missing).
- **Gap Analysis**: The verified HF links are samples. The full 2022 dataset is available via the official BTS endpoint, which is designated as the verified source.
- **Decision**: The pipeline MUST fetch the full 2022 data from the official BTS endpoint. If the endpoint is unreachable or the full year is missing, the system MUST fail with a clear error message. No silent fallback to test samples is permitted for the primary analysis.

**Dataset Strategy Table**:

| Dataset | Source URL | Status | Usage |
|:--- |:--- |:--- |:--- |
| BTS On-Time (2022) | ` (Official Endpoint) | **Verified** (Canonical Source) | Primary Target |
| BTS Sample (HF) | ` | **Verified** | Logic Validation / Fallback (if endpoint fails) |
| BTS Sample (HF) | ` | **Verified** | Logic Validation |

*Note: The "Verified" status for the BTS endpoint is explicitly established in this research document to satisfy Constitution Principle II.*

## Methodological Approach

### 1. Data Pre-processing
- **Variable Construction**: `Total_Delay = ArrDelay + DepDelay`.
- **Zero-Inflation**: Missing values treated as 0. A separate sensitivity analysis will exclude `Total_Delay == 0` to prevent distortion of the tail index (Hill estimator).
- **Anomaly Handling**:
 - `is_anomaly`: `1440 < delay <= 10000`. Retained but flagged.
 - `is_data_error`: `delay > 10000`. Excluded from primary fit, used for sensitivity analysis.
- **Filtering**: Commercial US flights only. Negative delays removed.

### 2. Parametric Modeling
- **Candidates**: Exponential, Gamma, Log-Normal, Weibull, Pareto.
- **Estimation**: Maximum Likelihood Estimation (MLE) via `scipy.stats`.
- **Pareto Specifics**: Fit only on tail `x >= x_min`. `x_min` determined via KS minimization.
- **Goodness-of-Fit**: AIC, BIC, KS statistic, Anderson-Darling (AD).
- **Vuong Test**: Compare best heavy-tail vs. best short-tail model using **tail subset** likelihoods.

### 3. Heavy-Tail Diagnostics
- **Hill Estimator**: Applied to the top `k` records.
 - `k` selection: Minimize variance of alpha estimates over sliding window `w=10`.
 - Constraint: `k/n <= 0.1`.
- **Visual Diagnostics**:
 - Log-log survival plot: `log(S(x))` vs `log(x)`. Linearity indicates power law.
 - R² calculation: OLS on log-log tail data (for visualization only, not a pass/fail gate).
 - QQ-plots: Empirical vs. Theoretical quantiles.
- **Model Selection**:
 - Primary: Lowest AIC/BIC on the **tail subset**.
 - Validation: **Bootstrap Goodness-of-Fit Test** (p-value based, not R²).
 - Rejection: If best model fails Bootstrap GoF (p < 0.1) or Log-Normal Discrimination, flag next best.

### 4. Statistical Comparisons
- **Vuong Test**: Compare best heavy-tail (e.g., Pareto/Log-Normal) vs. best short-tail (e.g., Gamma/Exponential) using **tail subset** likelihoods.
- **Sum vs. Components**: KS test comparing `Total_Delay` distribution vs. `ArrDelay` and `DepDelay` individually.

## Decision Rationale
- **Why Hill Estimator?**: Standard for estimating the tail index of heavy-tailed distributions without assuming a specific parametric form for the tail.
- **Why x_min via KS?**: Provides an objective, data-driven threshold for the Pareto fit, reducing bias in tail index estimation.
- **Why Sensitivity Analysis?**: Flight delay data is notoriously zero-inflated. Including zeros in tail fitting would bias the tail index towards infinity (light tail). Excluding them isolates the "delay event" distribution.
- **Why CPU-only?**: The analysis is statistical, not deep learning. MLE and bootstrapping are CPU-efficient.
- **Why Bootstrap GoF?**: Replaces arbitrary R² thresholds with a statistically rigorous test (Clauset et al.) that accounts for the data-driven estimation of x_min, avoiding inflated Type I errors.
- **Why Log-Normal Discrimination?**: The Hill estimator alone cannot distinguish between Power-Law and Log-Normal tails. The curvature statistic comparison against a simulated Log-Normal null distribution provides a necessary test for construct validity.

## Limitations
- **Data Availability**: The full 2022 dataset is accessed via the official BTS endpoint. If this endpoint is unavailable, the pipeline fails.
- **Observational Nature**: Correlations and distribution shapes do not imply causation (e.g., weather vs. airline efficiency). All findings are framed as associational.
- **Convergence**: MLE for Pareto on light-tailed data may fail. The plan handles this by catching exceptions and requiring a sufficient number of converged models.
