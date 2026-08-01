# Data Model: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

## Overview

This document defines the data structures, schemas, and relationships for the GWAS pipeline. All data flows through `data/` with strict versioning and checksumming.

## Entities

### Colony

- **Attributes**:
  - `colony_id` (string): Unique identifier.
  - `health_status` (binary): CCD=1, Healthy=0.
  - `geographic_region` (string): e.g., "California", "Florida".
  - `sampling_year` (integer): e.g., 2020, 2021.
  - `varroa_mite_count` (float): Mite count per colony.
- **Source**: Hugging Face dataset `bee_genome_variants` (v1.0).
- **Validation**: All fields required; `health_status` must be 0 or 1.

### SNP

- **Attributes**:
  - `rs_id` (string): rs identifier or "chr:pos:ref:alt".
  - `chromosome` (string): e.g., "chr1", "chr2".
  - `position` (integer): Genomic position.
  - `reference_allele` (string): e.g., "A", "T".
  - `alternate_allele` (string): e.g., "G", "C".
  - `allele_frequency` (float): Frequency of alternate allele.
  - `p_value` (float): GWAS p-value.
  - `q_value` (float): FDR-corrected q-value.
  - `odds_ratio` (float): Odds ratio from logistic regression.
- **Source**: PLINK output (`data/processed/gwas_results.tsv`).
- **Validation**: All fields required; `p_value` and `q_value` in [0, 1].

### Colony_Pheno

- **Attributes**:
  - `colony_id` (string): Foreign key to `Colony`.
  - `covariates` (dict): {`region`: str, `year`: int, `varroa`: float}.
- **Source**: Derived from `Colony` and metadata.
- **Validation**: Consistency check with `Colony` table.

## File Schema

### `data/raw/colony_metadata.csv`

| Column | Type | Description |
|--------|------|-------------|
| colony_id | string | Unique ID |
| health_status | int | 0=Healthy, 1=CCD |
| geographic_region | string | Region name |
| sampling_year | int | Year of sampling |
| varroa_mite_count | float | Mite count |

### `data/interim/gwas_raw.tsv`

| Column | Type | Description |
|--------|------|-------------|
| SNP | string | rs_id or chr:pos:ref:alt |
| CHR | int | Chromosome number |
| BP | int | Base pair position |
| A1 | string | Alternate allele |
| TEST | string | Test type (ADD) |
| OR | float | Odds ratio |
| SE | float | Standard error |
| P | float | P-value |

### `data/processed/gwas_results_fdr.tsv`

| Column | Type | Description |
|--------|------|-------------|
| SNP | string | rs_id |
| CHR | int | Chromosome |
| BP | int | Position |
| A1 | string | Alternate allele |
| P | float | Raw p-value |
| Q | float | FDR-corrected q-value |
| OR | float | Odds ratio |
| SIGNIFICANT | bool | q < 0.05 |

## Relationships

- `Colony` → `Colony_Pheno`: One-to-one (each colony has one phenotype record).
- `Colony` → `SNP`: Many-to-many (each colony has many SNPs; each SNP is in many colonies).
- `SNP` → `gwas_results_fdr`: One-to-one (each SNP has one GWAS result).

## Data Flow

1. **Download**: `code/01_download_data.sh` fetches real HF dataset with SSL validation.
2. **Harmonize**: `code/02_harmonize_phenotypes.py` maps CCD criteria and checks Varroa coverage.
3. **Align & Call**: `code/03_align_and_call.sh` produces VCF.
4. **Filter**: `code/04_filter_snps.py` pre-filters to immune pathway (Candidate-Gene).
5. **Collinearity**: `code/05_collinearity_diag.py` checks covariates.
6. **Power**: `code/06_power_analysis.py` calculates power with corrected alpha.
7. **GWAS**: `code/07_gwas_plink.sh` produces `gwas_raw.tsv`.
8. **FDR**: `code/08_apply_fdr.py` produces `gwas_results_fdr.tsv`.
9. **Sensitivity**: `code/09_threshold_sensitivity.py` sweeps p-values.
10. **LASSO**: `code/10_lasso_validation.py` trains on [deferred] and validates on [deferred].
11. **PRS**: `code/11_prs_and_lr_test.py` computes PRS and likelihood-ratio test.
12. **Annotation**: `code/12_annotate_genes.py` produces gene annotations.
13. **Format**: `code/13_format_results.py` adds associational disclaimer.
