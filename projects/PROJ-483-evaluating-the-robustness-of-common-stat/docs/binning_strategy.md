# Binning Strategy for Chi-Squared Tests

## Overview

This document describes the binning strategy used to convert continuous variables into categorical variables for Chi-squared tests.

## Method: Sturges' Rule

The number of bins $k$ is determined using **Sturges' rule**:

$$k = 1 + \log_2(N)$$

Where $N$ is the number of observations in the dataset.

## Implementation

The binning is implemented in `code/simulation_runner.py` (T020a) as follows:

```python
def bin_continuous_variable(data: pd.Series) -> pd.Series:
 """
 Bin continuous variable using Sturges' rule.

 Args:
 data: Continuous variable to bin

 Returns:
 Categorical variable with bin labels
 """
 n = len(data)
 k = int(1 + np.log2(n)) # Sturges' rule
 bins = pd.qcut(data, q=k, duplicates='drop')
 return bins.astype(str)
```

## Rationale

### Why Sturges' Rule?

1. **Simplicity**: Easy to compute and understand
2. **Adaptability**: Automatically adjusts to sample size
3. **Consistency**: Applied uniformly across all datasets
4. **Statistical Validity**: Well-established method for histogram binning

### Alternative Methods Considered

- **Freedman-Diaconis Rule**: More robust to outliers but may produce too many bins for small datasets
- **Square Root Rule**: Simpler but less adaptive to distribution shape
- **Scott's Rule**: Optimal for normal distributions but less general

Sturges' rule was chosen as the best balance between simplicity and adaptability for our use case.

## Consistency Across Configurations

The same binning strategy is applied to:
- All datasets (Wine, Car, Zoo, etc.)
- All dependency structures (AR(1), Block, Spatial)
- All dependency strengths ($r \in \{0, 0.1, 0.2, 0.3, 0.5\}$)
- Both synthetic and real data modes

This ensures that any observed differences in error rates are due to dependency structure, not binning artifacts.

## Edge Cases

### Small Sample Sizes

For $N < 10$, Sturges' rule may produce too few bins ($k < 2$). In such cases:
- Minimum of 2 bins is enforced
- Dataset is flagged in `results/edge_case_report.json`
- Chi-squared test is skipped if $k < 2$ after enforcement

### Large Sample Sizes

For $N > 10,000$, Sturges' rule may produce many bins ($k > 20$). In such cases:
- Maximum of 30 bins is enforced
- Dataset is logged in `results/perf_log.json`
- Chi-squared test proceeds with capped bins

### Ties in Data

If many observations have identical values:
- `pd.qcut` with `duplicates='drop'` handles ties gracefully
- Resulting bins may be fewer than target $k$
- Chi-squared test proceeds with available bins

## Validation

The binning strategy is validated through:
1. **Unit Tests**: Verify bin count matches Sturges' formula
2. **Integration Tests**: Ensure Chi-squared test runs successfully
3. **Consistency Checks**: Confirm same strategy across all configurations

## References

- Sturges, H. A. (1926). "The Choice of a Class Interval". Journal of the American Statistical Association.
- Freedman, D., & Diaconis, P. (1981). "On the histogram as a density estimator". Zeitschrift für Wahrscheinlichkeitstheorie und verwandte Gebiete.
- Scott, D. W. (1979). "On optimal and data-based histograms". Biometrika.
