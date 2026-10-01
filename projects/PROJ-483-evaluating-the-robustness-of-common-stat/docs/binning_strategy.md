# Chi-Squared Binning Strategy

## Overview
When applying the Chi-squared test to datasets containing continuous variables, these variables must be discretized into categorical bins. This document defines the standard binning strategy used throughout the project to ensure consistency and reproducibility.

## Strategy: Sturges' Rule
The number of bins $k$ is determined by **Sturges' Rule**:
$$ k = 1 + \log_2(N) $$
Where $N$ is the number of observations in the dataset.

## Implementation Details
- **Algorithm**: Equal-width binning is applied after discretization.
- **Edge Cases**: If $N$ is very small ($N < 10$), a minimum of 2 bins is enforced to ensure the Chi-squared test can be computed.
- **Consistency**: This strategy is applied uniformly across all datasets and dependency configurations (AR(1), Block, Spatial) to prevent bias in the comparison of test robustness.

## Rationale
Sturges' rule provides a reasonable balance between over-smoothing (too few bins) and over-fitting (too many bins) for typical sample sizes encountered in this study. It ensures that the degrees of freedom for the Chi-squared test remain manageable while preserving the distributional characteristics of the data.

## References
- Sturges, H. A. (1926). "The Choice of a Class Interval". *Journal of the American Statistical Association*.
