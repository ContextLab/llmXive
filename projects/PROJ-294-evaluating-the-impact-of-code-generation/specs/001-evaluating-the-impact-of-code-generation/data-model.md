# Data Model: Evaluating the Impact of Code Generation Models on Code Testability

## Overview

This document defines the data structures used throughout the project, ensuring consistency across data acquisition, generation, analysis, and reporting.

## Raw Data

### HumanEval Dataset (`data/raw/humaneval.parquet`)
- **Source**: HuggingFace `openai/openai_humaneval`
- **Format**: Parquet
- **Fields**:
  - `task_id` (string): Unique identifier for the task (e.g., "HumanEval/0").
  - `prompt` (string): The problem description.
  - `entry_point` (string): The function name to test.
  - `canonical_solution` (string): The reference human solution.
  - `test` (string): The test suite code.

## Generated Data

### Human Samples (`data/generated/human_samples.json`)
- **Format**: JSONL (JSON Lines)
- **Fields**:
  - `task_id` (string)
  - `code` (string): The `canonical_solution` extracted from the raw dataset.
  - `source` (string): "human"

### LLM Samples (`data/generated/codegen_samples.json`, `data/generated/sensitivity_samples.json`)
- **Format**: JSONL
- **Fields**:
  - `task_id` (string)
  - `code` (string): The generated code.
  - `model` (string): "codegen-mono-4b", "codegen-mono-350m", or "codellama-3b-q4"
  - `status` (string): "success" or "failed"
  - `error` (string, optional): Error message if failed.
  - `generation_time` (float): Time taken to generate.

## Analysis Data

### Metrics (`data/analysis/metrics.json`)
- **Format**: JSON
- **Structure**: List of objects, one per task.
- **Fields**:
  - `task_id` (string)
  - `model` (string): "human" or "llm" (with model name)
  - `cyclomatic_complexity` (float): >= 0
  - `static_branch_count` (integer): >= 0 (from radon)
  - `dynamic_branch_coverage` (float): 0.0 to 1.0 (from coverage.py)
  - `pass_rate` (float): 0.0 to 1.0
  - `is_valid` (boolean): True if `pass_rate` >= 0.80
  - `parse_error` (boolean): True if radon failed to parse

### Valid Task IDs (`data/analysis/valid_task_ids.json`)
- **Format**: JSON
- **Structure**: List of strings (task IDs).
- **Description**: Subset of tasks that passed the `pass_rate` filter. Used for secondary analysis.

### Full Sample Metrics (`data/analysis/full_sample_metrics.json`)
- **Format**: JSON
- **Structure**: Same as `metrics.json`.
- **Description**: All tasks, including those with `pass_rate` < 0.80. Used for primary analysis to avoid bias.

### Statistical Results (`data/analysis/statistical_results.json`)
- **Format**: JSON
- **Fields**:
  - `wilcoxon_p_value` (float): For valid pairs.
  - `wilcoxon_statistic` (float)
  - `ks_statistic` (float): For full sample.
  - `ks_p_value` (float)
  - `levene_statistic` (float): For variance comparison.
  - `levene_p_value` (float)
  - `mdes` (float): Minimum Detectable Effect Size (descriptive).
  - `achieved_power` (float): Post-hoc power.
  - `effect_size_ci_lower` (float): Lower bound of 95% CI.
  - `effect_size_ci_upper` (float): Upper bound of 95% CI.
  - `bias_analysis` (object): Results of MCAR test and difficulty comparison.

## Artifacts

### Artifact Hashes (`artifact_hashes.yaml`)
- **Format**: YAML
- **Structure**:
  ```yaml
  data/raw/humaneval.parquet: <sha256>
  data/generated/human_samples.json: <sha256>
  data/generated/codegen_samples.json: <sha256>
  data/analysis/metrics.json: <sha256>
  ...
  ```

### Sandbox Execution Logs (`code/sandbox_execution.log`)
- **Format**: Text
- **Description**: Logs from `code/sandbox.py` detailing execution environment setup and any errors.
- **Structure**: Timestamped entries with task ID, status, and error message.

## Logging

### Errors Log (`code/errors.log`)
- **Format**: Text
- **Content**: Timestamped error messages for generation and execution failures.

## Metadata

### Metadata (`data/metadata.yaml`)
- **Format**: YAML
- **Fields**:
  - `dataset_version`: Git commit hash or version tag.
  - `download_date`: ISO 8601 timestamp.
  - `model_versions`: Dict of model names and versions.
  - `quantization_level`: String (e.g., "Q4_K_M").