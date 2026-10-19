# Data Model: Predicting Molecular Reactivity

## Overview
Defines schemas, transformations, and storage formats for the end‑to‑end pipeline. All artifacts are validated against JSON‑Schema contracts under `contracts/`.

## Data Flow

1. **Raw Data** (`data/raw/`) – immutable downloads and curated CSV assets.  
2. **Processed Data** (`data/processed/`) – graph objects (`graphs.pt`) and scaffold split indices.  
3. **Artifacts** (`artifacts/`) – model checkpoints, predictions, metrics, attribution maps, logs, and checksums.

## Schema Definitions

### 1. Molecular Graph (`contracts/dataset.schema.yaml`)
- `molecule_id`: string  
- `smiles`: string  
- `node_features`: list of objects (`atomic_number`, `hybridization`, `formal_charge`, `num_neighbors`)  
- `edge_features`: list of objects (`bond_type`, `conjugation`, `in_ring`)  
- `target`: object (`homo_lumo_gap`: float)  
- `split`: enum(`train`, `val`, `test`)  
- `similarity_score`: float (max Tanimoto to training set)  

### 2. Checksum File (`data/raw/checksums.json`)
Conforms to `contracts/checksums.schema.yaml` (array of objects with `file_path` and `sha256`). Initially empty `{}`; populated after download.

### 3. Model Predictions (`contracts/model-output.schema.yaml`)
- `graph_id`: string  
- `actual_gap`: float  
- `predicted_gap`: float  
- `error`: float (`predicted_gap - actual_gap`)  
- `model_name`: enum(`spectral_gnn`, `heterophily_gnn`, `random_forest`)  

### 4. Evaluation Metrics (`contracts/metrics.schema.yaml`)
- Per‑model `mse`, `mae`, `pearson_r`  
- `statistical_tests` array (paired t‑test, p‑value, Bonferroni‑adjusted α, significance flag)  
- `interpretability` block (`alignment_score`, `top_features`, `reference_source_type`)  

### 5. Attribution Maps (`contracts/attribution.schema.yaml`)
- `molecule_id`: string  
- `node_importance`: array[float]  
- `edge_importance`: array[float]  
- `top_substructures`: array of objects (`substructure_smiles`, `importance_score`, `matches_reference`)  
- `alignment_score`: float (0 – 1)  
- `recall_at_k`: float  
- `null_model_score`: float  

### 6. Final Output (`contracts/output.schema.yaml`)
Aggregates `metrics`, `statistical_test`, `predictions` (list of per‑model predictions), and `attribution.top_features`.

## Storage Formats
- **Parquet** – QM9 raw, predictions (columnar, efficient).  
- **CSV** – Curated reference & kinetic assets.  
- **PyTorch `.pt`** – Serialized `torch_geometric` graphs.  
- **JSON** – Metrics, attribution, checksums, logs.

## Data Hygiene Rules
- **Immutability**: Files under `data/raw/` are never overwritten. New versions go to a versioned subdirectory.  
- **Checksums**: Every raw file must have a corresponding entry in `checksums.json`. Validation performed in **T006** and **T007**.  
- **Schema Validation**: After each generation step, the corresponding contract schema is validated; failures abort the pipeline.  

---
