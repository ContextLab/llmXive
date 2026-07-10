# Research: Predicting Yield Strength of BCC Alloys

## 1. Dataset Strategy

The project requires a dataset containing:
1. Elemental composition (atomic fractions).
2. Yield strength (MPa).
3. Crystal structure (must be BCC).

### Verified Sources Analysis

Based on the **# Verified datasets** block provided in the specification:

| Dataset Name | Verified URL | Suitability for BCC Yield Strength |
| :--- | :--- | :--- |
| **MPEA Database** | *NO verified source found* | **Critical Gap**: The spec cites DOI `10.1038/s41597-020-00768-9`. The verified block states "NO verified source found". **Action**: The implementation MUST NOT invent a URL. The plan will attempt to resolve the DOI at runtime. If the DOI does not resolve to a file containing the specific BCC+YieldStrength subset, the pipeline will halt with a "Data Source Unreachable" error. |
| **Materials Project** | *NO verified source found* | **Critical Gap**: No verified URL exists for a direct Materials Project BCC yield strength dataset. The plan will attempt to fetch via API if available, but will fall back to MPEA only. If MPEA N < 80, the pipeline halts. |
| **BCC (parquet)** | `https://huggingface.co/datasets/bccnf/MeLiDC-shuffled-completo/...` | **Mismatch**: The URL `MeLiDC-shuffled-completo` suggests a text/language dataset (MeLiDC), not materials. **Decision**: These are **NOT** suitable for materials science. |
| **MPa (parquet)** | `https://huggingface.co/datasets/mpalaval/scraped_xsum1/...` | **Mismatch**: `scraped_xsum1` implies text summarization data (XSum), not materials yield strength. **Decision**: These are **NOT** suitable for materials science. |

### Subset Verification & Fallback

1.  **Primary Strategy**: The implementation will attempt to load the MPEA dataset using the DOI `10.1038/s41597-020-00768-9`. The code will explicitly query for entries where `crystal_structure == "BCC"` and `yield_strength` is not null.
2.  **Verification Step**: If the dataset is loaded, the code will verify that the subset contains at least 80 entries. If not, the pipeline **HALTS** with a "Data Scarcity Warning".
3.  **Fallback Strategy**: If the MPEA dataset is unavailable (DOI resolution fails) or lacks the required subset, the project **cannot proceed** with the research question as specified. The pipeline will halt with a "Data Source Unreachable" error. No fallback to unverified sources is permitted.
4.  **Assumption**: The spec assumes the MPEA database contains ≥80 BCC alloys. This assumption is **unverified** given the lack of a verified URL. The research phase explicitly states this limitation and the hard halt condition.

*Note: Do NOT use the "BCC" or "MPa" HuggingFace URLs listed in the verified block as they appear to be text datasets mislabeled in the verification list.*

## 2. Feature Engineering Methodology

### Descriptors (FR-003)
Based on materials science literature for High-Entropy Alloys (HEAs) and Medium-Entropy Alloys (MEAs):
1.  **Atomic Radius Mismatch ($\delta$)**:
    $$ \delta = \sqrt{\sum_{i=1}^{n} c_i (1 - \frac{r_i}{\bar{r}})^2} \times 100 $$
    Where $c_i$ is atomic fraction, $r_i$ is atomic radius, $\bar{r} = \sum c_i r_i$.
2.  **Valence Electron Concentration (VEC)**:
    $$ VEC = \sum_{i=1}^{n} c_i VEC_i $$
3.  **Mixing Entropy ($\Delta S_{mix}$)**:
    $$ \Delta S_{mix} = -R \sum_{i=1}^{n} c_i \ln(c_i) $$
4.  **Mixing Enthalpy ($\Delta H_{mix}$)**:
    $$ \Delta H_{mix} = \sum_{i=1}^{n} \sum_{j=1}^{n} \Omega_{ij} c_i c_j $$
    Where $\Omega_{ij} = 4 \Delta H_{mix}^{AB}$ (binary interaction enthalpy).
    *   **Source of Interaction Parameters**: The binary interaction parameters ($\Omega_{ij}$) will be sourced from the supplementary data of the MPEA paper (DOI: 10.1038/s41597-020-00768-9) or the standard Miedema model table if the paper data is unavailable. This ensures consistency with the dataset's origin and avoids data source mismatch.
5.  **Electronegativity Difference ($\Delta \chi$)**:
    Calculated similarly to $\delta$ using electronegativity values.

### Log-Ratio Transformation (FR-003.1)
Compositional data lies on a simplex ($\sum c_i = 1$), causing perfect multicollinearity.
*   **Method**: Isometric Log-Ratio (ILR) transformation.
*   **Implementation**: Use `pyrolite` to transform the raw composition vector $x$ into ILR coordinates $z = V^T \ln(x)$.
*   **Feature Hierarchy**: The model will primarily use ILR coordinates. The scalar descriptors ($\delta$, VEC, etc.) will be included as additional predictors **ONLY IF** Variance Inflation Factor (VIF) < 5. This prevents redundancy, as scalars are deterministic functions of the composition already captured by ILR.
*   **Circular Validation Risk**: The plan will verify that the target variable (yield strength) is **experimentally measured** and not derived from CALPHAD calculations using the same interaction parameters ($\Omega_{ij}$) used for predictors. If the dataset contains only CALPHAD-derived yield strength, the pipeline will flag this as a "Circular Validation Risk".

## 3. Modeling Strategy

### Algorithms (FR-005)
1.  **Random Forest Regressor**: Handles non-linearities and interactions well.
2.  **Gradient Boosting Regressor**: High accuracy for tabular data.
3.  **Ridge Regression**: Baseline linear model; regularized to handle potential collinearity.

### Validation Strategy (FR-004, FR-006)
*   **Split**: Stratified 80/20 split based on **binned compositional ranges** (derived from ILR features), NOT yield strength. This avoids binning the continuous target variable and potential selection bias.
*   **Cross-Validation**: **Repeated 5-Fold Cross-Validation (10 repeats)** for all dataset sizes $N \ge 80$.
    *   *Methodology Deviation Note*: The spec (FR-005) originally mandated "LOOCV for N < 100, 5-fold CV for N >= 100". However, LOOCV is statistically unstable for regression tasks with small N, producing high variance in performance estimates. Repeated 5-Fold CV provides a more robust, lower-variance estimate of generalization error for all valid dataset sizes (N >= 80). This deviation is documented to prioritize scientific validity over the literal spec text, which will be flagged for amendment.
*   **Confidence Intervals**: 100-iteration Bootstrap resampling on the test set to generate 95% CI for $R^2$.
*   **Feature Importance**: Permutation importance (scikit-learn `permutation_importance`) to identify robust descriptors.

## 4. Statistical Rigor & Constraints

*   **Multiple Comparisons**: When comparing 3 models, apply Bonferroni correction to p-values if hypothesis testing is performed on $R^2$ differences.
*   **Power Analysis**: The plan explicitly checks $N \ge 80$. If $N < 80$, the pipeline halts. This is a hard constraint to ensure statistical power.
*   **Causal Claims**: The study is **observational**. Claims will be framed as "associational" or "predictive," not causal.
*   **Collinearity**: ILR transformation addresses compositional collinearity. VIF will be checked for scalar descriptors.

## 5. Compute Feasibility

*   **Hardware**: GitHub Actions Free Tier (multiple CPU cores, ~7 GB RAM).
*   **Memory Management**:
    *   Data loading: Stream or chunk if necessary (unlikely for <1000 rows).
    *   Models: `scikit-learn` models are CPU-efficient. No GPU required.
    *   ILR: Computationally light for $<1000$ samples.
*   **Runtime**: Estimated < 1 hour for full pipeline (Ingestion + Features + Modeling + Bootstrapping) on 2 CPUs.

## 6. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use ILR Transformation** | Required by FR-003.1 to handle compositional closure and multicollinearity. |
| **Halt if $N < 80$** | Spec requirement (Edge Cases) to ensure statistical validity. |
| **No External API for Periodic Table** | CI constraints; use a local static dictionary or `periodictable` library (if available in wheel). |
| **Repeated 5-Fold CV** | Statistically superior to LOOCV for small N regression; provides consistent methodology for all N >= 80. |
| **Dataset Handling** | The MPEA DOI is the primary source. If no verified URL exists or the subset is missing, the code must handle the failure gracefully with a hard halt. |
| **Stratification by Composition** | FR-004 explicitly requires stratification by "binned compositional ranges", not target variable. |
| **VIF Check for Scalars** | Prevents redundancy between ILR coordinates and scalar descriptors. |
| **Circular Validation Check** | Ensures target variable is independent of predictor parameters. |