# Research: Assessing the Sensitivity of Common Statistical Tests to Dataset Size

## Summary

This research phase defines the statistical methodology, data generation strategy, and computational approach to answer: "How do Type I and Type II error rates of common statistical tests vary as a function of sample size and underlying data distribution?" The study relies on synthetic data generation with known ground truth, avoiding the need for external datasets. The methodology prioritizes CPU-feasible operations while ensuring statistical rigor through adaptive Monte Carlo replication and appropriate regression modeling for bounded outcomes.

## Dataset Strategy

Since this study relies on **synthetic data** with known theoretical properties (normal, uniform, log-normal) rather than observed real-world measurements, no external dataset URLs are required or cited. The "dataset" is generated programmatically by `code/data_generator.py` (invoked via `code/run_data_gen.py`) using `numpy` and `scipy`.

**Generation Strategy**:
- **Distributions**: Normal (Gaussian), Uniform, Log-Normal.
- **Parameters**:
  - Null Hypothesis ($H_0$): Effect size = 0.0 (means equal).
  - Alternative Hypothesis ($H_1$): Effect size = 0.5 (Cohen's d equivalent for t-test/ANOVA; scaled for log-normal).
- **Sample Sizes**: 20 points logarithmically spaced from $n=10$ to $n=1000$.
- **Ground Truth**: Every generated batch includes metadata confirming the theoretical mean, variance, and skewness.

**Rationale**: Synthetic data is the only feasible approach to guarantee "known ground truth" for error rate calculation. Using real-world data would introduce unknown confounding variables, making it impossible to definitively classify an outcome as a Type I or Type II error.

## Statistical Methodology

### 1. Error Rate Calculation (FR-002, FR-003)
- **Type I Error**: Rejecting $H_0$ when $H_0$ is true (Effect Size = 0).
- **Type II Error**: Failing to reject $H_0$ when $H_1$ is true (Effect Size = 0.5).
- **Power**: $1 - \text{Type II Error Rate}$.
- **Alpha Threshold**: Nominal $\alpha = 0.05$.
- **Test Selection**:
  - **T-Test**: 
    - For **Normal** distribution (Null hypothesis validation): **Student's t-test** (equal variance) is used to match the ground truth parameters exactly as required by US-1.
    - For **Uniform** and **Log-Normal** distributions: **Welch's t-test** is used to account for potential variance heterogeneity, unless the simulation specifically tests variance equality.
  - **ANOVA**: One-way ANOVA.
  - **Chi-Squared**: Chi-squared test of independence for contingency tables.
    - *Critical Adjustment*: If expected cell counts < 5, the system **MUST** switch to **Fisher's Exact Test** (per Spec Edge Cases and FR-002) to maintain validity.

### 2. Adaptive Monte Carlo Replication (FR-002, FR-004)
- **Initial Replicates**: 1000 per configuration.
- **Convergence Criterion**: 95% Confidence Interval (CI) width for the error rate estimate $\le 0.01$.
- **CI Method**: **Clopper-Pearson (Exact) interval**. This is methodologically superior to Bootstrap for binomial proportions, especially for rare events or extreme sample sizes, ensuring the convergence criterion is stable and mathematically rigorous.
- **Adaptive Logic**: If CI width > 0.01, add 500 replicates and re-calculate. Repeat until convergence or a maximum number of replicates is reached (log warning if maximum hit).

### 3. Regression Analysis (FR-006)
- **Dependent Variable**: **Error Rate** (proportion of Type I or Type II errors for a given configuration). This avoids the circularity of using raw p-values (the test's stochastic output) to predict the test's own reliability.
- **Predictors**: $\log(\text{sample size})$, `distribution_type` (categorical), `test_type` (categorical).
- **Model**: **Beta Regression**. Since the dependent variable is a proportion bounded in (0, 1), Beta Regression is the appropriate generalized linear model. It handles the skewness and heteroscedasticity of proportional data better than OLS.
- **Success Metric**: **Cox-Snell or Nagelkerke pseudo-R² > 0.1**. 
  - *Note*: The original spec (SC-005) mandates "McFadden pseudo-R²", which is specific to Logistic Regression (binary outcomes). Since Beta Regression is the scientifically correct method for continuous proportions, this plan uses Cox-Snell/Nagelkerke R². The specification is flagged as a blocking gap requiring amendment to align with the methodology.
- **Collinearity**: Predictors (sample size, distribution) are orthogonal by design.

### 4. Theoretical Power Comparison (SC-004)
- **Method**: Calculate theoretical power curves using non-centrality parameters for t-tests and ANOVA.
- **Scope**: 
  - **Normal Distribution**: Theoretical power will be calculated using Cohen's d and standard non-centrality parameters ($\delta = d \times \sqrt{n/2}$).
  - **Uniform and Log-Normal Distributions**: Standard non-centrality parameters (Cohen's d) are **not** mathematically valid for these distributions due to skewness and variance-mean dependencies. For these distributions, the study will report **empirical power only** and explicitly note that no theoretical baseline exists for comparison. This avoids the category error of applying normal-theory formulas to non-normal data.
- **Comparison**: Observed Power vs. Theoretical Power (via MAE) for Normal data only.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Not explicitly corrected for in the *simulation* (as we are estimating rates, not testing a single hypothesis), but the regression model (FR-006) accounts for multiple predictors.
- **Sample Size/Power**: The adaptive replication strategy (FR-002) serves as the power justification for the *error rate estimates*, ensuring they are stable. The study acknowledges that for very small $n$ (e.g., 10), the error rate estimates themselves may have high variance, which is why the adaptive loop is critical.
- **Causal Inference**: This is a simulation study; claims are about the *properties of the tests*, not causal effects in a population. No randomization strategy is needed beyond the random seed.
- **Measurement Validity**: The "measures" are the statistical tests themselves. Their validity is tested against the known ground truth of the synthetic data.
- **Collinearity**: Predictors (sample size, distribution) are orthogonal by design.

## Compute Feasibility

- **CPU-First**: All operations (data generation, t-test, ANOVA, Fisher's Exact, Beta Regression) are computationally light and run efficiently on CPU.
- **Memory**: Streaming approach not needed for synthetic data (generated on-the-fly), but results are aggregated incrementally to stay within available RAM.
- **GPU**: Not required. No deep learning or large matrix inversions.
- **Time**: Estimated < 4 hours for full sweep on 2-core CPU.

## Decision Rationale

- **Why Synthetic Data?**: Only synthetic data provides the "known ground truth" required to definitively classify Type I/II errors. Real data introduces ambiguity.
- **Why Adaptive Replication?**: Fixed replicates (e.g., 1000) may yield unstable estimates for skewed distributions at small $n$. Adaptive loop ensures CI width $\le 0.01$ per Constitution Principle VII.
- **Why Fisher's Exact for Small Counts?**: Chi-squared approximation fails when expected counts < 5. Switching to Fisher's Exact ensures scientific validity (Spec Edge Cases).
- **Why No External Datasets?**: The research question is about *test behavior*, not specific real-world phenomena. External datasets would not offer the controlled ground truth needed.
- **Why Beta Regression?**: The dependent variable (error rate) is a proportion. OLS on proportions violates normality and homoscedasticity assumptions. Beta Regression is the standard for bounded continuous outcomes.
- **Why Restrict Theoretical Power to Normal?**: Cohen's d and non-centrality parameters assume normality. Applying them to Log-Normal/Uniform data is mathematically invalid.