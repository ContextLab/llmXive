# Data Model: Quantifying Calibration Drift of Machine Learning Classifiers Over Time

## 1. Overview
This document defines the data structures used to store raw inputs, intermediate processing artifacts, and final analysis results. All data is stored in CSV or JSONL format to ensure portability and reproducibility.

## 2. Entity Definitions

### 2.1 DatasetSnapshot
Represents a specific yearly version of a benchmark dataset.
- **Attributes**:
  - `snapshot_id`: Unique identifier (e.g., `cps_1994`).
  - `dataset_name`: Source name (e.g., `IPUMS_CPS`, `Synthetic_Drift`).
  - `year`: Integer year of the snapshot.
  - `path`: Relative path to the raw CSV file in `data/raw/`.
  - `checksum`: SHA-256 hash of the file.
  - `feature_columns`: List of column names (after schema alignment).
  - `target_column`: Name of the target variable.

### 2.2 FixedModel
Represents a serialized classifier trained on the earliest snapshot.
- **Attributes**:
  - `model_id`: Unique identifier (e.g., `lr_cps_1994`).
  - `algorithm`: Type (e.g., `LogisticRegression`, `RandomForest`).
  - `training_snapshot_id`: ID of the snapshot used for training.
  - `path`: Relative path to the serialized model (`.pkl` or `.joblib`).
  - `hyperparameters`: JSON string of the model's config (defaults).

### 2.3 CalibrationMetricRecord
A single data point representing the evaluation of a fixed model on a specific year's test set.
- **Attributes**:
  - `record_id`: Unique identifier.
  - `model_id`: FK to `FixedModel`.
  - `test_snapshot_id`: FK to `DatasetSnapshot`.
  - `year`: Integer year.
  - `ece_10`: Expected Calibration Error (10 bins).
  - `ece_5`: Expected Calibration Error (5 bins).
  - `ece_20`: Expected Calibration Error (20 bins).
  - `brier_score`: Brier Score.
  - `pca_shift`: Covariate shift magnitude (Euclidean distance of PCA-projected means).
  - `key_feature_shift`: Covariate shift magnitude (Average absolute mean shift of key features).
  - `n_samples`: Number of samples in the test set.

### 2.4 DriftAnalysisResult
Aggregated statistical results for a specific model-dataset pair.
- **Attributes**:
  - `analysis_id`: Unique identifier.
  - `model_id`: FK to `FixedModel`.
  - `dataset_name`: Source name.
  - `trend_slope`: Float (slope of Year vs. ECE).
  - `trend_p_value`: Float (p-value for slope).
  - `trend_intercept`: Float.
  - `correlation_rho`: Spearman correlation (Shift vs. Error).
  - `correlation_p_value`: Float.
  - `change_point_years`: List of integers (detected change points).
  - `change_point_confidence`: Float (confidence interval).
  - `robustness_check`: Boolean (True if correlation stable across binning).

## 3. Data Flow

1. **Ingestion**: Raw CSVs downloaded to `data/raw/` -> `DatasetSnapshot` metadata generated.
2. **Training**: Earliest snapshot -> `FixedModel` saved to `data/models/`.
3. **Evaluation**: Loop through years -> `CalibrationMetricRecord` appended to `data/processed/metrics.csv`.
4. **Analysis**: `metrics.csv` -> `DriftAnalysisResult` saved to `data/processed/results.json`.
5. **Reporting**: `results.json` -> Markdown report.

## 4. Storage Constraints
- **Raw Data**: Stored as CSV. Checksums recorded in `state/`.
- **Models**: Stored as `.joblib` (binary).
- **Metrics**: Stored as CSV for easy plotting and statistical analysis.
- **Max Size**: All intermediate files combined < 1GB.