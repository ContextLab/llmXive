# Data Model: Assessing the Validity of Frequentist Confidence Intervals with Small Sample Sizes

## Overview

This document defines the data models for the Monte Carlo simulation engine, including input distributions, intermediate simulation results, and aggregated outputs. All models are designed to support reproducibility (Constitution Principle I) and traceability (Constitution Principle IV).

## Entity Definitions

### Simulation Run

Represents one complete execution of the Monte Carlo process for a specific distribution, sample size, and confidence level.

**Attributes**:
- `run_id`: Unique identifier (UUID)
- `distribution_name`: Name of the parametric distribution (e.g., "LogNormal", "Beta")
- `distribution_parameters`: Dictionary of parameters (e.g., `{"mu": 0, "sigma": 1}`)
- `variable_name`: Name of the variable analyzed (e.g., "X")
- `sample_size`: Integer (10, 20, or 30)
- `confidence_level`: Float (0.90, 0.95, or 0.99)
- `replications`: Integer (10,000)
- `true_population_mean`: Float (theoretical mean of the parametric distribution)
- `start_timestamp`: ISO 8601 timestamp
- `end_timestamp`: ISO 8601 timestamp
- `random_seed`: Integer (pinned for reproducibility)

### Coverage Record

Represents the outcome of a single replication (interval contains true mean: boolean).

**Attributes**:
- `run_id`: Foreign key to Simulation Run
- `replication_index`: Integer (1 to [deferred])
- `sample_mean`: Float (mean of the sample)
- `sample_std`: Float (standard deviation of the sample)
- `t_interval_lower`: Float (lower bound of t-interval)
- `t_interval_upper`: Float (upper bound of t-interval)
- `t_interval_contains_mean`: Boolean
- `bootstrap_interval_lower`: Float (lower bound of bootstrap percentile interval)
- `bootstrap_interval_upper`: Float (upper bound of bootstrap percentile interval)
- `bootstrap_interval_contains_mean`: Boolean

*Note: In practice, individual coverage records are not stored to save disk space; only aggregated statistics are persisted.*

### Aggregate Report

Represents the summarized statistics across all replications for a single configuration.

**Attributes**:
- `run_id`: Foreign key to Simulation Run
- `t_coverage_rate`: Float (proportion of t-intervals containing true mean)
- `t_coverage_deviation`: Float (t_coverage_rate - confidence_level)
- `t_is_significant_deviation`: Boolean (|t_coverage_deviation| > 0.01)
- `bootstrap_coverage_rate`: Float (proportion of bootstrap intervals containing true mean)
- `bootstrap_coverage_deviation`: Float (bootstrap_coverage_rate - confidence_level)
- `bootstrap_is_significant_deviation`: Boolean (|bootstrap_coverage_deviation| > 0.01)
- `bonferroni_adjusted_pvalue_t`: Float (Bonferroni-adjusted p-value for t-interval deviation)
- `bonferroni_adjusted_pvalue_bootstrap`: Float (Bonferroni-adjusted p-value for bootstrap deviation)

### Sensitivity Report

Represents aggregated results across sample sizes or confidence levels.

**Attributes**:
- `report_type`: String ("sample_size" or "confidence_level")
- `distribution_name`: Name of the distribution
- `variable_name`: Name of the variable
- `varying_parameter`: String (sample size or confidence level value)
- `t_coverage_rates`: List of floats (coverage rates across varying parameter)
- `bootstrap_coverage_rates`: List of floats (coverage rates across varying parameter)
- `coverage_deviation_trend`: String (description of trend, e.g., "decreasing with n")

## Data Flow

1. **Input**: Parametric distribution definitions (JSON/YAML) → Synthetic data generation.
2. **Simulation**: Synthetic data → Monte Carlo replications → Coverage records (aggregated in memory).
3. **Aggregation**: Coverage records → Aggregate reports (per configuration).
4. **Sensitivity Analysis**: Aggregate reports → Sensitivity reports (across sample sizes/confidence levels).
5. **Output**: Aggregate reports + Sensitivity reports → JSON/CSV files + Markdown report.

## Storage Schema

- **Raw Data**: `data/raw/<distribution_name>_<params>.json` (checksummed)
- **Filtered Data**: Not applicable (synthetic data is clean by definition).
- **Aggregate Reports**: `outputs/coverage_results.json`
- **Sensitivity Reports**: `outputs/sensitivity_results.json`
- **Final Report**: `outputs/report.md`

## Validation Rules

- All distributions must be parametric with known theoretical mean.
- Random seeds must be pinned for reproducibility.
- All timestamps must be ISO 8601 format.
- Coverage rates must be in [0, 1].
- Deviations must be calculated as (empirical - nominal).
- Significance threshold: |deviation| > 0.01.