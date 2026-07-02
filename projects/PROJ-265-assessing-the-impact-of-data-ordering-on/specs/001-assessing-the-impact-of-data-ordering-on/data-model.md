# Data Model: Assessing the Impact of Data Ordering on Bootstrapping Results

## Overview

This document defines the data structures, schemas, and storage formats used in the project. It ensures that the `Implementer Agent` can generate code that produces outputs conforming to these definitions.

## Entities

### 1. TimeSeries
Represents a single synthetic or real-world time series segment.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `string` | Unique identifier (e.g., `synth_phi_0.5_trial_001` or `uci_hour_1234`) |
| `data` | `list[float]` | The observed time series values. |
| `phi` | `float` | The true (synthetic) or estimated (real) autoregressive coefficient. |
| `theoretical_mean` | `float` | Ground truth mean (0.0 for synthetic, NaN for real). |
| `source` | `string` | `synthetic` or `uci` |
| `segment_start` | `int` | Start index (for real data). |
| `segment_end` | `int` | End index (for real data). |

### 2. BootstrapResult
Represents the outcome of a single bootstrap run on a specific time series.

| Field | Type | Description |
| :--- | :--- | :--- |
| `series_id` | `string` | Reference to the `TimeSeries.id`. |
| `condition` | `string` | `ordered` or `shuffled` |
| `ci_lower` | `float` | Lower bound of the 95% CI. |
| `ci_upper` | `float` | Upper bound of the 95% CI. |
| `ci_width` | `float` | Width of the CI (`ci_upper - ci_lower`). |
| `covered` | `bool` | `True` if `theoretical_mean` (synthetic) is within `[ci_lower, ci_upper]`. `False` for real data (N/A). |
| `mean_estimate` | `float` | The bootstrap mean estimate. |

### 3. SimulationBatch
Aggregated results for a specific $\phi$ level or real-world segment group.

| Field | Type | Description |
| :--- | :--- | :--- |
| `phi_level` | `float` | The $\phi$ value (0.0 to 0.9) or `bin_label` (for real data). |
| `condition` | `string` | `ordered` or `shuffled` |
| `n_trials` | `int` | Number of trials in the batch. |
| `coverage_probability` | `float` | Percentage of `covered` = True (Synthetic only, NaN for real). |
| `ci_width_ratio` | `float` | Ratio of Ordered CI Width / Shuffled CI Width (Real data only, NaN for synthetic). |
| `mcnemar_p_value` | `float` | P-value from McNemar's test (aggregate). |
| `z_test_p_value` | `float` | P-value from Two-Proportion Z-Test. |
| `significance` | `bool` | `True` if p-value < 0.05. |

### 4. DataSegment (Real World)
Metadata for a segment of the UCI dataset.

| Field | Type | Description |
| :--- | :--- | :--- |
| `segment_id` | `string` | Unique ID for the segment. |
| `hour_start` | `datetime` | Start time of the hour. |
| `n_obs` | `int` | Number of observations in the segment. |
| `phi_estimate` | `float` | Estimated AR(1) coefficient. |
| `status` | `string` | `valid` (if $N \ge 30$) or `skipped`. |
| `bin_label` | `string` | Binned $\phi$ range (e.g., "0.0-0.1"). |

## Storage Formats

### CSV: `results/coverage_metrics.csv`
The primary output artifact for the research.

| Column | Type | Description |
| :--- | :--- | :--- |
| `phi_level` | `float` | $\phi$ value or `bin_label` for real data. |
| `condition` | `string` | `ordered` or `shuffled`. |
| `coverage_probability` | `float` | Empirical coverage rate (Synthetic only). |
| `ci_width_ratio` | `float` | Ordered Width / Shuffled Width (Real data only). |
| `n_trials` | `int` | Number of trials. |
| `mcnemar_p_value` | `float` | P-value for the difference (aggregate). |
| `z_test_p_value` | `float` | P-value for Two-Proportion Z-Test. |
| `significance` | `bool` | Whether the difference is significant. |

### JSON: `results/simulation_log.json`
Detailed logs for debugging and reproducibility.

### Parquet: `data/processed/segments.parquet`
Processed real-world data segments (if loaded).

## Constraints

- **Immutability**: Raw data in `data/raw/` must never be modified.
- **Determinism**: All random seeds must be logged in the metadata.
- **Schema Compliance**: All output files must strictly adhere to the defined schemas.
- **Real Data Metric**: For real data, `coverage_probability` is NaN; `ci_width_ratio` is the primary metric.