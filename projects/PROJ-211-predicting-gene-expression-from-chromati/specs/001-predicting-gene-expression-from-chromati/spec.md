# Specification: Predicting Gene Expression from Chromatin Accessibility in Human Cells

## Overview

This project aims to build a predictive model that estimates steady-state gene expression levels from bulk chromatin accessibility profiles across multiple human cell lines. The work investigates the extent to which open chromatin regions serve as proxies for transcriptional activity.

## User Stories

### US1: Download and preprocess paired multiomic data
As a researcher, I want to download and preprocess paired RNA-seq and DNase-seq/ATAC-seq data for at least 5 human cell lines so that I can train models on real biological data.

### US2: Train and validate interpretable regression models
As a data scientist, I want to train Elastic Net models with cross-validation and calculate correlation coefficients with statistical corrections so that I can assess model performance and generalizability.

### US3: Analyze feature importance and report regulatory insights
As a biologist, I want to extract feature importance, map peaks to TSS, and compare model performance across gene categories so that I can derive biological insights about gene regulation.

## Functional Requirements

### FR-001: Data Acquisition
The system shall download paired RNA-seq and DNase-seq/ATAC-seq count data from the ENCODE portal for at least 5 human cell lines.

### FR-002: Data Preprocessing
The system shall aggregate accessibility signal within ±50kb windows of transcription start sites (TSS) and filter genes with zero expression across all samples.

### FR-003: Model Training
The system shall train Elastic Net regression models for each cell line with cross-validation to select the optimal regularization parameter.

### FR-004: Statistical Validation
The system shall calculate Pearson correlation coefficients between predicted and actual expression values and apply Bonferroni correction for multiple testing.

### FR-005: Feature Importance
The system shall extract non-zero coefficients from trained models and rank features by absolute magnitude.

### FR-006: Multiple Testing Correction
The system shall implement Bonferroni correction for p-values derived from correlation analyses.

### FR-007: Regulatory Insight Generation
The system shall calculate the percentage of top-ranked features within ±10kb of TSS and report performance gaps between housekeeping and cell-type-specific genes.

### FR-008: External Validation
The system shall perform external validation by training on a subset of cell lines and testing on held-out cell lines.

### FR-009: Housekeeping Gene Analysis
The system shall calculate R² metrics specifically for housekeeping genes (defined as genes with coefficient of variation ≤ 0.2).

### FR-010: Performance Gap Analysis
The system shall calculate and report the performance gap (ΔR²) between housekeeping and cell-type-specific genes.

### FR-011: Memory Constraints
The system shall operate within 7GB RAM constraints throughout the pipeline.

### FR-012: Runtime Constraints
The system shall complete the full pipeline within 6 hours on standard CPU hardware.

### FR-013: Reproducibility
The system shall use fixed random seeds for all stochastic operations to ensure reproducibility.

### FR-014: Gene Categorization
The system shall identify and categorize genes as housekeeping or cell-type-specific based on expression variance metrics.

## Non-Functional Requirements

### NFR-001: Code Quality
All Python code shall pass flake8 linting and follow black formatting standards.

### NFR-002: Documentation
All public functions shall have docstrings describing parameters, return values, and behavior.

### NFR-003: Error Handling
The system shall implement retry logic with fixed time intervals for network requests.

### NFR-004: Checksum Verification
All output files shall have SHA256 checksums recorded for integrity verification.

### NFR-005: Logging
The system shall log memory usage and runtime metrics to support performance analysis.

## Success Criteria

### SC-001: Housekeeping Gene Performance
The model shall achieve R² ≥ 0.3 for housekeeping genes across all cell lines.

### SC-002: TSS Proximity
At least 60% of the top 100 features shall be located within ±10kb of a TSS.

### SC-003: Feature Enrichment
TSS-proximal regions shall be significantly enriched in the top-ranked features compared to random expectation (p < 0.05).

### SC-004: Performance Gap
The performance gap (ΔR²) between housekeeping and cell-type-specific genes shall be statistically significant (p < 0.05).

### SC-005: Resource Constraints
The pipeline shall complete within measurable resource thresholds: Several CPU cores, sufficient RAM (≤7GB), and within 6 hours of runtime.

### SC-006: External Validation
The model shall demonstrate generalizability with R² ≥ 0.2 on held-out cell lines for housekeeping genes.

## Data Models

### Input Data
- **RNA-seq counts**: Matrix of gene expression values (genes × samples)
- **DNase-seq/ATAC-seq peaks**: BED format file with genomic coordinates and signal values
- **Gene annotations**: BED format file with gene coordinates and TSS information

### Output Data
- **Aggregated features**: CSV file with accessibility signal aggregated around TSS regions
- **Filtered expression**: CSV file with genes filtered for zero expression
- **Model artifacts**: Pickle files containing trained Elastic Net models
- **Evaluation metrics**: CSV and JSON files with correlation coefficients, p-values, and R² scores
- **Feature importance**: CSV file with ranked features and their coefficients
- **Regulatory insights**: JSON and Markdown files summarizing biological findings

## Implementation Notes

### Caveats
This project uses bulk chromatin accessibility profiles which provide a first-order approximation of gene regulation. Bulk profiles smooth over single-cell heterogeneity that is the true engine of differentiation. Prediction models should not be interpreted as causal laws but as statistical associations that capture major regulatory patterns.

### Limitations
- Bulk profiling obscures cell-type-specific regulation within heterogeneous samples
- Correlation does not imply causation; identified associations require experimental validation
- The model may not generalize to cell lines not represented in the training data
- Regulatory elements beyond ±50kb of TSS may contribute to gene expression but are not captured

## References
- ENCODE Consortium: The Encyclopedia of DNA Elements
- Friedman et al. (2010). Regularization Paths for Generalized Linear Models via Coordinate Descent
- Fisher et al. (1925). On a distribution yielding the error functions of several well known statistics

## Version History
- v1.0: Initial specification
- v1.1: Added caveat regarding bulk profiling limitations and correlation vs causation
- v1.2: Corrected SC-005 to specify measurable resource thresholds (Several CPU, sufficient RAM, 6h)