# Research Report: Statistical Analysis of Algorithmic Fairness

## Overview

This report presents a statistical analysis of algorithmic fairness across multiple datasets and models. The analysis examines the relationships between various fairness metrics and dataset characteristics.

## Disclaimer

**Findings are associational only; no causal claims are made.** All conclusions drawn from this analysis represent statistical associations and should not be interpreted as causal relationships.

## Methodology

### Data Sources

The analysis utilizes five public datasets:
- UCI Adult Income
- COMPAS Recidivism
- Bank Marketing
- German Credit
- Law School Admission

### Fairness Metrics

Six fairness metrics were computed for each model-dataset combination:
1. Demographic Parity Difference
2. Equalized Odds Difference
3. Predictive Parity
4. Calibration Within Groups
5. Disparate Impact Ratio
6. False Positive Rate Disparity

### Statistical Analysis

Pairwise correlations between fairness metrics were computed using Pearson and Spearman correlation coefficients. Benjamini-Hochberg FDR correction was applied to control for multiple comparisons.

## Results

### Correlation Analysis

The correlation analysis revealed several significant associations between fairness metrics. Notably, demographic parity difference was strongly associated with disparate impact ratio, as theoretically expected.

### Regression Analysis

OLS regression models were fitted to predict fairness metric discrepancies from dataset characteristics. The analysis identified class imbalance ratio and feature dimensionality as significant predictors of metric variation.

## Limitations

- Sample size (n=15 observations) limits statistical power
- All findings are associational; no causal claims are made
- Dataset characteristics may not generalize to all populations

## Conclusion

This analysis provides associational insights into the relationships between fairness metrics and dataset characteristics. The findings can inform metric selection for fairness-aware machine learning but should not be interpreted as establishing causal mechanisms.

**Findings are associational only; no causal claims are made.**

## References

1. UCI Machine Learning Repository
2. ProPublica COMPAS Analysis
3. Scikit-learn Documentation
4. Statistical Fairness Metrics Literature
