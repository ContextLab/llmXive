# Data Model: llmXive follow-up: extending "APPO: Agentic Procedural Policy Optimization"

## Overview

This document defines the data structures used to store reasoning traces, branching scores, and analysis results. All data is stored in JSON/Parquet formats to ensure reproducibility and compatibility with the analysis pipeline.

## Key Entities

### 1. Reasoning Trace
A sequence of tokens representing a solution path for a math problem.

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | `string` | Unique identifier for the problem instance. |
| `dataset` | `string` | Source dataset (e.g., "gsm8k", "math"). |
| `question` | `string` | The original problem statement. |
| `ground_truth` | `string` | The correct answer. |
| `tokens` | `list[string]` | Tokenized sequence of the reasoning trace. |
| `static_scores` | `list[float]` | KL divergence scores for each token position. |
| `dynamic_scores` | `list[float]` | APPO likelihood gains for each token position. |
| `reasoning_pattern` | `string` | Classified pattern (e.g., "arithmetic", "algebra"). |

### 2. Branching Score
A numeric value representing the "decision value" at a specific token position.

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | `string` | Reference to the parent trace. |
| `token_position` | `int` | Index of the token in the sequence. |
| `score_type` | `string` | "static" or "dynamic". |
| `value` | `float` | The calculated score. |

### 3. Correlation Result
Aggregated statistical results from the analysis.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `string` | Unique identifier for the correlation run (seed). |
| `pearson_r` | `float` | Pearson correlation coefficient. |
| `spearman_rho` | `float` | Spearman rank correlation coefficient. |
| `p_value` | `float` | P-value from the permutation test. |
| `iterations` | `int` | Number of permutation iterations performed. |
| `status` | `string` | "complete", "timeout", or "inconclusive". |
| `residual_summary` | `dict` | Summary of residuals by reasoning pattern. |

## Data Flow

1. **Raw Data**: Downloaded from HuggingFace (GSM8K, MATH) and stored in `data/raw/`.
2. **Processed Traces**: Tokenized and scored by `static/scorer.py` and `dynamic/appo_runner.py`, stored in `data/derived/traces.jsonl`.
3. **Aligned Scores**: Traces aligned by token position, stored in `data/derived/aligned_scores.parquet`.
4. **Analysis Results**: Correlation and residual analysis results stored in `data/derived/correlation_results.jsonl`.

## Constraints

- **No PII**: No personally identifiable information is included in any dataset.
- **Checksums**: All raw data files are checksummed and recorded in `state/`.
- **Immutability**: Raw data is never modified; derivations are written to new files.
