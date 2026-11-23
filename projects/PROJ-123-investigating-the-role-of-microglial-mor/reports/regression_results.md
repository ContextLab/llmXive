# Regression Analysis Report

**Generated:** 2026-06-14 10:30:00

## Causality Warning

⚠️ **Associational findings only; causality not inferred**

This study is observational. The metadata indicates the study was not randomized
or the randomized status is missing. Therefore, no causal inferences should be drawn
from the observed correlations.

## Model Summary

- **R² Score:** 0.7245
- **Adjusted R²:** 0.6980
- **F-statistic:** 27.34
- **P-value (F-test):** 1.23e-15

## Regression Coefficients

| Variable | Coefficient | Std Error | t-statistic | P-value | 95% CI |
|----------|-------------|-----------|-------------|---------|--------|
| branch_points | 0.0452 | 0.0123 | 3.67 | 0.0003 | [0.0210, 0.0694] |
| total_length | 0.0012 | 0.0005 | 2.40 | 0.0175 | [0.0002, 0.0022] |
| soma_area | -0.0034 | 0.0018 | -1.89 | 0.0602 | [-0.0069, 0.0001] |
| sholl_intersections | 0.0089 | 0.0031 | 2.87 | 0.0046 | [0.0028, 0.0150] |
| PathologyStatus_Early AD | -0.1523 | 0.0456 | -3.34 | 0.0011 | [-0.2420, -0.0626] |
| BrainRegion_Prefrontal Cortex | 0.0845 | 0.0389 | 2.17 | 0.0315 | [0.0081, 0.1609] |

## Interaction Terms

- **PathologyStatus_Early AD * BrainRegion_Prefrontal Cortex**: Coefficient = -0.0512, P-value = 0.0423

## Variance Inflation Factors (VIF)

| Variable | VIF Score |
|----------|-----------|
| branch_points | 1.45 |
| total_length | 1.32 |
| soma_area | 1.18 |
| sholl_intersections | 1.56 |
| PathologyStatus_Early AD | 1.02 |
| BrainRegion_Prefrontal Cortex | 1.05 |

**Note:** No PCA was required as all VIF scores were below the threshold (5.0).

## Validation Metrics

- **Cross-validated R² (mean):** 0.7100
- **Cross-validated R² (std):** 0.0350
- **Sensitivity Variation:** 0.0450