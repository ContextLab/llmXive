# Data Dictionary: `data/processed/daily_aggregates.csv`

This file contains daily aggregated metrics derived from the StudentLife dataset,
aligning physical activity (steps) with mood variability and covariates.

## Schema Overview

| Column Name | Type | Description | Constraints |
|-------------|------|-------------|-------------|
| `participant_id` | string | Unique identifier for the participant | Required |
| `date` | date | The date of the observation (YYYY-MM-DD) | Required |
| `total_steps` | integer | Total number of steps recorded for the day | min=0 |
| `mean_mood` | float | Average mood rating for the day | Required |
| `mood_std` | float | Standard deviation of mood ratings for the day | min=0 (raw, untransformed) |
| `n_mood_ratings` | integer | Count of valid mood ratings collected that day | min=2 |
| `sleep_duration` | float | Average sleep duration in hours | Nullable |
| `baseline_affect` | float | Baseline affect score for the participant | Nullable |
| `day_of_week` | integer | Day of week (0=Monday, 6=Sunday) | Required |

## Field Details

### `participant_id`
- **Source**: Raw data participant identifier.
- **Format**: String (e.g., "P001").
- **Notes**: Used for grouping in mixed-effects models.

### `date`
- **Source**: Derived from timestamp in raw logs.
- **Format**: ISO 8601 date string.
- **Notes**: Days with fewer than 2 mood ratings are excluded.

### `total_steps`
- **Source**: Aggregated from step log entries.
- **Calculation**: Sum of `step_count` for the day.
- **Notes**: Days with 0 steps are recorded as 0, not dropped.

### `mean_mood`
- **Source**: EMA mood ratings.
- **Calculation**: Arithmetic mean of valid mood ratings.
- **Notes**: Only valid ratings (non-null) are included.

### `mood_std`
- **Source**: EMA mood ratings.
- **Calculation**: Population standard deviation of valid mood ratings.
- **Notes**:
 - **Raw value**: No log transformation is applied here.
 - **Zero handling**: If all ratings are identical, `mood_std` is `0.0`.
 - **Transformation**: Log-transformation (`np.log(mood_std + epsilon)`) is applied
 only in `code/analysis.py` during model fitting.

### `n_mood_ratings`
- **Source**: Count of EMA entries.
- **Notes**: Rows with `n_mood_ratings < 2` are excluded from this dataset entirely.

### `sleep_duration`
- **Source**: Derived from raw sensor data or user reports.
- **Notes**: Nullable if data is missing and cannot be derived.

### `baseline_affect`
- **Source**: Baseline survey data.
- **Notes**: Nullable if not available for the participant.

### `day_of_week`
- **Source**: Derived from `date`.
- **Encoding**: 0 = Monday,..., 6 = Sunday.
- **Usage**: Used as a covariate in models to control for weekly patterns.

## Data Integrity Notes

- **Missingness**: Rows with missing `total_steps`, `mean_mood`, or `mood_std` are
 not present in this file.
- **Exclusion**: Days with fewer than 2 mood ratings are excluded during
 preprocessing (see `code/preprocess.py`).
- **Validation**: The file is validated against `daily_aggregates.schema.yaml`
 before being used in analysis.
