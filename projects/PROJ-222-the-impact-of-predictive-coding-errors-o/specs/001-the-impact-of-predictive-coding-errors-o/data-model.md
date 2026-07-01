# Data Model: The Impact of Predictive Coding Errors on Subjective Time Perception

## Entity Definitions

### 1. Trial
Represents a single stimulus presentation within an experiment.
- **Attributes**:
  - `trial_id` (string): Unique identifier for the trial.
  - `participant_id` (string): Identifier for the participant.
  - `stimulus_sequence` (list of strings): The sequence of stimuli presented up to this trial.
  - `surprisal` (float): Negative log probability of the observed stimulus given the history (computed via Markov model).
  - `duration_estimate` (float): Participant's subjective estimate of elapsed time (in seconds or ms).
  - `stimulus_modality` (string): Type of stimulus (e.g., "visual", "auditory").
  - `sequence_length` (integer): Number of stimuli in the sequence.
  - `experimental_design_type` (string, optional): e.g., "oddball", "random", "unknown". **Required for valid surprisal computation.**

### 2. Participant
Represents an individual subject.
- **Attributes**:
  - `participant_id` (string): Unique identifier.
  - `condition_assignments` (list of strings): Conditions assigned to the participant (if applicable).
  - `trial_count` (integer): Number of trials completed.

### 3. Dataset
Represents a source data collection.
- **Attributes**:
  - `source_url` (string): Verified URL of the dataset.
  - `dataset_id` (string): Identifier (OpenML ID or HF path).
  - `total_trials` (integer): Total number of trials in the source.
  - `total_participants` (integer): Total number of participants.
  - `variable_availability` (dict): Boolean flags for required variables (duration_estimate, stimulus_sequence, etc.).
  - `exclusion_reason` (string, optional): Reason for exclusion if missing variables.
  - `experimental_design_type` (string, optional): Type of design (e.g., "oddball").

## Data Flow

1.  **Raw Data**: Downloaded from verified URLs to `data/raw/`. Format: Parquet, CSV, or JSON.
2.  **Preprocessing**:
    - Filter for studies with sequential stimuli.
    - **Gate 0**: Check for `duration_estimate` and `stimulus_sequence`. If missing, exclude.
    - Compute `surprisal` using a first-order Markov model if missing AND `experimental_design_type` is valid.
    - Validate `duration_estimate` presence.
    - Output: Standardized CSV in `data/processed/`.
3.  **Analysis**:
    - Load processed CSV.
    - Fit LMM.
    - Generate metrics (effect sizes, p-values, MDE).
4.  **Output**:
    - Statistical tables (JSON/CSV).
    - Figures (PNG, 300 DPI).

## Data Integrity Rules

- **Checksums**: Every file in `data/raw/` must have a corresponding checksum in `data/README.md`.
- **No In-Place Modification**: Raw data is never altered. All transformations create new files.
- **PII**: No Personally Identifiable Information is allowed in `data/`.
- **Variable Consistency**: All datasets must be normalized to the `Trial` schema before analysis.
- **Design Validity**: Surprisal is only computed if `experimental_design_type` indicates a structured experiment.