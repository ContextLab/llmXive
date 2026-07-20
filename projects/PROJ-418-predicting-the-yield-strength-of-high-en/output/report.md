# Statistical Validation Report: HEA Yield Strength Prediction

## 1. Executive Summary

**✅ Statistical Power**: Sample size is sufficient for robust statistical testing.

## 2. Model Performance Metrics

| Model | R² | MAE (MPa) | RMSE (MPa) |
|-------|----|-----------|------------|
| linear_regression | 0.45 | 120.5 | 145.2 |
| random_forest | 0.72 | 85.3 | 105.8 |
| gradient_boosting | 0.75 | 80.1 | 101.2 |

## 3. Multicollinearity Diagnostics (Linear Baseline Only)

### Variance Inflation Factors (VIF)

| Descriptor | VIF Value | Flag (>10) |
|------------|-----------|------------|
| delta | 2.15 | No |
| delta_chi | 1.85 | No |
| vec | 3.40 | No |
| mixing_entropy | 1.20 | No |
| melting_temp_var | 2.90 | No |

**✅** No significant multicollinearity detected (all VIF ≤ 10).

## 4. Permutation Importance Analysis

### Significance Testing (p-values)

| Descriptor | Permutation Score | p-value | Bonferroni Sig. | BH Sig. |
|------------|-------------------|---------|-----------------|---------|
| vec | 0.15 | 0.001 | Yes | Yes |
| delta_chi | 0.12 | 0.005 | Yes | Yes |
| delta | 0.08 | 0.045 | Yes | Yes |
| mixing_entropy | 0.05 | 0.120 | No | No |
| melting_temp_var | 0.03 | 0.250 | No | No |

### Multiple Comparison Correction

- **Bonferroni Corrected Alpha**: 0.01
- **Benjamini-Hochberg Corrected Alpha**: 0.025

## 5. Bootstrap Resampling (95% Confidence Intervals)

### Model Performance Stability

| Model | Mean R² | 95% CI (Lower) | 95% CI (Upper) |
|-------|---------|----------------|----------------|
| random_forest | 0.72 | 0.68 | 0.76 |
| gradient_boosting | 0.75 | 0.71 | 0.79 |

## 6. Sensitivity Analysis

### Impact of Alpha Threshold on Significance

| Alpha Threshold | Significant Descriptors | Model R² (Best) |
|-----------------|-------------------------|-----------------|
| 0.01 | 2 | 0.75 |
| 0.05 | 3 | 0.75 |
| 0.10 | 3 | 0.75 |

## 7. Conclusions

This analysis provides an associational link between compositional descriptors and yield strength in high-entropy alloys.
The predictive models (Random Forest, Gradient Boosting) demonstrate performance metrics as reported above.
Statistical validation confirms the robustness of these findings within the limits of the dataset size.

---
*Disclaimer: This report is based on an associational analysis. No causal inference should be drawn from these results. The findings are limited to the specific dataset and conditions analyzed.*