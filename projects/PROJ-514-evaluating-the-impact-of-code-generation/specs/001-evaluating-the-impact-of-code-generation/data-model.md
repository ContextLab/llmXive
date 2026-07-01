# Data Model: Evaluating Code Generation Impact on Code Smell Frequency

## Overview
This document defines the data structures used to store code samples, static analysis results, and statistical outcomes. All data is stored in `data/` and processed into a final CSV for analysis.

## Entities

### 1. CodeSample
Represents a single unit of code (Human or LLM).
- **Attributes**:
    - `sample_id`: UUID (Primary Key)
    - `source_type`: Enum {`human`, `llm`}
    - `repository_id`: String (GitHub URL or Repo Name)
    - `issue_id`: String (Linked Issue/PR ID)
    - `task_id`: String (For LLM: Prompt ID)
    - `language`: Enum {`python`, `java`}
    - `file_path`: String (Relative path in `data/raw/`)
    - `function_name`: String
    - `is_fresh_commit`: Boolean
    - `metadata_json`: String (JSON blob for LLM: model, prompt, seed; for Human: commit SHA)

### 2. SmellMetric
Represents the output of static analysis for a single sample.
- **Attributes**:
    - `metric_id`: UUID
    - `sample_id`: UUID (Foreign Key to CodeSample)
    - `smell_type`: Enum {`long_method`, `duplicated_code`, `feature_envy`, `long_parameter_list`}
    - `count`: Integer (Number of occurrences)
    - `threshold_used`: Integer (The threshold value used for detection)
    - `continuous_metric_value`: Float (e.g., Cyclomatic Complexity, Lines of Code)
    - `tool_version`: String
    - `validity_flag`: Boolean (True if tool ran successfully)

### 3. StatResult
Represents the outcome of a statistical test.
- **Attributes**:
    - `result_id`: UUID
    - `smell_type`: String
    - `test_method`: String (e.g., `welch_t`, `mann_whitney_u`)
    - `p_value`: Float
    - `p_value_corrected`: Float (Bonferroni adjusted)
    - `effect_size`: Float (Cohen's d or equivalent)
    - `confidence_interval_lower`: Float
    - `confidence_interval_upper`: Float
    - `correction_method`: String (e.g., `bonferroni`)

## Data Flow
1.  **Raw**: `data/raw/human_samples/` and `data/raw/llm_samples/` contain source files.
2.  **Intermediate**: `data/intermediate/analysis_results.json` contains the `SmellMetric` records.
3.  **Processed**: `data/processed/smell_metrics.csv` is a flattened table joining `CodeSample` and `SmellMetric` for statistical analysis.

## Storage Constraints
- **Format**: JSON for intermediate, CSV for final analysis.
- **Checksums**: All files in `data/` are checksummed (SHA-256).
- **PII**: No PII allowed. Repository IDs must be public.
