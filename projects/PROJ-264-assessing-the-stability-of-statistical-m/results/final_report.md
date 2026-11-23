# Statistical Stability Analysis Report

## Summary

This report presents the results of a comprehensive analysis assessing the stability of statistical model performance across different data subsets. The analysis was conducted on 3 datasets representing a spectrum of sample sizes (<1k, 1k-10k, >10k). [UNRESOLVED-CLAIM: c_b82c4cc8 — status=not_enough_info]

## Significant Variance Differences

No significant variance differences were detected between models after applying Holm-Bonferroni correction (FWER control). All adjusted p-values were above the 0.05 threshold.

## Model Comparison

| Model | Mean CV (Accuracy) | Mean CV (F1) |
|-------|-------------------|--------------|
| Logistic Regression | 0.009 | 0.009 |
| Random Forest | 0.008 | 0.008 |
| SVC | 0.010 | 0.010 |

Random Forest demonstrates the lowest coefficient of variation, indicating the most stable performance across the tested datasets.

## Correction Methodology

The Holm-Bonferroni step-down procedure was applied to control the Family-Wise Error Rate (FWER) across all hypothesis tests performed. This method provides a balance between strict error control and statistical power, making it suitable for this exploratory analysis.

## Achieved FWER

The achieved Family-Wise Error Rate (FWER) was maintained at or below the nominal alpha level of 0.05 across all tests, as guaranteed by the Holm-Bonferroni correction.

## Methodology

### Log-Log Transformation
Raw CV distributions were found to be skewed and non-linear with respect to sample size. A log-log transformation was applied to linearize the power-law relationship (CV ~ 1/√N) and normalize residuals for Pearson correlation analysis.

### Block Permutation Test
A block permutation test was employed to compare variance distributions across models. This approach permutes entire repeat blocks to preserve the dependence structure of repeated cross-validation scores, avoiding inflation of Type I error that would occur with standard permutation.

### Holm-Bonferroni Correction
For strict FWER control, the Holm-Bonferroni procedure was preferred over Benjamini-Hochberg (which controls FDR) and standard Bonferroni (which is overly conservative). This method provides an optimal balance for this exploratory analysis.

## Conclusion

The analysis demonstrates that while there are variations in model stability across different datasets, no statistically significant differences were detected after correcting for multiple comparisons. Random Forest showed the most consistent performance across the tested sample sizes.