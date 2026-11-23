# Project Plan: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

## Summary

This project executes a Genome-Wide Association Study (GWAS) on honeybee genomic data to identify Single Nucleotide Polymorphisms (SNPs) associated with susceptibility to Colony Collapse Disorder (CCD). {{claim:c_90ea1c29}} The pipeline includes rigorous quality control, LD pruning, logistic regression with mandatory covariates, Benjamini-Hochberg FDR correction, and machine learning validation using LASSO.

**Data Source**: NCBI BioProject PRJNA639195 and PRJNA566029 (Primary). No HuggingFace references remain.
**Reference Genome**: *Apis mellifera* Amel_HAv3.1.
**Key Constraint**: The pipeline enforces a minimum sample size (n >= 80) and mandatory Varroa mite covariate coverage (>80%) before proceeding.

## Phase 0: Prerequisites & Environment Setup

**Goal**: Establish the computational environment and verify tool availability.

- Install system dependencies: `bwa`, `freebayes`, `bcftools`, `plink`, `samtools`, `entrez-direct`.
- Install `dwgsim` via conda/bioconda for synthetic validation paths (T013a).
- Verify `dwgsim` availability (T013b).
- Set up Python environment with pinned dependencies (`requirements.txt`).
- Configure API keys for NCBI and Ensembl in `.env`.

## Phase 1: Data Acquisition & Power Analysis (Blocking)

**Goal**: Verify statistical power and fetch real data from NCBI.

1. **Run Power Analysis (T005)**: Execute `code/utils/power_analysis.py` to calculate statistical power based on expected effect sizes.
 - **Gate**: If calculated power < 0.80 or sample size n < 80, the pipeline halts with `ERR_SAMPLE_SIZE_INSUFFICIENT`.
 - **Output**: `data/processed/power_analysis_report.json`.
2. **Data Fetch (T012a)**: Execute `code/01_download.py` to fetch SRA metadata and FASTQ files for PRJNA639195 and PRJNA566029.
 - **Constraint**: Strict SSL verification. No fallback to synthetic data.
 - **Gate**: Verify sample count n >= 80.
 - **Output**: `data/raw/fastq_files/`, `data/processed/ncbi_fetch_log.json`.

## Phase 2: Preprocessing & Variant Calling

**Goal**: Align reads, call variants, and prepare PLINK datasets.

1. **Alignment & Variant Calling (T014)**: Execute `code/02_align_call.sh`.
 - Align FASTQ to *Amel_HAv3.1* using `bwa mem`.
 - Call variants with `freebayes`.
 - Filter to high-quality biallelic SNPs (QUAL > 30, DP >= 10).
 - **Output**: `data/interim/raw_variants.vcf`.
2. **VCF to PLINK Conversion (T015)**: Execute `code/utils/vcf_to_plink.py`.
 - **Output**: `data/interim/bed.{bed,bim,fam}`.
3. **Phenotype Harmonization (T062)**: Execute `code/02_harmonize_phenotypes.py`.
 - Map CCD diagnosis codes to binary (1/0).
 - **Gate**: Verify Varroa mite data coverage >= 80%.
 - **Output**: `data/interim/phenotypes_harmonized.fam`.
4. **LD Pruning (T016)**: Execute `code/utils/preprocess_phenotype.py`.
 - Perform LD pruning (r² < 0.2) for covariate analysis.
 - **Output**: `data/interim/bed_pruned.bim`.

## Phase 3: GWAS Execution & Machine Learning Validation

**Goal**: Execute the primary GWAS, apply FDR, and validate findings with ML.

1. **Primary GWAS (T017)**: Execute `code/03_gwas.sh`.
 - Run PLINK logistic regression with mandatory covariates (Geographic Region, Sampling Year, Varroa Count).
 - **Constraint**: Use ALL high-quality SNPs. Do NOT use the candidate-gene filtered list.
 - **Output**: `data/interim/gwas_raw.tsv`.
2. **FDR Correction (T020)**: Execute `code/utils/fdr_correction.py`.
 - Apply Benjamini-Hochberg procedure to raw p-values.
 - **Output**: `data/interim/gwas_fdr.tsv`.
3. **Result Merging (T022)**: Execute `code/04_apply_fdr.sh`.
 - Merge raw and FDR-corrected results.
 - **Output**: `data/processed/gwas_results_fdr.tsv`.
4. **Machine Learning Validation (T027)**: Execute `code/04_ml_validation.py`.
 - **Method**: LASSO logistic regression with **StratifiedKFold(n_splits=5)** cross-validation.
 - **Data Split**: **80/20** train-test split (stratified by phenotype).
 - **Output**: `data/processed/lasso_auc_report.json`.
5. **PRS & Likelihood Ratio Test (T028, T029)**:
 - Calculate Polygenic Risk Scores (PRS) for significant SNPs.
 - Perform likelihood-ratio test comparing PRS model vs. covariates-only model.
 - **Output**: `data/processed/prs_scores.tsv`, `data/processed/prs_lr_test.json`.

## Phase 4: Sensitivity Analysis & Annotation

**Goal**: Assess robustness and map SNPs to genes.

1. **Threshold Sensitivity (T021)**: Execute `code/utils/threshold_sensitivity.py`.
 - Sweep across significance thresholds to count robust SNPs.
 - **Output**: `data/processed/threshold_sensitivity.json`.
2. **Gene Annotation (T032)**: Execute `code/05_annotation.py`.
 - Map significant SNPs to genes using Ensembl Bees API v104.
 - Handle intergenic regions and API failures gracefully.
 - **Output**: `data/processed/annotation_results.tsv`.

## Phase N: Documentation & Reporting

**Goal**: Compile final reports and ensure reproducibility.

- **Study Design (T023)**: Generate `data/processed/study_design.md`.
- **Collinearity Report (T031)**: Generate `data/processed/collinearity_report.json`.
- **Runtime Verification (T089)**: Execute `code/07_wall_clock_timer.py`.
 - Measure total pipeline runtime.
 - **Output**: `data/processed/runtime_log.json`.
- **Final Validation (T095)**: Dry-run on synthetic data to verify all paths.

## Technical Context

- **Reference Genome**: *Apis mellifera* Amel_HAv3.1.
- **APIs**: Ensembl Bees API v104 for gene mapping.
- **Statistical Methods**: Logistic Regression (PLINK), Benjamini-Hochberg FDR, LASSO (scikit-learn), Likelihood Ratio Test.
- **Hardware**: CPU-tractable. No GPU required.

## Complexity Tracking

| Component | Complexity | Notes |
|:--- |:--- |:--- |
| Data Fetch | High | Network I/O, SSL verification |
| Alignment | High | CPU intensive (BWA) |
| GWAS | Medium | PLINK optimization |
| ML Validation | Medium | LASSO CV on CPU |
| Annotation | Medium | API rate limiting |

## Critical Methodological Adjustments

*None. The pipeline adheres strictly to the Spec (FR-004) requiring GWAS on all SNPs. Candidate-gene filtering is used only for annotation (T063), not the primary statistical test.*