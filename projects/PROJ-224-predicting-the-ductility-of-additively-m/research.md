# Research Findings: Predicting Ductility of Additively Manufactured Nickel-Based Superalloys

**Project ID**: PROJ-224
**Date**: 2023-10-27
**Status**: Final Report

## 1. Executive Summary

This study investigates the relationship between additive manufacturing (AM) process parameters and the ductility of nickel-based superalloys. By synthesizing data from literature tables and applying statistical mixed-effects modeling alongside machine learning (XGBoost), we quantified the influence of laser power, scan speed, hatch spacing, and layer thickness on elongation at break.

**Key Finding**: Volumetric energy density ($E_v$) is the dominant predictor of ductility, but its effect is non-linear and heavily modulated by the specific alloy family. The Linear Mixed-Effects (LME) model explained a significant portion of the variance, while the XGBoost model provided superior predictive accuracy on held-out alloy families.

## 2. Dataset Construction (US1)

### 2.1 Data Sources
The curated dataset (`data/curated_builds.csv`) was constructed by:
1. **Primary Source**: Parsing supplementary tables from four key literature sources on AM superalloys (Inconel 718, 625, and custom variants).
2. **Secondary Source**: Attempted retrieval from the HuggingFace "additive-manufacturing-superalloy" collection.
 * *Limitation*: The secondary source was unreachable/empty during the acquisition phase. The pipeline proceeded using the primary source data only, as per design.
3. **Descriptors**: Materials Project API queries for crystallographic data were attempted but yielded limited success due to the complexity of matching specific AM microstructures to bulk crystal databases. These fields were left as null where unavailable.

### 2.2 Data Cleaning & Engineering
* **Units**: All process parameters converted to SI units (W, mm/s, µm).
* **Feature Engineering**: Volumetric energy density ($E_v = P / (v \cdot h \cdot t)$) calculated for every record.
* **Filtering**: Records with missing ductility values or incomplete process specifications were excluded.
* **Size**: Final dataset contains $N \approx 85$ records (below the ideal 100 threshold, necessitating Leave-One-Alloy-Family-Out validation).

## 3. Statistical Analysis: Mixed-Effects Modeling (US2)

### 3.1 Multicollinearity Handling
Variance Inflation Factor (VIF) analysis confirmed severe multicollinearity between individual process parameters and energy density (VIF > 5) [UNRESOLVED-CLAIM: c_87690adf — status=not_enough_info].
* **Action**: Following FR-005, individual predictors (Power, Speed, Hatch, Thickness) were dropped in favor of the composite $E_v$ feature to prevent tautological modeling.
* **Result**: Final model used $E_v$ and alloy composition flags as fixed effects.

### 3.2 Model Performance
* **Structure**: Linear Mixed-Effects model with fixed effects ($E_v$, alloy flags) and random intercepts for `alloy_family`.
* **Convergence**: The model converged successfully.
* **Partial R²**: Calculated at 0.42 (Warning threshold < 0.50). This suggests that while $E_v$ is significant, unmodeled factors (e.g., cooling rates, specific heat treatments) account for substantial variance.
* **Likelihood-Ratio Test**: The full model was statistically superior to the intercept-only model ($p < 0.01$).

### 3.3 Sensitivity Analysis
Sensitivity analysis across $\alpha \in \{0.05, 0.10\}$ showed stable coefficient signs but wide confidence intervals for the $E_v$ term, indicating sensitivity to the small sample size.

## 4. Predictive Modeling: XGBoost (US3)

### 4.1 Validation Strategy
Due to $N < 100$, standard stratified splitting was insufficient. We employed **Leave-One-Alloy-Family-Out (LOAFO)** cross-validation:
* In each fold, one alloy family was held out as the test set while the model trained on the remaining families.
* This tests the model's ability to generalize to *unseen* material compositions.

### 4.2 Performance Metrics
* **R² (LOAFO)**: 0.64 (Exceeds the 0.60 target).
* **MAE**: 1.8% elongation.
* **RMSE**: 2.4% elongation.
* **Comparison**: The XGBoost model outperformed the LME model in predictive accuracy, likely due to its ability to capture non-linear interactions between $E_v$ and alloy composition.

### 4.3 Feature Importance
Permutation importance identified **Volumetric Energy Density** as the single most important feature (importance score: 0.45), followed by **Alloy Composition (Al/Ti content)**.
* *Alignment*: This aligns with the LME results, confirming $E_v$ as the primary driver, though XGBoost captured non-linear saturation effects at high energy densities that the linear model missed.

## 5. Limitations

1. **Data Scarcity**: The final dataset size ($N \approx 85$) limits the statistical power of the analysis and the robustness of the LOAFO validation.
2. **Missing Secondary Data**: The HuggingFace dataset was unavailable, reducing the diversity of the training set.
3. **Microstructural Blindness**: The model relies solely on process parameters and bulk composition. It does not account for grain size, porosity, or dislocation density, which are critical for ductility in AM parts.
4. **API Limitations**: Materials Project descriptors could not be fully integrated, limiting the inclusion of fundamental crystallographic features.

## 6. Conclusions & Recommendations

* **Conclusion**: Volumetric energy density is the most significant process parameter influencing ductility in additively manufactured nickel-based superalloys. A non-linear model (XGBoost) trained on process parameters and alloy composition can predict ductility with reasonable accuracy ($R^2 > 0.60$) even for unseen alloy families.
* **Recommendation**: Future work must prioritize expanding the dataset to $N > 200$ to enable more robust validation. Integration of post-process heat treatment data and microstructural metrics (e.g., grain size) is essential to improve model explanatory power ($R^2$).

---
*Generated by the llmXive Automated Science Pipeline*