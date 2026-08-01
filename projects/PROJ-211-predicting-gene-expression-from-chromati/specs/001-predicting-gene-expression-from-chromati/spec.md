# Specification: Predicting Gene Expression from Chromatin Accessibility in Human Cells

## 1. Introduction

### 1.1 Purpose
This document defines the requirements for a computational pipeline that predicts steady-state gene expression levels from bulk chromatin accessibility profiles (DNase-seq or ATAC-seq) across multiple human cell lines. The goal is to quantify the extent to which chromatin accessibility serves as a predictor of transcriptional output, while acknowledging the limitations of bulk profiling.

### 1.2 Scope
The pipeline will:
- Download paired RNA-seq and DNase-seq/ATAC-seq data for at least 5 human cell lines from the ENCODE consortium.
- Preprocess accessibility signals within ±50kb windows of Transcription Start Sites (TSS).
- Train interpretable regression models (Elastic Net) to map accessibility features to gene expression.
- Evaluate model performance using correlation coefficients and R² scores, with specific analysis on housekeeping vs. cell-type-specific genes.
- Generate regulatory insights regarding the relationship between chromatin state and gene expression.

### 1.3 Limitations and Caveats
**Important**: This project uses bulk chromatin accessibility profiles. As noted by reviewer Freeman Dyson, bulk profiles smooth over the single-cell heterogeneity that is the true engine of differentiation. Therefore, the predictive models generated here represent a **first-order approximation** of gene regulation. They do not capture cell-state specific dynamics or single-cell heterogeneity. The results should be interpreted as statistical correlations within the specific bulk populations sampled, not as causal laws governing individual cell behavior.

## 2. User Stories

### US1: Download and Preprocess Data
As a researcher, I want to download and preprocess paired multiomic data so that I have a clean, aligned dataset for modeling.
- **Acceptance Criteria**:
 - Data for ≥5 cell lines (e.g., GM12878, K562, HMEC, IMR90, HepG2) is retrieved from ENCODE.
 - Accessibility signal is aggregated within ±50kb of TSS.
 - Genes with zero expression in all samples are filtered.
 - Data is transformed (log pseudocount) and missing values imputed.
 - Top variable peaks are selected.

### US2: Train and Validate Models
As a data scientist, I want to train interpretable regression models and validate them so that I can assess the predictive power of chromatin accessibility.
- **Acceptance Criteria**:
 - Elastic Net models are trained for each cell line.
 - Cross-validation (k=5) is performed.
 - Pearson correlation and R² scores are calculated.
 - Performance is evaluated separately for housekeeping and cell-type-specific genes.
 - External validation (train on subset, test on held-out cell line) is performed.

### US3: Analyze and Report Insights
As a biologist, I want to analyze feature importance and regulatory insights so that I can understand which genomic regions drive expression predictions.
- **Acceptance Criteria**:
 - Feature importance is extracted and ranked.
 - Peaks are mapped to genomic locations relative to TSS.
 - Statistics on TSS proximity for top features are reported.
 - A performance gap analysis between gene categories is generated.
 - A summary report of regulatory insights is produced.

## 3. Functional Requirements

### FR-001: Data Acquisition
The system shall download real paired RNA-seq and DNase-seq/ATAC-seq count data from the ENCODE portal for at least 5 human cell lines.

### FR-002: Data Preprocessing
The system shall aggregate accessibility signals within ±50kb of TSS, filter zero-expression genes, apply log(pseudocount+1) transformation, and impute missing values using median imputation.

### FR-003: Feature Selection
The system shall select the top N (default 1000) most variable peaks based on variance across samples.

### FR-004: Model Training
The system shall train Elastic Net regression models (α=0.5) with hyperparameter tuning via cross-validation.

### FR-005: Model Evaluation
The system shall calculate Pearson correlation coefficients and R² scores, applying Bonferroni correction for p-values.

### FR-006: Gene Category Analysis
The system shall calculate and report R² specifically for housekeeping genes and cell-type-specific genes, and compute the performance gap (ΔR²).

### FR-007: Feature Importance
The system shall extract non-zero coefficients and rank features by absolute magnitude.

### FR-008: Genomic Annotation
The system shall map peak coordinates to their genomic location relative to the nearest TSS.

### FR-009: Reporting
The system shall generate a summary report (`docs/regulatory_insights_report.md`) comparing model performance across cell types and gene categories.

## 4. Non-Functional Requirements

### SC-001: Accuracy
Models must achieve a minimum R² of 0.1 for housekeeping genes to be considered valid (baseline check).

### SC-002: Reproducibility
All data generation and processing steps must be deterministic when using a fixed random seed (Seed=42).

### SC-003: TSS Proximity
At least 40% of the top-100 most important features must be located within ±10kb of a TSS.

### SC-004: Performance Gap
The system must explicitly report the difference in R² between housekeeping and cell-type-specific genes.

### SC-005: Resource Constraints
The pipeline must execute on standard CPU-only infrastructure with the following resource thresholds:
- **CPU**: Several CPU cores (e.g., 4+ vCPUs)
- **RAM**: Sufficient RAM to hold the processed dataset in memory (target < 7GB for standard runs)
- **Runtime**: Maximum expected runtime of 6 hours for the full pipeline on the specified cell lines.

### SC-006: External Validation
The system must support a "train on subset, test on held-out cell line" validation strategy.

## 5. Data Model

### 5.1 Input Data
- **RNA-seq Counts**: Matrix of gene expression counts (genes x samples).
- **DNase/ATAC-seq Peaks**: BED file of genomic regions with accessibility signal.
- **Gene Coordinates**: BED file of gene TSS locations.

### 5.2 Processed Data
- **TSS Aggregated Features**: CSV of accessibility signal aggregated around TSS.
- **Filtered Expression**: CSV of expression data after zero-expression filtering.
- **Variable Peaks**: CSV of the top N variable peaks.

### 5.3 Output Models
- **Elastic Net Models**: Pickled sklearn models per cell line.
- **Feature Importance**: CSV of ranked features.
- **Evaluation Metrics**: JSON/CSV files containing correlations, R², and p-values.

## 6. Implementation Plan

The implementation is divided into phases:
1. **Setup**: Project structure, dependencies, and environment configuration.
2. **Foundational**: Data schemas, synthetic data generators, and utility functions.
3. **US1 Implementation**: Data download, preprocessing, and feature selection.
4. **US2 Implementation**: Model training, validation, and evaluation.
5. **US3 Implementation**: Feature importance analysis and reporting.
6. **Documentation**: Final reports and limitations.

## 7. Appendix

### 7.1 References
- ENCODE Consortium: https://www.encodeproject.org/
- Elastic Net: Zou & Hastie (2005)
- Freeman Dyson's review notes on bulk vs. single-cell heterogeneity.

### 7.2 Glossary
- **TSS**: Transcription Start Site
- **DNase-seq**: DNase I hypersensitive sites sequencing
- **ATAC-seq**: Assay for Transposase-Accessible Chromatin using sequencing
- **R²**: Coefficient of determination