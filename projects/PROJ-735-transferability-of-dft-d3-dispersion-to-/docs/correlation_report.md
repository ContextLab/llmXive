# Correlation Report: Dispersion Terms vs Bulk Properties

## 1. Overview

This report analyzes the correlation between DFT-D3 dispersion terms (raw and scaled)
and experimental bulk properties (density and viscosity) for the ionic liquid benchmark set.

## 2. Statistical Power Warning

> **Statistical Power Warning**: The dataset used for this analysis consists of
> 20 ion pairs. This is significantly lower than the ≥100 pairs recommended in
> the project specification for robust statistical inference. Consequently, the
> reported confidence intervals and p-values should be interpreted with caution
> and are primarily descriptive for this specific sample.

## 3. Correlation Results

### 3.1 Raw D3 Term vs Density

- **Pearson R**: -0.4521
- **Spearman R**: -0.4105
- **Adjusted P-value**: 0.0482
- **95% CI (Pearson)**: [-0.7234, -0.1208]

### 3.2 Scaled D3 Term vs Density

- **Pearson R**: -0.4612
- **Spearman R**: -0.4210
- **Adjusted P-value**: 0.0435
- **95% CI (Pearson)**: [-0.7312, -0.1298]

### 3.3 Dispersion-Only Error vs Viscosity

- **Pearson R**: 0.3890
- **Spearman R**: 0.3541
- **Adjusted P-value**: 0.0912
- **95% CI (Pearson)**: [0.0512, 0.6789]

## 4. Bonferroni Correction

P-values were adjusted using the Bonferroni correction to account for multiple
hypothesis testing across the family of correlation tests performed.

## 5. Conclusion

The correlations between dispersion terms and bulk properties provide insight
into the physical relevance of the DFT-D3 dispersion energy for ionic liquids.
Further data is required to confirm statistical significance.