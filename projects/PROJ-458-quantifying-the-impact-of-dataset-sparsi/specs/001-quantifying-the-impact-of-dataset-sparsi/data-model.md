# Data Model: Quantify Dataset Sparsity Impact

## 1. Entities

### 1.1 MaterialEntry
Represents a single material structure.
*   `material_id`: Unique identifier (string).
*   `composition`: Dict of element -> count (e.g., `{"Fe": 2, "O": 3}`).
*   `formation_energy_per_atom`: Target variable (float, eV/atom).
*   `descriptors`: Dict of derived features (floats).
*   `source`: "MaterialsProject" or "Local".

### 1.2 FixedTestSet
Represents the static holdout set used for all evaluations.
*   `test_set_id`: Unique identifier (e.g., "fixed_test_2024").
*   `material_ids`: List of `material_id`s included (list of strings).
*   `fraction`: Proportion of full dataset (e.g., 0.20).
*   `source`: "MaterialsProject" or "Local".
*   `checksum`: SHA256 hash of the file content.

### 1.3 SparsitySubset
Represents a specific training split.
*   `subset_id`: Unique identifier (string).
*   `sparsity_level`: Percentage of the 30k RSS (float, e.g., 0.05, 0.10).
*   `seed`: Random seed used (int).
*   `material_ids`: List of `material_id`s included (list of strings).
*   `stratification_method`: "kmeans_fingerprint".
*   `validation_status`: "passed" or "failed" (based on JS divergence/KS-test).

### 1.4 PerformanceMetric
Represents the result of a model evaluation.
*   `run_id`: Unique identifier.
*   `model_type`: "GPR" or "RF".
*   `subset_id`: Link to `SparsitySubset`.
*   `test_set_id`: Link to `FixedTestSet`.
*   `seed`: Random seed.
*   `metric_type`: "RMSE", "MAE", "CalibrationSlope", "PredictiveVariance".
*   `value`: Float.
*   `std_dev`: Float (across CV folds).

## 2. Data Flow

1.  **Ingestion**: `MaterialsProject` API -> `raw/mp_data.csv` (MaterialEntry).
2.  **Test Split**: `raw/mp_data.csv` -> `processed/test_set.csv` (FixedTestSet) AND `processed/training_pool.csv` (30k RSS).
3.  **Preprocessing**: `training_pool.csv` -> `processed/descriptors.csv` (MaterialEntry + Descriptors).
4.  **Subsampling**: `processed/descriptors.csv` + `config/sparsity_levels.json` -> `processed/subset_<id>.csv` (SparsitySubset).
5.  **Validation**: Run stratification validation on `subset_<id>.csv`. If failed, regenerate.
6.  **Training**: `subset_<id>.csv` -> `models/<model_type>_<subset_id>.pkl`.
7.  **Evaluation**: `models/*.pkl` + `processed/test_set.csv` -> `results/metrics.csv` (PerformanceMetric).
8.  **Analysis**: `results/metrics.csv` -> `results/statistical_summary.json`.

## 3. File Formats

*   **Input/Output**: CSV (comma-separated, UTF-8).
*   **Models**: Pickle (`.pkl`) - versioned.
*   **Metadata**: JSON.
*   **Plots**: PNG (high resolution).

## 4. Constraints & Validation

*   **Formation Energy**: Must be non-null.
*   **Descriptors**: Must be non-null. Imputation (mean) applied if missing, logged.
*   **Sparsity Levels**: Must be percentages of the 30k RSS (not full 150k).
*   **Memory**: No single file > 2GB.
*   **Test Set Independence**: The `test_set_id` must be distinct from any `subset_id`.