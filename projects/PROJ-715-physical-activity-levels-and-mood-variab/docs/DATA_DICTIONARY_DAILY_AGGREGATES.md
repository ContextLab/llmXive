# Data Dictionary: `daily_aggregates.csv`

## Overview
This file contains daily aggregated metrics derived from the StudentLife dataset.
Each row represents a unique `participant_id` and `date` combination.
The data is the primary input for the statistical modeling phase.

## File Location
`data/processed/daily_aggregates.csv`

## Schema
The file is a CSV with the following columns:

| Column Name | Type | Description | Constraints/Notes |
|:--- |:--- |:--- |:--- |
| `participant_id` | string | Unique identifier for the study participant. | Not null. |
| `date` | date | The date of the observation (YYYY-MM-DD). | Not null. |
| `total_steps` | int | Total number of steps recorded for the day. | Can be 0. Not null. |
| `mean_mood` | float | Average mood rating for the day. | Calculated from EMA responses. |
| `mood_std` | float | Standard deviation of mood ratings for the day. | Calculated from EMA responses. |
| `log_mood_std` | float | Log-transformed mood variability: `np.log(mood_std + 0.01)`. | Used as outcome in LMM. Prevents log(0). |
| `sleep_duration` | float | Estimated sleep duration in hours. | Derived or raw. May be null if missing > threshold. |
| `baseline_affect` | float | Participant's baseline affect score. | Derived from pre-study survey or rolling mean. |
| `day_of_week` | int | Day of the week (0=Monday, 6=Sunday). | Categorical in models. |
| `rating_count` | int | Number of EMA mood ratings collected for the day. | Used for filtering (min 2). |

## Derivation Logic

### `mean_mood` and `mood_std`
- Calculated only for days with **at least 2 valid mood ratings**.
- Days with fewer than 2 ratings are excluded from the final dataset.

### `log_mood_std`
- Formula: `np.log(mood_std + 0.01)`
- Purpose: Normalizes the distribution of mood variability and handles zero variability
 (days where mood was constant) without generating `NaN` or `Inf` values.
- The `+ 0.01` is a small constant offset to ensure the log argument is positive.

### `total_steps`
- Sum of all step counts recorded for the participant on that day.
- If no steps are recorded, the value is `0` (not null), preserving the day for analysis.

### `sleep_duration`
- Extracted from raw accelerometer data or self-reports.
- If data is missing for a day and the missingness exceeds the configured threshold,
 the value may be derived or left as null (depending on `config.MISSINGNESS_THRESHOLD`).

### `baseline_affect`
- If not present in the raw data, this is derived using a rolling mean or pre-study
 baseline values.
- Used as a control variable in the LMM.

## Quality Control
- **Missing Values**: Critical fields (`participant_id`, `date`, `total_steps`) must not be null.
- **Outliers**: Extreme step counts (> 50,000) are flagged but retained unless specified in `config`.
- **Validation**: The file is validated against `specs/001-physical-activity-levels-and-mood-variability/contracts/daily_aggregates.schema.yaml`.

## Usage in Analysis
This dataset is loaded by `code/analysis.py` to fit the primary Linear Mixed-Effects Models:
1. **Model A**: Outcome = `log_mood_std`, Predictor = `total_steps`.
2. **Model B**: Outcome = `mean_mood`, Predictor = `total_steps`.
Both models control for `sleep_duration`, `day_of_week`, and `baseline_affect`.