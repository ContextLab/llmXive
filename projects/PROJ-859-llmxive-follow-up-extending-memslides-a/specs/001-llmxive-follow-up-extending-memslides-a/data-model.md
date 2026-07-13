# Data Model: Trace Compressibility Analysis

## Overview
This document defines the data structures used in the Trace Compressibility Analysis project. All data is stored locally under `data/` and validated against schemas in `contracts/` (located at repository root).

## Entities

### 1. Execution Trace
A single multi-turn revision session.
- **ID**: `trace_id` (string, unique)
- **Tools**: `tool_sequence` (list of strings, e.g., `["insert_chart", "format_text"]`)
- **Arguments**: `arguments` (list of dictionaries or strings, semantic content)
- **Final State**: `final_state` (dictionary representing slide state)
- **Metadata**: `session_length` (int), `generation_seed` (int)
- **Verification Fields**:
  - `exact_tool_sequence`: (list of strings) The raw, unmodified tool sequence logged for derivation checks.
  - `raw_arg_variance`: (float) The pre-calculated argument semantic variance stored for verification (Constitution Principle VI).

### 2. Structural Metrics
Derived features for each trace.
- **Trace ID**: `trace_id` (string, FK to Execution Trace)
- **Sequence Entropy**: `sequence_entropy` (float)
- **Tool Repetition Frequency**: `tool_repetition_freq` (float, 0.0 to 1.0)
- **Argument Semantic Variance**: `arg_semantic_variance` (float)
- **Complexity Label**: `complexity_class` (string: "Low", "Medium", "High")

### 3. Compressibility Analysis
Per-trace results from rule induction.
- **Trace ID**: `trace_id` (string, FK to Execution Trace)
- **Rule Set Size**: `rule_set_size_bytes` (int)
- **Trace Size**: `trace_size_bytes` (int)
- **Fidelity**: `fidelity_score` (float, 0.0 to 1.0)
- **Compressibility Score**: `compressibility_score` (float, 0.0 to 1.0)

### 4. Benchmark Results
Performance metrics for agents (Global).
- **Request ID**: `request_id` (string)
- **Agent Type**: `agent_type` (string: "baseline", "compressed")
- **Edit Accuracy**: `edit_accuracy` (float, 0.0 to 1.0)
- **Retrieval Latency**: `retrieval_latency_ms` (float)
- **Compression Ratio**: `compression_ratio` (float)

### 5. Statistical Analysis Output
Results of regression/correlation tests.
- **Metric Name**: `metric_name` (string)
- **Coefficient**: `coefficient` (float)
- **P-value**: `p_value` (float)
- **Significance**: `is_significant` (boolean)
- **Correction Method**: `correction_method` (string: "Bonferroni", "None")

## Data Flow

1. **Generation**: `synthetic_trace.py` -> `data/raw/traces.jsonl` (includes `exact_tool_sequence` and `raw_arg_variance`)
2. **Extraction**: `extract.py` reads `traces.jsonl` -> `data/processed/metrics.csv`
3. **Per-Trace Induction**: `rule_induction.py` reads `metrics.csv` -> `data/processed/compressibility_analysis.jsonl`
4. **Benchmark**: `benchmark.py` reads `model.pkl` and `traces.jsonl` -> `data/processed/benchmark_results.json`
5. **Analysis**: `stats.py` reads `compressibility_analysis.jsonl` -> `data/processed/statistical_analysis.json`

## File Formats

- **Traces**: JSONL (one JSON object per line) for streaming efficiency.
- **Metrics**: CSV (comma-separated values) for easy inspection and pandas loading.
- **Models**: Pickle (`.pkl`) or Joblib (`.joblib`) for `scikit-learn` artifacts.
- **Results**: JSON for structured data and statistical outputs.