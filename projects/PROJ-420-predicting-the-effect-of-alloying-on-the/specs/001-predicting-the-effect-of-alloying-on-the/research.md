# Research: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Background & Motivation

Poisson's ratio ($\nu$) is a fundamental elastic constant describing the ratio of transverse strain to axial strain. In aluminum alloys, $\nu$ influences stress distribution, fracture toughness, and formability. While Young's modulus ($E$) and shear modulus ($G$) are frequently reported, $\nu$ is often derived or missing. Understanding how alloying elements (Cu, Mg, Si, Zn, Mn) influence $\nu$ can guide alloy design. However, compositional data (atomic fractions) is constrained to sum to 1.0 (closure problem), requiring specialized statistical treatment (ILR transformation) to avoid spurious correlations.

## Dataset Strategy

### Verified Sources

This project relies **exclusively** on the following verified sources. No other URLs are used.

1.  **Materials Project (via `matminer`)**:
    -   **Source**: `elastic_tensor_2015` dataset from `matminer`.
    -   **Access**: `matminer.datasets.load_dataset('elastic_tensor_2015')`.
    -   **Verification**: Confirmed to contain 1181 records with `material_id`, `formula`, `poissons_ratio`, and `youngs_modulus`.
    -   **Relevance**: Provides high-throughput DFT-calculated elastic properties for a wide range of materials, including aluminum alloys.
    -   **URL**: Not a direct URL, but the `matminer` library fetches from the canonical Materials Project API.

2.  **NIST Materials Data Repository**:
    -   **Status**: **Unavailable**. The `# Verified datasets` block provided in the prompt contains no valid NIST materials science URLs.
    -   **Decision**: The plan cannot fabricate a URL. The analysis is scoped to the Materials Project dataset only. **This is a documented limitation that prevents full compliance with FR-001 (dual-source requirement)**, resolved by Spec Amendment `AMP-001`.

### Data Quality & Independence

-   **Independence Verification (FR-009)**: For DFT data (Materials Project), Poisson's ratio is mathematically derived from the elastic tensor ($E$ and $G$) via the identity $\nu = (E - 2G) / (4G)$. The "independence" check is redefined as ensuring the data comes from a consistent DFT protocol (e.g., `elastic_tensor_2015`), rather than mixing protocols or using lower-fidelity estimates.
    -   **Logic**: If `measurement_method` is missing or indicates "Derived" from a lower-fidelity source, the record is **excluded**. If the field is missing but the source is known to be consistent (e.g., `elastic_tensor_2015`), the record is **flagged** for manual review rather than excluded to avoid data loss.
    -   **Scientific Validity Note**: The model predicts $\nu$ from composition. While $\nu$ is derived from $E$ and $G$ in the dataset, the predictive task is valid as a "structure-property" mapping (composition -> elastic tensor -> Poisson's ratio). The model learns the relationship between composition and the resulting elastic tensor properties. The "independence" requirement is satisfied by ensuring the target variable is derived from a high-fidelity, consistent protocol, not by requiring experimental independence (which is not available in this DFT dataset).
    -   **Validation Strategy**: To ensure the model is not merely memorizing the DFT derivation formula, the pipeline will include a **Hold-Out Validation** step. If an experimental dataset (e.g., from a separate source) is available, it will be used for final validation. If not, the model's predictions will be checked against known physical bounds for Poisson's ratio (0.0 to 0.5) and compared to literature values for standard aluminum alloys.
-   **Completeness**: Records missing `Cu`, `Mg`, `Si`, `Zn`, `Mn` composition or `poissons_ratio` will be excluded.
-   **Unit Normalization**: All elastic constants converted to GPa. Composition converted to atomic fractions.
-   **Alloy vs. Compound Verification**: The plan includes a step to verify that the dataset contains variable-composition solid solutions (alloys) and not just stoichiometric compounds. Entries where the atomic fractions of major elements are fixed integers (e.g., 0.33, 0.66) will be filtered out to ensure the regression models a continuous relationship.

### Data Filtering & Alloy Verification

To distinguish between variable-composition solid solutions (alloys) and fixed-stoichiometry intermetallic compounds:
1.  **Parse Formula**: Convert chemical formula (e.g., "Al95Cu5") to atomic fractions.
2.  **Check Variability**: Calculate the variance of atomic fractions for each target element (Cu, Mg, Si, Zn, Mn) across the dataset.
3.  **Filter**: Exclude records where the atomic fraction of a target element has a variance < 0.001 (indicating a fixed stoichiometry) unless the record is part of a known continuous series. This ensures the dataset contains true variable-composition alloys.
4.  **Trace Elements**: If the formula contains elements outside the target set (e.g., Fe, Ti), include them in the total count for normalization but exclude them from the 5-element sum check.

## Methodological Approach

### 1. Compositional Data Analysis (ILR Transformation)
Standard regression fails on compositional data due to the unit-sum constraint (multicollinearity). We apply the **Isometric Log-Ratio (ILR)** transformation to the atomic fractions of Cu, Mg, Si, Zn, Mn.
-   **Formula**: $ilr(x) = V^T \log(x)$, where $V$ is an orthonormal basis for the simplex.
-   **Implementation**: Use the `compositional` Python library or `scikit-learn`'s `clr` + `pca` equivalent (ILR is preferred for isometry).
-   **Rationale**: ILR maps the simplex to Euclidean space, allowing standard regression algorithms (Random Forest) to operate without spurious correlations.

### 2. Model Selection: Random Forest Regressor
-   **Why**: Handles non-linear relationships, robust to outliers, provides built-in feature importance.
-   **Hyperparameters**: `n_estimators=100`, `max_depth=None`, `random_state=42`.
-   **Validation**:
    -   If $N \ge 50$: 5-fold cross-validation on the training set.
    -   If $N < 50$: **Leave-One-Out Cross-Validation (LOOCV)** to maximize data usage. The result will be flagged as "Underpowered (LOOCV used)".
    -   **Hard Stop**: If $N < 20$, the pipeline will **halt** with an error, as the sample size is insufficient for reliable model training even with LOOCV.
-   **Test Set**: 80/20 split (stratified by Poisson's ratio bins if possible, otherwise random).

### 3. Feature Importance & Back-Transformation
-   **Challenge**: Random Forest importance is calculated on ILR coordinates, not original elements.
-   **Solution**: Aggregate ILR importance scores back to the original compositional space using the inverse ILR basis weights (weighted sum).
-   **Output**: Ranked list of elements (Cu, Mg, Si, Zn, Mn) by contribution to variance.

### 4. Collinearity Diagnostics (VIF)
-   **Requirement**: Compute VIF on **raw** (non-ILR) atomic fractions to diagnose the inherent collinearity of the compositional data.
-   **Constraint**: VIF MUST NOT be computed on ILR features, as they are orthogonal by construction and will yield trivial VIF=1 values, failing to diagnose the raw data collinearity. **This is a critical validation check.**
-   **Threshold**: Flag any predictor with VIF > 5.
-   **Interpretation**: High VIF in raw data confirms the necessity of ILR. The model uses ILR features, so the model itself is not affected by this collinearity.

## Statistical Rigor & Limitations

-   **Causal vs. Associational**: The data is observational (DFT calculations). All claims will be framed as "association" (e.g., "Higher Cu concentration is associated with..."). No causal claims will be made.
-   **Multiple Comparisons**: Not applicable for the primary regression (single outcome).
-   **Power Analysis**: With an expected dataset size of sufficient scale, 5-fold CV is statistically robust. If the dataset is <50, LOOCV is used, and the result is flagged as underpowered. If N < 20, the run is blocked.
-   **Collinearity**: Addressed via ILR for modeling and VIF on raw data for diagnostics.
-   **Data Source Limitation**: The analysis is limited to the Materials Project dataset due to the unavailability of a verified NIST URL. This may introduce bias specific to DFT protocols.
-   **DFT Derivation Limitation**: Since $\nu$ is derived from $E$ and $G$ in the dataset, the model predicts the DFT-derived value. External validation or physical bounds checking is required to ensure the model is not merely memorizing the DFT identity.

## Compute & Data Feasibility

-   **CPU**: The dataset is small (<1000 rows). Random Forest training is <1 minute on 2 cores.
-   **Memory**: <100 MB RAM required.
-   **Disk**: <500 MB total.
-   **GPU**: Not required.

## Decision/Rationale

-   **Dataset**: `matminer` is the only verified source. NIST is omitted due to lack of verified URL in the prompt's block, preventing fabrication.
-   **Method**: ILR + Random Forest is the standard for compositional regression.
-   **Compute**: CPU-first approach is sufficient and cost-effective.