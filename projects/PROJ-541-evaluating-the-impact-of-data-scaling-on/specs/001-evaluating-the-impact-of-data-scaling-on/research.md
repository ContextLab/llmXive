# Research: Evaluating the Impact of Data Scaling on Robustness of Statistical Tests

## Executive Summary

This research plan outlines a simulation study to determine if data scaling (Standardization, Min-Max, Robust) impacts the *numerical stability* of parametric statistical tests (t-test, ANOVA). The core hypothesis is that while scaling is mathematically a linear transformation (preserving p-values for t-tests/ANOVA), numerical precision errors or edge cases (outliers, zero variance) might introduce small deviations. The study will generate synthetic data with known ground truth to measure empirical Type I error rates and power, then validate on real-world datasets by measuring p-value consistency. Chi-squared tests on binned data have been removed from the primary analysis to avoid construct validity issues.

## Dataset Strategy

The project requires two types of data: synthetic (ground truth known) and real-world (validation).

### Synthetic Data Generation
No external dataset is needed. Data will be generated programmatically using `numpy` and `scipy.stats` to ensure exact control over:
- **Null Hypothesis**: Mean difference = 0.
- **Alternative Hypothesis**: Mean difference = 1.0 (or specified effect size).
- **Distributional Properties**: Normal, Skewed (skewness=2.0), Heteroscedastic (variance ratio > 1).
- **Sample Sizes**: Varied per configuration (e.g., n=30, n=100, n=500).

### Real-World Datasets
Per FR-008, public datasets from UCI and OpenML are required.
**Constraint**: Only datasets with **verified sources** in the provided `# Verified datasets` block will be used.

**Available Verified Sources**:
1. **UCI HAR (CSV)**: `
 - *Relevance*: Human Activity Recognition. Contains continuous sensor data (accelerometer/gyroscope) suitable for t-tests on feature means.
2. **UCI Shopper (Parquet)**: `
 - *Relevance*: Customer behavior. Contains numerical features suitable for ANOVA.

**Strategy**:
- The implementation will attempt to load these specific URLs.
- If a dataset lacks a continuous variable suitable for the required tests (t-test/ANOVA), it will be skipped, and the reason logged.
- **Missing Data**: The verified list currently contains only a limited number of distinct, suitable datasets. The project will proceed with these available datasets and explicitly state this limitation in the final report. The spec requires "at least 10", but the plan must not invent data. We will prioritize quality (suitability for scaling tests) over quantity if the verified pool is limited.
- **Note**: Datasets like 'UCI DROP' (text-heavy) and generic 'RealWorldDataset' Parquet files are excluded as they lack the explicit continuous numerical features required for the planned parametric tests without complex, undefined feature extraction.

## Methodology

### Phase 1: Simulation Engine (US-1)
- **Generator**: Create data with known `mu`, `sigma`, `skew`, `kurt`.
- **Ground Truth**: Explicitly label each iteration as "Null" (diff=0) or "Alt" (diff=1).
- **Validation**: Verify generated data matches target stats (mean diff < 0.01, skewness within ±0.1).

### Phase 2: Scaling & Testing (US-2)
- **Scaling**: Apply Standardization, Min-Max, Robust.
 - *Robust Edge Case*: Handle zero IQR by returning constant/zero.
- **Tests**:
 - **t-test**: Welch's t-test (robust to variance inequality).
 - **ANOVA**: One-way ANOVA.
 - *Removed*: Chi-squared on binned data (construct validity issue).
- **Output**: Store p-value, statistic, scaling method, ground truth.

### Phase 3: Aggregation & Visualization (US-3)
- **Metrics**:
 - **Type I Error**: `count(p < 0.05) / total_null_iterations`.
 - **Power**: `count(p < 0.05) / total_alt_iterations`.
- **Analysis**:
 - **Synthetic Data**: Use **One-Way ANOVA** on the aggregated error rates to test if `ScalingMethod` significantly predicts deviation from the nominal 0.05 level. (Mixed-effects model is inappropriate here as 'dataset' is not a random variable).
 - **Real-World Data**: Use **Mixed-Effects Model** (`ErrorRate ~ ScalingMethod + (1|DatasetSource)`) *only* for real-world validation where dataset variance exists.
- **Visualization**: Plot empirical error rate vs. nominal 0.05 with 95% CI.

### Phase 4: Real-World Validation (US-4)
- Load verified datasets.
- Apply scaling and tests.
- **Metric**: Measure **consistency of p-values** (difference in p-values before/after scaling) rather than Type I error rates, as ground truth is unknown for real data.

## Statistical Rigor & Assumptions

1. **Multiple Comparisons**:
 - We are testing multiple scaling methods and test types.
 - **Correction**: We will use the **Bonferroni correction** for final inference if multiple hypotheses are tested simultaneously.
 - **Primary Metric**: The 'robustness' claim is based on the **raw empirical error rate** (unadjusted) compared against 0.05. Corrections are applied only for final significance testing of differences between methods.

2. **Sample Size / Power**:
 - **Target**: [deferred] iterations per configuration.
 - **Justification**: For a binomial proportion (error rate) at p=0.05, samples yield a standard error of $\sqrt{0.05 \times 0.95 / 10000} \approx 0.0022$. The 95% CI width is approx $\pm 0.0043$, meeting the SC-004 target of $\pm 0.005$.
 - **Limitation**: If runtime exceeds a predefined threshold, we will implement a hard stop and report partial results with wider CIs.

3. **Causal Inference**:
 - This is a simulation study with known ground truth. Claims are **associational** regarding real-world datasets but **causal** (deterministic) regarding the simulation mechanics (scaling X causes change in Y). No observational identification strategy is needed for the synthetic part.

4. **Measurement Validity**:
 - Standard `scipy.stats` implementations are used. No custom instruments.
 - Validation of generators against theoretical moments (skewness, kurtosis) will be performed in the "Independent Test" phase.

5. **Predictor Collinearity**:
 - Scaling is a linear transformation. For t-tests and ANOVA, scaling **should not** change the p-value (invariant to linear transformation).
 - **Hypothesis**: Deviations will only occur due to:
 - Numerical precision errors (floating-point noise).
 - Outlier handling in Robust scaling (if median/IQR changes group composition relative to mean/variance).
 - We will explicitly acknowledge that any observed "effect" of scaling on t-test p-values is likely a numerical artifact or implementation bug, not a statistical property.

## Compute Feasibility

- **Environment**: GitHub Actions Free Tier (multiple CPU, sufficient RAM).
- **Strategy**:
 - **No GPU**: All operations use CPU-optimized libraries (`numpy`, `scipy`).
 - **Memory**: Process simulations in batches (e.g., a manageable number of iterations at a time) to avoid loading all data into memory at once.
 - **Runtime**: [deferred] iterations of simple t-tests are computationally cheap. The bottleneck will be I/O and the mixed-effects model fitting (only for real-world data).
 - **Approximation**: If the mixed-effects model (statsmodels) is too slow for the available real-world datasets, we will use a simpler fixed-effects ANOVA on the error rates as a fallback, noting the limitation.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Suitability** | Verified datasets may lack continuous variables. | Inspect datasets first; skip if unsuitable. Report "N/A" for those cases. |
| **Runtime Exceeds 6h** | Incomplete results. | Implement batch processing and a checkpoint system. Stop and save partial results. |
| **Zero Variance** | Division by zero in scaling. | Add `try-except` blocks; log warning; skip iteration. |
| **Robust Scaling Failure** | NaNs from zero IQR. | Custom robust scaler that returns 0 if IQR=0. |
| **Numerical Noise** | Small deviations in p-values. | Explicitly frame results as "numerical stability" tests, not "statistical alteration" tests. |
