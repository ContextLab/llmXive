# Data Dictionary: daily_aggregates.csv

This document describes the schema, data types, and business logic for the `data/processed/daily_aggregates.csv` file, which contains daily aggregated metrics for physical activity and mood variability.

## File Information

- **Path:** `data/processed/daily_aggregates.csv`
- **Format:** CSV (Comma-Separated Values)
- **Encoding:** UTF-8
- **Delimiter:** `,`
- **Header:** Yes (first row contains column names)
- **Schema:** `specs/001-physical-activity-levels-and-mood-variability/contracts/daily_aggregates.schema.yaml`

## Column Descriptions

| Column Name | Data Type | Required | Description | Constraints |
|-------------|-----------|----------|-------------|-------------|
| `participant_id` | string | Yes | Unique identifier for each participant | Non-empty string |
| `date` | date | Yes | Calendar date of the observation (YYYY-MM-DD) | Valid ISO 8601 date format |
| `total_steps` | integer | Yes | Total number of steps recorded for the day | Min value: 0 |
| `mean_mood` | float | Yes | Mean of all mood ratings for the day | Range: 1.0 to 7.0 (based on EMA scale) |
| `mood_std` | float | Yes | Standard deviation of mood ratings for the day (raw, untransformed) | Min value: 0.0; No NaN/Inf values |
| `n_mood_ratings` | integer | Yes | Number of valid mood ratings collected for the day | Min value: 2 (days with <2 ratings are excluded) |
| `sleep_duration` | float | No | Total sleep duration in hours | Nullable; derived if missing |
| `baseline_affect` | float | No | Participant's baseline affect score | Nullable; derived if missing |
| `day_of_week` | integer | Yes | Day of week (0=Monday, 6=Sunday) | Range: 0 to 6 |

## Business Logic and Derivations

### 1. Daily Aggregation Logic
- **Input:** Raw step logs (`data/raw/bronze.parquet`) and EMA mood data.
- **Process:**
 1. Parse step logs to compute daily totals per participant.
 2. Align EMA timestamps within a 24-hour window.
 3. Exclude days with fewer than 2 valid mood ratings (per FR-002).
 4. Compute `mean_mood` and `mood_std` (raw standard deviation) for valid days.
 5. Handle days with zero steps by recording `total_steps = 0`.
 6. Handle days with identical mood ratings by recording `mood_std = 0.0` (not NaN).

### 2. Missing Data Handling
- **Step Count:** Missing `step_count` values are treated as 0.
- **Mood Ratings:** Days with missing `mood` values are excluded from aggregation.
- **Covariates:** `sleep_duration` and `baseline_affect` are derived from raw data if missing, using `config.MISSINGNESS_THRESHOLD` to decide between derivation and proceeding without them.

### 3. Exclusion Criteria
- Days with fewer than 2 valid mood ratings are excluded **before** variance calculation.
- Exclusion counts are logged to `data/processed/preprocess_stats.json`.

## Quality Checks

The following assertions are enforced before writing the file:
- `total_steps >= 0` for all rows.
- `mood_std >= 0.0` and no NaN/Inf values in `mood_std`.
- `n_mood_ratings >= 2` for all rows.
- `mean_mood` is within the valid range (1.0 to 7.0).
- No duplicate `(participant_id, date)` pairs.

## Usage in Downstream Analysis

This file serves as the primary input for:
- **User Story 2:** Fitting Linear Mixed-Effects Models (LMM) for mood variability and mean mood.
- **User Story 3:** Leave-One-Participant-Out (LOPO) cross-validation and sensitivity analyses.
- **Reporting:** Generating diagnostic plots and final research reports.

## Schema Validation

The file is validated against `daily_aggregates.schema.yaml` using the `output_validator.py` module. Validation ensures:
- Correct column names and data types.
- Compliance with min/max constraints.
- No null values in required fields.

## Examples

### Sample Row
```csv
participant_id,date,total_steps,mean_mood,mood_std,n_mood_ratings,sleep_duration,baseline_affect,day_of_week
3001,2013-06-01,12500,4.5,0.8,3,7.5,3.2,5
```

### Edge Cases
- **Zero Steps:** `total_steps = 0` is recorded for days with no step data.
- **Zero Variability:** `mood_std = 0.0` when all mood ratings are identical.
- **Missing Covariates:** `sleep_duration` and `baseline_affect` may be null if derivation fails.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-18 | Initial release aligned with spec.md and plan.md |
