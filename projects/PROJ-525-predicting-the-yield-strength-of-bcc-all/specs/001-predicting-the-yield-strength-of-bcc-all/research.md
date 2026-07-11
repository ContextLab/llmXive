# Research: Predicting Yield Strength of BCC Alloys

## Dataset Strategy

### Source Verification & Acquisition

**Primary Dataset**: MPEA Database (DOI: 10.1038/s41597-020-00768-9).
- **Status**: NO verified source found in the provided list.
- **Action Plan**: The implementation will attempt to fetch via the DOI or a known repository (e.g., figshare, zenodo) linked from the paper. If a direct programmatic URL cannot be verified by the Reference-Validator Agent, the pipeline will require manual data placement.
- **Manual Data Acquisition Protocol**:
  1.  User downloads the dataset from the DOI-linked repository.
  2.  User calculates the SHA-256 checksum of the downloaded file.
  3.  User places the file in `data/raw/mpea_raw.csv` and creates a `checksums.txt` file with the calculated hash.
  4.  The `Reference-Validator Agent` verifies the checksum against the known hash from the DOI. If the checksum matches, the data is considered "Verified" and the pipeline proceeds. If the checksum does not match or the file is missing, the pipeline halts with `NO_VERIFIED_DATA`.
- **Fallback Strategy**: **NONE**. There are no alternative verified numerical datasets with yield strength values in the current context. If the MPEA database is inaccessible or cannot be verified, the pipeline halts with a `NO_VERIFIED_DATA` error. No speculative "verified lists" or generic BCC parquet files are assumed to exist.

### Data Schema & Requirements

The dataset MUST contain:
1.  `elemental_composition`: Dict or string of atomic fractions (e.g., `{"Fe": 0.5, "Cr": 0.5}`).
2.  `yield_strength`: Numeric value in MPa.
3.  `crystal_structure`: String (must be "BCC").
4.  `system_id`: Unique identifier.

### Potential Mismatches & Risks

- **Risk**: The MPEA database might not contain enough BCC alloys (N < 80).
- **Mitigation**: FR-004 mandates an immediate halt with exit code 1 and the message "DATA_SCARCITY: Insufficient BCC alloys (N < 80)" if the count is insufficient.

## Feature Engineering Strategy

### Descriptors (FR-003)

1.  **Atomic Radius Mismatch (δ)**:
    $$ \delta = \sqrt{\sum_i c_i (1 - \frac{r_i}{\bar{r}})^2} \times 100 $$
    Where $c_i$ is atomic fraction, $r_i$ is atomic radius, $\bar{r}$ is average radius.
2.  **Valence Electron Concentration (VEC)**:
    $$ VEC = \sum_i c_i VEC_i $$
3.  **Mixing Entropy ($\Delta S_{mix}$)**:
    $$ \Delta S_{mix} = -R \sum_i c_i \ln c_i $$
4.  **Mixing Enthalpy ($\Delta H_{mix}$)**:
    $$ \Delta H_{mix} = \sum_{i \neq j} \Omega_{ij} c_i c_j $$
    *Source of $\Omega_{ij}$*: NIST-JANAF or CALPHAD assessment (distinct from yield strength source).
5.  **Electronegativity Difference**: Weighted variance of electronegativity.

### Pre-Analysis Independence Check (Addressing Data Leakage)

To mitigate the risk of circular validation where thermodynamic parameters (used for $\Delta H_{mix}$) might be correlated with the target yield strength (as both relate to phase stability):
1.  **Action**: Before model training, calculate the Pearson correlation coefficient ($r$) between the derived `mixing_enthalpy` and `yield_strength`.
2.  **Source Audit**: If $|r| > 0.7$, the `mixing_enthalpy` feature is flagged as "High Correlation". The plan mandates a **Source Audit**: the specific thermodynamic database used for parameters must be checked for overlap with the yield strength source.
3.  **Decision**: If overlap is found, the feature is excluded from the model, and a note is added to the final report stating that the predictor independence could not be verified. If no overlap is found, the feature is retained with a warning. This ensures that the model does not make claims based on potentially circular data.

### Compositional Transformation (FR-003.1)

- **Method**: Isometric Log-Ratio (ILR) transformation.
- **Rationale**: Elemental compositions are compositional data (sum to 1). Standard regression assumes independence, which is violated here. ILR maps the simplex to Euclidean space, removing the closure effect and multicollinearity.
- **Implementation**: `skbio.stats.composition` or manual implementation using balances.

### Feature Orthogonalization (Addressing Multicollinearity)

- **Method**: **Residualization**.
- **Procedure**:
  1.  Compute the ILR-transformed features ($X_{ilr}$).
  2.  For each scalar descriptor ($y_{scalar}$, e.g., VEC, $\delta$), regress $y_{scalar}$ against $X_{ilr}$: $y_{scalar} = X_{ilr} \beta + \epsilon$.
  3.  Use the **residuals ($\epsilon$)** as the final scalar features.
- **Rationale**: This removes the component of the scalar descriptors that is linearly explained by the compositional geometry (ILR), ensuring that the model learns the *unique* contribution of the physical mechanism (e.g., VEC) beyond just the elemental proportions.

### Pre-Filter Dimensionality Reduction (Addressing Overfitting for Small N)

- **Method**: Principal Component Analysis (PCA).
- **Procedure**: Before model training, apply PCA to the combined feature set (ILR + orthogonalized scalars). Retain only components that explain a substantial majority of the variance.
- **Rationale**: For N < 80, the high dimensionality of the feature space (ILR coordinates + scalars) poses a significant risk of overfitting. PCA reduces the effective dimensionality while preserving the majority of the variance, ensuring the model is robust.

### Feature Selection (FR-003.2)

- **Method**: Recursive Feature Elimination (RFE) with a Random Forest estimator or L1 (Lasso) regularization.
- **Goal**: Identify the minimal subset of ILR coordinates and orthogonalized scalar descriptors that maximize predictive power while reducing overfitting.
- **Constraint**: Feature selection must occur **strictly within the inner loop** of the Nested Cross-Validation to prevent data leakage.

## Modeling Strategy

### Algorithms (FR-005)

1.  **Random Forest Regressor**: Handles non-linear relationships; robust to outliers.
2.  **Gradient Boosting Regressor (e.g., XGBoost/CatBoost CPU mode)**: High accuracy, handles feature interactions.
3.  **Ridge Regression**: Baseline linear model with L2 regularization to handle multicollinearity in scalar descriptors.

### Validation & Metrics (FR-006, SC-001, SC-002, SC-003)

- **Evaluation Protocol**: **Stratified 80/20 Split + Nested Cross-Validation**.
 - **Outer Layer**: A stratified train-test split (based on 4 quantile bins of yield strength) is performed on the full dataset. The [deferred] holdout set is reserved for final performance estimation only.
 - **Inner Layer**: Nested Cross-Validation is performed **strictly on the [deferred] training set**.
    - **Inner Loop**: 5-Fold Cross-Validation. Used for hyperparameter tuning and feature selection.
    - **Outer Loop (for CI)**: **Repeated Stratified K-Fold** (5 repeats of 5-fold) is performed on the training set to generate a distribution of 25 scores.
  - **Rationale**: This satisfies the spec's requirement for a split (FR-004) while maintaining statistical rigor for small N. The Repeated K-Fold provides a sufficient distribution of scores for valid Confidence Interval calculation.
- **Metrics**: R², MAE, RMSE.
- **Confidence Intervals**: 95% CI for R² calculated from the distribution of 25 scores (5 repeats of 5-fold) using the percentile method. This avoids the instability of bootstrapping only 5 points.
- **Feature Importance**: Permutation importance (mean decrease in R²) to verify model reliance on physical descriptors, not artifacts.

### Statistical Rigor & Assumptions

- **Power Analysis**: Given the constraint of N < 80 (if met), power is limited. The plan explicitly acknowledges this limitation. The success criterion MAE ≤ 50 MPa is conditional on the model being statistically distinguishable from a null model.
- **Multiple Comparisons**: When comparing 3 models, a correction (e.g., Bonferroni) will be applied if hypothesis testing on model differences is performed.
- **Causal Inference**: This is an observational study. Claims will be framed as "associational" or "predictive," not causal. No randomization exists in the dataset.
- **Collinearity**: Addressed via Residualization of scalar descriptors against ILR coordinates and PCA for dimensionality reduction.
- **Measurement Validity**: Yield strength values are assumed to be measured under comparable conditions (room temp, standard strain). No normalization for testing conditions is applied (per Assumptions).

### Limitations

- **External Validity**: The model is validated only on the MPEA dataset population. No external "ground truth" or out-of-distribution test set (e.g., a specific alloy family not in the MPEA DB) is available. Claims are strictly limited to the MPEA population. The model's ability to generalize to unseen alloy systems is unverified.
- **Data Scarcity**: For N < 80, the confidence intervals will be wide. The model's ability to generalize to unseen alloy systems is uncertain.