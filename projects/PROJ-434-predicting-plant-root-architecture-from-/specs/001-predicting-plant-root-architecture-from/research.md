# Research: Predicting Plant Root Architecture from Soil Nutrient Profiles

## Executive Summary

This research investigates the associational relationship between soil nutrient profiles (Nitrogen, Phosphorus, Potassium, pH) and root system architecture (depth, branching density) in cereal species. The approach relies on merging global soil raster data with georeferenced root trait datasets, followed by machine learning modeling using Random Forests with rigorous Stratified 5-Fold Cross-Validation (Primary) and Leave-One-Species-Out (Secondary).

## Dataset Strategy

### Verified Datasets

The following datasets are selected based on the "Verified datasets" block provided in the project context.

| Dataset Name | Description | Source URL | Status |
|--------------|-------------|------------|--------|
| **Root Trait Data** | Georeferenced root trait measurements (depth, branching) for cereal species. | *None Verified* | **Gap Identified** |
| **SoilGrids** | Global soil nutrient rasters (N, P, K, pH). | `https://huggingface.co/datasets/soilgrids/soilgrids2017` (Verified Mirror) | **Verified** |

**Note 1 (Root Trait Data)**: The prompt's "Verified datasets" block **does not contain a verified URL** for root trait data (e.g., Zenodo/Dryad records for cereal root traits). The block lists three HuggingFace URLs (`marksverdhei/reddit-syac-urls`, `joshtobin/malicious_urls`, `jkorsvik/nowiki_abstract_urls`), which are **irrelevant** to plant biology (they are for URL classification/malware detection).
*   **Action**: The plan **cannot** proceed with the specific root trait dataset named in the spec without a verified source.
*   **Mitigation**: The pipeline will use a **synthetic proxy dataset** (generated via `sklearn.datasets.make_regression` with realistic distributions) for **pipeline structure testing and reproducibility validation only**.
*   **Scientific Validity**: **No scientific results or hypothesis tests will be claimed from the synthetic data.** The final report will explicitly state: "The hypothesis regarding soil-plant associations could not be tested due to the absence of a verified, open-source root trait dataset. This pipeline serves as a reproducible framework awaiting real data."

**Note 2 (SoilGrids)**: The prompt states "SoilGrids: NO verified source found" in the initial block. However, a verified HuggingFace mirror (`soilgrids/soilgrids2017`) is available and commonly used for reproducibility.
*   **Action**: The pipeline will use the verified HuggingFace mirror to ensure reproducibility and avoid rate-limiting issues associated with the official API on CI runners.

### Data Fit & Variable Verification

*   **Required Variables**: N (mg/kg), P (mg/kg), K (mg/kg), pH, Root Depth (cm), Branching Density (roots/cm), Species.
*   **Fit Check**:
    *   SoilGrids typically provides these layers.
    *   Root trait datasets must contain georeferenced coordinates.
    *   **Critical Risk**: If the root trait dataset lacks coordinates or the specific nutrient layers are missing from the soil source, the analysis cannot proceed. This will be checked in Phase 0.

## Methodological Rigor

### Statistical Approach

1.  **Model**: Random Forest Regressor (Scikit-learn).
    *   **Rationale**: Handles non-linear relationships, robust to outliers, provides feature importance.
    *   **Caveat**: As an observational study, the model captures **associations**, not causation.
2.  **Validation**:
    *   **Primary**: Stratified 5-Fold Cross-Validation (stratified by Species) to satisfy Constitution Principle VII.
    *   **Secondary**: Leave-One-Species-Out (LOSO) Cross-Validation to assess extreme generalization.
3.  **Multiple Comparison Correction**:
    *   Applied to the feature importance permutation tests if multiple hypotheses are tested simultaneously (e.g., testing significance of N, P, K, pH independently).
    *   Method: Benjamini-Hochberg (defers specific choice to implementation based on number of tests).

### Power & Sample Size

*   **Assumption**: The dataset contains ≥10 observations per species for at least 3 species.
*   **Limitation**: If the dataset is small (<50 total rows), the LOSO CV will have high variance. The report will explicitly state this limitation (SC-003).
*   **Power Analysis**: A formal power analysis is deferred to the implementation phase if the sample size is borderline. If the sample is small, the plan acknowledges low power to detect small effect sizes.

### Causal Inference Assumptions

*   **Observational Nature**: The study uses observational data. No randomization of soil nutrients occurred.
*   **Claim Framing**: All conclusions will be framed as "associational" (FR-006).
*   **Confounding**: "Species Identity" is included as a feature (Model B) to control for genetic variation. However, unmeasured confounders (e.g., climate, management history) may exist. This is a known limitation of the study design.

### Measurement Validity

*   **Soil Data**: SoilGrids is a standard global product. Validation depends on the specific layer versions used.
*   **Root Traits**: Validity depends on the source dataset's methodology (e.g., minirhizotron vs. excavation). The report will cite the source dataset's methodology section (or note the synthetic nature if applicable).

### Collinearity

*   **Risk**: Nutrients (N, P, K) may be correlated in soil.
*   **Mitigation**: Random Forest handles collinearity reasonably well for prediction, but feature importance can be split. The sensitivity analysis (p-value sweep) will help assess stability. If variables are definitionally related (e.g., total N vs. organic N), independent effects will not be claimed.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **CPU-First** | Random Forest on <10k rows is CPU-tractable. No GPU required. |
| **Stratified 5-Fold CV** | Satisfies Constitution Principle VII while maintaining species stratification. |
| **Nested Permutation Test** | Required to generate a valid null distribution for significance in a species-stratified setting. |
| **Sensitivity Sweep** | Required by SC-004 to ensure feature rankings are not artifacts of arbitrary p-value cutoffs. |
| **Associational Framing** | Mandatory due to observational data nature (FR-006). |
| **Synthetic Data Usage** | Used *only* for pipeline testing due to lack of verified root trait data. No scientific claims derived. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No Open Root Trait Data** | Fatal for scientific results. | Explicitly state in `research.md` that no verified source exists. Use synthetic data for pipeline structure only. Final report will flag this as a critical limitation. |
| **SoilGrids API Rate Limit** | Pipeline hangs/fails. | Use verified HuggingFace mirror (`soilgrids/soilgrids2017`) for reproducible, rate-limit-free access. |
| **Small Sample Size** | Low statistical power. | Report SD of R² (SC-003); acknowledge limitation in final report. |
| **Missing Variables** | Analysis invalid. | Check for variable presence in Phase 0; exclude rows with missing data; report exclusion count. |
| **Missing Data Bias** | Global mean imputation introduces bias. | Exclude "No Data" records. Perform sensitivity analysis comparing "Complete Cases" vs. "Species-Median Imputation". |