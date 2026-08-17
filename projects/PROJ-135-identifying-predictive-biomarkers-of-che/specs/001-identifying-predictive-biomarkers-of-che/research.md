# Research: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

## Overview
This research phase validates the feasibility of the proposed pipeline, confirms data availability, and defines the statistical methodology. The primary goal is to ensure that the required datasets (TCGA RNA-seq, GEO microarray with response labels) are accessible via the official GDC API and GEOquery, and that the statistical methods (DESeq2, Stouffer's meta-analysis, Elastic-Net) are computationally feasible on the target hardware within a Dockerized R environment.

## Dataset Strategy

| Dataset Name | Purpose | Verified Source (URL) | Access Method | Notes |
|--------------|---------|-----------------------|---------------|-------|
| TCGA RNA-seq (Ovarian, LUAD, BRCA) | Discovery Cohort | Name or service not known)"))] (via TCGAbiolinks) | `TCGAbiolinks::GDCdownload()` | Official GDC API. Requires `TCGAbiolinks` R package. Data is RNA-seq HTSeq-Counts. |
| GEO Microarray (GSE25055) | Validation Cohort 1 | | `GEOquery::getGEO()` | Official GEO. Contains expression data and chemotherapy response annotations. |
| GEO Microarray (GSE42752) | Validation Cohort 2 | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE42752 | `GEOquery::getGEO()` | Official GEO. Contains expression data and chemotherapy response annotations. |

**Critical Feasibility Note**: The plan explicitly rejects the use of synthetic data or metadata-only HuggingFace files for the primary analysis. The spec (FR-001, FR-002) requires real RNA-seq count matrices and GEO microarray expression data.
- **Resolution**: The pipeline will use the official GDC API (via `TCGAbiolinks`) and GEOquery to download real expression matrices. If a specific GEO dataset (e.g., GSE25055) is found to lack response annotations or expression data during the feasibility check, the pipeline will skip that dataset and log a warning. The pipeline will proceed only if at least 2 valid datasets with response labels are available (satisfying the "skip and warn" logic of T013).
- **Data Volume**: The full TCGA datasets may exceed the available RAM limit. The plan will implement a "Small-Sample Real Data Mode" where a random subset of samples (e.g., 200 per tumor type) is used for the initial pipeline validation and model training, ensuring the -hour and 7 GB RAM limits are not breached while maintaining biological validity.

**Dataset Variables Fit**:
- **TCGA**: Metadata contains `tumor_type`, `sample_id`, `response_label` (if available in clinical data). Expression data (counts) is downloaded via GDC API.
- **GEO**: Metadata contains `response_label`. Expression data (matrix) is downloaded via GEOquery.
- **Action**: The `data_acquisition.py` script will:
 1. Download metadata and expression data from GDC/GEO.
 2. Verify the presence of response labels.
 3. If valid, proceed. If invalid, skip and log a warning.
 4. If the dataset is too large, sample a subset of samples for the "Small-Sample Real Data Mode".

## Statistical Methodology

### Differential Expression (FR-005)
- **Method**: DESeq2 Wald test (`DESeq2::DESeq()`).
- **Implementation**: R package `DESeq2` within the Docker container.
- **Thresholds**: FDR < 0.05 (Benjamini-Hochberg), |log2FC| > 1.0.
- **Handling**: Real count data will be used. No synthetic data.

### Meta-Analysis (FR-006)
- **Method**: Stouffer's method (weighted Z-score combination) using `meta::metap()`.
- **Fallback**: If intersection of significant genes is empty, use union of top-ranked genes ranked by meta p-value.
- **Correction**: Bonferroni correction applied to the final gene panel significance (m = number of genes).

### Predictive Modeling (FR-007, FR-008)
- **Algorithm**: Elastic-Net Logistic Regression (`glmnet` in R or `sklearn` in Python for the final model if R is not used for modeling).
- **Validation**: Nested Cross-Validation (Inner: parameter tuning, Outer: performance estimation).
- **External Validation**: Leave-One-Cancer-Type-Out (LOO) and external GEO datasets.
- **Metrics**: ROC-AUC, Precision-Recall, Calibration (Hosmer-Lemeshow or decile-based), DeLong's test (`pROC::roc.test()`).
- **Class Imbalance**: Stratified K-Fold; Cost-sensitive learning (class weights) if responder ratio < 20%.

### Multiple Testing (FR-010)
- **Correction**: Bonferroni.
- **m**: Number of genes in the final panel (for gene-level significance) or number of model comparisons (for DeLong's test).
- **Threshold**: Adjusted p < 0.01.

### Cross-Platform Normalization (FR-014)
- **Method**: ComBat-seq (`sva::ComBat_seq()`) for RNA-seq and ComBat (`sva::ComBat()`) for microarray data, or quantile matching.
- **Implementation**: R package `sva` within the Docker container.
- **Goal**: Align TCGA (RNA-seq) and GEO (Microarray) data before model application.

## Compute Feasibility

- **CPU-First**: All statistical methods (DESeq2, Elastic-Net, Stouffer's) are computationally lightweight and will run easily on a limited number of CPU cores / 7 GB RAM when using a "Small-Sample Real Data Mode" (subset of samples).
- **Data Volume**: The plan uses a subset of real data to fit within the 7 GB RAM limit. Full data streaming is not required for the initial validation run.
- **GPU Escape Hatch**: Not required. No deep learning or large transformer models are used.
- **Docker Overhead**: The Docker container adds minimal overhead to the CPU runtime and is well within the time limit for the subset of data.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **GDC/GEO download failure** | Retry logic with exponential backoff. Skip invalid datasets and log warnings. |
| **R dependency failure** | Use a pre-built Docker container (e.g., `biocontainers/deseq2`) to ensure all R packages are available. |
| **Class imbalance** | Use stratified CV and class weights. |
| **Runtime > 6 hours** | Use "Small-Sample Real Data Mode" (subset of samples) to ensure the pipeline completes within the time limit. |
| **Memory > 7 GB** | Use "Small-Sample Real Data Mode" and stream data where possible. |

## Decision/Rationale

- **Language**: Python 3.11 for orchestration, R 4.3 for statistical core (via Docker).
- **Data Strategy**: Real data from GDC and GEO. No synthetic data. "Small-Sample Real Data Mode" used to fit within compute constraints.
- **Statistical Rigor**: DESeq2, Stouffer's, Bonferroni correction, and DeLong's test are implemented using official R packages.
- **Feasibility**: The pipeline is designed to run on CPU within a Docker container. No GPU is needed.
