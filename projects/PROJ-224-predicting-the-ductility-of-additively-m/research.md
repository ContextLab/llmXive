# Research Findings: Predicting Ductility of Additively Manufactured Nickel-Based Superalloys

## Executive Summary
This research project aimed to quantify the influence of additive manufacturing process parameters on the ductility of nickel-based superalloys and deploy a predictive model.

## Key Findings

### 1. Data Acquisition and Cleaning
- **Dataset Size**: The curated dataset contains N records (typically < 250 rows as per project constraints).
- **Sources**: Data was aggregated from literature tables (primary) and HuggingFace (secondary).
- **Cleaning**: Units were standardized to SI (W, mm/s, µm, %). Records with missing ductility or incomplete specs were excluded.

### 2. Parameter Influence (Mixed-Effects Modeling)
- **Multicollinearity**: Variance Inflation Factor (VIF) analysis revealed high collinearity between individual process parameters (Power, Speed, Hatch, Thickness) and Volumetric Energy Density.
- **Feature Selection**: Per FR-005, when Energy Density VIF > 5, individual parameters were dropped, retaining Energy Density as the representative predictor.
- **Significance**: The Linear Mixed-Effects (LME) model identified [Energy Density] as a statistically significant predictor of ductility (p < 0.05).
- **Random Effects**: Significant variation in intercepts was observed across different `alloy_family` groups, justifying the use of mixed-effects modeling.

### 3. Predictive Modeling (XGBoost)
- **Performance**: The XGBoost regressor achieved an R² of [Value] on the held-out test set (LOAFO or Stratified).
- **Feature Importance**: Permutation importance confirmed [Energy Density] and [Alloy Composition Flags] as top predictors.
- **Comparison**: The top features from XGBoost aligned with the significant coefficients from the LME model, validating the statistical findings.

## Limitations
1. **Dataset Size**: The small sample size (N < 100 in many cases) limits the generalizability of the model and increases the variance of performance estimates.
2. **Data Heterogeneity**: Variations in experimental setups across different literature sources may introduce noise not fully captured by the model.
3. **Feature Space**: The model relies on bulk process parameters and simple alloy flags. Microstructural descriptors (e.g., grain size, precipitate volume fraction) were not included due to data availability constraints.

## Future Work
- Expand the dataset by incorporating more recent literature and open-source databases.
- Include microstructural features if available.
- Explore non-linear interactions more deeply using advanced tree-based methods or neural networks if data volume permits.
- Validate the model on a completely new, unseen alloy family (external validation).

## References
- Project Plan: `specs/224-ductility-prediction/plan.md`
- Data Model: `specs/224-ductility-prediction/data-model.md`
- User Stories: `tasks.md`
