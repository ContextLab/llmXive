# Data Model: Leveraging LLMs for Automated Code Refactoring

## Overview

This document defines the data structures used in the pipeline, ensuring alignment with the `plan.md` and `spec.md`. All data is persisted in JSON or CSV formats within the `data/` directory.

## Core Entities

### 1. FunctionSample
Represents a single unit of analysis.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `id` | string | Unique identifier (hash of original code) | Generated |
| `original_code` | string | Raw Python source code | BigCode/CodeParrot |
| `refactored_code` | string | LLM-generated refactored code | WizardCoder API |
| `baseline_code` | string | Identity copy of original code | Generated |
| `is_parseable` | boolean | True if original code is valid Python | `ast.parse` |
| `is_refactor_valid` | boolean | True if refactored code is valid Python | `ast.parse` |
| `loc` | integer | Lines of Code | `radon` |
| `nesting_depth` | integer | Max nesting depth | `radon` |
| `param_count` | integer | Number of parameters | `ast` |
| `pep8_score` | float | PEP-8 adherence score | `pylint` |
| `has_docstring` | boolean | Presence of docstring | `ast` |
| `complexity_original` | integer | Cyclomatic complexity (original) | `radon` |
| `complexity_refactored` | integer | Cyclomatic complexity (refactored) | `radon` |
| `pylint_score_original` | float | Pylint score (0-10, original) | `pylint` |
| `pylint_score_refactored` | float | Pylint score (0-10, refactored) | `pylint` |
| `pylint_warning_count_original` | integer | Warning count (original) | `pylint` |
| `pylint_warning_count_refactored` | integer | Warning count (refactored) | `pylint` |
| `delta_complexity` | float | `complexity_original` - `complexity_refactored` | Derived |
| `delta_pylint_score` | float | `pylint_score_refactored` - `pylint_score_original` | Derived |
| `delta_warning_count` | float | `pylint_warning_count_original` - `pylint_warning_count_refactored` | Derived |
| `relative_improvement_complexity` | float | `delta_complexity / complexity_original` | Derived |
| `relative_improvement_score` | float | `delta_pylint_score / pylint_score_original` (if > 0) | Derived |
| `status` | string | "success", "refactor_failed", "parse_error" | Pipeline |

### 2. ModelResult
Output of the regression analysis.

| Field | Type | Description |
|-------|------|-------------|
| `predictor` | string | Name of the structural predictor |
| `coefficient` | float | Ridge Regression coefficient (β) |
| `std_error` | float | Robust standard error of the coefficient |
| `p_value` | float | P-value for the coefficient |
| `alpha` | float | Regularization parameter used |
| `adj_r_squared` | float | Adjusted R² of the model (for Ridge) |
| `f_statistic` | float | Global F-statistic |
| `f_p_value` | float | Global F-test p-value |
| `model_type` | string | "Ridge" or "GLM" |

### 3. ExperimentSummary
High-level summary of the run.

| Field | Type | Description |
|-------|------|-------------|
| `total_attempts` | integer | Total sampling attempts |
| `valid_functions` | integer | Number of valid, parseable functions |
| `refactor_success_rate` | float | Percentage of successful refactors |
| `mean_delta_complexity` | float | Mean improvement in complexity |
| `mean_relative_improvement_complexity` | float | Mean relative improvement in complexity |
| `mean_delta_pylint_score` | float | Mean improvement in pylint score |
| `mean_delta_warning_count` | float | Mean improvement in warning count |
| `t_statistic` | float | One-sample t-test statistic |
| `t_p_value` | float | One-sample t-test p-value |
| `significance` | boolean | True if p < 0.05 |

## File Layout

- `data/raw/samples.json`: List of `FunctionSample` objects (raw state).
- `data/processed/metrics.csv`: CSV version of `FunctionSample` for modeling (validated against `output.schema.yaml`).
- `data/processed/model_results.json`: List of `ModelResult` objects.
- `data/processed/experiment_summary.json`: Single `ExperimentSummary` object.