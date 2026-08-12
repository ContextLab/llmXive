# Research: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

## Research Question

Can constitutive (pre-challenge) metabolite profiles in plants predict disease resistance phenotypes using supervised machine learning, while maintaining rigorous statistical validation and avoiding data leakage?

## Dataset Strategy

### Primary Data Source
The study relies on **Metabolomics Workbench**, a public repository containing metabolomic data with associated phenotype metadata.

*   **Source**: Metabolomics Workbench (https://www.metabolomicsworkbench.org/)
*   **Access**: Public, programmatic download via `requests` or `pyMW` (Python wrapper).
*   **Verification**: Verified via `fetch_url` on Metabolomics Workbench study catalog that multiple public datasets include pre-challenge metabolite profiles linked to disease-resistance metadata (phenotype scores) for the same germplasm.
*   **Feasibility**: Direct download is possible without credentials, satisfying GitHub Actions free-tier constraints. No access-gated data (e.g., ADNI, UK Biobank) is required.

### Dataset Selection Criteria
1.  **Content**: Must contain both pre-challenge metabolite intensity tables AND disease-resistance labels (binary or ordinal) for the same samples.
2.  **Sample Size**: Target ≥50 samples to support stratified 5-fold cross-validation and a meaningful hold-out set.
3.  **Identifier**: Metabolites must be identifiable by InChIKey for cross-study alignment.

### Data Processing Strategy
1.  **Download**: Fetch raw files (intensity matrices, phenotype metadata) for ≥1 study.
2.  **Preprocessing**:
    *   **Missing Values**: Discard features missing >30% of samples (FR-002).
    *   **Normalization**: Log-transform remaining intensities to stabilize variance.
    *   **Batch Correction**: Apply ComBat (if ≥2 studies combined) to remove technical batch effects (FR-004).
3.  **Label Harmonization**:
    *   Standardize resistance labels via z-scoring within study or stratification by assay method to address heterogeneity (FR-013).
    *   Ensure labels are binary (resistant/susceptible) or ordinal (0–3) based on published thresholds.

### Statistical Rigor & Methodological Constraints

#### Multiple Comparison Correction
*   **Requirement**: Benjamini-Hochberg FDR ≤0.05 for correlation tests between metabolites and resistance (FR-008).
*   **Rationale**: Controls false discovery rate in exploratory analysis where hundreds of metabolites are tested simultaneously.
*   **Source**: Benjamini & Hochberg (1995), verified via source `1906.01701` (arXiv:1906.01701).

#### Power & Sample Size
*   **Limitation**: If sample size <50, the project will flag a power limitation and perform learning curve analysis (SC-004) per DOME recommendations.
*   **Strategy**: Use stratified 5-fold CV to maximize data utilization. Reserve a hold-out set only if N ≥ 50.

#### Causal Inference & Framing
*   **Constraint**: The study is **observational**. No randomization is used.
*   **Action**: All findings MUST be framed as **associational** (FR-011). No causal claims (e.g., "metabolite X causes resistance") will be made.
*   **Rationale**: Pre-challenge metabolites are correlated with the outcome, but the design does not support causal inference.

#### Collinearity Diagnostics
*   **Requirement**: Calculate Variance Inflation Factor (VIF) for all predictors (FR-012).
*   **Threshold**: Flag metabolites with VIF > 5.
*   **Rationale**: Even though Random Forest handles collinearity internally, biological interpretation requires identifying redundant predictors.

#### Permutation Testing
*   **Requirement**: Perform ≥1,000 permutations to assess significance against a null distribution (FR-007).
*   **Threshold**: Model performance must exceed null distribution with p < 0.05 (SC-003).
*   **Rationale**: Validates that the model is not learning noise.

### Compute Feasibility (CPU-First)
*   **Environment**: GitHub Actions free-tier (multi-core CPU, sufficient RAM, 14GB disk, 6h limit).
*   **Method**: Random Forest with ≤50 features and ≤1000 samples is CPU-tractable.
*   **No GPU Needed**: No deep learning or large transformer models are used. All methods (scikit-learn, ComBat, VIF) run efficiently on CPU.
*   **Streaming**: If dataset > 7GB, stream data using `pandas.read_csv(..., chunksize=...)` to process in batches.

### Decision / Rationale
*   **Why Random Forest?** Robust to non-linear relationships, handles mixed data types, provides feature importance, and is computationally efficient on CPU.
*   **Why ComBat?** Standard method for batch correction in metabolomics; essential for combining multiple studies.
*   **Why Benjamini-Hochberg?** Controls false discovery rate better than Bonferroni for high-dimensional data.
*   **Why CPU?** The scale of the data (metabolomics, not genomics) and the algorithm (Random Forest) fit comfortably within CPU constraints. No GPU escape hatch is required.

## Edge Cases & Mitigations

| Edge Case | Mitigation |
|-----------|------------|
| **No dataset with both pre-challenge data and resistance labels** | Metabolomics Workbench verified to contain such studies. If none found, reframe question or use a proxy dataset (open source only). |
| **Sample size < 50** | Flag power limitation. Use learning curve analysis. Avoid hold-out set; use full CV for evaluation. |
| **Batch correction fails (ComBat convergence)** | Log error. Proceed with single-study analysis if only one study available. If multiple, skip correction and flag as limitation. |
| **Metabolites cannot be aligned via InChIKey** | Exclude unmatched metabolites. Report number of dropped features. |
| **Hold-out set has no positive samples** | Stratified splitting ensures class balance. If imbalance persists, use stratified shuffling or report as limitation. |
