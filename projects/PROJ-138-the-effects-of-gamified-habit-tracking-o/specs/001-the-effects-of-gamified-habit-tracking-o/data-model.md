# Data Model: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

## Overview
This document defines the schema for the data pipeline, from raw generation to the final analysis-ready dataset. All data is stored in CSV/Parquet format to ensure reproducibility and compatibility with the CI environment.

## Entity Definitions

### 1. User Profile (Synthetic)
Represents an anonymized individual with personality traits and group assignment.
- `user_id`: `str` (UUID format, e.g., "usr_001"). Unique identifier.
- `gamification_status`: `int` (0 or 1). 1 = Gamified app, 0 = Non-gamified. (Randomly assigned).
- `conscientiousness_score`: `float` (0.0 to 1.0). Normalized BFI score.
- `achievement_score`: `float` (0.0 to 1.0). Normalized Need for Achievement score.
- `created_at`: `str` (ISO8601). Date of simulated account creation.

### 2. Behavioral Log (Synthetic)
Represents a daily record of user activity.
- `user_id`: `str` (Foreign Key to User Profile).
- `date`: `str` (ISO8601, YYYY-MM-DD).
- `event_type`: `str` (e.g., "habit_check", "badge_earned").
- `app_id`: `str` (e.g., "app_gamified_01", "app_plain_01").

### 3. Weekly Aggregation (Derived)
Derived table for longitudinal modeling.
- `user_id`: `str`.
- `week_number`: `int` (1, 2, 3...). Sequential from account start.
- `adherence_flag`: `int` (0 or 1). 1 if ≥ 1 event in week, 0 otherwise.
- `streak_length`: `int`. Current consecutive weeks of adherence.
- `dropout_event`: `int` (0 or 1). 1 if 3 consecutive weeks of 0 adherence occurred.

### 4. Analysis Result (Derived)
Output of statistical tests.
- `test_type`: `str` (e.g., "MixedEffects", "CoxPH").
- `coefficient`: `float`.
- `p_value`: `float`.
- `confidence_interval_low`: `float`.
- `confidence_interval_high`: `float`.
- `sample_size`: `int`.
- `recovery_error`: `float` (Optional, for synthetic data). Difference between estimated and true parameter.

## Data Flow

1.  **Ingestion**: `code/data/ingestion.py` generates `raw/user_profile.csv` and `raw/behavioral_logs.csv`.
    - *Constraint*: Must include `CONSENT_PLACEHOLDER.txt` check (FR-010).
    - *Note*: Personality scores are generated from a multivariate normal distribution using BFI parameters. No external CSV ingestion.
2.  **Validation**: `code/data/validation.py` checks for missing IDs, valid scores, and consent.
3.  **Aggregation**: `code/data/aggregation.py` joins logs by user, bins by week, calculates `adherence_flag` and `streak_length`.
    - *Logic*: `week_number` = floor((date - start_date) / 7 days).
    - *Logic*: `dropout_event` = 1 if `adherence_flag` == 0 for 3 consecutive weeks.
4.  **Merge**: Final dataset `processed/merged_data.csv` contains one row per (user, week).

## Data Hygiene Rules
- **Checksums**: All raw and processed files are checksummed (SHA-256) and stored in `state/`.
- **PII**: No real names, emails, or IPs are generated. `user_id` is a random UUID.
- **Immutability**: Raw files are never overwritten. Derived files use new timestamps.

## Assumptions
- Personality scores are static (measured at baseline).
- "Gamified" status is binary and stable.
- Dropouts are censored if the user leaves the study before 3 weeks of non-adherence.
- The "ground truth" parameters used in generation are known and used for recovery error calculation.
