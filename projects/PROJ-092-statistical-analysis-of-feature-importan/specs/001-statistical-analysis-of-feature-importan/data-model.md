# Data Model: Statistical Analysis of Feature Importance Drift

## 1. Overview

This document defines the data structures, schemas, and transformation logic for the feature importance drift analysis. The system operates on a stream of time-series data, converting it into windowed datasets, model profiles, and statistical metrics.

## 2. Entity Definitions

### 2.1 TimeWindow
A slice of the raw dataset representing a specific 30-day period.
- **Attributes**:
  - `window_id`: Unique integer identifier (0, 1, 2...).
  - `start_timestamp`: ISO 8601 datetime of the first hour.
  - `end_timestamp`: ISO 8601 datetime of the last hour.
  - `data_path`: Relative path to the CSV file containing the windowed data.
  - `feature_count`: Number of features retained after zero-variance filtering.

### 2.2 ImportanceProfile
The output of the Random Forest model for a specific window.
- **Attributes**:
  - `window_id`: Link to `TimeWindow`.
  - `timestamp_start`: ISO 8601 start time.
  - `timestamp_end`: ISO 8601 end time.
  - `feature_names`: List of strings (feature names).
  - `importance_scores`: List of floats (permutation importance values).
  - `rank`: List of integers (1-based rank, 1 = most important).
  - `model_r2`: Float (average $R^2$ score from 5 bootstrap runs on validation set).
  - `status`: String ("SUCCESS", "FAILED").

### 2.3 DriftMetric
The result of comparing two consecutive `ImportanceProfile`s.
- **Attributes**:
  - `transition_id`: Integer (e.g., 0->1, 1->2).
  - `window_t`: Integer (source window).
  - `window_t_plus_1`: Integer (target window).
  - `spearman_rho`: Float (correlation coefficient).
  - `is_high_drift`: Boolean (True if p-value < 0.05).

### 2.4 GlobalStats
Aggregated results for the entire time series.
- **Attributes**:
  - `kendall_tau`: Float (trend direction).
  - `permutation_p_value`: Float (significance).
  - `trend_direction`: String ("increasing", "decreasing", "no trend").
  - `total_windows`: Integer.
  - `valid_windows`: Integer (after R² filter).

## 3. Data Flow

1. **Raw Data** (CSV) $\rightarrow$ **Preprocessing** (Imputation) $\rightarrow$ **Windowed Data** (CSVs).
2. **Windowed Data** $\rightarrow$ **Model Training** $\rightarrow$ **ImportanceProfile** (CSV/JSON).
3. **ImportanceProfiles** $\rightarrow$ **Drift Analysis** $\rightarrow$ **DriftMetric** (CSV).
4. **DriftMetrics** $\rightarrow$ **Significance Test** $\rightarrow$ **GlobalStats** (JSON).

## 4. File Formats

### 4.1 Input: `data/raw/electricity_load.csv`
- **Format**: CSV.
- **Columns**: `timestamp`, `MZ1`, `MZ2`, ..., `MZ321`.
- **Encoding**: UTF-8.

### 4.2 Intermediate: `data/processed/window_{id}.csv`
- **Format**: CSV.
- **Columns**: `timestamp`, `MZ1`, ..., `MZ321` (subset if dropped).
- **Note**: Contains only data for the specific 30-day window.

### 4.3 Output: `outputs/importance_profiles.csv` (Primary SSoT for Rankings)
- **Format**: CSV.
- **Columns**: `window_id`, `timestamp_start`, `timestamp_end`, `feature`, `importance_score`, `rank`.
- **Purpose**: Satisfies FR-006 requirement for "feature importance rankings".

### 4.4 Output: `outputs/drift_metrics.csv` (Primary SSoT for Metrics)
- **Format**: CSV.
- **Columns**: `window_t`, `window_t_plus_1`, `spearman_rho`, `p_value`, `is_high_drift`.

### 4.5 Output: `outputs/global_stats.json` (Derived Summary)
- **Format**: JSON.
- **Structure**:
  ```json
  {
    "kendall_tau": 0.0,
    "permutation_p_value": 0.0,
    "trend_direction": "string",
    "total_windows": 0,
    "valid_windows": 0
  }
  ```