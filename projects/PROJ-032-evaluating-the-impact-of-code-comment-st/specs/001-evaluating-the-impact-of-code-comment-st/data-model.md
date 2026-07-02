# Data Model: Evaluating the Impact of Code Comment Style on Maintainability

## 1. Overview
This document defines the data structures for the research pipeline. All data is stored in `data/` with checksums.

## 2. Entities

### Repository
*   `repo_id` (str): Unique identifier (e.g., "owner/repo").
*   `stars` (int): Star count at time of selection.
*   `language` (str): "Python".
*   `clone_path` (str): Local path to the clone.
*   `clone_status` (str): "success", "failed", "excluded".

### Comment
*   `comment_id` (str): Unique hash of the comment text + location.
*   `repo_id` (str): Foreign key.
*   `file_path` (str): Relative path in repo.
*   `start_line` (int): Start line number.
*   `end_line` (int): End line number.
*   `text` (str): Raw comment text.

### Metrics (Aggregated per Repository)
*   `repo_id` (str): Primary Key.
*   `comment_density` (float): Lines of comment / Lines of code.
*   `avg_readability` (float): Mean Flesch-Kincaid score.
*   `readability_std_dev` (float): Standard deviation of Flesch-Kincaid scores (style consistency).
*   `avg_sentiment` (float): Mean polarity (-1 to 1).
*   `sentiment_variance` (float): Variance of sentiment polarity (style consistency).
*   `total_churn` (int): Total lines changed (all commits).
*   `code_quality_degradation_rate` (float): Ratio of sampled commits with pylint error-level warnings.
*   `issue_bug_rate` (float): Ratio of commits fixing issues labeled 'bug' (if available, else null).
*   `total_lines_of_code` (int): Total lines of code (LOC).
*   `project_age_years` (float): Years since first commit.
*   `contributor_count` (int): Unique committers.
*   `avg_complexity` (float): Mean cyclomatic complexity.

## 3. Data Flow

1.  **Raw**: `data/raw/<repo_id>/` (Git clones).
2.  **Intermediate**: `data/intermediate/comments.jsonl` (Extracted comments).
3.  **Processed**: `data/processed/metrics.csv` (Final analysis dataset).
4.  **Validation**: `data/processed/validation_report.json` (Accuracy of automated metrics vs manual labels).
5.  **Results**: `data/processed/results.json` (Regression coefficients, p-values, sensitivity sweep).

## 4. Constraints

*   **PII**: No personal emails/names in `data/processed`.
*   **Checksums**: All files in `data/` must have corresponding entries in `state/...yaml`.
*   **Immutability**: Raw data never modified.
