# Data Model: Assessing Uncertainty Quantification Techniques

## Entity Relationship Overview

The system processes three main entities: `MaterialsDataset`, `UQMethod`, and `EvaluationMetric`.

### 1. MaterialsDataset
Represents a specific property dataset (Elastic Modulus, Band Gap, Thermal Conductivity).

| Field | Type | Description |
| :--- | :--- | :--- |
| `dataset_id` | `str` | Unique identifier (e.g., "elastic_modulus", "band_gap"). |
| `source_url` | `str` | URL from `# Verified datasets`. |
| `property_name` | `str` | Name of the target property. |
| `n_samples` | `int` | Total samples after loading. |
| `n_train` | `int` | Training set size. |
| `n_val` | `int` | Validation set size. |
| `n_test` | `int` | Test set size. |
| `features` | `list[str]` | List of feature column names. |
| `target` | `str` | Target column name. |

### 2. UQMethod
Represents a UQ technique and its configuration.

| Field | Type | Description |
| :--- | :--- | :--- |
| `method_id` | `str` | "gpr", "mc_dropout", "deep_ensemble", "conformal". |
| `baseline_model` | `str` | "xgboost", "mlp", "gpr_standalone". |
| `hyperparams` | `dict` | JSON-serializable hyperparameters (e.g., `{"n_estimators": 100}`). |
| `n_iterations` | `int` | Number of MC passes or ensemble size. |
| `status` | `str` | "success", "failed", "skipped". |
| `error_msg` | `str` | Error message if failed. |

### 3. EvaluationMetric
The result of a single UQ method on a specific dataset.

| Field | Type | Description |
| :--- | :--- | :--- |
| `dataset_id` | `str` | Foreign key to `MaterialsDataset`. |
| `method_id` | `str` | Foreign key to `UQMethod`. |
| `metric_type` | `str` | "calibration_error", "sharpness", "coverage_error". |
| `value` | `float` | Calculated scalar value. |
| `nominal_coverage` | `float` | Target coverage (e.g., 0.95) for interval metrics. |
| `timestamp` | `str` | ISO 8601 timestamp of calculation. |

### 4. StatisticalTestResult
Result of the significance test.

| Field | Type | Description |
| :--- | :--- | :--- |
| `dataset_id` | `str` | Dataset context. |
| `method_a` | `str` | First method. |
| `method_b` | `str` | Second method. |
| `metric_type` | `str` | "calibration_error" or "sharpness". |
| `p_value` | `float` | P-value from Welch's t-test or Mann-Whitney U. |
| `test_type` | `str` | "welch_t", "mann_whitney_u". |
| `significant` | `bool` | True if p < 0.05. |

## Data Flow

1. **Ingest**: `download.py` fetches raw CSV/Parquet from verified URLs.
2. **Preprocess**: `featurize.py` generates features (composition/structure) and splits data (Stratified by property).
3. **Train**: `models/` submodules train the baseline and apply UQ.
4. **Evaluate**: `metrics/evaluation.py` calculates Calibration Error and Sharpness.
5. **Analyze**: `stats/significance.py` performs pairwise tests.
6. **Output**: `results/summary.csv` aggregates all metrics.
