# Data Model: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

## 1. Overview

This document defines the data structures, schemas, and flow for the project. All artifacts adhere to the **Data Hygiene** principle (checksums, immutable raw data, derived artifacts).

## 2. Entity Definitions

### 2.1 SNP (Variant)
A genomic variant characterized by chromosome, position, reference allele, alternate allele, Minor Allele Frequency (MAF), and Quality Score.
- **Source**: dbSNP (Common)
- **Filter**: MAF > 0.01, Alleles in {A, C, G, T}, Quality Score > 20.

### 2.2 RegulatoryRegion
A genomic interval annotated as a promoter or enhancer.
- **Source**: ENCODE/Roadmap
- **Attributes**: Chromosome, Start, End, Strand, Type (Promoter/Enhancer).

### 2.3 PWM (Position Weight Matrix)
A matrix representing the binding preference of a TF.
- **Source**: JASPAR 2024
- **Attributes**: TF ID, Name, Matrix (4 x L), Log-odds thresholds.

### 2.4 AffinityScore
The log-odds score of a sequence matching a PWM.
- **Attributes**: Sequence, PWM_ID, Score (float), Type (Ref/Alt).

### 2.5 DeltaScore
The difference in affinity between alternate and reference alleles.
- **Attributes**: SNP_ID, PWM_ID, DeltaScore (float).

### 2.6 EnrichmentResult
The statistical result of the GWAS overlap test.
- **Attributes**: PWM_ID, Observed_Overlap, Expected_Overlap, Enrichment_Ratio, P_Value, FDR_Adjusted_P.

## 3. Artifact Flow

1.  **Raw Data**: `data/raw/snp_common.vcf.gz`, `data/raw/pwm_jaspar.txt`, `data/raw/regulatory_regions.bed`.
2.  **Derived Data**:
    - `data/derived/filtered_snps.parquet`: SNPs within regulatory regions, MAF > 1%.
    - `data/derived/scores.parquet`: $\Delta Score$ for all valid SNP-TF pairs.
    - `data/derived/null_distributions.parquet`: Permutation results.
    - `data/derived/enrichment_results.csv`: Final statistical outputs.
3.  **Reports**: `paper/figures/`, `paper/results.md`.

## 4. Schema Definitions

### 4.1 Filtered SNPs Schema
- `snp_id`: string (rsID)
- `chromosome`: string (chr1, chr2...)
- `position`: integer (1-based)
- `ref_allele`: string (A/C/G/T)
- `alt_allele`: string (A/C/G/T)
- `maf`: float (0.01 - 0.5)
- `quality_score`: float (Phred-scaled quality score)
- `regulatory_type`: string (promoter/enhancer)
- `overlap_region_id`: string (BED region ID)

### 4.2 Delta Score Schema
- `snp_id`: string
- `pwm_id`: string
- `delta_score`: float
- `score_ref`: float
- `score_alt`: float
- `context_sequence`: string

### 4.3 Enrichment Schema
- `pwm_id`: string
- `tf_name`: string
- `n_snps_tested`: integer
- `observed_gwas_overlap`: integer
- `expected_gwas_overlap`: float
- `enrichment_ratio`: float
- `p_value_raw`: float
- `p_value_fdr`: float
- `significance`: boolean (True if FDR < 0.05)

## 5. Constraints & Validation

- **Alleles**: Must be A, C, G, T. Any other character causes exclusion.
- **Coordinates**: 1-based, GRCh38.
- **MAF**: Strictly > 0.01.
- **Permutations**: Must be constrained to the same regulatory region type (for baseline comparison).
