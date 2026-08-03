# Data Model: Predict Protein‑Protein Interactions from Co‑expression Networks

## Core Entities
| Entity | Attributes | Description |
|--------|------------|-------------|
| **RNASeqSample** | `sample_accession`, `geo_series_accession`, `metadata`, `raw_counts_path` | One GEO GSM record. |
| **GeneExpressionMatrix** | `species`, `gene_ids`, `sample_ids`, `normalized_matrix_path` | VST‑ or TPM‑normalized expression matrix after filtering. |
| **Gene** | `gene_id` (TAIR or Ensembl), `protein_id` (STRING), `variance` | Holds mapping to STRING protein IDs. |
| **RawCorrelation** | `gene_id_1`, `gene_id_2`, `correlation`, `p_value`, `adjusted_p_value` | Pairwise correlation before ID mapping; stored gzipped. |
| **ProteinCorrelation** | `protein_id_1`, `protein_id_2`, `correlation` | Correlation after gene‑to‑protein mapping. |
| **PredictedEdge** | `protein_id_1`, `protein_id_2`, `correlation` | Edge retained after thresholding (FR‑011). |
| **EvaluationMetric** | `species`, `auroc`, `auprc`, `baseline_auroc`, `baseline_auprc`, `baseline_p` | JSON representation (`evaluation_metrics.json`). |
| **GOEnrichmentRecord** | `go_id`, `description`, `raw_p`, `adjusted_p`, `gene_count` | One row of `go_enrichment_<species>.tsv`. |
| **ThresholdSensitivityRecord** | `threshold`, `num_edges`, `auroc`, `auprc` | Row of `threshold_sensitivity_<species>.tsv`. |
| **MasterResults** | `species`, `edge_count`, `auroc`, `auprc`, `baseline_p`, `top_go_terms` | Aggregated per‑species summary stored in `master_results.json`; serves as the Single Source of Truth for the project. |

## Relationships
- **RNASeqSample** → belongs to → **GeneExpressionMatrix** (many‑to‑one per species).  
- **GeneExpressionMatrix** → contains → **Gene** (≤ 5 000 retained).  
- **Gene** ↔ maps to ↔ **ProteinCorrelation** via `protein_id`.  
- **RawCorrelation** → filtered → **ProteinCorrelation** → **PredictedEdge** (threshold).  
- **PredictedEdge** → defines gene set for → **GOEnrichmentRecord**.  
- **EvaluationMetric** consumes **RawCorrelation**, **PredictedEdge**, and STRING reference set.  
- **MasterResults** aggregates the above per species for reporting.

All files are TSV/JSON/GZ formats and validated against contracts in `contracts/`.
