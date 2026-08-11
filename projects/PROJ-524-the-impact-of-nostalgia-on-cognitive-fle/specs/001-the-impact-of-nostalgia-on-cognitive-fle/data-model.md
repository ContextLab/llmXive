# Data Model: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

**Version**: 1.0
**Generated**: Based on Specification `spec.md` and Task `T020a` (Dataset Schema)
**Project**: PROJ-524

## 1. Overview

This document defines the logical data model for the study investigating the impact of nostalgia on cognitive flexibility in aging adults. The model centers on participant performance data collected via the Wisconsin Card Sorting Test (WCST) under two distinct stimulus conditions: **Nostalgia** and **Control**.

The data model supports a between-subjects experimental design where participants are assigned to one condition, and their cognitive flexibility is measured using standard WCST metrics.

## 2. Core Entities

### 2.1 Participant
Represents an individual subject in the study.

| Attribute | Type | Constraints | Description |
|:--- |:--- |:--- |:--- |
| `participant_id` | String (UUID) | **Primary Key**, Unique, Non-Null | Unique identifier for the participant. |
| `age` | Integer | **Required**, $\ge$ 65 | Age of the participant at the time of testing. |
| `stimulus_type` | String | **Required**, Enum: `['nostalgia', 'control']` | The experimental condition assigned to the participant. |
| `mmse` | Integer | **Optional**, Range: 0-30 | Mini-Mental State Examination score. Used to screen for cognitive impairment. |

### 2.2 CognitivePerformance
Represents the outcome metrics for a participant's performance on the WCST.

| Attribute | Type | Constraints | Description |
|:--- |:--- |:--- |:--- |
| `participant_id` | String (UUID) | **Foreign Key** -> Participant | Links performance to the specific participant. |
| `perseverative_errors` | Integer | **Required**, $\ge$ 0 | Number of perseverative errors (repeating a previously correct rule). |
| `categories_completed` | Integer | **Required**, $\ge$ 0 | Number of sorting categories successfully completed. |

## 3. Relationships

- **Participant (1) ↔ (N) CognitivePerformance**:
 In this specific implementation, the model assumes a **1:1** relationship for the primary analysis (one performance record per participant). If longitudinal data is added in future phases, this relationship would expand to 1:N.

- **Data Flow**:
 1. **Raw Ingestion**: Data is fetched from external sources (OpenML/HuggingFace) containing columns mapping to the `Participant` and `CognitivePerformance` attributes.
 2. **Validation & Filtering**:
 - `age` must be $\ge$ 65.
 - `stimulus_type` must be valid.
 - `perseverative_errors` and `categories_completed` must be non-null.
 3. **MMSE Conditional Logic**:
 - The `mmse` field is **optional** in the source data.
 - If `mmse` is present, records with `mmse < 24` are excluded (indicating cognitive impairment).
 - If `mmse` is absent, this exclusion step is skipped, and a flag `has_mmse = false` is recorded.

## 4. Field Specifications & Constraints

### 4.1 Required Fields
- `participant_id`: Must be unique across the dataset.
- `age`: Must be an integer $\ge$ 65. Records failing this are excluded.
- `stimulus_type`: Must be either "nostalgia" or "control".
- `perseverative_errors`: Must be a non-negative integer.
- `categories_completed`: Must be a non-negative integer.

### 4.2 Optional Fields (Conditional)
- `mmse`:
 - **Nature**: Optional. The dataset may or may not include this column.
 - **Handling**:
 - If present: Values $< 24$ trigger exclusion (log `ERR_MMSE_IMPAIRED`).
 - If absent: The pipeline proceeds without MMSE filtering (log `SKIP_MMSE_EXCLUSION`).
 - **Storage**: The presence/absence of this column is tracked in `data/processed/mmse_flag.json`.

## 5. Schema Mapping (Source to Internal)

The ingestion pipeline (`code/ingestion.py`) maps external column names to this internal model:

| Internal Field | Source Column (Expected) | Transformation |
|:--- |:--- |:--- |
| `participant_id` | `participant_id`, `id`, `subject_id` | String normalization |
| `age` | `age` | Cast to Integer |
| `stimulus_type` | `stimulus_type`, `condition`, `group` | Lowercase, Enum validation |
| `perseverative_errors` | `perseverative_errors`, `pe` | Cast to Integer |
| `categories_completed` | `categories_completed`, `cc` | Cast to Integer |
| `mmse` | `mmse`, `mini_mental_state` | Cast to Integer (Optional) |

## 6. Data Integrity Rules

1. **Age Constraint**: No record with `age < 65` is allowed in the final `cleaned_dataset.csv`.
2. **Score Constraint**: No record with null `perseverative_errors` or `categories_completed` is allowed.
3. **MMSE Constraint**: If the `mmse` column exists, no record with `mmse < 24` is allowed in the final cleaned dataset.
4. **Stimulus Balance**: The dataset should contain records for both "nostalgia" and "control" groups to enable Welch's t-test.

## 7. File Artifacts

The data model is realized through the following files:

- **Raw Data**: `data/raw/raw_dataset.csv` (Unfiltered source data)
- **Intermediate**: `data/processed/cleaned_dataset_intermediate.csv` (Post-age/score filter, pre-MMSE filter if applicable)
- **Final Output**: `data/processed/cleaned_dataset.csv` (Fully filtered dataset)
- **Flags**: `data/processed/mmse_flag.json` (Tracks if MMSE exclusion was applied)
- **Exclusion Log**: `data/processed/exclusion_log.json` (Counts of excluded records per reason)