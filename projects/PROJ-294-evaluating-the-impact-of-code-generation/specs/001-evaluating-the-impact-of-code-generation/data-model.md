# Data Model: Evaluating the Impact of Code Generation Models on Code Testability

## Overview

This document defines the data structures used throughout the pipeline, ensuring type safety and reproducibility. All data flows from `raw` (HumanEval) to `generated` (LLM code) to `analysis` (metrics) and finally to `results` (report data).

## Entity Definitions

### 1. CodeSample
Represents a single unit of code (human or LLM) linked to a specific HumanEval task.

| Attribute | Type | Description |
|-----------|------|-------------|
| `task_id` | `str` | Unique identifier from HumanEval (e.g., "HumanEval/0"). |
| `source_type` | `str` | Enum: `"human"`, `"codegen-350M"`, `"codellama-7b"`, `"codellama-3b"`. |
| `raw_code` | `str` | The raw Python code string. |
| `status` | `str` | Enum: `"success"`, `"failed_generation"`, `"failed_execution"`, `"failed_coverage"`. |
| `error_log` | `str` | Optional error message if status is not "success". |

### 2. MetricResult
Computed static and dynamic analysis metrics for a `CodeSample`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `task_id` | `str` | Links to `CodeSample`. |
| `source_type` | `str` | Links to `CodeSample`. |
| `cyclomatic_complexity` | `float` | From `radon`. `[deferred]` if execution fails. |
| `halstead_volume` | `float` | From `radon`. `[deferred]` if execution fails. |
| `branch_coverage_pct` | `float` | From `coverage.py` (0.0 to 100.0). `[deferred]` if execution fails. |
| `pass_rate` | `int` | Binary: 1 (all tests pass), 0 (any failure). |

### 3. StatisticalTestResult
Output of hypothesis testing.

| Attribute | Type | Description |
|-----------|------|-------------|
| `test_name` | `str` | e.g., "Wilcoxon Signed-Rank", "McNemar". |
| `metric` | `str` | The metric being tested (e.g., "cyclomatic_complexity"). |
| `statistic` | `float` | The test statistic value. |
| `p_value` | `float` | The p-value. |
| `significant` | `bool` | True if $p < 0.05$ (after correction). |
| `null_hypothesis` | `str` | Text description of $H_0$. |
| `conclusion` | `str` | Text interpretation of the result. |

### 4. PowerAnalysisResult
Output of power analysis.

| Attribute | Type | Description |
|-----------|------|-------------|
| `analysis_type` | `str` | "a_priori" or "post_hoc". |
| `effect_size` | `float` | Observed or assumed effect size (Cohen's d). |
| `sample_size` | `int` | Number of paired samples. |
| `power` | `float` | Achieved or target power. |
| `alpha` | `float` | Significance threshold (0.05). |
| `status` | `str` | "PASS" or "FAIL" based on power threshold. |

## File Formats

### `data/analysis/metrics.json`
A list of `MetricResult` objects.
```json
[
  {
    "task_id": "HumanEval/0",
    "source_type": "human",
    "cyclomatic_complexity": 2.0,
    "halstead_volume": 15.5,
    "branch_coverage_pct": 85.0,
    "pass_rate": 1
  },
  {
    "task_id": "HumanEval/0",
    "source_type": "codegen-350M",
    "cyclomatic_complexity": 3.0,
    "halstead_volume": 18.2,
    "branch_coverage_pct": 70.0,
    "pass_rate": 0
  }
]
```

### `data/analysis/statistical_results.json`
A list of `StatisticalTestResult` objects.

### `state/artifact_hashes.yaml`
Tracking file for reproducibility.
```yaml
dataset:
  source: "openai/openai_humaneval"
  hash: "sha256:..."
  commit: "..."
artifacts:
  codegen_samples: "sha256:..."
  codellama_samples: "sha256:..."
```
