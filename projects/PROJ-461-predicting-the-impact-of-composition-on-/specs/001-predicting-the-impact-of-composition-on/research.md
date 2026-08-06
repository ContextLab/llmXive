# Research: Predicting the Impact of Composition on the Density of Metallic Glasses

## Problem Statement

Metallic glasses (MGs) possess unique mechanical properties, but their density prediction is often limited to simple linear mixing rules which ignore atomic packing effects. This project investigates whether incorporating atomic-level descriptors (radius mismatch, packing efficiency) derived from elemental composition improves density prediction accuracy (MAE ≤ 0.1 g/cm³) over a baseline linear mixing rule.

## Dataset Strategy

### Verified Sources
*Note: Primary source is the UCI Machine Learning Repository. No synthetic fallback is used.*

The following datasets were evaluated for availability and content:
- **Primary Source**: UCI Machine Learning Repository "Metallic Glasses" (ID: 469). This dataset contains experimental metallic glass compositions and densities.
  - **URL**: `https://archive.ics.uci.edu/dataset/469/metallic+glasses`
  - **Access**: Programmatic via `ucimlrepo` library.
  - **Content**: Real experimental data containing elemental mass fractions and bulk densities.
- **Fallback Source**: None. The project relies exclusively on real experimental data.

**Decision**: The pipeline will fetch the UCI ID 469 dataset. If the dataset is <100 rows, the system halts with `E_DATA_INSUFFICIENT` as per Spec.

### Dataset Variables
- **Inputs**: Elemental mass fractions (e.g., `Zr`, `Cu`, `Al`, `Ni`, `Ti`, etc.).
- **Target**: Bulk Density (g/cm³).
- **Derived Features**: Mean Atomic Mass, Mean Atomic Radius, Electronegativity Variance, Atomic Radius Mismatch, Packing Efficiency Proxy.

### Data Availability Risks
- **Risk**: No open source for MG density.
- **Mitigation**: The UCI ID 469 dataset is a verified open source. If it is insufficient, the project halts rather than using synthetic data.

## Methodology

### Feature Engineering
1. **Normalization**: Convert all elemental symbols to IUPAC standard (e.g., "Fe", "Cu").
2. **Atomic Properties Lookup**: Use `mendeleev` to fetch atomic mass, atomic radius, and electronegativity for each element.
3. **Baseline Calculation**: Compute the **Linear Mixing Rule** baseline: $\rho_{baseline} = \sum (w_i \times \rho_i)$, where $\rho_i$ is the standard elemental density.
4. **Residual Target**: Calculate $y_{residual} = \rho_{actual} - \rho_{baseline}$. The model will predict this residual, not the absolute density.
5. **Descriptor Calculation**:
   - **Mean Atomic Mass**: $\sum (w_i \times M_i)$
   - **Mean Atomic Radius**: $\sum (w_i \times R_i)$
   - **Electronegativity Variance**: Variance of electronegativity weighted by mass fraction.
   - **Atomic Radius Mismatch**: $\delta = \sqrt{\sum c_i (1 - R_i/\bar{R})^2}$ (where $c_i$ is atomic fraction, derived from mass fraction).
   - **Packing Efficiency Proxy**: $P_{eff} = \delta \times \sqrt{|\Delta H_{mix}|}$. Here, $\Delta H_{mix}$ is the **Mixing Enthalpy** calculated using Miedema's rules (pairwise enthalpy of formation), which introduces a non-linear, chemical interaction term distinct from simple radius mismatch. This breaks the linear dependency between $\delta$ and $P_{eff}$.
6. **Collinearity Mitigation**: Apply a Centered Log-Ratio (clr) transform to the compositional features (mass fractions) before deriving atomic properties to mitigate the "sum-to-one" constraint.
7. **Collinearity Check**: Calculate Variance Inflation Factor (VIF) for all derived features. If VIF > 5 for any feature, it will be flagged and potentially removed or combined.

### Model Training
- **Algorithm**: LightGBM Regressor (CPU version).
- **Target**: **Residual Density** ($y_{residual}$), not absolute density. This isolates the non-linear packing effects.
- **Validation**: Stratified K-Fold (k=5) based on the dominant element (highest mass fraction).
- **Hyperparameters**: Default or grid search within CPU time limits.
- **Baseline**: Linear Mixing Rule ($\rho_{baseline} = \sum w_i \rho_i$). The model's performance is measured by how well it predicts the *deviation* from this baseline.

### Statistical Significance Test (SC-003)
To validate that packing descriptors significantly improve prediction accuracy (SC-003), a **Nested F-Test** (or Likelihood Ratio Test) will be performed:
1. **Model A (Null)**: Predicts residual density using only `Dominant_Element` (categorical) and `Mean_Atomic_Mass`.
2. **Model B (Alternative)**: Predicts residual density using Model A features + `Atomic_Radius_Mismatch` and `Packing_Efficiency_Proxy`.
3. **Test**: Compare the R² of Model A and Model B. If the increase in R² is statistically significant (p < 0.05), SC-003 is validated.

### Evaluation Metrics
- **Primary**: Mean Absolute Error (MAE) of the *residual* prediction vs. 0.1 g/cm³ threshold.
- **Secondary**: R² score of the residual model.
- **Robustness**: Sensitivity analysis (sweeping density thresholds).
- **Hypothesis Test**: If MAE > 0.1, use **SHAP Interaction Values** and **Partial Dependence Plots (PDP)** to explicitly quantify the variance explained by `radius mismatch` and `packing efficiency` descriptors.

## Statistical Rigor
- **Multiple Comparisons**: Not applicable for a single regression model, but SHAP values will be used for feature importance ranking.
- **Sample Size**: Target ≥100. If <100, the system halts with `E_DATA_INSUFFICIENT`.
- **Collinearity**: Addressed by using **clr transform** on compositional inputs, predicting the **residual** (which removes the dominant linear mass effect), and performing a **VIF check** before modeling. The `P_eff` feature uses $\Delta H_{mix}$ (chemical interaction) to ensure it is not collinear with $\delta$ (geometric size).
- **Causal Claims**: The study is observational. Claims will be framed as "associational" or "predictive," not causal.

## Compute Feasibility
- **CPU-First**: LightGBM is highly optimized for CPU. The dataset size (≤1000 rows) fits easily in 7GB RAM.
- **GPU Escape Hatch**: Not required. The model is small and CPU-tractable.
- **Execution**: Entire pipeline < 2 hours on GitHub Actions free tier.

## Decision/Rationale
- **Method**: LightGBM chosen for speed and ability to handle non-linear relationships in atomic packing.
- **Dataset**: Plan explicitly anchors on UCI ID 469 as the verified open source. No synthetic fallback is used.
- **Baseline**: Linear mixing rule is the standard scientific baseline for density prediction. The model predicts the *residual* to isolate packing effects.
- **Feature Engineering**: `P_eff` uses Miedema's $\Delta H_{mix}$ to ensure non-linearity and distinctness from radius mismatch.
- **Collinearity**: `clr` transform, residual modeling, and VIF checks address the "sum-to-one" and dominant mass effects.

## Success Criteria Contingency
- **SC-001 (MAE)**: Measurable only if dataset ≥ 100 rows. If < 100 rows, project halts with `E_DATA_INSUFFICIENT`, and SC-001 is marked "Not Measurable".
- **SC-003 (Hypothesis)**: Measurable only if dataset ≥ 100 rows. If < 100 rows, project halts, and SC-003 is marked "Not Measurable".
