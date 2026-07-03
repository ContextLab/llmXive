# Data Model: Evaluating the Impact of Code Generation Models on Code Testability

## Entities

### CodeSample
Represents a single unit of code (human or LLM generated) for a specific task.
- `task_id`: str (Unique identifier from HumanEval)
- `source_type`: str ("human" or "llm")
- `model_name`: str (e.g., "codegen-350M-mono", "human")
- `raw_code`: str (The Python source code)
- `generation_status`: str ("success", "timeout", "syntax_error")
- `error_log`: str (Optional error message)

### MetricResult
Computed structural and dynamic properties for a `CodeSample`.
- `sample_id`: str (Foreign key to CodeSample)
- `cyclomatic_complexity`: int
- `halstead_volume`: float
- `halstead_difficulty`: float
- `halstead_effort`: float
- `dynamic_branch_coverage`: float (0.0 – 1.0, measured via **execution**; nullable if execution fails)
- `pass_rate`: float (0.0 or 1.0)
- `analysis_timestamp`: str (ISO 8601)

### StatisticalTest
Result of hypothesis testing.
- `metric_name`: str (e.g., "cyclomatic_complexity")
- `test_type`: str ("wilcoxon_signed_rank", "fisher_exact")
- `test_statistic`: float
- `p_value`: float
- `significant`: bool
- `effect_size`: float (r for Wilcoxon, odds ratio for Fisher)
- `power`: float (Post‑hoc power)
- `correction_method`: str (e.g., "none")

### DecouplingResult
Result of the independence analysis.
- `predictor`: str (e.g., "cyclomatic_complexity")
- `outcome`: str (e.g., "pass_rate")
- `control_variable`: str (e.g., "source_type")
- `partial_correlation`: float
- `regression_coefficient`: float
- `p_value`: float

## Data Flow

1. **Raw Data**: `data/raw/humaneval.parquet` (downloaded, checksummed).
2. **Generated Data**: `data/generated/{task_id}_{source}.py` (code files).
3. **Analysis Data**: `data/analysis/metrics.json` (aggregated `MetricResult`s).
4. **Results**: `results/stats.json` (StatisticalTest outcomes).
5. **Decoupling**: `results/decoupling.json` (DecouplingResult outcomes).
6. **Report**: `results/results_report.md` (Final human‑readable report).

## Constraints

- All `CodeSample` entries with `generation_status != "success"` are excluded from statistical analysis but must appear in `errors.log`.
- `MetricResult` entries must be non‑null for successful samples; `dynamic_branch_coverage` may be null only when execution fails.
- `pass_rate` is binary (0.0 or 1.0) based on the all‑or‑nothing test harness.
- Analysis is strictly **paired**: only tasks with valid human and LLM samples are included.