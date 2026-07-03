# Data Model: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

## 1. Entity Relationship Overview

The data model consists of three primary entities:
1.  **Colony**: The biological unit of analysis.
2.  **Genotype**: The set of SNPs for a specific colony.
3.  **AssociationResult**: The output of the GWAS pipeline.

### 1.1 Colony
- **Primary Key**: `colony_id`
- **Attributes**:
  - `health_status`: Binary (0=Healthy, 1=CCD)
  - `geographic_region`: String (Categorical)
  - `sampling_year`: Integer
  - `Varroa_mite_count`: Integer
  - `PC1` ... `PC10`: Float (Principal Components for population structure)
- **Constraints**:
  - `health_status` must be 0 or 1.
  - `Varroa_mite_count` ≥ 0.
  - Missing `Varroa_mite_count` > 10% of total triggers `ERR_VARROA_COVARIATE_MISSING`.
  - If `geographic_region` and `sampling_year` are collinear (VIF > 5), they are excluded from the primary model in favor of PCs.

### 1.2 Genotype (SNP)
- **Composite Key**: (`colony_id`, `SNP_rs_id`)
- **Attributes**:
  - `SNP_ref`: String (A/C/G/T)
  - `SNP_alt`: String (A/C/G/T)
  - `Allele_Freq`: Float (0.0 - 1.0)
  - `Genotype_Call`: Integer (0, 1, 2) representing count of alt allele.
- **Quality Filters**:
  - `QUAL` > 30 (from VCF)
  - `Depth` ≥ 10 (from VCF)

### 1.3 AssociationResult
- **Primary Key**: `SNP_rs_id`
- **Attributes**:
  - `p_value`: Float
  - `bonferroni_q`: Float (Bonferroni-corrected p-value)
  - `fdr_q_value`: Float (BH-corrected q-value, exploratory)
  - `odds_ratio`: Float
  - `significant`: Boolean (bonferroni_q < 0.05)
  - `chromosome`: Integer
  - `position`: Integer

## 2. File Formats & Schemas

The pipeline consumes and produces files in specific formats. Schemas are defined in `contracts/`.

### 2.1 Input: Synthetic VCF (Simulated)
- **Format**: VCF 4.2
- **Structure**: Header lines (`##`) + Header (`#CHROM...`) + Data rows.
- **Validation**: Checked against `contracts/dataset.schema.yaml`.

### 2.2 Input: Phenotype Metadata
- **Format**: CSV
- **Columns**: `colony_id`, `health_status`, `geographic_region`, `sampling_year`, `Varroa_mite_count`.

### 2.3 Output: GWAS Results
- **Format**: TSV (Tab-Separated Values)
- **Columns**: `SNP`, `CHR`, `POS`, `A1`, `A2`, `FREQ`, `P`, `BONFERRONI_P`, `FDR_Q`, `OR`, `SE`.

## 3. Data Flow

1.  **Raw**: `data/raw/synthetic_vcf.vcf`, `data/raw/phenotypes.csv`, `data/raw/simulated_reads.fastq`
2.  **Interim**: `data/interim/plink.bed`, `data/interim/plink.bim`, `data/interim/plink.fam`, `data/interim/pcs.tsv`
3.  **Processed**: `data/processed/gwas_results.tsv`, `data/processed/lasso_metrics.json`, `data/processed/power_analysis.txt`

## 4. Data Quality Rules

- **Missing Data**:
  - If `Varroa_mite_count` is missing for >10% of colonies, halt with `ERR_VARROA_COVARIATE_MISSING`.
  - SNPs with missing genotypes in >5% of samples are pruned.
- **Hardy-Weinberg Equilibrium**: SNPs failing HWE (p < 1e-6) are flagged (optional, but recommended for QC).
- **Minor Allele Frequency (MAF)**: SNPs with MAF < 0.01 are pruned to reduce multiple testing burden.
- **Population Structure**: Top 10 PCs must be computed and included as covariates.
