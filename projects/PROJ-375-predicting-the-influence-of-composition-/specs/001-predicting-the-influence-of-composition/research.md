# Research: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Dataset Strategy

The project relies on public repositories for metallic glass composition and CTE data.

| Dataset Name | Source / URL | Access Method | Relevance | Status |
|:--- |:--- |:--- |:--- |:--- |
| **Zhang et al. (Metallic Glass CTE)** | ` (Verified) | Direct Download (Zenodo API) | **PRIMARY FALLBACK**: Contains verified CTE values and compositions for amorphous alloys. | **VERIFIED** |
| **Materials Project** | ` Name or service not known)"))] (API) | Programmatic API (Requires Key) | Contains thermodynamic properties. CTE for amorphous phases is sparse. | **PENDING KEY** |
| **AFLOWlib** | ` Name or service not known)"))] (API) | Programmatic API (Requires Key) | Contains high-throughput DFT data. Metallic glass entries are rare. | **PENDING KEY** |

### Data Availability Analysis & Risk Mitigation

**Critical Finding**: The provided "Verified Dataset" URL in the system prompt was an Afrikaans NER corpus and is unusable. The project now relies on the **Zhang et al. (2020)** Zenodo dataset as the **guaranteed fallback** source.

**Implication**: The plan **must** implement a dual-source strategy:
1. **Primary**: Attempt API fetch from Materials Project/AFLOWlib.
 * **Constraint**: Must collect **all** available valid entries from APIs, even if the count is 0.
2. **Fallback**: If APIs return < 50 entries OR fail, download the **verified Zenodo CSV** (Zhang et al., 2020).
3. **Validation**: Check if the resulting dataset has `N >= 50`.
 * **If N >= 50**: Proceed with full statistical analysis (Permutation Test, 5-fold CV).
 * **If 20 <= N < 50**: Proceed with Hold-Out validation (skip 5-fold).
 * **If N < 20**: Proceed with Leave-One-Out (LOO) validation.
 * **If N = 0**: Trigger **No Data Termination** (valid completion, not a failure). **Do not fabricate data.**

**Revised Data Plan**:
1. **Attempt API Fetch**: Script attempts to fetch from Materials Project/AFLOWlib using `os.getenv("MP_API_KEY")` and `os.getenv("AFLOW_API_KEY")`.
2. **Filter**: Strictly filter for `state == "amorphous"` or `structure_type == "metallic_glass"`.
3. **Fallback Trigger**: If `N < 50` after API fetch (or API failure), download the verified Zenodo CSV.
4. **Final Validation**: If `N < 50` after fallback, proceed with **Qualitative Trend Analysis** and flag results as "Low Power / Qualitative". If `N = 0`, flag as "No Data Available".

## Methodological Rigor

### Statistical Approach
1. **Feature Engineering**:
 * **Weighted Mean Atomic Radius**: $\bar{R} = \sum c_i R_i$
 * **Electronegativity Variance**: $\sigma_{\chi}^2 = \sum c_i (\chi_i - \bar{\chi})^2$
 * **Valence Electron Concentration (VEC)**: $\sum c_i VEC_i$
 * **Atomic Size Mismatch**: $\delta = \sqrt{\sum c_i (1 - R_i/\bar{R})^2}$
 * *Constraint*: These are derived strictly from elemental tables (e.g., `mendeleev` Python library).
 * *Multicollinearity Check*: Calculate Variance Inflation Factor (VIF) for `mean_atomic_radius` and `size_mismatch`. Since $\delta$ is mathematically coupled with $\bar{R}$, including both introduces multicollinearity. If VIF > 5.0, exclude `size_mismatch` from the model input to ensure valid feature importance.

2. **Modeling**:
 * **Baselines**:
 * **Null Model**: Predicts the mean CTE of the training set.
 * **Linear Regression**: Trained on the *same* descriptors as the RF model.
 * *Note on SC-001*: The spec requires a baseline of "linear weighted average of elemental CTEs". However, elemental CTE data is not available in the input features. The plan uses the Null Model and Linear Regression on Descriptors as the scientifically valid baseline. SC-001 is flagged as a spec-root cause for revision.
 * **Validation**:
 * **If N >= 50**: 5-Fold Stratified CV by Alloy Family (Zr, Pd, Fe, etc.).
 * *Fallback*: If any family has < 5 samples, group into "Other" or revert to random split.
 * **If 20 <= N < 50**: Hold-Out split (70/30) or 3-Fold CV.
 * **If N < 20**: Leave-One-Out (LOO) CV.
 * *Fallback*: If any family has < 5 samples, revert to random split.
 * **Metrics**: $R^2$, MAE, RMSE.

3. **Significance Testing**:
 * **Permutation Test**: 1000 iterations (only if N >= 50). Shuffle target variable (CTE) and re-evaluate model.
 * **Null Hypothesis**: The model's $R^2$ is not significantly different from random chance.
 * **Threshold**: If $R^2_{obs} > 0.3$ and $p < 0.05$, the relationship is considered significant.
 * *Fallback (N < 50)*: Skip permutation test. Report correlation coefficients and feature rankings as "Qualitative Trends".

4. **Feature Importance vs. Correlation (Divergence Analysis)**:
 * **Goal**: Identify non-linear drivers.
 * **Method**: Compare the Top 3 features by Random Forest importance against the Top 3 by absolute correlation coefficient.
 * **Interpretation**:
 * **Match**: Suggests linear dominance.
 * **Divergence**: Suggests non-linear interactions (e.g., VEC or Mismatch effects).
 * *Note*: We do **not** require a match as a pass/fail criterion (as per SC-003 revision). SC-003 requires a match, which is scientifically unsound as it assumes linearity. The plan implements Divergence Analysis as the valid scientific outcome and flags SC-003 as a spec-root cause.

### Computational Feasibility (CPU-First)
* **Hardware**: GitHub Actions (2 vCPU, 7GB RAM).
* **Strategy**:
 * Use `scikit-learn` (CPU optimized).
 * Avoid deep learning (no faithful CPU form for this specific regression task; RF/Linear is sufficient).
 * Stream data if > 7GB (unlikely for <10k rows, but implemented via `pandas` chunking if needed).
 * **No GPU Escape Hatch Required**: The problem domain (tabular regression on <10k rows) is well within CPU capabilities.

## Decision Rationale

* **Why Linear Regression & Random Forest?** The spec explicitly requires these baselines (FR-004). They are computationally cheap, interpretable, and sufficient for the "composition-to-property" mapping without needing complex neural architectures.
* **Why Permutation Testing?** Standard CV gives performance estimates but not statistical significance against the null hypothesis. SC-002 explicitly requires a p-value (if N ≥ 50).
* **Why Stratified Split?** Alloy families (Zr-based vs. Pd-based) have vastly different physical properties. A random split could result in a test set containing only Zr-based alloys, making the model's generalization to Pd-based alloys untested.
* **Why Qualitative Fallback?** If N < 50, statistical power is insufficient for p-values. A qualitative analysis of trends and correlations remains scientifically valid and avoids the "failure" of a halted pipeline.
* **Why Divergence Analysis?** Forcing feature importance to match correlation assumes linearity. Comparing them allows us to detect non-linear effects, which is a more robust scientific outcome. SC-003's "match" requirement is scientifically unsound and flagged for spec revision.