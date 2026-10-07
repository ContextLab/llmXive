# Data Model: The Impact of Parasocial Relationships with AI Companions on Loneliness

## Entity Relationship Overview

The data model consists of three primary stages: **Raw Ingestion**, **Matched Users**, and **Longitudinal Records**.

1.  **UserProfile**: A unique entity representing a matched user. Contains static demographics and emotional coping scores.
2.  **LongitudinalRecord**: A time-series entity linked to a `UserProfile`. Contains repeated measures of loneliness and usage metrics.
3.  **WeeklyAggregates**: A derived entity representing weekly aggregates of the longitudinal data.
4.  **ModelResult**: A derived entity storing the statistical output.

## Schema Definitions

### UserProfile
*Represents a matched individual.*
- `user_id` (string): SHA-256 hash of the Reddit username.
- `age` (integer): Self-reported age.
- `gender` (string): Self-reported gender.
- `emotional_coping_anxiety_score` (float): Normalized frequency of anxiety terms.
- `emotional_coping_avoidance_score` (float): Normalized frequency of avoidance terms.
- `match_status` (string): "matched" or "excluded".

### LongitudinalRecord
*Represents a single time-point observation.*
- `record_id` (string): Unique ID for the observation.
- `user_id` (string): Foreign key to `UserProfile`.
- `timestamp` (datetime): Date of the survey/observation.
- `loneliness_score` (float): UCLA Loneliness Scale score.
- `usage_frequency` (float): Count of AI interactions in the preceding week.
- `session_duration` (float): Total duration of AI interactions in the preceding week (minutes).
- `lag_usage_frequency` (float): Usage frequency at $T-1$.

### WeeklyAggregates
*Represents weekly aggregates of the longitudinal data.*
- `week_start` (date): ISO-8601 date representing the start of the week (Monday).
- `avg_loneliness_score` (float): Average UCLA Loneliness Scale score for the given week.
- `total_ai_activity` (integer): Total number of AI-companion interactions during the week.
- `avg_emotional_coping_anxiety` (float): Average anxiety subscale (0 = no anxiety terms, 1 = max observed frequency) based on ECR-S keywords. Null if no text available.
- `avg_emotional_coping_avoidance` (float): Average avoidance subscale based on ECR-S keywords. Null if no text available.
- `n_respondents` (integer): Number of survey respondents in the week.
- `lagged_activity` (integer): Total AI activity from the previous week (T-1). Null for the first week (T0).
- `missing_attachment_flag` (boolean): True if emotional coping scores were imputed as neutral (0.0) due to missing text data.

### ModelResult
*Represents the output of the statistical analysis.*
- `model_id` (string): Unique ID for the run.
- `fixed_effects` (dict): Map of coefficient names to estimates.
- `p_values` (dict): Map of p-values for fixed effects.
- `confidence_intervals` (dict): Map of 95% confidence intervals [lower, upper] for fixed effects.
- `marginal_r2` (float): Variance explained by fixed effects.

## Data Flow

1.  **Ingestion**: 
    - `data/raw/zenodo_loneliness.csv` (Raw survey data).
    - `data/raw/pushshift_logs.jsonl` (Raw interaction logs).
2.  **Matching**: 
    - `data/processed/matched_users.parquet` (UserProfile + LongitudinalRecords merged).
3.  **Aggregation**: 
    - `data/processed/weekly_aggregates.parquet` (WeeklyAggregates).
4.  **Analysis**: 
    - `data/results/model_summary.json` (ModelResult).

## Constraints & Validation

- **Uniqueness**: `user_id` must be unique in `UserProfile`.
- **Completeness**: `loneliness_score`, `usage_frequency`, `session_duration` must be non-null in `LongitudinalRecord`.
- **Range**: `loneliness_score` must be within the valid range of the UCLA scale (e.g., 20-80).
- **Temporal Integrity**: `timestamp` in `LongitudinalRecord` must be strictly ordered. Lagged variables must reference valid prior timestamps.