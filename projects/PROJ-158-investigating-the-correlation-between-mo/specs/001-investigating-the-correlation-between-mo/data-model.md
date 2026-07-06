# Data Model: Investigating the Correlation Between Molecular Structure and Dye‑Sensitized Solar Cell Performance

## 1. Domain Entities

### Molecule
Represents a chemical entity in the dataset.
- **Attributes**:
  - `smiles` (str): Canonicalized SMILES string.
  - `pce` (float): Power Conversion Efficiency in percent (%).
  - `scaffold` (str): Bemis-Murcko scaffold string.
  - `status` (str): `valid`, `invalid_smiles`, `missing_pce`.
  - `graph_features` (dict): Computed atom/bond features (if processed).

### ModelArtifact
Represents a trained model instance.
- **Attributes**:
  - `model_type` (str): `GCN` or `RandomForest`.
  - `fold_id` (int): Cross-validation fold index (0-4).
  - `metrics` (dict): `mae`, `rmse`, `r2`.
  - `weights_path` (str): Path to saved model weights.
  - `hyperparameters` (dict): Configuration used for training.

### Motif
Represents a recurring substructure identified by the interpretability module.
- **Attributes**:
  - `subgraph` (str): Canonical SMILES of the substructure.
  - `frequency` (int): Count of occurrences in high-PCE predictions.
  - `importance_score` (float): Average contribution to PCE prediction.
  - `is_non_isomorphic` (bool): True if unique from other top motifs.

## 2. Data Flow

1. **Raw Input**: `dssc_dataset.csv` (or JSONL) -> `download.py`.
2. **Standardization**: `preprocess.py` -> `graph_data.pt` (PyTorch Geometric `Data` objects).
3. **Splitting**: `split.py` -> `train_idx`, `val_idx`, `test_idx` (scaffold-aware).
4. **Training**: `train.py` -> `model_weights.pt`, `metrics.json`.
5. **Analysis**: `interpret.py` -> `motifs.json`.

## 3. File Formats

- **Raw Data**: CSV or JSONL (UTF-8).
- **Processed Graphs**: PyTorch Geometric `.pt` (binary).
- **Metrics**: JSON (UTF-8).
- **Logs**: `.log` (UTF-8).

## 4. Constraints

- **PCE**: Must be > 0 and < 30 (physical limits for DSSC). Values outside this range trigger a warning.
- **SMILES**: Must be parseable by RDKit.
- **Scaffold**: Must be non-empty string.
