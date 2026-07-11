# Data Model: The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers

## Entity Relationship Overview

The data model consists of three primary entities: `Participant`, `NoiseLog`, and `TaskScore`. Data flows from `Raw` (immutable) to `Processed` (aggregated) to `Results` (model outputs).

### 1. Participant
Represents a unique remote worker.
- **Attributes**:
  - `participant_id` (str): Unique identifier.
  - `age` (int): Age in years.
  - `gender` (str): Self-reported gender.
  - `job_type` (str): Category of employment.
  - `noise_sensitivity` (float): Self-reported score (1-5).
  - `valid_logging_hours` (float): Total hours of valid noise logging.
  - `task_completion_rate` (float): Proportion of completed trials (0.0-1.0).
  - `is_excluded` (bool): Flag set if `valid_logging_hours` < 80% or `task_completion_rate` < 90%.

### 2. NoiseLog
Time-series record of ambient sound.
- **Attributes**:
  - `log_id` (str): Unique log identifier.
  - `participant_id` (str): Foreign key to `Participant`.
  - `timestamp` (datetime): Time of measurement.
  - `decibel_level` (float): Calibrated dB level.
  - `hourly_avg` (float): Average dB for the hour (derived).
  - `hourly_std` (float): Standard deviation for the hour (derived).

### 3. TaskScore
Performance metric for cognitive flexibility.
- **Attributes**:
  - `score_id` (str): Unique score identifier.
  - `participant_id` (str): Foreign key to `Participant`.
  - `trial_type` (str): "switch" or "repeat".
  - `reaction_time_ms` (float): Reaction time in milliseconds.
  - `error_count` (int): Number of errors in the trial.
  - `test_time` (str): "baseline" or "final".
  - `normalized_rt` (float): Log-transformed RT after outlier removal.

## Data Flow

1. **Raw Data (`data/raw/`)**:
   - `mturk_scores.csv`: Original task scores (Verified Source).
   - `noise_logs.csv`: (Synthetic for pipeline) Raw decibel logs.
2. **Processed Data (`data/processed/`)**:
   - `participants_filtered.csv`: Participants meeting validity criteria.
   - `noise_aggregated.csv`: Hourly averages and standard deviations.
   - `task_normalized.csv`: Cleaned, log-transformed reaction times.
   - `analysis_dataset.csv`: Merged dataset for modeling (Participant + Noise + Task).
3. **Results (`data/results/`)**:
   - `model_summary.json`: LMM coefficients, p-values, confidence intervals.
   - `sensitivity_sweep.json`: Results of threshold variations.
   - `figures/`: PNG/SVG plots (RT vs. Noise, Sensitivity curves).

## Schema Constraints

- **Integrity**: `participant_id` must be unique in `Participant`.
- **Range**: `decibel_level` must be > 0. `reaction_time_ms` must be > 0.
- **Validity**: `is_excluded` must be `False` for any record included in `analysis_dataset.csv`.
- **Normalization**: `normalized_rt` must be calculated *after* outlier removal.
