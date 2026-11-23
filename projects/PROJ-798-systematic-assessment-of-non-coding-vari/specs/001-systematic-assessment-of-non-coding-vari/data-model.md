# Data Model: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

## Core Entities

### SNP (Variant)
| Field | Type | Description |
|-------|------|-------------|
| `chromosome` | `string` | e.g., `"chr1"` |
| `position` | `integer` | 1‑based coordinate |
| `reference_allele` | `string` (A/C/G/T) | Reference base |
| `alternate_allele` | `string` (A/C/G/T) | Alternate base |
| `maf` | `float` (0‑1) | Minor allele frequency |
| `gc_content` | `float` (0‑1) | GC fraction of the context window |
| `is_regulatory` | `boolean` | Overlaps ENCODE/Roadmap promoter/enhancer |
| `is_gwas_lead` | `boolean` | Present in GWAS Catalog |
| `ld_block_id` | `string` | Identifier of LD block (preserves correlation) |
| `stratum_id` | `string` | Composite ID for GC‑content, TSS‑distance, and optional DNase‑I hypersensitivity bins (used for stratified permutation) |
| `delta_score` | `float` | Difference in binding affinity (Alt - Ref) |
| `is_large_magnitude` | `boolean` | True if absolute `delta_score` ≥ 2 bits |

### PWM (Motif)
| Field | Type | Description |
|-------|------|-------------|
| `motif_id` | `string` | JASPAR ID, e.g. `"MA0139.1"` |
| `tf_name` | `string` | Human transcription factor name |
| `matrix` | `list[list[float]]` | 4 × L position weight matrix (rows A,C,G,T) |
| `length` | `integer` | Motif length L |
| `information_content` | `float` | Average bits per position (used for filtering) |

### AffinityScore (SNP‑TF pair)
| Field | Type | Description |
|-------|------|-------------|
| `snp_id` | `string` | `"chr1:12345:A:G"` |
| `motif_id` | `string` | PWM identifier |
| `score_ref` | `float` | Log‑odds for reference allele |
| `score_alt` | `float` | Log‑odds for alternate allele |
| `delta_score` | `float` | `score_alt − score_ref` |
| `is_large_magnitude` | `boolean` | `|delta_score| ≥ 2` bits |

### EnrichmentResult (per TF)
| Field | Type | Description |
|-------|------|-------------|
| `motif_id` | `string` | PWM identifier |
| `tf_name` | `string` | Transcription factor name |
| `ks_statistic` | `float` | KS test statistic |
| `p_value_ks_observed` | `float` | Raw KS p‑value |
| `p_value_ks_corrected` | `float` | West‑Stephens max‑T FDR‑adjusted p‑value |
| `tail_proportion_observed` | `float` | Fraction of SNPs with `|Δ Score| ≥ 2` bits |
| `tail_p_value` | `float` | Fisher's exact p‑value for tail enrichment |
| `is_significant_ks` | `boolean` | `p_value_ks_corrected < 0.05` |
| `is_significant_tail` | `boolean` | `tail_p_value < 0.05` |
| `permutation_count` | `integer` | Fixed at 500 (see plan) |
| `n_snps_tested` | `integer` | Number of SNP‑TF pairs scored for this TF |

## Data Flow
1. **Raw Input** – VCF (dbSNP), BED (ENCODE), PWM files (JASPAR), GWAS BED.  
2. **Intermediate** – `filtered_snps.parquet`, `control_set.parquet`, `scores.parquet`, `null_distributions.npy`.  
3. **Final Output** – `results_summary.csv`, `report.md`.

## Schema Definitions
All schemas are located in `contracts/` and are validated during the CI run.

---