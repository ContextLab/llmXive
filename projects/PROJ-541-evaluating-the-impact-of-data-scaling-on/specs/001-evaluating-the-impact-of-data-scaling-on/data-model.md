# Data Model: Evaluating the Impact of Data Scaling on Robustness of Statistical Tests

## Overview

This document defines the data structures used in the simulation and analysis pipeline. The model is designed to be lightweight, serializable (CSV/Parquet), and compatible with the `contracts/` schemas.

## Core Entities

### 1. SimulationConfig
Represents the parameters for a single simulation run.
- `config_id`: Unique identifier (UUID).
- `distribution_type`: Enum (`"normal"`, `"skewed"`, `"heteroscedastic"`).
- `scaling_method`: Enum (`"standard"`, `"minmax"`, `"robust"`).
- `sample_size`: Integer (e.g., 30, 100).
- `alpha_level`: Float (default 0.05).
- `ground_truth`: Enum (`"null"`, `"alternative"`).
- `effect_size`: Float (e.g., 0.0 for null, 1.0 for alt).
- `seed`: Integer (random seed).

### 2. TestResult
Represents the output of a single statistical test.
- `result_id`: Unique identifier.
- `config_id`: Foreign key to `SimulationConfig`.
- `test_type`: Enum (`"t_test"`, `"anova"`). *(Removed: "chi_squared")*
- `statistic`: Float (t-value or F-value).
- `p_value`: Float.
- `is_rejected`: Boolean (`p_value < alpha`).
- `ground_truth`: Enum (`"null"`, `"alternative"`).
- `scaling_method`: String.
- `error_type`: Enum (`"type1"`, `"type2"`, `"none"`, `"error"`).

### 3. AggregateMetrics
Summary statistics for a configuration.
- `config_id`: Foreign key.
- `total_iterations`: Integer.
- `rejected_count`: Integer.
- `empirical_error_rate`: Float.
- `confidence_interval_lower`: Float.
- `confidence_interval_upper`: Float.
- `nominal_alpha`: Float.
- `deviation`: Float (`empirical_error_rate - nominal_alpha`).

### 4. RealWorldDataset
Metadata for ingested public datasets.
- `dataset_id`: Unique identifier.
- `source_url`: String (verified URL).
- `source_name`: String (e.g., "UCI HAR").
- `file_path`: String (local path).
- `checksum`: String (SHA256).
- `preprocessed_status`: Enum (`"loaded"`, `"cleaned"`, `"skipped"`).
- `skipped_reason`: String (if applicable).

### 5. MixedEffectModelOutput
Results of the mixed-effects analysis (Real-World only).
- `model_id`: Unique identifier.
- `fixed_effects`: JSON (coefficients for scaling methods).
- `random_effects_variance`: Float.
- `p_value_fixed_effect`: Float.
- `significance`: Boolean (`p < 0.05`).

## Data Flow

1. **Generation**: `SimulationConfig` -> `TestResult` ([deferred]x).
2. **Aggregation**: `TestResult` -> `AggregateMetrics` (grouped by config).
3. **Validation**: `RealWorldDataset` -> `TestResult` (real-world).
4. **Analysis**: `AggregateMetrics` -> ANOVA (simulation); `TestResult` (real-world) -> `MixedEffectModelOutput`.

## Storage Format

- **Raw Results**: `results/simulation_results.csv` (Flattened `TestResult`).
- **Aggregates**: `results/aggregate_metrics.csv`.
- **Real World**: `results/real_world_results.csv`.
- **Models**: `results/mixed_effect_model.json`.
