# Quickstart: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

## Prerequisites

- GitHub Actions free-tier runner (2 CPU, 7 GB RAM, 6h).
- Python 3.11, Bash 5.0.
- Tools: `bwa`, `freebayes`, `plink2`, `wget`, `curl`, `datasets`.

## Installation

```bash
# Clone repository
git clone <repo-url>
cd projects/PROJ-207-identifying-genetic-markers-associated-w

# Install dependencies
pip install -r requirements.txt

# Verify tools
bwa --version
freebayes --version
plink2 --version
```

## Running the Pipeline

### Step 1: Download Real Data

```bash
bash code/01_download_data.sh
```

- Fetches verified Hugging Face dataset (`bee_genome_variants`) with SSL validation.
- Validates checksums and schema.
- Outputs `data/raw/verified_dataset_info.json`.

### Step 2: Harmonize Phenotypes

```bash
python code/02_harmonize_phenotypes.py
```

- Maps CCD diagnosis codes to CCD Working Group criteria.
- Checks Varroa data coverage (≥90%).
- Outputs `data/interim/phenotypes_cleaned.fam`.

### Step 3: Align and Call Variants

```bash
bash code/03_align_and_call.sh
```

- Aligns reads to `Amel_HAv3.1`.
- Calls variants with FreeBayes.
- Outputs `data/interim/variants.vcf`.

### Step 4: Filter SNPs (Candidate-Gene)

```bash
python code/04_filter_snps.py
```

- Pre-filters SNPs to known immune pathway (a curated set of immune-related SNPs).
- Outputs `data/interim/snp_filtered.bim`.

### Step 5: Collinearity Diagnostics

```bash
python code/05_collinearity_diag.py
```

- Checks VIF/correlation for covariates.
- Outputs `data/processed/collinearity_report.json`.

### Step 6: Power Analysis

```bash
python code/06_power_analysis.py
```

- Calculates power with corrected alpha (significance threshold).
- Halts with `ERR_SAMPLE_SIZE_INSUFFICIENT` if n < 80 or power < 0.8.
- Outputs `data/processed/power_report.json`.

### Step 7: Run GWAS

```bash
bash code/07_gwas_plink.sh
```

- Runs logistic regression in PLINK.
- Outputs `data/interim/gwas_raw.tsv`.

### Step 8: Apply FDR Correction

```bash
python code/08_apply_fdr.py
```

- Applies Benjamini-Hochberg FDR.
- Outputs `data/processed/gwas_results_fdr.tsv`.

### Step 9: Threshold Sensitivity

```bash
python code/09_threshold_sensitivity.py
```

- Sweeps p-value cutoffs across a range of stringent thresholds.
- Outputs `data/processed/sensitivity_report.json`.

### Step 10: LASSO Validation

```bash
python code/10_lasso_validation.py
```

- Trains LASSO on a majority discovery set, validates on a remaining hold-out set.
- Outputs `data/processed/lasso_metrics.json`.

### Step 11: Polygenic Risk Scoring

```bash
python code/11_prs_and_lr_test.py
```

- Computes PRS and likelihood-ratio test.
- Outputs `data/processed/prs_report.json`.

### Step 12: Gene Annotation

```bash
python code/12_annotate_genes.py
```

- Maps SNPs to genes via Ensembl Bees API.
- Outputs `data/processed/gene_annotations.json`.

### Step 13: Format Results

```bash
python code/13_format_results.py
```

- Adds explicit associational disclaimer to all outputs.
- Outputs `data/processed/final_report.md`.

## Expected Outputs

- `data/processed/gwas_results_fdr.tsv`: GWAS results with FDR.
- `data/processed/lasso_metrics.json`: AUC and model performance (on hold-out set).
- `data/processed/prs_report.json`: PRS and likelihood-ratio test.
- `data/processed/final_report.md`: Final report with associational disclaimer.

## Troubleshooting

- **Missing `gwas_raw.tsv`**: Ensure `code/07_gwas_plink.sh` ran successfully.
- **Collinearity Warning**: Check `data/processed/collinearity_report.json` for r² > 0.8.
- **Sample Size Error**: If n < 80, pipeline halts with `ERR_SAMPLE_SIZE_INSUFFICIENT`.
- **Varroa Data Missing**: If <80% Varroa data, pipeline halts with `ERR_VARROA_COVARIATE_MISSING`.

==DISCLAIMER==
All findings in this report are ASSOCIATIONAL, not causal. The study design is observational.
==END_DISCLAIMER==
