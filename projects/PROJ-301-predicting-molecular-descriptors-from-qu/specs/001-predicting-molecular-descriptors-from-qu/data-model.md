# Data Model: Predicting Molecular Descriptors

## 1. Entity-Relationship Overview

The data model is designed to support a pipeline that transforms raw molecular data into feature matrices, trains models, and stores evaluation metrics.

### Core Entities

1.  **Molecule**: The fundamental unit of analysis.
2.  **FeatureSet**: The input representation for a model (2D or 3D).
3.  **ModelResult**: The output of the training process.
4.  **EvaluationMetric**: The quantitative assessment of model performance.

## 2. Data Schemas

### 2.1 Raw Data (QM9 Parquet)
*Source*: HuggingFace QM9 Dataset
*Format*: Parquet
*Schema*:
- `mol_id`: string (Unique identifier, e.g., "c1ccccc1")
- `smiles`: string (Canonical SMILES)
- `x`: float[] (3D coordinates of atoms, shape: [n_atoms, 3])
- `y`: float[] (3D coordinates of atoms, shape: [n_atoms, 3])
- `z`: float[] (3D coordinates of atoms, shape: [n_atoms, 3])
- `mu`: float (Dipole moment in Debye)
- `homo`: float (HOMO energy in eV)
- `lumo`: float (LUMO energy in eV)
- `n_atoms`: int (Number of atoms)

### 2.2 Feature Matrices (Processed)
*Format*: NumPy (`.npy`) or CSV
*Schema*:
- **2D Features (`features_2d.npy`)**:
  - Shape: `[N_molecules, 2048]`
  - Type: `float32` (binary fingerprint values)
  - Index: Molecule ID (aligned with labels)
- **3D Features (`features_3d.npy`)**:
  - Shape: `[N_molecules, N_features]` (N_features is variable based on graph construction, e.g., a range of values)
  - Type: `float32` (normalized geometric invariants)
  - Index: Molecule ID (aligned with labels)

### 2.3 Labels (Processed)
*Format*: CSV
*Schema*:
| Column | Type | Description |
|--------|------|-------------|
| `mol_id` | string | Unique molecule identifier |
| `mu` | float | Dipole moment (Debye) |
| `homo` | float | HOMO energy (eV) |
| `lumo` | float | LUMO energy (eV) |

### 2.4 Model Artifacts
*Format*: Pickle (`.pkl`)
*Schema*:
- `model_2d.pkl`: Trained Random Forest Regressor (2D features).
- `model_3d.pkl`: Trained Random Forest Regressor (3D features).
- `cv_results_2d.json`: Cross-validation metrics (MAE, RMSE per fold).
- `cv_results_3d.json`: Cross-validation metrics (MAE, RMSE per fold).

### 2.5 Evaluation Results
*Format*: JSON
*Schema*:
```json
{
  "descriptor": "mu",
  "model_2d": { "mae": 0.05, "rmse": 0.06, "std_mae": 0.002 },
  "model_3d": { "mae": 0.03, "rmse": 0.04, "std_mae": 0.001 },
  "relative_error_increase": 0.67,
  "is_significant": true,
  "p_value": 0.001,
  "cv_stability": 0.04,
  "cv_stability_pass": true,
  "stratification": {
    "by_atom_count": { "bins": [5, 10, 15], "rei": [0.1, 0.5, 0.8] },
    "by_polarity": { "bins": [0, 1, 2], "rei": [0.2, 0.4, 0.9] }
  },
  "mean_predictor_error": 0.5,
  "theoretical_lower_bound": 0.5
}
```

## 3. Data Flow

1.  **Ingestion**: Raw Parquet → Filtered Subset (Memory Check) → `data/raw/qm9_subset.parquet`.
2.  **Transformation**:
    - `data/raw` → `02_feature_extraction.py` → `data/processed/features_2d.npy`, `features_3d.npy`, `labels.csv`.
3.  **Training**:
    - `features_2d.npy` + `labels.csv` → `03_model_training.py` → `models/model_2d.pkl`, `results/cv_2d.json`.
    - `features_3d.npy` + `labels.csv` → `03_model_training.py` → `models/model_3d.pkl`, `results/cv_3d.json`.
4.  **Analysis**:
    - `models/` + `results/` → `04_analysis.py` → `results/metrics.json`, `results/parity_plots.png`.

## 4. Constraints & Validation

- **Alignment**: All feature matrices and label vectors must share the exact same `mol_id` order (after strict intersection filtering).
- **Missing Data**: Rows with missing `mu`, `homo`, or `lumo` are dropped before feature extraction.
- **Memory**: Feature extraction must not exceed a moderate RAM footprint.; if so, `N_molecules` is reduced while preserving chemical diversity.
- **Reproducibility**: All random seeds for splitting and model initialization are fixed (seed=42).