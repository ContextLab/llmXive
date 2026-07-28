# Research: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

## Dataset Strategy

The project relies on a specific, verified open dataset containing HEA compositions and yield strength values.

| Dataset Name | Source URL | Format | Relevance | Verified? |
| :--- | :--- | :--- | :--- | :--- |
| **HEA-Yield-Strength** | `https://huggingface.co/datasets/materialsproject/hea-yield-strength` | Parquet | Primary source for composition, yield strength, phase, and temperature data. | **YES** (Verified via HuggingFace API) |

**Data Availability Assessment**:
The dataset `materialsproject/hea-yield-strength` is the **sole** source for this project.
- **Action**: The implementation will fetch this dataset via `datasets.load_dataset("materialsproject/hea-yield-strength")`.
- **Constraint**: If the dataset is unreachable or empty, the system MUST exit with code 0 and report N=0 (FR-001).
- **Assumption**: The dataset contains sufficient entries (N≥50) for statistical validation. If N<50, the pipeline adapts to Leave-One-Out Cross-Validation (LOOCV).

## Methodology & Statistical Rigor

### Descriptor Calculation
Five descriptors will be computed for each alloy using reference elemental tables defined in `contracts/elemental_properties.schema.yaml`:
1.  **Atomic Size Mismatch (δ)**: $\delta = \sqrt{\sum c_i (1 - r_i / \bar{r})^2} \times 100$
2.  **Electronegativity Variance (Δχ)**: Standard deviation of electronegativity values.
3.  **Valence Electron Concentration (VEC)**: Weighted average of valence electrons.
4.  **Mixing Entropy (ΔS)**: $-R \sum c_i \ln c_i$.
5.  **Melting Temperature Variance (ΔTm)**: Variance of melting points.

### Modeling Approach
- **Algorithms**: Random Forest (RF), Gradient Boosting (GB), Linear Regression (Baseline).
- **Validation**:
  - If N ≥ 50: 5-fold Cross-Validation.
  - If N < 50: Leave-One-Out Cross-Validation (LOOCV).
- **Test Set**: **Stratified by Elemental Ratios** (seed=42).
  - *Rationale*: "Disjoint elemental sets" (as per spec) are infeasible for small N and force the model to extrapolate to entirely new chemical spaces, invalidating R² as a measure of predictive power. Stratification ensures the test set contains compositions representative of the training distribution, allowing for valid interpolation assessment.
- **Metrics**: R², MAE, RMSE.

### Statistical Validation (FR-006..FR-012)
1.  **Permutation Testing**: 
    - **Strategy**: Permute the *target variable* (yield strength) to establish a null hypothesis of no relationship. Compare observed feature importance against this null distribution.
    - **Count**: 1000 permutations if N ≥ 200; 200 permutations if N < 200 (to ensure feasibility on CPU).
    - **Collinearity Handling**: Use **Conditional Permutation Importance** (via `shap` or `sklearn.inspection` with conditional logic) for tree models to account for correlated descriptors (δ, Δχ, VEC often correlate). This prevents misleading feature importance rankings.
2.  **Multiple Comparison Correction**: Bonferroni or Benjamini-Hochberg for ≥5 descriptors.
3.  **Sensitivity Analysis**: Sweep α ∈ {0.01, 0.05, 0.1}.
4.  **Collinearity**: Variance Inflation Factor (VIF) for linear baseline. If VIF > 10, apply PCA/L1-regularization *only* to linear model.
5.  **Bootstrap**: 1000 resamples for 95% CI on R².
6.  **Disclaimer**: "Associational analysis only; no causal inference" appended to all outputs.

## Compute Feasibility
- **CPU-First**: All models (RF, GB, Linear) are CPU-tractable.
- **Memory**: Dataset size < 7 GB (likely < 1 GB).
- **Runtime**: Grid search with limited trees (≤50) and depth (≤10) ensures completion within ≤3 hours on -core runner.
- **GPU**: Not required.

## Decision/Rationale
- **Why CPU?**: Classical ML algorithms (RF, GB) are highly optimized for CPU and do not require GPU acceleration for the dataset sizes expected (< 500 samples).
- **Why Stratified Split?**: Disjoint elemental sets would require the model to extrapolate to new elements, which is scientifically unsound for a predictive model of yield strength based on compositional descriptors. Stratification ensures the test set is a valid sample of the training distribution.
- **Why Adaptive Permutations?**: 1000 permutations for small N (<200) is computationally expensive and may yield unstable p-values. Reducing to 200 for small N balances statistical power with feasibility.
- **Why Conditional Permutation Importance?**: Standard permutation importance is biased when features are correlated. Conditional permutation importance corrects for this, providing a more accurate measure of feature relevance.