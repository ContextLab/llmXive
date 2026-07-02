# Data Model: Predict Protein‑Protein Interactions from Co‑expression Networks

## Core Entities
| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| **RNASeqSample** | One GEO accession (Series) containing raw count matrix and metadata. | `accession_id`, `species`, `raw_counts_path`, `metadata_path`, `checksum` |
| **Gene** | Biological gene identifier (TAIR or Ensembl). | `gene_id`, `species`, `normalized_expression_vector`, `string_protein_id` |
| **CoExpressionEdge** | Undirected edge between two genes derived from correlation analysis. | `protein_id_1`, `protein_id_2`, `correlation`, `method` (pearson/spearman), `bootstrap_ci_lower` (opt), `bootstrap_ci_upper` (opt) |
| **EvaluationMetric** | Performance metrics for a species. | `species`, `auroc`, `auprc`, `baseline_auroc`, `baseline_auprc`, `baseline_p` |
| **GOEnrichmentRecord** | Result of GO term enrichment for a given species. | `go_id`, `description`, `raw_p`, `adjusted_p`, `gene_count` |

## File Artifacts & Contracts
| File | Format | Purpose | Contract |
|------|--------|---------|----------|
| `raw_correlations_<species>.tsv` | TSV (no header) | Gene‑pair ID1, ID2, Pearson (or Spearman) correlation. Required for unbiased AUROC/AUPRC. | `contracts/raw_correlations.schema.yaml` |
| `predicted_ppi_<species>.tsv` | TSV (header) | Predicted edges after threshold (and optional bootstrap filter). Columns: `protein_id_1`, `protein_id_2`, `correlation`, `method`, optional CI fields. | `contracts/predicted_ppi.schema.yaml` |
| `evaluation_metrics.json` | JSON (object keyed by species) | AUROC, AUPRC, baseline metrics, `baseline_p`. | `contracts/evaluation.schema.yaml` |
| `go_enrichment_<species>.tsv` | TSV (header) | GO term, raw p, adjusted p, gene count. | `contracts/go_enrichment.schema.yaml` |
| `threshold_sensitivity_<species>.tsv` | TSV (header) | Correlation threshold, AUROC, AUPRC for each tested threshold. | `contracts/threshold_sensitivity.schema.yaml` |
| `summary_<species>.txt` | Plain text | Human‑readable summary (edge count, metrics, top GO terms). | No formal schema; validated by presence. |
| `pipeline.log` | JSONL | Timestamped log of each pipeline step. | `contracts/pipeline_log.schema.yaml` |

## Schema Definitions (YAML)
*Full schema files are provided in the `contracts/` directory (see `contracts/predicted_ppi.schema.yaml`, `contracts/evaluation.schema.yaml`, etc.).*  

---



