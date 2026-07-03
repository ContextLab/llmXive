# Synthetic Data Generator API

This document describes the public API for the physics-based synthetic data generator used in the `llmXive` pipeline for quantifying the influence of topological defects on 2D material properties.

## Overview

The synthetic data generator provides a fallback mechanism when real experimental or DFT data is unavailable. It implements physics-based analytical models (Griffith criterion, Rule of Mixtures, Matthiessen's rule) and a Gaussian Process (GP) surrogate for hold-out set generation.

**Module Location**: `src/generators/synthetic_data_generator.py`

**Usage Context**: Invoked by `code/01_data_acquisition.py` (Task T012) when the primary defect dataset is missing or invalid.

## Public API Surface

### `generate_synthetic_train_dataset(n_samples: int, seed: int = 42) -> pd.DataFrame`

Generates the primary training dataset using analytical continuum mechanics.

**Parameters**:
- `n_samples` (int): Number of synthetic entries to generate. Recommended: ≥100.
- `seed` (int): Random seed for reproducibility. Default: 42.

**Returns**:
- `pd.DataFrame`: A DataFrame containing synthetic defect data with the following columns:
 - `defect_type`: Categorical (e.g., "vacancy", "grain_boundary", "adatom")
 - `defect_density`: Float in range [0.001, 0.1]
 - `conductivity`: Float (normalized relative to pristine)
 - `youngs_modulus`: Float (normalized relative to pristine)
 - `fracture_energy`: Float (normalized relative to pristine)
 - `data_source`: String literal `'synthetic'`
 - `version`: Git hash string for versioning

**Physics Model**:
- **Conductivity**: Modeled via Matthiessen's rule, reducing conductivity linearly with defect density.
- **Young's Modulus**: Modeled via Rule of Mixtures, assuming linear degradation.
- **Fracture Energy**: Modeled via Griffith criterion, scaling with the square root of defect density.

**Example**:
```python
from src.generators.synthetic_data_generator import generate_synthetic_train_dataset

df = generate_synthetic_train_dataset(n_samples=100, seed=42)
df.to_csv("data/raw/synthetic_train.csv", index=False)
```

---

### `generate_synthetic_holdout_dataset(n_samples: int, train_data: pd.DataFrame, seed: int = 42) -> pd.DataFrame`

Generates a hold-out dataset using a Gaussian Process Surrogate trained on a distinct set of physical parameters to emulate a "Distinct Physics Engine".

**Parameters**:
- `n_samples` (int): Number of synthetic hold-out entries to generate.
- `train_data` (pd.DataFrame): The training dataset used to fit the GP surrogate.
- `seed` (int): Random seed for reproducibility. Default: 42.

**Returns**:
- `pd.DataFrame`: A DataFrame similar to `generate_synthetic_train_dataset` but with properties predicted by the GP surrogate, ensuring statistical independence from the primary analytical model.

**Note**: This mode triggers "Method Validation" scope shift per Plan's Critical Scope Limitation. Claims derived from this data are restricted to internal consistency checks.

---

### `get_git_hash() -> str`

Retrieves the current Git commit hash for versioning the generated data.

**Returns**:
- `str`: The 7-character abbreviated Git hash. If not in a Git repository, returns `"unknown"`.

---

## Output Specifications

All generated files must adhere to the following schema:

| Column | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `defect_type` | str | Type of defect | Non-null, categorical |
| `defect_density` | float | Defect density | ∈ [0.001, 0.1], > 0 |
| `conductivity` | float | Relative conductivity | > 0, ≤ 1.0 |
| `youngs_modulus` | float | Relative Young's Modulus | > 0, ≤ 1.0 |
| `fracture_energy` | float | Relative Fracture Energy | > 0 |
| `data_source` | str | Data origin | `'synthetic'` |
| `version` | str | Git hash | Non-empty string |

## Integration with Workflow

The generator is integrated into the main acquisition pipeline (`code/01_data_acquisition.py`):

1. **Attempt Real Data**: The pipeline first attempts to download the 2022 Supplementary Defect Dataset.
2. **Validation Check**: If the download fails or the data is invalid (missing columns, zero rows), the pipeline invokes the synthetic generator.
3. **Fallback Generation**:
 - `generate_synthetic_train_dataset` is called to create `data/raw/synthetic_train.csv`.
 - If a hold-out set is required for validation, `generate_synthetic_holdout_dataset` is called to create `data/raw/synthetic_holdout.csv`.
4. **State Recording**: The `data_source` flag and `version` (Git hash) are recorded in the project state file (`state/projects/PROJ-209-...yaml`) via `scripts/update_state_hashes.py`.

## Dependencies

- `numpy`
- `pandas`
- `scikit-learn` (for Gaussian Process)
- `gitpython` (optional, for robust Git hash retrieval)

## Error Handling

- **Missing Git**: If the Git repository is not initialized, the `version` field is set to `"unknown"`.
- **Invalid Parameters**: If `n_samples` < 1 or `defect_density` bounds are violated, a `ValueError` is raised.
- **GP Convergence**: If the Gaussian Process fails to converge during hold-out generation, the pipeline falls back to a secondary analytical model with perturbed parameters.