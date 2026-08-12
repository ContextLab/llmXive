# Data Model: llmXive Follow-up: Trace Compressibility Analysis

## Overview

This document defines the data structures used throughout the pipeline: synthetic traces, extracted metrics, induced rules, and evaluation results. All data is stored in the `data/` directory, with raw data in `data/raw/` and processed data in `data/processed/`.

## Data Flow

1.  **Generation**: `code/synthesis/generator.py` -> `data/raw/traces/` (JSONL) + `data/raw/logs/trace_integrity.log`
2.  **Extraction**: `code/analysis/metrics.py` -> `data/processed/metrics.csv`
3.  **Induction**: `code/analysis/rules.py` -> `data/processed/rules/model.json`
4.  **Evaluation**: `code/evaluation/benchmark.py` -> `data/processed/results/` (per-request JSON) + `data/processed/results/summary.json`
5.  **Analysis**: `code/evaluation/statistical_analysis.py` -> `data/processed/statistical_analysis_results.json`
6.  **Sensitivity**: `code/evaluation/sensitivity.py` -> `data/processed/sensitivity_report.json`
7.  **Feasibility**: `code/utils/monitor.py` -> `data/processed/feasibility_report.json`
8.  **Reporting**: `code/evaluation/final_report_generator.py` -> `data/processed/final_report.md`

## Schema Definitions

### 1. Execution Trace (Raw)
*Source*: `data/raw/traces/{session_id}.jsonl`  
*Format*: JSONL (one JSON object per line)

| Field | Type | Description |
| :--- | :--- | :--- |
| `session_id` | string | Unique identifier for the session. |
| `turns` | array | List of tool execution steps. |
| `turns[].tool` | string | Tool name (e.g., "insert_chart"). |
| `turns[].args` | object | Tool arguments (key-value pairs). |
| `turns[].timestamp` | integer | Unix timestamp of the turn. |
| `final_state` | object | Ground-truth slide state representation. |

### 2. Trace Integrity Log
*Source*: `data/raw/logs/trace_integrity.log`  
*Format*: JSONL (one JSON object per line)  
*Purpose*: Verifies Principle VI (Trace Structural Integrity).

| Field | Type | Description |
| :--- | :--- | :--- |
| `session_id` | string | Reference to trace. |
| `tool_sequence` | array | Exact sequence of tool calls. |
| `arg_variance` | float | Pre-computed argument semantic variance. |
| `timestamp` | integer | Log generation timestamp. |

### 3. Structural Metrics
*Source*: `data/processed/metrics.csv`  
*Format*: CSV

| Field | Type | Description |
| :--- | :--- | :--- |
| `session_id` | string | Reference to raw trace. |
| `sequence_entropy` | float | Shannon entropy of the tool sequence. |
| `tool_repetition_freq` | float | Frequency of repeated tool calls. |
| `arg_semantic_variance` | float | Variance of argument embeddings. |
| `trace_length` | integer | Number of turns in the trace. |
| `split` | string | "training" or "held_out". |

### 4. Induced Rules
*Source*: `data/processed/rules/model.json`  
*Format*: JSON

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_id` | string | Unique identifier for the rule set. |
| `rules` | array | List of symbolic rules. |
| `rules[].condition` | string | IF condition (e.g., "entropy < 0.5"). |
| `rules[].action` | string | THEN action (e.g., "rule=chart_insertion"). |
| `fidelity_score` | float | Accuracy of rules on validation set (Training Set). |
| `compression_ratio` | float | Ratio of rule size to trace size. |

### 5. Evaluation Results
*Source*: `data/processed/results/summary.json`  
*Format*: JSON

| Field | Type | Description |
| :--- | :--- | :--- |
| `baseline_accuracy` | float | Edit Accuracy of raw memory agent (Held-Out). |
| `compressed_accuracy` | float | Edit Accuracy of rule-based agent (Held-Out). |
| `accuracy_diff` | float | `baseline_accuracy` - `compressed_accuracy`. |
| `baseline_latency` | float | Mean retrieval latency of raw memory. |
| `compressed_latency` | float | Mean retrieval latency of rule-based. |
| `latency_diff` | float | `baseline_latency` - `compressed_latency`. |

### 6. Statistical Analysis Results
*Source*: `data/processed/statistical_analysis_results.json`  
*Format*: JSON

| Field | Type | Description |
| :--- | :--- | :--- |
| `method` | string | "Multiple Linear Regression" or "Spearman Correlation". |
| `coefficients` | object | Regression coefficients for each metric. |
| `p_values` | object | P-values for each coefficient. |
| `significance_threshold` | number | Threshold used for significance (e.g., 0.05). |
| `assumption_violations` | array | List of violated assumptions (if any). |

### 7. Sensitivity Report
*Source*: `data/processed/sensitivity_report.json`  
*Format*: JSON

| Field | Type | Description |
| :--- | :--- | :--- |
| `thresholds` | array | List of compression thresholds swept. |
| `fidelity_rates` | array | Corresponding fidelity rates for each threshold. |
| `compression_ratios` | array | Derived compression ratios for each threshold. |

### 8. Feasibility Report
*Source*: `data/processed/feasibility_report.json`  
*Format*: JSON

| Field | Type | Description |
| :--- | :--- | :--- |
| `total_runtime_seconds` | number | Total pipeline runtime. |
| `peak_memory_gb` | number | Peak memory usage. |
| `peak_disk_gb` | number | Peak disk usage. |
| `status` | string | "PASS" or "FAIL" (based on CI constraints). |
| `constraints` | object | Limits (6h, 7GB RAM, 14GB disk). |

## Data Hygiene & Versioning

- **Checksums**: All files in `data/` are checksummed (SHA-256) and recorded in `state/...yaml`.
- **Immutability**: Raw data is never modified. Derivations create new files.
- **Seeds**: Random seeds for generation and splitting are pinned in configuration.