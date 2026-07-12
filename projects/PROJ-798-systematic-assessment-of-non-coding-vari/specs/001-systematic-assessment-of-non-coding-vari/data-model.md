# Data Model: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

## 1. Core Entities

### 1.1 SNP (Variant)
Represents a genomic variant.
- `chromosome` (str): Chromosome identifier (e.g., "chr1").
- `position` (int): 1-based genomic position.
- `reference_allele` (str): Reference nucleotide (A, C, G, T).
- `alternate_allele` (str): Alternate nucleotide (A, C, G, T).
- `maf` (float): Minor Allele Frequency.
- `gc_content` (float): GC content of the local context window.
- `is_regulatory` (bool): True if overlapping a promoter/enhancer.
- `is_gwas_lead` (bool): True if present in GWAS Catalog lead SNPs.
- `ld_block_id` (str): Identifier for the LD block this SNP belongs to (derived from index SNP proximity).
- `stratum_id` (str): Composite ID for GC-content and TSS-distance bin (used for stratified permutation).

### 1.2 PWM (Motif)
Represents a Transcription Factor binding motif.
- `motif_id` (str): Unique identifier (e.g., "MA0001.1").
- `tf_name` (str): Transcription Factor name.
- `matrix` (list of list of float): Position Weight Matrix (4 x L).
- `length` (int): Length of the motif (L).

### 1.3 AffinityScore
Result of scoring a SNP against a PWM.
- `snp_id` (str): Unique identifier for the SNP (e.g., "chr1:12345:A:G").
- `motif_id` (str): The PWM used.
- `score_ref` (float): Log-odds score for reference allele.
- `score_alt` (float): Log-odds score for alternate allele.
- `delta_score` (float): $Score_{alt} - Score_{ref}$.
- `is_large_magnitude` (bool): True if $|\Delta Score| \ge 2$.

### 1.4 EnrichmentResult
Statistical test output per TF.
- `motif_id` (str): The TF tested.
- `ks_statistic` (float): KS test statistic.
- `p_value_observed` (float): Raw p-value from KS test.
- `p_value_corrected` (float): West-Stephens FDR corrected p-value.
- `is_significant` (bool): True if $p_{corrected} < 0.05$.

## 2. Data Flow

1.  **Raw Input**: VCF (dbSNP), BED (ENCODE), Matrix (JASPAR), BED (GWAS).
2.  **Intermediate**:
    - `filtered_snps.parquet`: SNPs with regulatory flags, LD block IDs, and strata.
    - `scores.parquet`: All SNP-TF $\Delta Score$ pairs.
    - `null_distributions.npy`: Permutation results (stratified).
3.  **Final Output**:
    - `results_summary.csv`: Aggregated enrichment results.
    - `report.md`: Human-readable summary.

## 3. Schema Definitions

See `contracts/` for detailed YAML schemas.