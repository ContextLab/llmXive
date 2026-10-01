# Project Plan: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

## Summary

This project implements a rigorous, reproducible GWAS pipeline to identify SNPs associated with Colony Collapse Disorder (CCD) susceptibility in honeybees (*Apis mellifera*). The pipeline fetches real genomic data from NCBI BioProject PRJNA639195 (CCD) and PRJNA566029 (Healthy), performs alignment, variant calling, quality control, and statistical association analysis, followed by machine learning validation and functional annotation.

**Primary Data Source**: NCBI BioProject PRJNA639195 and PRJNA566029.
**Reference Genome**: Amel_HAv3.1 (Wikipedia: Western honey bee, https://en.wikipedia.org/wiki/Western_honey_bee).
**Key Constraint**: No synthetic data is used for the primary analysis; the pipeline halts if real data fetch fails.

## Phase 0: Setup & Prerequisites

- **Goal**: Initialize project structure andinstall system dependencies.
- **Tasks**:
 - Initialize Python environment (T001-T003).
 - Install system binaries: `dwgsim` (via conda/bioconda), `plink2`, `freebayes`, `samtools`, `bcftools`, `bwa`, `entrez-direct`.
 - Verify tool availability (T013b).

## Phase 1: Foundational Infrastructure (Blocking)

- **Goal**: Establish data validation, power analysis, and schema constraints before data acquisition.
- **Tasks**:
 - **Power Analysis (T005)**: Run power analysis to ensure sufficient sample size (n >= 80). **This must run BEFORE Data Fetch.**
 - **Data Fetch (T012a)**: Download SRA metadata and FASTQ files from NCBI using `entrez-direct`.
 - **Gate**: If sample count < 80, exit with `ERR_SAMPLE_SIZE_INSUFFICIENT`.
 - **Gate**: If SSL verification fails, exit with `ERR_SSL_VERIFICATION_FAILED`.
 - **Schema Validation (T007)**: Define and enforce data schemas for Coloney and SNP entities.
 - **Collinearity Diagnostics (T006)**: Prepare VIF calculation infrastructure.

## Phase 2: User Story 1 - GWAS Pipeline Execution (MVP)

- **Goal**: Produce FDR-corrected association statistics.
- **Workflow**:
 1. **Alignment & Variant Calling (T014)**: Align reads to `Amel_HAv3.1` using `bwa mem`, call variants with `FreeBayes`, filter with `bcftools`. Output: `data/interim/raw_variants.vcf`.
 2. **Format Conversion (T015)**: Convert VCF to PLINK binary format (`.bed`, `.bim`, `.fam`).
 3. **Preprocessing (T016)**: LD pruning (`r² < 0.2`) and covariate encoding.
 4. **Phenotype Harmonization (T062)**: Map CCD diagnosis codes to binary (1/0) and verify Varroa mite data coverage (>80%).
 5. **GWAS Execution (T017)**: Run PLINK logistic regression with mandatory covariates on **ALL** high-quality SNPs. Output: `data/interim/gwas_raw.tsv`.
 6. **FDR Correction (T020)**: Apply Benjamini-Hochberg correction. Output: `data/interim/gwas_fdr.tsv`.
 7. **Merging (T022)**: Merge raw and FDR results into final artifact `data/processed/gwas_results_fdr.tsv`.
 8. **Study Design Documentation (T023)**: Generate `data/processed/study_design.md`.

## Phase 3: User Story 2 - Multiple Testing & Sensitivity

- **Goal**: Validate robustness of associations via threshold sensitivity.
- **Workflow**:
 1. **Threshold Sensitivity (T021)**: Sweep thresholds on `data/processed/gwas_results_fdr.tsv` to count significant SNPs at various q-value cutoffs. Output: `data/processed/threshold_sensitivity.json`.

## Phase 4: User Story 3 - Machine Learning Validation

- **Goal**: Validate GWAS findings using LASSO and PRS.
- **Workflow**:
 1. **LASSO Logistic Regression (T027)**: Train LASSO model with 5-fold cross-validation on an 80/20 train-test split.
 - **Configuration**: `StratifiedKFold(n_splits=5)`, random_state=42.
 - **Metric**: Out-of-sample AUC. Flag if AUC < 0.75.
 - **Output**: `data/processed/lasso_auc_report.json`.
 2. **Phenotype Permutation (T027b)**: Generate null distribution for AUC comparison. Output: `data/processed/phenotype_permutation_null.json`.
 3. **Polygenic Risk Score (PRS) (T028)**: Calculate PRS for each colony using significant SNPs. Output: `data/processed/prs_scores.tsv`.
 4. **Likelihood Ratio Test (T029)**: Test PRS improvement over covariates-only model. Output: `data/processed/prs_lr_test.json`.
 5. **Collinearity Diagnostics (T031)**: Verify VIF for covariates in the ML context. Output: `data/processed/collinearity_report.json`.
 6. **Functional Annotation (T032)**: Map significant SNPs to genes using Ensembl Bees API v104. Output: `data/processed/annotation_results.tsv`.

## Phase 5: Polish & Cross-Cutting

- **Goal**: Final validation, profiling, and documentation.
- **Tasks**:
 - **Profiling (T041)**: CPU profiling of pipeline steps.
 - **Wall-Clock Timer (T089)**: Measure total runtime using `code/07_wall_clock_timer.py`.
 - **Documentation (T033a, T033b, T038)**: Pipeline guide, data dictionary, report template with mandatory disclaimers.
 - **Final Dry-Run (T095)**: Verify end-to-end execution on synthetic data (validation only) to ensure script paths are correct.

## Technical Context

- **Languages**: Python 3.11, Bash.
- **Key Libraries**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `biopython`, `requests`.
- **Genomic Tools**: `plink2`, `freebayes`, `bwa`, `samtools`, `bcftools`, `entrez-direct`.
- **APIs**: Ensembl Bees API v104 (for gene annotation).
- **Data Sources**: NCBI BioProject PRJNA639195, PRJNA566029.

## Constraints & Assumptions

- **No GPU**: The pipeline is CPU-tractable.
- **Real Data Only**: No synthetic data is used for primary analysis.
- **Fail Loudly**: Any data fetch or validation failure halts the pipeline immediately.
- **Candidate-Gene Approach**: Used **only** for annotation (T032), not for GWAS filtering (T017).
- **Power Analysis**: Must pass (n >= 80) before data fetch.
- **Varroa Data**: Required for covariate encoding; <80% coverage halts the pipeline.

## Complexity Tracking

- **Data Volume**: ~760GB raw FASTQ (streamed/processed in chunks).
- **Variant Count**: ~1-2M SNPs (standard for honeybee WGS).
- **Computational Load**: Alignment and GWAS are the heaviest steps; parallelized where possible.

## Risk Mitigation

- **API Rate Limits**: Implement retries for NCBI and Ensembl API calls.
- **Disk Space**: Stream data to avoid full download of massive FASTQ files if possible; use temporary directories for intermediate alignment files.
- **Reproducibility**: Pin all dependencies in `requirements.txt` and `environment.yml`. Use fixed random seeds for ML and synthetic data generation (validation only).

## Deliverables

- **Primary**: `data/processed/gwas_results_fdr.tsv` (FDR-corrected associations).
- **Secondary**: `data/processed/lasso_auc_report.json`, `data/processed/prs_scores.tsv`, `data/processed/annotation_results.tsv`.
- **Documentation**: `data/processed/study_design.md`, `docs/pipeline_execution_guide.md`.