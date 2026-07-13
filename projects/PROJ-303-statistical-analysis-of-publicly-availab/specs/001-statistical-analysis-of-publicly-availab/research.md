# Research: Statistical Analysis of Publicly Available Weather Data for Extreme Event Prediction

## 1. Research Question & Hypotheses

**Primary Question**: How does spatial dependence structure the tail behavior of localized extreme weather events, and what is the predictive gain of modeling this dependence over independent station assumptions?

**Hypotheses**:
- **H1**: Modeling spatial dependence (Spatial-GPD with Gaussian Copula) will yield a statistically significant reduction in Brier score for exceedance prediction compared to independent GPD models.
- **H2**: The spatial model will demonstrate lower RMSE for intensity estimation in regions with high station density due to borrowing strength from neighbors.
- **H3**: In areas with idiosyncratic local extremes (low spatial correlation), the independent model will perform comparably to the spatial model (null result).

## 2. Dataset Strategy

**Source Selection**:
The project requires daily precipitation data for a dense sub-region (Northeast USA) spanning 2000–2020.
- **Selected Dataset**: `NOAA_GHCN_Daily` (raw daily records).
- **Verified URL**: ` (Primary Source).
- **Data Availability Check**: The pipeline MUST query the source to verify the presence of a continuous 2000–2020 time series. If the specific file cited (e.g., `train-00000-of-00001.parquet`) is partial, the pipeline MUST halt with `DATA_INCOMPLETE` and log the missing years. No substitution or assumption is permitted.
- **Variable Fit Verification**: The dataset must contain `station_id`, `date`, `prcp` (precipitation), `latitude`, and `longitude`. If any required variable is missing, the plan explicitly states this mismatch and halts.

**Data Partitioning**:
- **Training Set**: 2000–01-01 to 2015-12-31. Used for:
 - Calculating the 95th percentile threshold per station.
 - Fitting GPD and Spatial-GPD parameters.
- **Test Set**: 2019-01-01 to 2020-12-31. Used for:
 - Evaluating Brier scores and RMSE.
 - Generating diagnostic plots.
- **Exclusion**: 2016–2018 (gap) to prevent temporal leakage and assess model stability.

**Imputation Strategy**:
- **Linear Interpolation**: For gaps < 30 days.
- **Exclusion**: Stations with >15% total missing data OR any contiguous gap > 30 days.
- **Justification**: Linear interpolation preserves short-term trends without introducing artificial extremes. Long gaps are unreliable for extreme value analysis.

## 3. Statistical Methodology

### 3.1 Extreme Event Definition (Peaks-Over-Threshold)
- **Threshold ($u$)**: 95th percentile of daily precipitation calculated **strictly** on the Training Set (2000–2015) for each station.
- **Exceedance**: $X > u$.
- **Magnitude**: $Y = X - u$ (excess over threshold).
- **Rationale**: POT is standard for extreme value analysis, allowing more data points than Block Maxima while focusing on the tail.

### 3.2 Baseline Model: Independent GPD
- **Method**: Fit Generalized Pareto Distribution (GPD) to excesses $Y$ for each station independently.
- **Parameters**: Shape ($\xi$), Scale ($\sigma$).
- **Library**: `scipy.stats.genpareto`.
- **Prediction**: Probability of exceedance $P(X > x) = 1 - F_{GPD}(x-u)$.

### 3.3 Spatial Model: Spatial-GPD with Gaussian Copula
- **Method**: Model the joint distribution of extremes using a Spatial-GPD structure with a Gaussian Copula for dependence.
- **Covariance**: Matérn covariance function for spatial dependence.
- **Estimation**:
 1. Fit marginal GPDs independently for all stations.
 2. Estimate the dependence structure (Kendall's tau variogram) from the marginal residuals.
 3. Fit the Gaussian Copula parameters to the variogram.
- **Rationale**: Spatial-GPD is a robust, computationally feasible alternative to Brown-Resnick for moderate station networks (N~100) on CPU. It captures tail dependence while being tractable.
- **Constraint**: If fitting fails due to time (> 6h) or convergence, fallback to Independent GPD (FR-008).

#### 3.3.1 Prediction Mechanism (Brier Score Derivation)
To calculate the Brier score for the Spatial-GPD model:
1. **Conditional Distribution**: For a target station $s$ and a set of neighbors $N_s$ with observed exceedances $y_{N_s}$, the conditional distribution of $y_s$ is derived from the Gaussian Copula density:
 $$ f(y_s | y_{N_s}) = \frac{f_{Copula}(F_1(y_1),..., F_N(y_N))}{\prod_{i \neq s} f_i(y_i)} $$
 where $F_i$ are the marginal GPD CDFs.
2. **Exceedance Probability**: The probability of exceedance $P(X_s > x)$ for a threshold $x$ is calculated by integrating the conditional density:
 $$ P(X_s > x | y_{N_s}) = \int_{x-u_s}^{\infty} f(y_s | y_{N_s}) dy_s $$
3. **Brier Score**: This probability $f_i$ is used in the Brier score formula. This ensures the spatial model's contribution is non-trivial and derived from the joint dependence structure.

### 3.4 Evaluation Metrics
- **Brier Score**: For binary exceedance prediction ($0/1$). Lower is better.
 $$ Brier = \frac{1}{N} \sum_{i=1}^N (f_i - o_i)^2 $$
 where $f_i$ is predicted probability, $o_i$ is observed outcome.
- **RMSE**: For intensity prediction (magnitude of exceedance).
- **Coverage**: Empirical coverage of 95% confidence intervals for regional sums (via block bootstrap).

### 3.5 Cross-Validation: Global Dependence, Local Prediction
- **Method**: Leave-One-Station-Out (LOSO) with a specific adaptation for computational feasibility.
- **Procedure**:
 1. **Global Fit**: Estimate the spatial dependence structure (variogram/Copula parameters) ONCE using the full training set (N stations). This is the "Global Dependence" step.
 2. **Local Prediction**: For each held-out station $s$:
 - Use the *global* dependence parameters.
 - Use the *neighbors'* observed extremes to predict the distribution of $s$.
 - (Optional) Re-fit the marginal GPD for $s$ if data allows, or use the global marginal if $s$ is excluded.
- **Goal**: Assess generalization to unseen locations without the prohibitive cost of re-fitting the dependence model N times. This avoids the instability of re-estimating the variogram on N-1 stations.

### 3.6 Fallback Protocol
- **Condition**: If the Spatial-GPD model fails to converge or exceeds the 5.5-hour time limit.
- **Action**:
 1. Log `FALLBACK: CONVERGENCE_ERROR` or `FALLBACK: TIMEOUT`.
 2. Use the Independent GPD model for the affected iterations.
 3. **Reporting**: In the final report, explicitly state: "Spatial model failed; Independent GPD reported as 'Best Achievable'. Comparison for 'Predictive Gain' is invalid."
- **Rationale**: This distinguishes between a scientific null result (no gain) and a computational failure (model didn't run), preventing false conclusions.

## 4. Compute Feasibility & Risk Mitigation

**Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM, No GPU).
**Risk**: Spatial-GPD fitting is computationally intensive ($O(N^2)$).
**Mitigation**:
1. **Subsampling**: If time > 2 hours, subsample the time series (e.g., every 5th day) to reduce $T$.
2. **Fallback**: If spatial model fails to converge within 5.5 hours, switch to Independent GPD and log a warning.
3. **Library Choice**: Use `scipy` and `numpy` for core math. Avoid heavy deep learning frameworks. If `spatial-extremes` (R) is required, use `rpy2`, but prefer the pure Python implementation for CI compatibility.

## 5. Decision Log & Rationale

| Decision | Rationale |
|----------|-----------|
| **Use 95th Percentile** | Community standard for "extreme" in hydrology; balances data availability with tail focus. |
| **Training: 2000–2015, Test: 2019–2020** | Ensures no temporal leakage; accounts for climate trends by re-calculating thresholds on the most recent relevant training window. |
| **Spatial-GPD over Brown-Resnick** | Brown-Resnick is computationally infeasible for N~100 on CPU. Spatial-GPD with Gaussian Copula is a scientifically sound, tractable alternative that captures tail dependence. |
| **Global Dependence, Local Prediction for LOSO** | Essential for validating spatial generalization while respecting the 6-hour compute limit. Re-fitting dependence N times is impossible. |
| **Fallback to GPD** | Required by FR-008 to ensure pipeline completion on CI; null result (no gain) is a valid scientific outcome, but must be distinguished from failure. |
| **Data Availability Check** | Required by Constitution Principle II to ensure the dataset actually contains the full 2000-2020 range before proceeding. |