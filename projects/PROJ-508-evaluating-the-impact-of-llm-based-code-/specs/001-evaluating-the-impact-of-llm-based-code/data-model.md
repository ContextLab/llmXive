# Data Model: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

## Overview
This document defines the data structures used for ingestion, storage, and analysis. All data flows from the GitHub API into raw JSON, is transformed into CSV/Parquet, and then consumed by the analysis engine.

## Entity Definitions

### 1. Repository (Unit of Analysis)
Aggregated data per repository.
-   `repo_id` (string): Unique identifier (e.g., `owner/repo`).
-   `llm_adoption_flag` (integer): Binary (0 or 1).
-   `lines_of_code` (integer): Total LOC.
-   `contributor_count` (integer): Number of unique contributors.
-   `domain_complexity` (integer): Sum of unique languages + dependency count.
-   `pr_count_12m` (integer): Number of PRs in last 12 months.
-   `project_scale_pca` (float, optional): PCA-derived factor replacing LOC and domain_complexity if VIF > 5.0.

### 2. PullRequest (Observation Unit)
Individual PR metrics.
-   `pr_id` (string): Unique PR identifier.
-   `repo_id` (string): Foreign key to Repository.
-   `avg_comment_length` (float): Mean character length of review comments.
-   `iteration_count` (integer): Number of human review iterations (excluding auto-commits). **Note**: This is the total push count, no exclusions.
-   `review_thread_depth` (integer): Max nesting depth of review threads.
-   `reverted` (boolean): Whether the PR was reverted.

### 3. AnalysisResult (Output)
Results of the regression models.
-   `dependent_variable` (string): Name of the proxy (e.g., `avg_comment_length`).
-   `coefficient` (float): $\beta_1$ for `llm_adoption_flag`.
-   `standard_error` (float): SE of the coefficient.
-   `p_value` (float): Raw p-value.
-   `adjusted_p_value` (float): Bonferroni-corrected p-value.
-   `ci_lower` (float): 95% CI lower bound.
-   `ci_upper` (float): 95% CI upper bound.

## Data Flow

1.  **Raw Ingestion**:
    -   Source: GitHub API.
    -   Format: JSON files in `data/raw/`.
    -   Content: Full API responses for repos, PRs, commits, comments.
2.  **Derived Processing**:
    -   Script: `code/ingest.py`.
    -   Output: `data/derived/master_dataset.csv`.
    -   Logic: Aggregates PR metrics per repo, calculates control variables, applies LLM flagging logic.
3.  **Analysis Output**:
    -   Script: `code/analyze.py`.
    -   Output: `data/derived/regression_results.csv`, `data/derived/sensitivity_results.csv`.
4.  **Reporting**:
    -   Script: `code/report.py`.
    -   Output: Figures (PNG/SVG) and text report (PDF/HTML).

## Assumptions & Constraints
-   **Missing Data**: Repositories with <10 PRs in 12 months are excluded (SC-001).
-   **Rate Limits**: API calls are throttled; data ingestion may be partial if limits are hit (retry logic implemented).
-   **PII**: No personal names or emails are stored; only public metadata.
-   **Collinearity**: If VIF > 5.0 between LOC and domain_complexity, both are replaced by `project_scale_pca`.