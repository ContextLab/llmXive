# Data Model: Predicting Molecular Dipole Moments with Graph Neural Networks

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    Molecule     │───────│    FeatureSet   │───────│    Model        │
│                 │       │                 │       │                 │
│ - mol_id        │       │ - mol_id        │       │ - model_id      │
│ - formula       │       │ - features_3d   │       │ - model_type    │
│ - num_atoms     │       │ - features_2d   │       │ - seed          │
│ - dipole_ref    │       │ - fingerprint   │       │ - hyperparams   │
│ - conformer_id  │       │ - coulomb_mat   │       │ - metrics       │
└─────────────────┘       └─────────────────┘       └─────────────────┘
        │                         │                         │
        │                         │                         │
        ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    Attrib       │       │    Split        │       │    Checkpoint   │
│                 │       │                 │       │                 │
│ - mol_id        │       │ - mol_id        │       │ - model_id      │
│ - feature_name  │       │ - split_type    │       │ - file_path     │
│ - importance    │       │ - seed          │       │ - checksum      │
│ - method        │       └─────────────────┘       └─────────────────┘
└─────────────────┘
```

## Core Entities

### Molecule

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| mol_id | string | Unique molecule identifier | Primary key, format: QM9_{hex} |
| formula | string | Molecular formula (e.g., "C6H6") | Not null |
| num_atoms | integer | Total atom count | > 0 |
| num_heavy | integer | Heavy atom count (non-H) | > 0 |
| dipole_ref | float | Reference dipole moment (Debye) | From QM9 DFT calculations |
| conformer_id | string | Conformer identifier | Single lowest-energy conformer |
| coordinates | array[float] | 3D atomic coordinates (N×3) | Shape: (num_atoms, 3) |
| atom_types | array[int] | Atomic numbers | Shape: (num_atoms,) |
| bonds | array[tuple] | Bond connectivity | Edge list format |

### FeatureSet

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| mol_id | string | Foreign key to Molecule | Not null |
| features_3d | object | 3D coordinate features | Shape: (num_atoms, 3) |
| features_2d | object | 2D connectivity features | Shape: (num_atoms, 1) |
| fingerprint | array[float] | Morgan fingerprint (2048 bits) | Binary vector |
| coulomb_mat | array[float] | Coulomb matrix (N×N) | Symmetric matrix |
| extracted_at | timestamp | Extraction timestamp | ISO 8601 |

### Model

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| model_id | string | Unique model identifier | Primary key |
| model_type | string | "schnet" or "random_forest" | Enum |
| seed | integer | Random seed used | One of [42, 123, 456, 789, 101112] |
| hyperparams | object | Training hyperparameters | JSON schema |
| metrics | object | Performance metrics | Contains MAE, RMSE |
| trained_at | timestamp | Training completion | ISO 8601 |

### Attribution

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| mol_id | string | Foreign key to Molecule | Not null |
| model_id | string | Foreign key to Model | Not null |
| feature_name | string | Feature identifier | e.g., "atom_0_type" |
| importance | float | Importance score | Can be negative |
| method | string | "permutation" or "saliency" | Enum |
| computed_at | timestamp | Computation timestamp | ISO 8601 |

## File Formats

### Parquet Schema (data/processed/*.parquet)

All processed data files use Apache Parquet format with PyArrow engine.

| Column | Type | Nullable |
|--------|------|----------|
| mol_id | string | false |
| features_3d | binary (serialized) | false |
| features_2d | binary (serialized) | false |
| fingerprint | binary (serialized) | false |
| coulomb_mat | binary (serialized) | false |
| dipole_ref | float64 | false |

### Model Checkpoints (data/checkpoints/*.pt)

PyTorch state dict format containing:
- model.state_dict()
- optimizer.state_dict()
- training_args
- epoch_completed
- seed_used
- checksum (SHA-256)

### Results CSV (results/*.csv)

Standard CSV with UTF-8 encoding, comma delimiter.

| Column | Type |
|--------|------|
| metric_name | string |
| model_type | string |
| seed | integer |
| value | float64 |
| std_error | float64 |

## Data Pipeline Flow

```
┌─────────────────┐
│  QM9 Source     │ (HuggingFace parquet)
└────────┬────────┘
         │ download_qm9.py
         ▼
┌─────────────────┐
│  data/raw/      │ qm9.parquet (checksummed)
└────────┬────────┘
         │ preprocess_3d.py
         ▼
┌─────────────────┐
│  data/processed/│ features_3d.parquet
└────────┬────────┘
         │ extract_2d_descriptors.py
         ▼
┌─────────────────┐
│  data/processed/│ features_2d.parquet
└────────┬────────┘
         │ train_gnn.py / train_rf.py
         ▼
┌─────────────────┐
│  data/checkpts/ │ model_seed_{N}.pt
└────────┬────────┘
         │ evaluate.py
         ▼
┌─────────────────┐
│  results/       │ metrics.csv
└─────────────────┘
```

## Integrity Constraints

1. **Checksum Verification**: All files under data/raw/ MUST have SHA-256 checksum recorded in state/*.yaml
2. **No In-Place Modification**: Transformations write to new files; original raw data preserved
3. **Schema Validation**: All Parquet files MUST pass validation against contracts/*.schema.yaml
4. **Seed Reproducibility**: All random seeds MUST be logged in model hyperparams and results
5. **Split Consistency**: Train/test splits MUST be identical across GNN and RF models (same seed)
