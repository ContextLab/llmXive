# Data Model: Investigating the Correlation Between Code Churn and Technical Debt

## Entity Relationship Diagram

```
Repository (1) ----< FileMetric (N) ----> CorrelationResult (1)
Repository (1) ----< ToolValidationLog (N)
Repository (1) ----< SensitivityResult (N)
```

## Core Entities

### Repository

| Attribute | Type | Description |
|-----------|------|-------------|
| `repo_id` | string | Unique identifier (`owner/repo`) |
| `owner` | string | GitHub owner |
| `name` | string | Repository name |
| `url` | string | GitHub URL |
| `stars` | integer | Star count |
| `language` | string | Primary language |
| `created_at` | datetime | Creation date |
| `last_commit` | datetime | Date of most recent commit |
| `contributor_count` | integer | Unique committers in last 2 years |
| `status` | string | `pending` / `success` / `failed` |
| `error_message` | string (nullable) | Error details if processing failed |

### FileMetric

| Attribute | Type | Description |
|-----------|------|-------------|
| `repo_id` | string | FK to Repository |
| `file_path` | string | Path within repo |
| `language` | string | Detected language |
| `total_lines_changed` | integer | **Raw** lines changed in last 2 years |
| `avg_loc` | number | Average LOC over 2 years (≥10) |
| `churn_density` | number (nullable) | **Deprecated**: `total_lines_changed` / `avg_loc` (kept for legacy) |
| `debt_score` | number | **Raw** debt score from static analysis |
| `debt_density` | number (nullable) | **Deprecated**: `debt_score` / `avg_loc` (kept for legacy) |
| `commit_count` | integer | Commits touching file (auxiliary) |
| `avg_cc` | number (nullable) | Average Cyclomatic Complexity |
| `avg_mi` | number (nullable, 0‑100) | Average Maintainability Index |
| `code_smells` | integer (nullable) | Code smell count (Semgrep) |

*Note*: Primary analysis uses `total_lines_changed`, `debt_score`, and `avg_loc` as a covariate. Density metrics are deprecated to avoid spurious correlation.

### CorrelationResult

| Attribute | Type | Description |
|-----------|------|-------------|
| `result_id` | string | Unique identifier |
| `repo_id` | string (nullable) | Null for aggregate |
| `correlation_type` | string | `pearson`, `spearman`, or `partial` |
| `r_value` | number | Correlation coefficient (from raw metrics) |
| `p_value` | number | P‑value |
| `n` | integer | Number of files (or repos for aggregate) |
| `confounders_controlled` | array[string] | Covariates used |
| `vif_values` | object | VIF per covariate |
| `threshold_used` | integer | LOC exclusion threshold |
| `bonferroni_adjusted` | boolean | Always `false` – replaced by meta‑analysis |
| `adjusted_p_value` | number (nullable) | Null when not adjusted |
| `timestamp` | datetime | Analysis timestamp |

### ToolValidationLog (new)

| Attribute | Type | Description |
|-----------|------|-------------|
| `tool_name` | string | `radon` or `semgrep` |
| `version` | string | Tool version |
| `github_stars` | integer | Star count at runtime |
| `citation` | string | Bibliographic reference (e.g., Kitchenham et al., 2009) |
| `retrieved_at` | datetime | When the metadata was fetched |

### SensitivityResult (new)

| Attribute | Type | Description |
|-----------|------|-------------|
| `threshold_loc` | integer | File‑size exclusion threshold (5, 10, 20) |
| `repo_id` | string (nullable) | Null for aggregate |
| `correlation_type` | string | `pearson` / `spearman` |
| `r_value` | number | Correlation coefficient |
| `p_value` | number | Corresponding p‑value |
| `n` | integer | Sample size |
| `timestamp` | datetime | When computed |

## Data Flow

1. **Raw Extraction** → `data/raw/` (metadata, git history, static analysis).  
2. **Processing** → `data/processed/unified_metrics.csv` (FileMetric).  
3. **Analysis** → `data/results/correlation_results.csv` (CorrelationResult).  
4. **Tool Validation** → `data/logs/tool_validation_log.csv` (ToolValidationLog).  
5. **Sensitivity** → `data/results/sensitivity_analysis.csv` (SensitivityResult).  
6. **Reporting** → `summary_report.txt` (aggregates above).

## Data Quality Rules

- Numeric fields non‑negative (except `r_value`).  
- `avg_loc` ≥ 10 (per FR‑007).  
- Missing values are explicit (`null`).  
- All files checksummed; raw data never overwritten.

## Schema Evolution

- Initial version: 1.0.0.  
- Changes documented in `derivation_notes.md`.  
- Backward compatibility maintained for legacy fields.