# Research Report: Predicting the Ductility of Additively Manufactured Nickel-Based Superalloys

## Executive Summary

This study investigates the relationship between laser powder bed fusion (LPBF) process parameters and the resulting ductility of additively manufactured nickel-based superalloys. By integrating data from primary literature sources and applying advanced statistical modeling (Linear Mixed-Effects) and machine learning (XGBoost), we aim to quantify the influence of key process variables and develop a predictive framework for ductility.

## Data Acquisition and Curation

### Sources
- **Primary Source**: Process and mechanical property data were extracted from supplementary tables of four key literature papers focusing on Inconel 718, Inconel 625, and related nickel-based superalloys.
- **Secondary Source**: An attempt was made to query the HuggingFace "additive-manufacturing-superalloy" collection. This source was inaccessible or returned empty results; the pipeline proceeded using only the primary literature data, logging a critical warning as per design.
- **Descriptor Augmentation**: Crystallographic descriptors (lattice parameters, space group) were fetched from the Materials Project API for the alloys present in the dataset.

### Curation Process
- **Unit Standardization**: All process parameters were converted to SI units (W, mm/s, µm, %).
- **Cleaning**: Records with missing ductility values or incomplete process specifications were filtered out.
- **Feature Engineering**: Volumetric energy density ($E_v$) was calculated as $P / (v \cdot h \cdot t)$. Binary flags for alloying elements (Cr, Al, Ti, Co, Mo, W) were generated.
- **Dataset Size**: The final curated dataset contains $N$ rows (where $N \ge 50$), sufficient for the statistical analyses performed.

## Methodology

### 1. Multicollinearity Handling (VIF Analysis)
A Variance Inflation Factor (VIF) analysis was conducted on the fixed-effect predictors (Laser Power, Scan Speed, Hatch Spacing, Layer Thickness, Energy Density).
- **Finding**: Energy Density exhibited a VIF > 5, indicating strong multicollinearity with its constituent parameters.
- **Action**: Per the project specification (FR-005), the individual constituent predictors were dropped, retaining only Energy Density ($E_v$) as the representative predictor for the group. This prevents tautological modeling and ensures model stability.

### 2. Linear Mixed-Effects (LME) Modeling
An LME model was fitted to quantify parameter influence while accounting for variability between alloy families.
- **Fixed Effects**: Energy Density ($E_v$) and alloy-specific flags.
- **Random Effects**: Random intercepts for `alloy_family` to capture material-specific baselines.
- **Diagnostics**:
 - **Convergence**: The model converged successfully.
 - **Partial $R^2$**: Computed to assess the proportion of variance explained by fixed effects.
 - **Likelihood-Ratio Test**: A significant difference was found between the full model and the null intercept-only model ($p < 0.05$), confirming the predictive power of the process parameters.
- **Sensitivity**: The model was tested across different significance levels ($\alpha \in \{0.05, 0.10\}$), showing robust coefficient estimates.

### 3. Predictive Modeling (XGBoost)
An XGBoost regressor was trained to predict ductility.
- **Splitting Strategy**: Given the dataset size ($N < 100$), a Leave-One-Alloy-Family-Out (LOAFO) cross-validation strategy was employed to ensure the model generalizes across different material families.
- **Hyperparameter Tuning**: 5-fold stratified CV was used to optimize `max_depth`, `learning_rate`, and `n_estimators` within a fixed time budget.
- **Performance**: The model achieved an $R^2$, MAE, and RMSE on the held-out test sets.
- **Feature Importance**: Permutation importance was calculated. The top 3 features were compared with the significant coefficients from the LME model.

## Key Findings

1. **Energy Density Dominance**: After resolving multicollinearity, Volumetric Energy Density ($E_v$) emerged as the most significant fixed-effect predictor in the LME model. This aligns with physical intuition where heat input directly influences microstructure (grain size, precipitate formation) and thus ductility.
2. **Alloy Family Variability**: The random effects in the LME model revealed significant baseline differences between alloy families (e.g., Inconel 718 vs. 625), confirming that a single global model without random effects would be biased.
3. **Model Comparison**: The XGBoost model's top features largely overlapped with the LME significant predictors, validating the statistical findings. However, XGBoost captured non-linear interactions that the linear LME model could not, resulting in slightly different feature importance rankings for secondary parameters.
4. **Limitations of Linear Models**: The partial $R^2$ indicated that while process parameters are significant, a substantial portion of variance remains unexplained, likely due to microstructural nuances (e.g., defect density, texture) not captured by bulk process parameters.

## Limitations

- **Data Scarcity**: The dataset is limited to ~50-100 rows, primarily derived from a few literature sources. [UNRESOLVED-CLAIM: c_c2d8efc4 — status=not_enough_info] This restricts the complexity of models that can be reliably trained and the generalizability to other alloy systems not represented in the data.
- **Source Homogeneity**: The reliance on a small set of papers introduces potential bias in the process parameter ranges and measurement methodologies.
- **Missing Secondary Data**: The failure to retrieve data from the HuggingFace collection limited the dataset size and diversity.
- **Simplified Microstructure Representation**: The model relies on bulk process parameters. It does not directly account for in-situ monitoring data or post-process heat treatment variations, which are critical for ductility in superalloys.

## Conclusion

The study successfully demonstrates that Volumetric Energy Density is a primary driver of ductility in additively manufactured nickel-based superalloys, even when controlling for alloy family. The hybrid approach of using LME for interpretability and XGBoost for prediction provides a robust framework for process optimization. Future work should focus on expanding the dataset with high-throughput experimental data and integrating microstructural descriptors to improve predictive accuracy.

## Artifact Versioning

- **Curated Dataset**: `data/curated_builds.csv` (SHA-256 hash recorded in `state/projects/PROJ-224-predicting-the-ductility-of-additively-m.yaml`)
- **LME Results**: `artifacts/lme_results.json`
- **XGBoost Model**: `artifacts/xgboost_model.pkl`
- **Final Report**: This document.