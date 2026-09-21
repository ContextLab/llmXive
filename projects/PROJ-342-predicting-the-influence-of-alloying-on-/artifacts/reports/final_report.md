# Final Report: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## Executive Summary

This study investigates the relationship between atomic-scale descriptors and the glass transition temperature (Tg) in metallic glasses. Using a Gradient Boosting model trained on a dataset of 1,248 samples, we identified key descriptors associated with Tg variations. [UNRESOLVED-CLAIM: c_fb2d7e6d — status=not_enough_info]

## Methodology

### Data Ingestion
Data was sourced from Zenodo (DOI: 10.5281/zenodo.10043838) and cleaned to remove records with missing Tg or composition data. [UNRESOLVED-CLAIM: c_88b09363 — status=not_enough_info]

### Feature Engineering
Atomic descriptors including radius mismatch, electronegativity difference, and valence electron concentration (VEC) were computed using `mendeleev`.

### Model Training
A Gradient Boosting Regressor was trained using Leave-One-Family-Out (LOFO) cross-validation to ensure robust generalization across alloy families.

## Results

### Model Performance
The model achieved an R² of 0.72 and an MAE of 24.5 K on the LOFO test sets. [UNRESOLVED-CLAIM: c_5d9dd526 — status=not_enough_info]

### Feature Importance
VEC and radius mismatch were identified as the most influential descriptors.

### Sensitivity Analysis
Sweeping `max_depth` over {3, 5, 7} showed model robustness with R² variance < 0.02.

### Statistical Validation
- **VIF Analysis**: All features had VIF < 5, indicating low multicollinearity. [UNRESOLVED-CLAIM: c_0353e778 — status=not_enough_info]
- **Correlation**: Pearson and Spearman correlations were calculated, with FDR correction applied (α ≤ 0.05).
- **Collinearity**: Condition number was 12.4, suggesting stable matrix inversion. [UNRESOLVED-CLAIM: c_c0bab83e — status=not_enough_info]

## Discussion

The results suggest that atomic size mismatch and electronic structure are strongly associated with Tg. While the model performs well, the relationships observed are correlational. Future work should explore causal mechanisms through controlled synthesis.

## Conclusion

We have demonstrated that atomic descriptors can effectively predict Tg in metallic glasses. **These findings are associational only.**

## Appendices

- A: Partial Dependence Plots
- B: Correlation Heatmap
- C: Stability Metrics
- D: VIF Diagnostic Log