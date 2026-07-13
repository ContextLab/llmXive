# Research: Assessing the Sensitivity of Common Statistical Tests to Dataset Size

## Research Question

How do Type I and Type II error rates of common statistical tests (t-test, ANOVA, chi-squared) vary as a function of sample size (n=10 to n=1000) and underlying data distribution (normal, uniform, log-normal)?

## Dataset Strategy

Since this project relies on **synthetic data** with known ground truth parameters rather than observed real-world measurements, no external dataset URLs are required. The data generation strategy is defined as follows:

| Dataset Component | Source/Method | Verification Method |
| :--- | :--- | :--- |
| **Null Hypothesis Data** | Generated via `numpy.random` with `mu1=mu2` (effect size 0.0). | Compare sample means; verify difference < 1e-6. |
| **Alternative Hypothesis Data** | Generated via `numpy.random` with `mu=mu2+0.5` (effect size 0.5). | Compare sample means; verify difference ≈ 0.5. |
| **Distributions** | Normal (`norm`), Uniform (`uniform`), Log-Normal (`lognorm`). | Verify skewness/kurtosis against theoretical values. |
| **Ground Truth Metadata** | Embedded in generation parameters. | Logged in `data/` metadata files. |

*Note: McFadden pseudo-R² is a standard metric for regression model fit (no external URL required for definition).*

## Methodology

### 1. Data Generation (FR-001)
- **Inputs**: Sample size `n` (10, 20, ..., 1000), Distribution `D` (Normal, Uniform, Log-Normal), Effect Size `δ` (0.0, 0.5).
- **Process**:
  - Generate two groups of size `n/2` (or appropriate split for ANOVA/Chi-sq).
  - For Normal: `np.random.normal(loc=μ, scale=σ, size=n)`.
  - For Uniform: `np.random.uniform(low=a, high=b, size=n)`.
  - For Log-Normal: `np.random.lognormal(mean=μ, sigma=σ, size=n)`.
- **Validation**: Before testing, compute sample statistics and assert they match theoretical parameters within a numerical tolerance (Constitution Principle VI).

### 2. Monte Carlo Simulation (FR-002, FR-003)
- **Tests**: Student's t-test (independent), One-way ANOVA, Chi-squared test.
- **Adaptive Replication**:
  1. Initialize `rep_count = 1000`.
  2. Run simulation loop: Generate data → Select test → Compute p-value.
     - *Chi-squared Edge Case*: Calculate expected cell counts for the generated contingency table as `(row_total * col_total) / grand_total`. If **any** expected count < 5, switch to Fisher's Exact Test.
  3. Calculate observed error rate (Type I if `δ=0` and `p < 0.05`; Type II if `δ=0.5` and `p >= 0.05`).
  4. Compute a confidence interval via **Clopper-Pearson (exact) interval** based on the binomial distribution of successes/failures.
  5. If CI width > 0.01, increment `rep_count` and repeat.
  6. Cap at `rep_count = 10,000` to respect compute constraints (Assumption: Compute constraints).
- **Alpha Threshold**: Fixed at 0.05 (Assumption: Threshold justification).

### 3. Aggregation & Analysis (FR-004, FR-005, FR-006)
- **Aggregation**: Group results by `n`, `Distribution`, `Test`.
- **Confidence Intervals**: **Clopper-Pearson** 95% CI for all error rates (replaces bootstrap).
- **Visualization**:
  - Line plots: Error Rate (y) vs. Sample Size (x), faceted by Distribution and Test.
  - Error bars: 95% CI.
- **Regression**:
  - **Model**: **Generalized Linear Model (GLM)** with **binomial family** and **logit link**.
  - **Response Variable**: **Observed error rate** (proportion of rejections) per configuration (NOT raw p-values or p-value deviations).
  - **Predictors**: `log(n)`, `Distribution` (categorical), `Test` (categorical).
  - **Metric**: McFadden pseudo-R² (Target > 0.1 per SC-005).
  - **Output**: Coefficients (beta), p-values.
  - **Note**: The previous requirement to model "log-transformed p-value distribution" is removed as it is methodologically unsound for assessing error rates.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: The study focuses on the behavior of individual tests under varying conditions. While multiple tests are run, the primary output is the *rate* of errors, not a single hypothesis test result. Correction is not applied to the simulation loop itself but is acknowledged in the interpretation of error rates.
- **Sample Size/Power**: The adaptive replication strategy (Constitution Principle VII) ensures that the *estimates* of error rates are precise (CI width ≤ 0.01). This is distinct from the power of the *underlying statistical tests* being simulated, which is the variable being measured (SC-004).
- **Causal Inference**: This is a simulation study. The "causal" link between sample size and error rate is established by the controlled generation of data (ground truth known). No observational assumptions are needed.
- **Measurement Validity**: Standard `scipy.stats` implementations are used. For log-normal skewness, parameters are chosen to ensure finite moments and avoid numerical overflow (Edge Case: Distribution Extremes).
- **Collinearity**: Predictors (sample size, distribution) are orthogonal by design in the simulation grid. No collinearity diagnostics required (Assumption: Collinearity).
- **Confidence Interval Method**: The use of Clopper-Pearson intervals ensures stability for binary outcomes (error/no-error) even with small counts or extreme probabilities, avoiding the bias and instability of bootstrap resampling in this regime.

## Compute Feasibility

- **Environment**: GitHub Actions free-tier (multiple CPU cores, standard RAM).
- **Strategy**:
  - Sequential execution of configurations to avoid memory bloat.
  - Data subsets kept in memory only during the active simulation loop.
  - Results immediately written to CSV to free memory.
  - No GPU usage; all operations are CPU-native (`numpy`, `scipy`).
  - Adaptive replication capped at 10,000 to guarantee runtime < 6 hours.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Adaptive Replication** | Ensures precision (CI ≤ 0.01) without wasting compute on easy cases (large n, normal dist). |
| **Fisher's Exact for Chi-sq** | Required for scientific validity when expected counts < 5; standard Chi-sq fails here. Explicit calculation of expected counts from marginal totals ensures robustness. |
| **Synthetic Data** | Allows exact control of ground truth (effect size, distribution) impossible with real data. |
| **CPU-only** | Matches GitHub Actions constraints; statistical tests are lightweight. |
| **Clopper-Pearson CI** | Statistically superior for binary outcomes; avoids bootstrap instability for small proportions. |
| **GLM Binomial Regression** | Correctly models the bounded nature of error rates (proportions) and avoids tautological validation of p-values. |