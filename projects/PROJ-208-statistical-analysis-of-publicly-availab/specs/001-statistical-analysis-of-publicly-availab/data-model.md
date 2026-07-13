# Data Model: GitHub Issue Resolution Analysis

## Overview
This document defines the core entities, attributes, and relationships for the statistical analysis of GitHub issue resolution times. The data model supports the collection, preprocessing, and analysis of issue lifecycle data from public GitHub repositories.

## Core Entities

### Repository
Represents a GitHub repository from which issues are collected.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `repo_id` | integer | Unique internal identifier for the repository | Generated |
| `full_name` | string | Full GitHub repository name (owner/repo) | GitHub API |
| `owner` | string | Repository owner (organization or user) | GitHub API |
| `name` | string | Repository name | GitHub API |
| `language` | string | Primary programming language | GitHub API |
| `created_at` | timestamp | Repository creation timestamp | GitHub API |
| `stargazers_count` | integer | Number of stargazers | GitHub API |
| `forks_count` | integer | Number of forks | GitHub API |
| `open_issues_count` | integer | Current open issues count | GitHub API |
| `archived` | boolean | Whether the repository is archived | GitHub API |

### Issue
Represents a GitHub issue with its lifecycle timestamps and metadata.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `issue_id` | integer | GitHub issue ID (unique within repo) | GitHub API |
| `repository_id` | integer | Foreign key to Repository | Derived |
| `number` | integer | Issue number within repository | GitHub API |
| `title` | string | Issue title | GitHub API |
| `state` | string | Issue state (open/closed) | GitHub API |
| `created_at` | timestamp | Issue creation timestamp | GitHub API |
| `updated_at` | timestamp | Last update timestamp | GitHub API |
| `closed_at` | timestamp | Issue closure timestamp (nullable) | GitHub API |
| `author` | string | Issue author username | GitHub API |
| `labels` | array[string] | List of issue labels | GitHub API |
| `assignees` | array[string] | List of assignee usernames | GitHub API |
| `is_pull_request` | boolean | Whether the issue is a PR | Derived from `pull_request` field |
| `body_length` | integer | Length of issue body text | GitHub API |
| `comment_count` | integer | Number of comments on the issue | GitHub API |
| `resolution_time_hours` | float | Time from creation to closure in hours | Computed |
| `time_to_first_response_hours` | float | Time from creation to first comment | Computed |
| `days_to_close` | integer | Number of days until closure | Computed |
| `has_labels` | boolean | Whether issue has any labels | Computed |
| `has_assignee` | boolean | Whether issue has at least one assignee | Computed |

### IssueEvent
Represents individual events in an issue's lifecycle (optional, for detailed analysis).

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `event_id` | integer | Unique event identifier | GitHub API |
| `issue_id` | integer | Foreign key to Issue | Derived |
| `event_type` | string | Type of event (e.g., "labeled", "closed", "reopened") | GitHub API |
| `created_at` | timestamp | Event timestamp | GitHub API |
| `actor` | string | Username who triggered the event | GitHub API |
| `label_name` | string | Label name (if event type is labeled/unlabeled) | GitHub API |
| `commit_id` | string | Commit SHA (if event type is cross-referenced) | GitHub API |

## Derived Metrics

### Resolution Time
- **Definition**: `resolution_time_hours` = (closed_at - created_at) in hours
- **Constraints**:
 - Must be non-negative
 - Must be finite (no NaN/Inf)
 - Issues with `closed_at` < `created_at` are excluded
 - Issues without `closed_at` (still open) are excluded from resolution analysis

### Time to First Response
- **Definition**: `time_to_first_response_hours` = (first_comment_at - created_at) in hours
- **Constraints**:
 - Only computed for issues with at least one comment
 - Excludes self-comments by the author if tracked

## Data Quality Constraints

### Required Fields (Non-Null)
- `issue_id`, `repository_id`, `number`, `created_at`, `state`
- For closed issues: `closed_at` must be present

### Validity Rules
1. **Timestamp Consistency**: `created_at` ≤ `updated_at` ≤ `closed_at` (if closed)
2. **Resolution Time**: `resolution_time_hours` ≥ 0
3. **Repository Language**: Must be a non-empty string or null (not empty string)
4. **Issue State**: Must be one of "open" or "closed"

### Exclusion Criteria
Issues are excluded from the final analysis dataset if:
- `closed_at` is missing (issue not yet closed)
- `closed_at` < `created_at` (invalid timestamp)
- `resolution_time_hours` < 0 (negative duration)
- `resolution_time_hours` is NaN or Inf
- `created_at` is missing or invalid

## Relationships

```
Repository (1) ───< Issue (N)
Issue (1) ───< IssueEvent (N)
Issue (N) ───< Label (N) [Many-to-Many via labels array]
Issue (N) ───< Assignee (N) [Many-to-Many via assignees array]
```

## File Outputs

### Raw Data
- `data/raw/issues_raw.json`: Raw JSON from GitHub API per repository
- `data/raw/repositories.json`: Repository metadata

### Processed Data
- `data/processed/cleaned_issues.csv`: Final analysis-ready dataset
 - Columns: All Issue attributes + derived metrics
 - Format: CSV with UTF-8 encoding
 - Index: None (or issue_id as column)

### Aggregated Data
- `data/processed/distribution_metrics.json`: Distribution fit results
- `data/processed/hypothesis_results.json`: Statistical test results

## Schema Versioning

- **Version**: 1.0.0
- **Date**: 2024
- **Last Updated**: Based on plan.md Phase 1 outputs

## References

- GitHub REST API v3 Documentation
- Plan.md: Statistical Analysis of GitHub Issue Resolution Times
- Spec.md: User Stories and Acceptance Criteria
