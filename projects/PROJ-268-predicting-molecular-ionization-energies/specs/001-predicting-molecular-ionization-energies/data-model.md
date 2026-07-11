# Data Model: Predicting Molecular Ionization Energies

## Key Entities

### 1. MoleculeGraph
Represents the 2D molecular structure derived from SMILES.
- **Nodes**:
  - `atom_type`: Integer (mapped from element symbol, e.g., C=6, N=7, O=8).
  - `formal_charge`: Integer.
  - `is_aromatic`: Boolean.
  - `num_hydrogens`: Integer.
- **Edges**:
  - `bond_type`: Integer (Single=1, Double=2, Triple=3, Aromatic=4).
  - `is_conjugated`: Boolean.
  - `stereo`: Integer (None=0, Cis=1, Trans=2).
- **Connectivity**: Adjacency list or edge index (source, target).

### 2. IonizationEnergyTarget (Proxy)
- **Value**: Float (eV).
- **Source**: QM9 dataset column `HOMO`.
- **Definition**: The target variable is `-HOMO` (negative HOMO energy), used as a proxy for Ionization Energy via Koopmans' theorem (IE ≈ -HOMO).
- **Unit**: Electron Volts (eV).
- **Note**: This is an approximation with known systematic errors (often > 1 eV) for organic molecules. The study acknowledges this proxy nature.

### 3. AblationConfig
- **Feature**: String (e.g., "bond_type", "atom_type").
- **Perturbation**: String (e.g., "zeroing", "gaussian_noise").
- **Sigma**: Float (e.g., 0.1).

### 4. AttributionMap
- **Indices**: List of integers (atom/bond indices).
- **Scores**: List of floats (gradient magnitudes).
- **Normalization**: Min-Max or L2 normalized.
- **Algorithm**: **Integrated Gradients** (as defined in `model_output.schema.yaml`).

## Model Architecture Definition (Single Source of Truth)
The following architecture is the definitive specification for the MPNN used in this project:
- **Type**: **Graph Convolutional Network (GCN)**.
- **Input**: 2D Graph (Nodes: Atom type, Formal Charge; Edges: Bond type, Conjugation, Stereo).
- **Layers**: **3 layers**.
- **Hidden Dimension**: **64 dimensions**.
- **Embedding**: Atom features embedded to 64-dim; Bond features to 32-dim.
- **Readout**: Global average pooling + MLP head (2 layers: 64 -> 1).
- **Activation**: ReLU.
- **Optimizer**: Adam (lr=0.001).
- **Loss Function**: Mean Squared Error (MSE).
- **Precision**: Float32.
- **CPU Compatibility**: All operations are CPU-compatible (no CUDA).

## Data Flow

1.  **Ingestion**: `raw_parquet` -> `smiles_list` + `labels` (HOMO).
2.  **Preprocessing**: `smiles` -> `rdkit_mol` -> `MoleculeGraph` (PyTorch Geometric `Data` object).
3.  **Splitting**: `MoleculeGraph` list -> `train_set`, `val_set`, `test_set` (Scaffold-based).
4.  **Training**: `train_loader` -> `MPNN` -> `predictions` -> `loss`.
5.  **Evaluation**: `test_set` -> `predictions` -> `MAE`, `RMSE`, `AttributionMap`.

## Storage Format
- **Raw Data**: Parquet (compressed).
- **Processed Graphs**: PyTorch Geometric `Data` objects saved as `.pt` files (or Parquet if serializing features).
- **Checkpoints**: `.pth` (PyTorch state dict).
- **Results**: CSV (metrics), JSON (attribution scores).