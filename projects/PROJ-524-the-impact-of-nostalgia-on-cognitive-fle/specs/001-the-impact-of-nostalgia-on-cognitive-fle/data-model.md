# Data Model: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## Overview

This document defines the data entities, relationships, and constraints for the project investigating the impact of nostalgia on cognitive flexibility in aging adults. The model supports the ingestion of WCST (Wisconsin Card Sorting Test) data, demographic information, and optional cognitive impairment screening results.

## Entities

### 1. Participant

Represents a single individual enrolled in the study.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `participant_id` | String | Unique identifier for the participant. | Primary Key, Not Null, Unique |
| `age` | Integer | Age of the participant in years. | Not Null, Min: 65 (for inclusion) |
| `stimulus_type` | Enum | The experimental condition assigned. | Values: `['nostalgia', 'control']`, Not Null |
| `perseverative_errors` | Integer | Number of perseverative errors on WCST. | Not Null, Min: 0 |
| `categories_completed` | Integer | Number of categories successfully completed on WCST. | Not Null, Min: 0 |
| `MMSE` | Integer | Mini-Mental State Examination score. | **Optional**, Range: 0-30, Min: 24 (if present and used for exclusion) |

### 2. StudySession

Represents a single testing instance for a participant (1:1 with Participant in this simplified schema, but modeled for potential expansion).

*Note: In the current implementation (T010a-T014a), the Participant and Session are flattened into a single dataframe row for efficiency, but the logical entity remains.*

## Relationships

- **Participant 1..1 Session**: Each participant record corresponds to one study session data point in this dataset.
- **Participant 0..1 MMSE**: A participant may or may not have an MMSE score recorded.

## Optional Field: MMSE

The `MMSE` (Mini-Mental State Examination) field is **optional** in the raw dataset.

- **Presence**: If the source dataset includes an `MMSE` column, it is validated and used for exclusion criteria (excluding scores < 24 to filter out cognitive impairment).
- **Absence**: If the `MMSE` column is missing from the source:
 1. The system sets `has_mmse = False` in `data/processed/mmse_flag.json`.
 2. The MMSE exclusion step (T012e) is skipped.
 3. All other valid records (age >= 65, non-null cognitive metrics) are retained.
- **Validation**: The presence or absence of this field is explicitly logged in `data/processed/exclusion_log.json` and the `mmse_flag.json` artifact.

## Data Flow & Constraints

1. **Ingestion**: Raw data is fetched from OpenML/HuggingFace or generated as a deterministic fallback (T010a).
2. **Validation**:
 - `age` must be >= 65.
 - `stimulus_type` must be present.
 - `perseverative_errors` and `categories_completed` must be non-null.
3. **Filtering**:
 - If `MMSE` exists: Filter out records where `MMSE < 24`.
 - If `MMSE` missing: Proceed without this filter.
4. **Output**: Cleaned dataset saved to `data/processed/cleaned_dataset.csv` with schema:
 - `participant_id`, `stimulus_type`, `perseverative_errors`, `categories_completed`, `age`.
 - `MMSE` is excluded from the final output unless explicitly required for downstream analysis (current spec excludes it from the primary cleaned dataset to focus on the core cognitive metrics).

## Schema Compliance

This model aligns with `contracts/dataset.schema.yaml` generated in T020a.
- `participant_id`: String (PK)
- `age`: Integer (>= 65)
- `stimulus_type`: String (Enum)
- `perseverative_errors`: Integer
- `categories_completed`: Integer
- `MMSE`: Integer (Optional)