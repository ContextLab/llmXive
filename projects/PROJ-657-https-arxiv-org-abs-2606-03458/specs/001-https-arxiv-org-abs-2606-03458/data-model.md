# Data Model: KVarN Quantization Study

## 1. Overview

This document defines the data structures for the KVarN experiment. All data flows through `code/src/` and is persisted in `data/`. The model supports reproducibility (Constitution Principle I) and data hygiene (Principle III). The `contracts/` directory contains the source of truth for the JSONL schemas used in `data/processed/`, ensuring synchronization with this document. The `contracts` files are explicitly linked to the data flow steps below to ensure the data model and schemas are synchronized.

## 2. Entity Definitions

### 2.1 QuantizationConfig
Configuration for the quantization method.
- `method`: str (`"uniform"`, `"kvarn"`)
- `bit_width`: int (e.g., 8)
- `variance_window`: int (e.g., 32)
- `epsilon`: float (e.g., 1e-8)
- `seed`: int

### 2.2 InferenceResult
A single record of an inference run.
- `instance_id`: str (unique ID for the prompt)
- `benchmark`: str (`"MATH500"`, `"AIME24"`, etc.)
- `method`: str (`"uniform"`, `"kvarn"`)
- `prompt`: str (truncated to 512 tokens for storage)
- `generated_response`: str
- `ground_truth`: str
- `exact_match`: bool (True/False)
- `mse_per_token`: list[float] (reconstruction error per token, **required for slope analysis**)
- `cumulative_mse`: float (average MSE over the sequence)
- `peak_memory_mb`: float
- `generation_time_s`: float
- `timestamp`: datetime
- `config_hash`: str (hash of `QuantizationConfig`)
- `kv_cache_size_bytes`: int (size of KV cache in bytes, **required for FR-007**)
- `reduction_percent`: float (size reduction compared to full-precision baseline, **required for FR-007**)

### 2.3 BenchmarkDataset
Metadata about the dataset used.
- `name`: str
- `source_url`: str
- `version`: str
- `split`: str
- `checksum`: str (SHA-256)
- `num_samples`: int

### 2.4 AnalysisSummary
Aggregate metrics calculated across a set of instances.
- `benchmark`: str
- `method`: str
- `num_instances`: int
- `accuracy`: float
- `mean_mse`: float
- `correlation_mse_accuracy`: float (Pearson correlation between cumulative MSE and exact_match, **required for FR-009**)
- `error_slope`: float (Linear regression slope of cumulative MSE vs token position)
- `slope_p_value`: float (Significance of slope difference if comparing methods)

## 3. Data Flow

1. **Ingestion**: `data/raw/` contains downloaded datasets. Checksums verified.
2. **Processing**: `code/src/benchmarks/loader.py` reads raw data and yields `Prompt` objects.
3. **Execution**: `code/src/inference/engine.py` runs inference, producing `InferenceResult`. **The `contracts/inference_result_schema.schema.yaml` defines the strict schema for this output.**
4. **Aggregation**: `code/src/analysis/stats.py` aggregates `InferenceResult` into `AnalysisSummary` (CSV/JSONL). **The `contracts/analysis_summary_schema.schema.yaml` defines the strict schema for this output.**
5. **Analysis**: `code/src/analysis/plots.py` generates figures from aggregated data.
6. **Schema Validation**: All JSONL files in `data/processed/` are validated against the schemas in `contracts/`.

## 4. Storage Schema

### 4.1 File Formats
- **Raw Data**: JSONL, Parquet (as per source).
- **Logs**: JSONL (one line per `InferenceResult`).
- **Summary**: CSV (aggregated metrics).
- **Config**: YAML.

### 4.2 Directory Structure
```text
data/
├── raw/
│   ├── math500_test.jsonl
│   ├── aime24_test.parquet
│   └── ...
├── processed/
│   ├── results_uniform.jsonl
│   ├── results_kvarn.jsonl
│   ├── summary_stats.csv
│   ├── analysis_summary.jsonl
│   └── plots/
│       ├── error_accumulation.png
│       └── accuracy_comparison.png
└── checksums.txt
```
