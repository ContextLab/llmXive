# Data Model: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

## Entity Definitions

### 1. Participant
Represents an individual subject in the study.
- **participant_id**: `string` (Unique ID, e.g., "P001")
- **cognitive_reflection_score**: `float` (Continuous score from CRT, capped at 1st/99th percentile)
- **data_loss_ratio**: `float` (Proportion of trials excluded due to data quality, 0.0 to 1.0)

### 2. Stimulus
Represents a news headline used in the experiment.
- **stimulus_id**: `string` (Unique ID, e.g., "H001")
- **headline_text**: `string` (The raw text of the headline)
- **valence_score**: `float` (Calculated emotional valence, range -1.0 to 1.0)
- **lexicon_source**: `string` ("NRC" or "VADER")

### 3. GazeEvent
Represents a single fixation event mapped to a stimulus.
- **event_id**: `string` (Unique ID)
- **participant_id**: `string` (Foreign Key to Participant)
- **stimulus_id**: `string` (Foreign Key to Stimulus)
- **fixation_duration_ms**: `float` (Duration of fixation in milliseconds)
- **roi_type**: `string` (e.g., "source_attribution", "headline_body")
- **is_valid**: `boolean` (True if fixation meets >100ms threshold)

### 4. AnalysisResult
Represents the output of the regression model.
- **model_id**: `string`
- **coefficient_fixation**: `float`
- **coefficient_valence**: `float`
- **coefficient_crt**: `float`
- **coefficient_interaction_3way**: `float` (The primary metric)
- **p_value_interaction_3way**: `float`
- **ci_lower_3way**: `float`
- **ci_upper_3way**: `float`
- **significance_flag**: `boolean` (True if p < 0.05 after correction)

## Data Flow

1.  **Ingestion**: Raw Parquet files (from verified ROI dataset) are loaded into `Participant` and `GazeEvent` tables.
2.  **Filtering**: Participants with `data_loss_ratio` > 0.20 are excluded.
3.  **Valence Calculation**: `Stimulus` table is populated by applying NRC/VADER to `headline_text`.
4.  **Merge**: `GazeEvent` is joined with `Stimulus` and `Participant` on IDs.
5.  **Aggregation**: Per-participant/stimulus aggregates (e.g., mean fixation duration on "source_attribution") are calculated.
6.  **Regression**: The aggregated dataset is fed into the Mixed-Effects Model.
7.  **Output**: `AnalysisResult` is written to CSV.

## Constraints & Validation Rules
- **Fixation Duration**: Must be $\ge 0$. Values < 100ms are flagged as invalid for primary analysis but retained for robustness checks.
- **Valence**: Must be in range [-1.0, 1.0].
- **CRT**: Must be $\ge 0$. Outliers capped at 1st/99th percentiles.
- **Completeness**: `participant_id` and `stimulus_id` must not be null in the final analysis dataset.
