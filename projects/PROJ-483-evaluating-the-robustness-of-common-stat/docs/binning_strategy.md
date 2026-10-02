# Chi-Squared Binning Strategy

## Overview

This document defines the binning strategy used for continuous variables when performing Chi-squared tests in the absence of native categorical variables. Consistent application of this strategy is critical for the reproducibility of results across datasets and dependency configurations.

## Strategy: Sturges' Rule

We use **Sturges' Rule** to determine the number of bins $k$ for discretizing continuous variables. This rule is chosen for its simplicity and robustness in providing a reasonable initial estimate for the number of bins in a histogram, which is directly applicable to constructing contingency tables for Chi-squared tests.

### Formula

The number of bins $k$ is calculated as:

$$k = 1 + \log_2(N)$$

Where:
- $N$ is the number of observations (sample size) in the dataset.
- $\log_2$ is the logarithm to base 2.

### Implementation Details

1. **Calculation**: The value $k$ is computed as a float and then rounded to the nearest integer, ensuring $k \ge 2$.
2. **Binning Method**: The continuous variable is binned using `pandas.cut` with `bins=k`. The bins are created to have equal width across the range of the data (min to max).
3. **Contingency Table Construction**:
 - If the dataset has a target variable (categorical), the binned predictor is cross-tabulated against the target.
 - If both variables are continuous, both are binned using Sturges' rule (or a consistent rule) before cross-tabulation.
4. **Edge Cases**:
 - If $N$ is very small (e.g., $N < 5$), a minimum of 2 bins is enforced to allow for a valid Chi-squared test.
 - If a bin ends up with 0 expected frequency, a small epsilon or merging of adjacent bins may be required (handled by `scipy.stats.chi2_contingency` with warnings, but we log these cases).

## Rationale

Sturges' rule is a standard heuristic in exploratory data analysis. While it tends to under-smooth for very large datasets compared to rules like Freedman-Diaconis, it provides a deterministic and sample-size-dependent bin count that scales appropriately for our simulation framework. It ensures that the degrees of freedom in the Chi-squared test are consistent relative to the sample size across different replications.

## Consistency Across Tests

This strategy is applied uniformly in:
- `code/simulation_runner.py` (Task T020a)
- `code/t019_us2_comparison_runner.py`
- Any other module requiring discretization for Chi-squared tests.

## References

- Sturges, H. A. (1926). "The Choice of a Class Interval". *Journal of the American Statistical Association*.
- Implementation in `code/simulation_runner.py` function `bin_continuous_variable`.
