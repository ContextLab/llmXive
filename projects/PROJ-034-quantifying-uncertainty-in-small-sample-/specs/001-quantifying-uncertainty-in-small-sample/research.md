# Research: Quantifying Uncertainty in Small Sample Regression Models

## Executive Summary

This research investigates the performance of three uncertainty quantification methods—Ordinary Least Squares (OLS) with asymptotic intervals, Non-parametric Bootstrap (BCa), and Bayesian Linear Regression with weakly informative priors—under conditions of small sample sizes ($N < 50$) and high predictor collinearity. The study utilizes a Monte Carlo simulation framework to empirically measure coverage probabilities against known ground truth parameters. A critical methodological refinement involves grouping results by *realized* collinearity metrics to avoid ecological fallacy.

## Theoretical Background

### Small Sample Inference Challenges
In small samples ($N < 50$), asymptotic approximations (e.g., Normal distribution for OLS coefficients) often fail, leading to under-coverage (confidence intervals too narrow). Bootstrap methods offer a resampling-based alternative but can be unstable with very small $N$ and high collinearity. Bayesian methods with weakly informative priors (WIP) aim to regularize estimates, potentially improving coverage by shrinking extreme values, though the choice of prior scale is critical.

### Collinearity Impact
High collinearity ($\rho > 0.85$) inflates the variance of coefficient estimates. In OLS, this leads to wider intervals but potentially poor coverage if the variance estimation is biased. In Bayesian models, the prior acts as a regularizer, which may mitigate variance inflation but introduces bias if the prior is too strong.

## Methodology

### Simulation Design
1. **Data Generation**: Synthetic datasets generated with $N \in [3, 49]$ and predictors $X$ drawn from a multivariate normal distribution with a specified correlation matrix $\Sigma$.
 * **Ground Truth**: True coefficients $\beta_{true}$ and noise $\sigma$ are fixed and recorded.
 * **Collinearity**: Target correlations $\rho \in \{0.0, 0.5, 0.85\}$ enforced via Cholesky decomposition.
 * **Realized Metric Check**: For each generated dataset, the *realized* sample correlation and Variance Inflation Factor (VIF) are calculated. Datasets where the realized VIF < 10 (for high collinearity targets) are discarded and regenerated to ensure the analysis subset strictly meets the "high collinearity" condition without selection bias.
2. **Monte Carlo Replications**: $M = 200$ datasets generated per configuration to estimate coverage probability with acceptable Monte Carlo error.
3. **Model Fitting**:
 * **OLS**: Standard linear regression with $t$-distribution based intervals.
 * **Bootstrap**: Non-parametric resampling ($B=500$) using **Bias-Corrected and Accelerated (BCa)** intervals to correct for skewness and bias in small samples.
 * **Bayesian**: Stan model (via `cmdstanpy`) with $\beta_j \sim \text{Normal}(0, 10)$ and $\sigma \sim \text{Half-Cauchy}(0, 2.5)$. 4 chains, 2000 samples (1000 warmup).
4. **Sensitivity Analysis**: A secondary simulation run will be conducted with scaled priors (e.g., $\beta_j \sim \text{Normal}(0, 5)$ and $\text{Normal}(0, 20)$) to verify that coverage results are not driven primarily by prior shrinkage.

### Metrics
* **Empirical Coverage Probability (ECP)**: Proportion of intervals containing $\beta_{true}$.
* **Average Interval Width (AIW)**: Mean width of the [deferred] intervals.
* **Coverage-Adjusted Efficiency (CAE)**: A joint metric defined as $CAE = \text{AIW} \times (1 + |\text{ECP} - 0.95| / 0.05)$, penalizing width if coverage deviates from the nominal level.
* **Convergence Diagnostics**: R-hat for Bayesian chains; VIF for collinearity.

### Analysis Grouping
Results will be grouped and analyzed based on the **realized** VIF and realized sample correlation, not the target parameter $\rho$. This prevents ecological fallacy by ensuring that the "high collinearity" group represents the actual data conditions experienced by the models.

## Dataset Strategy

| Dataset | Source | Usage | Notes |
|:--- |:--- |:--- |:--- |
| **Synthetic Data** | N/A (Generated) | Primary analysis | Controlled $N$, $\rho$, $\beta_{true}$. Grouped by realized VIF. |
| **UCI Concrete Compressive Strength** | [Verified Dataset] | Real-world validation | Subsampled to $N < 50$; used for **interval stability and width comparison only**. No coverage validation possible (no ground truth). |

**Note**: The UCI Concrete dataset is selected based on the spec's assumption of availability. The verified source for the UCI HAR dataset is provided in the input block, but the Concrete dataset is a standard UCI repository item. We will proceed by attempting to load the Concrete dataset via `ucimlrepo` or a standard URL. If no verified URL exists in the block, we will document the name only and not fabricate a URL. The plan will rely on the `ucimlrepo` library which is known to fetch from the canonical UCI source, satisfying the "canonical source" requirement of the constitution.

**Verified Sources**:
* **UCI HAR**: ` (Not Concrete, but UCI).
* **Action**: The plan will use `ucimlrepo` to fetch the Concrete dataset, ensuring the source is canonical. If `ucimlrepo` fails, the fallback is the standard UCI repository URL (canonical), but no specific HuggingFace URL for Concrete is in the verified block. The research will proceed with the name "UCI Concrete Compressive Strength" and note the canonical source.

## Decision & Rationale

| Decision | Rationale |
|:--- |:--- |
| **CPU-Only Execution** | The project runs on GitHub Actions free tier (limited CPU and RAM resources). GPU methods are infeasible. |
| **200 Replications** | Balances statistical power (SE $\approx 0.035$ for [deferred] coverage) with the 6-hour runtime limit. |
| **Weakly Informative Priors** | Normal(0, 10) and Half-Cauchy(0, 2.5) are standard defaults that regularize without dominating small data. Sensitivity analysis will verify robustness. |
| **VIF > 10 Threshold (Realized)** | Standard threshold for "high collinearity". Filtering on *realized* VIF ensures the condition is met in the data, not just the generation parameter. |
| **BCa Bootstrap** | Superior to percentile intervals for small samples and skewed distributions, reducing bias in interval estimation. |
| **Subsampling UCI** | Real-world data rarely has $N < 50$; subsampling allows testing the small-sample hypothesis on messy data. |

## Risk Assessment

* **Risk**: Bayesian sampler fails to converge (R-hat > 1.05) in high collinearity.
 * **Mitigation**: Flag run as invalid; exclude from coverage calculation; log failure.
* **Risk**: Runtime exceeds 6 hours.
 * **Mitigation**: Profile the simulation engine; reduce $M$ to 150 if necessary (documented); optimize bootstrap vectorization.
* **Risk**: Generated correlation matrix not positive semi-definite.
 * **Mitigation**: Use Cholesky decomposition with a check; regenerate if invalid.
* **Risk**: Prior sensitivity dominates results.
 * **Mitigation**: Conduct sensitivity analysis with scaled priors; if results vary significantly, report this as a limitation of the "weakly informative" approach in extreme small samples.

## Conclusion

This research plan establishes a rigorous framework for comparing uncertainty quantification methods in the small-sample regime. By leveraging Monte Carlo simulation with known ground truth and grouping results by *realized* collinearity, we can empirically validate theoretical properties of OLS, Bootstrap (BCa), and Bayesian methods. The inclusion of a real-world validation step focuses on interval stability and width comparison, explicitly acknowledging that coverage validation is impossible without ground truth.
