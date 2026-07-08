# Data Model: Evaluating the Impact of Code Generation on Code Review Turnaround Time

## Overview

This document defines the data structures, schemas, and relationships for the project. All data flows from the GitHub API through preprocessing, analysis, and reporting stages.

## Entities

### PullRequest
Represents a single pull request fetched from GitHub.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `pr_id` | int | Unique PR ID | GitHub API |
| `repo_name` | str | Repository name (e.g., `owner/repo`) | GitHub API |
| `created_at` | datetime | PR creation timestamp | GitHub API |
| `merged_at` | datetime | PR merge timestamp (nullable) | GitHub API |
| `labels` | list[str] | List of PR labels | GitHub API |
| `commit_messages` | list[str] | List of commit messages for the PR | GitHub API |
| `is_ai_labeled` | bool | True if classified as AI-assisted | Derived |
| `turnaround_hours` | float | Turnaround time in calendar hours | Derived |
| `pr_size` | int | Total additions + deletions | Derived |
| `author_activity` | int | Total PRs by author in last 6 months | Derived |
| `exclusion_reason` | str | Reason for exclusion (if any) | Derived |

### StatisticalResult
Represents the output of the statistical analysis.

| Field | Type | Description |
|-------|------|-------------|
| `group` | str | "AI" or "Non-AI" |
| `n_total` | int | Total PRs before outlier removal (for reporting) |
| `n_clean` | int | PRs used in analysis (full dataset for MWU) |
| `mean` | float | Mean turnaround time |
| `median` | float | Median turnaround time |
| `std` | float | Standard deviation |
| `q1` | float | First quartile |
| `q3` | float | Third quartile |
| `iqr` | float | Interquartile range (Q3 - Q1) |
| `u_statistic` | float | Mann-Whitney U statistic (if applicable) |
| `p_value` | float | P-value from Mann-Whitney U test |
| `effect_size_r` | float | Effect size (r) |
| `stratified` | bool | True if stratified test was used |

### RepoMetadata
Represents metadata about the selected repositories.

| Field | Type | Description |
|-------|------|-------------|
| `repo_name` | str | Repository name |
| `language` | str | "Python" or "JavaScript" |
| `star_count` | int | Number of stars |
| `contributor_count` | int | Number of contributors |
| `pr_count` | int | Total PRs fetched |
| `ai_pr_count` | int | AI-labeled PRs |
| `non_ai_pr_count` | int | Non-AI-labeled PRs |

### SpotCheckResult
Represents the manual validation results.

| Field | Type | Description |
|-------|------|-------------|
| `pr_id` | int | PR ID |
| `predicted_label` | str | "AI" or "Non-AI" |
| `true_label` | str | "AI" or "Non-AI" (human verified) |
| `is_correct` | bool | True if prediction matches truth |

## Data Flow

1. **Raw Data**: `data/raw/github_prs.json` (unprocessed API response)
2. **Processed Data**: `data/processed/prs_cleaned.csv` (filtered, labeled, covariates added)
3. **Validation Data**: `data/spot_check/validation_report.csv` (manual spot-check results)
4. **Analysis Data**: `data/processed/stats_summary.csv` (descriptive stats, test results)
5. **Artifacts**: `artifacts/boxplot.png` (visualization)

## Constraints

- **Turnaround Time**: Must be non-negative.
- **Classification**: Boolean (`True`/`False`), derived from keywords/labels.
- **Outliers**: **Not removed** for primary statistical testing (full dataset used). IQR bounds used only for visualization.
- **Missing Data**: PRs with missing `merged_at` excluded; reason logged.

## File Formats

### Input (GitHub API)
- JSON (nested structure, paginated)

### Intermediate (Processed)
- CSV (flat, tabular)
  - Columns: `pr_id`, `repo_name`, `created_at`, `merged_at`, `labels`, `commit_messages`, `is_ai_labeled`, `turnaround_hours`, `pr_size`, `author_activity`, `exclusion_reason`

### Output (Analysis)
- CSV (statistical summary)
- PNG (visualization, ≥300 DPI)

## Validation Rules

- **PR ID**: Unique per repo.
- **Timestamps**: ISO 8601 format.
- **Labels**: Lowercase, trimmed.
- **Commit Messages**: List of strings, case-insensitive keyword matching.
- **Turnaround Hours**: Float, ≥0.
- **PR Size**: Integer, ≥0.
- **Author Activity**: Integer, ≥0.
