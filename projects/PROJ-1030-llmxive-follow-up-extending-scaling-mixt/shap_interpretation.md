# Feature Importance Interpretation Report

## Disclaimer: Associational Findings Only

This report presents **associational** findings derived from the trained classifier.
All correlations and feature importances identified here are **not causal**.
The model learns patterns from observational data, and these patterns do not imply
that changing a feature will necessarily change the outcome in a real-world setting.
Refer to FR-007 for the required associational framing.

## Methodology

Feature importance was assessed using **SHAP (SHapley Additive exPlanations)** values,
which measure the contribution of each feature to the model's prediction for individual samples.
Mean absolute SHAP values across the test set were used to rank global feature importance.
Permutation importance was also computed as a secondary validation metric.

## Top Features by Mean Absolute SHAP Value

| Rank | Feature | Mean |Abs| SHAP |
|------|---------|--------|
| 1 | feature_2 | 0.1333 |
| 2 | feature_1 | 0.0833 |
| 3 | feature_3 | 0.0667 |

## Key Limitations

- SHAP values indicate feature contribution to prediction, not causality.
- Correlation does not imply causation.
- Results are specific to the trained model and dataset.

## Conclusion

The identified features are strongly associated with the model's predictions of physical validity.
However, these associations should not be interpreted as evidence of causal relationships.
Further experimental validation would be required to establish causality.
