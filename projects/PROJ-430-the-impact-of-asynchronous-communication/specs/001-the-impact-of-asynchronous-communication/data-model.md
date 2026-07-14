# Data Model: The Impact of Asynchronous Communication Delays on Team Cohesion

## Overview

This document defines the data structures used throughout the pipeline, from raw ingestion to final statistical output. All data is stored in CSV or Parquet formats within the `data/` directory.

## Entities & Attributes

### 1. Project (Core Entity)
Represents an open-source repository.
- `project_id`: Unique identifier (e.g., GitHub repo ID).
- `name`: Repository name (e.g., `owner/repo`).
- `star_count`: Number of stars (used for sorting).
- `created_at`: Repository creation timestamp (for `project_age`).
- `team_size`: Count of unique contributors (active).
- `primary_language`: Detected primary programming language.

### 2. Event (Raw Interaction)
Represents a discrete interaction (issue, PR, comment).
- `event_id`: Unique event ID.
- `project_id`: Link to Project.
- `author_id`: Unique author identifier.
- `author_name`: Display name.
- `is_bot`: Boolean flag (True if `[bot]` in name or known App ID).
- `event_type`: "issue", "pull_request", "comment".
- `created_at`: Timestamp of event.
- `text_content`: The raw text of the comment/issue body.
- `language_code`: Detected language code (e.g., `en`, `es`).
- `language_confidence`: Confidence score from `langdetect`.

### 3. ContributorPair (Derived Relationship)
Represents a directed relationship between two authors.
- `pair_id`: Unique ID (e.g., `A_B`).
- `project_id`: Link to Project.
- `author_a_id`: Initiator.
- `author_b_id`: Responder.
- `interaction_count`: Number of exchanges.
- `mean_delay`: Average time (hours) between A's event and B's response.
- `response_time_variance`: Variance of delays for this pair.
- `is_mutual`: Boolean (True if B also responded to A).

### 4. ProjectMetrics (Aggregated)
Project-level summary for analysis.
- `project_id`: Link to Project.
- `response_time_variance`: **Interaction-weighted mean** of all pair variances (FR-010, updated for stability).
- `mean_delay`: Interaction-weighted mean of all pair means.
- `cohesion_proxy_score`: Composite score (0.4 * sentiment_stability + 0.3 * reciprocity + 0.3 * density).
- `sentiment_stability`: Standard deviation of VADER compound scores.
- `reciprocity_ratio`: Ratio of mutual responses to total responses.
- `network_density`: Density of the interaction graph.
- `team_size`: Count of unique contributors.
- `project_age_days`: Age in days.
- `exclusion_reason`: "insufficient_data", "no_text_data", "non_english", or null.

### 5. ValidationSample (Manual Coding)
Subset of comments for manual validation.
- `sample_id`: Unique ID.
- `project_id`: Link to Project.
- `comment_id`: Link to Event.
- `manual_cohesion_score`: Integer score (1-5) from manual coding of **relational indicators** (e.g., 'we', 'together', 'collaborative tone').
- `vader_score`: VADER compound score.

### 6. StatisticalResult (Output)
Final analysis results.
- `test_type`: "spearman", "regression", "stratified".
- `coefficient`: Value (r or beta).
- `p_value`: Significance level.
- `confidence_interval_low`: Lower bound.
- `confidence_interval_high`: Upper bound.
- `vif_values`: Dict of VIF scores for control variables.
- `fdr_corrected`: Boolean (if BH correction applied).
- `interaction_effect`: Boolean (if interaction term was included).

## Data Flow

1.  **Raw Ingestion**: `GitHub API` → `data/raw/events.csv` (JSON/CSV).
2.  **Cleaning**: `events.csv` → `data/derived/clean_events.csv` (filters bots, non-English).
3.  **Metrics**: `clean_events.csv` → `data/derived/pair_metrics.csv` → `data/derived/project_metrics.csv` (includes structural metrics).
4.  **Analysis**: `project_metrics.csv` → `data/derived/statistical_results.csv` + `figures/`.
5.  **Validation**: `clean_events.csv` (sampled) → `data/validation/manual_coding.csv` → `data/derived/validation_results.csv`.

## Constraints

- **PII**: No user emails or real names stored; only `author_id` and `author_name` (public).
- **Immutability**: `data/raw/` is read-only. Derivations create new files.
- **Checksums**: All files in `data/` are checksummed (SHA-256) and recorded in `state/` via `code/utils/hygiene.py`.