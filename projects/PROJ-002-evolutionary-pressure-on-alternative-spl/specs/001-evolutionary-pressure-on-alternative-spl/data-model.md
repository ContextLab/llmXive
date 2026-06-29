# Data Model: Evolutionary Pressure on Alternative Splicing in Primates

## Overview
The pipeline operates on a small set of structured files. The following entities are defined with JSON‑compatible schemas (also provided as YAML contracts).

### 1. RNASeqSample
| Field | Type | Description |
|-------|------|-------------|
| `accession_id` | string | SRA Run accession (e.g., `SRR1234567`). |
| `species` | enum[`human`,`chimpanzee`,`macaque`,`marmoset`] | Species label. |
| `fastq_path` | string (path) | Location of the downloaded FASTQ (paired‑end). |
| `checksum` | string | SHA‑256 of the raw FASTQ archive. |
| `download_date` | string (ISO‑8601) | Timestamp of download. |

### 2. SplicingEvent
| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | SUPPA2 event identifier. |
| `gene_id` | string | Ensembl gene identifier (canonical across species). |
| `species` | enum[`human`,`chimpanzee`,`macaque`,`marmoset`] |
| `delta_psi` | number | ΔPSI between lineage and outgroup (absolute). |
| `fdr` | number | Benjamini‑Hochberg adjusted FDR for the event. |
| `flank_seq` | string | FASTA‑encoded ±500 bp intronic sequence. |
| `phyloP_score` | number | Average phyloP score (may be `null`). |
| `accelerated_flag` | boolean | TRUE if `phyloP_score ≤ -2.0`. |
| `origin_lineage` | enum[`human`,`chimpanzee`,`macaque`,`marmoset`] | Lineage where event is specific. |

### 3. EnrichmentResult
| Field | Type | Description |
|-------|------|-------------|
| `lineage` | enum[`human`,`chimpanzee`,`macaque`,`marmoset`] |
| `odds_ratio` | number |
| `p_raw` | number |
| `p_bonferroni` | number |
| `p_fdr_lineage` | number |
| `p_phylo_adjusted` | number |
| `significant` | boolean | TRUE if final corrected p < 0.05. |

## Relationships
- Each **RNASeqSample** yields one BAM → contributes to many **SplicingEvent** PSI entries (one per sample).  
- **SplicingEvent** rows are filtered to produce `lineage_specific_events.tsv`.  
- **EnrichmentResult** aggregates counts of accelerated vs. non‑accelerated events per lineage.

## Contract Schemas
The YAML files in `contracts/` (see below) encode the above structures and are used by the CI validation suite.

---
