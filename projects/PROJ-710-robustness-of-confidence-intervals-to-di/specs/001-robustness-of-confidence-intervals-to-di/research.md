# Research: Robustness of Confidence Intervals to Differential Privacy Noise

## 1. Research Question & Hypotheses

**Primary Question**: How does the magnitude of differential-privacy noise (controlled by $\epsilon$) affect the frequentist coverage probability of 95% confidence intervals for simple means and linear-regression coefficients?

**Hypotheses**:
1. **H1**: As $\epsilon$ decreases (tighter privacy), the empirical coverage probability of standard 95% CIs will degrade significantly below the nominal [deferred] level.
2.  **H2**: Bias-correction and variance-inflation adjustments will restore coverage closer to the nominal level for moderate $\epsilon$ values, but may fail for very low $\epsilon$.
3.  **H3**: The degradation effect will be statistically significant (GLM p-value < 0.05) and differ by noise type (Laplace vs. Gaussian).

## 2. Dataset Strategy

The project relies on a **Synthetic Population** approach for ground truth, supplemented by real-world datasets for the noisy sample generation to ensure realistic data distributions.

### Ground Truth Generation
* **Method**: Generate a synthetic population of $N \ge [deferred]$ records for each target distribution (Normal, Skewed, Multivariate Normal) mimicking the statistics of the UCI Adult, Iris, and Wine Quality datasets.
*   **Rationale**: Real datasets do not have "known" true parameters. To measure coverage (True Parameter $\in$ CI), we must generate a population where parameters are known by construction. This satisfies FR-002 and FR-008.
*   **Source**: Generated internally via `code/data/synthetic_pop.py`. No external URL required.
*   **Ground Truth Definition**: The "True Parameter" is the **population mean** (or regression coefficient) calculated from the full N=1M synthetic population. This value is **fixed** before any sampling or noise injection.

### Noisy Sample Sources
The simulation will draw samples from the synthetic population and then add DP noise. The *distributions* of the synthetic data will be calibrated to match the marginal statistics of the following real-world datasets:
*   **UCI Adult**: Income prediction (numeric attributes).
*   **UCI Iris**: Flower measurements.
*   **UCI Wine Quality**: Chemical properties.

*Note on Verified Datasets*: The provided "Verified datasets" block contains URLs for specific HuggingFace splits (e.g., `udayl/UCI_HAR`, `ucinlp/drop`). However, **none of these verified URLs correspond to the standard UCI Adult, Iris, or Wine Quality datasets** required for this specific simulation's distribution calibration.
*   **Decision**: We will **not** cite the verified URLs for Adult/Iris/Wine as they are mismatched. Instead, we will generate the synthetic population using distributions that *approximate* the known statistics of Adult/Iris/Wine (e.g., mean/variance of Age, Sepal Length, Alcohol content) as documented in the UCI Machine Learning Repository (public knowledge).

## 3. Methodology

### 3.1. Two-Level Simulation Design
To correctly estimate **Coverage Probability**, we distinguish between two loops:
1.  **Outer Loop (Monte Carlo Replications)**:
    *   **Goal**: Estimate the probability that a CI covers the true parameter.
    *   **Action**: Generate $N_{sim} = 1,000$ *independent* noisy samples for each condition.
    *   **Metric**: Proportion of these 1,000 CIs that contain the fixed Ground Truth.
2.  **Inner Loop (Bootstrap Resampling)**:
    *   **Goal**: Construct a single 95% CI for *one* noisy sample.
    *   **Action**: Draw $B = 1,000$ bootstrap resamples from the *noisy sample*.
    *   **Output**: One CI (Lower, Upper) per noisy sample.

*Note*: The "1,000 bootstrap resamples" mentioned in the spec refers to the **Inner Loop**. The "1,000 Monte Carlo replications" refers to the **Outer Loop**.

### 3.2. Differential Privacy Noise Calibration
*   **Mechanism**: Global Sensitivity Mechanism.
*   **Sensitivity ($\Delta f$)**: Calculated based on known global bounds (e.g., normalized [0, 1] or domain-specific max ranges).
*   **Noise Distributions**:
    *   **Laplace**: $Noise \sim Laplace(0, \Delta f / \epsilon)$.
    *   **Gaussian**: $Noise \sim N(0, \sigma^2)$ where $\sigma = \Delta f \sqrt{2 \ln(1.25/\delta)} / \epsilon$.
*   **Implementation**: `numpy.random.laplace` and `numpy.random.normal`.

### 3.3. Confidence Interval Construction & Adjustments
*   **Base Method**: Non-parametric Bootstrap (Percentile method) on the noisy sample.
*   **Bias Correction**:
    *   **Mean**: Laplace noise is unbiased ($E[\hat{\mu}_{noisy}] = \mu$). No bias correction needed for the mean.
    *   **Regression**: If noise is added to predictors (Errors-in-Variables), the OLS estimator is biased. We will apply a bias-correction factor derived from the noise variance to the point estimate (e.g., $\hat{\beta}_{corrected} = \hat{\beta}_{noisy} \times \frac{Var(X)}{Var(X) + Var(Noise)}$).
*   **Variance Inflation**:
    *   The bootstrap distribution of the noisy mean naturally includes both sampling variance and noise variance.
    *   **Adjustment**: If the theoretical noise variance is known, we can widen the CI by a factor $\sqrt{1 + \frac{Var(Noise)}{Var(\hat{\mu}_{sample})}}$ if the bootstrap underestimates the total variance (e.g., in small samples). Alternatively, we use the bootstrap SE directly if it captures the noise.
    *   **Decision**: We will compute the bootstrap SE on the noisy data. If the theoretical noise variance is large, we will apply a post-hoc width adjustment to ensure the CI accounts for the full noise distribution.

### 3.4. Statistical Analysis (GLM)
*   **Model**: Generalized Linear Model with Binomial family and Logit link.
*   **Response**: Binary indicator (1 if CI covers **Fixed Ground Truth**, 0 otherwise) per Outer Loop replication.
*   **Predictors**: $\epsilon$, Noise Type, Statistic Type, Adjustment Method.
*   **Goal**: Test significance of $\epsilon$ and interaction terms.

## 4. Compute Feasibility & Constraints

*   **Hardware**: CPU-only (GitHub Actions free tier).
*   **Memory**: 7 GB RAM.
    *   *Strategy*: Process one condition at a time. Store only the final CI bounds (a representative subset of rows) in memory/disk.
*   **Runtime**: 6 hours.
    *   *Estimate*: 30,000 CIs $\times$ 1,000 bootstrap resamples = 30M operations.
    *   *Optimization*: Use vectorized numpy for resampling (e.g., `np.random.choice` with replacement on the whole array at once).

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Mismatch** | High | Use synthetic populations matching known stats. Do not fabricate URLs. |
| **Collinearity** | Medium | Generate multivariate normal data with known covariance; check condition number. |
| **NaNs at Low $\epsilon$** | High | Clamp noise or log warning; skip CI calculation if data is randomized. |
| **Runtime > 6h** | High | Vectorize bootstrap. If needed, reduce $N_{sim}$ to 500 (documented). |

## 6. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Two-Level Simulation** | Required to distinguish CI construction (Inner) from Coverage Estimation (Outer). |
| **Fixed Ground Truth** | Ensures the target of inference is independent of the sample realization. |
| **GLM (Binomial)** | Statistically appropriate for binary coverage outcomes. |
| **No External URLs** | Verified dataset list does not contain standard Adult/Iris/Wine. |