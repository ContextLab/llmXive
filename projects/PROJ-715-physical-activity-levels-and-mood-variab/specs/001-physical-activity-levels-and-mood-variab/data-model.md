# Data Model: Physical Activity Levels and Mood Variability in Daily Life

## Overview

This document defines the data structures used throughout the pipeline. All data is derived from the raw `StudentLife` dataset and transformed into a normalized `ParticipantDay` level for analysis.

## Entity: ParticipantDay

The core analytical unit. Represents one participant on one calendar day.

| Field | Type | Description | Source/Transformation |
| :--- | :--- | :--- | :--- |
| `participant_id` | string | Unique anonymized ID. | Raw dataset |
| `date` | date | Calendar date (YYYY-MM-DD). | Raw timestamp |
| `total_steps` | integer | Sum of step counts for the day. | `sum(step_count)` |
| `mean_mood` | float | Average mood rating for the day. | `mean(mood)` (min 2 ratings) |
| `mood_std` | float | Standard deviation of mood for the day. | `std(mood)` (min 2 ratings) |
| `log_mood_var` | float | `log(mood_std + 0.01)`. | Derived |
| `sleep_duration` | float | Average sleep duration (hours) for the day. | **Derived** from accelerometer inactivity (if not in raw) or `mean(sleep_duration)` |
| `day_of_week` | string | Day name (e.g., "Monday"). | Derived from `date` |
| `baseline_affect` | float | Baseline affect score (participant-level). | **Derived** from baseline survey aggregate (if not in raw) |
| `n_mood_ratings` | integer | Count of valid mood ratings for the day. | `count(mood)` |

## Data Flow

1.  **Raw Input**: `bronze.parquet` (StudentLife).
2.  **Preprocessing**:
    -   Filter: Exclude rows with `null` mood.
    -   Group: By `participant_id`, `date`.
    -   Aggregate: Compute `total_steps`, `mean_mood`, `mood_std`, `n_mood_ratings`.
    -   **Derive Metrics**:
        -   If `sleep_duration` is missing in raw data, compute from accelerometer inactivity periods (nighttime).
        -   If `baseline_affect` is missing, compute from baseline survey responses.
    -   Filter: Drop groups where `n_mood_ratings < 2` (for Primary Model).
    -   Transform: Compute `log_mood_var`.
    -   Join: Attach `sleep_duration` (daily avg) and `baseline_affect`.
3.  **Output**: `daily_aggregates.csv` (for modeling).

## Constraints

-   `total_steps` $\ge 0$.
-   `mood_std` $\ge 0$.
-   `n_mood_ratings` $\ge 2$ (for valid variance calculation in Primary Model).
-   `log_mood_var` defined for all rows (offset 0.01 applied).