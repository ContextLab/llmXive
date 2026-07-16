# Statistical Methodology Documentation

## Overview

This document details the statistical methods implemented in the "Assessing Statistical Significance of Observed Correlations" pipeline. The goal is to determine whether observed correlation structures in multivariate datasets are statistically significant or could have arisen by chance.

## Data Preprocessing

### Dataset Selection
- Sources: UCI Machine Learning Repository
- Criteria:
 - Multivariate datasets
 - At least 20 continuous variables
 - No missing values (rows with missing values are dropped)
 - No constant variables (variables with zero variance are excluded)

### Data Hygiene Pipeline
1. **Missing Value Handling**: Rows with any missing values are dropped to ensure complete cases.
2. **Constant Variable Detection**: Variables with zero variance (constant values) are identified and excluded.
3. **Continuous Variable Filtering**: Only continuous (numeric) variables are retained for correlation analysis.
4. **Dimensionality Validation**: Datasets must have at least 20 continuous variables after cleaning.

## Correlation Analysis

### Correlation Metrics
- **Pearson Correlation**: Primary metric for linear relationships. Used for graph construction and significance testing.
- **Spearman Correlation**: Computed for exploratory comparison only. **Excluded** from significance testing and BY correction.

### Graph Construction
- Correlation matrices are thresholded at absolute values (configurable, default: 0.3).
- Edges are created where |r| > threshold.
- Graphs are treated as undirected.
- Spearman matrices are stored separately and not used for graph construction.

## Permutation Testing

### Null Hypothesis
The null hypothesis is that there is no association between variables; any observed correlation structure is due to random chance.

### Permutation Procedure
1. For each dataset, we generate `N` permuted versions (default: 1,000).
2. In each permutation, values within each column are shuffled independently.
3. This preserves the marginal distribution of each variable while destroying any true associations.
4. For each permuted dataset, we compute the same statistics as for the observed data.

### Statistics Computed
- **Mean Absolute Correlation**: Average of all absolute correlation values in the matrix.
- **Edge Density**: Proportion of possible edges that exist in the thresholded graph.
- **Max Absolute Correlation**: Maximum absolute correlation value in the matrix.
- **Average Clustering Coefficient**: Average local clustering coefficient of the graph.

### Optimization for Large Datasets
For datasets with more than 50 variables, the number of permutations for clustering coefficient is reduced to 500 to ensure runtime < 6 hours, as authorized by Plan Phase 1.

## Significance Testing

### Empirical P-Value Calculation
For each statistic:
```
p = (r + 1) / (N + 1)
```
where:
- `r` = number of permuted statistics >= observed statistic
- `N` = number of permutations

This formula avoids p-values of exactly 0 or 1, providing a conservative estimate.

### Multiple Testing Correction
We test multiple statistics across multiple datasets, requiring correction for multiple comparisons.

#### Benjamini-Yekutieli (BY) Procedure
- **Why BY?** The standard Benjamini-Hochberg (BH) procedure assumes independence or positive dependence. Our correlation tests are likely to be arbitrarily dependent, so we use the more conservative BY procedure which controls FDR under arbitrary dependence.
- **Implementation**: The BY procedure adjusts p-values by dividing each by a sum of harmonic series, providing a guaranteed FDR control.

### Significance Threshold
- Default FDR threshold: 0.05
- A result is considered significant if its q-value (adjusted p-value) < 0.05.

## Threshold Sensitivity Analysis

### Purpose
To assess whether significant findings are robust to the choice of correlation threshold.

### Thresholds Tested
{0.1, 0.2, 0.3, 0.4, 0.5}

### Output
A summary table showing the number of significant edges/statistics at each threshold, allowing researchers to see if findings are stable or threshold-dependent.

## Visualization

### Heatmaps
- Display observed correlation matrices
- Compare observed vs. null correlation distributions
- High-resolution PNG output

### Histograms
- Show null distributions for each statistic
- Overlay observed statistic value
- Visual assessment of significance

### Primary Threshold Visualizations
- Dedicated plots for |r| > 0.3 threshold
- Saved to `output/plots/primary/`

## Validation

### Synthetic Data Validation
- Generated synthetic datasets with known properties (identity covariance, no true correlations)
- Verified that observed statistics fall within the central region of the null distribution (p > 0.05) in >=95% of runs
- This confirms the null model is correctly calibrated

### Permutation Preservation Test
- Verified that marginal distributions are preserved after permutation
- Ensures the permutation procedure does not introduce artifacts

## Limitations and Assumptions

1. **Marginal Preservation**: Permutation preserves marginal distributions but may not preserve higher-order dependencies.
2. **Sample Size**: Results are most reliable with sufficient sample sizes; small datasets may have low power.
3. **Variable Count**: The requirement for >=20 continuous variables ensures sufficient degrees of freedom for meaningful graph statistics.
4. **BY Conservatism**: The BY procedure is conservative; some true effects may be missed (Type II error).
5. **Associational Language**: All conclusions are framed in terms of association, not causation.

## Reproducibility

- Random seeds are set globally for reproducibility.
- All data sources are from the public UCI repository.
- Code is version-controlled and documented.
- Checksums are stored for downloaded datasets (T035).
