# Data Model: Evaluating the Impact of Code Generation on Code Review Quality

## Overview

This document defines the data structures used throughout the pipeline. The model supports the transition from raw GitHub data to the final analysis-ready dataset.

## Entities

### 1. PullRequest (Raw)
Represents a single record from the source dataset.
- `pr_id`: String (Unique Identifier)
- `repo_name`: String
- `author`: String
- `commit_message`: String (Source for classification)
- `diff_text`: String (Source for complexity analysis)
- `created_at`: Timestamp
- `merged_at`: Timestamp (Nullable - indicates censoring)
- `review_comments`: List[Object] (or aggregated string)
  - `body`: String
  - `created_at`: Timestamp
- `language`: String (e.g., "Python", "JavaScript")
- `repo_size`: Integer (Number of files/commits - for confounder control)

### 2. PR_Metrics (Derived)
Computed attributes for each PR.
- `pr_id`: String (FK)
- `label`: Enum["LLM-generated", "Human-written"]
- `comment_count`: Integer
- `sentiment_score`: Float (Range -1.0 to 1.0)
- `merge_latency_hours`: Float (Nullable)
- `is_censored`: Boolean (True if `merged_at` is null)
- `loc`: Integer (Lines of Code)
- `cyclomatic_complexity`: Float
- `bug_density`: Float (Warnings per 100 LOC)
- `is_valid`: Boolean (True if all required metrics computed)
- `propensity_score`: Float (Probability of being LLM, from PSM)
- `match_status`: Enum["Matched", "Discarded"] (Result of PSM/Exact Matching)

### 3. AuditSample (Validation)
Stores the ground truth for the manual audit.
- `pr_id`: String
- `label_heuristic`: Enum["LLM-generated", "Human-written"]
- `label_ground_truth`: Enum["LLM-generated", "Human-written"] (Manual label)
- `is_correct`: Boolean

### 4. Analysis_Group (Aggregated)
Aggregated statistics for the final report.
- `group`: Enum["LLM-generated", "Human-written"]
- `n`: Integer
- `median_comment_count`: Float
- `median_sentiment`: Float
- `median_merge_latency`: Float (or median survival time)
- `p_value_raw`: Float
- `p_value_adjusted`: Float
- `effect_size_raw`: Float
- `effect_size_simex`: Float (Corrected for measurement error)
- `confounder_flag`: Boolean (True if sentiment correlated with bug density > 0.5)

## Data Flow

1.  **Ingestion**: `prs-v2-sample` parquet → `PR_Metrics` (Raw).
2.  **Labeling**: `commit_message` → Heuristic → `PR_Metrics.label`.
3.  **Enrichment**: `diff_text` → `radon`/`lizard` → `PR_Metrics` (Complexity/Bug Density).
4.  **Sentiment**: `review_comments` → `textblob` → `PR_Metrics.sentiment_score`.
5.  **Filtering**: Remove records where `is_valid` is False (missing timestamps, null diffs).
6.  **Validation**: Manual audit sample → `AuditSample` → Calculate misclassification matrix.
7.  **PSM**: Calculate `propensity_score`, perform matching → `match_status`.
8.  **Confounding Check**: Compute correlation(sentiment, bug_density) → `confounder_flag`.
9.  **Analysis**: Filtered `PR_Metrics` (Matched) → Grouped `Analysis_Group` → Statistical Tests (Cox PH / Mann-Whitney) → SIMEX Correction.

## Constraints

- **Completeness**: ≥95% of records must have valid `diff_text`, `review_comments`, and `created_at` (FR-011).
- **Classification**: `label` must be derived solely from `commit_message` keywords (FR-002).
- **Mediator Control**: Do **not** use `cyclomatic_complexity` or `loc` as covariates in PSM (they are mediators).
- **Sentiment**: If `abs(correlation(sentiment, bug_density)) > 0.5`, `confounder_flag` is set to True, and the result is reported with a caveat (FR-016).
- **Censoring**: `is_censored` must be True for PRs with no `merged_at`.