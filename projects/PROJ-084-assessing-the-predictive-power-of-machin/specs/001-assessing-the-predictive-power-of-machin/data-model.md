# Data Model: Assessing the Predictive Power of Machine Learning for Organic Reaction Outcomes

## Entities & Relationships

### Reaction
The core entity representing a single chemical transformation.
- **Attributes**:
  - `id`: Unique identifier (UUID or hash of SMILES).
  - `reactants_smiles`: List of SMILES strings for reactants.
  - `reagents_smiles`: List of SMILES strings for reagents.
  - `yield_value`: Float (0.0 - 100.0).
  - `reaction_class`: String (e.g., "Suzuki", "Amide Formation").
  - `scaffold`: String (Murcko scaffold string).
  - `ecfp4_vector`: Binary array (2048 bits).
  - `maccs_vector`: Binary array (167 bits).

### ModelConfiguration
Stores the hyperparameters and metadata for a trained model.
- **Attributes**:
  - `model_type`: String ("RandomForest", "SVM").
  - `hyperparameters`: JSON object (e.g., `{"n_estimators": 100, "max_depth": 10}`).
  - `cv_score`: Float (Mean R² from cross-validation).
  - `training_set_size`: Integer.

### PerformanceMetric
Stores evaluation results for a specific model and dataset split.
- **Attributes**:
  - `model_id`: Reference to `ModelConfiguration`.
  - `dataset_split`: String ("train", "val", "test").
  - `r_squared`: Float.
  - `rmse`: Float.
  - `mae`: Float.
  - `reaction_class`: String (if per-class).

## Data Flow

1. **Raw Ingestion**: `data/raw/uspto_yield.parquet` -> `preprocessing/sanitize.py` -> `data/processed/sanitized.parquet`
2. **Feature Engineering**: `sanitized.parquet` -> `preprocessing/fingerprints.py` -> `data/processed/with_fingerprints.parquet`
3. **Subset Creation**: `with_fingerprints.parquet` -> `modeling/split.py` -> `data/processed/subset_train.parquet` (Fixed Representative Subset), `val.parquet`, `test.parquet`
4. **Training**: `subset_train.parquet` -> `modeling/train.py` -> `data/results/models/` (pickle files) + `data/results/metrics.json`
5. **Analysis**: `models/` + `test.parquet` -> `modeling/evaluate.py` -> `data/results/feature_importance.json`, `data/results/per_class_metrics.json`

## Storage Strategy

- **Parquet**: Used for all intermediate and final datasets due to efficient columnar storage and compression.
- **Pickle**: Used for serialized scikit-learn models (`.pkl`).
- **JSON**: Used for metrics and configuration logs.
- **Checksums**: SHA-256 hashes recorded for all files in `data/raw` and `data/processed` (including `subset_train.parquet`) in the project state file.

## Constraints

- **Memory**: Data frames must be chunked if > 500MB.
- **Precision**: Yield values stored as `float32` to save space; metrics calculated in `float64`.
- **Immutability**: `data/raw` files are never modified. All transformations create new files.
