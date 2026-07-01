# Data Model: Evolutionary Pressure on Alternative Splicing in Primates

## Overview

This document defines the data structures, schemas, and relationships used throughout the pipeline. It ensures data hygiene (Constitution Principle III) and serves as the contract for the `contracts/` schemas.

## Entity Definitions

### 1. RNASeqSample
Represents a single biological sample (SRA run).

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `accession_id` | string | SRA Accession (e.g., SRR123456) | Input |
| `species` | string | One of: `human`, `chimpanzee`, `macaque`, `marmoset` | Input |
| `fastq_path` | string | Local path to raw FASTQ | Pipeline |
| `checksum` | string | SHA256 hash of FASTQ | Pipeline |
| `replicate_id` | int | Biological replicate index (1..N) | Input |

### 2. SplicingEvent
Represents an alternatively spliced exon/isoform event.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `event_id` | string | Unique identifier (e.g., ENSG001:exon12) | SUPPA2 |
| `gene_id` | string | Ensembl Gene ID | SUPPA2 |
| `species` | string | Species of origin | Input |
| `psi_mean` | float | Mean PSI across replicates | Calculated |
| `psi_std` | float | Standard deviation of PSI | Calculated |
| `delta_psi` | float | Difference in PSI vs. reference lineage | Calculated |
| `fdr` | float | Benjamini-Hochberg corrected p-value | Calculated |
| `is_lineage_specific` | boolean | TRUE if ΔPSI > 0.1 and FDR < 0.05 | Filtered |

### 3. RegulatoryAnnotation
Annotations for the flanking regions of a splicing event.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `event_id` | string | Link to SplicingEvent | Join |
| `flank_seq` | string | ±500bp intronic sequence | bedtools |
| `avg_phylop` | float | Mean phyloP score in flanking region | UCSC/Sim |
| `is_accelerated` | boolean | TRUE if avg_phylop ≤ -2.0 | Calculated |
| `chrom` | string | Chromosome | Input |
| `start` | int | Start coordinate | Input |
| `end` | int | End coordinate | Input |

### 4. EnrichmentResult
Statistical outcome per lineage.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `lineage` | string | Species name | Input |
| `n_lse_accelerated` | int | Count of LSEs with accelerated flag | Count |
| `n_lse_total` | int | Total LSEs | Count |
| `n_non_lse_accelerated` | int | Count of non-LSEs with accelerated flag | Count |
| `n_non_lse_total` | int | Total non-LSEs | Count |
| `odds_ratio` | float | Fisher's OR | Calculated |
| `p_raw` | float | Raw Fisher p-value | Calculated |
| `p_bonferroni` | float | Bonferroni corrected (within lineage) | Calculated |
| `p_phylolm` | float | PGLS adjusted p-value (PGLR in practice) | R/phylolm |
| `p_final` | float | Final FDR corrected (across lineages) | Calculated |
| `is_significant` | boolean | TRUE if p_final < 0.05 | Filtered |

## Data Flow

1.  **Ingestion**: `RNASeqSample` (FASTQ) → `align.py` → `SplicingEvent` (BAM/PSI).
2.  **Annotation**: `SplicingEvent` + `ReferenceGenome` → `annotate.py` → `RegulatoryAnnotation`.
3.  **Analysis**: `RegulatoryAnnotation` + `SpeciesTree` → `stats.py` → `EnrichmentResult`.
4.  **Visualization**: `EnrichmentResult` → `plot.py` → `Manhattan_Plot.png`.

## Constraints & Validation

-   **Species**: Must be one of the 4 allowed values.
-   **PSI**: Must be between 0.0 and 1.0.
-   **PhyloP**: No strict bounds, but `is_accelerated` logic relies on the -2.0 threshold.
-   **Missing Data**: If `avg_phylop` is NA, the event is excluded from enrichment tests (Edge Case handling).