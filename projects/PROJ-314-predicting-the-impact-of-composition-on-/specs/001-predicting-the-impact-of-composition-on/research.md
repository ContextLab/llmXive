# Research: Predicting the Impact of Composition on the Weibull Modulus of Ceramics

## Executive Summary

This research phase investigates the feasibility of predicting the Weibull modulus of ceramics using compositional descriptors. The primary challenge identified is the **absence of a verified, publicly available dataset** containing the specific combination of Weibull modulus values, stoichiometry, and processing parameters required by the specification. The current "Verified datasets" block provided for this project context contains no relevant materials science data.

Consequently, the plan relies on a **Curated Literature Dataset** fallback strategy: the ingestion script will attempt to parse a pre-defined CSV of literature-extracted data if automated fetches from Materials Project or NIST fail (as these typically lack the target variable). The implementation includes a robust "Data Gap" detection mechanism: if the ingestion step fails to retrieve $\ge 30$ valid entries, the pipeline will halt and generate a "Data Availability Report" rather than a model.

## Dataset Strategy

### Verified Datasets Analysis
The provided verified dataset list contains **zero** entries relevant to ceramic Weibull modulus:
- **MAE (zip)**: Audio/Music data (irrelevant).
- **TOTAL (csv)**: Unrelated to materials.
- **OOM (parquet)**: Out-of-memory error logs (irrelevant).
- **GBM (json)**: Glioblastoma medical data (irrelevant).

**Critical Finding**: No verified source exists in the current context for the required data.

### Proposed Data Sources & Fallback
*Note: Materials Project (MP) and NIST are unlikely to contain Weibull modulus (a mechanical reliability metric derived from experimental fracture tests). The strategy is as follows:*

1.  **Materials Project (MP)**:
    -   *Target*: Crystal structures and elemental properties.
    -   *Limitation*: MP provides DFT-calculated formation energy and bandgap, rarely Weibull modulus.
    -   *Strategy*: Use MP for stoichiometry and elemental descriptors **only** if a separate Weibull dataset is found.

2.  **NIST / Ceramics Data Repository**:
    -   *Target*: Experimental mechanical properties.
    -   *Limitation*: Rarely contains structured, machine-readable tables of Weibull modulus linked to stoichiometry.
    -   *Strategy*: Scrape for "Weibull modulus" + "ceramic" + "stoichiometry".

3.  **Curated Literature Dataset (Fallback)**:
    -   *Target*: A pre-compiled CSV of data extracted from key papers (e.g., "Effect of composition on reliability").
    -   *Strategy*: If automated sources fail, load this CSV. The source DOI/URL will be validated against the primary source (Constitution Principle II) before ingestion.

### Data Acquisition Plan
1.  **Ingestion Script**: Will attempt to fetch data from assumed sources.
2.  **Validation Check**: Immediately after ingestion, the script will count rows where `weibull_modulus` is present AND `sample_count` $\ge 30$.
3.  **Data Gap Protocol**: If $N < 30$, the script exits with a specific error code and generates a "Data Availability Report" instead of a model.

## Feature Engineering Strategy

### Elemental Descriptors
Per FR-002, the following descriptors will be computed from stoichiometry (using `chemparse`):
1.  **Mean Atomic Radius**: $\bar{r} = \frac{1}{n} \sum r_i$
2.  **Electronegativity Spread**: $\sigma_{\chi} = \sqrt{\frac{1}{n} \sum (\chi_i - \bar{\chi})^2}$
3.  **Valence Electron Concentration (VEC)**: $VEC = \frac{\sum v_i}{n}$
4.  **Cation Size Variance**: Variance of ionic radii for cation species.
5.  **Processing Parameters**: Sintering temperature (imputed if missing, see below).

### Handling Missing Data (FR-003, US-1)
-   **Sample Count ($N$)**: If missing, exclude entry (FR-003).
-   **Processing Params**: Impute with median of the `primary_anion_cation_group`. If group size < 5, use global median.
    -   *Bias Mitigation*: Add a boolean feature `is_imputed` to allow the model to learn if the value was imputed.
    -   *High-Bias Flag*: If >40% of a class is imputed, that class is flagged as 'high-bias' and excluded from training (used only for descriptive stats).
-   **Range Values**: Extract midpoint, set `is_range_flag=True`.
    -   *Uncertainty Handling*: Add `range_uncertainty` (width of range) as a feature to account for measurement variance.

### Collinearity & Interpretation
-   **Correlated Features**: Descriptors like Mean Atomic Radius and Cation Size Variance are definitionally coupled.
-   **Strategy**: Calculate VIF. If VIF > 5, group features into a "Cluster" and report the aggregate importance of the cluster rather than ranking individual features as unique drivers. SHAP values for correlated features are unstable; the plan will interpret them as "cluster contributions".

## Modeling Strategy

### Algorithm Selection
-   **Random Forest Regressor**: Robust to non-linearities and outliers; provides native feature importance.
-   **Gradient Boosting Regressor**: High predictive power; handles interactions well.
-   **Baseline**: Global mean predictor (for SC-001 comparison).

### Validation Protocol
-   **Split**:
    -   If $N \ge 50$: Stratified 5-fold CV.
    -   If $30 \le N < 50$: Stratified 80/20 Hold-out.
    -   **Rare Class Handling**: If any class has < 5 samples, exclude that class from stratification (treat as 'rare' or drop from training).
-   **Cross-Validation**: 5-fold if $N \ge 50$; Hold-out if $30 \le N < 50$.
-   **Hyperparameter Tuning**: Grid search limited to a predefined set of combinations.
-   **Descriptor Sufficiency Check** (Corrected Logic):
    -   Re-run best model without `primary_anion_cation_group`.
    -   **Interpretation**: If performance drops significantly, the *descriptors* are insufficient to capture the material class physics. If performance does *not* drop, the descriptors are sufficient. (This is **not** a leakage check; it is a sufficiency check).

### Statistical Rigor & Constraints
-   **Power Analysis**: Acknowledged that N=30 is the absolute statistical minimum for Weibull parameter estimation but is critically underpowered for regression.
    -   **Protocol**: If N < 100, results are labeled "Exploratory".
    -   **Confidence Intervals**: Use bootstrapping to report confidence intervals for R^2 and MAE.
-   **Multiple Comparisons**: Since only two models are compared, family-wise error correction (e.g., Bonferroni) is applied to the significance of the difference in $R^2$ if a formal test is run.
-   **Causal Framing**: All outputs will include the disclaimer: "These results represent statistical associations only and do not imply causal relationships" (FR-008).
-   **Collinearity**: VIF calculated for all pairs. If VIF > 5, features are reported as "correlated" and not claimed as independent causal drivers (FR-007, SC-003).

### Success Criteria Validation
-   **SC-001 (MAE Improvement)**:
    -   Calculate MAE improvement over baseline.
    -   **Permutation Test**: Run a sufficient number of permutations of the target variable to generate a null distribution of MAE.
    -   **Pass**: Observed MAE < 90% of Baseline MAE **AND** p-value < 0.05.
    -   **Fail**: If p-value >= 0.05, report "Not Statistically Significant" regardless of numerical improvement.

## Computational Feasibility

-   **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
-   **Memory**: Data subset to < 1GB. Descriptors are lightweight.
-   **Runtime**:
    -   Ingestion: < 30 mins.
    -   Feature Engineering: < 10 mins.
    -   Modeling (multiple combinations, k-fold): ~2-3 hours (CPU optimized).
    -   SHAP Analysis: < 1 hour.
    -   **Total**: Well within 6-hour limit.
-   **Libraries**: `scikit-learn` (CPU only), `pandas`, `numpy`, `scipy` (for permutation tests). No GPU/CUDA.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No valid dataset found** | Project cannot proceed (N < 30). | Implementation halts with "Data Availability Report". |
| **High Collinearity** | Feature importance rankings unstable. | Group features into clusters; report aggregate importance. |
| **Range Data Dominance** | High variance in target. | Include `range_uncertainty` as a feature; perform sensitivity analysis. |
| **Overfitting** | Poor generalization. | Strict hyperparameter limits; stratified CV; bootstrapping for CI. |
| **Power Limitation** | N < 100 makes effect sizes unreliable. | Report results as "Exploratory"; use bootstrapping for wide CIs. |
| **Imputation Bias** | Model learns imputation pattern. | Add `is_imputed` flag; exclude classes with >40% imputation. |
| **Descriptor Sufficiency** | Descriptors fail to capture physics. | Run "Descriptor Sufficiency Check"; if failed, report "Descriptors Insufficient". |