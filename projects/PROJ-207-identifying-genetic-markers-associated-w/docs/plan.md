# Research Plan: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

## Summary

This project executes a Genome-Wide Association Study (GWAS) on honeybee genomic data to identify Single Nucleotide Polymorphisms (SNPs) associated with susceptibility to Colony Collapse Disorder (CCD). The analysis uses real data sourced from NCBI BioProject PRJNA639195 (CCD-affected colonies) and PRJNA566029 (Healthy colonies). [UNRESOLVED-CLAIM: c_3b218d4c — status=refuted] The pipeline includes data download, alignment, variant calling, quality control, GWAS execution with covariate adjustment, Benjamini-Hochberg FDR correction, threshold sensitivity analysis, and machine learning validation (LASSO) with Polygenic Risk Score (PRS) calculation.

## Data Sources

- **Primary Source**: NCBI BioProject PRJNA639195 (CCD) and PRJNA566029 (Healthy).
- **Reference Genome**: *Apis mellifera* Amel_HAv3.1.
- **Annotation**: Ensembl Bees API v104.

## Phase 1: Setup & Prerequisites (Blocking)

**Goal**: Establish the computational environment and verify statistical power before data acquisition.

1. **Power Analysis**: Run `code/utils/power_analysis.py` to verify sample size sufficiency (n >= 80) and calculate statistical power. **HALT** if power is insufficient.
2. **Data Fetch**: Download raw FASTQ data from NCBI BioProjects PRJNA639195 and PRJNA566029 using `code/01_download.py`.
 - Validate SSL certificates.
 - Verify sample count (n >= 80) before proceeding.
3. **Infrastructure**: Install required system binaries (dwgsim, bwa, freebayes, samtools, plink2) and Python dependencies.

## Phase 2: Data Processing & Variant Calling

**Goal**: Convert raw reads into a high-quality VCF file suitable for GWAS.

1. **Alignment**: Align FASTQ reads to the Amel_HAv3.1 reference using `bwa mem`.
2. **Variant Calling**: Call variants using `FreeBayes`.
3. **Filtering**: Filter variants for quality (QUAL > 30, depth >= 10) and biallelic SNPs using `bcftools`.
4. **Format Conversion**: Convert VCF to PLINK binary format (bed/bim/fam) using `code/utils/vcf_to_plink.py`.
5. **Phenotype Harmonization**: Map CCD diagnosis codes and encode covariates (geographic region, sampling year, Varroa count) using `code/02_harmonize_phenotypes.py`. Ensure Varroa data coverage is >= 80%.
6. **LD Pruning**: Perform LD pruning (r² < 0.2) using PLINK to reduce multicollinearity for covariate diagnostics.

## Phase 3: GWAS Execution & Correction (US1)

**Goal**: Identify significant SNP associations and correct for multiple testing.

1. **GWAS Run**: Execute logistic regression using PLINK (`code/03_gwas.sh`) with mandatory covariates. Output raw statistics to `data/interim/gwas_raw.tsv`.
 - **Note**: This step uses **ALL** high-quality SNPs. Do not use the candidate-gene filtered list for the primary statistical test.
2. **Collinearity Diagnostics**: Calculate VIF for covariates to ensure model stability (`code/05_collinearity_diag.py`).
3. **FDR Correction**: Apply Benjamini-Hochberg correction to raw p-values using `code/utils/fdr_correction.py`.
4. **Result Merging**: Merge raw and FDR-corrected results into `data/processed/gwas_results_fdr.tsv` (`code/04_apply_fdr.sh`).

## Phase 4: Sensitivity Analysis (US2)

**Goal**: Assess robustness of findings across different significance thresholds.

1. **Threshold Sweep**: Run `code/utils/threshold_sensitivity.py` to count significant SNPs across a range of q-value thresholds.
2. **Output**: Generate `data/processed/threshold_sensitivity.json`.

## Phase 5: Machine Learning Validation (US3)

**Goal**: Validate GWAS findings using predictive modeling.

1. **LASSO Regression**: Train a LASSO logistic regression model with 5-fold cross-validation (StratifiedKFold) on an 80/20 train/test split.
 - **Input**: GWAS results and phenotypes.
 - **Output**: AUC score in `data/processed/lasso_auc_report.json`.
2. **Null Distribution**: Perform phenotype permutation to generate a null distribution for AUC comparison.
3. **Polygenic Risk Score (PRS)**: Calculate PRS for each colony based on significant SNPs.
4. **Likelihood Ratio Test**: Compare PRS model against a covariates-only model.
5. **Annotation**: Map significant SNPs to genes using Ensembl Bees API v104 (`code/05_annotation.py`).

## Phase 6: Documentation & Reporting

**Goal**: Synthesize results and ensure reproducibility.

1. **Study Design**: Document study design, associational nature, and covariate handling (`code/05_document_study_design.py`).
2. **Pipeline Execution**: Generate a runtime log using `code/07_wall_clock_timer.py`.
3. **Final Report**: Compile results into `docs/report.md` with mandatory disclaimers.

## Technical Context

- **Language**: Python 3.11
- **Key Libraries**: pandas, numpy, scikit-learn, statsmodels, biopython, requests.
- **Bioinformatics Tools**: bwa, freebayes, bcftools, plink2, samtools, entrez-direct.
- **APIs**: Ensembl Bees API v104, NCBI E-utilities.

## Critical Methodological Notes

- **Sample Size**: The study requires a minimum of 80 colonies to achieve adequate statistical power. [UNRESOLVED-CLAIM: c_6fb56086 — status=not_enough_info]
- **Covariates**: Geographic region, sampling year, and Varroa mite count are mandatory covariates to control for confounding.
- **Candidate-Gene Approach**: The immune pathway SNP list is used **only** for annotation purposes (T063) and is **excluded** from the primary GWAS run (T017) to avoid bias.
- **Data Integrity**: Raw data is immutable. All processing steps are deterministic and logged.

## Complexity Tracking

| Component | Complexity | Mitigation |
|:--- |:--- |:--- |
| Data Volume | High (~760GB raw) | Streaming processing, chunked analysis |
| Compute | High (Alignment/GWAS) | Parallel processing, optimized C tools |
| Statistical | Medium | Standardized PLINK/scikit-learn pipelines |
| Annotation | Medium | Caching API responses, retry logic |

## Assumptions

- No GPU or CUDA accelerators are required; the pipeline is CPU-tractable.
- NCBI BioProject data is accessible and complete for the specified projects.
- Ensembl Bees API v104 is available for gene annotation.
- The honeybee reference genome (Amel_HAv3.1) is correctly installed in the environment.