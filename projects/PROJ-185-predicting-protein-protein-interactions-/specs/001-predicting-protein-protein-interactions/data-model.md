# Data Model: Predict Protein‑Protein Interactions from Co‑expression Networks

## Core Entities

| Entity | Attributes | Description |
|--------|------------|-------------|
| **RNASeqSample** | `accession_id: str` (GEO series), `raw_counts_path: str`, `metadata: dict`, `species: str` | Represents a single GEO series raw count matrix and its associated metadata. |
| **Gene** | `gene_id: str` (TAIR or Ensembl), `normalized_expression: np.ndarray`, `cpm: float`, `string_protein_id: Optional[str]` | Normalized expression vector after TPM/VST, CPM value for filtering, optional mapped STRING protein identifier. |
| **CoExpressionEdge** | `gene_a: str`, `gene_b: str`, `pearson_r: float`, `string_score: Optional[int]` | Undirected edge between two genes; `string_score` filled only after mapping to STRING reference. |
| **PredictedPPINetwork** | `species: str`, `edges: List[CoExpressionEdge]`, `threshold: float`, `seed: int` | Whole set of predicted PPIs for a species, generated with a fixed correlation threshold and random seed. |
| **StringReferenceEdge** | `protein_a: str`, `protein_b: str`, `combined_score: int` | High‑confidence interaction from STRING (combined_score ≥ 700). |
| **EvaluationMetric** | `species: str`, `auroc: float`, `auprc: float`, `baseline_auroc: float`, `baseline_auprc: float` | Performance numbers for a species, including random‑graph baseline. |
| **GOEnrichmentRecord** | `go_id: str`, `description: str`, `raw_p: float`, `adjusted_p: float`, `gene_count: int` | Result of GO enrichment for a species. |
| **ProvenanceLog** | `artifact_path: str`, `checksum_sha256: str`, `generation_timestamp: str`, `parameters: dict` | Records how a file was derived, satisfying data‑hygiene requirements. |

## Relationships

- **RNASeqSample** → multiple **Gene** objects (one per row after loading).  
- **Gene** ↔ **StringReferenceEdge** via `string_protein_id`.  
- **CoExpressionEdge** links two **Gene** objects; after mapping, may be annotated with a **StringReferenceEdge** `combined_score`.  
- **PredictedPPINetwork** aggregates **CoExpressionEdge** instances for a species.  
- **EvaluationMetric** consumes a **PredictedPPINetwork** and the set of **StringReferenceEdge** for benchmarking.  
- **GOEnrichmentRecord** consumes the set of genes present in a **PredictedPPINetwork**.

All entities are persisted as tab‑/JSON‑delimited files under `results/` and `data/derived/`. Provenance information is stored alongside each file in a matching `.prov.json` file.

---
