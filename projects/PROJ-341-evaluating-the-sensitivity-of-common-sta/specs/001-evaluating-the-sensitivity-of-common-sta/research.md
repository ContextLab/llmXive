# Research: Evaluating the Sensitivity of Common Statistical Tests to Dataset Size

## Executive Summary

This research plan outlines the methodology to empirically determine the reliability thresholds of t-tests, ANOVA, and chi-squared tests under small sample sizes. By simulating 10,000+ iterations per condition across $n=5$ to $n=500$, we will map the deviation of Type I error rates from the nominal 0.05 level and the drop in power (Type II error) for effect sizes $d \in \{0.2, 0.5, 0.8\}$. The study addresses the critical gap in practical guidance for researchers working with limited data, identifying the specific sample size where these tests become statistically unreliable.

## Methodology

### Simulation Design

The core of this study is a Monte Carlo simulation framework.
1. **Data Generation**: Synthetic datasets will be generated for three test types:
 * **t-test**: Two independent groups drawn from normal distributions $N(\mu_1, \sigma^2)$ and $N(\mu_2, \sigma^2)$.
 * **ANOVA**: Three or more groups drawn from normal distributions with varying means.
 * **Chi-squared**: Categorical data generated from multinomial distributions with known probabilities.
2. **Conditions**:
 * **Sample Size ($n$)**: Grid from 5 to 500 in increments of 5 (100 conditions).
 * **Effect Size**: Small ($d=0.2$), Medium ($d=0.5$), Large ($d=0.8$) for continuous tests; probability shifts for categorical.
 * **Hypothesis State**: Null ($H_0$: effect=0) and Alternative ($H_1$: effect>0).
 * **Iterations**: [deferred] per condition to ensure binomial variance stability ($\pm 0.005$ margin).
3. **Statistical Tests**:
 * **t-test**: Welch's t-test (robust to unequal variances) and Student's t-test.
 * **ANOVA**: One-way ANOVA with F-test.
 * **Chi-squared**: Pearson's chi-squared test with Yates' continuity correction or Fisher's Exact Test fallback for expected cell counts < 5 (FR-007).
4. **Error Calculation**:
 * **Type I Error**: Proportion of $p < 0.05$ when $H_0$ is true.
 * **Type II Error**: Proportion of $p > 0.05$ when $H_1$ is true (Power = $1 - \beta$).
 * **Confidence Intervals**: 95% Wilson score intervals for all error rate estimates (FR-003).

### Threshold Identification

Thresholds will be identified using the following criteria (FR-004):
* **Type I Reliability**: The smallest sample size $n$ where the **upper bound** of the 95% CI for Type I error is $\le 0.06$ (i.e., the test is no longer significantly liberal). This identifies the point where the test stops inflating Type I error.
* **Power Reliability**: The smallest sample size $n$ where the **lower bound** of the 95% CI for Power **exceeds 0.80**. This identifies the first point where the test achieves sufficient power with statistical confidence.

### Validation Strategy

To ensure external validity (FR-006), the simulation results will be compared against real-world small-sample datasets.
* **Datasets**: UCI HAR (Human Activity Recognition) and Shopper (from verified sources).
* **Method**: Apply the same statistical tests to these datasets. Compare the **observed p-value distribution shape** against the **theoretical distribution** expected under the null (Uniform) or alternative (Skewed) assumptions derived from the simulation.
* **Metric**: Kolmogorov-Smirnov (KS) distance statistic to measure alignment (SC-003).
* **Note on Ground Truth**: Real-world datasets do not have known ground truth for effect sizes. Therefore, validation does not claim to verify "truth" but rather checks if the test behaves **consistently** with statistical expectations (e.g., uniform p-values under the null hypothesis) for the given sample size.

## Dataset Strategy

The project relies on the following verified datasets for validation. **Note**: No fabricated URLs are used. The synthetic data is generated internally.

| Dataset Name | Source / Verified URL | Usage |
|:--- |:--- |:--- |
| UCI HAR (Human Activity Recognition) | `https://archive.ics.uci.edu/dataset/231/human+activity+recognition+using+smartphones` (Verified via `ucimlrepo`) | Validation of t-test/ANOVA on real small-sample sensor data. |
| Shopper | ` (Verified via HuggingFace) | Validation of chi-squared on real categorical data. |

**Critical Note on Dataset Availability**:
* **Action**: The implementation will load these datasets using `ucimlrepo` (for UCI HAR) and `datasets` (for Shopper).
* **Constraint**: Do NOT invent a URL. The URLs above are from the `Verified datasets` block.
* **Fallback**: If a loader fails, the research report will explicitly state that validation for that specific dataset could not be performed, and the analysis will proceed with the simulation results only, noting this limitation.

**Dataset Variable Fit Check**:
* **Requirement**: The spec requires "ground truth" or "known effect direction" for validation.
* **Reality**: Real-world datasets do not have known ground truth for statistical tests (unlike simulation).
* **Resolution**: As stated in the **Assumptions** section of the spec, we will compare the **observed p-value distribution shape** against the **theoretical expectation** (e.g., Uniform for Null) to assess consistency, acknowledging that real-world ground truth is unknown.

## Statistical Rigor & Methodological Constraints

### Multiple Comparison Correction
Since multiple tests are run across many sample sizes and effect sizes, family-wise error rate (FWER) control is critical.
* **Method**: The Benjamini-Hochberg procedure is **NOT** applied to the set of p-values generated in the simulation. The simulation generates a distribution of p-values to *estimate* an error rate (a proportion). The error rate itself is the metric of interest, not a hypothesis test requiring FDR correction.
* **Threshold Identification**: The threshold identification (FR-004) relies on Confidence Intervals (Wilson), which already account for variance. No additional FDR correction is needed for the aggregate error rate estimation.

### Sample Size & Power Justification
* **Iterations**: [deferred] iterations per condition ensures a margin of error of $\approx \pm 0.005$ for $\alpha=0.05$ (Binomial variance $\sqrt{p(1-p)/N}$).
* **Power**: The simulation itself *measures* power; it does not require a priori power calculation for the simulation design, as the "power" is the output metric.

### Causal Inference & Assumptions
* **Observational Nature**: The simulation is a controlled experiment (parameter sweep), not an observational study. Causal claims about the *relationship between sample size and error rate* are valid within the simulation context.
* **Generalizability**: Claims about real-world reliability are associational and depend on the assumption that real data follows the simulated distributions (normality, multinomial). The validation step (FR-006) tests this assumption by checking for consistency of distribution shape.

### Measurement Validity
* **Instruments**: Standard `scipy.stats` and `statsmodels` implementations are used, which are widely validated.
* **Collinearity**: In ANOVA and t-tests, predictors are defined by group membership (dummy variables), so collinearity is handled by the design matrix construction.

## Compute Feasibility & Optimization

The project must run on a GitHub Actions free-tier runner with standard CPU resources, sufficient RAM, and a 6-hour timeout.

* **Vectorization**: All synthetic data generation and statistical testing will be vectorized using `numpy` and `scipy`. Loops will be minimized.
* **Memory Management**: Data will be processed in **batches** (e.g., [deferred] iterations at a time) to keep memory usage low. Results will be appended to CSVs rather than stored in large in-memory arrays.
* **Parallelization**: `joblib` or `multiprocessing` will be used to parallelize the simulation across the 2 available CPU cores.
* **Algorithm Choice**:
 * **t-test/ANOVA**: Use `scipy.stats` which is highly optimized.
 * **Chi-squared**: Use `scipy.stats.chi2_contingency` with `correction=True`. For small expected counts, implement a fallback to `scipy.stats.fisher_exact`.
* **Runtime Estimate**:
 * Total conditions: $100 \text{ (n)} \times 3 \text{ (tests)} \times 3 \text{ (effects)} \times 2 \text{ (hypotheses)} = 1,800$ conditions.
 * Total iterations: $[deferred] \times [deferred] = 18,000,000$.
 * **Conservative Estimate**: Assuming a batch of [deferred] iterations takes ~2-5 seconds (including overhead), total time $\approx [deferred] \times 3 \text{ seconds} \approx [deferred] \text{ seconds}$ (1.5 hours). Even with overhead, this is well within the 6-hour limit.
 * **Optimization**: If runtime exceeds estimates, the number of iterations per condition can be reduced to 5,000 (still $\pm 0.007$ margin) or the sample size grid can be coarsened (e.g., increments of 10).