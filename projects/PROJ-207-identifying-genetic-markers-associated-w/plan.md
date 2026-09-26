# Project Plan: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

## Executive Summary

This project implements a Genome-Wide Association Study (GWAS) pipeline to identify Single Nucleotide Polymorphisms (SNPs) associated with susceptibility to Colony Collapse Disorder (CCD) in honeybees (*Apis mellifera*). The pipeline adheres to strict data integrity, statistical rigor, and reproducibility standards defined in the project specification.

## Objectives

1. **Primary Goal**: Identify genetic markers (SNPs) significantly associated with CCD status using a logistic regression GWAS approach.
2. **Statistical Rigor**: Apply Benjamini-Hochberg (BH) False Discovery Rate (FDR) correction to control for multiple testing across the entire set of high-quality SNPs.
3. **Validation**: Validate findings using LASSO logistic regression and Polygenic Risk Scores (PRS).
4. **Annotation**: Map significant SNPs to genes and Gene Ontology (GO) terms using the Ensembl Bees API.
5. **Reproducibility**: Ensure all steps are documented, automated, and reproducible via a defined run-book.

## Scope

### In Scope
- Data acquisition from verified public repositories (Hugging Face/NCBI).
- Data preprocessing (alignment, variant calling, QC, LD pruning).
- GWAS execution (logistic regression with covariates).
- Multiple testing correction (BH FDR).
- Functional annotation of significant SNPs.
- Machine learning validation (LASSO, PRS).
- Generation of final reports and visualizations.

### Out of Scope
- Wet-lab data generation (sequencing, phenotyping).
- Causal inference (findings are associational).
- Real-time monitoring of beehives.

## Architecture & Workflow

The pipeline follows a linear, stage-gated workflow:

1. **Setup & Validation**: Environment setup, dependency installation, and power analysis.
2. **Data Ingestion**: Downloading raw FASTQ/VCF data and phenotype metadata.
3. **Preprocessing**: Alignment, variant calling, VCF to PLINK conversion, LD pruning, and phenotype harmonization.
4. **GWAS Execution**: Running PLINK logistic regression with mandatory covariates.
5. **Statistical Correction**: Applying BH FDR correction and sensitivity analysis.
6. **Validation & Annotation**: LASSO/PRS validation and Ensembl gene mapping.
7. **Reporting**: Generating final artifacts and documentation.

## Data Management

- **Raw Data**: Stored in `data/raw/`. Immutable. Verified via checksums.
- **Interim Data**: Stored in `data/interim/`. Intermediate files (BAM, VCF, PLINK binary).
- **Processed Data**: Stored in `data/processed/`. Final analysis results (GWAS stats, PRS, annotations).
- **Sources**:
 - Genomic Data: `bee_genome_variants` (Hugging Face, derived from NCBI BioProject PRJNA/566029).
 - Reference Genome: `Amel_HAv3.1`.
 - Annotation: Ensembl Bees API.

## Statistical Methodology

- **Association Test**: Logistic Regression (PLINK `--logistic`).
- **Covariates**: Geographic region, sampling year, Varroa mite count.
- **Multiple Testing**: Benjamini-Hochberg FDR (q-value < 0.05 threshold).
- **Power Analysis**: Non-central chi-squared distribution (Target Power > 0.8).
- **Validation**: 5-fold Cross-Validation for LASSO; Likelihood Ratio Test for PRS.

## Complexity Tracking

| Component | Complexity | Mitigation Strategy |
|:--- |:--- |:--- |
| **GWAS Scale** | High (Millions of SNPs) | **Primary GWAS is performed on ALL high-quality SNPs.** Candidate-Gene filtering is applied *only* for downstream functional annotation (T032) to manage API load and focus interpretation, NOT for the statistical test. |
| **API Load** | Medium | Rate limiting and retry logic in annotation scripts. |
| **Compute** | Medium | CPU-tractable. No GPU required. |
| **Data Size** | Medium | Streaming/Chunked processing for large datasets. |

## Risks & Mitigations

- **Risk**: Insufficient statistical power.
 - **Mitigation**: Gate T005 halts pipeline if power < 0.8.
- **Risk**: Missing Varroa data.
 - **Mitigation**: T062 halts pipeline if Varroa coverage < 80%.
- **Risk**: API unavailability.
 - **Mitigation**: Retry logic and fallback to 'UNAVAILABLE' status in annotations.
- **Risk**: Data fabrication.
 - **Mitigation**: Strict enforcement of real data sources; synthetic data only for pipeline validation (T009) with explicit flags.

## Deliverables

1. `data/processed/gwas_results_fdr.tsv`: Final GWAS results with FDR correction.
2. `data/processed/annotation_results.tsv`: Gene mappings for significant SNPs.
3. `data/processed/lasso_auc_report.json`: LASSO validation metrics.
4. `data/processed/prs_scores.tsv`: Polygenic Risk Scores.
5. `docs/report_template.md`: Final report structure with mandatory disclaimers.

## References

- **Spec**: `specs/001-gene-regulation/`
- **Contracts**: `specs/001-gene-regulation/contracts/`
- **API Surface**: `code/` directory modules.