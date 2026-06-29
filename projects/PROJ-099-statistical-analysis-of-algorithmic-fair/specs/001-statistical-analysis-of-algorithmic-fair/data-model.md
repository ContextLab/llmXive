# Data Model: Statistical Analysis of Algorithmic Fairness Metrics

## Entities

### Dataset
Represents a public dataset with protected attribute, outcome, and feature columns.
- **Attributes**: `dataset_id`, `source_url`, `row_count`, `feature_count`, `base_rate`, `base_rate_diff`, `class_imbalance_ratio`, `checksum_sha256`.
- **Storage**: `data/processed/{dataset_id}.parquet`.

### Model
Represents a trained baseline classifier.
- **Attributes**: `model_id`, `dataset_id`, `algorithm` (LogReg, RF, GB), `random_seed`, `train_test_split_seed`.
- **Storage**: `code/analysis/` (logic only, weights not persisted to save space).

### FairnessMetric
Represents a computed fairness metric value.
- **Attributes**: `metric_id`, `dataset_id`, `model_id`, `metric_name`, `value`, `failure_reason`, `timestamp`.
- **Storage**: `data/analysis/metrics.csv`.

### DatasetCharacteristic
Represents a dataset property used in regression.
- **Attributes**: `dataset_id`, `base_rate_diff`, `feature_dim`, `imbalance_ratio`, `vif_base_rate`, `vif_imbalance`.
- **Storage**: `data/analysis/characteristics.csv`.

### CorrelationResult
Represents a pairwise correlation between fairness metrics.
- **Attributes**: `correlation_id`, `metric_1`, `metric_2`, `correlation_coefficient`, `p_value_raw`, `p_value_fdr`, `ci_lower`, `ci_upper`, `bootstrap_n`.
- **Storage**: `data/analysis/correlations.csv`.

### RegressionResult
Represents a regression coefficient from fixed-effects model.
- **Attributes**: `regression_id`, `outcome_metric`, `predictor`, `coefficient`, `std_error`, `p_value`, `p_value_fdr`, `ci_lower`, `ci_upper`, `vif`.
- **Storage**: `data/analysis/regression.csv`.

### BootstrapResult
Represents a bootstrap confidence interval for a correlation.
- **Attributes**: `bootstrap_id`, `metric_1`, `metric_2`, `ci_lower`, `ci_upper`, `resample_n`, `dataset_id`.
- **Storage**: `data/analysis/bootstrap_ci.csv`.

## Data Flow

1.  **Raw**: Downloaded CSV/Parquet from verified URLs → `data/raw/`.
2.  **Processed**: Preprocessed binary protected/outcome, sampled ≤100k rows → `data/processed/`.
3.  **Metrics**: Fairness metric values computed per model → `data/analysis/metrics.csv`.
4.  **Characteristics**: Dataset properties computed → `data/analysis/characteristics.csv`.
5.  **Analysis**: Correlation matrices, regression coefficients, bootstrap CIs → `data/analysis/`.
6.  **Viz**: Heatmaps, scatter plots saved to `data/analysis/figures/`.

## File Formats

- **Input**: CSV, Parquet.
- **Output**: CSV (metrics, characteristics, correlations, regression, bootstrap), PNG (figures).
- **Schema**: `contracts/fairness-metrics-output.schema.yaml`.

## Integrity

- **Checksums**: SHA-256 recorded in `state/projects/PROJ-099-statistical-analysis-of-algorithmic-fair.yaml`.
- **Versioning**: Content hashes for all artifacts in `data/`.
- **Logs**: Error logs in `data/processed/logs/` and `data/analysis/logs/`.
