# Data Model: GitHub Issue Resolution Analysis

## Entity-Relationship Overview

The data model represents a hierarchical structure: **Repositories** contain **Issues**. Each issue has temporal attributes and categorical metadata.

### Key Entities

1.  **Repository**
    *   `repo_id` (str): Unique identifier (e.g., "owner/repo").
    *   `language` (str): Primary programming language.
    *   `star_count` (int): Popularity metric.
    *   `contributor_count` (int): Number of unique contributors.
    *   `created_at` (datetime): Repository creation time.

2.  **Issue**
    *   `issue_id` (str): Unique issue ID.
    *   `repo_id` (str): Foreign key to Repository.
    *   `created_at` (datetime): Issue creation timestamp (ISO 8601).
    *   `closed_at` (datetime): Issue closure timestamp (ISO 8601).
    *   `resolution_time_hours` (float): Derived: `(closed_at - created_at) / 3600`.
    *   `labels` (str): Comma-separated list of labels.
    *   `assignee` (str): Username or "unassigned".
    *   `comments_count` (int): Number of comments.
    *   `is_outlier` (bool): True if `resolution_time_hours > 30 * 24`.
    *   `is_valid` (bool): True if `closed_at >= created_at`.

3.  **AnalysisResult**
    *   `test_type` (str): e.g., "Kruskal-Wallis", "LMM".
    *   `predictor` (str): Variable tested.
    *   `p_value` (float): Raw p-value.
    *   `adjusted_p_value` (float): Holm-Bonferroni adjusted.
    *   `effect_size` (float): e.g., eta-squared.
    *   `ci_lower` (float): 95% CI lower bound.
    *   `ci_upper` (float): 95% CI upper bound.

## Data Flow

1.  **Raw Input**: Parquet from HuggingFace (`akhousker/github-issues`).
2.  **Cleaned**: `data/processed/cleaned_issues.csv`.
    *   Filtered: `state == "closed"`, `closed_at >= created_at`.
    *   Derived: `resolution_time_hours`, `is_outlier`.
3.  **Analysis Output**: `data/interim/` (JSON/CSV) for metrics, figures.

## Storage Constraints

- **Format**: CSV for processed data (human-readable, streamable).
- **Size Limit**: Target < 500MB for processed CSV to ensure fast I/O on CI.
- **Checksum**: SHA-256 of `cleaned_issues.csv` recorded in `state/`.
