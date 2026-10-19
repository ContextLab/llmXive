# Data Model: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

## Overview
The pipeline stores all artifacts under `data/` with strict versioning and checksum tracking. The model defines six core entity types that flow from raw ingestion to the final statistical report.

## Entities

| Entity | Fields | Description |
|--------|--------|-------------|
| **Dataset** | `dataset_id` (str), `source_url` (str), `status` (enum), `checksum` (str), `raw_path` (str), `processed_path` (str, nullable) | Represents a GEO accession; status indicates availability. |
| **PreprocessedMatrix** | `dataset_id`, `matrix_path` (Parquet), `n_cells`, `n_genes`, `hvg_count`, `geometric_descriptors` (object) | Log‑CPM transformed, HVG‑selected, possibly sampled matrix. |
| **Embedding** | `dataset_id`, `method` (enum), `embedding_path` (CSV), `dimensions` (int), `hyperparameters` (object), `clustering` (object) | Low‑dimensional representation plus clustering results. |
| **FidelityMetric** | `dataset_id`, `method`, `metric_type` (enum), `value` (float), `silhouette_score` (float), `optimal_resolution` (float) | ARI or NMI for a given embedding (logit‑transformed for modeling). |
| **MixedEffectsModel** | `model_type` (enum), `formula` (str), `fixed_effects` (array), `random_effects` (object), `vif_values` (object), `collinearity_passed` (bool), `permutation_p_value` (float, nullable) | Captures the mixed‑effects regression output, including VIF after dropping a reference level. |
| **StatisticalResult** | `model_summary` (object), `sensitivity_analysis` (object), `execution_metadata` (object) | Final ANOVA/Permutation output, VIF diagnostics, and runtime stats. |

## Data Flow Diagram
```mermaid
graph TD
    A[Raw GEO JSON] -->|Phase 0| B[Dataset Manifest]
    B -->|Phase 1| C[PreprocessedMatrix]
    C -->|Phase 2| D[Embedding]
    D -->|Phase 3| E[FidelityMetric]
    E -->|Phase 5| F[MixedEffectsModel]
    F -->|Phase 6| G[StatisticalResult]
```

## Storage Formats
- **Raw JSON**: `data/raw/<dataset_id>.json` (as extracted from the GSE JSON).  
- **Processed Matrix**: Parquet (`data/processed/<dataset_id>_logcpm.parquet`).  
- **Embeddings**: CSV (`data/embeddings/<dataset_id>_<method>.csv`).  
- **Geometric Descriptors**: JSON (`data/processed/<dataset_id>_geometric.json`).  
- **Fidelity Metrics**: JSON (`data/metrics/fidelity_<dataset_id>.json`).  *Values are stored **logit‑transformed** to match modeling requirements.*  
- **Statistical Result**: YAML (`data/results/statistical_result.yaml`).  
- **Manifest & Checksums**: `data/manifest.json` (generated after Phase 0).  

## Contracts
All output files are validated against schemas in `contracts/` (e.g., `statistical_result.schema.yaml`). The manifest records a SHA‑256 checksum for every raw file, enabling reproducibility checks (Constitution III).

---



