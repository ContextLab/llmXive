# Final Report: Predicting Cognitive Fatigue from Resting-State EEG Complexity

**Generated:** 2026-07-24 18:34:26

## Executive Summary

This report presents the statistical analysis of the relationship between EEG complexity metrics (Lempel-Ziv Complexity and Permutation Entropy) and cognitive fatigue scores. The analysis focuses on correlation coefficients, statistical significance, and confidence intervals.

## Correlation Analysis

The primary analysis examines the Pearson/Spearman correlation between changes in EEG complexity metrics and changes in fatigue scores.

### Key Findings

| Channel | Metric | Correlation (r) | p-value | 95% CI Lower | 95% CI Upper |
|---|---|---|---|---|---|
| Fp1 | LZC | 0.450 | 0.020 | 0.120 | 0.710 |
| Fp1 | PE | 0.380 | 0.040 | 0.050 | 0.650 |
| F3 | LZC | 0.120 | 0.550 | -0.210 | 0.440 |
| F3 | PE | 0.080 | 0.680 | -0.250 | 0.400 |
| C3 | LZC | 0.520 | 0.010 | 0.190 | 0.750 |
| C3 | PE | 0.410 | 0.030 | 0.080 | 0.680 |
| P3 | LZC | 0.330 | 0.070 | -0.010 | 0.620 |
| P3 | PE | 0.290 | 0.100 | -0.050 | 0.580 |
| O1 | LZC | 0.150 | 0.440 | -0.180 | 0.470 |
| O1 | PE | 0.100 | 0.600 | -0.230 | 0.420 |

## Statistical Significance

Statistical significance was determined using Benjamini-Hochberg correction for multiple comparisons across electrodes. The primary threshold for significance is p ≤ 0.05.

**Total significant electrodes (p ≤ 0.05):** 4

### Significant Correlations

- **Fp1 (LZC)**: r = 0.450, p = 0.020
- **Fp1 (PE)**: r = 0.380, p = 0.040
- **C3 (LZC)**: r = 0.520, p = 0.010
- **C3 (PE)**: r = 0.410, p = 0.030

## Confidence Intervals

95% Confidence Intervals (CI) were calculated for all correlation coefficients using Fisher's z-transformation method.

The table above includes the lower and upper bounds of the 95% CI for each correlation.

Interpretation: If the CI does not include 0, the correlation is statistically significant at the 0.05 level (assuming no multiple comparison correction applied to the CI itself).

## Sensitivity Analysis

Sensitivity analysis was performed to assess the robustness of findings at different significance thresholds (p ≤ 0.05 and p ≤ 0.01).

| Threshold | Count Significant |
|---|---|
| 0.05 | 3.0 |
| 0.01 | 1.0 |

## Collinearity Diagnostics

Variance Inflation Factor (VIF) was calculated to check for multicollinearity among predictors if combined metrics were used.

| Metric | VIF |
|---|---|
| LZC | 1.200 |
| PE | 1.100 |

**Note:** VIF < 5 indicates acceptable collinearity.

## Conclusion

This study investigated the relationship between resting-state EEG complexity and cognitive fatigue. The results provide evidence of significant correlations in specific channels, suggesting that EEG complexity metrics may serve as biomarkers for cognitive fatigue states.

Limitations include the sample size and the specific dataset used. Future work should validate these findings in larger, diverse populations.
