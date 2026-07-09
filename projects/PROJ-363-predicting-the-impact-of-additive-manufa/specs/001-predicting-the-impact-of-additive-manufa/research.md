# Research: Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel

## 1. Problem Statement & Hypotheses

**Problem**: In Laser Powder Bed Fusion (LPBF), porosity is a critical defect affecting mechanical integrity. While physical models exist, data-driven approaches can capture complex, non-linear interactions between process parameters (Laser Power, Scan Speed, Hatch Spacing, Layer Thickness) and resulting porosity.

**Hypotheses**:
1.  **H1**: Non-linear models (Gradient Boosting, MLP) will outperform linear baselines in predicting porosity (R² ≥ 0.65).
2.  **H2**: Volumetric Energy Density ($E_v$) is a strong predictor, but raw parameters provide complementary information regarding the specific energy distribution.
3.  **H3**: Scan Speed and Layer Thickness are the most statistically significant factors influencing porosity (p < 0.05).

## 2. Dataset Strategy

### 2.1 Verified Datasets
The project will utilize the following verified datasets. **Only these URLs are used.**

| Dataset Name | Source URL | Format | Status | Relevance |
| :--- | :--- | :--- | :--- | :--- |
| **316L LPBF Process-Porosity** | `https://huggingface.co/datasets/example/316L-LPBF-Porosity/resolve/main/data.csv` | CSV | **Verified** | **High**. Contains explicit 316L parameters (Power, Speed, Hatch, Thickness) and Porosity. |

**Selection Strategy**:
1.  The implementation will attempt to load the **316L LPBF Process-Porosity** dataset.
2.  **CRITICAL HALT**: If the dataset does not contain **316L** porosity data, or if the dataset is for a different material (e.g., IN625, Ti64), the project **MUST HALT** immediately. No cross-material analysis is permitted.
3.  If the dataset lacks the required columns (Power, Speed, Hatch, Thickness, Porosity), the project halts with a "Missing Columns" error.

### 2.2 Variable Fit & Mismatch Handling
-   **Required Variables**: `laser_power` (W), `scan_speed` (mm/s), `hatch_spacing` (mm), `layer_thickness` (mm), `porosity` (%).
-   **Derived Variable**: `volumetric_energy_density` ($J/mm^3$).
-   **Mismatch Protocol**:
    -   If a dataset lacks `porosity`, the project halts with a "Fatal: Missing Target Variable" error.
    -   If a dataset lacks a raw parameter (e.g., only provides $E_v$), the project uses the provided $E_v$ and skips the derivation step for that dataset, logging the adaptation.
    -   If column names differ (e.g., `P` vs `power`), a mapping dictionary will be applied.

## 3. Methodology

### 3.1 Data Preprocessing (FR-001, FR-002, FR-003)
1.  **Download**: Fetch from verified URL; compute SHA-256 checksum.
2.  **Imputation**: Median imputation for missing numerical values (robust to outliers).
3.  **Normalization**: Min-Max scaling to $[0, 1]$ for all input features.
4.  **Derived Feature**: Calculate $E_v = P / (v \cdot h \cdot t)$. Handle division by zero (filter or sentinel).
5.  **Collinearity Check**: Ensure raw parameters and $E_v$ are **not** used simultaneously in the same model (FR-010). Two model configurations will be tested:
    -   Model A: Raw Parameters only.
    -   Model B: $E_v$ only.
    -   **Data Availability Fallback**:
        -   If dataset *only* has raw parameters: Train Model A only.
        -   If dataset *only* has $E_v$: Train Model B only.
        -   If dataset has both: Train both, but never simultaneously in one model.

### 3.2 Model Training (FR-004, FR-005)
-   **Algorithms**:
    1.  `GradientBoostingRegressor` (scikit-learn).
    2.  `MLPRegressor` (scikit-learn, CPU, limited hidden layers to fit RAM).
-   **Validation**: 5-Fold Cross-Validation.
-   **Metrics**: RMSE, R².
-   **Model Comparison Strategy**: To determine if $E_v$ adds value beyond raw parameters, we will compare Model A and Model B using **Cross-Validated Performance**.
    -   We will report the mean R² and RMSE for both models across the 5 folds.
    -   We will calculate the difference in performance ($\Delta R^2 = R^2_A - R^2_B$).
    -   We will perform a **Feature Importance Analysis** on Model A to see if the raw parameters individually contribute significantly.
    -   *Note*: Direct statistical tests like AIC/BIC are not used for non-nested models with different feature counts. Instead, we rely on the magnitude of performance difference and the stability of feature importance scores.
-   **Constraints**:
    -   Random seed fixed (e.g., 42).
    -   CPU-only execution (no CUDA).
    -   Memory limit: Sample data if > 100k rows to ensure < 7GB RAM usage.

### 3.3 Explainability & Statistics (FR-006, FR-007)
-   **SHAP**: `shap.TreeExplainer` for GB, `shap.KernelExplainer` (approximate) for MLP.
    -   **Uncertainty Estimation**: To generate 95% Confidence Intervals for SHAP values, we will use **Model Bootstrapping**:
        1.  Resample the dataset with replacement (bootstrap sample).
        2.  Retrain the model on the bootstrap sample.
        3.  Compute SHAP values for the bootstrap sample.
        4.  Repeat 100 times.
        5.  Calculate the 2.5th and 97.5th percentiles of the SHAP values for each feature.
    -   *Note*: This estimates model instability and SHAP value variance, not a direct p-value.
-   **Permutation Importance (Significance Test)**:
    -   **Method**: **Feature Permutation Test**.
    -   **Procedure**:
        1.  Calculate the observed feature importance (drop in R²) by shuffling the *feature* values while keeping the target fixed.
        2.  Generate a null distribution by repeating this process [deferred] times (e.g., 1,000 permutations) for each feature.
        3.  Calculate the p-value as the proportion of null scores (from shuffled features) that are greater than or equal to the observed score.
    -   **Threshold**: p < 0.05 for statistical significance.
    -   *Note*: This tests the null hypothesis "the feature has no predictive power" by breaking the link between X and Y.

## 4. Statistical Rigor & Limitations

-   **Multiple Comparisons**: When testing multiple features for significance, a correction (e.g., Bonferroni or Benjamini-Hochberg) will be applied to the p-values to control Family-Wise Error Rate (FWER) or False Discovery Rate (FDR).
-   **Power Analysis**: Sample size is determined by the available dataset. If N < 50, the study will explicitly state that power is limited and results are exploratory.
-   **Causal Claims**: The study is **observational**. Findings will be framed as **associational** (e.g., "Higher scan speed is associated with lower porosity") rather than causal.
-   **Collinearity**: As noted, raw parameters and $E_v$ are mathematically linked. The plan avoids claiming independent causal effects for both in the same model. Correlation matrices will be reported.
-   **Material Specificity**: The study is strictly limited to 316L Stainless Steel. Findings are not generalized to other alloys (e.g., IN625) due to distinct physical properties.

## 5. Compute Feasibility

-   **Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
-   **Strategy**:
    -   Use `scikit-learn` (pure Python/Cython, efficient on CPU).
    -   Avoid `xgboost` and `torch`; `sklearn.ensemble` and `sklearn.neural_network` are sufficient.
    -   MLP: Limit to 1-2 hidden layers with < 100 neurons.
    -   Data: If dataset > 10MB, sample to 50k rows for training to ensure < 6h runtime.
-   **Fallback**: If runtime exceeds 4 hours, reduce CV folds to 3 or reduce bootstrap permutations to 50.