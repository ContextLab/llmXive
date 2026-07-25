# Data Model: Predict Protein‑Protein Interactions from Co‑expression Networks

## Core Entities

| Entity | Attributes | Description |
|--------|------------|-------------|
| **RNASeqSample** | `accession` (GEO ID), `species`, `raw_counts_path`, `metadata_path` | Represents a single GEO series (multiple samples). |
| **Gene** | `gene_id` (TAIR or Ensembl), `normalized_expression` (vector), `string_protein_id` (optional) | After normalization and filtering. |
| **RawCorrelation** | `gene_id_1`, `gene_id_2`, `correlation`, `p_value`, `adjusted_p_value` | Computed before identifier mapping; stored in `raw_correlations_*.tsv.gz`. |
| **ProteinCorrelation** | `protein_id_1`, `protein_id_2`, `correlation` | Post‑mapping edge candidate. |
| **PredictedEdge** | `protein_id_1`, `protein_id_2`, `correlation` | Edges passing threshold & BH filter; output file `predicted_ppi_*.tsv`. |
| **EvaluationMetric** | `species`, `auroc`, `auprc`, `baseline_auroc`, `baseline_auprc`, `baseline_p` | Stored in `evaluation_metrics.json`. |
| **GOEnrichmentRecord** | `go_id`, `term_name`, `raw_p`, `adjusted_p`, `gene_count` | Rows of `go_enrichment_*.tsv`. |
| **ThresholdSensitivityRecord** | `threshold`, `edge_count`, `auroc`, `auprc` | Rows of `threshold_sensitivity_*.tsv`. |
| **PipelineLogEntry** | `timestamp`, `level`, `message`, `schema_version` | JSON‑Line log file `pipeline.log`. |

## Relationships
- Each **RNASeqSample** contains many **Gene** objects after normalization.
- **RawCorrelation** links two **Gene** objects.
- **ProteinCorrelation** links two **PredictedEdge** objects after mapping.
- **EvaluationMetric** is computed from the full set of **RawCorrelation** scores versus STRING positives/negatives.
- **GOEnrichmentRecord** is derived from the set of genes appearing in **PredictedEdge**.

## File Schemas (see `contracts/`)

| File | Schema |
|------|--------|
| `predicted_ppi_<species>.tsv` | `predicted_edges.schema.yaml` |
| `evaluation_metrics.json` | `evaluation.schema.yaml` |
| `threshold_sensitivity_<species>.tsv` | `threshold_sensitivity.schema.yaml` |
| `pipeline.log` | `pipeline_log.schema.yaml` |

All schemas enforce column order, data types, and required fields (see contract files).

---
