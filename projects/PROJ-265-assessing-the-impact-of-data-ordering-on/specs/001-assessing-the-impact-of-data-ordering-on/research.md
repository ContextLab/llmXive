# Research: Assessing the Impact of Data Ordering on Bootstrapping Results

## Research Question
How does temporal autocorrelation in synthetic AR(1) time-series data degrade the empirical coverage probability of standard non-parametric bootstrap confidence intervals, and can random shuffling isolate the variance component of this error?

*Note: The original research question included validation on UCI Power data. Due to the lack of a verified source, this phase is blocked. The study now focuses exclusively on synthetic validation.*

## Background & Theory
Standard non-parametric bootstrapping assumes that observations are Independent and Identically Distributed (IID). In time-series data with positive autocorrelation (e.g., AR(1) processes), this assumption is violated. Resampling with replacement from ordered data preserves the local autocorrelation structure but fails to capture the true variance of the mean estimator, leading to confidence intervals that are too narrow (under-coverage).

**Key Hypotheses**:
1. **H1**: As the autoregressive coefficient $\phi$ increases, the empirical coverage probability of the standard bootstrap (ordered) will decrease monotonically below the nominal [deferred] level.
2. **H2**: Randomly shuffling the data (breaking temporal dependence) will restore coverage to $\approx$ [deferred], confirming that the bias is due to order, not distribution shape.
3. **H3**: The difference in coverage between Ordered and Shuffled conditions isolates the *variance estimation error* of the bootstrap, as shuffling preserves the sample mean (and thus the bias) but removes autocorrelation.

## Dataset Strategy

The research utilizes synthetic data for controlled validation. The real-world analysis is blocked.

| Dataset Name | Type | Purpose | Source / Loader | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **Synthetic AR(1)** | Synthetic | Controlled testing of $\phi \in [0.0, 0.9]$ | `numpy` generator (code) | N/A (Generated) |
| **UCI Power (Spec)** | Real-world | **BLOCKED** | **No verified source available** | **BLOCKED** |

### ⚠️ Real-World Analysis Blocked
The specification requires the **UCI Individual Household Electric Power Consumption** dataset. The "Verified datasets" block provided in the input **does not contain a verified source** for this dataset.
- **Action**: The plan explicitly **SKIPS** the real-world analysis phase (US-3).
- **Rationale**: Substituting a different dataset (e.g., UCI HAR) would violate construct validity, as the autocorrelation structures of human activity signals differ fundamentally from power consumption. Furthermore, Principle II (Verified Accuracy) prohibits using unverified data sources.
- **Impact**: The study will only report findings on synthetic AR(1) processes. No claims will be made about generalizability to specific real-world domains.

## Methodology

### Phase 1: Synthetic Simulation (US-1, US-2)
1.  **Data Generation**: Generate $K=1,000$ independent AR(1) time series for each $\phi \in \{0.0, 0.1, \dots, 0.9\}$ and $N \in \{50, 100, 200\}$.
    - Model: $X_t = \phi X_{t-1} + \epsilon_t$, where $\epsilon_t \sim \mathcal{N}(0, 1)$.
    - Theoretical Mean: 0.
2.  **Standard Bootstrap (Ordered)**: For each series, compute 95% CI using a resampling procedure.
3.  **Standard Bootstrap (Shuffled)**: For each series, randomly permute the data, compute 95% CI using 1,000 resamples.
4.  **Coverage Calculation**: Count how many CIs contain 0. Calculate empirical coverage for both conditions.
5.  **Statistical Test**: Perform **McNemar's Test** on the contingency table of coverage outcomes (Covered/Not Covered) for Ordered vs. Shuffled conditions *per series*. This accounts for the paired nature of the data (same series, different permutation).

### Bias vs. Variance Decomposition
- The sample mean $\bar{X}$ of an AR(1) process is a biased estimator of the true mean (0) when $\phi > 0$ and $N$ is finite.
- The CI is constructed as $\bar{X} \pm z \cdot SE_{boot}$.
- If the CI misses 0, it could be due to:
  1.  **Bias**: $\bar{X}$ is far from 0.
  2.  **Variance Error**: $SE_{boot}$ is too small.
- **Decomposition Strategy**: The **Shuffled** condition removes autocorrelation but preserves $\bar{X}$. Thus, the coverage drop in the Shuffled condition relative to [deferred] is primarily due to **Bias**. The *additional* drop in the **Ordered** condition (Ordered Coverage < Shuffled Coverage) is attributed to **Variance Error** (failure of bootstrap to capture true variance).
- **Metric**: We report the difference: $\Delta Coverage = Coverage_{shuffled} - Coverage_{ordered}$. This isolates the degradation caused specifically by the violation of the independence assumption.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: With 10 $\phi$ levels and 3 sample sizes, we perform 30 hypothesis tests. We will apply a **Bonferroni correction** to the p-values from McNemar's test to control family-wise error rate.
- **Power Analysis**: We assume [deferred] trials per condition is sufficient to detect a coverage drop of >5% with high power.
- **Causal Inference**: This is a controlled simulation. We claim **causal** evidence that $\phi$ drives coverage drop, as $\phi$ is the only manipulated variable.
- **Collinearity**: In AR(1), $X_t$ and $X_{t-1}$ are collinear. We do **not** claim independent effects of lag; we measure the aggregate effect of the process.
- **Measurement Validity**: The AR(1) generator is the ground truth. The coverage metric is the standard validity measure for CIs.
- **Paired Data Handling**: The Ordered and Shuffled versions of a series are paired. A **Two-Proportion Z-Test** (which assumes independent groups) is **incorrect**. **McNemar's Test** is used instead.

## Feasibility & Compute Constraints
- **Runtime**: [deferred] trials $\times$ 10 $\phi$ $\times$ 3 $N$ = A large number of bootstrap runs. Each run takes a short duration on CPU. Total estimated time: ~ seconds (a few minutes) + I/O. Well within 6-hour limit.
- **Memory**: Storing a large number of series of moderate size is negligible.
- **Dependencies**: `statsmodels`, `scipy`, `numpy` are CPU-only and compatible with GitHub Actions free tier.

## Limitations
- **Real-World Data**: The specific UCI Power dataset is not in the verified list. The analysis is **blocked** for this phase. No proxy is used to avoid invalid generalizations.
- **Bias Confounding**: The coverage drop measures the combined effect of bias and variance error. However, the Shuffled baseline allows us to isolate the variance component as the *difference* between conditions.