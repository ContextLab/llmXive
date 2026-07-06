# Research: Predicting the Influence of Alloying on the Seebeck Coefficient Using Public Data

## Executive Summary

This research plan outlines the methodology for predicting the Seebeck coefficient of thermoelectric alloys using compositional descriptors derived from the electronic transport database (DOI: 10.1038/sdata.2017.85). The study focuses on three material families: Bismuth Telluride, Lead Telluride, and Skutterudites. The primary hypothesis is that simple compositional features (mean atomic radius, electronegativity variance, valence electron concentration, atomic number variance) exhibit a statistically significant correlation with the Seebeck coefficient, though the predictive power (R²) is expected to be low due to the inability of composition alone to capture complex band structure effects.

## Dataset Strategy

### Target Dataset
- **Source**: Electronic Transport Database (DOI: 10.1038/sdata.2017.85).
- **Status**: **NO verified source found** in the provided "Verified datasets" block.
- **Action**: The implementation will attempt to fetch the dataset using the DOI resolver or a known repository URL associated with the DOI (e.g., Nature Scientific Data repository). If a direct programmatic loader (like `datasets` from HuggingFace) does not exist for this specific DOI, the script will use `requests` to download the raw file from the publisher's landing page, parsing it based on the expected format (likely CSV or JSON).
- **Verification**: The script MUST verify the file integrity (checksum) and format before proceeding. If the DOI does not resolve to a downloadable file in the CI environment, the pipeline will halt with a clear error message, preventing "silent" failure.

### Material Family Mapping (Addressing Data Resource Concerns)
To handle inconsistent naming conventions (e.g., "CoSb3" vs "Skutterudite"), the pipeline uses a **Formula-to-Family Mapping** table:
- **Bi-Te**: Matches formulas containing "Bi" and "Te" with stoichiometry ratio ~2:3.
- **Pb-Te**: Matches formulas containing "Pb" and "Te" with stoichiometry ratio ~1:1.
- **Skutterudites**: Matches formulas containing "Co", "Sb", "Fe", "Ni" with stoichiometry ratios typical of CoSb3, FeSb3, etc.
This mapping is hardcoded in `utils/mapping.json` and applied during Phase 1.

### Dataset Limitations & Mitigation
- **Missing Variables**: The spec assumes the database contains "elemental composition" and "Seebeck coefficient". If the raw data lacks specific elemental breakdowns (e.g., only provides a formula string), the feature engineering step must include a robust parser or fallback to exclusion.
- **Sample Size**: If the filtered dataset (after restricting to Bi-Te, Pb-Te, Skutterudites) contains fewer than 100 records, the 80/20 split is replaced by **Repeated 5-Fold Cross-Validation (10 repeats)** to ensure stable metric estimation.
- **Missing Periodic Data**: If an element in the composition lacks electronegativity/radius data in `mendeleev`, the record is excluded (as per `spec.md` Edge Cases), and a log entry is created.
- **Temperature Confounding**: Temperature is a critical covariate. If missing, the record is excluded.

## Methodology

### Phase 1: Data Ingestion, Stoichiometry Filtering, and Retention Check (FR-001, FR-002, SC-005)
1.  **Download**: Fetch data from the DOI source.
2.  **Parse & Map**: Normalize formulas and map to families using the **Formula-to-Family Mapping**.
3.  **Stoichiometry Filter**: Parse formulas (e.g., "Bi2Te3") and filter for specific stoichiometric ranges (e.g., 2:3 for Bi-Te) to reduce noise.
4.  **Retention Check**: Calculate retention rate = (Filtered Records / Total Input Records).
    -   **CRITICAL**: If retention rate < 95%, **HALT** pipeline with error "SC-005 Violation: Retention < 95%".
5.  **Sanity Check**: Remove records with missing Seebeck or Temperature values.
6.  **Output**: `data/processed/cleaned_compositions.csv`.

### Phase 2: Feature Engineering (FR-003, VI)
For each valid record, calculate the following descriptors using `mendeleev`:
1.  **Mean Atomic Radius**: Weighted average of constituent atomic radii.
2.  **Electronegativity Variance**: Variance of constituent electronegativities.
3.  **Valence Electron Concentration (VEC)**: Weighted average of valence electrons.
4.  **Atomic Number Variance**: Variance of constituent atomic numbers (Retained per FR-003).
5.  **Temperature**: Included as a continuous covariate.
6.  **Material Family**: Categorical encoding (One-Hot).

*Statistical Note*: These descriptors are defined by deterministic formulas. No stochastic imputation is used. Collinearity between VEC and Atomic Number Variance is expected; this is addressed in Phase 4.

### Phase 3: Modeling and Evaluation (FR-004, FR-005, FR-008, SC-002)
1.  **Split Strategy**:
    -   If N >= 100: Stratified 80/20 split by `Material Family`.
    -   If N < 100: Repeated 5-Fold CV (10 repeats) on full set.
2.  **Baseline**: Linear Regression (Ordinary Least Squares).
3.  **Model**: `GradientBoostingRegressor` (scikit-learn), `n_estimators=100`, `max_depth=3`, `random_state=42`.
4.  **Cross-Validation**: 5-fold CV on the training set (or full set if N < 100).
5.  **Significance Testing**:
    -   **Permutation Test**: 1,000 iterations shuffling the target variable.
    -   **p-value (Model vs Null)**: Proportion of permuted R² >= Observed R².
    -   **Baseline Comparison**: F-test to determine if Gradient Boosting significantly improves over Linear Regression (p < 0.05).
6.  **Metrics**:
    -   R² (Coefficient of Determination).
    -   MAE (Mean Absolute Error).
    -   **95% Confidence Interval** for R² (calculated from CV distribution).
    -   **Permutation p-value**.
    -   **Baseline p-value**.
7.  **Feature Importance**: Extract and rank top 5 features.

### Phase 4: Visualization and Reporting (FR-006, FR-007)
1.  **Collinearity Analysis**:
    -   Calculate Pearson correlation matrix for all descriptors.
    -   Calculate Variance Inflation Factor (VIF) for each feature.
    -   Report features with VIF > 5 as "High Collinearity".
2.  **Plots**: Scatter plots of Top 3 descriptors vs. Seebeck coefficient (residualized for Temperature) with trend lines.
3.  **Physical Plausibility Check**: Compare top features against known thermoelectric trends (e.g., VEC trends in Bi-Te).
4.  **Classification**:
    -   **Success**: R² > 0.2 AND Permutation p-value < 0.05.
    -   **Inconclusive**: 0.2 ≤ R² < 0.4 OR (R² > 0.2 but p >= 0.05).
    -   **Failure**: R² < 0.2 OR p >= 0.05.
5.  **Output**: `docs/figures/` (PNG/SVG) and `docs/report.md`.

## Statistical Rigor & Assumptions

-   **Multiple Comparisons**: Since individual Pearson correlations are reported for multiple descriptors, a Bonferroni correction is applied for hypothesis testing.
-   **Causal Inference**: This is an observational study. Claims are strictly **associational**. No causal claims about "alloying causing changes" are made; the model predicts based on correlation.
-   **Collinearity**: Compositional descriptors (e.g., VEC and Atomic Number) are highly correlated. The plan reports feature importance from the tree-based model but explicitly acknowledges in the report that "independent effects" cannot be definitively separated. VIF and PCA are used to quantify this.
-   **Power Analysis**: For small datasets (N < 100), Repeated CV is used to stabilize estimates. Permutation tests are robust for small N.
-   **Measurement Validity**: The periodic table data from `mendeleev` is the standard reference. Validation of the Seebeck coefficient values relies on the integrity of the source database (DOI 10.1038/sdata.2017.85).

## Computational Feasibility (CI Constraints)

-   **Hardware**: 2 CPU cores, 7 GB RAM.
-   **Strategy**:
    -   Use `pandas` with `float32` where possible to reduce memory.
    -   Limit dataset to the specific material families to reduce N.
    -   `GradientBoostingRegressor` with 100 trees is CPU-tractable for N < 10,000.
    -   Permutation test (1,000 iterations) is CPU-tractable for N < 1,000.
    -   No GPU libraries (PyTorch/TensorFlow) are used.
    -   Runtime target: < 1 hour for the full pipeline.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **DOI 10.1038/sdata.2017.85 unreachable in CI** | High | Script attempts multiple known URLs (Nature, Zenodo). If all fail, pipeline exits with `DATA_UNAVAILABLE` error. |
| **Dataset too small (< 50 records)** | Medium | Fallback to Repeated 5-Fold CV (10 repeats). Report explicitly states "Small Sample Size". |
| **Retention Rate < 95%** | Critical | Pipeline halts with CRITICAL ERROR. No report generated. |
| **Missing periodic data for rare elements** | Medium | Exclude record, log warning. Do not impute. |
| **R² < 0.05 (Worse than mean)** | Low | Expected outcome. Report "Failure" per spec, but analyze *why* (e.g., "Band structure missing"). |