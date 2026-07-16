# Data Model Documentation

This document describes the data structures, file formats, and schemas used throughout the pipeline.

## Raw Data
### Source: QM9 (via `lisn/QM9`)
The dataset contains quantum chemical calculations for ~134k small organic molecules. [UNRESOLVED-CLAIM: c_19b8a9bf — status=not_enough_info]

**Key Columns**:
- `smiles`: Canonical SMILES string.
- `u0_atom`: Atomization energy.
- `dipole`: Dipole moment (Debye).
- `homo`: HOMO energy (eV).
- `lumo`: LUMO energy (eV).
- `coordinates`: 3D atomic coordinates (XYZ format).

## Processed Data Formats

### Parquet Files
- **`data/raw/qm9_full.parquet`**: Raw downloaded data.
- **`data/processed/molecules_cleaned.parquet`**: Filtered dataset with valid DFT labels and geometry.

**Schema**:
| Column | Type | Description |
|:--- |:--- |:--- |
| `molecule_id` | str | Unique identifier |
| `smiles` | str | SMILES string |
| `dipole` | float | Target: Dipole moment |
| `homo` | float | Target: HOMO energy |
| `lumo` | float | Target: LUMO energy |
| `coordinates` | list | 3D coordinates |

### NumPy Arrays
- **`data/processed/features_2d.npy`**: 2D Morgan fingerprints.
 - Shape: `(N, 2048)` where N is the number of molecules.
 - Data type: `bool` or `int` (bit vector).
- **`data/processed/features_3d.npy`**: 3D graph features.
 - Shape: `(N, F)` where F is the number of 3D features.
 - Data type: `float32`.

### CSV Files
- **`data/processed/labels.csv`**: Target values aligned with feature matrices.
 - Columns: `molecule_id`, `dipole`, `homo`, `lumo`.
 - Index: Must match the order of rows in the `.npy` feature files.

## Model Artifacts
- **`artifacts/models/model_2d.pkl`**: Pickled Random Forest model for 2D features.
- **`artifacts/models/model_3d.pkl`**: Pickled Random Forest model for 3D features.

## Metrics and Analysis Artifacts

### `artifacts/metrics/cv_metrics.json`
Cross-validation results.
```json
{
 "model_2d": {
 "fold_maes": [0.12, 0.11, 0.13,...],
 "mean_mae": 0.12,
 "std_mae": 0.01
 },
 "model_3d": {
 "fold_maes": [0.08, 0.07, 0.09,...],
 "mean_mae": 0.08,
 "std_mae": 0.005
 }
}
```

### `artifacts/metrics/stability_report.json`
Stability verification (SC-005).
```json
{
 "fold_maes": [0.12, 0.11,...],
 "stability_ratio": 0.05,
 "passed": true
}
```

### `artifacts/metrics/statistics.json`
Wilcoxon signed-rank test results.
```json
{
 "dipole": {"statistic": 1234.5, "pvalue": 0.001},
 "homo": {"statistic": 567.8, "pvalue": 0.03},
 "lumo": {"statistic": 890.1, "pvalue": 0.002}
}
```

### `artifacts/metrics/failure_boundary.json`
List of molecules where 2D model fails relative to 3D.
```json
[
 {
 "molecule_id": "qm9_12345",
 "descriptor": "dipole",
 "reason": "REI >= 10% or p-value < 0.0167"
 }
]
```

### `artifacts/plots/parity_*.png`
Scatter plots of Predicted vs. DFT values.
- **X-axis**: DFT (Ground Truth)
- **Y-axis**: Predicted
- Includes regression line and R² score.

## Internal Data Classes (code/utils/models.py)
- **`Molecule`**: Dataclass representing a single molecule with SMILES, coordinates, and targets.
- **`FeatureSet`**: Container for 2D and 3D feature matrices.
- **`ModelResult`**: Container for model predictions and metrics.
