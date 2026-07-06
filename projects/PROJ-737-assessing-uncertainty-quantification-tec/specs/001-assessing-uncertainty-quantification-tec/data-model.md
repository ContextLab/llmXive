# Data Model: Assessing Uncertainty Quantification Techniques

## Overview

This document defines the data schemas, model interfaces, and metric structures used in the project. All data flows through the `code/` directory and is validated against the schemas in `contracts/`.

## Entity Definitions

### 1. MaterialsDataset
Represents a specific property dataset.
- **Properties**:
  - `name`: String (e.g., "OQMD_BandGap")
  - `source_url`: String (Verified URL)
  - `property`: String (e.g., "band_gap")
  - `features`: List of strings (featurized columns)
  - `target`: String (column name for ground truth)
  - `split_indices`: Dict (keys: "train", "val", "test"; values: list of int)

### 2. UQMethod
Represents an uncertainty quantification technique.
- **Properties**:
  - `name`: String (e.g., "GPR", "MC_Dropout")
  - `config`: Dict (hyperparameters)
  - `model`: Object (trained model instance)
  - `prediction_intervals`: List of tuples (lower, upper)

### 3. EvaluationMetric
A record of a single metric calculation.
- **Properties**:
  - `dataset`: String
  - `method`: String
  - `metric_type`: String ("calibration_error", "sharpness")
  - `value`: Float
  - `nominal_coverage`: Float (e.g., 0.95)

## Data Flow

1.  **Ingestion**: Raw data downloaded from verified URLs → `data/raw/`.
2.  **Preprocessing**: `matminer` featurizers applied → `data/processed/`.
3.  **Splitting**: Stratified split by property range → `train`, `val`, `test`.
4.  **Modeling**: UQ methods trained on `train`, calibrated on `val` (for Conformal), tested on `test`.
5.  **Evaluation**: Metrics calculated on `test` → `data/results/metrics_summary.csv`.

## Schema Constraints

- **Data Types**: All numerical values are `float64`.
- **Missing Values**: Rows with missing features or targets are dropped during preprocessing.
- **Seeds**: All random operations use a fixed seed defined in `config.py`.

## Output Schema

The final output is a CSV file (`metrics_summary.csv`) with the following columns:
- `dataset_name`
- `uq_method`
- `calibration_error`
- `sharpness`
- `nominal_coverage`
- `p_value` (from statistical test)
- `significance` (boolean)
