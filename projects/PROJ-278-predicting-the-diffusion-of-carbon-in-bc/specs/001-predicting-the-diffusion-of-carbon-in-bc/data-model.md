# Data Model: Predicting the Diffusion of Carbon in BCC Metals from Compositional Data

## Entity Definitions

### DiffusionEntry
Represents a single experimental or computational measurement of carbon diffusion.
- **Source**: Derived from `MeLiDC` parquet.
- **Filter**: Only rows where `structure == "BCC"`, `solute == "C"`, and `microstructure_controlled` (or equivalent) is true.

### CompositionalDescriptor
Derived features calculated from the atomic composition of the alloy and temperature.
- **Calculation**: Weighted averages and variances of atomic properties, plus `1/T`.

### ModelResult
Output of the training pipeline.
- **Fields**: Model type, hyperparameters, metrics ($R^2$, RMSE, MAE), feature importances.

## Schema Definitions

### Input Data Schema (Raw)
The raw parquet file is expected to contain:
- `composition`: Dict or string of atomic fractions (e.g., `{"Fe": 0.9, "C": 0.1, ...}`).
- `structure`: String (e.g., "BCC", "FCC").
- `diffusion_coefficient`: Float (m²/s).
- `temperature`: Float (K).
- `microstructure_controlled`: Boolean (or equivalent flag).

### Processed Data Schema (Cleaned)
The `dataset_cleaned.csv` will contain:
- `atomic_radius_variance`: Float.
- `VEC`: Float.
- `electronegativity_spread`: Float.
- `mixing_entropy`: Float.
- `inv_temperature`: Float (1/K).
- `log_D`: Float ($\log_{10}$ of diffusion coefficient).
- `composition_str`: String (original composition for reference).

### Model Output Schema
The `model_results.json` will contain:
- `best_model`: String (e.g., "XGBoost").
- `metrics`: Object with `R2`, `RMSE`, `MAE`.
- `hyperparameters`: Object of tuned params.
- `feature_importance`: List of `{feature: str, value: float}`.

## Data Flow

1.  **Ingestion**: `raw/` parquet → `processed/` CSV (filtering + log-transform + provenance check).
2.  **Engineering**: `processed/` CSV → `processed/features.csv` (descriptor calculation including `1/T`).
3.  **Training**: `features.csv` → `outputs/model_results.json` + `outputs/shap_values.csv`.
4.  **Validation**: `outputs/` → `contracts/` schema validation.