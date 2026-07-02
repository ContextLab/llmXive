# Research: Assessing the Validity of Frequentist Confidence Intervals with Small Sample Sizes

## Research Question

Do standard frequentist confidence intervals (e.g., t-intervals, z-intervals) maintain their nominal coverage probabilities when applied to samples of size n < 30 drawn from real-world distributions?

## Background & Motivation

Frequentist confidence intervals (CIs) are widely used in statistical inference, with the t-interval being the standard for small samples when population variance is unknown. The t-interval relies on the assumption that the sampling distribution of the mean is approximately normal (Central Limit Theorem, CLT). However, the CLT's convergence rate depends on the underlying distribution's shape; for highly skewed or heavy-tailed distributions, small samples (n < 30) may not yield normal sampling distributions, potentially leading to coverage rates that deviate from the nominal level.

Bootstrap percentile intervals offer a non-parametric alternative that does not rely on normality assumptions but may also underperform in small samples. This research systematically evaluates both methods across diverse real-world distributions to quantify coverage deviations.

## Parametric Distribution Strategy

To ensure mathematical consistency between the sampling model (infinite super-population) and the ground truth (theoretical mean), this research uses parametric distributions with known parameters rather than finite datasets. This approach eliminates the Finite Population Correction (FPC) conflict and ensures the t-interval's assumptions are valid.

### Distribution Selection Criteria

The following distributions are selected to stress-test the t-interval under conditions where the CLT may not have converged:
- **LogNormal**: Highly skewed, heavy-tailed. Parameters: `mu`, `sigma` chosen to yield skewness > 1.0.
- **Beta**: Bounded, can be skewed or symmetric. Parameters: `alpha`, `beta` chosen to yield skewness > 1.0 or kurtosis > 3.0.
- **Student's t**: Heavy-tailed. Degrees of freedom: `df` = 3, 5, 10 (to vary tail heaviness).
- **Gamma**: Skewed, positive-only. Parameters: `shape`, `scale` chosen to yield skewness > 1.0.
- **Normal**: Baseline (skewness = 0, kurtosis = 3) for comparison.

### Excluded Sources

The following datasets are explicitly excluded from the simulation population due to methodological limitations:
- **FPC Summary Statistics**: Aggregated data lacks row-level structure required for Monte Carlo resampling.
- **FPC Audit Data**: Discrete scores or JSONL format not suitable for continuous variable simulation.
- **FPC Object Annotations**: Discrete bounding boxes or confidence scores not representative of continuous distributions.
- **UCI HAR / Shopper (HuggingFace mirrors)**: While useful for empirical validation, these datasets often contain pre-processed, normalized, or zero-inflated variables that do not reliably stress-test the CLT convergence. They are excluded from the primary simulation to ensure distributional diversity and theoretical validity.

## Simulation Design

### Core Methodology

1. **Population Definition**: The "population" is defined as an infinite theoretical distribution (e.g., LogNormal(mu, sigma)) with known theoretical mean (e.g., `exp(mu + sigma^2/2)`). This ensures compatibility with the t-interval's infinite population assumption.

2. **Sampling Strategy**: Draw samples *with replacement* from the theoretical distribution (i.e., generate new random variates) for each replication. This simulates an infinite super-population, avoiding the FPC issue.

3. **Replications**: Perform 10,000 Monte Carlo replications per configuration (distribution × sample size × confidence level) to achieve ±1% precision in coverage estimation (per Constitution Principle VI).

4. **Confidence Interval Methods**:
   - **t-interval**: Compute using sample mean, sample standard deviation, and t-distribution critical value (t_{n-1, 1-α/2}).
   - **Bootstrap percentile interval**: Compute using **2,000** bootstrap resamples of the sample (not 10,000) to construct the interval. This reduces computational load while maintaining sufficient precision for the bootstrap estimate.

5. **Coverage Calculation**: For each replication, check if the computed CI contains the **theoretical population mean** (ground truth). Coverage rate = (number of CIs containing true mean) / (total replications).

### Configuration Matrix

| Sample Sizes | Confidence Levels | Distributions | Replications per Config | Inner Bootstrap Resamples |
|--------------|-------------------|---------------|-------------------------|---------------------------|
| n=10, n=20, n=30 | [deferred], [deferred], [deferred] | ~15 (parametric) | [deferred] | [deferred] |

Total configurations: sample sizes × 3 confidence levels × ~15 distributions = ~135 configurations.  
Total replications: 135 × 10,000 = 1.35 million interval computations.  
Total bootstrap resamples: 1.35 million × 2,000 = 2.7 billion resampling operations (optimized via vectorization).

### Statistical Rigor Considerations

- **Multiple Comparison Correction**: When testing for significant deviations across multiple distributions, apply Bonferroni correction to control family-wise error rate (per FR-006).
- **Causal Framing**: All findings will be framed as associational regarding coverage properties; no causal claims will be made (per FR-007).
- **Measurement Validity**: The t-interval's validity relies on the assumption of normality for the sampling distribution; bootstrap intervals rely on the representativeness of the sample. Both methods will be evaluated against the known theoretical mean.
- **Collinearity**: Not applicable for univariate mean estimation; each analysis focuses on a single variable at a time.
- **Power Justification**: 10,000 replications provide sufficient power to detect deviations of ±1% from nominal coverage (standard error ≈ √(p×(1-p)/n), where p denotes the population proportion and n denotes the sample size., yielding ~95% CI width of ±0.0043 for 95% nominal coverage).

## Sensitivity Analysis Plan

### Confidence Level Sensitivity (FR-008)
Sweep confidence levels across {90%, [deferred], [deferred]} to test robustness of coverage deviations. Expected outcome: Deviations may vary across confidence levels, with extreme levels ([deferred]) potentially showing larger deviations in small samples.

### Sample Size Sensitivity (FR-009)
Explicitly compare coverage rates across n=10, n=20, and n=30 to quantify the impact of sample size on interval validity. Expected outcome: Coverage deviations are expected to decrease as sample size increases, with non-linear degradation at very small n (n=10).

## Computational Feasibility

- **Runtime**: 1.35 million interval computations with 2,000 inner bootstrap resamples per sample (optimized via vectorized NumPy operations) on 2-core CPU should complete within 6 hours.
- **Memory**: Peak memory usage estimated at a moderate scale (storing distribution parameters + temporary arrays for bootstrap resampling), well within 7 GB limit.
- **Disk**: Output files (JSON/CSV) estimated at <100 MB total, well within 14 GB limit.
- **GPU**: Not required; all operations are CPU-tractable.

## Decision Rationale

- **Why parametric distributions?**: To ensure mathematical consistency between the sampling model (infinite population) and the ground truth (theoretical mean), avoiding the FPC conflict and circular validation of finite-dataset resampling.
- **Why 2,000 inner bootstrap resamples?**: To balance computational feasibility (reducing total resamples substantially) with sufficient precision for the bootstrap percentile interval estimate.
- **Why these distributions?**: Selected to explicitly cover skewed, heavy-tailed, and bounded distributions with skewness > 1.0 or kurtosis > 3.0, ensuring the simulation stress-tests the t-interval under non-normal conditions.
- **Why t-interval and bootstrap?**: These are the two most common frequentist CI methods for small samples; comparing them addresses the core research question.
- **Why Bonferroni correction?**: To control family-wise error rate when testing multiple distributions (per FR-006).
- **Why associational framing?**: Observational nature of dataset-based simulation precludes causal claims (per FR-007).

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Runtime exceeds 6 hours | Medium | High | Optimize code (vectorization), reduce inner bootstrap resamples if needed (e.g., to 1,000). |
| Memory exceeds 7 GB | Low | Medium | Process distributions sequentially; avoid storing all replications. |
| Coverage deviation >1% | High | Low | Expected outcome; document as finding rather than failure. |
| Parametric distributions not representative of real-world | Medium | Medium | Validate distribution shapes (skewness/kurtosis) against empirical data from UCI datasets (as a secondary step, not primary simulation). |