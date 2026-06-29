# Data Model: Fairness Metric Divergence Analysis

## Overview

This document defines the data structures, schemas, and relationships used throughout the Fairness Metric Divergence Analysis pipeline.

## Entity Definitions

### Dataset

Represents a public ML dataset containing features, protected attributes, and outcomes.

| Attribute | Type | Description |
|-----------|------|-------------|
| dataset_id | string | Unique identifier (e.g., "compas_recidivism") |
| row_count | integer | Number of rows after preprocessing |
| feature_count | integer | Number of features used for modeling |
| protected_attribute_name | string | Name of the protected attribute column |
| protected_attribute_values | array | Binary values (e.g., [0, 1] or ["male", "female"]) |
| outcome_name | string | Name of the outcome column |
| checksum | string | SHA-256 checksum of raw file |

### Model

Represents a trained baseline classifier.

| Attribute | Type | Description |
|-----------|------|-------------|
| model_id | string | Unique identifier (e.g., "compas_lr_001") |
| model_type | string | Model class (e.g., "LogisticRegression", "RandomForest") |
| dataset_id | string | Foreign key to Dataset |
| training_parameters | object | Hyperparameters used for training |
| random_seed | integer | Random seed for reproducibility |

### FairnessMetric

Represents a computed fairness metric value.

| Attribute | Type | Description |
|-----------|------|-------------|
| metric_id | string | Unique identifier |
| metric_name | string | Name of the metric (e.g., "demographic_parity_difference") |
| metric_value | float | Computed value |
| metric_discrepancy | float | Absolute deviation from 0: |metric_value - 0| |
| model_id | string | Foreign key to Model |
| dataset_id | string | Foreign key to Dataset |
| protected_attribute | string | Protected attribute used for computation |
| confidence_interval_lower | float | Lower bound of 95% CI (if applicable) |
| confidence_interval_upper | float | Upper bound of 95% CI (if applicable) |

### DatasetCharacteristic

Represents a property of the dataset used for prediction.

| Attribute | Type | Description |
|-----------|------|-------------|
| characteristic_id | string | Unique identifier |
| characteristic_name | string | Name (e.g., "feature_dimensionality", "class_imbalance_ratio") |
| value | float | Numeric value |
| dataset_id | string | Foreign key to Dataset |

### CorrelationResult

Represents a pairwise correlation between fairness metrics.

| Attribute | Type | Description |
|-----------|------|-------------|
| correlation_id | string | Unique identifier |
| metric_1 | string | First metric name |
| metric_2 | string | Second metric name |
| correlation_coefficient | float | Pearson or Spearman correlation |
| p_value | float | Raw p-value |
| q_value | float | Benjamini-Hochberg corrected q-value |
| ci_lower | float | Bootstrap CI lower bound |
| ci_upper | float | Bootstrap CI upper bound |
| method | string | "pearson" or "spearman" |

### BootstrapResult

Represents bootstrap resampling results for correlation confidence intervals.

| Attribute | Type | Description |
|-----------|------|-------------|
| bootstrap_id | string | Unique identifier |
| correlation_id | string | Foreign key to CorrelationResult |
| iteration | integer | Bootstrap iteration number (1-1000) |
| resampled_coefficient | float | Correlation coefficient for this iteration |

### GuidanceRecord

Represents metric selection guidance mapping dataset characteristics to metric associations.

| Attribute | Type | Description |
|-----------|------|-------------|
| guidance_id | string | Unique identifier |
| characteristic_name | string | Dataset characteristic (e.g., "class_imbalance_ratio") |
| metric_name | string | Fairness metric name |
| association_strength | float | Correlation coefficient indicating association strength |
| association_direction | string | "positive" or "negative" |
| disclaimer | string | "Findings are associational only; no causal claims are made." |

## Data Flow

```
Raw Datasets (data/raw/)
    ↓ [01_data_acquisition.py]
Preprocessed Datasets (data/processed/)
    ↓ [02_preprocessing.py]
Trained Models (data/processed/models/)
    ↓ [03_model_training.py]
Fairness Metrics (data/analysis/metrics.csv)
    ↓ [04_fairness_metrics.py]
Correlation Results (data/analysis/correlations.csv)
    ↓ [05_correlation_analysis.py]
Bootstrap Results (data/analysis/bootstrap_results.csv)
    ↓ [07_bootstrap_analysis.py]
Regression Results (data/analysis/regression_results.csv)
    ↓ [06_regression_analysis.py]
Guidance Output (data/analysis/guidance.csv)
    ↓ [08_metric_guidance.py]
Final Report (paper/final_report.md)
```

## File Formats

### CSV Structure

All intermediate and final results are stored as CSV files with UTF-8 encoding.

### JSON Structure

Configuration files and model parameters are stored as JSON files.

### Log Format

Exclusion events logged to logs/exclusion.log in format:
```
{timestamp}|{dataset_id}|{reason}|{missing_variable_name}
```