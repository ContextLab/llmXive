# Data Model for Statistical Analysis of GitHub Issue Resolution Times

## Overview

This document defines the entity relationships, attributes, and data flow for the GitHub issue resolution analysis pipeline.

## Entities

### Repository

Represents a GitHub repository being analyzed.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| repository_id | string | Unique identifier | Primary key |
| full_name | string | Full name (owner/repo) | Unique, not null |
| owner | string | Repository owner | Not null |
| name | string | Repository name | Not null |
| primary_language | string | Primary programming language | Not null |
| created_at | timestamp | Repository creation time | Not null |
| updated_at | timestamp | Last update time | Not null |
| stargazers_count | integer | Number of stars | >= 0 |
| forks_count | integer | Number of forks | >= 0 |
| open_issues_count | integer | Number of open issues | >= 0 |
| is_archived | boolean | Whether repository is archived | Not null |

### Issue

Represents a GitHub issue within a repository.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| issue_id | string | Unique identifier | Primary key |
| repository_id | string | Foreign key to Repository | Not null |
| number | integer | Issue number within repo | Not null |
| title | string | Issue title | Not null |
| body | text | Issue body content | Optional |
| state | string | Issue state (open/closed) | Enum: open, closed |
| created_at | timestamp | Issue creation time | Not null |
| updated_at | timestamp | Last update time | Not null |
| closed_at | timestamp | Issue closure time | Required if state=closed |
| author | string | Author username | Not null |
| assignee | string | Assignee username | Optional |
| labels | array | List of labels | Default: [] |
| comments_count | integer | Number of comments | >= 0 |
| resolution_time_hours | float | Time to resolve in hours | >= 0, computed |
| is_valid | boolean | Whether issue passed validation | Not null |

### IssueLabel

Represents a label applied to an issue.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| issue_id | string | Foreign key to Issue | Not null |
| label_name | string | Label name | Not null |
| label_color | string | Label color code | Optional |

### AnalysisResult

Represents the results of statistical analysis.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| result_id | string | Unique identifier | Primary key |
| analysis_type | string | Type of analysis | Not null |
| artifact_path | string | Path to result file | Not null |
| checksum | string | SHA-256 checksum | Not null |
| created_at | timestamp | Creation time | Not null |
| status | string | Status of result | Enum: pending, completed, failed |
| metadata | json | Additional metadata | Optional |

## Relationships

- Repository 1:N Issue (A repository has many issues)
- Issue 1:N IssueLabel (An issue has many labels)
- AnalysisResult 1:1 Artifact (Each result corresponds to one artifact)

## Data Flow

1. **Collection**: Fetch issues from GitHub API → Raw Issues
2. **Preprocessing**: Validate, filter, compute resolution times → Cleaned Issues
3. **Analysis**: Statistical tests, distribution fitting → Analysis Results
4. **Validation**: Schema validation, checkpoint verification → Validated Artifacts

## Constraints

- **FR-001**: Minimum 100 repositories must be collected
- **FR-002**: Resolution time must be non-negative
- **FR-003**: Invalid issues (missing timestamps, negative resolution time) must be excluded
- **SC-001**: Dataset completeness must be >= 95%
- **SC-002**: All analysis artifacts must have checksums
- **Constitution Principle II**: Checkpoint verification at artifact write
