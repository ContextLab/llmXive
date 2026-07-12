# Data Model: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Entities

### 1. Stimulus
Represents a specific visual image variant used in the experiment.
- **Attributes**:
  - `stimulus_id`: Unique identifier (string).
  - `scenario_id`: Identifier for the base scenario (string).
  - `salience_level`: Categorical (low, medium, high).
  - `file_path`: Relative path to the image file.
  - `manipulation_params`: JSON object containing `brightness_factor`, `contrast_factor`.
  - `created_at`: Timestamp of generation.

### 2. Participant
Represents an individual completing the survey.
- **Attributes**:
  - `participant_id`: Unique identifier (string).
  - `start_time`: Timestamp.
  - `end_time`: Timestamp.
  - `valid`: Boolean (true if not a straight-liner).

### 3. Response
Represents a single rating provided by a participant for a stimulus.
- **Attributes**:
  - `response_id`: Unique identifier (string).
  - `participant_id`: Foreign key to Participant.
  - `stimulus_id`: Foreign key to Stimulus.
  - `blame_rating`: Integer (1-7).
  - `timestamp`: Timestamp of response.

## Relationships
- **Stimulus** (1) --- (N) **Response** (A stimulus is rated by multiple participants).
- **Participant** (1) --- (N) **Response** (A participant rates multiple stimuli).

## Data Flow
1. **Raw Data**: Downloaded images (if available) or generated placeholders.
2. **Processed Stimuli**: `data/processed/stimuli/` containing generated variants.
3. **Survey Data**: `data/raw/survey_responses.csv` (input from survey platform).
4. **Cleaned Data**: `data/processed/cleaned_responses.csv` (filtered for straight-liners).
5. **Results**: `data/results/analysis_results.json` (ANOVA tables, effect sizes).

## Storage Format
- **Images**: `.png` (lossless, small size).
- **Tabular Data**: `.csv` (comma-separated, UTF-8).
- **Metadata/Results**: `.json` (structured).
