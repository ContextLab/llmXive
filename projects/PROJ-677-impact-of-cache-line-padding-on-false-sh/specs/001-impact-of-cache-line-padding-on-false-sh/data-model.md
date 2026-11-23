# Data Model: Impact of Cache Line Padding on False Sharing in Concurrent Counters

## 1. Raw Data Schema

### `BenchmarkRun`
Represents a single execution of the benchmark binary.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `thread_count` | integer | Number of worker threads (1, 2, 4, 8) | Yes |
| `configuration` | string | "packed" or "padded" | Yes |
| `iteration_count` | integer | Number of atomic increments per thread | Yes |
| `wall_clock_time_ms` | float | Wall-clock time in milliseconds | Yes |
| `run_id` | string | Unique identifier for the run (timestamp + hash) | Yes |
| `timestamp` | ISO8601 | Execution timestamp | Yes |

**Source**: `code/scripts/run_benchmarks.sh` → `data/raw/benchmark_results.csv`

## 2. Aggregated Data Schema

### `AggregatedResult`
Represents mean throughput and standard deviation across ≥5 runs for a given thread_count/configuration pair.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `thread_count` | integer | Number of worker threads | Yes |
| `configuration` | string | "packed" or "padded" | Yes |
| `mean_throughput_ops_per_sec` | float | Mean operations per second | Yes |
| `std_throughput_ops_per_sec` | float | Standard deviation of throughput | Yes |
| `n_runs` | integer | Number of runs aggregated | Yes |
| `ci_lower_95` | float | 95% CI lower bound (t-distribution) | Yes |
| `ci_upper_95` | float | 95% CI upper bound (t-distribution) | Yes |

**Source**: `code/analysis/analysis.py` → `data/processed/aggregated_results.csv`

## 3. Statistical Comparison Schema

### `StatisticalComparison`
Represents t-test results comparing padded vs. unpadded at a specific thread count.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `thread_count` | integer | Thread count for comparison | Yes |
| `t_statistic` | float | T-statistic from two-sample t-test | Yes |
| `p_value_raw` | float | Raw p-value | Yes |
| `p_value_fdr` | float | Benjamini-Hochberg FDR-adjusted p-value | Yes |
| `cohen_d` | float | Effect size (Cohen's d) | Yes |
| `significant_fdr` | boolean | True if `p_value_fdr` ≤ 0.05 | Yes |

**Source**: `code/analysis/analysis.py` → `data/processed/statistical_comparisons.csv`

## 4. Hardware Specification Schema

### `HardwareSpec`
Records the execution environment.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `cpu_model` | string | CPU model name | Yes |
| `core_count` | integer | Number of physical cores | Yes |
| `cache_line_size` | integer | Cache line size in bytes (typically 64) | Yes |
| `compiler_flags` | string | Compilation flags (e.g., "-O3 -march=native") | Yes |
| `timestamp` | ISO8601 | Detection timestamp | Yes |

**Source**: `code/benchmark/hardware_detect.py` → `data/hardware_spec.yaml`

## 5. Data Flow

1. **Generation**: `run_benchmarks.sh` → `data/raw/benchmark_results.csv`
2. **Validation**: `validate_raw_data.py` checks schema, NaNs, missing values.
3. **Aggregation**: `analysis.py` → `data/processed/aggregated_results.csv`
4. **Statistical Testing**: `analysis.py` → `data/processed/statistical_comparisons.csv`
5. **Visualization**: `analysis.py` → `data/processed/throughput_plot.png`