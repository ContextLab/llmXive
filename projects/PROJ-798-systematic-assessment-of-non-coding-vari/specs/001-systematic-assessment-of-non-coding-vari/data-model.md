# Data Model: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

## 1. Entities & Relationships

### 1.1 SNP (Variant)
A single nucleotide polymorphism.
- **Attributes**: `chrom` (str), `pos` (int), `ref` (str), `alt` (str), `maf` (float), `rs_id` (str).
- **Constraints**: `ref` and `alt` must be in {A, C, G, T}. `maf` > 0.01.

### 1.2 RegulatoryRegion
A genomic interval annotated as a regulatory element.
- **Attributes**: `chrom` (str), `start` (int), `end` (int), `type` (str: "promoter" | "enhancer"), `source` (str).
- **Constraints**: `start` < `end`.

### 1.3 PWM (Motif)
A Position Weight Matrix for a TF.
- **Attributes**: `tf_id` (str), `matrix` (2D array: 4xL), `background_freq` (dict).
- **Constraints**: Matrix columns sum to 1.0 (probabilities).

### 1.4 ScoreRecord
The result of scoring a SNP against a PWM.
- **Attributes**: `snp_id`, `tf_id`, `score_ref` (float), `score_alt` (float), `delta_score` (float), `context_seq_ref` (str), `context_seq_alt` (str), `window_size` (int).
- **Note**: `window_size` is now dynamic (PWM-length dependent).

### 1.5 EnrichmentResult
The result of the statistical test.
- **Attributes**: `tf_id`, `observed_overlap` (int), `expected_overlap` (float), `p_value` (float), `fdr_q_value` (float), `enrichment_ratio` (float), `n_snps_tested` (int), `n_high_impact` (int), `significant` (bool).

## 2. Data Flow

1. **Raw Data** (`data/raw/`) -> **Filtered SNPs** (`data/derived/filtered_snps.parquet`)
2. **Filtered SNPs** + **PWMs** -> **ScoreRecords** (`data/derived/scores.parquet`)
3. **ScoreRecords** -> **Null Distribution** (in-memory) -> **EnrichmentResult** (`data/derived/enrichment_results.parquet`)

## 3. Storage Format

- **Parquet**: Used for intermediate tables (filtered SNPs, scores) for efficient columnar access.
- **JSON**: Used for configuration and checksums.
- **FASTA**: Used for genomic context sequences (memory-mapped).