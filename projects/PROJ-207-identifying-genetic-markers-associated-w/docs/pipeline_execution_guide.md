# GWAS Pipeline Execution Guide

This document provides step-by-step instructions for executing the Honeybee Colony Collapse Disorder (CCD) GWAS analysis pipeline.

## Prerequisites

1. **Python Environment**: Ensure Python 3.11+ is installed.
2. **Dependencies**: Install required packages from `code/requirements.txt`.
3. **API Keys**: Set the following environment variables (see `.env.example`):
 - `NCBI_API_KEY`
 - `ENSEMBL_API_KEY`
4. **External Tools**: Ensure the following are installed and in your `PATH`:
 - `plink2`
 - `freebayes`
 - `bwa`
 - `dwgsim`

## Pipeline Execution Steps

### Step 1: Initialize Project Structure (If not already done)
Run the setup script to create necessary directories:
```bash
cd code
python setup_project.py
```
*This creates: `data/raw/`, `data/processed/`, `data/interim/`, `state/`, `docs/`, `tests/`.*

### Step 2: Data Acquisition
The pipeline supports both real data download and synthetic data generation.

#### Option A: Download Real Data (Recommended)
Fetch data from NCBI BioProject (PRJNA566029) [UNRESOLVED-CLAIM: c_bfefb70c — status=not_enough_info]:
```bash
python code/01_download.py --project PRJNA566029 --output data/raw/
```
*Note: This script validates SSL certificates. If SSL verification fails, the pipeline halts unless a fallback configuration is explicitly set.*

#### Option B: Generate Synthetic Data (For Testing)
If real data is unavailable or for validation purposes:
1. Generate synthetic VCF and Phenotypes:
 ```bash
 python code/00_generate_synthetic_data.py --output data/interim/synthetic.vcf
 ```
2. Simulate FASTQ files from the synthetic VCF:
 ```bash
 python code/00_generate_simulated_fastq.py --vcf data/interim/synthetic.vcf --output data/interim/
 ```

### Step 3: Power Analysis Check
**CRITICAL**: This step must run before any GWAS execution to ensure sample size adequacy.
```bash
python code/utils/power_analysis.py --input data/processed/phenotypes_cleaned.pheno
```
- **Success**: Writes power calculation to `data/processed/power_analysis.txt`.
- **Failure**: Halts pipeline with error code `ERR_SAMPLE_SIZE_INSUFFICIENT` if sample size < 80.

### Step 4: Alignment and Variant Calling
Execute alignment (BWA) and variant calling (FreeBayes):
```bash
bash code/02_align_call.sh --input data/interim/synthetic_R1.fastq data/interim/synthetic_R2.fastq --output data/interim/
```
*Filters applied: QUAL > 30, Depth ≥ 10 [UNRESOLVED-CLAIM: c_f7d092e8 — status=not_enough_info].*

### Step 5: Preprocessing and Phenotype Cleaning
Convert VCF to PLINK format and prepare phenotypes with covariates:
```bash
# Convert VCF to PLINK
python code/utils/vcf_to_plink.py --vcf data/interim/calls.vcf --out data/processed/genotypes

# Clean phenotypes and encode covariates
python code/utils/preprocess_phenotype.py --input data/raw/phenotypes.csv --output data/processed/
```
*Covariates included: Geographic region, Sampling year, Varroa mite count [UNRESOLVED-CLAIM: c_c09d70bd — status=not_enough_info].*

### Step 6: GWAS Execution
Run logistic regression with PLINK:
```bash
bash code/03_gwas.sh --genotype data/processed/genotypes --phenotype data/processed/phenotypes_cleaned.pheno --covariates data/processed/phenotypes_cleaned.cov --out data/interim/gwas_raw
```

### Step 7: Multiple Testing Correction (FDR)
Apply Benjamini-Hochberg correction:
```bash
bash code/04_apply_fdr.sh --input data/interim/gwas_raw.tsv --output data/processed/gwas_results_fdr.tsv
```
*Output includes a mandatory disclaimer: "Findings are associational, not causal..."*

### Step 8: Machine Learning Validation
Validate findings using LASSO and calculate Polygenic Risk Scores (PRS):
```bash
python code/04_ml_validation.py \
 --gwas data/processed/gwas_results_fdr.tsv \
 --phenotype data/processed/phenotypes_cleaned.pheno \
 --genotype data/processed/genotypes \
 --output data/processed/
```
*Outputs:*
- `data/processed/collinearity_report.tsv` (VIF diagnostics)
- `data/processed/ml_validation_report.txt` (AUC, PRS, Likelihood-ratio test)

### Step 9: SNP Annotation
Map significant SNPs to genes using Ensembl:
```bash
python code/05_annotation.py --gwas data/processed/gwas_results_fdr.tsv --output data/processed/annotated_snps.tsv
```

## Output Artifacts

| File Path | Description |
|:--- |:--- |
| `data/processed/power_analysis.txt` | Sample size power calculation result |
| `data/interim/gwas_raw.tsv` | Raw GWAS association statistics |
| `data/processed/gwas_results_fdr.tsv` | FDR-corrected results with significance flags |
| `data/processed/collinearity_report.tsv` | VIF and correlation diagnostics |
| `data/processed/annotated_snps.tsv` | SNP-to-gene mapping with GO terms |
| `data/processed/ml_validation_report.txt` | LASSO AUC and PRS validation metrics |

## Troubleshooting

- **SSL Verification Failed**: Ensure your system CA bundle is up to date or set `SSL_CA_BUNDLE` in `.env`.
- **Sample Size Insufficient**: Ensure at least 80 samples are present in the phenotype data.
- **Missing Covariates**: Verify that `geographic_region`, `sampling_year`, and `varroa_load` columns exist in the input phenotype file.