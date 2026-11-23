# Data Model: Evaluating the Impact of Code Generation on Code Review Quality Using LLMs

## Overview

This document defines the data structures, schemas, and relationships for the project. It ensures data hygiene (Principle III) and reproducibility (Principle I).

## Entity Definitions

### 1. PullRequest (Raw)
Raw metadata fetched from the GitHub API.
*   `pr_id`: Integer (GitHub PR number)
*   `repo`: String (e.g., "psf/requests")
*   `user_login`: String (Author username)
*   `created_at`: ISO8601 Timestamp
*   `merged_at`: ISO8601 Timestamp (Nullable)
*   `comments_count`: Integer
*   `commits_count`: Integer
*   `additions`: Integer
*   `deletions`: Integer
*   `diff_url`: String (URL to fetch diff)
*   `commit_message`: String (Full message)

### 2. PullRequest (Processed)
Derived entity with classification and metrics.
*   `pr_id`: Integer
*   `repo`: String
*   `source_type`: Enum (`llm`, `human`)
*   `confidence_score`: Float (0.0 - 1.0)
*   `flagged_for_audit`: Boolean
*   `comment_count`: Integer
*   `time_to_merge_minutes`: Float
*   `review_cycles`: Integer (Heuristic: `commits_count` or `comments_count` / 2)
*   `complexity_score`: Float (Cyclomatic Complexity)
*   `loc`: Integer (Lines of Code in diff)
*   `entropy_score`: Float (Secondary detector score)
*   `hour_of_day`: Integer (0-23, extracted from `created_at`)
*   `day_of_week`: Integer (0-6, extracted from `created_at`)

### 3. StatisticalResult
Aggregated results of hypothesis tests.
*   `metric_name`: String
*   `group_a_mean`: Float (LLM)
*   `group_b_mean`: Float (Human)
*   `u_statistic`: Float (Primary Mann-Whitney U)
*   `t_statistic`: Float (Sensitivity t-test)
*   `p_value_u`: Float (Mann-Whitney p-value)
*   `p_value_t`: Float (t-test p-value)
*   `effect_size_u`: Float (Rank-biserial correlation)
*   `effect_size_t`: Float (Cohen's d)
*   `is_significant_u`: Boolean
*   `is_significant_t`: Boolean
*   `sample_size_a`: Integer
*   `sample_size_b`: Integer

### 4. AuditSample
Manual validation records.
*   `pr_id`: Integer
*   `predicted_label`: String (Primary Signature)
*   `human_ground_truth`: String (Manual judgment)
*   `detector_score`: Float (Secondary detector score, per SC-004)
*   `notes`: String
*   `correct`: Boolean (Human vs. Predicted)

## Data Flow

1.  **Ingestion**: `fetch_github.py` -> `data/raw/prs_raw.json` (Batched).
2.  **Transformation**: `classify_prs.py` + `extract_metrics.py` -> `data/processed/prs_labeled.csv` (includes temporal covariates).
3.  **Analysis**: `statistical_tests.py` -> `data/processed/results.json` (aggregated stats).
4.  **Audit**: `manual_validation.py` -> `data/processed/audit_log.csv`.
5.  **Sensitivity**: `sensitivity_analysis.py` -> `data/processed/sensitivity_results.json`.

## Constraints

*   **PII**: `user_login` is public; no email addresses stored.
*   **Checksums**: Every file in `data/` is checksummed (SHA-256) and recorded in `state/`.
*   **Immutability**: Raw files are never modified. Derivations create new files.
