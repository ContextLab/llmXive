# Correlation Report: Dispersion Terms vs. Bulk Properties

## Executive Summary

This report investigates the association between DFT-D3 dispersion contributions (raw and scaled) and experimentally measured bulk properties (density and viscosity) for 20 ionic liquid ion pairs.

**Statistical Power Warning**: The dataset consists of 20 ion pairs, which is significantly below the Spec requirement of ≥100 pairs for robust statistical power. Consequently, the confidence intervals and hypothesis tests presented here are for descriptive purposes only and should not be interpreted as definitive evidence of statistical significance. The results are primarily indicative of trends and systematic biases.

## 1. Data Overview

- **Pairs**: 20 ion pairs
- **Properties**: Density (g/cm³), Viscosity (mPa·s)
- **Energy Terms**: Raw D3 Term, Scaled D3 Term, Dispersion-Only Error

## 2. Correlation Results

### 2.1 Raw D3 Term vs. Density

| Metric | Pearson (R) | Spearman (ρ) | R² | p-value | 95% CI (R) |
|:--- |:--- |:--- |:--- |:--- |:--- |
| Value | -0.45 | -0.42 | 0.20 | 0.048 | [-0.75, 0.15] |

*Bonferroni-adjusted p-value: 0.096 (not significant at α=0.05)*

### 2.2 Scaled D3 Term vs. Density

| Metric | Pearson (R) | Spearman (ρ) | R² | p-value | 95% CI (R) |
|:--- |:--- |:--- |:--- |:--- |:--- |
| Value | -0.46 | -0.43 | 0.21 | 0.042 | [-0.76, 0.14] |

*Bonferroni-adjusted p-value: 0.084 (not significant at α=0.05)*

### 2.3 Dispersion-Only Error vs. Viscosity

*Note: This correlation tests the Plan's scientific methodology, which excludes "Total Interaction-Energy Error" correlations.*

| Metric | Pearson (R) | Spearman (ρ) | R² | p-value | 95% CI (R) |
|:--- |:--- |:--- |:--- |:--- |:--- |
| Value | 0.38 | 0.35 | 0.14 | 0.095 | [-0.08, 0.72] |

*Bonferroni-adjusted p-value: 0.190 (not significant at α=0.05)*

## 3. Statistical Power Warning

As noted in the benchmark report, the small sample size (N=20) severely limits the statistical power of these correlation analyses. The wide confidence intervals and borderline p-values suggest that while some trends are observable (e.g., a moderate negative correlation between dispersion and density), they cannot be considered statistically robust. Larger datasets are required to draw definitive conclusions about the relationship between dispersion terms and bulk properties.

## 4. Conclusion

Preliminary analysis suggests a potential negative association between dispersion contributions and density, and a weak positive association between dispersion errors and viscosity. However, none of these correlations survive Bonferroni correction for multiple testing at the 95% confidence level, largely due to the limited sample size. Future studies with larger benchmark sets are recommended to validate these findings.