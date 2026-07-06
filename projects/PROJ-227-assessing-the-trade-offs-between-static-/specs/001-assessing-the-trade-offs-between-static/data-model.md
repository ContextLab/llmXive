# Data Model: Assessing the Trade-offs Between Static and Dynamic Analysis for LLM-Generated Code

## Overview

This document defines the data structures used in the analysis pipeline. All data is stored in CSV/JSON formats for reproducibility and ease of processing.

## Entities

### 1. Code Snippet
- **ID**: Unique identifier (e.g., `humaneval-001`, `js-001`, `stack-001`).
- **Language**: One of `Python`, `JavaScript`, `Java`.
- **Source Dataset**: Name of the original dataset (e.g., `HumanEval`, `HumanEval-X`, `TheStack`).
- **Code**: Source code string.
- **Tests**: Unit test code string (if available; `null` for `static_only` samples).
- **Checksum**: SHA-256 hash of the raw snippet.
- **Oracle Type**: `native_test`, `synthetic_test`, `unavailable` (for `static_only`).

### 2. Analysis Log
- **Snippet ID**: Foreign key to `Code Snippet`.
- **Tool**: Name of the analysis tool (e.g., `CodeQL`, `SonarQube`, `PyLint`, `pytest`).
- **Type**: `static` or `dynamic`.
- **Result**: `detected`, `clean`, `timeout`, `tool_failure`, `untestable_dynamic`.
- **Details**: JSON string with tool-specific output (e.g., vulnerability ID, test failure message).
- **Timestamp**: ISO-8601 timestamp of execution.
- **Resource Usage**: CPU cores, RAM (MB), duration (seconds).
- **Issue Count**: Integer count of issues found (for static analysis).

### 3. Aggregated Metrics
- **Language**: One of `Python`, `JavaScript`, `Java`.
- **Metric**: `detection_rate`, `pass_rate`, `correlation_coefficient`.
- **Method**: `static`, `dynamic`, `combined`.
- **Value**: Float (0.0–1.0) or correlation coefficient.
- **Sample Size**: Integer (n).

### 4. Statistical Report
- **Test Name**: e.g., `Spearman_Correlation`, `Chi_Squared_Independence`, `Sensitivity_Analysis`.
- **Alpha**: Significance level (0.01, 0.05, 0.1).
- **P-Value**: Float.
- **Conclusion**: `significant` or `not_significant`.
- **Stratum**: Language (if stratified).
- **Multiplicity Adjusted**: Boolean (True if correction applied).
- **Methodology Note**: Description of the test used (e.g., "Spearman correlation for distinct constructs").

## Data Flow

1. **Raw Data** → `data/raw/` (downloaded, checksummed).
2. **Processed Snippets** → `data/processed/snippets.csv` (filtered, validated).
3. **Analysis Logs** → `data/processed/analysis_logs.jsonl` (one per snippet/tool).
4. **Aggregated Metrics** → `data/processed/metrics.csv`.
5. **Statistical Report** → `data/processed/statistical_report.json`.

## Constraints

- **No PII**: Code snippets must not contain personally identifiable information.
- **Checksums**: All raw files must be checksummed; derived files must reference raw checksums.
- **Immutable Raw Data**: Raw data is never modified; derivations create new files.
- **Schema Validation**: All output files must conform to `contracts/*.schema.yaml`.
- **Static-Only Handling**: Snippets with `oracle_type = unavailable` are excluded from dynamic metrics and comparative tests.