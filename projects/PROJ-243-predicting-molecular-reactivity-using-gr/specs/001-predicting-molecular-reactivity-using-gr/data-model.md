# Data Model: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

## Entity Relationship Overview

The system processes raw chemical data into graph structures, trains models, and outputs metrics and attribution maps.

### 1. Raw Data (Input)
*   **Source**: QM9 Parquet files.
*   **Fields**: `smiles`, `atom_types`, `bond_types`, `homo`, `lumo`, `gap`, `energy`, `dipole_moment`.

### 2. Processed Graph (Internal)
*   **Node**: Represents an atom.
    *   `atomic_number` (int)
    *   `hybridization` (int: 0=sp, 1=sp2, 2=sp3, 3=other)
    *   `formal_charge` (int)
    *   `is_aromatic` (bool)
*   **Edge**: Represents a bond.
    *   `bond_type` (int: 1=single, 2=double, 3=triple, 4=aromatic)
    *   `conjugation` (bool)
    *   `is_in_ring` (bool)
*   **Graph ID**: Unique identifier (derived from SMILES hash).
*   **Target**: `gap` (float).

### 3. Model Outputs
*   **Predictions**: `graph_id`, `predicted_gap`, `actual_gap`, `error`.
*   **Attribution**: `graph_id`, `node_importance` (list), `edge_importance` (list), `top_subgraph_smiles`.

### 4. Evaluation Metrics
*   **Metrics**: `model_name`, `mse`, `mae`, `pearson_r`, `p_value_wilcoxon`, `p_value_ttest`, `significant_wilcoxon`, `significant_ttest`.

## Data Flow

1.  **Download**: Raw Parquet -> `data/raw/qm9.parquet`
2.  **Preprocess**: `data/raw/qm9.parquet` -> `data/processed/graphs.pkl` (List of Graph objects)
3.  **Split**: `data/processed/graphs.pkl` -> `data/processed/train_graphs.pkl`, `data/processed/test_graphs.pkl`
4.  **Train**: `train_graphs.pkl` -> `code/models/weights.pth`
5.  **Evaluate**: `test_graphs.pkl` + `weights.pth` -> `data/processed/predictions.csv`, `data/processed/metrics.json`
6.  **Explain**: `test_graphs.pkl` + `weights.pth` -> `data/processed/attribution.json`

## Constraints & Types

*   **Memory**: All graph objects must be serialized to disk if memory usage > 3.5 GB.
*   **Precision**: Float32 for model weights to save memory; Float64 for statistical calculations.
*   **Validity**: SMILES strings must pass RDKit validation. Invalid entries are logged and dropped.
*   **Provenance**: The `Curated Reference Set` (FR-008) must include a `source_type` field indicating "Experimental" or "Independent Literature" to ensure it is not derived from QM9.