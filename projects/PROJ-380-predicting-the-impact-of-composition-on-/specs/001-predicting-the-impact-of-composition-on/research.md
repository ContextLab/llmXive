# Research: Predicting the Impact of Composition on the Shear Modulus of Bulk Metallic Glasses

## Executive Summary

This research validates the feasibility of predicting the shear modulus of Bulk Metallic Glasses (BMGs) using compositional descriptors. The core hypothesis is that atomic size mismatch ($\delta$) and mixing enthalpy ($\Delta H_{mix}$) are the primary drivers of shear modulus variability. The implementation will rely on CPU-tractable methods (Linear Regression, Random Forest, Gradient Boosting, Ridge) and non-parametric statistical tests to ensure validity on small datasets.

## Dataset Strategy

### Verified Sources & Availability

**Critical Finding**: The "Verified datasets" block provided for this project indicates **NO verified direct download URL** for a complete "Inoue BMG Compilation" containing shear modulus. The Materials Project API typically provides crystal structure data, and BMGs (amorphous) are often excluded or require specific, non-standard queries.

**Strategy**:
1. **Primary**: Attempt to fetch data via the **Materials Project API**.
 * *Requirement*: The user must provide an API key via `MP_API_KEY` environment variable.
 * *Validation*: If the API returns data, verify the `shear_modulus` field exists and the phase is "amorphous" or "BMG".
2. **Secondary (Verified Inoue Subset)**: If the API fails, attempt to load a curated subset of the Inoue compilation from a **verified GitHub repository** (URL: ` - *Note: This is a placeholder for the verified URL if one exists in the verified block; if not, proceed to Synthetic*).
3. **Tertiary (Synthetic Fallback)**: If neither real data source is available or complete, the pipeline **automatically generates a Synthetic BMG Dataset**.
 * *Basis*: Generated from verified literature parameters (Inoue et al., 2000s; Miedema model parameters) cited in `research.md`.
 * *Reproducibility*: The generator code is deterministic (pinned seeds). This ensures the pipeline runs end-to-end on a fresh runner without manual file injection, satisfying Constitution Principle I and II.
 * *Reporting*: The final paper will clearly distinguish between "Real Data Results" and "Synthetic Validation Results".

**Data Volume Estimate**:
* BMG literature is sparse. Expect $N \approx -800$ entries for real data.
* Synthetic data will be generated to match this distribution for robustness testing.
* This volume is well within the available RAM limit for CPU training.

### Feature Engineering Strategy

The plan computes four descriptors based on elemental properties (Atomic Radius, Electronegativity, Valence, Enthalpy of Mixing).
* **Source**: `mendeleev` Python library (CPU-friendly, no external API needed for elemental data).
* **Formulas**:
 * $\delta = \sqrt{\sum c_i (1 - r_i / \bar{r})^2}$
 * $\Delta H_{mix} = 4 \sum \sum c_i c_j \Delta H_{ij}$
 * $VEC = \sum c_i v_i$
 * $\Delta \chi = \sqrt{\sum c_i (\chi_i - \bar{\chi})^2}$
* **Validity**: These are standard descriptors in materials informatics (Inoue et al., 2000s).

## Statistical Rigor & Methodology

### Hypothesis Testing
* **Hypothesis**: Atomic size mismatch ($\delta$) and mixing enthalpy ($\Delta H_{mix}$) explain a substantial portion of the variance.
* **Method**: Linear Regression baseline + Non-linear models (RF, GB) + **Ridge Regression** (to handle collinearity).
* **Collinearity Control**:
 * Calculate **Variance Inflation Factors (VIF)** for all descriptors.
 * If VIF > 5, the feature is either removed or combined via PCA before training.
 * Ridge Regression (L2 regularization) is used as a baseline to ensure stable coefficients.
* **Model Comparison**:
 * **Primary**: **Wilcoxon Signed-Rank Test** on paired cross-validation fold errors (non-parametric, robust to small N and non-normality).
 * **Secondary (Fallback)**: **Bayes Factors** to quantify evidence for Model A > Model B if the Wilcoxon test is underpowered (small N).

### Power & Sample Size
* **Limitation**: With $N < 1000$, power for detecting small effect sizes is limited.
* **Mitigation**: Use a **Hybrid Validation Strategy**:
 * **LOFO (Leave-One-Family-Out)**: Performed **only** for alloy families with $N \ge 10$.
 * **Stratified Group K-Fold (5-fold)**: Performed for the entire dataset, ensuring every family (including small ones) appears in both train and test sets. This reduces variance in the generalization estimate for sparse families.
* **Success Criteria**: $R^2 \ge 0.60$ must be achieved on the **Stratified Group K-Fold** metric. If any family has $N \ge 10$, the LOFO metric for that family must also be reported. If *no* families have $N \ge 10$, the Stratified Group K-Fold metric is the sole success criterion.

### Collinearity & Measurement Validity
* **Collinearity**: $\delta$ and $\Delta H_{mix}$ are often correlated.
 * *Action*: Generate a correlation heatmap. If $|r| > 0.8$, the plan will **remove or combine** features (via VIF/PCA) before training, rather than just reporting them as a cluster.
 * *Validity*: Descriptors are derived from well-established elemental tables (Mendeleev DB). The synthetic fallback uses verified literature parameters.

## Compute Feasibility (GitHub Actions Free Tier)

* **Memory**: Dataset < 1 MB. Model training (RF/GB) on < 1000 rows takes < 1 GB RAM.
* **CPU**: 2 Cores.
 * Grid Search: Limited to a manageable number of combinations. 3 models $\times$ 50 $\times$ 5 folds = 750 fits.
 * Estimated Time: < 30 minutes total.
* **GPU**: None required. All libraries (`scikit-learn`, `numpy`) run natively on CPU.
* **Constraint Adherence**:
 * No `torch`/`tensorflow` heavy lifting.
 * No 8-bit quantization.
 * Data subset: Full dataset fits in memory.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No BMG Data Available** | High (Project Stalls) | **Synthetic Fallback**: Pipeline automatically generates a verified synthetic dataset. Research continues with "Synthetic Validation" results. |
| **API Rate Limiting** | Medium | Implement exponential backoff in `ingest.py`. |
| **Family Imbalance** | Medium | Hybrid validation (LOFO for large, GroupKFold for small) ensures no empty folds. |
| **Overfitting** | Medium | Strict 5-fold CV + VIF pruning + Ridge baseline. Permutation importance to check for spurious correlations. |
| **Underpowered Statistics** | Medium | Use Wilcoxon (non-parametric) and Bayes Factors (quantitative evidence) instead of standard t-tests. |
