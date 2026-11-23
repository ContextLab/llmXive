# Data Model: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

## Entity-Relationship Overview

The data model consists of three core entities: `Participant`, `Stimulus`, and `GazeEvent`. These entities are linked to form the analysis-ready dataset.

### Entities

#### Participant
Represents an individual in the study.
- **Attributes**:
  - `participant_id` (string, unique): Unique identifier.
  - `cognitive_reflection_score` (float): Score on the Cognitive Reflection Test (CRT).
  - `random_intercept` (float): Random intercept value for the mixed-effects model.
  - `data_loss_percent` (float): Percentage of data loss (used for filtering).

#### Stimulus
Represents a news headline used in the experiment.
- **Attributes**:
  - `headline_id` (string, unique): Unique identifier.
  - `headline_text` (string): The text content of the headline.
  - `emotional_valence` (float): Calculated emotional valence score (NRC or VADER).
  - `random_intercept` (float): Random intercept value for the mixed-effects model.

#### GazeEvent
Represents a fixation event recorded during the eye-tracking task.
- **Attributes**:
  - `event_id` (string, unique): Unique identifier.
  - `participant_id` (string, FK): Link to Participant.
  - `headline_id` (string, FK): Link to Stimulus.
  - `timestamp` (float): Timestamp of the fixation.
  - `duration` (float): Duration of the fixation in milliseconds.
  - `roi_type` (string): Type of ROI (e.g., "source_attribution", "headline_body").
  - `x_coord` (float): X-coordinate of the fixation.
  - `y_coord` (float): Y-coordinate of the fixation.

### Relationships

- **Participant** 1:N **GazeEvent**: One participant has multiple gaze events.
- **Stimulus** 1:N **GazeEvent**: One stimulus (headline) is associated with multiple gaze events.
- **AnalysisResult**: A derived entity representing the output of the regression model, containing coefficients, p-values, and confidence intervals.

## Data Flow

1. **Raw Data**: Ingested from Hugging Face datasets into `data/raw/`.
2. **Preprocessing**:
   - Fixation detection (I-VT) applied.
   - Participants with >20% data loss filtered.
   - ROI mapping performed.
   - Output: `data/derived/preprocessed_gaze.csv`.
3. **Valence Calculation**:
   - NRC/VADER applied to `headline_text`.
   - Output: `data/derived/valence_scores.csv`.
4. **Merging**:
   - `preprocessed_gaze.csv`, `valence_scores.csv`, and `participant_scores.csv` merged.
   - Output: `data/derived/merged_dataset.csv`.
5. **Analysis**:
   - Mixed-effects regression performed on `merged_dataset.csv`.
   - Output: `data/processed/regression_results.json`.
6. **Robustness**:
   - Threshold sweep performed on `merged_dataset.csv`.
   - Output: `data/processed/robustness_results.json`.

## Data Hygiene

- **Checksumming**: All files in `data/raw/` are checksummed (SHA-256) upon ingestion.
- **No In-Place Modification**: All derivations create new files with timestamps.
- **PII Scan**: No personally identifiable information (PII) is stored in `data/`.
- **Versioning**: Every artifact in `data/` carries a content hash recorded in `state/artifacts.yaml`.

## Schema Validation

All data files must conform to the schemas defined in `contracts/`. The `dataset.schema.yaml` defines the structure of `merged_dataset.csv`, and `output.schema.yaml` defines the structure of `regression_results.json`.