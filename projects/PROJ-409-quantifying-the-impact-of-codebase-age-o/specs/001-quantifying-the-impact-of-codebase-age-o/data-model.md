# Data Model: Quantifying the Impact of Codebase Age on LLM Code Understanding

## 1. Overview

This document defines the data structures used in the pipeline. All data is stored in CSV format for interoperability and simplicity, adhering to the "Data Hygiene" principle.

## 2. Entity Definitions

### 2.1 Snippet
Represents a single function-level code extract (Intermediate Stage).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `snippet_id` | string | Unique identifier (hash of content + repo + line) | Primary Key, Non-null |
| `file_path` | string | Relative path in repo (Foreign Key to File) | Non-null |
| `repo_url` | string | Source GitHub URL | Non-null |
| `function_name` | string | Name of the function | Non-null |
| `code_content` | string | The source code of the function | Non-null |
| `token_count` | integer | Number of tokens (approx) | $\ge$ 50 |
| `extraction_timestamp` | datetime | When extraction occurred | ISO 8601 |

### 2.2 FileAnalysisUnit
Represents the aggregated metrics for a single file (Primary Unit of Analysis).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `file_path` | string | Relative path in repo | Primary Key |
| `repo_url` | string | Source GitHub URL | Non-null |
| `median_commit_age_days` | float | Median age of commits touching this file | $\ge$ 0 |
| `low_confidence_age` | boolean | Flag if age calculation was based on < 2 commits | True/False |
| `mean_perplexity` | float | Mean perplexity of snippets in this file | > 1.0 or NaN |
| `syntax_validity_rate` | float | Proportion of snippets with valid syntax [0.0, 1.0] | [0.0, 1.0] or NaN |
| `mean_cyclomatic_complexity` | float | Mean complexity of snippets in this file | $\ge$ 1 |
| `mean_token_length` | float | Mean token length of snippets in this file | $\ge$ 50 |
| `snippet_count` | integer | Number of snippets in this file | $\ge$ 1 |
| `aggregation_timestamp` | datetime | When aggregation occurred | ISO 8601 |

### 2.3 CorrelationReport
Final aggregated results.

| Field | Type | Description |
|-------|------|-------------|
| `metric_name` | string | "age_vs_perplexity" or "age_vs_syntax_validity" |
| `spearman_rho` | float | Correlation coefficient |
| `p_value` | float | P-value of the test |
| `sample_size` | integer | Number of valid file pairs used |
| `significance_flag` | string | "significant" or "not_significant" |
| `controlled_for` | string | List of covariates used (e.g., "complexity, length") |

## 3. Data Flow

1. **Raw Input**: GitHub Repos -> `extraction/run_extraction.py` -> `data/extracted/snippets.csv`
2. **Inference**: `snippets.csv` -> `inference/run_inference.py` -> `data/extracted/snippet_metrics.csv`
3. **Aggregation**: `snippet_metrics.csv` -> `analysis/aggregate.py` -> `data/aggregated/file_analysis.csv`
4. **Analysis**: `file_analysis.csv` -> `analysis/correlation.py` -> `data/results/correlation_report.json`

## 4. Data Hygiene Rules

- **Immutability**: `snippets.csv` and `file_analysis.csv` are never modified. If re-extraction is needed, a new file with a timestamp suffix is created.
- **Checksums**: Every CSV file generated is checksummed (SHA-256) and recorded in the project state.
- **PII**: No personal emails or secrets are extracted. The `ast` parser ignores comments and strings that might contain sensitive data patterns (optional regex filter).

