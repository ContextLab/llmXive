# Architecture Documentation

## System Overview

The Feature Importance Drift Analysis Pipeline is a modular Python application designed to detect and quantify statistical drift in feature importance rankings over time. The system processes time-series data in sequential windows, trains machine learning models, and applies statistical tests to identify significant changes in feature importance.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Input Data Source │
│ (UCI Electricity Load Diagrams) │
└───────────────────────────┬─────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Download Module │
│ (code/download.py) │
│ - Fetches dataset from UCI archive │
│ - Verifies file integrity │
└───────────────────────────┬─────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Preprocessing Module │
│ (code/preprocess.py) │
│ - Handles missing values (median imputation) │
│ - Checks feature variance │
│ - Splits data into 30-day windows │
└───────────────────────────┬─────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Model Training Module │
│ (code/train_and_importance.py) │
│ - Trains Random Forest Regressor per window │
│ - Validates R² performance (threshold: 0.8) │
│ - Calculates permutation importance │
└───────────────────────────┬─────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Importance Profiles Output │
│ (outputs/importance_profiles.csv) │
└───────────────────────────┬─────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Drift Analysis Module │
│ (code/drift_analysis.py) │
│ - Computes Spearman rank correlation │
│ - Generates pairwise drift metrics │
│ - Creates null baseline (shuffled windows) │
└───────────────────────────┬─────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Significance Testing Module │
│ (code/significance_test.py) │
│ - Mann-Kendall trend test │
│ - Block permutation test │
└───────────────────────────┬─────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Final Report Generation │
│ (code/generate_final_report.py) │
│ - Aggregates all metrics │
│ - Produces global statistics │
└─────────────────────────────────────────────────────────────────┘
```

## Module Descriptions

### 1. Download Module (`code/download.py`)

**Purpose**: Fetch and verify the UCI Electricity Load Diagrams dataset.

**Key Functions**:
- `download_file()`: Downloads dataset from UCI archive
- `verify_dataset()`: Validates file integrity via hash
- `calculate_file_hash()`: Computes SHA256 hash

**Dependencies**: `requests`, `hashlib`

### 2. Preprocessing Module (`code/preprocess.py`)

**Purpose**: Clean and prepare data for model training.

**Key Functions**:
- `load_raw_dataset()`: Loads and parses the dataset
- `handle_missing_values()`: Median imputation
- `check_variance()`: Identifies and drops zero-variance features
- `split_into_windows()`: Creates sequential 30-day windows

**Dependencies**: `pandas`, `numpy`

### 3. Model Training Module (`code/train_and_importance.py`)

**Purpose**: Train models and compute feature importance.

**Key Functions**:
- `train_model()`: Fits Random Forest Regressor
- `evaluate_model()`: Computes R² score
- `validate_model_performance()`: Checks against R² threshold
- `calculate_importance()`: Permutation importance calculation

**Dependencies**: `scikit-learn`, `numpy`

### 4. Drift Analysis Module (`code/drift_analysis.py`)

**Purpose**: Quantify drift between consecutive windows.

**Key Functions**:
- `calculate_rank_correlation()`: Spearman correlation
- `compute_pairwise_drift()`: T vs T+1 comparison
- `load_null_baseline()`: Loads shuffled baseline
- `flag_high_drift()`: Identifies significant drift events

**Dependencies**: `scipy`, `pandas`

### 5. Significance Testing Module (`code/significance_test.py`)

**Purpose**: Statistical validation of drift trends.

**Key Functions**:
- `mann_kendall_test()`: Trend detection
- `block_permutation_test()`: Significance testing
- `load_correlation_sequence()`: Loads drift metrics

**Dependencies**: `scipy`, `numpy`

### 6. Null Baseline Module (`code/null_baseline.py`)

**Purpose**: Generate baseline distribution for significance testing.

**Key Functions**:
- `shuffle_windows_and_compute_rho()`: Randomizes window order
- `run_null_baseline()`: Executes multiple shuffled runs

**Dependencies**: `random`, `numpy`

### 7. Final Report Module (`code/generate_final_report.py`)

**Purpose**: Aggregate and serialize final results.

**Key Functions**:
- `aggregate_global_stats()`: Computes summary statistics
- `save_final_report()`: Writes JSON report

**Dependencies**: `json`, `pandas`

### 8. Pipeline Orchestration (`code/main.py`)

**Purpose**: Coordinate the end-to-end pipeline execution.

**Key Functions**:
- `run_pipeline()`: Orchestrates all modules
- `process_window()`: Handles individual window processing

## Data Flow

1. **Raw Data**: Downloaded from UCI archive → `data/raw/`
2. **Processed Windows**: Cleaned and windowed data → `data/processed/`
3. **Importance Profiles**: Per-window importance scores → `outputs/importance_profiles.csv`
4. **Drift Metrics**: Pairwise correlations → `outputs/drift_metrics.csv`
5. **Null Baseline**: Shuffled correlation distribution → `outputs/null_baseline.json`
6. **Global Stats**: Aggregated results → `outputs/global_stats.json`

## Configuration

All configuration is managed through `code/utils/config.py`:

- **Window Size**: 30 days (configurable)
- **Model Parameters**: Random Forest with n_estimators=100, max_depth=10
- **R² Threshold**: 0.8 (minimum acceptable performance)
- **Permutation Resamples**: 1000 (for significance testing)
- **Block Size**: 5 (for block permutation test)

## Logging

Logging is configured via `code/utils/logger.py`:

- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Output**: Console (stdout) and optional file
- **Format**: `timestamp - logger - level - message`

## Error Handling

- **Missing Data**: Logs warning, skips affected features
- **Model Failure**: Skips windows with R² < threshold, logs failure
- **Zero Variance**: Drops features with no variance per window
- **Small Samples**: Uses permutation tests when n < 10

## Extensibility

The modular design allows for:

- Adding new data sources
- Implementing alternative drift metrics
- Extending statistical tests
- Custom model architectures (within CPU constraints)
