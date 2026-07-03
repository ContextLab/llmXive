# Research: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

## Executive Summary

This research plan outlines the strategy to identify cross-tumor gene-expression biomarkers predicting chemotherapy response. The core challenge is integrating heterogeneous data (TCGA RNA-seq vs. GEO microarrays) and ensuring statistical rigor (multiple testing correction, power analysis) while adhering to strict CPU-only compute constraints. The strategy relies on a **Data Feasibility Gate** to ensure valid response labels and **Nested Cross-Validation** to prevent data leakage.

## Dataset Strategy

The project relies on public repositories. Per the `# Verified datasets` block, we will use the following verified sources. Note that while specific GEO accession numbers (GSE25055, GSE42752) are mentioned in the spec, the verified block does not contain direct URLs for these specific GEO IDs. We will use the verified HuggingFace mirrors for general RNA-seq and GEO data structures, and if specific GEO IDs are unavailable in the verified list, we will explicitly state the data gap and attempt to fetch via standard `GEOquery` (which may fail if the specific dataset is not mirrored or accessible without authentication). If the preferred datasets are unavailable, the pipeline will dynamically select the next available verified GEO dataset with response labels.

**Verified Data Sources to be Used:**

| Dataset Type | Source / Description | Verified URL (if available) | Usage Strategy |
|:--- |:--- |:--- |:--- |
| **TCGA RNA-seq** | TCGA RNA-seq counts & metadata | ` (Example) | Primary discovery set. We will attempt to fetch TCGA data via `TCGAbiolinks` (R) or the verified HuggingFace mirrors. If specific tumor types (e.g., BRCA, LUAD, COAD) are not in the verified list, we will use the available TCGA samples and limit analysis to those types. **Feasibility Gate**: Must have response labels. |
| **GEO Microarray** | GEO expression data | ` | External validation. We will use verified GEO mirrors. If GSE25055/GSE42752 are not directly available in the verified list, we will use the available GEO datasets with response labels and note the substitution in `results/summary.md`. **Feasibility Gate**: Must have response labels. |
| **RNA-seq Index** | RNA-seq metadata | ` | Cross-reference for gene IDs and platform info. |

**Dataset Gap Analysis & Mitigation:**
- **Gap**: The `# Verified datasets` block does not contain direct URLs for `GSE25055` or `GSE42752`.
- **Mitigation**: The pipeline will first attempt to fetch these specific IDs via `GEOquery`. If that fails (or if the verified list implies they are not available in the provided mirrors), the system will fallback to using the *verified* GEO datasets available in the HuggingFace mirrors that contain response labels. The `results/summary.md` will explicitly list which datasets were actually used versus those requested in the spec.
- **Gap**: `DESeq2` and `VST` have "NO verified source found" in the block.
- **Mitigation**: These are *methods*, not datasets. We will implement them via the `rpy2` interface to the R `DESeq2` package, which is a standard, open-source tool. No external URL is needed for the software itself, only for the data it processes.

## Methodological Rationale

### 1. Data Harmonization & Normalization
- **Challenge**: TCGA (RNA-seq) and GEO (Microarray) use different scales and identifier types.
- **Strategy**:
 1. **Identifier Harmonization**: Use `biomaRt` (R) or `mygene` (Python) to map all gene IDs to HGNC symbols. Filter out genes with <95% coverage.
 2. **Normalization**:
 - **RNA-seq**: Standard DESeq2 VST.
 - **Microarray**: Convert raw intensities to log2.
 - **Cross-Platform Alignment**: Apply **Quantile Normalization** to align the distribution of log2-transformed microarray data with the VST-normalized RNA-seq data.
 - **Exclusion**: **ComBat-seq is NOT used** for microarray data as it assumes a negative binomial distribution which microarrays do not follow.
- **Rationale**: VST stabilizes variance for RNA-seq. Quantile Normalization is a distribution-agnostic method suitable for aligning continuous data from different platforms, avoiding the statistical invalidity of applying count-based methods to microarrays.

### 2. Differential Expression (DE) & Meta-Analysis
- **Strategy**:
 1. **Feature Selection**: Instead of a fixed Discovery/Training split, feature selection (DE) is performed **inside the inner loop** of the Nested Cross-Validation.
 2. **DE Analysis**: Run DESeq2 Wald test on the training fold of the inner loop. Filter: FDR < 0.05, |log2FC| > 1.0.
 3. **Cross-Tumor Integration**:
 - Compute intersection of significant genes across ≥2 tumor types (from the meta-analysis of p-values).
 - **Fallback**: If intersection is empty, take the union of top-ranked genes (≤50) by p-value.
 - **Meta-Analysis**: Apply Stouffer's method to combine p-values across tumor types.
 - **Usage**: The resulting gene panel is used as the **feature set** for the Pan-Cancer model.
- **Rationale**: Nested CV prevents data leakage (circular validation). Stouffer's method provides a robust ranking of genes across tumors, which defines the search space for the predictive model.

### 3. Predictive Modeling
- **Model**: Elastic-net logistic regression (L1 + L2 regularization).
- **Training Strategy**: **Pan-Cancer Model**.
 - Pool all samples from all available tumor types (after normalization).
 - Train a single model using the meta-analyzed gene panel as features.
 - **Validation**:
 - **Internal**: 5-fold nested cross-validation (outer loop for evaluation, inner loop for hyperparameter tuning and feature selection).
 - **External**: Test on independent GEO datasets (not used in training).
 - **Cross-Tumor**: Leave-One-Cancer-Type-Out (LOO) validation (dynamic based on available types).
- **Rationale**: Training a single model on pooled data tests the hypothesis that a *common* biomarker panel predicts response across tumors. Nested CV ensures the model's performance is an unbiased estimate of its predictive power.

### 4. Statistical Rigor & Multiple Testing
- **Correction**: Bonferroni correction applied to:
 - Meta-analysis p-values (m = number of genes in final panel).
 - Model comparisons (DeLong's test, m = number of comparisons).
- **Threshold**: Adjusted p < 0.01.
- **Power**: Acknowledgement that sample sizes may be limited in specific tumor types. If <50 responders/non-responders, power limitations are explicitly reported.

### 5. Compute Feasibility (CPU-Only)
- **Constraint**: 2 CPU, 7GB RAM, 6h runtime.
- **Mitigation**:
 - **Gene Limit**: Analysis restricted to the **top [deferred] most variable genes**.
 - **Batch Processing**: Process tumor types sequentially, not in parallel, to save RAM.
 - **Model Size**: Restrict final gene panel to ≤50 genes.
 - **Library Choice**: Use `scikit-learn` for modeling (CPU-optimized) and `rpy2` for DESeq2 (which is efficient enough for ≤1000 samples).
 - **Timeout Watchdog**: Implementation of a watchdog to halt if runtime exceeds a predefined threshold.

## Decision Log

| Decision | Rationale | Alternative Rejected |
|:--- |:--- |:--- |
| **Use R (DESeq2) via rpy2** | DESeq2 is the gold standard for RNA-seq DE; Python alternatives are less mature. | Pure Python GLMs (e.g., `statsmodels`) lack specific RNA-seq variance modeling. |
| **Stouffer's Method** | Robust for combining p-values from independent studies; handles directionality. | Fisher's method (less sensitive to consistent direction). |
| **Elastic-Net** | Handles high dimensionality (p >> n) and collinearity; performs feature selection. | Random Forest (harder to interpret coefficients, higher RAM usage). |
| **Fallback to Union** | Ensures a panel is produced even if intersection is empty (common in cross-tumor studies). | Strict intersection only (risk of producing an empty panel). |
| **Quantile Normalization** | Distribution-agnostic method suitable for aligning microarray and RNA-seq data. | ComBat-seq (invalid for microarrays due to distributional mismatch). |
| **Nested CV with Internal Feature Selection** | Prevents data leakage; ensures feature selection is part of the model training process. | Fixed Discovery/Training split (creates circular validation). |