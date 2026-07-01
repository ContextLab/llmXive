# Data Model: Impact of Cache Line Padding on False Sharing in Concurrent Counters

## Overview

This document defines the data structures used in the project, including raw benchmark outputs, aggregated results, and statistical comparisons.

## Entities

### BenchmarkRun

A single execution of the C++ binary with specific thread count and configuration.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `run_id` | string | Unique identifier for the run (e.g., UUID or timestamp). |
| `thread_count` | integer | Number of worker threads (1, 2, 4, or 8). |
| `configuration` | string | Counter variant ("packed" or "padded"). |
| `iteration_count` | integer | Number of atomic increments per thread (10⁷). |
| `wall_clock_time_ms` | float | Wall-clock time for the run in milliseconds. |
| `cpu_model` | string | CPU model string (e.g., "Intel Xeon..."). |
| `core_count` | integer | Number of physical cores available. |
| `cache_line_size` | integer | Cache line size in bytes (typically 64). |
| `timestamp` | datetime | ISO 8601 timestamp of the run. |

### AggregatedResult

Mean throughput and standard deviation across at least 5 runs for a given `thread_count`/`configuration` pair.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `thread_count` | integer | Number of worker threads. |
| `configuration` | string | Counter variant. |
| `mean_throughput` | float | Mean operations per second. |
| `std_throughput` | float | Standard deviation of throughput. |
| `n_runs` | integer | Number of runs averaged. |
| `ci_lower` | float | Lower bound of 95% CI. |
| `ci_upper` | float | Upper bound of 95% CI. |

### StatisticalComparison

T-test results comparing padded vs. unpadded throughput at a specific thread count.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `thread_count` | integer | Number of worker threads. |
| `t_statistic` | float | T-statistic from the two-sample t-test. |
| `p_value` | float | Raw p-value. |
| `p_value_fdr` | float | FDR-adjusted p-value. |
| `cohen_d` | float | Effect size (Cohen's d). |
| `significant` | boolean | True if `p_value_fdr` ≤ 0.05. |

## Data Flow

1. **Generation**: `code/benchmark/main.cpp` generates raw CSV files (`data/raw/benchmark_run_*.csv`) containing `BenchmarkRun` records.
2. **Aggregation**: `code/analysis/run_analysis.py` reads raw CSVs, computes `AggregatedResult` statistics, and saves to `data/processed/aggregated_results.csv`.
3. **Statistical Testing**: The same script performs t-tests, computes Cohen's d, applies FDR correction, and saves `StatisticalComparison` records to `data/processed/statistical_comparison.csv`.
4. **Visualization**: The script generates a PNG plot (`data/processed/throughput_plot.png`) using the aggregated results.

## File Formats

### Raw CSV (`data/raw/*.csv`)

```csv
run_id,thread_count,configuration,iteration_count,wall_clock_time_ms,cpu_model,core_count,cache_line_size,timestamp
...
```

### Aggregated CSV (`data/processed/aggregated_results.csv`)

```csv
thread_count,configuration,mean_throughput,std_throughput,n_runs,ci_lower,ci_upper
...
```

### Statistical CSV (`data/processed/statistical_comparison.csv`)

```csv
thread_count,t_statistic,p_value,p_value_fdr,cohen_d,significant
...
```
