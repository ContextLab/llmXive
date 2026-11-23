# Data Model: Assessing the Stability of Statistical Model Performance Across Data Subsets

## Entities and Attributes

### 1. Dataset
Represents a single binary classification dataset used in the study.
- `dataset_id`: Unique identifier (e.g., "openml-1590").
- `source_url`: The URL or programmatic loader reference (e.g., `fetch_openml`).
- `n_samples`: Total number of samples in the dataset.
- `n_features`: Total number of features.
- `binary_target`: Boolean, indicating if the target is binary.
- `checksum`: SHA-256 hash of the raw file (for reproducibility).

### 2. EvaluationRun
Represents a single instance of model training and testing within a specific fold and repeat.
- `dataset_id`: Foreign key to Dataset.
- `model_name`: One of "LogisticRegression", "RandomForest", "LinearSVM".
- `fold_id`: Integer (0-9).
- `repeat_id`: Integer (0-9).
- `accuracy`: Float (0.0 - 1.0).
- `f1_score`: Float (0.0 - 1.0).
- `runtime_seconds`: Float (execution time).

### 3. StabilityMetric
Aggregated metrics for a (dataset, model) pair.
- `dataset_id`: Foreign key to Dataset.
- `model_name`: String.
- `mean_accuracy`: Float (average of 100 runs).
- `std_accuracy`: Float (standard deviation of 100 runs).
- `cv_accuracy`: Float ($\frac{std}{mean}$).
- `mean_f1`: Float.
- `std_f1`: Float.
- `cv_f1`: Float.

### 4. CorrelationResult
Result of the log-log correlation analysis between stability and dataset properties.
- `dataset_property`: "log_n_samples" or "log_n_features".
- `metric_type`: "log_cv_accuracy" or "log_cv_f1".
- `slope`: Float (beta_1 coefficient).
- `p_value`: Float (raw).
- `p_value_adjusted`: Float (Holm-Bonferroni adjusted).
- `significant`: Boolean (adjusted p < 0.05).
- `hypothesis_tested`: String (e.g., "H0: beta1 = -0.5").

### 5. PermutationResult
Result of the variance comparison test for a dataset.
- `dataset_id`: Foreign key to Dataset.
- `comparison_pair`: String (e.g., "LR_vs_RF", "RF_vs_SVM").
- `metric_type`: "accuracy" or "f1".
- `test_statistic`: Float (observed difference in variances).
- `p_value`: Float (raw).
- `p_value_adjusted`: Float (Holm-Bonferroni adjusted).
- `significant`: Boolean.

## Data Flow

1. **Ingestion**: `download_data.py` fetches datasets -> `data/raw/` (checksummed).
2. **Evaluation**: `run_evaluation.py` iterates datasets/models -> generates `results/raw_evaluations.csv` (EvaluationRun).
3. **Aggregation**: `analyze_stability.py` computes CVs -> `results/stability_metrics.csv` (StabilityMetric).
4. **Analysis**: `analyze_stability.py` computes log-log correlations and permutation tests -> `results/correlation_results.csv` and `results/permutation_results.csv`.
5. **Reporting**: `report_generator.py` aggregates all CSVs -> `docs/final_report.md`.

## Constraints

- **No Data Leakage**: Imputation and scaling parameters are fit on the training fold only.
- **Reproducibility**: All random seeds (numpy, sklearn) are set to a fixed integer (e.g., 42) at the start of the script.
- **Schema Validation**: Output CSVs must match the schema defined in `contracts/`.