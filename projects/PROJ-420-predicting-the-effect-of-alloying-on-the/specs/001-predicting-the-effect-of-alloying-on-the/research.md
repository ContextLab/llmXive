# Research: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Dataset Strategy

The project relies on public materials databases. The following sources have been verified for reachability and format compatibility.

| Dataset Name | Source URL | Format | Usage |
| :--- | :--- | :--- | :--- |
| **Materials Project** | *No verified public URL in source block* | JSON/API | **Critical Gap**: The spec requests Materials Project data, but no verified URL exists in the provided block. The implementation will attempt to fetch from the public MP API (unauthenticated). If unreachable or requires auth, the pipeline halts. |
| **NIST Materials Data** | *No verified public URL in source block* | JSONL/CSV | **Critical Gap**: The spec requests NIST data, but no verified URL exists in the provided block. The implementation will attempt to fetch from standard NIST endpoints. If unreachable, the pipeline halts. |
| **ILR Methodology Reference** | N/A (Statistical Literature) | Text | Reference for ILR implementation logic: Aitchison, J. (1986). *The Statistical Analysis of Compositional Data*. Chapman & Hall. |
| **ILR Implementation Code** | `https://pypi.org/project/compositional/` | Python Package | Verified source for ILR transformation logic. |

> **Note on Data Availability**: The provided "Verified datasets" block does not contain direct URLs to the Materials Project or NIST Materials Data Repository for aluminum alloys. The implementation plan assumes the existence of a fallback mechanism: if the primary APIs (Materials Project, NIST) are unreachable or require authentication, the system will halt with a clear error message (per Edge Case logic) rather than fabricating data or using proxy datasets. **No proxy datasets are used.** The research phase will document the actual data retrieval success rate.

## Methodological Approach

### 1. Data Extraction & Filtering (Data Availability Gate)
- **Source**: Attempt to query Materials Project and NIST repositories for Al-alloys.
- **Verification (FR-009)**:
  - **Check 1**: Verify `shear_modulus_gpa` is present. If missing in >20% of entries, proceed but flag.
  - **Check 2**: Verify `measurement_method` contains "Ultrasonic", "Shear", or "Resonant".
  - **Logic**: Poisson's ratio (ν) is mathematically defined by the relationship between Young's modulus (E) and shear modulus (G). Without G, ν is often derived from E. The presence of G allows verification of independence. If G is missing, independence cannot be verified, and the data is **excluded** from the training set (not the whole project).
  - **Filtering Action**: Entries lacking `shear_modulus_gpa` or independent `measurement_method` tags are marked as non-independent and removed from the analysis dataset.
  - **Halt Condition**: If the count of *remaining* independent entries is < 50, the pipeline halts with "Insufficient Data: <50 independent measurements found".
- **Filtering**:
  - Keep only monolithic alloys (exclude composites).
  - Require non-missing: Poisson's ratio, Young's modulus, Cu, Mg, Si, Zn, Mn.
  - **Unit Normalization**: Convert all elastic constants to GPa. Convert weight percentages to atomic fractions.
  - **Completeness Check**: Exclude entries where sum of major elements < 0.95 (to avoid bias from missing trace elements).

### 2. Power & Sensitivity Analysis (Task T015)
- **Goal**: Determine if the expected sample size (N=50) is sufficient to detect meaningful effects.
- **Method**: Calculate Minimum Detectable Effect Size (MDES) for a Random Forest with 5 features and N=50.
- **Halt Condition**: If MDES > 0.1 MAE improvement, the pipeline halts with a warning that the study is underpowered to detect small compositional effects.

### 3. Feature Engineering (Compositional Data)
- **Problem**: Elemental fractions sum to 1.0, creating perfect multicollinearity.
- **Solution**: Apply **Isometric Log-Ratio (ILR)** transformation.
  - Input: Atomic fractions of [Cu, Mg, Si, Zn, Mn].
  - Process: Transform to an orthonormal basis in real space.
  - Output: A set of numeric features suitable for regression.
- **Diagnostic**: Compute Variance Inflation Factors (VIF) on the *raw* fractions to document collinearity (FR-007). These scores are persisted in the final output.
- **Balance Element**: Aluminum (Al) is used as the implicit denominator/balance. This choice is tested for sensitivity (Task T017).

### 4. Model Training & Validation
- **Algorithm**: Random Forest Regressor.
- **Validation**: 5-fold Cross-Validation.
- **Test**: 80/20 Train/Test split.
- **Metric**: Mean Absolute Error (MAE).
- **Constraint**: Must run on CPU (multi-core, standard RAM). No GPU.
- **Hyperparameter Limits**: `max_depth=10`, `min_samples_leaf=5` to prevent overfitting on small N.

### 5. Interpretation & Significance
- **Feature Importance**: Use **Compositional Perturbation** (Task T016).
 - Method: Perturb target element (e.g., Cu) by +[deferred], proportionally reduce Al to maintain unit sum, measure prediction change.
  - Ranking: Rank elements by the magnitude of prediction change.
- **Sensitivity Check**: Re-run importance with an alternative ILR basis (e.g., balance Cu/Mg vs. rest) to ensure robustness (Task T017).
- **Null Model**: Run Random Forest on 100 shuffled target permutations (Task T018).
  - Significance: Only importance scores exceeding the upper tail of the null distribution are reported as significant.
- **Framing**: All results framed as **associational** (observational data, no randomization).

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Not applicable; single outcome (Poisson's ratio).
- **Power Analysis**: Assuming ≥50 entries (per spec assumption). If <50, the pipeline will halt or flag insufficient power. MDES will be calculated to quantify the limitation.
- **Collinearity**: Addressed via ILR for modeling; VIF reported for diagnostics and persisted in output.
- **Causality**: Explicitly denied. Claims limited to "X is associated with higher Poisson's ratio in this dataset."
- **Overfitting Risk**: Mitigated by hyperparameter limits, null model validation, and small dataset size awareness.

## Decision Rationale

- **ILR vs. Standard Regression**: Standard regression on compositional data violates the simplex constraint. ILR is the standard statistical remedy for this specific data type.
- **Random Forest**: Chosen for robustness to non-linearity and ability to handle feature interactions without extensive hyperparameter tuning, fitting the CPU constraint.
- **No GPU**: The dataset size (<1000 rows) and model complexity (Random Forest) are well within CPU capabilities; GPU adds unnecessary complexity and violates the "free-tier runner" constraint.
- **Perturbation Importance**: Chosen over simple back-transformation to avoid closure artifacts in the ranking of elements.
- **Null Model**: Chosen to establish statistical significance of feature importance in small N datasets where standard p-values are unreliable.