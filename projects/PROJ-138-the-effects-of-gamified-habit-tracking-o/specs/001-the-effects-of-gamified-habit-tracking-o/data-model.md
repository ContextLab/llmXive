# Data Model: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

## Entity Definitions

### 1. User Profile
Represents an anonymized individual participant.
- **`user_id`**: Integer, unique identifier.
- **`gamified_status`**: Integer (0 or 1). 1 = uses gamified app, 0 = non-gamified.
- **`conscientiousness_score`**: Float (0.0 - 100.0). Standardized score.
- **`need_for_achievement_score`**: Float (0.0 - 100.0). Standardized score.
- **`consent_verified`**: Boolean. True if consent artifact exists.

### 2. Behavioral Log (Daily)
Represents a single daily activity event.
- **`user_id`**: Integer, foreign key to User Profile.
- **`date`**: ISO 8601 date string (YYYY-MM-DD).
- **`event_type`**: String (e.g., "habit_completed", "goal_reached").
- **`app_id`**: String (e.g., "habitica", "todoist"). Used to derive `gamified_status`.

### 3. Weekly Aggregation
Derived entity for longitudinal analysis.
- **`user_id`**: Integer.
- **`week_number`**: Integer (1 to 12).
- **`adherence_flag`**: Integer (0 or 1). 1 if ≥1 event in week.
- **`streak_length`**: Integer. Consecutive weeks of adherence.
- **`dropout_event`**: Boolean. True if 3 consecutive weeks of 0 adherence.

### 4. Analysis Result
Derived entity for statistical outputs.
- **`test_type`**: String (e.g., "MixedEffects", "CoxPH", "LogRank").
- **`coefficient`**: Float.
- **`p_value`**: Float.
- **`confidence_interval_lower`**: Float.
- **`confidence_interval_upper`**: Float.
- **`sample_size`**: Integer.

## Data Flow

1. **Ingestion**: `synthetic_generator.py` creates `data/raw/synthetic_data.csv` (User + Daily Logs) OR API data is fetched.
2. **Validation**: `ingestion.py` checks schema and `MIN_TOTAL_RECORDS` (≥100).
3. **Aggregation**: `aggregation.py` converts Daily Logs → Weekly Aggregation.
4. **Merging**: `data/processed/merged_data.csv` combines User Profile + Weekly Aggregation.
5. **Modeling**: `modeling.py` consumes `merged_data.csv` to produce `Analysis Result` objects.
6. **Reporting**: `generate_report.py` consumes `Analysis Result` to produce HTML/PDF.

## Constraints & Validations

- **N ≥ 100**: Pipeline halts if `len(merged_data)` < 100.
- **Consent Check**: Pipeline halts if `data/consent/` is empty (FR-010).
- **Collinearity**: VIF > 5 triggers removal of `need_for_achievement` (FR-002).
- **Event Count**: Survival analysis halts if dropout events < 10 per group (FR-009).
