# Data Model: Evolutionary Pressure on Alternative Splicing in Primates

## Core Entities

| Entity | Attributes | Description |
|--------|------------|-------------|
| **RNASeqSample** | `accession_id` (string), `species` (enum: Human, Chimpanzee, Macaque, Marmoset), `fastq_path` (path), `replicate_id` (int) | One SRA run; used for download and downstream processing. |
| **AlignedSample** | `sample_id` (FK → RNASeqSample), `bam_path` (path), `alignment_time_sec` (float), `sha256` (string) | Result of STAR alignment. |
| **SplicingEvent** | `event_id` (string), `gene_id` (string), `species` (enum), `psi_values` (list[float]), `delta_psi` (float), `fdr` (float), `is_lineage_specific` (bool), `is_placeholder` (bool) | One alternative‑splicing event after SUPPA2 quantification. |
| **ControlRegion** | `event_id` (string), `species` (enum), `chrom` (string), `start` (int), `end` (int), `strand` (+/-), `match_criteria` (dict) | A matched non-LSE intronic region used as a control. Linked to `SplicingEvent` via `event_id` in the cohort. |
| **FlankRegion** | `event_id` (FK → SplicingEvent or ControlRegion), `chrom` (string), `start` (int), `end` (int), `strand` (+/-), `sequence` (string), `mean_phyloP` (float or NA), `accelerated_flag` (bool) | ±500 bp intronic region surrounding the event. |
| **EnrichmentResult** | `result_id` (string), `lineage` (enum), `odds_ratio` (float), `p_raw` (float), `p_fdr` (float), `p_empirical` (float), `is_placeholder` (bool) | Output of phylogenetic logistic regression + permutation test. |
| **LifecycleRecord** | `artifact_path` (path), `checksum` (string), `creation_date` (date), `deletion_date` (date, optional), `zenodo_doi` (string, optional) | Tracks long‑term storage and Zenodo deposition. |

## File‑Level Schemas

- `results/psi.tsv` – rows: `gene_id`, `event_id`, `sample_<replicate_id>_psi`.
- `results/lineage_specific_events.tsv` – rows: `lineage`, `event_id`, `gene_id`, `delta_psi`, `fdr`, `is_placeholder`, `count_LSE`, `count_NonLSE`.
- `results/control_regions.tsv` – rows: `event_id`, `species`, `chrom`, `start`, `end`, `strand`, `match_criteria`.
- `results/annotation.csv` – rows: `event_id`, `chrom`, `start`, `end`, `mean_phyloP`, `accelerated_flag`.
- `results/regression_cohort.tsv` – rows: `event_id`, `lineage`, `is_lse` (bool), `mean_phyloP` (float), `accelerated_flag` (bool), `match_criteria`.
- `results/enrichment_results.tsv` – rows: `result_id`, `lineage`, `odds_ratio`, `p_raw`, `p_fdr`, `p_empirical`, `is_placeholder`.
- `results/manhattan.png` – PNG image (≥ 1200 × 800 px).

All files are UTF‑8 encoded, tab‑ or comma‑separated as indicated, and accompanied by a SHA‑256 hash recorded in `artifacts_manifest.json`.

---