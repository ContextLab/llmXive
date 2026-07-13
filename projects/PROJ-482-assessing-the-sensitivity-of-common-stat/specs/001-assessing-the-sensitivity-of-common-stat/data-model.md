# Data Model: Assessing the Sensitivity of Common Statistical Tests to Dataset Size

## Overview

This document defines the data structures for the simulation engine, focusing on the representation of configurations, simulation runs, and aggregated error metrics. All data is stored in CSV format for portability and reproducibility.

## Entities

### 1. Configuration
Defines the parameters for a batch of simulations.
- `config_id`: Unique identifier (hash of parameters).
- `sample_size`: Integer (n).
- `distribution`: String (normal, uniform, lognormal).
- `effect_size`: Float (0.0 or 0.5).
- `test_type`: String (ttest, anova, chi2).

### 2. SimulationRun
Represents a single iteration of the Monte Carlo loop.
- `run_id`: Unique identifier.
- `config_id`: FK to Configuration.
- `replicate_index`: Integer (1 to N).
- `p_value`: Float.
- `test_used`: String (e.g., "ttest_ind", "fisher_exact").
- `error_type`: String (type1, type2, none).
- `rejected_null`: Boolean.

### 3. ErrorMetric
Aggregated results for a specific configuration.
- `config_id`: FK to Configuration.
- `error_rate`: Float (proportion of errors).
- `ci_lower`: Float (95% CI lower bound, calculated via **Clopper-Pearson**).
- `ci_upper`: Float (95% CI upper bound, calculated via **Clopper-Pearson**).
- `replicate_count`: Integer (final number of replicates).
- `convergence_achieved`: Boolean.

### 4. RegressionResult
Output of the regression analysis.
- `predictor`: String (log_n, distribution, test_type).
- `coefficient`: Float (beta).
- `p_value`: Float.
- `pseudo_r_squared`: Float (McFadden).

## File Formats

### `data/raw/simulation_runs.csv`
Raw output of the Monte Carlo engine.
- Columns: `run_id`, `config_id`, `replicate_index`, `p_value`, `test_used`, `error_type`, `rejected_null`.

### `data/processed/error_metrics.csv`
Aggregated results.
- Columns: `config_id`, `sample_size`, `distribution`, `effect_size`, `test_type`, `error_rate`, `ci_lower`, `ci_upper`, `replicate_count`.

### `data/processed/regression_results.csv`
Regression analysis output.
- Columns: `predictor`, `coefficient`, `p_value`, `pseudo_r_squared`.

## Data Flow

1. **Generation**: `config.py` → `data_generator.py` → `SimulationRun` objects.
2. **Simulation**: `simulation_engine.py` processes `SimulationRun` objects, writes to `data/raw/simulation_runs.csv`.
3. **Aggregation**: `analyzer.py` reads raw runs, computes `ErrorMetric` using **Clopper-Pearson** intervals, writes to `data/processed/error_metrics.csv`.
4. **Analysis**: `analyzer.py` fits a **GLM binomial regression** on the error rate, writes `RegressionResult` to `data/processed/regression_results.csv`.