# Research: Predicting the Impact of Impurities on the Superconductivity of Magnesium Diboride

## Dataset Strategy

The analysis relies on two primary sources for MgB₂ experimental data. The plan strictly adheres to the "Verified datasets" block provided in the user message.

| Dataset Name | Source Type | Verified URL | Usage in Plan |
|--------------|-------------|--------------|---------------|
| MgB2 (SuperCon subset) | HuggingFace (TSV) | ` | Primary source for Tc and impurity data. |
| MgB2 Audio Transcriptions | HuggingFace (Parquet) | ` | **Excluded**: Contains audio/transcriptions, not material properties. |
| MgB2 Audio Preprocessed | HuggingFace (Parquet) | ` | **Excluded**: Contains audio/transcriptions, not material properties. |
| Materials Project API | API (CSV/JSON) | **NO verified source found** | **Fallback Strategy**: The spec mentions the Materials Project API. Since no verified URL is provided in the "Verified datasets" block, the plan will attempt to access the public API via `pymatgen` (which uses the standard MP endpoint). **API Key Handling**: The `MATERIALS_PROJECT_API_KEY` must be provided as a GitHub Secret in the CI environment. If the key is missing, the script will skip MP data, log a warning, and proceed with SuperCon data only. If the combined N < 100, the script will fail with exit code 1. |

**Critical Gap Analysis & Validation**:
- **Schema Verification**: Before training, the ingestion script will validate that the HuggingFace dataset (`taqwa92/cm.mgb2`) contains the required `impurity` structure (element symbol -> concentration).
- **Unstructured Text Fallback**: If structured columns (e.g., `impurities`, `doping`) are missing, the system will attempt to parse text fields `doping_info`, `description`, or `notes` using the regex pattern: `r'([A-Z][a-z]?)\s*:?\\s*([0-9.]+)%?'`. This extracts element symbols and percentages. If parsing yields < 50% of rows with valid impurity data, the script will fail with a specific error: "Dataset lacks required impurity concentration fields and text parsing failed."
- **Sample Size Requirement**: The plan defines a minimum sample size of **N ≥ 100** (combined from SuperCon and MP) to ensure statistical power for regression. If the merged dataset has N < 100, the pipeline will halt with a specific error regarding power limitations.
- **Variable Fit**: The `taqwa92/cm.mgb2` dataset will be inspected to confirm it contains `Tc` and `impurity` columns. If it lacks specific impurity columns (e.g., only has "impurity type" without concentration), the plan will fail with a specific error message (per Edge Cases).

## Statistical Methodology

### Model Selection
Three models will be trained:
1. **Ridge Regression**: Baseline linear model with L2 regularization. Chosen over standard Linear Regression to handle multicollinearity among impurities without discarding features, preserving interpretability of coefficients.
2. **Random Forest**: Captures non-linear interactions, robust to outliers.
3. **XGBoost**: Gradient boosting for potential higher accuracy, limited grid search.

### Significance Testing (FR-004 Correction)
> **Methodological Correction**: The source spec (FR-004) mandates a "Target Permutation Test" (shuffling Y) for tree-based models. This tests global model significance, not specific feature effects. This plan implements **Feature Permutation Importance** (shuffling X) to correctly answer the research question. The spec requires revision to align with this correction.

- **Linear/Ridge Regression**: **Partial F-test**.
 - Null Hypothesis ($H_0$): Impurity coefficients are jointly zero.
 - Method: Compare the full model (with impurities) against a reduced model (without impurities) using an F-test on training residuals. This isolates the contribution of impurities.
- **Tree-Based (RF/XGBoost)**: **Feature Permutation Importance**.
 - Procedure: Shuffle the specific impurity feature column $X_{imp}$ (while keeping $Y$ fixed) $N=100$ times (capped for 30-min runtime). Measure the drop in model performance (R²).
 - Null Hypothesis ($H_0$): Permuting the impurity feature has no effect on model performance.
 - P-value Calculation: The fraction of permuted scores that are equal to or better than the original model score.
 - *Note*: This directly tests the specific effect of the impurity, unlike Target Permutation (shuffling Y) which only tests global model significance.
 - **Global vs. Feature**: A global test (shuffling Y) will be performed first to confirm the model has predictive power. Only if the global test is significant ($p < 0.05$) will feature-specific tests be reported. The "rule-of-thumb" values are derived only from features passing the Feature Permutation Test ($p < 0.05$).

### Multiple Comparison Correction
- If multiple impurity effects are tested individually, the Benjamini-Hochberg procedure will be applied to control the False Discovery Rate (FDR).

### Collinearity Handling
- **Ridge Regression**: The primary linear model uses L2 regularization to shrink coefficients of correlated predictors, preventing instability without removing features.
- **VIF Check**: Variance Inflation Factor (VIF) will still be calculated. If VIF $\ge 5.0$ for a specific impurity in the Ridge model, the feature is retained but reported with a "High Collinearity" flag. **No features are removed to avoid bias.**
- **Principal Component Regression (PCR)**: If Ridge Regression fails to converge or explain sufficient variance, PCR will be used as a fallback to transform correlated impurities into orthogonal components.

## Computational Feasibility

- **Hardware**: GitHub Actions Free Tier (limited vCPU, limited RAM).
- **Memory Strategy**:
 - Data loading: Use `pandas` with `dtype` optimization.
 - Model training: Use `n_jobs=1` or `2` (no parallelism overhead on small cores).
 - Grid Search: A limited set of combinations will be explored.
 - XGBoost: Use `tree_method='hist'` (CPU optimized) and limit `max_depth` to 4 (reduced from 6 for speed).
- **Runtime**:
 - Ingestion & Validation: < 5 min.
 - Training (3 models): < 15 min.
 - Significance Testing (Feature Permutation, N=100): < 5 min.
 - Visualization: < 5 min.
 - **Total Budget**: **30 minutes** (strictly aligned with Constitution Principle VII).

## Decision Rationale

- **Why Ridge Regression first?** Provides direct $\Delta T_c$ estimates (K/at%) which are scientifically interpretable and handles multicollinearity (common in co-doping) without discarding features, unlike simple removal.
- **Why Feature Permutation for Trees?** Trees do not provide p-values for coefficients. Feature Permutation (shuffling X) is the standard non-parametric method to assess the significance of *specific* features.
- **Why cap grid search and resamples?** The 30-minute limit on free-tier runners is strict. A full grid search or high resample count would exceed this. A limited search (e.g., `n_estimators`: [50, 100], `max_depth`: [3, 4]) and 100 resamples balance performance and feasibility.
- **Why exclude N < 5 from effect estimation?** Estimating a $\Delta T_c$ coefficient for a group with < 5 samples is statistically unstable. These elements will be grouped for stratification only, but no specific effect size will be reported for them.