# Data Model: Evaluating the Impact of Code Generation Models on Code Testability

## Overview

This document defines the data structures for the project, ensuring alignment with the **Constitution Principle III (Data Hygiene)** and **IV (Single Source of Truth)**. All data is stored in JSON/YAML formats for programmatic access and validation.

## Raw Data

### HumanEval Benchmark
- **Source**: `data/raw/humaneval.parquet`
- **Format**: Parquet (converted to JSON for processing if needed).
- **Fields**:
  - `task_id`: String (e.g., "HumanEval/0")
  - `prompt`: String (Code snippet to complete)
  - `canonical_solution`: String (Human reference)
  - `test`: String (Unit tests)
  - `entry_point`: String (Function name)

## Processed Data

### Metrics Dataset (`data/analysis/metrics.json`)
This is the **Single Source of Truth** for all statistical analysis.
- **Format**: JSON Array
- **Schema**: See `contracts/metrics.schema.yaml`
- **Key Fields**:
  - `mutation_score`: Float (0.0 to 1.0) - Primary measure of **Testability**.
  - `pass_rate`: Integer (0 or 1) - Measure of **Correctness**.
  - `cyclomatic_complexity`: Integer - Static complexity.

### Artifact Hashes (`state/artifact_hashes.yaml`)
- **Format**: YAML
- **Content**: SHA256 hashes of all files in `data/` and `code/`.

### Validation Results (`state/validation_results.yaml`)
- **Format**: YAML
- **Content**: Results of statistical tests and citation validation.

### Power Analysis (`state/power_analysis.yaml`)
- **Format**: YAML
- **Content**: A Priori and Post-Hoc power analysis results.

## Metadata

### Project Metadata (`data/metadata.yaml`)
- **Fields**:
  - `dataset_version`: Version of HumanEval used.
  - `model_version`: Hash/ID of the LLM used for generation.
  - `seed`: Random seed used for generation.
  - `timestamp`: ISO8601 timestamp of generation.

## Data Flow

1.  **Download**: `download_data.py` fetches HumanEval -> `data/raw/humaneval.parquet`.
2.  **Generate**: `generate_code.py` reads raw, calls LLM, saves to `data/analysis/model_outputs/`.
3.  **Analyze**: `analyze_metrics.py` reads raw + generated, runs Radon/Mutmut/Coverage, writes `data/analysis/metrics.json`.
4.  **Validate**: `validate_citations.py` checks references -> `state/validation_report.yaml`.
5.  **Stats**: `statistical_tests.py` reads `metrics.json`, writes `state/validation_results.yaml` and `state/power_analysis.yaml`.
6.  **Report**: `report_generator.py` reads `metrics.json`, `state/validation_results.yaml`, `state/power_analysis.yaml` -> Markdown report.
