# Project Plan: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

## Overview
This project aims to identify genetic markers (SNPs) associated with susceptibility to Colony Collapse Disorder (CCD) in honeybees (*Apis mellifera*) using a Genome-Wide Association Study (GWAS) pipeline. The analysis leverages genomic data from public repositories (NCBI BioProject PRJNA566029) and applies rigorous statistical methods to distinguish true associations from false positives.

## Objectives
1. **Data Acquisition**: Retrieve high-quality genomic and phenotypic data for honeybee colonies with confirmed CCD status.
2. **Quality Control**: Implement strict filtering for variant quality, missingness, and population stratification.
3. **Association Testing**: Perform logistic regression GWAS with Benjamini-Hochberg FDR correction.
4. **Validation**: Validate findings using LASSO regression and Polygenic Risk Scores (PRS).
5. **Annotation**: Map significant SNPs to genes and functional pathways.

## Methodology

### 1. Data Sources
- **Genomic Data**: NCBI BioProject PRJNA566029 (Honeybee Genome Variants).
- **Phenotypic Data**: Colony health records including CCD diagnosis, Varroa mite counts, and geographic metadata.
- **Reference Genome**: *Apis mellifera* HAv3.1.

### 2. Statistical Analysis
- **Primary Test**: Logistic regression (PLINK) with covariates (geographic region, sampling year, Varroa count).
- **Multiple Testing Correction**: Benjamini-Hochberg (BH) FDR procedure on the full set of high-quality SNPs (FR-004).
- **Validation**: LASSO logistic regression for feature selection and predictive modeling.

### 3. Complexity Tracking
- **Genome Size**: ~236 Mb.
- **Expected SNPs**: ~1.5 million high-quality variants after QC.
- **Sample Size**: ~200-300 colonies (Power analysis required).
- **Computational Requirements**: CPU-tractable; no GPU required.
- **Runtime Estimate**: < 6 hours on standard HPC node.

**Note on Candidate-Gene Approach**: The primary GWAS (FR-004) is performed on **all** high-quality SNPs without pre-filtering to ensure comprehensive discovery. A Candidate-Gene filtering step (immune pathway genes) is applied **only** for downstream functional annotation (T032) to manage API load and focus biological interpretation, not for the statistical significance testing.

## Constraints & Assumptions
- **Spec Priority**: The Feature Specification (FR-004, FR-005) governs the statistical methodology. Any conflict with the Plan is resolved in favor of the Spec.
- **Data Integrity**: Raw data is immutable; all processing steps are reproducible.
- **No Fabrication**: All results must be derived from real data or clearly labeled synthetic test data.
- **API Limits**: Ensembl API calls are rate-limited; caching and retries are implemented.

## Deliverables
1. `data/processed/gwas_results_fdr.tsv`: Final association results with FDR-corrected q-values.
2. `data/processed/lasso_auc_report.json`: Predictive performance metrics.
3. `data/processed/annotation_results.tsv`: Gene and pathway annotations for significant SNPs.
4. `docs/report_template.md`: Final report structure with mandatory disclaimers.

## Risk Management
- **Low Power**: If sample size < 80, the pipeline halts with an error (T005).
- **Data Quality**: If Varroa data coverage < 80%, the pipeline halts (T062).
- **API Failures**: Retry logic with exponential backoff for external API calls.

## Revision History
- **v1.0**: Initial plan.
- **v1.1**: Updated to align with Spec FR-004 regarding BH FDR on all SNPs. Removed "Candidate-Gene Pre-filtering" as a justification for reducing GWAS burden. Candidate-Gene logic is now strictly for annotation (T063/T032).