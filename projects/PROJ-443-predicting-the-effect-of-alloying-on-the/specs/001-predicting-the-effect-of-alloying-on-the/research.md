# Research: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## Summary

This research phase validates the data sources, defines the feature engineering strategy (ILR for linear models, residuals for physics), and outlines the statistical methodology for model evaluation. It confirms that the proposed approach is feasible within the 6-hour CPU-only constraint and addresses the critical requirement of compositional data handling and statistical validity.

## Dataset Strategy

The study relies on public materials databases. Per the project constraints and the "Verified datasets" block, the following sources are utilized. **Note**: The spec mentions Materials Project, but the verified list contains OQMD sources. The pipeline will attempt MP first (if keys exist), then prioritize OQMD. If OQMD does not yield sufficient HEA samples (≥500 with elastic constants) or lacks elemental composition vectors, the pipeline halts (Edge Case 1).

| Dataset Name | Description | Source URL (Verified) | Usage |
|:--- |:--- |:--- |:--- |
| **OQMD Targets** | Elastic constants and composition data for materials, including potential HEAs. | ` | Primary source for Bulk Modulus and composition. **Requires verification of elemental vector columns.** |
| **OQMD Raw** | Raw OQMD dump (if needed for deeper filtering). | ` | Fallback for raw structure data if targets.csv lacks composition details. |

**Dataset Fit Verification**:
- **Required Variables**: Bulk Modulus (Outcome), Elemental Composition (Predictors: `element_symbols`, `atomic_fractions`), Crystal Structure (Covariate).
- **Verification**: The OQMD `targets.csv` is known to contain formation energy and elastic properties. We must verify in `data_ingestion.py` that it also contains the elemental breakdown for HEAs (≥5 elements). **If the verified source lacks explicit elemental percentages for HEAs, we will flag a Fatal Data Gap and halt**, as we cannot fabricate composition data.
- **Constraint Check**: The OQMD sources are standard CSV/Parquet files, easily loadable via `pandas` within 7GB RAM limits.

**Excluded Sources**:
- Mental Health datasets (Amod, lavita, etc.): Irrelevant to materials science.
- ElasticNet/MAE/RMSE datasets in verified list: These appear to be meta-datasets or results from other studies, not raw material property data. They are excluded from the training pipeline to avoid data leakage or contamination.

## Feature Engineering Strategy

### Compositional Descriptors
Per FR-002, the following descriptors will be computed for every sample:
1. **Mixing Enthalpy ($\Delta H_{mix}$)**: Calculated using Miedema's model (approximated via `pymatgen`). **Note**: This is used to compute a *baseline* prediction.
2. **Atomic Radius Variance ($\delta$)**: Variance of atomic radii weighted by atomic fraction.
3. **Entropy of Mixing ($\Delta S_{mix}$)**: Calculated from atomic fractions.
4. **Valence Electron Concentration (VEC)**: Weighted average of valence electrons.
5. **Electronegativity Variance**: Variance of Pauling electronegativity.

### Isometric Log-Ratio (ILR) Transformation
Per FR-003 and US-1, standard compositional data (summing to 1.0) suffers from the "closure problem," leading to singular covariance matrices.
- **Method**: Apply ILR transformation to the elemental composition vector $x$.
- **Implementation**: Use the `compositions` package or a custom implementation of the centered log-ratio (CLR) followed by an orthonormal basis transformation.
- **Scope**: **Applied ONLY to ElasticNet (linear models)**. Random Forest and Gradient Boosting are robust to multicollinearity and will use raw compositions or simple ratios to preserve interpretability.
- **Benefit**: Breaks the sum constraint for linear models, allowing the use of standard regression without singularity issues.

### Residual Prediction Strategy
To address "physics leakage" (where the model simply learns elemental properties), the target variable will be the **residual** from a physics-based baseline:
- **Baseline**: $BulkModulus_{Miedema}$ (calculated via Rule of Mixtures or Miedema's model).
- **Target**: $BulkModulus_{Residual} = BulkModulus_{Observed} - BulkModulus_{Miedema}$.
- **Rationale**: This forces the model to learn the *specific alloying effects* and deviations from the baseline, ensuring the analysis is scientifically meaningful and not just a re-parameterization of known physics.

## Statistical Methodology

### Model Selection
Three models will be trained (FR-004):
1. **Random Forest (RF)**: Non-linear, robust to outliers.
2. **Gradient Boosting (GB)**: High predictive power, handles complex interactions.
3. **ElasticNet**: Linear baseline, interpretable coefficients (post-ILR).

### Evaluation Metrics
- **Primary**: $R^2$ (Coefficient of Determination), RMSE, MAE.
- **Null Hypothesis**: $H_0: R^2 = 0$.
- **Confidence Intervals**: 95% CI for $R^2$ via **Grouped Bootstrap** (1000 iterations).
 - *Grouping*: Samples are grouped by "Alloy System" (unique set of constituent elements, e.g., 'Fe-Co-Ni-Cr-Mn').
 - *Fallback*: If unique groups < 30, switch to **Leave-One-System-Out (LOSO)** cross-validation to ensure stable variance estimation.
- **Significance**: Defined strictly as **95% CI excluding 0**. No parametric t-tests are used on R².
- **Permutation Test**: 100 permutations of the target variable to verify signal is not random.
- **Multiple Comparison Correction**: False Discovery Rate (FDR) applied to p-values when comparing model performances (FR-005).

### Sensitivity Analysis
Per FR-006, the $R^$ threshold for "success" will be swept across {0.25, 0.30, 0.35} to report the variance in false-positive rates (proportion of bootstrap CIs excluding 0 when the null is effectively true or near-zero).

### Power & Sample Size
- **Limitation**: With N~large and grouped bootstrapping, the study is likely underpowered to detect moderate effect sizes (R² ~ moderate) with narrow confidence intervals.
- **Mitigation**: The plan will explicitly calculate and report the **Minimum Detectable Effect Size (MDES)** given the sample size and alpha. Results will be framed as "detecting large effects" rather than definitive proof for moderate effects.

## Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation Strategy |
|:--- |:--- |:--- |:--- |
| **Insufficient HEA Samples** | High | Fatal | Pipeline checks sample count immediately after ingestion. If < 500, it halts with a specific error (Edge Case 1). |
| **Missing Elastic Constants** | Medium | High | Filter logic strictly enforces presence of Bulk Modulus. Samples without it are dropped and logged. |
| **Missing Elemental Data** | Medium | Fatal | Data Modality Check (Phase 0) halts pipeline if `element_symbols`/`atomic_fractions` are missing. |
| **Compositional Data Errors** | Medium | Medium | Normalization step (US-1) forces sum=1.0 and logs adjustments. |
| **Overfitting** | Medium | Medium | Grouped bootstrap/LOSO and FDR correction ensure robust performance estimates. |
| **CPU Time Exceeded** | Low | High | Use `n_jobs=1` or `2` (matching runner cores) for RF/GB. Limit tree depth. |
| **Underpowered Study** | Medium | Medium | Report MDES. Do not claim significance for small effect sizes. |

## Decision Rationale

- **Why OQMD?** It is the only verified source in the provided list with elastic property data. Materials Project requires API keys that may not be available; we will attempt to fetch if keys are provided, but OQMD is the primary fallback.
- **Why ILR (Linear Only)?** Standard regression fails on compositional data due to perfect multicollinearity. ILR is the standard statistical solution for linear models. Tree models do not require it.
- **Why Residual Target?** To avoid "physics leakage" where the model simply learns elemental properties. The goal is to predict the *deviation* from the baseline.
- **Why Grouped Bootstrap / LOSO?** Random splits in materials science often leak information because similar alloys (same base elements) appear in both train and test sets, artificially inflating $R^2$. Grouping by alloy system prevents this. If groups are too few, LOSO is the robust alternative.
- **Why CI-Based Significance?** R² is bounded and non-normally distributed. Parametric t-tests are invalid. Bootstrap CIs provide a robust, non-parametric test of significance.