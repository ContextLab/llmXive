# Data Model: Predict Protein‑Protein Interactions from Co‑expression Networks

## Core Entities
| Entity | Attributes | Description |
|--------|------------|-------------|
| **RNASeqSample** | `accession` (str), `species` (str), `raw_counts` (path to TSV), `metadata` (JSON) | One GEO series after download. |
| **Gene** | `gene_id` (str, TAIR or Ensembl), `cpm` (float), `variance` (float), `string_protein_id` (str, optional) | Represents a transcript after filtering. |
| **RawCorrelation** | `gene_id_1` (str), `gene_id_2` (str), `correlation` (float), `p_value` (float), `adjusted_p_value` (float) | Pairwise correlation before identifier mapping; stored in `raw_correlations_<species>.tsv.gz`. |
| **ProteinCorrelation** | `protein_id_1` (str), `protein_id_2` (str), `correlation` (float) | After mapping via `string_protein_id`. |
| **PredictedEdge** | `protein_id_1` (str), `protein_id_2` (str), `correlation` (float) | Row in `predicted_ppi_<species>.tsv`. |
| **EvaluationMetric** | `species` (str), `auroc` (float), `auprc` (float), `baseline_auroc` (float), `baseline_auprc` (float), `baseline_p` (float) | Stored in `evaluation_metrics.json`. |
| **GOEnrichmentRecord** | `go_id` (str), `description` (str), `raw_p` (float), `adj_p` (float), `gene_count` (int) | Row in `go_enrichment_<species>.tsv`. |
| **ThresholdSensitivityRecord** | `threshold` (float), `edge_count` (int), `auroc` (float), `auprc` (float) | Row in `threshold_sensitivity_<species>.tsv`. |
| **PipelineLogEntry** | `timestamp` (ISO‑8601), `level` (str), `message` (str), `schema_version` (str) | JSON‑Line entry in `pipeline.log`. |

## Relationships
- `RNASeqSample` → many `Gene` (genes expressed in the sample).  
- `Gene` ↔ `Gene` → `RawCorrelation` (undirected).  
- `Gene` → `ProteinCorrelation` after mapping via `string_protein_id`.  
- `ProteinCorrelation` filtered by threshold → `PredictedEdge`.  
- `PredictedEdge` set evaluated against STRING high‑confidence edges → `EvaluationMetric`.  
- Genes in `PredictedEdge` serve as background for `GOEnrichmentRecord`.  

## Contracts (YAML schemas) – see `contracts/` directory.

**Note**: Success Criterion SC‑002 mandates that each GO enrichment report contain at least one term with an adjusted p‑value < 0.05; this is reflected in the `GOEnrichmentRecord` usage.

---



