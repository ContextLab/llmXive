# Data Model: Leveraging LLMs for Automated Test Case Generation

## Overview
This document defines the data structures, schemas, and flow for the test generation and analysis pipeline. All data flows from the raw Defects4J Parquet input to the final statistical report.

## Data Flow

1. **Input**: `data/raw/defects4j_prompts.parquet` (Downloaded from verified URL).
2. **Processed**: `data/interim/prompt_batch.jsonl` (Formatted prompts with metadata).
3. **Generated**: `data/interim/generated_tests/` (Directory of `.java` files).
4. **Executed**: `data/interim/coverage_results/` (JaCoCo XML/CSV outputs).
5. **Aggregated**: `data/processed/coverage_metrics.csv` (Final metrics for analysis).
6. **Analyzed**: `data/processed/analysis_results.json` (Statistical summary).

## Entity Definitions

### BugFixDescription
- **Source**: Defects4J Parquet.
- **Fields**: `project_id`, `version`, `bug_id`, `description_text`, `source_url`, `changed_lines` (list of line numbers).
- **Usage**: Input for LLM prompt and scope isolation.

### GeneratedTest
- **Source**: LLM Output.
- **Fields**: `project_id`, `test_class_name`, `source_code`, `compile_status` (success/fail), `compile_error_msg`, `execution_status`, `execution_time`, `changed_lines_coverage` (coverage on specific lines).
- **Usage**: Subject of coverage measurement.

### CoverageMetric
- **Source**: JaCoCo Report (filtered for changed lines).
- **Fields**: `project_id`, `test_type` (generated/manual), `line_coverage_percent`, `branch_coverage_percent`, `assertion_count`, `line_count`, `changed_lines_coverage` (coverage on specific lines).
- **Usage**: Primary data for statistical comparison.

### AnalysisResult
- **Source**: Statistical Script.
- **Fields**: `test_type` (Wilcoxon/t-test), `p_value`, `mean_difference`, `confidence_interval` (lower/upper), `effect_size` (Cohen's d or rank-biserial), `power` (achieved), `sample_size`, `conclusion`, `is_exploratory` (boolean flag).
- **Usage**: Final report content. **Crucial**: `is_exploratory` must be true if power < 0.8.

## Storage Strategy

- **Raw Data**: Immutable. Downloaded once, checksummed.
- **Interim Data**: Transient. Can be regenerated if `coverage_metrics.csv` is deleted.
- **Processed Data**: Versioned. `coverage_metrics.csv` is the "Single Source of Truth" for the analysis.
- **Checksums**: Recorded in `state/projects/PROJ-052-.../artifact_hashes`.

## Constraints & Validation

- **File Formats**:
  - Input: Parquet (verified).
  - Output: CSV (for analysis), JSON (for structured results).
- **Data Integrity**:
  - No PII (software bug descriptions are public).
  - All derived files must reference the source file hash.
  - **Schema Validation**: All output files must pass validation against `contracts/` schemas via `jsonschema` before any statistical analysis proceeds.