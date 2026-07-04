# Data Model: Predicting Material Stability using Machine Learning and DFT Calculations

## Entities

### MaterialEntry
Represents a single compound in the OQMD dataset.
- `material_id`: Unique identifier (string).
- `composition`: Chemical formula (string).
- `structure`: Crystal structure object (JSON representation of lattice vectors and atomic positions).
- `formation_energy_per_atom`: DFT ground truth energy (float, eV/atom).
- `distance_to_hull`: Calculated distance to convex hull (float, eV/atom).
- `is_stable`: Boolean (True if `distance_to_hull` == 0.0).
- `is_metastable`: Boolean (True if `0.0 < distance_to_hull <= threshold`).
- `is_near_hull`: Boolean (True if `0.0 < distance_to_hull <= 0.05`).

### FeatureVector
Numerical representation of a material for ML models.
- `magpie_features`: Dictionary of bulk compositional descriptors (floats).
- `voronoi_stats`: Dictionary of Voronoi tessellation metrics (coordination number, face area, etc.) (floats).
- `bond_length_histograms`: Dictionary of bond length distributions (list of floats).
- `combined_features`: Concatenated vector of all above (list of floats).
- `collinearity_vif`: Dictionary of Variance Inflation Factors for each feature (floats).

### ModelPerformance
Aggregated metrics for a trained model.
- `model_type`: "baseline" or "augmented".
- `mae`: Mean Absolute Error (float).
- `rmse`: Root Mean Squared Error (float).
- `r2`: R-squared score (float).
- `auc_roc`: Area Under ROC Curve for metastability classification (float).
- `auc_roc_near_hull`: Area Under ROC Curve specifically for the Near-Hull cohort (float).
- `training_time`: Time taken to train (float, seconds).
- `p_value_permutation`: P-value from the permutation test on MAE reduction (float).

## Data Flow

1. **Raw Data**: Downloaded OQMD files (CSV/TAR/Parquet) stored in `data/raw/`.
2. **Filtered Data**: Subset of Li-rich rock-salt structures (topological criteria) stored in `data/processed/filtered_oqmd.parquet`.
3. **Featurized Data**: `filtered_oqmd.parquet` augmented with feature vectors stored in `data/processed/featurized_data.parquet`.
4. **Model Artifacts**: Trained `.pkl` files stored in `data/models/`.
5. **Results**: Metrics and plots stored in `outputs/`.

## Schema Definitions

See `contracts/` for formal schema definitions.