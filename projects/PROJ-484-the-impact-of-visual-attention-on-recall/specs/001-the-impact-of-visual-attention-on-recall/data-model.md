# Data Model: Visual Attention and Recall of Emotional Stimuli

This document defines the schema for the core entities used in the analysis of the impact of visual attention on recall. It serves as the authoritative reference for data ingestion, preprocessing, and modeling tasks.

## Entity Overview

The dataset is structured around three primary entities:
1. **Participant**: The human subject providing data.
2. **Stimulus**: The visual image presented during the trial.
3. **Trial**: A single instance of a stimulus presentation and the corresponding response/eye-tracking data.

---

## 1. Participant Entity

Represents the demographic and psychological profile of the study subject.

| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `participant_id` | string | Unique identifier for the participant (e.g., "sub-01") | Primary Key, Non-null |
| `age` | integer | Age of the participant in years | `age >= 18` |
| `gender` | string | Gender of the participant | Enum: ['M', 'F', 'Other'] |
| `trait_anxiety` | float | Total score on the State-Trait Anxiety Inventory (STAI) | `0 <= score <= 80` |
| `vision_corrected` | boolean | Whether the participant wore corrective lenses during the task | Non-null |
| `exclusion_reason` | string | Reason for exclusion if the participant was removed from analysis | Nullable |

### Relationships
- One Participant can have many Trials.

---

## 2. Stimulus Entity

Represents the visual content presented to the participant. This dataset primarily uses images from the International Affective Picture System (IAPS) or NimStim sets.

| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `stimulus_id` | string | Unique identifier for the image (e.g., "IAPS_1234" or "NimStim_01") | Primary Key, Non-null |
| `valence` | float | Emotional valence rating (1=Negative, 9=Positive) | `1.0 <= valence <= 9.0` |
| `arousal` | float | Emotional arousal rating (1=Calm, 9=Excited) | `1.0 <= arousal <= 9.0` |
| `dominance` | float | Emotional dominance rating (1=Controlled, 9=In Control) | `1.0 <= dominance <= 9.0` |
| `category` | string | Broad category of the image (e.g., "Nature", "Threat", "Neutral") | Non-null |
| `source` | string | Source dataset of the image (e.g., "IAPS", "NimStim") | Non-null |

### Relationships
- One Stimulus can appear in many Trials.

---

## 3. Trial Entity

Represents the atomic unit of analysis: a specific presentation of a stimulus to a participant, including eye-tracking metrics and recall outcome.

| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `trial_id` | string | Unique identifier for the trial | Primary Key, Non-null |
| `participant_id` | string | FK to Participant | Non-null |
| `stimulus_id` | string | FK to Stimulus | Non-null |
| `recall_correct` | boolean | Binary outcome: 1 if participant correctly recalled the stimulus details, 0 otherwise | Non-null |
| `fixation_duration` | float | Total duration of fixations on the stimulus (ms) | `fixation_duration >= 0` |
| `saccade_count` | integer | Number of saccades detected during the stimulus presentation | `saccade_count >= 0` |
| `pupil_diameter_avg` | float | Average pupil diameter during the trial (mm) | Nullable |
| `gaze_x` | float | Average gaze X coordinate (pixels) | Nullable |
| `gaze_y` | float | Average gaze Y coordinate (pixels) | Nullable |
| `blink_duration` | float | Total duration of blinks during the trial (ms) | `blink_duration >= 0` |
| `missing_data_pct` | float | Percentage of frames with missing eye-tracking data | `0.0 <= pct <= 100.0` |
| `trial_duration` | integer | Total duration of the trial in milliseconds | Non-null |

### Derived Metrics (Preprocessing Output)
- `attention_score`: Calculated as `fixation_duration / trial_duration`.
- `anxiety_group`: Categorical label derived from `trait_anxiety` (e.g., "High", "Low" based on median split).

---

## Schema Validation Rules

1. **Referential Integrity**: Every `participant_id` and `stimulus_id` in the Trial table must exist in their respective parent tables.
2. **Data Types**: All numeric fields must be valid floats/ints; no "NaN" strings or non-numeric characters.
3. **Range Checks**: Valence, Arousal, and Dominance must fall within standard IAPS ranges.
4. **Exclusion Logic**: Trials with `missing_data_pct > 50` or `blink_duration` exceeding 50% of `trial_duration` should be flagged or excluded during the preprocessing phase (T016).

## File Formats

- **Raw Data**: BIDS format (TSV/JSON sidecars).
- **Processed Data**: `data/processed/analysis.csv` (Comma-separated values matching the Trial entity schema).
- **Metadata**: `specs/001-visual-attention-recall/contracts/dataset.schema.yaml` (Machine-readable version of this model).