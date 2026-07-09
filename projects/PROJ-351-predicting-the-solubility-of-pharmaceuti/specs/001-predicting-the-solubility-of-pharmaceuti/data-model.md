# Data Model: Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

## 1. Domain Entities

### 1.1 Molecule
Represents a chemical compound.
- `smiles`: `str` - Canonical SMILES string.
- `logS`: `float` - Experimental solubility in water (log mol/L).
- `mol`: `rdkit.Chem.rdchem.Mol` - RDKit molecular object (derived).
- `scaffold`: `str` - Bemis-Murcko scaffold string (derived).
- `features`: `dict` - Extracted features (atom/bond tensors for GNN, fingerprint bit vector for RF).
- `valid`: `bool` - Whether the SMILES parsed successfully.

### 1.2 DatasetSplit
Represents the partitioned data.
- `train_indices`: `list[int]` - Indices of training samples.
- `val_indices`: `list[int]` - Indices of validation samples.
- `test_indices`: `list[int]` - Indices of test samples.
- `scaffold_distribution`: `dict` - Map of scaffold strings to counts per split.
- `logS_distribution`: `dict` - Statistics (mean, std, min, max) per split.

### 1.3 Model
Represents a trained predictor.
- `type`: `str` - "RandomForest", "MPNN_Raw", or "MPNN_FP".
- `metrics`: `dict` - `{"rmse": float, "r2": float, "mae": float}`.
- `weights_path`: `str` - Path to saved model file.
- `hyperparams`: `dict` - Configuration used for training.

### 1.4 EvaluationResult
Represents the outcome of a comparison.
- `baseline_metrics`: `dict` - RF metrics.
- `gnn_raw_metrics`: `dict` - GNN (Raw Graph) metrics.
- `gnn_fp_metrics`: `dict` - GNN (Fixed Features) metrics.
- `p_value_permutation`: `float` - Result of scaffold-aware permutation test.
- `p_value_wilcoxon`: `float` - Result of Wilcoxon test (if applicable).
- `mdes`: `float` - Minimum Detectable Effect Size from simulation.
- `significance`: `bool` - True if p < 0.05.
- `delta_rmse`: `float` - GNN RMSE - RF RMSE.

## 2. Data Flow

1.  **Raw CSV** → `download_esol.py` → **Cleaned CSV** (invalid SMILES removed).
2.  **Cleaned CSV** → `preprocess.py` → **Scaffold Extraction** + **Featurized Parquet** (RF features + GNN graphs + scaffold strings).
3.  **Featurized Parquet** → `split.py` → **Scaffold-Based Split Parquets** (train/val/test).
4.  **Split Parquets** → `train_baseline.py` / `train_gnn_raw.py` / `train_gnn_fp.py` → **Model Artifacts** (.pkl, .pt) + **Metrics JSON**.
5.  **Metrics JSON** → `statistical_test.py` (Permutation + Wilcoxon) → **Final Report JSON**.

## 3. Storage Schema

- `data/raw/esol_raw.csv`: Original download.
- `data/processed/cleaned_esol.parquet`: Cleaned data.
- `data/processed/featurized_esol.parquet`: With fingerprint/graph/scaffold columns.
- `data/processed/splits.json`: Indices for train/val/test + scaffold mapping.
- `models/baseline_rf.pkl`: Scikit-learn model.
- `models/mpnn_raw_gnn.pt`: PyTorch Geometric model (Raw Graph).
- `models/mpnn_fp_gnn.pt`: PyTorch Geometric model (Fixed Features).
- `results/metrics.json`: Final metrics.
- `results/interpretability/`: PNG files.