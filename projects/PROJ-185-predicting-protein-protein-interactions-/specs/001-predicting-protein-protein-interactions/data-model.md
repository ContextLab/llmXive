# Data Model: Predict Protein‑Protein Interactions from Co‑expression Networks

## Overview
The pipeline manipulates several tabular data artifacts. Each artifact is defined by a schema stored under `specs/PROJ-185-predict-ppi-coexpression/contracts/`. The schemas enable automated validation in the CI.

## Entities

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **RawCountMatrix** | Unprocessed GEO count matrix (genes × samples). | `gene_id` (string), `sample_id` (string), `count` (integer) |
| **NormalizedExpression** | TPM or VST normalized values per gene per sample. | `gene_id`, `sample_id`, `value` (float) |
| **FilteredGeneList** | Genes passing CPM < 1 filter in ≤ 80 % of samples. | `gene_id` |
| **VariableGeneSet** | Top‑MAD (median absolute deviation) selected genes used for correlation. | `gene_id`, `mad_score` (float) |
| **CoExpressionEdge** | Undirected gene‑gene correlation edge. | `gene_a` (string), `gene_b` (string), `pearson_r` (float), `p_value` (float), `fdr` (float) |
| **MappedEdge** | Edge after gene → STRING protein mapping. | `protein_a` (string, STRING ID), `protein_b` (string), `pearson_r` (float) |
| **StringInteraction** | Reference interaction from STRING v11.5. | `protein_a` (string), `protein_b` (string), `combined_score` (integer), `evidence_type` (string, optional) |
| **EvaluationMetric** | AUROC/AUPRC per species plus baseline scores and empirical p‑value. | `species` (string), `auroc` (float), `auprc` (float), `baseline_auroc` (float), `baseline_auprc` (float), `baseline_p` (float) |
| **GOEnrichmentRecord** | GO term enrichment result. | `go_id` (string), `description` (string), `raw_p` (float), `adj_p` (float), `gene_count` (int) |

## Relationships
- `MappedEdge` is derived from `CoExpressionEdge` via `map_ids.py`.  
- `EvaluationMetric` compares `MappedEdge` set to `StringInteraction` (high confidence and experimental subsets).  
- `GOEnrichmentRecord` is derived from the union of genes participating in `MappedEdge`.  

All intermediate files are immutable; any transformation produces a new file with a filename indicating the processing step (e.g., `*_norm.tsv`, `*_filtered.tsv`, `*_variable.tsv`).  

## Contract Associations
- **Raw edge list** (`results/edges/<species>_raw_edges.tsv`) must conform to `contracts/predicted_edges.schema.yaml`.  
- **Final PPI edge list** (`results/predicted_ppi_<species>.tsv`) must conform to `contracts/predicted_ppi.schema.yaml`.  

These contracts are validated in the CI as part of tasks T012 and T014.

--- 
