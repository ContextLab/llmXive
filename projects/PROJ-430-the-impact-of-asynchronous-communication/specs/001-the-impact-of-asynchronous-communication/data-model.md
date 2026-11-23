# Data Model: Asynchronous Communication Delays and Team Cohesion

## Overview
This document defines the data entities, their attributes, and the transformation logic used to move from raw GitHub events to final statistical results. The model enforces strict separation between temporal metadata and textual content to satisfy Constitution Principle VI.

## Entities

### 1. RawEvent
Represents a single interaction on GitHub.
- **Source**: GitHub API (Issues, Pull Requests, Comments).
- **Attributes**:
  - `event_id` (str): Unique identifier.
  - `repository_id` (int): GitHub repo ID.
  - `author_id` (int): GitHub user ID.
  - `timestamp` (datetime): ISO 8601 timestamp of creation.
  - `text_content` (str): Body of the comment/issue/PR. *Nullable for PRs without body.*
  - `event_type` (str): "issue", "pr", "comment".
  - `is_bot` (bool): True if author name ends in "[bot]" or is in GitHub Apps registry.
  - `in_reply_to_id` (str, optional): ID of the message being replied to (for thread context).

### 2. ContributorPair
Represents a relationship between two distinct authors.
- **Attributes**:
  - `pair_id` (str): Hash of sorted (author_a, author_b) IDs.
  - `author_a_id` (int), `author_b_id` (int).
  - `project_id` (int): Parent project ID.
  - `interactions` (list): List of `RawEvent` timestamps where A and B exchanged messages.
  - `response_times` (list[float]): Time in seconds from message M1 (Author A) to the first subsequent message M2 (Author B) in the same thread or issue context.
  - `sentiment_scores` (list[float]): VADER compound scores for comments in this pair.

### 3. PairMetrics
Aggregated pair-level metrics (Primary Unit of Analysis).
- **Attributes**:
  - `pair_id` (str).
  - `project_id` (int).
  - `response_time_variance` (float): Variance of response times for this pair.
  - `mean_delay` (float): Mean of response times for this pair.
  - `cohesion_proxy_score` (float): Mean of VADER compound scores for this pair.
  - `interaction_count` (int): Number of exchanges between the pair.

### 4. ProjectMetrics
Aggregated project-level metrics (Secondary Unit of Analysis).
- **Attributes**:
  - `project_id` (int).
  - `response_time_variance` (float): Median of all pair-level variances.
  - `mean_delay` (float): Mean of all pair-level mean delays.
  - `cohesion_proxy_score` (float): Aggregated VADER compound score.
  - `team_size` (int): Unique author count.
  - `project_age` (float): Days since first event.
  - `total_comment_count` (int): Total number of text-based events (for volume control).
  - `lang_primary` (str): Primary programming language.

### 5. StatisticalResult
Output of the analysis.
- **Attributes**:
  - `test_type` (str): "hlm", "ols", "spearman".
  - `coefficient` (float): Correlation coefficient or regression beta.
  - `p_value` (float): Significance of test.
  - `confidence_interval_low` (float).
  - `confidence_interval_high` (float).
  - `vif_values` (dict): VIF for each control variable (if applicable).
  - `corrected_p_values` (dict): BH-corrected p-values for stratified tests.
  - `status` (str): "success", "halted_vif", "insufficient_data".

### 6. ValidationReport
Output of the manual validation step.
- **Attributes**:
  - `vader_manual_rho` (float): Correlation between VADER and manual scores.
  - `manual_sample_size` (int): Number of manually coded comments.
  - `pass_threshold` (float): 0.5.
  - `result` (str): "pass", "fail", "skipped", "synthetic".
  - `is_synthetic` (bool): True if manual data was missing and synthetic data was used.

## Transformation Logic

### Phase 1: Ingestion & Temporal Metrics (Pair-Level)
1. **Fetch**: Retrieve events from GitHub API. Filter out `is_bot` events.
2. **Parse**: Extract timestamps and text. *Skip PRs without `body` for sentiment, but keep for timestamps.*
3. **Pairing**: Group events by `repository_id` and identify `ContributorPair` interactions. Use `in_reply_to_id` where available to define thread context.
4. **Calculation**: For each pair, calculate `response_times` (time from M1 to first M2 in thread). Compute `variance` and `mean` for the pair.
5. **Output**: Write `data/derived/pair_metrics.parquet` (Pair-Level) and `data/derived/timestamp_features.parquet` (Project-Level Summary).

### Phase 2: Sentiment Analysis (Pair-Level)
1. **Filter**: Select `text_content` where `langdetect` confidence ≥ 0.95 and language is English. Log exclusion rate to `data/derived/language_exclusion_log.json`.
2. **Score**: Apply VADER `get_scores` to each comment.
3. **Aggregate**: Compute mean compound score per pair.
4. **Output**: Write `data/derived/pair_sentiment.parquet`.

### Phase 3: Statistical Analysis
1. **Join**: Merge `PairMetrics` and `PairSentiment`.
2. **Primary**: Fit HLM with `project_id` as random effect.
3. **Secondary**: Aggregate to project-level (median) and run OLS.
4. **VIF Check**: Compute VIF. If VIF > 5, write `data/logs/vif_halt_warning.log` and halt.
5. **Stratification**: Repeat for language/size tiers. Apply Benjamini-Hochberg.
6. **Output**: Write `data/derived/statistical_results.json` and `data/derived/fdr_corrected_results.json`.

### Phase 4: Validation & Robustness
1. **Check**: If `data/validation/manual_ground_truth.csv` exists, run validation.
2. **Validate**: Compute Spearman correlation between VADER and manual scores.
3. **Synthetic Fallback**: If missing, generate synthetic manual scores and run validation, flagging as "synthetic".
4. **Robustness**: Compare HLM and OLS results.
5. **Output**: Write `data/validation/validity_report.json` and `data/derived/robustness_hlm_results.json`.

## Data Hygiene
- **Immutability**: Raw data is stored in `data/raw/` and never modified.
- **Checksums**: All files in `data/` are checksummed (SHA-256).
- **PII**: User IDs are used as opaque integers; no usernames or emails are stored.
