# Data Dictionary: daily_aggregates.csv

This document describes the schema and semantics of the `data/processed/daily_aggregates.csv` file, which serves as the primary input for statistical modeling in the Physical Activity Levels and Mood Variability project.

## File Location
`data/processed/daily_aggregates.csv`

## Overview
This file contains one row per participant per day, aggregating raw step logs and EMA mood ratings into daily metrics. It is produced by `code/preprocess.py` (Task T015).

## Columns

| Column Name | Type | Required | Description |
|:--- |:--- |:--- |:--- |
| `participant_id` | string | Yes | Unique identifier for the participant. |
| `date` | date | Yes | The date of the observation (YYYY-MM-DD). |
| `total_steps` | integer | Yes | Total number of steps recorded for the day. Minimum value is 0. |
| `mean_mood` | float | Yes | Arithmetic mean of all valid mood ratings recorded on this day. |
| `mood_std` | float | Yes | **Raw** standard deviation of mood ratings for the day. No log transformation is applied here. Value is 0.0 if all ratings are identical. |
| `n_mood_ratings` | integer | Yes | Count of valid mood ratings included in the calculation. Minimum value is 2 (days with <2 ratings are excluded). |
| `sleep_duration` | float | No | Duration of sleep in hours. Nullable if not recorded or derived. |
| `baseline_affect` | float | No | Baseline affect score for the participant. Nullable if not recorded. |
| `day_of_week` | integer | Yes | Day of the week (0=Monday, 6=Sunday). |

## Data Quality & Constraints

- **Exclusion Criteria**: Days with fewer than 2 valid mood ratings are excluded entirely to satisfy FR-002.
- **Zero Steps**: Days with zero steps are retained and recorded as `total_steps = 0`.
- **Missingness**: Columns `sleep_duration` and `baseline_affect` are nullable. Their presence depends on the derivation logic in `code/preprocess.py` and the `MISSINGNESS_THRESHOLD` constant.
- **Normalization**: `mood_std` is the raw standard deviation. The log transformation (`log(mood_std + epsilon)`) is applied later in `code/analysis.py` for modeling purposes only.

## Schema Contract
This file must conform to `specs/001-physical-activity-levels-and-mood-variab/contracts/daily_aggregates.schema.yaml`.
Validation is performed by `code/output_validator.py` and `tests/contract/test_daily_aggregates.py`.
