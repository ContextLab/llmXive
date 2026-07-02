# Data Model: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

## Overview
This document defines the data structures, transformations, and schemas used throughout the research pipeline. The design reflects a **cross‑sectional** study (one row per user) because the MyPersonality dataset provides only a single observation per participant.

## Input Data Schema
**Source**: `data/raw/mypersonality.parquet`  
**Format**: Parquet

**Key Fields**:
- `user_id`: Unique identifier (string/int).
- `conscientiousness`: Score (float, 1‑5 or 1‑7 scale).
- `need_for_achievement`: Score (float, if available).
- `habit_tracking_method`: Categorical (e.g., "app", "paper", "none").
- `gamified_app_usage`: Categorical/Binary (e.g., "yes", "no", "points").
- `habit_duration`: Integer (weeks tracked, self‑reported).
- `entry_frequency`: Integer (entries per week, self‑reported).

**Derived Fields**:
- `gamified_binary`: 1 if `gamified_app_usage` indicates gamified features, 0 otherwise.
- `long_term_adherence`: 1 if `habit_duration` > 4 weeks (or equivalent frequency), 0 otherwise.
- `dropout_event`: **null** (not applicable for cross‑sectional data).

## Output Data Schema
**Target**: `data/processed/results.json` (JSON)  
**Format**: JSON adhering to `contracts/output.schema.yaml`

**Key Fields**:
- `logistic_regression_model.interaction_coefficient`
- `logistic_regression_model.interaction_p_value`
- `logistic_regression_model.interaction_ci_lower`
- `logistic_regression_model.interaction_ci_upper`
- `logistic_regression_model.sample_size`
- `bootstrapping.effect_size_mean`
- `bootstrapping.effect_size_ci_lower`
- `bootstrapping.effect_size_ci_upper`
- `bootstrapping.iterations` (1000)
- `sensitivity_analysis.thresholds_tested`
- `sensitivity_analysis.p_value_stability`

## Data Flow

1. **Ingestion** (`code/ingest.py`):
   - Load parquet, verify required columns, compute Cronbach’s α for the Big Five, and write `cleaned_data.csv`.
   - **Validation**: The resulting CSV is validated against `contracts/dataset.schema.yaml` using `jsonschema`.

2. **Cleaning**:
   - Exclude rows with missing `gamified_binary` or `long_term_adherence`.
   - Standardise `conscientiousness` (z‑score) if needed.
   - Ensure the cleaned file conforms to the dataset schema.

3. **Transformation**:
   - No reshaping to long format; each user remains a single record.
   - Derive binary adherence and gamification flags.

4. **Analysis** (`code/modeling.py`):
   - Fit logistic regression with interaction.
   - Compute VIF, apply multiple‑comparison correction, run 5‑fold CV, bootstrap, and sensitivity analysis.
   - **Output** conforms to `contracts/output.schema.yaml`.

5. **Export**:
   - `data/processed/cleaned_data.csv`
   - `data/processed/results.json`
   - Plots saved to `docs/plots/`.

## Error Handling

- **Missing Columns**: Raises `DataInsufficiencyError` with a clear message; pipeline stops before modeling.
- **Small Sample**: If < 100 valid records, generates a “Data Insufficiency” report and halts.
- **Collinearity**: VIF > 5 triggers automatic removal of the collinear moderator (prioritising conscientiousness) and logs the change.
- **Model Non‑Convergence**: Adds a small L2 penalty and retries; logs any adjustments.

## Assumptions

- `conscientiousness` is a continuous predictor suitable for interaction modeling.
- `habit_duration` or `entry_frequency` provides a valid proxy for long‑term adherence.
- The “need for achievement” score, when present, is comparable in scale to conscientiousness.
