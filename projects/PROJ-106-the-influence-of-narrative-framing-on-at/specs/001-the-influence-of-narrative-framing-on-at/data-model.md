# Data Model: The Influence of Narrative Framing on Attitudes Towards AI Assistance

## Overview
This document defines the data structures for the experiment, including the stimuli, raw survey responses, and derived analysis datasets. All data is stored in CSV format with strict schema validation.

## Entity Definitions

### 1. Participant
Unique identifier for a survey respondent.
-   `participant_id`: String (UUID or sequential hash).
-   `condition`: String (`"partner"`, `"tool"`).
-   `age`: Integer (optional, for robustness checks).
-   `gender`: String (optional, for robustness checks).
-   `timestamp`: ISO 8601 DateTime.

### 2. Stimulus (Vignette)
The text presented to the participant.
-   `stimulus_id`: String (e.g., `"vignette_partner_v1"`).
-   `framing`: String (`"partner"`, `"tool"`).
-   `text_content`: String (Full vignette text).
-   `readability_score`: Float (Flesch-Kincaid).
-   `sentiment_score`: Float (VADER Compound).

### 3. Response Set
The survey answers for a participant.
-   `participant_id`: String (FK).
-   `attitude_q1` ... `attitude_q7`: Integer (1-7 Likert).
-   `usefulness_q1` ... `usefulness_q3`: Integer (1-7 Likert).
-   `trust_q1` ... `trust_q4`: Integer (1-7 Likert).
-   `manipulation_check`: Integer (1 = Correct, 0 = Incorrect).
-   `completion_status`: String (`"complete"`, `"partial"`).

## Derived Fields (Computed)
-   `attitude_score`: Sum of `attitude_q1` to `attitude_q7`.
-   `usefulness_score`: Sum of `usefulness_q1` to `usefulness_q3`.
-   `trust_score`: Sum of `trust_q1` to `trust_q4`.
-   `manipulation_check_failed`: Boolean (True if `manipulation_check` == 0).

## File Structure & Hygiene

| File Path | Description | Schema | Checksum |
| :--- | :--- | :--- | :--- |
| `data/raw/survey_export_YYYYMMDD.csv` | Raw export from survey platform. | `contracts/raw_survey.schema.yaml` | SHA-256 |
| `data/stimuli/vignettes.csv` | Generated stimuli with metrics. | `contracts/stimuli.schema.yaml` | SHA-256 |
| `data/processed/cleaned_data.csv` | Filtered, derived scores, flagged. | `contracts/cleaned_data.schema.yaml` | SHA-256 |

## Data Validation Rules
1.  **Range**: Likert items must be integers in [1, 7].
2.  **Completeness**: No missing values in primary DVs for inclusion in analysis.
3.  **Uniqueness**: `participant_id` must be unique per file.
4.  **Consistency**: `condition` in `cleaned_data` must match the `framing` of the stimulus assigned.

## Privacy & Ethics
-   **PII**: No names, emails, or IP addresses stored in `data/`.
-   **Consent**: Consent logs stored separately in `data/ethics/` (access restricted), not linked to response data in committed artifacts.
