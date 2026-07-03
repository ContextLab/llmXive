# Data Model: Quantifying the Association Between Code Authorship Diversity and Software Security

## Overview

This document defines the data schemas for the pipeline. All data flows from raw downloads to processed CSVs, then to model inputs.

## Entity Definitions

### 1. Repository Metrics (Processed)
Derived from local git clones and `cloc` execution.
- **Source**: `code/data/extract_github.py`
- **Target**: `data/processed/repo_metrics.csv`
- **Keys**: `repo_url` (PK)

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `repo_url` | string | Full HTTPS URL of the repository. | Input List |
| `primary_language` | string | Dominant language (e.g., Python, JavaScript). | GitHub API / cloc |
| `raw_line_count` | integer | Total lines of code from `cloc`. | cloc |
| `kloc` | float | `raw_line_count / 1000`. | Derived |
| `unique_authors` | integer | Count of unique emails/names in `git log`. | git log |
| `author_count` | integer | Same as `unique_authors` (alias for model). | Derived |
| `project_age_years` | float | Years since first commit. | git log |
| `release_count` | integer | Number of tags/releases. | GitHub API |
| `num_dependencies` | integer | Number of dependencies (if available). | GitHub API / `package.json` |
| `cve_count` | integer | Number of matching CVEs from NVD feed. | NVD Dataset Join |
| `cve_density` | float | `cve_count / kloc` (Descriptive only). | Derived |

### 2. Model Results
Output of the statistical analysis.
- **Source**: `code/analysis/fit_models.py`
- **Target**: `data/processed/model_results.json`

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | "Poisson" or "NegativeBinomial" |
| `coef_author_count` | float | Coefficient for author count. |
| `se_author_count` | float | Standard error. |
| `pvalue_raw` | float | Raw p-value. |
| `pvalue_adj` | float | Benjamini-Hochberg adjusted p-value. |
| `ci_lower` | float | 95% Confidence Interval Lower. |
| `ci_upper` | float | 95% Confidence Interval Upper. |
| `coef_log_kloc` | float | Coefficient for `log(kloc)` (predictor, not offset). |
| `vif_scores` | object | Map of predictor -> VIF value. |
| `convergence_status` | string | "OK" or "FAILED" |
| `power_analysis` | object | Minimum Detectable Effect Size (MDES) and power estimate. |

## Data Lineage

1.  **Raw**: Downloaded NVD JSON feed -> `data/raw/`.
2.  **Raw**: Cloned Repos (local git, full clone) -> Temporary workspace (cleaned after).
3.  **Processed**: `repo_metrics.csv` (Join of Raw Git + Raw NVD).
4.  **Final**: `model_results.json` (Output of GLM).
