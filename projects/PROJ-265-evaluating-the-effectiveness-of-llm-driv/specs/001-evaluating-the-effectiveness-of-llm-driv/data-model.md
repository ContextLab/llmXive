# Data Model: Evaluating the Effectiveness of LLM-Driven Code Simplification on Performance

## Overview

This document defines the data structures used for storing original functions, simplified functions, benchmark results, and statistical summaries. All data is stored in CSV or Parquet formats for reproducibility and efficient querying.

## Entities

### 1. FunctionPair
Represents a single unit of analysis: the original code and its simplified counterpart.

| Field | Type | Description |
| :--- | :--- | :--- |
| `pair_id` | string | Unique identifier (e.g., `pair_001`). |
| `original_code` | string | The source code of the original function. |
| `simplified_code` | string | The source code of the simplified function. |
| `original_lines` | int | Line count of original code. |
| `simplified_lines` | int | Line count of simplified code. |
| `stratum` | string | "0-10", "11-50", "51+". |
| `equivalence_status` | string | "passed", "failed", "unverifiable". |
| `exclusion_reason` | string | If excluded, reason (e.g., "syntax_error", "drift"). |

### 2. BenchmarkRun
Stores the result of a single execution (one of the 100 iterations).

| Field | Type | Description |
| :--- | :--- | :--- |
| `run_id` | string | Unique identifier. |
| `pair_id` | string | FK to FunctionPair. |
| `version` | string | "original" or "simplified". |
| `iteration` | int | 1 to 100. |
| `cpu_time_ms` | float | CPU time in milliseconds. |
| `peak_memory_mb` | float | Peak memory in MB. |
| `timeout_hit` | boolean | True if execution exceeded 5s. |
| `memory_limit_hit` | boolean | True if execution exceeded 500MB. |
| `status` | string | "success", "timeout", "memory_error", "exception". |

### 3. StatisticalSummary
Aggregated results per function pair and global statistics.

| Field | Type | Description |
| :--- | :--- | :--- |
| `pair_id` | string | FK to FunctionPair. |
| `mean_orig_time` | float | Mean CPU time of original (100 runs, trimmed). |
| `mean_simp_time` | float | Mean CPU time of simplified (100 runs, trimmed). |
| `trimmed_mean_orig_time` | float | Trimmed mean ([deferred] trim) of original. |
| `trimmed_mean_simp_time` | float | Trimmed mean ([deferred] trim) of simplified. |
| `delta_time` | float | `mean_simp_time - mean_orig_time`. |
| `std_dev_orig_time` | float | Std dev of original runs. |
| `std_dev_simp_time` | float | Std dev of simplified runs. |
| `mean_orig_mem` | float | Mean peak memory of original. |
| `mean_simp_mem` | float | Mean peak memory of simplified. |
| `delta_mem` | float | `mean_simp_mem - mean_orig_mem`. |

### 4. GlobalStats
Final statistical test results.

| Field | Type | Description |
| :--- | :--- | :--- |
| `test_type` | string | "t-test" or "wilcoxon". |
| `metric` | string | "time" or "memory". |
| `p_value_raw` | float | Raw p-value. |
| `p_value_adjusted` | float | Bonferroni adjusted p-value. |
| `significant` | boolean | True if `p_value_adjusted < 0.05`. |
| `n_pairs` | int | Number of valid pairs (N). |
| `normality_p` | float | Shapiro-Wilk p-value. |

## File Structure

- `data/processed/function_pairs.parquet`: Stores `FunctionPair` data.
- `data/results/benchmark_runs.parquet`: Stores `BenchmarkRun` data (large file).
- `data/results/statistical_summary.csv`: Stores `StatisticalSummary` and `GlobalStats`.