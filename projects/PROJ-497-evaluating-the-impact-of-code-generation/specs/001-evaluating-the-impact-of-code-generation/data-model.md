# Data Model: Evaluating the Impact of Code Generation Models on Code Vulnerability Density

## Overview

This document defines the data structures, schemas, and relationships used throughout the research pipeline. All data is stored in `data/` (raw) and `data/processed/` (derived), with checksums recorded in `state/`.

## Entity Definitions

### CodeSample
Represents a single unit of code (generated or human) with attributes.
- `id`: Unique identifier (UUID).
- `source_type`: "LLM" or "Human".
- `model_name`: Name of the LLM (if LLM) or "Human".
- `benchmark_name`: "HumanEval" or "MBPP".
- `task_id`: Identifier of the coding task.
- `lines_of_code`: Integer count of lines.
- `vulnerability_count`: Integer count of vulnerabilities (raw).
- `is_valid`: Boolean (passed benchmark tests).
- `content_hash`: SHA-256 of the code content.

### AggregatedTaskRecord
Represents the aggregated data for a single task (Unit of Analysis).
- `task_id`: Unique identifier for the task.
- `benchmark_name`: "HumanEval" or "MBPP".
- `source_type`: "LLM" (aggregated) or "Human".
- `model_name`: "Human" or "Aggregate_StarCoder" / "Aggregate_CodeGen".
- `lines_of_code`: Mean lines of code for the group.
- `vulnerability_count`: Mean vulnerability count for the group.
- `sample_count`: Number of samples aggregated (for LLM).
- `is_valid`: Boolean (task had at least one valid sample).

### VulnerabilityReport
Represents the output of the static analysis tool for a specific file.
- `file_path`: Path to the code file.
- `cwe_id`: Common Weakness Enumeration ID (e.g., "CWE-79").
- `severity`: "LOW", "MEDIUM", "HIGH", "CRITICAL".
- `line_number`: Line number in the source file.
- `description`: Text description of the vulnerability.

### StatisticalResult
Represents the outcome of a hypothesis test.
- `test_type`: "ZINB" or "Permutation".
- `p_value`: Float.
- `confidence_interval`: Tuple (lower, upper).
- `effect_size`: Incidence Rate Ratio (IRR).
- `adjusted_p_value`: Float (after correction).
- `convergence_status`: "SUCCESS" or "FAILED".
- `power`: Float (if applicable).
- `flag`: "OK", "UNDER_POWERED", "INSUFFICIENT_DATA".

## Data Flow

1.  **Download**: Raw datasets (HumanEval, MBPP) are downloaded to `data/raw/`.
2.  **Generation**: LLM generates code samples, validated against tests. Output: `data/generated/`.
3.  **Analysis**: Bandit runs on `data/generated/` and `data/human/`. Output: `data/processed/vulnerability_reports.json`.
4.  **Aggregation**: Reports are aggregated into `data/processed/aggregated_analysis_dataset.csv` (One row per task).
5.  **Stats**: Statistical tests run on `aggregated_analysis_dataset.csv`. Output: `results/statistical_results.json`.
6.  **Visualization**: Plots generated from `statistical_results.json`. Output: `results/plots/`.

## File Formats

- **Raw Datasets**: Parquet (from HuggingFace).
- **Generated Code**: `.py` files in `data/generated/`.
- **Vulnerability Reports**: JSON (list of objects).
- **Aggregated Dataset**: CSV (rows = tasks, columns = metrics).
- **Statistical Results**: JSON.
- **Visualizations**: PNG/SVG.

## Checksums & Hygiene

- All files in `data/raw/` are checksummed upon download.
- Derived files in `data/processed/` are checksummed upon creation.
- Checksums are stored in `state/artifact_hashes.yaml`.
- No file is modified in place; new versions are created with new hashes.
