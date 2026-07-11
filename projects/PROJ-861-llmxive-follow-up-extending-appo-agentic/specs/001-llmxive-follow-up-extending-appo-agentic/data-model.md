# Data Model: llmXive follow-up: extending "APPO: Agentic Procedural Policy Optimization"

## Overview

This document defines the data structures for the static and dynamic branching scores, the alignment process, and the final correlation results. All data is stored in `data/` with checksums.

## Entities

### 1. ReasoningTrace
Represents a single problem instance from GSM8K or MATH.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `trace_id` | `string` | Unique identifier for the trace. | Generated (UUID) |
| `dataset` | `string` | Source dataset name (e.g., "gsm8k", "math"). | Input |
| `question` | `string` | The problem text. | Input |
| `ground_truth` | `string` | The correct answer. | Input |
| `reasoning_steps` | `list<string>` | List of intermediate reasoning steps (semantic steps extracted via fixed regex). | Input |
| `static_scores` | `list<dict>` | List of objects: `{"step_id": string, "score": float}` for each valid semantic step. | Derived |
| `dynamic_scores` | `list<dict>` | List of objects: `{"step_id": string, "score": float}` for each valid semantic step. | Derived |
| `status` | `string` | "completed", "dropped_timeout", "dropped_failure". | System |

### 2. BranchingScore
A single score instance (either static or dynamic).

| Field | Type | Description |
|-------|------|-------------|
| `step_id` | `string` | Semantic step identifier (e.g., "Step 1: Define variables"). |
| `score` | `float` | The calculated score (KL divergence or Advantage value). |
| `type` | `string` | "static" or "dynamic". |
| `context` | `string` | The text of the reasoning step at this identifier. |

### 3. CorrelationResult
The final output of the analysis phase.

| Field | Type | Description |
|-------|------|-------------|
| `pearson_r` | `float` | Pearson correlation coefficient. |
| `spearman_rho` | `float` | Spearman rank correlation coefficient. |
| `p_value` | `float` | P-value from permutation test. |
| `n_pairs` | `integer` | Number of aligned score pairs. |
| `residuals` | `list[float]` | List of residuals (static - dynamic). |
| `ljung_box_p` | `float` | P-value from Ljung-Box test on residuals. |
| `threshold_met` | `boolean` | True if `pearson_r > 0.7` and `p_value < 0.05`. |

## Data Flow

1. **Raw Data Ingestion**: GSM8K/MATH parquet files are downloaded to `data/raw/` via `load_dataset`.
2. **Static Processing**: `static_scorer.py` reads raw data, extracts semantic steps via `step_parser.py`, computes `static_scores` at semantic steps, and writes to `data/processed/static_scores.parquet`.
3. **Dynamic Processing**: `dynamic_scorer.py` reads raw data, runs APPO, computes `dynamic_scores` (Advantage values), and writes to `data/processed/dynamic_scores.parquet`.
4. **Alignment & Analysis**: `analyzer.py` joins the two files, aligns based on **step_id** (semantic step identifier), computes correlations, and writes to `data/results/correlation_results.json`.

## Storage Constraints

- **Format**: Parquet for intermediate data (efficient columnar storage); JSON for final results.
- **Size Limit**: The size of the `data/` directory must be constrained to a manageable limit appropriate for the research infrastructure.
- **Memory**: Streaming processing ensures peak RAM < 7 GB.
