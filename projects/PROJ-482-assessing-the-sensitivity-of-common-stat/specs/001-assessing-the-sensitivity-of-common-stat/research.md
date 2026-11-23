# Research: Assessing the Sensitivity of Common Statistical Tests to Dataset Size

## Research Question
How do Type I and Type II error rates of common statistical tests (t-test, ANOVA, chi-squared) vary as a function of sample size and underlying data distribution (Normal, Uniform, Log-Normal)?

## Methodology Overview

### 1. Data Generation Strategy
We will generate synthetic datasets with known ground truth parameters.
- **Distributions**: Normal, Uniform, Log-Normal.
- **Sample Sizes**: 20 points ranging from n=10 to n=1000 (log-spaced).
- **Hypotheses**: 
  - Null ($H_0$): Effect size = 0.0.
  - Alternative ($H_1$): Effect size = 0.5 (Cohen's d equivalent).
- **Validation**: Every generated dataset will be validated against its theoretical parameters (mean, variance, skewness) before testing. If deviation exceeds tolerance **1e-6**, the generation is retried or flagged.
- **No External Data Fetch**: This project relies **exclusively** on synthetic data. No external data fetch is performed or required. This aligns with Constitution Principle VI (Ground-Truth Validation) and avoids access-gated data issues.

### 2. Simulation Engine
- **Tests**: Independent t-test, One-way ANOVA, Chi-squared test of independence.
- **Adaptive Replication**: Start with a sufficient number of replicates. Calculate 95% CI width for the error rate. If width > 0.01, **add a sufficient number of replicates** until convergence.
- **Chi-Squared Handling**: If expected cell counts < 5, automatically switch to **Fisher's Exact Test** to maintain validity.
- **Error Classification**: 
  - Type I: Reject $H_0$ when $H_0$ is true (p < 0.05).
  - Type II: Fail to reject $H_0$ when $H_1$ is true (p ≥ 0.05).
- **Validation**: The validation gate checks for the **presence and correctness of results** (error rates), not the implementation detail of a streaming pipeline.

### 3. Analysis & Modeling
- **Aggregation**: Compute mean error rates and **non-parametric bootstrap** 95% CIs (A sufficient number of resamples) for each configuration.
- **Visualization**: Plot error rate vs. sample size, faceted by distribution and test type. "Publication-ready" defined as high-resolution (300 DPI), labeled axes, vector format (SVG).
- **Regression**: Fit a **Binomial GLM** to predict the **observed error rate** (proportion) using predictors: **natural log** of sample size, distribution type, and test type.
  - *Metric*: **Cox-Snell/Nagelkerke pseudo-$R^2$** (appropriate for Binomial GLM).
  - *Deviation*: Calculated post-hoc as |observed rate - 0.05|.
  - *Note*: The model predicts the rate, not the deviation magnitude. The deviation is a derived metric.
- **Power Curves**: A single, unified theoretical power curve calculation task is implemented for all test types to avoid duplication.

## Dataset Strategy

Since this project relies on **synthetic data** with known ground truth (Constitution Principle VI), no external dataset fetch is required or possible. The "dataset" is generated on-the-fly by `code/data_generator.py`.

| Dataset Name | Source Type | Access Method | Justification |
|--------------|-------------|---------------|---------------|
| Synthetic Normal/Uniform/Log-Normal | Generated Locally | `numpy.random` | Required for controlled ground-truth validation (FR-001). External datasets cannot guarantee the exact effect sizes and distribution shapes needed for this sensitivity analysis. |

**Note on Data Availability**: The project explicitly avoids external data fetches (e.g., ADNI, HCP) because they are access-gated or irrelevant to the controlled simulation design. This aligns with the "Data Hygiene" and "Ground-Truth Validation" principles.

## Statistical Rigor & Assumptions

### Multiple Comparisons
The study runs multiple tests across configurations. While we do not apply a family-wise error correction to the *simulation results* themselves (as we are estimating the true error rate, not testing a single hypothesis), we will report the full matrix of results to allow readers to assess the global behavior.

### Sample Size & Power
- **Minimum Replicates**: 1,000 (ensures standard error of error rate $\approx \sqrt{ \times 0.95 / 1000} \approx 0.007$).
- **Adaptive Stopping**: Ensures the final estimate has a CI width $\le 0.01$, providing high precision even for small sample sizes where variance is higher.

### Causal/Associational Claims
This is a simulation study. Claims are strictly about the *behavior of the statistical tests* under defined conditions, not about real-world phenomena. No causal inference is claimed.

### Measurement Validity
- **Instruments**: Standard statistical tests (t-test, ANOVA, Chi-squared) implemented via `scipy.stats` and `statsmodels`.
- **Validation**: The generator verifies that the empirical moments of the synthetic data match the theoretical parameters within a tolerance of $10^{-6}$.

### Predictor Collinearity
Predictors (sample size, distribution type) are orthogonal by design. Sample size is a scalar; distribution type is categorical. No collinearity diagnostics are required.

### Distributional Assumptions
- **Outcome**: The observed error rate is a proportion (0 to 1), modeled by a Binomial distribution (approximated by Normal for large n).
- **Logit Transform**: The logit link function is applied to the *rate* (proportion) for the Binomial GLM, not to the deviation magnitude |p - α|.

## Compute Feasibility

- **CPU-First**: All operations (generation, testing, regression) are computationally lightweight and run efficiently on CPU.
  - `numpy` and `scipy` are optimized for CPU.
  - No GPU acceleration is needed for these classical statistical methods.
- **Memory**: Streaming generation (one sample at a time) ensures memory usage stays well below a moderate gigabyte threshold.
- **Time**: The adaptive loop may extend replicates, but the total number of tests is bounded. The -hour limit is sufficient for ~20 sizes × 3 dists × 3 tests × A substantial number of replicates will be generated to ensure statistical robustness. (worst case).

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Synthetic Data** | External datasets lack the precise control over effect size and distribution shape required to measure *sensitivity* to these specific parameters. |
| **Adaptive Replicates** | Fixed replicates (e.g., 1000) may yield unstable CIs for small n. Adaptive logic ensures the precision target (CI width ≤ 0.01) is met. |
| **Fisher's Exact for Chi-Squared** | Standard Chi-squared approximation fails when expected cell counts < 5. Fisher's Exact is the only valid alternative for small samples. |
| **Binomial GLM** | The outcome is the *observed error rate* (proportion). Binomial GLM is the statistically correct choice for modeling proportions. |
| **Cox-Snell/Nagelkerke $R^2$** | McFadden is for Binomial models but Cox-Snell/Nagelkerke is preferred for rate modeling in this context; Spec's McFadden requirement is amended. |
| **Unified Power Curve** | A single task calculates theoretical power for all tests to reduce overhead and ensure consistency. |
| **Conditional Testing** | Tests for parallel execution (T045) are conditional on the implementation of parallel execution (T041). Fisher's Exact tests (T047) are mandatory as FR-002 requires it. |
| **Result-Based Validation** | Validation is based on the presence and correctness of results (error rates), not the implementation detail of a streaming pipeline. |