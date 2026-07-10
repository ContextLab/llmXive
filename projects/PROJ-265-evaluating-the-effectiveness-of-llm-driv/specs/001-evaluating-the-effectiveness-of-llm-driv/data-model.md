# Data Model: Evaluating the Effectiveness of LLM-Driven Code Simplification on Performance

## Entities

### FunctionPair

Represents a pair of original and simplified Python functions.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the function pair |
| original_code | string | Original Python function code |
| simplified_code | string | Simplified Python function code |
| lines_original | int | Line count of original code |
| lines_simplified | int | Line count of simplified code |
| equivalence_status | string | "pass", "fail", "excluded" |
| equivalence_details | json | Details of equivalence check (source of tests, test results) |
| excluded_reason | string | Reason for exclusion (if any) |

### BenchmarkResult

Stores performance metrics for a single execution.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the benchmark result |
| function_pair_id | string | Reference to FunctionPair |
| version | string | "original" or "simplified" |
| iteration | int | Iteration number (1–100) |
| cpu_time_ms | float | CPU time in milliseconds |
| peak_memory_mb | float | Peak memory in megabytes |
| timeout | bool | Whether execution timed out |
| memory_limit_exceeded | bool | Whether memory limit was exceeded |

### StatisticalSummary

Aggregates results across the dataset.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the summary |
| metric | string | "execution_time" or "memory_usage" |
| mean_original | float | Mean value for original code (averaged across 100 iterations) |
| mean_simplified | float | Mean value for simplified code (averaged across 100 iterations) |
| mean_delta | float | Mean difference (original - simplified) |
| std_original | float | Standard deviation for original (across multiple function means) |
| std_simplified | float | Standard deviation for simplified (across 100 function means) |
| normality_p_value | float | Shapiro-Wilk p-value (on a sample of function means) |
| test_type | string | "t-test" or "wilcoxon" |
| raw_p_value | float | Raw p-value from statistical test |
| corrected_p_value | float | Bonferroni-corrected p-value |
| significant | bool | Whether result is statistically significant (p < 0.05) |

## Data Flow

1. **Download**: Raw parquet files → `data/raw/`
2. **Preprocess**: Validate, isolate, mock, **generate test suite** → `data/processed/`
3. **Simplify**: LLM inference → `data/processed/simplified/`
4. **Equivalence**: Run test suite → `data/processed/equivalence/`
5. **Benchmark**: Run **100 iterations** → `data/results/benchmark/`
6. **Analyze**: Aggregate to **function means**, run statistical tests on means → `data/results/stats/`

## Storage Format

- **Raw Data**: Parquet (CodeSearchNet)
- **Processed Data**: JSON (function pairs, equivalence results)
- **Benchmark Results**: CSV (iteration-level metrics)
- **Statistical Summaries**: JSON (aggregated results)

## Constraints

- **File Size**: Each processed function <10 KB
- **Total Dataset**: <250 MB (A set of functions, each approximately 2.5 KB in size.)
- **Iteration Logs**: <2.5 GB (A set of functions, each subjected to multiple iterations, with each operation consuming approximately 50 bytes of memory.)
- **RAM Usage**: <7 GB during execution (model + data + overhead)