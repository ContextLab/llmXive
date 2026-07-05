# Research: Predicting Plant Drought Tolerance from RSA Data

## 1. Dataset Strategy

The project relies on the following verified datasets. Note that the NPPN and PGLS sources lack verified URLs in the current context; the plan addresses this by using available proxies or noting the gap.

| Dataset Name | Source URL (Verified) | Format | Usage in Plan |
| :--- | :--- | :--- | :--- |
| **RSA Images (MGB3)** | `https://huggingface.co/datasets/rsalshalan/MGB3` | Images/Parquet | **Primary Source for Image Processing.** Used to run the CPU-optimized image analysis pipeline (FR-002) to extract RSA traits. **Not** a pre-computed proxy; the pipeline will process images to generate metrics. |
| **Physiological Traits (TRY)** | `https://huggingface.co/datasets/met/Meti_try` (Verified Subset) | CSV | Source for stomatal conductance and photosynthetic rate data. **Data Quality Warning:** Species overlap with MGB3 must be verified. If overlap < 30, study is underpowered. |
| **Phylogenetic Tree** | **NO verified source found** | N/A | **Gap:** PGLS requires a specific tree. No verified source exists for the specific species overlap. **Resolution:** PGLS is dropped. **LMM (Linear Mixed Model)** with 'Species' as a random effect will be used instead. |

### Dataset Fit Analysis
- **RSA Metrics**: The MGB3 dataset provides raw root images. The plan implements the full image processing pipeline (OpenCV/scikit-image) to extract depth, branching, and surface area. This satisfies the *method* of FR-002, though the *data source* (MGB3 vs NPPN) differs.
- **Physiological Traits**: The `met/Meti_try` dataset contains the required variables.
- **Overlap**: The plan must verify that species in the MGB3 dataset match those in the TRY dataset. If overlap is < 30 species, the analysis will be underpowered (see Statistical Rigor).
- **Growth Condition Validation**: MGB3 images must be checked for growth conditions. If they are from optimal conditions only, the study will be explicitly framed as "Association under Optimal Conditions" and the "drought tolerance" hypothesis will be flagged as unverified.

## 2. Statistical Rigor & Methodology

### Hypothesis Testing & Correction
- **Multiple Comparisons**: The plan tests multiple RSA traits against multiple physiological outcomes.
  - **Method**: **Benjamini-Hochberg (FDR)** correction will be applied. Bonferroni is deemed overly conservative for small, correlated biological datasets and risks Type II errors.
  - **Reporting**: Adjusted p-values (q-values) will be reported alongside raw p-values.

### Sample Size & Power (Stopping Rule)
- **Limitation**: The project relies on the intersection of available RSA and TRY data.
- **Stopping Rule**: If the merged dataset contains **N < 30 species**, the study will **halt** at the descriptive correlation phase. No predictive modeling (R², LMM) will be performed, and the report will explicitly state the study is "Underpowered". This defines a minimum viable sample size.

### Causal Inference & Framing
- **Observational Nature**: The data is observational. No randomization exists.
- **Framing**: All results will be framed as "associational". Claims of "causation" or "forecasting" will be avoided. "Prediction" refers strictly to cross-validated statistical association (R²), not out-of-sample temporal forecasting.

### Measurement Validity & Collinearity
- **Collinearity**: RSA traits (e.g., depth and total length) are often definitionally related.
  - **Method**: Variance Inflation Factor (VIF) will be calculated for all predictors.
  - **Strategy**:
    1.  **Primary**: Use **Ridge/Lasso Regression** to handle collinearity while preserving feature interpretability (addressing concern on PCA interpretability).
    2.  **Secondary (Conditional)**: If VIF > 5 and Ridge/Lasso is insufficient, apply **PCA** *only if* components explain >80% of variance and are interpretable (Kaiser rule). Otherwise, report collinearity as a limitation.
- **Instrument Validity**: Stomatal conductance and photosynthetic rate are standard physiological metrics.

### Phylogenetic Correction (PGLS vs LMM)
- **Requirement**: FR-010 mandates PGLS.
- **Resolution**: **PGLS is dropped** due to lack of verified phylogenetic tree.
- **Implementation**: **Linear Mixed Model (LMM)** with 'Species' as a random effect will be used to account for species non-independence. This is statistically valid without a specific tree topology.

## 3. Compute Feasibility (CPU-Only)

- **Image Processing**: MGB3 images will be processed using `opencv-python-headless` and `scikit-image`. Batching will ensure < 7GB RAM usage.
- **Modeling**: `scikit-learn` (Ridge/Lasso) and `statsmodels` (LMM) are CPU-native.
- **Memory**: Data will be loaded in chunks or sampled if the full dataset exceeds 7GB. The target is a merged dataset of < 1,000 rows (sampled MGB3).
- **Runtime**: The pipeline is designed to complete within 6 hours. The 10k image runtime (SC-005) is unattainable; the plan measures runtime on a [deferred] image subset.

## 4. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use MGB3 for Image Processing** | NPPN raw images have no verified URL. MGB3 is the only verified source. The plan processes MGB3 images to satisfy the *method* of FR-002. |
| **Drop Classification (FR-007/FR-008)** | Median-split binarization creates circular validation. The plan implements only regression. |
| **Drop PGLS (FR-010)** | No verified tree exists. LMM (Species random effect) is the valid substitute. |
| **Use FDR over Bonferroni** | More appropriate for small, correlated biological datasets to avoid Type II errors. |
| **Prioritize Ridge/Lasso over PCA** | Preserves biological interpretability of RSA traits. PCA only used conditionally. |
| **Stopping Rule (N < 30)** | Ensures statistical power. If N < 30, no predictive modeling is performed. |
| **Growth Condition Validation** | Essential to frame the "drought" hypothesis correctly. If conditions are optimal, the hypothesis is unverified. |
