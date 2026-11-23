# Data Dictionary: Daily Aggregates

**File:** `data/processed/daily_aggregates.csv`
**Schema:** `specs/001-physical-activity-levels-and-mood-variability/contracts/daily_aggregates.schema.yaml`
**Description:** This file contains daily aggregated metrics for each participant, derived from raw step logs and EMA mood ratings. It serves as the primary input for statistical modeling.

## Column Definitions

| Column Name | Type | Required | Description |
|:--- |:--- |:--- |:--- |
| `participant_id` | string | Yes | Unique identifier for the participant. |
| `date` | date | Yes | The date of the observation (YYYY-MM-DD). |
| `total_steps` | integer | Yes | Total number of steps recorded for the participant on this date. Minimum value is 0. |
| `mean_mood` | float | Yes | The average mood rating for the participant on this date. Calculated from EMA responses. |
| `mood_std` | float | Yes | The raw standard deviation of mood ratings for the participant on this date. **Note:** No log transformation is applied here; it is the raw SD. Days with 0 variability (all identical ratings) have `mood_std` = 0.0. |
| `n_mood_ratings` | integer | Yes | The number of valid mood ratings recorded for this participant on this date. Must be ≥ 2 for inclusion. |
| `sleep_duration` | float | No | Average sleep duration in hours for this participant on this date. Nullable if missing in raw data. |
| `baseline_affect` | float | No | Baseline affect score for the participant. Nullable if missing in raw data. |
| `day_of_week` | integer | Yes | Day of the week (0=Monday, 6=Sunday). Derived from the `date` column. |

## Data Generation Logic

- **Filtering:** Days with fewer than 2 mood ratings (`n_mood_ratings < 2`) are excluded from the dataset to satisfy FR-002.
- **Aggregation:**
 - `total_steps`: Sum of step counts from raw logs.
 - `mean_mood`: Mean of EMA mood ratings.
 - `mood_std`: Standard deviation of EMA mood ratings (using population or sample SD as per `pandas` default, unadjusted).
- **Covariates:** `sleep_duration` and `baseline_affect` are derived from raw data if available; otherwise, they are set to `NaN`.

## Constraints & Validation

- **No NaN/Inf:** The `mood_std` column must not contain NaN or Inf values. If all ratings are identical, `mood_std` is recorded as `0.0`.
- **Non-negative:** `total_steps` must be ≥ 0.
- **Mood Variability:** `mood_std` must be ≥ 0.
- **Minimum Ratings:** `n_mood_ratings` must be ≥ 2 (enforced during preprocessing).

## Usage in Analysis

This file is the input for:
1. **Linear Mixed-Effects Models:** `total_steps` is the primary predictor for `log(mood_std + 0.01)` and `mean_mood`.
2. **Validation:** Used in LOPO cross-validation and sensitivity analyses.
3. **Reporting:** Aggregated results and plots are generated based on this data.

## Example Row

```csv
participant_id,date,total_steps,mean_mood,mood_std,n_mood_ratings,sleep_duration,baseline_affect,day_of_week
P001,2023-01-01,5432,3.5,0.8,4,7.2,2.1,6
P001,2023-01-02,8120,4.1,0.5,5,6.8,2.1,0
```
