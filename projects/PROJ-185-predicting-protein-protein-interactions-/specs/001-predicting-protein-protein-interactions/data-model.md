# Data Model: Predict Protein‑Protein Interactions from Co‑expression Networks

## Core Entities

| Entity | Attributes | Description |
|--------|------------|-------------|
| **RNASeqSample** | `accession` (string), `species` (string), `raw_counts_path` (string), `metadata_path` (string) | Represents a GEO series; raw count matrix stored as TSV. |
| **Gene** | `gene_id` (string, TAIR or Ensembl), `species` (string), `norm_expression` (array[float]), `mapped_protein_id` (string, optional) | Normalized expression vector after VST/TPM; may be unmapped. |
| **Protein** | `protein_id` (string, STRING ID), `gene_id` (string) | One‑to‑one mapping from Gene (when available). |
| **RawCorrelation** | `gene_id_1` (string), `gene_id_2` (string), `correlation` (float), `p_value` (float), `adj_p_value` (float) | Correlation computed before identifier mapping; stored in `raw_correlations_*.tsv.gz`. |
| **ProteinCorrelation** | `protein_id_1` (string), `protein_id_2` (string), `correlation` (float) | After successful mapping; used for edge selection. |
| **PredictedEdge** | `protein_id_1` (string), `protein_id_2` (string), `correlation` (float) | Written to `predicted_ppi_<species>.tsv`. |
| **EvaluationMetric** | `species` (string), `auroc` (float), `auprc` (float), `baseline_auroc` (float), `baseline_auprc` (float), `baseline_p` (float) | Stored in `evaluation_metrics.json`. |
| **GOEnrichmentRecord** | `go_id` (string), `description` (string), `p_value` (float), `adj_p_value` (float), `gene_count` (int) | One row per GO term in `go_enrichment_<species>.tsv`. |
| **ThresholdSensitivityRecord** | `threshold` (float), `edge_count` (int), `auroc` (float), `auprc` (float) | Rows of `threshold_sensitivity_<species>.tsv`. |
| **PipelineLogEntry** | `timestamp` (ISO‑8601 string), `level` (enum), `message` (string), `schema_version` (string) | JSON‑Line entry in `pipeline.log`. |

## Relationships
- **RNASeqSample** → many **Gene** (genes expressed in the sample).  
- **Gene** ↔ **Protein** (0‑1 mapping).  
- **RawCorrelation** links two **Gene** records; after mapping, becomes **ProteinCorrelation** linking two **Protein** records.  
- **PredictedEdge** is a filtered subset of **ProteinCorrelation**.  
- **EvaluationMetric** aggregates over all **PredictedEdge** and the STRING reference set.  
- **GOEnrichmentRecord** aggregates over the set of genes appearing in **PredictedEdge**.  

## File Formats
| File | Format | Primary Entity | Key Columns |
|------|--------|----------------|-------------|
| `data/raw/<species>/<accession>.counts.tsv` | TSV (genes × samples) | RNASeqSample | `gene_id`, sample columns |
| `data/processed/<species>/norm_expr.tsv` | TSV | Gene (norm) | `gene_id`, sample columns |
| `results/raw_correlations_<species>.tsv.gz` | gzipped TSV | RawCorrelation | `gene_id_1`, `gene_id_2`, `correlation`, `p_value`, `adj_p_value` |
| `data/mapped/<species>/gene2string.tsv` | TSV | Gene ↔ Protein | `gene_id`, `protein_id` |
| `results/predicted_ppi_<species>.tsv` | TSV | PredictedEdge | `protein_id_1`, `protein_id_2`, `correlation` |
| `results/evaluation_metrics.json` | JSON | EvaluationMetric | `{species: ..., auroc: ..., auprc: ..., baseline_auroc: ..., baseline_auprc: ..., baseline_p: ...}` |
| `results/go_enrichment_<species>.tsv` | TSV | GOEnrichmentRecord | `go_id`, `description`, `p_value`, `adj_p_value`, `gene_count` |
| `results/threshold_sensitivity_<species>.tsv` | TSV | ThresholdSensitivityRecord | `threshold`, `edge_count`, `auroc`, `auprc` |
| `logs/pipeline.log` | JSON‑Line | PipelineLogEntry | `timestamp`, `level`, `message`, `schema_version` |
| `logs/mapping_warnings_<species>.log` | Plain text | – | List of unmapped gene IDs |

---
