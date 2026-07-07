# Data Model: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Entities

### PolymerRecord

Represents a single polymer degradation entry.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `id` | str | Unique identifier (hash of SMILES + conditions) | Derived |
| `smiles` | str | Canonical SMILES string of polymer | NIST/WebBooks-1 |
| `temp` | float | Temperature (°C) | NIST/WebBooks-1 (records with missing values are EXCLUDED) |
| `pH` | float | pH value | NIST/WebBooks-1 (records with missing values are EXCLUDED) |
| `uv` | float | UV exposure (W/m²) | NIST/WebBooks-1 (records with missing values are EXCLUDED) |
| `pathway` | str | Degradation pathway label (hydrolysis/oxidation/photolysis/other) | NIST/WebBooks-1 (records without this label are EXCLUDED) |
| `flags` | list[str] | Flags for missing data, invalid SMILES, manual review | Derived |

### MolecularGraph

Graph representation of a polymer record.

| Field | Type | Description |
|-------|------|-------------|
| `nodes` | list[dict] | Atom features: `{atomic_num, degree, hybridization, charge}` |
| `edges` | list[dict] | Bond features: `{type, conjugation}` |
| `global_features` | list[float] | `[temp, pH, uv]` |
| `label` | int | Integer-encoded degradation pathway |

### MotifImportance

Derived metric linking structural motifs to pathways.

| Field | Type | Description |
|-------|------|-------------|
| `motif_pattern` | str | SMILES fragment or subgraph description |
| `pathway` | str | Associated degradation pathway |
| `importance_score` | float | Integrated Gradients attribution score (for interpretation only) |
| `p_value_global` | float | Label-shuffling permutation test p-value (global model significance) |
| `p_value_local` | float | Motif-masking permutation test p-value (local motif significance) |
| `confidence` | float | Prediction confidence (0-1) |

## Data Flow

1. **Ingestion**: `raw/` → `processed/polymer_graphs.csv` (FR-001, FR-008). **Records with missing environmental data or missing pathway labels are excluded.**
2. **Preprocessing**: `polymer_graphs.csv` → `processed/graph_dataset.pt` (PyTorch Geometric DataList) (FR-002).
3. **Augmentation**: `graph_dataset.pt` → `processed/augmented_graph_dataset.pt` (FR-004). **Only if n < 150; uses SMILES canonicalization and functional-group-preserving edge dropout (corrected from bond rotation).**
4. **Training**: `augmented_graph_dataset.pt` → `models/gnn_model.pt` (FR-003).
5. **Evaluation**: `models/gnn_model.pt` + `graph_dataset.pt` → `reports/motif_report.yaml` (FR-006, FR-007). **Uses Label-Shuffling (global) and Motif-Masking (local) permutation tests.**

## Storage Schema

- **Raw Data**: `data/raw/*.txt` (original downloads, checksummed).
- **Processed Data**: `data/processed/*.csv`, `*.pt` (PyTorch Geometric format).
- **Models**: `models/*.pt` (trained GNN weights).
- **Reports**: `reports/*.yaml`, `*.json` (motif rankings, p-values, macro-F1).
