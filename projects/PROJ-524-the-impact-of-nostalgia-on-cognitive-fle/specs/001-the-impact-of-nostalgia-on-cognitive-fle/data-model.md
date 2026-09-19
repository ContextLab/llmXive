# Data Model: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## Overview

This document defines the core data entities, attributes, and relationships required for the automated science pipeline analyzing the impact of nostalgia on cognitive flexibility in aging adults. The model supports the between-subjects experimental design described in the project specification.

## Entities

### 1. Participant

Represents an individual human subject enrolled in the study.

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `participant_id` | string | Unique identifier for the participant. | Primary Key, Non-null, Unique |
| `age` | integer | Age of the participant in years. | `age >= 65` (Study inclusion criterion), Non-null |
| `stimulus_condition` | string | The experimental condition assigned to the participant. | Enum: `['nostalgia', 'control']`, Non-null |
| `MMSE` | integer | Mini-Mental State Examination score. | **Optional**. Range 0-30. If present, used for exclusion if `< 24`. |

### 2. Stimulus

Represents the experimental material or prompt presented to the participant.

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `stimulus_id` | string | Unique identifier for the stimulus file or prompt. | Primary Key, Non-null |
| `stimulus_type` | string | Category of the stimulus. | Enum: `['nostalgia', 'control']`, Non-null |
| `file_path` | string | Relative path to the stimulus file in `data/stimuli/`. | Non-null |
| `checksum` | string | SHA-256 hash of the stimulus file for integrity verification. | Non-null |

### 3. Metric

Represents the cognitive performance outcome measured for a participant.

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `metric_id` | string | Unique identifier for the metric record. | Primary Key, Non-null |
| `participant_id` | string | Foreign key linking to the Participant. | Non-null, Foreign Key |
| `perseverative_errors` | integer | Number of perseverative errors on the WCST. | Non-null for valid records |
| `categories_completed` | integer | Number of categories completed on the WCST. | Non-null for valid records |
| `total_trials` | integer | Total number of trials administered. | Optional |

## Relationships

- **Participant (1) ↔ (N) Metric**: A single participant may have multiple metric records if the study design includes multiple sessions or trials, though the primary analysis aggregates to one record per participant per condition.
- **Participant (1) ↔ (1) Stimulus**: In this between-subjects design, a participant is assigned to exactly one stimulus condition (nostalgia OR control). The `stimulus_condition` field in the Participant entity captures this assignment.

## Data Flow & Validation Rules

1. **Ingestion**: Raw data is fetched from the canonical source.
2. **Age Filtering**: Records where `age < 65` are excluded.
3. **Score Filtering**: Records with null `perseverative_errors` or `categories_completed` are excluded.
4. **MMSE Handling**:
 - The `MMSE` field is **optional** in the raw dataset.
 - **Validation**: The pipeline checks if the `MMSE` column exists and contains at least one non-null value.
 - **Flagging**: A flag `has_mmse` is set in `data/processed/mmse_flag.json`.
 - **Exclusion**:
 - If `has_mmse == True`: Records with `MMSE < 24` are excluded (cognitive impairment filter).
 - If `has_mmse == False`: The MMSE exclusion step is skipped, and all records passing age/score filters are retained.
5. **Final Dataset**: The cleaned dataset (`data/processed/cleaned_dataset.csv`) contains only valid participants with complete cognitive metrics and, if applicable, acceptable MMSE scores.

## Schema Representation

The logical schema is enforced via the generated YAML contracts in `contracts/dataset.schema.yaml`.

```yaml
# Simplified logical representation
Participant:
 participant_id: str (PK)
 age: int (>= 65)
 stimulus_condition: str (nostalgia | control)
 MMSE: int? (optional, >= 0, <= 30)

Metric:
 metric_id: str (PK)
 participant_id: str (FK)
 perseverative_errors: int
 categories_completed: int
```

## Notes

- The `MMSE` field's optional nature is critical for robustness. The pipeline must not fail if this column is missing from the source; it must adaptively skip the impairment filter in such cases.
- All string identifiers must be treated as case-sensitive.
- Timestamps for data creation and processing are managed in `data/raw/metadata.json` and `state/state.yaml`.