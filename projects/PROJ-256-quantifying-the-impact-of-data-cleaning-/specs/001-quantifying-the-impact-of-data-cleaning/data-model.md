# Data Model: Quantifying the Impact of Data Cleaning on Statistical Inference

## Overview
This document defines the data structures used for ingestion, processing, and output. All data is persisted in `data/` and `output/` directories.

## Entities

### 1. Dataset
Represents a raw dataset loaded from a verified source.
- `dataset_id`: Unique identifier (e.g., `uci_har`, `uci_shopper`).
- `source_url`: Verified URL string.
- `raw_path`: Path to raw file.
- `checksum`: SHA-256 hash of raw file.
- `sample_size`: Integer (n).
- `missingness_rate`: Float (0.0-1.0).
- `predictor_columns`: List[str].
- `outcome_column`: str.

### 2. CleaningStrategy
Represents a specific cleaning intervention.
- `strategy_id`: Unique identifier (e.g., `outlier_iqr_1.5`, `imp_mean`, `imp_knn_5`).
- `type`: Enum: `outlier_removal`, `imputation`, `recoding`.
- `parameters`: Dict (e.g., `{"k": 1.5}`).
- `rows_affected`: Integer (count removed or modified).

### 3. AnalysisResult
Statistical output for a specific (Dataset, Strategy) pair.
- `dataset_id`: str.
- `strategy_id`: str.
- `test_type`: Enum: `t_test`, `linear_regression`.
- `p_value`: Float.
- `ci_lower`: Float.
- `ci_upper`: Float.
- `effect_size`: Float (Cohen's d or R²).
- `sample_size_final`: Integer.

### 4. ComparisonReport
Aggregated differences between Baseline and Cleaned results.
- `dataset_id`: str.
- `strategy_id`: str.
- `p_value_diff`: Float (|p_cleaned - p_baseline|).
- `ci_width_change_pct`: Float.
- `effect_size_delta`: Float.
- `bootstrap_ci_lower`: Float.
- `bootstrap_ci_upper`: Float.

## Data Flow
1. **Ingest**: `data_loader.py` downloads and checksums raw files -> `Dataset`.
2. **Clean**: `cleaning.py` applies strategies -> `CleaningStrategy` + modified dataframes.
3. **Analyze**: `analysis.py` runs tests -> `AnalysisResult` (stored in JSON/Parquet).
4. **Compare**: `sensitivity.py` computes deltas and bootstraps -> `ComparisonReport`.
5. **Visualize**: `reporting.py` generates PNGs from `ComparisonReport`.
