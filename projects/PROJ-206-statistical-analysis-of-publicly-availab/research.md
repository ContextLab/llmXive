# Research and Mathematical Formulations

This document details the mathematical foundations of the statistical methods implemented in this project, along with explicit documentation of sanctioned architectural exceptions where implementation choices deviate from the initial project plan to satisfy feature specifications.

## 1. Methodological Formulations

### 1.1 Simple Unweighted Averaging

The simplest baseline forecast aggregates available polls by calculating the arithmetic mean of vote shares for a given candidate within a specific time window (weekly bin).

Let $P_{i,t}$ be the vote share reported by pollster $i$ at time $t$ for a specific candidate. Let $W_k$ denote the set of all polls collected within week $k$. The simple average forecast $\hat{y}_k$ for week $k$ is:

$$ \hat{y}_k = \frac{1}{|W_k|} \sum_{(i,t) \in W_k} P_{i,t} $$

**Assumptions**:
- All polls in the bin are equally reliable.
- Pollster-specific biases are uncorrelated and cancel out in the aggregate.
- Sample sizes do not influence the weight of the observation.

### 1.2 Accuracy-Weighted Averaging (Frequentist)

To improve upon the simple average, we weight polls inversely proportional to the historical Root Mean Squared Error (RMSE) of the pollster. This assumes that pollsters with a history of higher accuracy are more reliable predictors.

Let $RMSE_i$ be the historical RMSE for pollster $i$, calculated on out-of-sample data from previous election cycles. The weight $w_{i,t}$ for a poll $P_{i,t}$ is:

$$ w_{i,t} = \frac{1 / (RMSE_i + \epsilon)}{\sum_{(j, \tau) \in W_k} (1 / (RMSE_j + \epsilon))} $$

Where $\epsilon$ is a small constant (e.g., $10^{-6}$) to prevent division by zero for pollsters with perfect historical scores (or default median weights).

The weighted forecast $\hat{y}_k^{weighted}$ is:

$$ \hat{y}_k^{weighted} = \sum_{(i,t) \in W_k} w_{i,t} P_{i,t} $$

**Key Constraint**: Weights are calculated using a strict temporal split. For election cycle $T$, weights are derived only from cycles $t < T$.

### 1.3 Bayesian Hierarchical Model (Random Walk)

We implement a dynamic Bayesian model where the latent true preference $\theta_t$ evolves over time according to a Random Walk process. This allows the model to adapt to shifts in public opinion rather than assuming a static underlying value.

**Model Structure**:
1. **Latent State Equation (Random Walk)**:
 $$ \theta_t \sim \mathcal{N}(\theta_{t-1}, \sigma_{rw}^2) $$
 Where $\theta_0$ is the initial state (prior) and $\sigma_{rw}^2$ is the process variance (volatility).

2. **Observation Equation**:
 $$ y_{i,t} \sim \mathcal{N}(\theta_t + \beta_i, \tau_i^2) $$
 Where:
 - $y_{i,t}$ is the observed vote share from pollster $i$ at time $t$.
 - $\beta_i$ is the pollster-specific bias term (modeled as a random effect or fixed effect depending on data sufficiency).
 - $\tau_i^2$ is the observation noise, often approximated by the inverse of the sample size $n_{i,t}$ (i.e., $\tau_i^2 \approx \frac{1}{n_{i,t}}$) or a learned parameter.

3. **Priors**:
 - $\sigma_{rw} \sim \text{HalfNormal}(1)$
 - $\beta_i \sim \mathcal{N}(0, \sigma_{bias}^2)$
 - $\sigma_{bias} \sim \text{HalfNormal}(1)$

**Inference**:
We use Markov Chain Monte Carlo (MCMC) with the No-U-Turn Sampler (NUTS) to approximate the posterior distribution $P(\theta_{1:T}, \beta, \sigma | \text{data})$.

**Forecast**:
The forecast for the election day $T_{elec}$ is the posterior mean (or median) of $\theta_{T_{elec}}$, with uncertainty quantified by the 95% Highest Density Interval (HDI).

## 2. Statistical Evaluation Metrics

### 2.1 Diebold-Mariano (DM) Test

To rigorously compare the predictive accuracy of two forecasting methods (e.g., Simple Average vs. Weighted Average vs. Bayesian), we employ the Diebold-Mariano test.

Let $e_{1,t}$ and $e_{2,t}$ be the forecast errors of method 1 and method 2 at time $t$. The loss differential series is $d_t = L(e_{1,t}) - L(e_{2,t})$, where $L$ is a loss function (typically Squared Error or Absolute Error).

The null hypothesis $H_0$ is that the expected loss differential is zero ($E[d_t] = 0$), implying equal predictive accuracy.

The DM statistic is:
$$ DM = \frac{\bar{d}}{\sqrt{\hat{V}(\bar{d})}} $$
Where $\bar{d}$ is the mean of the loss differential and $\hat{V}(\bar{d})$ is the long-run variance of $d_t$, accounting for autocorrelation in the forecast errors.

Under $H_0$, $DM \xrightarrow{d} \mathcal{N}(0, 1)$.

### 2.2 Westfall-Young Step-Down Max-T Correction

When performing multiple pairwise comparisons (e.g., Method A vs B, A vs C, B vs C), the family-wise error rate (FWER) increases. We apply the Westfall-Young step-down max-t procedure to control FWER.

**Procedure**:
1. Calculate the t-statistic for each pairwise comparison.
2. Generate the joint null distribution of the maximum t-statistic via permutation (1000 permutations).
3. Adjust p-values based on the proportion of permutations where the maximum t-statistic exceeds the observed maximum.

This method is superior to Bonferroni correction as it accounts for the correlation structure between the test statistics.

### 2.3 Coverage Reliability

For the Bayesian model, we verify that the 95% credible intervals (CI) actually contain the true election outcome 95% of the time.

Let $I_t$ be the indicator variable that the true outcome $y_t$ falls within the 95% CI of the forecast $\hat{y}_t$.
$$ I_t = \mathbb{1}(L_t \le y_t \le U_t) $$
The empirical coverage is $\hat{p} = \frac{1}{N} \sum I_t$.

We perform a binomial test against the null hypothesis $p_0 = 0.95$ at significance level $\alpha = 0.05$.

## 3. Sanctioned Architectural Exceptions

The following deviations from the initial Project Plan were mandated by the Feature Specification (Spec) to ensure methodological rigor and specific analytical capabilities. These exceptions are documented here as required.

### 3.1 Exception T021: Random Walk vs. Static Parameter
- **Plan Decision**: The initial plan favored a "Static Parameter" model for simplicity.
- **Spec Mandate**: The Spec (FR-005) requires a **Random Walk** hierarchical model to capture temporal dynamics in voter preference.
- **Implementation**: The `src/models/bayesian.py` module implements the Random Walk formulation ($\theta_t \sim \mathcal{N}(\theta_{t-1}, \sigma^2)$) as described in Section 1.3.
- **Rationale**: Polling data exhibits significant time-series dependency. A static model fails to account for late-breaking news or campaign effects. The Random Walk is a minimal dynamic model that balances complexity with the need to track evolving public opinion. This is treated as a hypothesis test: "Does a dynamic model outperform a static one?"

### 3.2 Exception T026: Diebold-Mariano with Westfall-Young Correction
- **Plan Decision**: The initial plan rejected the Diebold-Mariano test for static forecasts, preferring simple RMSE comparison.
- **Spec Mandate**: The Spec (FR-006, SC-003) explicitly requires pairwise Diebold-Mariano tests with Westfall-Young correction to rigorously validate predictive accuracy differences.
- **Implementation**: The `src/evaluation/meta_analysis.py` module implements the DM statistic and a custom permutation-based Westfall-Young step-down max-t correction (1000 permutations).
- **Rationale**: Simple RMSE comparisons do not account for the statistical significance of the difference between models, especially when forecast errors are autocorrelated. The DM test is the standard in time-series forecasting literature for this purpose. The Westfall-Young correction is necessary to maintain statistical validity when comparing multiple model pairs simultaneously.

### 3.3 Exception T009b: Exclusion of RealClearPolitics (RCP)
- **Plan Decision**: The plan initially listed RCP as a potential data source.
- **Spec Mandate**: The Spec (FR-001, Plan's "Verified Accuracy" principle) explicitly excludes RCP data due to concerns regarding the verification of their aggregation methodology and potential bias.
- **Implementation**: The `src/data/download.py` module includes a `log_rcp_exclusion` function that explicitly logs a warning citing the "Verified Accuracy" principle. No code attempts to fetch RCP data.
- **Rationale**: Data integrity is paramount. FiveThirtyEight's methodology is transparent and reproducible. RCP's aggregation methods are proprietary and less transparent. Excluding RCP ensures the model is built on a foundation of verified, auditable data sources.

## 4. Conclusion

This project implements a comprehensive suite of forecasting methods, ranging from simple baselines to advanced Bayesian hierarchical models. The choice of methods, particularly the Random Walk model and the rigorous Diebold-Mariano evaluation with Westfall-Young correction, represents a deliberate architectural decision to prioritize statistical robustness and dynamic adaptability over the simplicity of the initial plan. These decisions are documented as sanctioned exceptions to ensure transparency and traceability.

All data sources are restricted to publicly available, verified aggregates (FiveThirtyEight), and all code is designed to run on CPU-only infrastructure with constrained resources.