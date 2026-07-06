# Data Model: Predicting Molecular Permeability of Polymers via Graph Neural Networks

## 1. Entities & Relationships

### 1.1 Core Entities

1.  **PolymerGraph**
    - **Description**: Represents a polymer molecule as a graph.
    - **Attributes**:
        - `smiles` (str): Canonical SMILES string.
        - `molecular_weight` (float): Calculated MW.
        - `nodes`: List of atom features (dict: `{"element": str, "hybridization": str, "charge": int}`).
        - `edges`: List of bond features (dict: `{"type": str, "stereo": str}`).
        - `scaffold_id` (str): Murcko scaffold hash for splitting.

2.  **PermeabilityRecord**
    - **Description**: Links a `PolymerGraph` to its target value.
    - **Attributes**:
        - `graph_id` (str): Reference to `PolymerGraph`.
        - `permeability_coefficient` (float): Experimental value in Barrer.
        - `log_permeability` (float): `log10(permeability_coefficient)`.
        - `gas_type` (str): Target gas (e.g., "CO2").
        - `source` (str): "NIST" or "Mock" (since real NIST URL is missing).

3.  **ModelArtifact**
    - **Description**: Serialized trained model and metadata.
    - **Attributes**:
        - `model_type` (str): "GNN", "RandomForest", "LinearRegression".
        - `weights_path` (str): Path to `.pt` or `.pkl`.
        - `config` (dict): Hyperparameters (layers, dims, lr).
        - `metrics` (dict): R², MAE, Pearson on test set.
        - `seed` (int): Random seed used.

### 1.2 Relationships

- **PolymerGraph** `1` -- `1` **PermeabilityRecord** (One-to-One).
- **ModelArtifact** `1` -- `N` **PermeabilityRecord** (One model predicts many records).
- **PolymerGraph** `N` -- `1` **ScaffoldGroup** (Many graphs belong to one scaffold group).

## 2. Data Flow

1.  **Ingestion**: Raw SMILES (PubChem) -> `ingestion.py` -> `PolymerGraph` objects + Mock `PermeabilityRecord`.
2.  **Preprocessing**: `PolymerGraph` -> `preprocessing.py` -> Train/Val/Test splits (Scaffold-aware).
3.  **Training**: Train Split -> `trainer.py` -> `ModelArtifact`.
4.  **Evaluation**: Test Split + `ModelArtifact` -> `metrics.py` -> JSON Report.

## 3. File Formats

- **Input**: Parquet (PubChem SMILES).
- **Intermediate**: HDF5 (Graph features, splits).
- **Output**: JSON (Metrics), Pickle/PT (Models).

## 4. Constraints

- **No Missing Values**: Critical features (SMILES, MW) must be present. If missing, record is dropped.
- **Log Scale**: Target variable stored as `log10` to normalize distribution.
- **Scaffold Integrity**: Test set must not share scaffolds with Train set.
