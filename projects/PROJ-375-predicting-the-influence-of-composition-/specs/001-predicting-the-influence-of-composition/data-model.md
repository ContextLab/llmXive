# Data Model: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Entities

### MetallicGlassEntry
Represents a single alloy sample.
- `composition`: string (e.g., "Zr50Cu40Al10")
- `cte`: float (Coefficient of Thermal Expansion, 1/K)
- `atomic_radius_mean`: float (Weighted mean)
- `electronegativity_var`: float
- `vec`: float (Valence Electron Concentration)
- `size_mismatch`: float (Original, coupled feature)
- `size_mismatch_resid`: float (Orthogonalized feature for linear models)
- `alloy_family`: string (e.g., "Zr-based")
- `source`: string (e.g., "zenodo", "materials_project", "aflow")
- `is_amorphous`: boolean
- `vif_score`: float (Optional, for linear model collinearity check)
- `stability_score`: float (Optional, for feature importance stability)

### ModelPerformance
Represents evaluation results.
- `model_type`: string (e.g., "linear", "random_forest", "baseline_weighted_avg")
- `r2`: float
- `mae`: float
- `rmse`: float
- `p_value`: float (from permutation test)
- `is_significant`: boolean (based on p < 0.05, not R² threshold)
- `divergence_score`: float (Difference between importance rank and correlation rank, descriptive only)
- `stability_score`: float (Average stability across bootstraps)

### FeatureImportance
Represents ranked features.
- `feature_name`: string
- `importance_score`: float
- `correlation_coefficient`: float
- `rank`: integer
- `vif_score`: float (if applicable)
- `stability_score`: float (from bootstrapping)

## Data Flow

1.  **Ingestion**: Raw data fetched from Zenodo -> `data/raw/zenodo_mg.parquet`
2.  **Cleaning**: Filter for amorphous, valid CTE -> `data/processed/clean_mg_data.parquet`
3.  **Feature Engineering**: Calculate descriptors + **Orthogonalization** -> `data/processed/clean_mg_data_with_features.parquet` (includes `size_mismatch_resid`)
4.  **Splitting**: 60/20/20 Split (Train/Val/Test) -> `data/processed/train_split.parquet`, `data/processed/val_split.parquet`, `data/processed/test_split.parquet`
5.  **Modeling**: Training -> `results/metrics.csv`, `results/feature_importance.csv`
6.  **Analysis**: Stability Analysis + Divergence Analysis -> `results/divergence.csv`, `results/correlations.csv`, `results/stability.csv`

## Constraints

- **Data Integrity**: No in-place modification. All transformations create new files.
- **Checksums**: All files in `data/` must have a corresponding `.sha256` hash.
- **Schema Validation**: All Parquet files must conform to `contracts/mg_dataset.schema.yaml`.
- **Collinearity**: **Orthogonalization** must be applied to `size_mismatch` before linear models. VIF scores must be calculated for linear models.
- **Split**: 3-way split (Train/Val/Test) must be used to satisfy SC-003.
  - **Validation Set**: Used for SC-003 Stability Analysis and tuning.
  - **Test Set**: Used for final R²/MAE reporting.
