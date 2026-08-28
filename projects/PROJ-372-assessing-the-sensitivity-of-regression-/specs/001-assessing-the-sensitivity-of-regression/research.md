# Research Rationale: Sample Size Tier Selection

## Overview

This document provides the research rationale for the fixed sample size tier percentages used in the sensitivity analysis of regression coefficients. These tiers define the subset sizes relative to the full dataset N that will be used to generate random observation subsets for resampling experiments.

## Selected Sample Size Tiers

The following five percentage tiers have been selected for this implementation:

- **10%** (0.10 × N)
- **25%** (0.25 × N)
- **50%** (0.50 × N)
- **75%** (0.75 × N)
- **90%** (0.90 × N)

These values are hardcoded in `src/utils/config.py` as the `SAMPLE_SIZE_TIERS` list.

## Rationale for Tier Selection

### 1. Coverage of the Subset Spectrum

The selected tiers provide comprehensive coverage of the possible subset sizes:

- **Lower bound (10%)**: Represents a small but statistically meaningful subset. At 10%, we test the stability of coefficients when a significant portion (90%) of data is withheld, simulating scenarios with limited data availability or high variability.

- **Lower-mid range (25%)**: A quarter of the data provides a moderate subset that balances statistical power with the ability to detect sensitivity to data composition. This tier is commonly used in bootstrap and cross-validation contexts.

- **Midpoint (50%)**: The median tier represents an equal split, providing a strong baseline for comparing how coefficients behave when half the data is randomly selected. This is a standard split in many resampling methodologies.

- **Upper-mid range (75%)**: This tier tests the stability of coefficients when the majority of data is retained. It helps identify whether coefficient variance diminishes as the subset approaches the full dataset size.

- **Upper bound (90%)**: A near-full subset that tests the asymptotic behavior of coefficient stability. At 90%, the subset is large enough that any remaining variance is likely due to extreme outliers or structural instability rather than sample size effects.

### 2. Statistical Power Considerations

The tiers are spaced to ensure sufficient statistical power at each level:

- For a dataset with N = 10,000 observations, the tiers yield subsets of 1,000, 2,500, 5,000, 7,500, and 9,000 observations respectively.
- Even at the 10% tier, a subset of 1,000 observations typically provides adequate power for OLS estimation with a moderate number of predictors (e.g., <50 features), satisfying the constraint that subset size ≥ 10 × number of predictors.

### 3. Detection of Non-Linear Sensitivity

The non-uniform spacing (10, 25, 50, 75, 90) is intentional to detect non-linear relationships between subset size and coefficient variance:

- The gap between 10% and 25% is 15 percentage points, allowing detection of rapid changes in stability at small sample sizes.
- The gap between 25% and 50% is 25 percentage points, covering the critical mid-range where many datasets transition from unstable to stable.
- The gaps between 50-75% and 75-90% are 25 and 15 percentage points respectively, capturing the asymptotic approach to full-dataset stability.

This spacing enables the identification of "tipping points" where coefficient stability significantly improves or deteriorates.

### 4. Comparison with Standard Methodologies

The selected tiers align with and extend standard resampling practices:

- **Cross-validation**: Typical k-fold CV uses 1/k and (k-1)/k splits. For k=4, this yields 25% and 75%, which are directly included in our tiers.
- **Bootstrap**: Bootstrap resampling often uses the full dataset size (100%), but our 90% tier approximates this while maintaining a distinct subset.
- **Leave-one-out**: While not directly represented, the 10% tier provides a coarse approximation of high-variance, low-data scenarios.

### 5. Practical Constraints and Feasibility

The tiers balance scientific rigor with computational feasibility:

- **Lower tiers (10%, 25%)**: Computationally inexpensive, allowing for a larger number of iterations (subsets) to be generated and analyzed.
- **Upper tiers (75%, 90%)**: More computationally intensive but fewer iterations are needed to detect stability trends, as variance typically decreases with larger sample sizes.
- The 5-tier structure is a manageable number for analysis and visualization, avoiding the complexity of too many tiers while providing sufficient resolution.

### 6. Alignment with Research Goals

The primary research goal is to assess the **sensitivity** of regression coefficients to dataset subset selection. The selected tiers directly support this goal by:

- Providing a range of subset sizes to measure how coefficient variance changes.
- Enabling the detection of thresholds where coefficients become stable or unstable.
- Allowing comparison of stability across different violation severities (Low/Medium/High) identified in the data profiling phase.

## Implementation Details

The `SAMPLE_SIZE_TIERS` list in `src/utils/config.py` is defined as:

```python
SAMPLE_SIZE_TIERS = [10, 25, 50, 75, 90]
```

These values are used by the resampling engine (`src/resampling/engine.py`) to calculate subset sizes:

```python
subset_size = int(N * (tier / 100))
```

where `N` is the total number of observations in the dataset.

## Conclusion

The selected sample size tiers of [10, 25, 50, 75, 90] provide a scientifically grounded, computationally feasible, and statistically rigorous framework for assessing the sensitivity of regression coefficients to dataset subset selection. These tiers cover the full spectrum of subset sizes, enable detection of non-linear stability patterns, and align with standard resampling methodologies while addressing the specific goals of this research project.

This document replaces any `[deferred]` placeholders in the specification with these concrete values, satisfying the requirement for fixed sample size tiers as per FR-003.