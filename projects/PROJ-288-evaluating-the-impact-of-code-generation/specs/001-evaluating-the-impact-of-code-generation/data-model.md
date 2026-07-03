# Data Model: Evaluating the Impact of Code Generation on Code Review Time

## Overview

This document defines the data structures used in the `projects/PROJ-288-evaluating-the-impact-of-code-generation` pipeline. All data flows from `data/raw/` (immutable) to `data/processed/` (derived).

## Entities

### 1. PullRequest (Raw)
*Source*: GitHub API Response / Verified PR Datasets
*Location*: `data/raw/prs_YYYYMMDD.json`

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `repo_id` | string | Unique repository identifier (e.g., "owner/repo") | Not Null |
| `pr_number` | integer | Pull Request number | > 0 |
| `author` | string | Username of the PR author | Not Null |
| `title` | string | PR Title | Max 500 chars |
| `body` | string | PR Body text | - |
| `created_at` | datetime | ISO8601 timestamp of PR creation | Not Null |
| `merged_at` | datetime | ISO8601 timestamp of merge (null if open) | - |
| `closed_at` | datetime | ISO8601 timestamp of close (null if open) | - |
| `comments_count` | integer | Total number of comments on the PR | >= 0 |
| `commits_count` | integer | Total number of commits in the PR | >= 1 |
| `lines_added` | integer | Total lines added in the PR | >= 0 |
| `lines_deleted` | integer | Total lines deleted in the PR | >= 0 |
| `review_comments` | list | List of review comment objects | - |

### 2. PullRequest (Processed)
*Source*: `data/raw/prs_YYYYMMDD.json` + Classification Logic
*Location*: `data/processed/prs_classified.parquet`

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `repo_id` | string | Repository ID | Not Null |
| `pr_number` | integer | PR Number | > 0 |
| `origin_label` | string | **Disclosure Status**: "Disclosing" (LLM keywords present) or "Non-Disclosing" | Enum |
| `confidence_score` | float | Heuristic confidence (0.0 - 1.0) for *disclosure* signal | [0, 1] |
| `formatting_consistency` | float | Style score (0.0 - 1.0) - used as covariate | [0, 1] |
| `comment_density` | float | Ratio of comments to code - used as covariate | [0, 1] |
| `first_review_time` | float | Minutes from creation to first comment | >= 0 |
| `total_review_time` | float | Minutes from creation to merge/close | >= 0 |
| `reviewer_count` | integer | Number of unique reviewers | >= 0 |
| `reviewer_experience_proxy` | float | Proxy for reviewer experience (e.g., karma, contribution count) | >= 0 |
| `code_size` | integer | Total lines changed (added + deleted) | >= 0 |
| `is_outlier` | boolean | Flagged if time > 30 days or < 0 | - |
| `validation_flag` | string | "Manual", "Auto", or "LowConfidence" | Enum |

### 3. ReviewMetrics (Aggregated)
*Source*: Analysis Results
*Location*: `data/processed/metrics_summary.json`

| Field | Type | Description |
| :--- | :--- | :--- |
| `group` | string | "Disclosing" or "Non-Disclosing" |
| `sample_size` | integer | Count of PRs in group |
| `median_time` | float | Median review time (minutes) |
| `mean_time` | float | Mean review time |
| `std_dev` | float | Standard deviation |
| `shapiro_p_value` | float | Normality test p-value |
| `code_size_slope` | float | Regression slope for code size in this group (SC-003) |

### 4. ValidationLog
*Source*: Manual Review Process
*Location*: `data/validation_log.csv`

| Field | Type | Description |
| :--- | :--- | :--- |
| `pr_id` | string | Unique ID (repo_id#pr_number) |
| `auto_label` | string | Heuristic label (Disclosure status) |
| `human_label` | string | Manual verified disclosure status |
| `discrepancy` | boolean | True if labels differ |
| `notes` | string | Manual reviewer notes |

## Data Flow

1.  **Fetch**: `fetch_prs.py` pulls from GitHub API -> `data/raw/prs_raw.json`.
2.  **Clean**: `process.py` calculates time deltas, removes outliers -> `data/processed/prs_clean.parquet`.
3.  **Classify**: `classify.py` applies keyword-based labeling (Disclosure status) and style heuristics (covariates) -> `data/processed/prs_classified.parquet`.
4.  **Validate**: Manual review generates `data/validation_log.csv`.
5.  **Analyze**: `models.py` computes metrics and SIMEX correction -> `data/processed/metrics_summary.json`.

