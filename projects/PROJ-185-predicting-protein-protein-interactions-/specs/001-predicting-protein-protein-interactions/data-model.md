# Data Model: Predict Protein‑Protein Interactions from Co‑expression Networks

## Core Entities
| Entity | Description | Key Attributes | Storage |
|--------|-------------|----------------|---------|
| **RNASeqSample** | Raw GEO series sample | `accession_id` (e.g., GSE12345), `species`, `raw_counts_path`, `metadata` (dict) | `data/raw/<species>/<accession>.tsv` |
| **GeneExpressionMatrix** | Normalized, filtered, batch‑corrected, covariate‑adjusted expression matrix | `genes` (list of gene IDs), `samples` (list of sample IDs), `matrix` (genes × samples float), `norm_method` (`TPM`/`VST`) | `data/processed/<species>/filtered_counts.tsv` |
| **CoExpressionEdge** | Undirected relationship **after mapping to STRING protein IDs** | `protein_id_a` (STRING ID), `protein_id_b` (STRING ID), `correlation` (float, Pearson or Spearman), `bootstrap_ci_lower` (float, optional), `bootstrap_ci_upper` (float, optional), `is_robust` (bool, derived) | `predicted_ppi_<species>.tsv` |
| **StringInteraction** | Reference interaction from STRING | `protein_a`, `protein_b`, `combined_score` (int), `evidence_channels` (list) | Loaded from `string_links.v11.5.txt.gz` (in‑memory) |
| **EvaluationMetric** | Performance summary per species | `species`, `auroc`, `auprc`, `baseline_auroc`, `baseline_auprc`, `baseline_p`, `threshold` | `evaluation_metrics.json` |
| **GOEnrichmentRecord** | GO term enrichment result | `go_id`, `description`, `raw_p`, `adj_p`, `gene_count`, `background_gene_count` | `go_enrichment_<species>.tsv` |
| **SummaryReport** | Human‑readable per‑species summary | `species`, `num_edges`, `auroc`, `auprc`, `baseline_p`, `top_go_terms` (list) | `summary_<species>.txt` |

## File Schemas
- **Raw Correlations** (`raw_correlations_<species>.tsv`)  
  Columns: `gene_a`, `gene_b`, `pearson_r`, `spearman_r` (optional). One row per unordered gene pair.

- **Predicted Edges** (`predicted_ppi_<species>.tsv`) – see `contracts/predicted_edges.schema.yaml`.

- **Evaluation Metrics** (`evaluation_metrics.json`) – see `contracts/evaluation.schema.yaml`.

- **GO Enrichment** (`go_enrichment_<species>.tsv`)  
  Columns: `go_id`, `description`, `raw_p`, `adj_p`, `gene_count`, `background_gene_count`.

- **Threshold Sensitivity** (`threshold_sensitivity_<species>.tsv`)  
  Columns: `threshold`, `auroc`, `auprc`.

## Relationships
- Each **CoExpressionEdge** references two genes that have been mapped to STRING protein IDs; the edge list is the output of the thresholding step.
- **EvaluationMetric** links to the underlying raw correlation scores used for AUROC/AUPRC computation.
- **GOEnrichmentRecord** links to the set of proteins participating in **CoExpressionEdge** (union of all edge endpoints).

All relationships are many‑to‑many and are expressed implicitly via shared identifiers in the TSV/JSON files.

---

