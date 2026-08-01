# Data Model: Assessing Dataset Imbalance Effects on Materials Property Predictions

## 1. Entity Definitions

### MaterialEntry
Represents a single material record.
- `material_id`: Unique identifier (string).
- `composition`: Chemical formula (string, e.g., "Fe2O3").
- `targets`: Dictionary mapping property names to values (e.g., `{"formation_energy": -2.5, "band_gap": 1.2}`).
- `descriptors`: List of 14 float values (Magpie features, L2-normalized).
- `source`: String ("OQMD", "AFLOW", "MP").
- `metadata`: Dictionary for additional context (e.g., `{"space_group": 225}`).

### ImbalanceMetrics
Derived metrics for a dataset or subset.
- `dataset_id`: Identifier for the dataset version.
- `compositional_coverage_score`: Float (Normalized Convex Hull Volume of Magpie space).
- `compositional_density_score`: Float (Mean nearest-neighbor distance).
- `target_imbalance_scores`: Dictionary mapping property name to Gini coefficient.
- `sample_count`: Integer.
- `minority_subset_count`: Integer (count of samples in bottom [deferred]).

### ModelArtifact
Container for trained model and metadata.
- `model_id`: UUID.
- `strategy`: String ("skewed", "balanced_undersampled", "cost_sensitive").
- `model_type`: String ("RandomForest", "GradientBoosting").
- `hyperparameters`: Dictionary of hyperparameters used.
- `random_seed`: Integer.
- `performance_metrics`: Dictionary (MAE, RMSE, R² for full and minority subsets).
- `feature_importance`: Dictionary mapping feature name to importance score.
- `shap_values`: Array of floats (if computed).

### SHAPComparison
Comparison result for feature importance.
- `comparison_id`: UUID.
- `skewed_model_id`: Reference to ModelArtifact.
- `balanced_model_id`: Reference to ModelArtifact.
- `feature_rank_delta`: Dictionary mapping feature name to rank shift (int).
- `top_10_skewed`: List of feature names.
- `top_10_balanced`: List of feature names.
- `mean_rank_shift`: Float.

### SyntheticGroundTruth
Generated dataset for validation.
- `synthetic_id`: UUID.
- `feature_weights`: Dictionary mapping feature name to true weight (float) — **Non-linear function parameters**.
- `noise_level`: Float.
- `sample_count`: Integer.
- `physical_constraints`: Dictionary (e.g., `{"charge_balance": true}`).

## 2. Data Flow

1. **Ingestion**: Raw CSV/Parquet -> `MaterialEntry` (raw).
2. **Processing**: `MaterialEntry` (raw) -> `MaterialEntry` (with descriptors).
3. **Imbalance Calc**: `MaterialEntry` (processed) -> `ImbalanceMetrics`.
4. **Resampling**: `MaterialEntry` (processed) -> `MaterialEntry` (balanced_undersampled) or `ModelArtifact` (cost_sensitive).
5. **Training**: `MaterialEntry` (balanced/skewed) -> `ModelArtifact`.
6. **Evaluation**: `ModelArtifact` + Test Set -> `ModelArtifact` (with metrics).
7. **SHAP**: `ModelArtifact` -> `SHAPComparison`.

## 3. Storage Schema

- **Raw Data**: `data/raw/<source>_<timestamp>.parquet`
- **Processed Data**: `data/processed/merged_<timestamp>.parquet`
- **Balanced Data**: `data/processed/balanced_<strategy>_<timestamp>.parquet`
- **Models**: `artifacts/models/<model_id>.pkl`
- **Results**: `results/metrics_<timestamp>.csv`, `results/shap_<timestamp>.json`
- **State**: `state/projects/PROJ-756-...yaml`

## 4. Constraints

- **Max Dataset Size**: 5 GB (enforced during ingestion).
- **Min Samples per Property**: 100 (skip if lower).
- **Synthetic Data Cap**: N/A (SMOTE excluded).
- **Undersampling Constraint**: If bin size < 100, switch to Cost-Sensitive.