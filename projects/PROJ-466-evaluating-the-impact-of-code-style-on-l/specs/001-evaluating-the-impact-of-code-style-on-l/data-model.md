# Data Model: Evaluating the Impact of Code Style on LLM Code Generation Diversity

## Overview

This document defines the data structures, schemas, and flow for the project. All data is stored in CSV format for compatibility with standard Python data analysis tools (`pandas`).

## Data Flow Diagram

1.  **Raw Data**: `data/raw/human_eval_subset.csv` (Downloaded from HuggingFace)
2.  **Generation Output**:
    *   `data/processed/samples_all.csv` (All generated samples, unfiltered)
    *   `data/processed/samples_valid.csv` (Samples that passed unit tests)
3.  **Metrics Output**:
    *   `data/processed/metrics_all.csv` (Diversity metrics for all samples)
    *   `data/processed/metrics_valid.csv` (Diversity metrics for valid samples)
4.  **Analysis Output**:
    *   `data/processed/stats_results.json` (H-statistic, p-values, post-hoc results)
    *   `artifacts/report.pdf` (Final summary report)

## Entity Definitions

### 1. Task
A single programming problem.
- `task_id`: Unique identifier (e.g., "HumanEval/0")
- `prompt`: The base prompt text.
- `test`: The unit test code string.

### 2. Sample
A generated code snippet.
- `task_id`: Foreign key to Task.
- `style`: The style constraint applied (Neutral, PEP8, Minified).
- `sample_id`: Integer (0-4) within the task/style group.
- `code`: The generated source code string.
- `pass_status`: Boolean (True/False) indicating if unit tests passed.
- `generation_time`: Float (seconds).

### 3. Diversity Metric
Aggregated metrics for a task/style group.
- `task_id`: Foreign key to Task.
- `style`: Style constraint.
- `metric_type`: "ast_distance" or "ngram_entropy".
- `value`: The computed metric value.
- `sample_count`: Number of samples used to compute the metric.
- `is_valid_only`: Boolean (True if computed from valid samples only).

## Schema Definitions

### samples_all.csv / samples_valid.csv
| Column | Type | Description |
| :--- | :--- | :--- |
| `task_id` | string | Unique task identifier |
| `style` | string | "neutral", "pep8", or "minified" |
| `sample_id` | integer | 0 to 4 |
| `code` | string | Generated Python code |
| `pass_status` | boolean | True if tests passed |
| `generation_time` | float | Time taken to generate |

### metrics_valid.csv (Primary Analysis Dataset)
| Column | Type | Description |
| :--- | :--- | :--- |
| `task_id` | string | Unique task identifier |
| `style` | string | Style constraint |
| `avg_ast_distance` | float | Mean pairwise AST edit distance |
| `avg_ngram_entropy` | float | Mean n-gram entropy |
| `sample_count` | integer | Number of valid samples |
| `valid_pass_rate` | float | Pass rate for this task/style |

### metrics_all.csv (Pre-Filter Dataset)
| Column | Type | Description |
| :--- | :--- | :--- |
| `task_id` | string | Unique task identifier |
| `style` | string | Style constraint |
| `avg_ast_distance` | float | Mean pairwise AST edit distance |
| `avg_ngram_entropy` | float | Mean n-gram entropy |
| `sample_count` | integer | Number of total samples (always 5) |
| `pass_rate` | float | Pass rate for this task/style |

## Data Hygiene & Versioning

- **Checksums**: `data/raw/human_eval_subset.csv` checksum recorded in `state.yaml`.
- **Immutability**: `samples_all.csv` is never modified. `samples_valid.csv` is derived from it.
- **PII**: No personally identifiable information is collected. Code samples are synthetic.
- **State Tracking**: Every artifact (CSV, JSON, PDF) hash is recorded in `state.yaml` via the `update_state.py` script.