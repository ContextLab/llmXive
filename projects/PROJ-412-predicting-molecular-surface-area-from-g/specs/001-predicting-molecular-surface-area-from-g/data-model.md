# Data Model: Predicting Molecular Surface Area from Graph Convolutional Networks

## 1. Entities

### Molecule
Represents a chemical compound.
- `smiles` (string): Canonical SMILES string.
- `mol_id` (string): Unique identifier (hash of SMILES).
- `molecular_weight` (float): Calculated MW.
- `node_features` (list[float]): Vector of atom properties (type, hybridization, charge).
- `edge_features` (list[float]): Vector of bond properties (type, conjugation).
- `surface_area_3d` (float): Computed 3D surface area (Å²).
- `conformer_success` (bool): Whether 3D conformer was generated.
- `conformer_params` (string): JSON string of RDKit conformer generation parameters (attempts, minimization steps).

### Graph
Represents the 2D topological structure.
- `adjacency_matrix` (2D array): Node connectivity.
- `node_matrix` (2D array): Node feature vectors.
- `edge_index` (2D array): Edge connectivity for PyTorch Geometric.

### ModelArtifact
Represents a trained model.
- `model_id` (string): Unique hash.
- `model_type` (enum): `GCN_2D` | `GCN_3D`.
- `hyperparameters` (dict): Architecture details.
- `weights_path` (string): Path to serialized weights.
- `training_metrics` (dict): Final loss, epochs.

### EvaluationResult
Represents the outcome of a test.
- `model_id` (string): Reference to model.
- `test_set_id` (string): Reference to test split.
- `mae` (float): Mean Absolute Error.
- `rmse` (float): Root Mean Squared Error.
- `r_squared` (float): R² score.
- `p_value` (float): Statistical significance (if applicable).
- `effect_size` (float): Cohen's d.

## 2. Data Flow

1.  **Raw Input**: SMILES strings from HuggingFace (Parquet).
2.  **Processed Input**: `processed_molecules.parquet` (SMILES, 2D features, 3D labels, conformer_params).
3.  **Training Data**: `train_graphs.pt`, `train_labels.pt`.
4.  **Test Data**: `test_graphs.pt`, `test_labels.pt`.
5.  **Outputs**: `results.json` (metrics), `models/` (weights).

## 3. Constraints

- **Missing Values**: `surface_area_3d` must not be NaN for training rows.
- **Invalid SMILES**: Excluded from dataset; logged.
- **Conformer Failure**: Excluded from dataset; logged.
- **Max Atoms**: Molecules > 100 atoms excluded (memory constraint).
- **Conformer Params**: `conformer_params` field must be present and non-empty for all molecules with `conformer_success=true`.