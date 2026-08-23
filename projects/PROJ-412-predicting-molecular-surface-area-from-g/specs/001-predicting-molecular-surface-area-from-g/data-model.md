# Data Model: Predicting Molecular Surface Area from Graph Convolutional Networks

## 1. Conceptual Model

The data model represents a molecular entity with both 2D topological and 3D geometric properties.

-   **Molecule**: The atomic unit.
    -   `smiles`: String (Canonical SMILES).
    -   `molecular_weight`: Float.
    -   `atom_count`: Integer.
    -   `node_features`: List of Float (Atom type, hybridization, charge, etc.).
    -   `edge_features`: List of Float (Bond type, conjugation, etc.).
    -   `sasa`: Float (Computed 3D Surface Area).
    -   `conformer_id`: String (Identifier for the specific 3D conformation used).
    -   `conformer_params`: String (JSON string of RDKit parameters).

-   **Graph**: The 2D representation of a Molecule.
    -   `nodes`: List of Node objects.
    -   `edges`: List of Edge objects.

-   **Prediction**: The output of the model.
    -   `smiles`: String.
    -   `predicted_sasa`: Float.
    -   `actual_sasa`: Float.
    -   `error`: Float (Absolute difference).

## 2. Physical Data Model (Parquet Schema)

The primary storage format is Apache Parquet for efficient columnar access and streaming.

### 2.1 Dataset Schema (`data/processed/graphs_with_features.parquet`)
*SSoT: `contracts/dataset.schema.yaml`*

| Column Name | Data Type | Description | Nullable |
| :--- | :--- | :--- | :--- |
| `smiles` | String | Canonical SMILES string | False |
| `molecular_weight` | Float64 | Molecular weight in g/mol | False |
| `atom_count` | Int64 | Number of atoms in the molecule | False |
| `node_features` | List<Float32> | Flattened atom feature vectors | False |
| `edge_features` | List<Float32> | Flattened bond feature vectors | False |
| `sasa` | Float64 | Computed 3D Surface Area (Å²) | False |
| `conformer_params` | String | JSON string of RDKit parameters used | False |
| `split` | String | 'train', 'test', or 'val' | False |

### 2.2 Prediction Schema (`results/predictions/gcn_predictions.parquet`)

| Column Name | Data Type | Description | Nullable |
| :--- | :--- | :--- | :--- |
| `smiles` | String | Canonical SMILES string | False |
| `predicted_sasa` | Float64 | GCN predicted SASA (Å²) | False |
| `actual_sasa` | Float64 | Ground truth SASA (Å²) | False |
| `error` | Float64 | |predicted - actual| | False |
| `model_version` | String | Git commit hash or model ID | False |

## 3. In-Memory Data Structures

### 3.1 Molecule Class (Python)
```python
class Molecule:
    def __init__(self, smiles: str, mol: rdkit.Chem.Mol):
        self.smiles = smiles
        self.mol = mol
        self.molecular_weight = ...
        self.atom_count = ...
        self.node_features = ...
        self.edge_features = ...
        self.sasa = None  # Computed later
        self.conformer_params = None
```

### 3.2 Graph Data (PyTorch Geometric)
```python
class MolGraph(Data):
    x: Tensor  # Node features [num_nodes, node_dim]
    edge_index: Tensor  # Edge connectivity [2, num_edges]
    edge_attr: Tensor  # Edge features [num_edges, edge_dim]
    y: Tensor  # Target SASA (scalar)
```

## 4. Data Flow

1.  **Ingest**: `smiles` (raw) -> `Mol` (RDKit) -> `Molecule` (filtered).
2.  **Preprocess**: `Molecule` -> `MolGraph` (2D) + `sasa` (3D) -> `Parquet`.
    - **Note**: `conformer_params` stored in Parquet column AND separate JSON summary file.
3.  **Train**: `Parquet` -> `DataLoader` -> `MolGraph` batches -> `GCN` -> `predictions`.
4.  **Eval**: `predictions` + `actual` -> `EvaluationResult` (MAE, RMSE, R², p-value).
