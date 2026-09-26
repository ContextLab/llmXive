# Data Model: Quantifying Hallucination in LLM-Generated API Documentation

## Overview

This document defines the data structures used in the pipeline. All data is persisted as CSV or JSON to ensure transparency and reproducibility.

## Entities

### 1. FunctionRecord
Represents a single code unit from the dataset.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique identifier (hash of code + line number) | Derived |
| `source_code` | string | Raw Python source code | CodeSearchNet |
| `reference_docstring` | string | Original docstring (if exists) | CodeSearchNet |
| `func_name` | string | Function name | CodeSearchNet |
| `token_count_source` | int | Token count of **source code** | Calculated |
| `token_count_gen` | int | Token count of generated description | Calculated |
| `naming_style` | string | `snake_case`, `camelCase`, or `other` | Calculated |
| `cyclomatic_complexity` | float | Complexity score (Radon) | Calculated |
| `generated_description_codegen` | string | Description from `codegen-350M` | Generated |
| `generated_description_starcoder` | string | Description from `starcoderbase-1b` | Generated |
| `entity_f1_codegen` | float | Hallucination index (F1) for codegen | Calculated |
| `entity_f1_starcoder` | float | Hallucination index (F1) for starcoder | Calculated |
| `precision_hallucination_codegen` | float | Precision component of F1 (invented entities) | Calculated |
| `recall_omission_codegen` | float | Recall component of F1 (missing entities) | Calculated |

### 2. ManualScoreRecord
Represents a human-annotated validation entry.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `id` | string | Matches `FunctionRecord.id` | Derived |
| `human_score_raw` | int | Raw score 0-3 from **Behavioral Consistency** rubric | Human Input |
| `human_score_norm` | float | Normalized score (0.0-1.0) | Calculated |
| `annotator_id` | string | Identifier for the human annotator | System |

### 3. AnalysisResult
Aggregated statistical output.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `model_name` | string | `codegen-350M` or `starcoderbase-1b` | Config |
| `correlation_length` | float | Spearman $\rho$ for length | Calculated |
| `p_value_length` | float | Raw p-value for length | Calculated |
| `p_value_length_adj` | float | Bonferroni-adjusted p-value | Calculated |
| `correlation_naming` | float | Mann-Whitney U statistic or Point-Biserial $\rho$ | Calculated |
| `p_value_naming` | float | Raw p-value for naming | Calculated |
| `p_value_naming_adj` | float | Bonferroni-adjusted p-value | Calculated |
| `correlation_complexity` | float | Spearman $\rho$ for complexity | Calculated |
| `p_value_complexity` | float | Raw p-value for complexity | Calculated |
| `p_value_complexity_adj` | float | Bonferroni-adjusted p-value | Calculated |
| `regression_coefficients` | dict | Coefficients for MLR model (controlled by source length) | Calculated |
| `vif_scores` | dict | Variance Inflation Factors for predictors | Calculated |
| `sensitivity_data` | list | Threshold sweep results | Calculated |
| `manual_validation_correlation` | float | Correlation between F1 and Human Score (Behavioral) | Calculated |
| `validation_flag` | string | "PASS" if $r \ge 0.7$, else "NEEDS_REVIEW" | Calculated |

## Data Flow

1.  **Raw Data**: `data/raw/*.parquet` (CodeSearchNet)
2.  **Processed Data**: `data/processed/records.csv` (FunctionRecord)
3.  **Manual Data**: `data/manual/scores.csv` (ManualScoreRecord) - Produced by T030c.
4.  **Final Report**: `results/final_report.json` (AnalysisResult)

## Constraints

- **Null Handling**: Missing docstrings are filtered out. Missing complexity metrics are set to `NaN` and excluded from regression.
- **Range**: `entity_f1`, `precision_hallucination`, `recall_omission`, and `human_score_norm` are strictly in $[0.0, 1.0]$.
- **Uniqueness**: `id` must be unique across all records.
- **Independence**: The `human_score_raw` is derived from a behavioral rubric, independent of the AST-based automated metric.
- **No Coupling**: Regression models do not include `token_count_gen` as a predictor.