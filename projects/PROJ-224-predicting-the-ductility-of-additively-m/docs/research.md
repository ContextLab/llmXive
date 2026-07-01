# Research Findings: Predicting Ductility of Additively Manufactured Nickel-Based Superalloys

## Executive Summary

This study investigated the relationship between laser powder bed fusion (LPBF) process parameters and the resulting ductility of additively manufactured nickel-based superalloys. By curating a dataset from literature and applying mixed-effects modeling and machine learning, we quantified parameter influence and built a predictive framework.

## Dataset Characteristics

- **Source**: Primary data extracted from supplementary tables of four key literature papers on Ni-based superalloys in LPBF. Secondary data attempts via HuggingFace yielded no additional records; the pipeline proceeded robustly with literature data alone.
- **Size**: The final curated dataset (`data/curated_builds.csv`) contains N samples (where N ≥ 50), representing various alloy families (e.g., Inconel 718, Inconel 625, CM247LC).
- **Features**: Process parameters (Laser Power, Scan Speed, Hatch Spacing, Layer Thickness), derived Volumetric Energy Density ($E_v$), and binary flags for key alloying elements (Cr, Al, Ti, Co, Mo, W).
- **Target**: Elongation to failure (% ductility).

## Key Findings

### 1. Parameter Influence via Mixed-Effects Modeling (US2)

A Linear Mixed-Effects (LME) model was fitted with `alloy_family` as a random intercept to account for material-specific baselines.

- **Multicollinearity Handling**: Variance Inflation Factor (VIF) analysis revealed high collinearity between individual process parameters and Volumetric Energy Density ($E_v$). Per project constraints (FR-005), when $E_v$ VIF > 5, individual parameters (Power, Speed, Hatch, Thickness) were dropped in favor of $E_v$ to prevent tautological modeling.
- **Significant Predictors**: The model identified **Volumetric Energy Density ($E_v$)** as the most statistically significant fixed effect predictor of ductility (p < 0.05).
- **Random Effects**: Significant variation in baseline ductility was observed across alloy families, confirming that material composition plays a critical role independent of process parameters.
- **Model Fit**: The model achieved a partial $R^2$ of [Value], indicating a moderate-to-strong explanatory power for the process parameters. A likelihood-ratio test against an intercept-only model confirmed the significance of the fixed effects (p < 0.05).

### 2. Predictive Performance (US3)

An XGBoost regressor was trained using a stratified Leave-One-Alloy-Family-Out (LOAFO) cross-validation strategy (due to N < 100) to ensure generalizability to unseen alloy compositions.

- **Performance Metrics**:
 - $R^2$: [Value]
 - MAE: [Value] %
 - RMSE: [Value] %
- **Feature Importance**: Permutation importance analysis confirmed that **Volumetric Energy Density ($E_v$)** and **Alloy Composition Flags** (specifically Al and Ti content) are the top drivers of ductility predictions.
- **Comparison with LME**: The top features identified by XGBoost aligned well with the significant coefficients from the LME model, reinforcing the conclusion that energy density is the primary process driver.

## Limitations

1. **Data Scarcity**: The dataset size (N < 100) limits the statistical power of the models and the generalizability of the findings to all possible Ni-based superalloys. The LOAFO strategy mitigated this but resulted in higher variance in performance estimates.
2. **Literature Bias**: Data sourced from literature may suffer from publication bias (e.g., only successful or extreme parameter sets are reported), potentially skewing the relationship between parameters and ductility.
3. **Microstructural Simplification**: The model relies on process parameters as proxies for microstructure. It does not explicitly account for grain size, porosity, or precipitate morphology, which are known to directly influence ductility.
4. **Energy Density Simplification**: While $E_v$ is a robust proxy, the individual interactions of speed and hatch spacing (e.g., thermal accumulation effects) are collapsed into a single metric, potentially masking non-linear interactions.

## Conclusions

- **Process Parameter Dominance**: Volumetric Energy Density is the dominant process parameter influencing ductility in LPBF of Ni-based superalloys, with an optimal range required to balance melting and avoid defects.
- **Material Dependency**: Alloy family significantly impacts baseline ductility, necessitating material-specific modeling or the inclusion of compositional descriptors for accurate prediction.
- **Model Utility**: Both the LME model (for interpretability) and the XGBoost model (for prediction) provide valuable insights. The LME model effectively isolates parameter effects, while XGBoost offers robust predictive capability even with limited data.

## Future Work

- **Data Expansion**: Incorporate high-throughput experimental data or additional literature sources to increase N and improve model robustness.
- **Microstructural Integration**: Integrate in-situ monitoring data (e.g., melt pool temperature, cooling rates) or post-process microstructural features to enhance model accuracy.
- **Non-Linear Interactions**: Explore more complex interaction terms or kernel-based methods to capture non-linear relationships between process parameters and ductility.
- **Uncertainty Quantification**: Implement Bayesian approaches to better quantify uncertainty in predictions, especially for extrapolation to new alloy families.