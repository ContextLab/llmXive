# Data Dictionary: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

This document defines all data artifacts, schemas, and formats used throughout the GWAS pipeline.
It serves as the canonical reference for data structures, ensuring consistency across ingestion,
processing, analysis, and reporting stages.

---

## 1. Directory Structure

| Directory | Purpose | Immutability |
|-----------|---------|--------------|
| `data/raw/` | Raw data fetched from external sources (NCBI, Ensembl). | **Immutable** once checksum verified. |
| `data/interim/` | Intermediate files (FASTQ, BAM, unpruned VCF). | Mutable during pipeline execution. |
| `data/processed/` | Cleaned, normalized, and analysis-ready datasets. | Immutable after generation. |
| `state/` | Pipeline execution state and logs. | Mutable. |

---

## 2. Raw Data Artifacts

### 2.1 Raw Genomic Sequencing Data (FASTQ)
*Source*: NCBI BioProject PRJNA566029 (or synthetic fallback).
*Files*: `data/raw/*.fastq` or `data/interim/synthetic_*.fastq`

| Field | Type | Description |
|-------|------|-------------|
| Read ID | String | Sequencer read identifier. |
| Sequence | String | Nucleotide sequence (A, C, G, T, N). |
| Quality | String | Phred quality scores (ASCII encoded). |
| Pair | Int | 1 (R1) or 2 (R2) for paired-end reads. |

### 2.2 Raw Variant Calls (VCF)
*Source*: FreeBayes output or NCBI.
*File*: `data/interim/raw_variants.vcf`

| Column | Type | Description |
|--------|------|-------------|
| CHROM | String | Chromosome name. |
| POS | Int | 1-based position. |
| ID | String | Variant identifier (rsID or.). |
| REF | String | Reference allele. |
| ALT | String | Alternate allele(s). |
| QUAL | Float | Phred-scaled quality score. |
| FILTER | String | Filter status (PASS or reason). |
| INFO | String | Semicolon-separated key=value pairs. |
| FORMAT | String | Genotype format definition. |
| Samples | String | Genotype data per sample. |

---

## 3. Processed Data Artifacts

### 3.1 PLINK Binary Files
*Source*: `code/utils/vcf_to_plink.py` (T015).
*Files*: `data/processed/genotypes.{bed,bim,fam}`

| File | Description |
|------|-------------|
| `.bed` | Binary genotype matrix (0, 1, 2 for allele counts). |
| `.bim` | Variant map: Chromosome, rsID, Genetic distance, Position, Allele 1, Allele 2. |
| `.fam` | Sample map: Family ID, Individual ID, Paternal ID, Maternal ID, Sex, Phenotype. |

### 3.2 Cleaned Phenotypes
*Source*: `code/utils/preprocess_phenotype.py` (T016).
*File*: `data/processed/phenotypes_cleaned.{fam,pheno}`

| Column | Name | Type | Description |
|--------|------|------|-------------|
| 1 | Family ID | String | Hive identifier. |
| 2 | Individual ID | String | Sample identifier. |
| 3 | Paternal ID | 0 | Unused. |
| 4 | Maternal ID | 0 | Unused. |
| 5 | Sex | Int | 1=Male, 2=Female, 0=Unknown. |
| 6 | Phenotype | Int | 1=Control, 2=CCD Case, -9=Missing. |
| Cov1 | Geo_Region | String | Geographic region code. |
| Cov2 | Year | Int | Sampling year. |
| Cov3 | Varroa_Load | Float | Mite count per sample. |

### 3.3 GWAS Raw Results
*Source*: `code/03_gwas.sh` (T017).
*File*: `data/interim/gwas_raw.tsv`

| Column | Name | Type | Description |
|--------|------|------|-------------|
| 1 | CHR | Int | Chromosome. |
| 2 | SNP | String | Variant ID. |
| 3 | BP | Int | Base pair position. |
| 4 | A1 | String | Test allele. |
| 5 | TEST | String | Test name (e.g., LOGISTIC). |
| 6 | NMISS | Int | Number of non-missing observations. |
| 7 | BETA | Float | Log-odds ratio. |
| 8 | SE | Float | Standard error. |
| 9 | L95 | Float | Lower 95% CI. |
| 10 | U95 | Float | Upper 95% CI. |
| 11 | STAT | Float | Wald statistic. |
| 12 | P | Float | P-value. |

### 3.4 FDR-Corrected Results
*Source*: `code/04_apply_fdr.sh` (T022).
*File*: `data/processed/gwas_results_fdr.tsv`

| Column | Name | Type | Description |
|--------|------|------|-------------|
| All above | | | |
| 13 | Q_VALUE | Float | Benjamini-Hochberg adjusted p-value. |
| 14 | SIGNIFICANT | Bool | True if Q_VALUE < 0.05. |
| *Header* | Disclaimer | String | "Findings are associational, not causal..." |

### 3.5 Threshold Sensitivity Report
*Source*: `code/utils/threshold_sensitivity.py` (T021).
*File*: `data/processed/threshold_sensitivity_report.tsv`

| Column | Name | Type | Description |
|--------|------|------|-------------|
| 1 | Threshold | Float | P-value cutoff used. |
| 2 | Count | Int | Number of SNPs passing cutoff. |
| 3 | Q_Value_Median | Float | Median q-value of passing SNPs. |

### 3.6 Annotated SNPs
*Source*: `code/05_annotation.py` (T032).
*File*: `data/processed/annotated_snps.tsv`

| Column | Name | Type | Description |
|--------|------|------|-------------|
| 1 | rs_id | String | Variant identifier. |
| 2 | gene_symbol | String | Nearest gene symbol (Ensembl). |
| 3 | go_terms | String | Gene Ontology terms (semicolon-separated). |
| 4 | pathway | String | KEGG/Reactome pathway name. |

### 3.7 Collinearity Report
*Source*: `code/04_ml_validation.py` (T031).
*File*: `data/processed/collinearity_report.tsv`

| Column | Name | Type | Description |
|--------|------|------|-------------|
| 1 | Variable | String | Covariate name. |
| 2 | VIF | Float | Variance Inflation Factor. |
| 3 | Tolerance | Float | 1/VIF. |
| 4 | Flag | String | "HIGH" if r² > 0.8 with another covariate. |

---

## 4. Schema Validation Rules

All data ingestion points enforce validation against the schemas defined in:
- `code/utils/validators/colony_schema.py`
- `code/utils/validators/snp_schema.py`

### 4.1 Colony Schema (`ColonySchema`)
- `colony_id`: Unique string, not null.
- `status`: Enum ['healthy', 'ccd', 'unknown'].
- `geo_region`: String, not null.
- `sampling_year`: Int, range [2000, 2024].
- `varroa_load`: Float, >= 0.

### 4.2 SNP Schema (`SnpSchema`)
- `chromosome`: String, valid format (1-32 or 'X').
- `position`: Int, > 0.
- `ref_allele`: String, length 1 (or indel).
- `alt_allele`: String, length 1 (or indel).
- `quality`: Float, > 30 (hard filter).

---

## 5. Execution Artifacts

### 5.1 Power Analysis Output
*File*: `data/processed/power_analysis.txt`
*Format*: Single line: `Power: X.XX`
*Constraint*: If sample size < 80, pipeline halts with `ERR_SAMPLE_SIZE_INSUFFICIENT`.

### 5.2 Checksum Manifest
*File*: `data/raw/.checksums.txt`
*Format*: `SHA256 filename`
*Usage*: Verified by `code/utils/checksum_verify.py` before processing.

---

## 6. Notes

- **Immutability**: Files in `data/raw/` are never overwritten. If re-downloading is required, the filename must change or the directory must be cleared manually.
- **Missing Data**: Represented by `-9` in PLINK phenotype files.
- **Significance**: Statistical significance is determined by Q-Value < 0.05 after Benjamini-Hochberg correction.