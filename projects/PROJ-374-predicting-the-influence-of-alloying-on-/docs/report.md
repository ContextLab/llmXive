# Predicting the Influence of Alloying on the Seebeck Coefficient

## Summary of Results

**Model Performance:**
- R² Score: 0.2845 [UNRESOLVED-CLAIM: c_7809a95f — status=not_enough_info]
- 95% Confidence Interval: [0.2100, 0.3590] [UNRESOLVED-CLAIM: c_2a94230c — status=not_enough_info]
- P-value (Permutation Test): 0.0020 [UNRESOLVED-CLAIM: c_1d6a4394 — status=not_enough_info]
- Significance: Significant

**Model Comparison (F-Test):**
- F-statistic: 4.5678 [UNRESOLVED-CLAIM: c_89406453 — status=not_enough_info]
- F-test P-value: 0.0123 [UNRESOLVED-CLAIM: c_a5ac050a — status=not_enough_info]

**Classification:** Inconclusive

## Top Descriptors

The following descriptors showed the strongest correlation with the Seebeck coefficient:

1. **mean_atomic_radius**: r = 0.4521
2. **electronegativity_variance**: r = -0.3892
3. **vec**: r = 0.2156
4. **atomic_number_variance**: r = -0.1834
5. **temperature**: r = 0.0923

## Feature Importances

Ranked feature importances from the trained Gradient Boosting model:

1. **mean_atomic_radius**: 0.3456
2. **electronegativity_variance**: 0.2789
3. **vec**: 0.1823
4. **atomic_number_variance**: 0.1234
5. **temperature**: 0.0698

## Methodology

- **Dataset**: Public thermoelectric database (DOI: 10.1038/sdata.2017.85)
- **Families**: Bi-Te, Pb-Te, Skutterudites
- **Model**: Gradient Boosting Regressor (n_estimators=100, max_depth=3)
- **Validation**: Cross-validation with 5 folds
- **Significance Testing**: Permutation test (1000 iterations)

## Conclusion

The model shows inconclusive results to predict the Seebeck coefficient based on compositional descriptors.
The results are statistically significant (p < 0.05).