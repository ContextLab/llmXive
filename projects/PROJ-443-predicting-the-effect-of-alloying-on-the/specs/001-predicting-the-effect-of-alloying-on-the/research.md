# Research: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## Dataset Strategy

The study relies on two primary external sources for High-Entropy Alloy (HEA) data: the Materials Project and the Open Quantum Materials Database (OQMD). Per the `# Verified datasets` block provided in the project inputs, the following sources are utilized.

| Dataset | Type | Source URL | Usage |
|:--- |:--- |:--- |:--- |
| **OQMD Targets** | CSV | ` | Primary source for Formation Energy and crystal structures. Elastic constants are sparsely available; a 'Data Availability Check' is performed to verify presence. |
| **Materials Project API** | API | ` Name or service not known)"))] (via `materials-project` library) | Primary source for Elastic Constants (Bulk, Shear, Young's Moduli) and composition data for HEAs (≥5 elements). |

**Dataset Fit Analysis**:
- **Variables Needed**: Elemental composition (atomic %), Elastic Constants (Bulk, Shear, Young's Moduli), Formation Energy.
- **OQMD Coverage**: The OQMD `targets.csv` contains formation energy and crystal structures. Elastic constants are not guaranteed for all HEAs.
- **Materials Project Coverage**: The Materials Project API provides elastic constants for many materials, but access requires an API key and may have rate limits.
- **Gap Handling**: If the verified OQMD dataset lacks sufficient HEA samples (≥500) and the Materials Project API does not yield enough data, the system will NOT attempt to fetch unverified data. Instead, it will proceed with a **'Reduced Power Analysis'**, explicitly logging the sample count and adjusting confidence interval calculations. This is the only valid fallback path.

## Feature Engineering Strategy

1. **Composition Parsing**: Extract atomic percentages from chemical formulas. Normalize to sum to 1.0.
2. **ILR Transformation**: Apply Isometric Log-Ratio transformation to the composition vector to map the data from the simplex to Euclidean space, breaking the closure constraint. This is a programmatic calculation using the `compositional` library.
3. **Descriptor Calculation**:
 - **Standard**: Mixing Entropy, Atomic Radius Variance (standard deviation), Electronegativity Variance (standard).
 - **Miedema**: Mixing Enthalpy (Miedema), Atomic Radius Variance (Miedema parameters), Electronegativity Variance (Miedema parameters).
4. **VIF Check (Orthogonality)**: Calculate the Variance Inflation Factor (VIF) for all 'Standard Descriptors' against the 'Miedema Prediction' (as a proxy for the Miedema baseline). Any descriptor with VIF > 5 is **excluded** from the predictor set to ensure orthogonality and prevent the model from implicitly learning the Miedema baseline.
5. **Target Construction**:
 - **Residual Modulus**: $M_{res} = M_{observed} - M_{Miedema\_prediction}$.
 - **Direct Modulus**: $M_{observed}$.
6. **Exclusion Rule**: If Target == Residual Modulus, **exclude** the set `$MIEDEMA_FEATURES$` from the predictor matrix to prevent circularity.

## Model Training Strategy

- **Algorithms**: Random Forest (RF), Gradient Boosting (GB), ElasticNet (EN).
- **Infrastructure**: CPU-only, `scikit-learn`.
- **Hyperparameter Tuning**: Grid search with 5-fold CV (stratified by element groups).
- **Data Split**: [deferred] Train, [deferred] Validation, [deferred] Test. Split stratified by unique element sets to prevent leakage.

## Statistical Evaluation Plan

1. **Primary Metrics**: R², RMSE, MAE on the Test set.
2. **Confidence Intervals**: 95% CI for R² via **Grouped Bootstrap** (1000 iterations). Groups defined by unique constituent element sets (e.g., "CrMnFeCoNi").
 - *Fallback*: If < 10 groups exist, use standard bootstrap with a warning flag.
3. **Null Hypothesis Test**: Permutation test (1000 iterations) to test $H_0: R^2 = 0$.
 - **Threshold**: If p-value > 0.05, the claim of predictive power is rejected.
4. **Multiple Comparison Correction**: Benjamini-Hochberg (FDR) applied to p-values from pairwise model comparisons (RF vs GB, RF vs EN, GB vs EN).
5. **Circularity Check (Stronger Test)**:
 - **Baseline Reconstruction Check**: Calculate the Pearson correlation between the **Model's Predicted Residual Values** and the **Miedema Prediction Values**. If $|r| > 0.5$, the model is flagged as potentially re-learning the baseline.
 - **Input Orthogonality**: The VIF check (Step 4) ensures the input features are orthogonal to the Miedema baseline.
6. **Sensitivity Analysis**: Sweep null hypothesis thresholds across a range of values.
 - **Method**: Calculate the 95% Confidence Interval (CI) of the R² score via bootstrapping for each model.
 - **Decision Rule**: If the **lower bound** of the 95% CI is greater than the threshold (e.g., 0.3), the claim is supported at that threshold. If the lower bound is below the threshold, the claim is rejected. This replaces the incorrect 'shifted permutation test' method.
 - **Robustness**: Report the variance in the lower bound of the CI across the tested thresholds.

## Decision Rationale & Constraints

- **CPU-Only Constraint**: All models are selected for their ability to train on 2 CPU cores within 6 hours. No deep learning models are used.
- **ILR Necessity**: Standard regression on compositional data leads to singular matrices due to the sum-to-one constraint. ILR is the mathematically rigorous solution.
- **Residual Strategy**: The research question focuses on the *effect of alloying* beyond the rule of mixtures. Using Miedema features to predict a residual of Miedema would be a logical fallacy (circular validation).
- **Associational Framing**: The dataset is observational. The plan explicitly frames all results as correlations, avoiding causal language.
- **Data Scarcity**: If N < 500, the study proceeds with a 'Reduced Power Analysis' as the only valid path, acknowledging the limitation.

## Risk Assessment

- **Data Scarcity**: Risk of < 500 HEA samples in OQMD/MP. *Mitigation*: Proceed with "Reduced Power Analysis" and report widened CIs.
- **API Instability**: Risk of failed downloads. *Mitigation*: Retry logic (limited attempts) and fallback to verified local dumps if available.
- **Overfitting**: Risk due to high dimensionality. *Mitigation*: ElasticNet regularization, strict train/test separation by element groups, and CI monitoring.
- **Circularity**: Risk of model learning the Miedema baseline. *Mitigation*: VIF check for input orthogonality and Baseline Reconstruction Check for output validation.