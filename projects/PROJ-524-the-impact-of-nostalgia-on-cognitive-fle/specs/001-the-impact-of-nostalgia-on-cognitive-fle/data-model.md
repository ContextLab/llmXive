# Data Model: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## Overview
The data model captures participants, stimuli, and WCST performance metrics required for the analysis. It aligns with the input schema defined in the specification and supports FR-001–FR-007. All data are simulation-generated (seed = 42) and labeled as such.

## Entities

### Participant
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `participant_id` | string | Unique identifier | Primary key, non-null, unique |
| `age` | integer | Age in years | Minimum 65, non-null |
| `stimulus_type` | string | Assigned experimental condition | Enum: `["nostalgia","control"]`, non-null |
| `education_years` | number | Years of education (covariate) | Non-null, ≥ 0 |
| `gender` | string | Gender category (covariate) | Enum: `["female","male","other"]`, non-null |
| `MMSE` | integer (optional) | Mini-Mental State Examination score | Range 0-30; if present and `<24` → exclusion (FR-006) |

### Stimulus
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `stimulus_id` | string | Unique identifier for the media file | Primary key, non-null |
| `stimulus_type` | string | Type of stimulus (renamed from `stimulus_condition` for consistency with the dataset schema) | Enum: `["nostalgia","control"]`, non-null |
| `file_path` | string | Relative path under `data/stimuli/` | Non-null |
| `checksum` | string | SHA-256 hash of the file | Non-null |

### WCSTMetric
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `metric_id` | string | Unique identifier for the metric record | Primary key, non-null |
| `participant_id` | string | FK → Participant | Non-null, must exist |
| `perseverative_errors` | number | Number of perseverative errors | Non-null |
| `categories_completed` | number | Number of categories completed | Non-null |
| `total_trials` | integer (optional) | Total trials administered | Optional |

## Relationships
- **Participant ↔ Stimulus**: One-to-one via `stimulus_type`.
- **Participant ↔ WCSTMetric**: One-to-many (raw trial logs preserved; primary analysis aggregates to one row per participant).

## Validation Rules (implemented in `code/cleaning.py`)
1. **Age Filter** (`FR-001`): Exclude rows where `age` < 65 or missing.
2. **Missing WCST Metrics**: Exclude rows with null `perseverative_errors` or `categories_completed`.
3. **MMSE Handling** (`FR-006`): The canonical field name is `MMSE` (uppercase), matching the spec's raw input schema and `contracts/dataset.schema.yaml`:
   - Detect presence of the `MMSE` column.
   - If present, set flag `has_mmse`.
   - Exclude participants with `MMSE` < 24.
   - If absent, skip exclusion and log `"MMSE_COLUMN_MISSING"` in `exclusion_log.json`.
4. **Stimulus Integrity** (`VI. Stimulus Fidelity`): Verify file checksum matches recorded value; abort on mismatch.

## Schema Representation
The logical schema is captured in JSON-Schema files under `contracts/`:

- `contracts/dataset.schema.yaml` – validates the cleaned dataset rows (field names: `participant_id`, `age`, `stimulus_type`, `perseverative_errors`, `categories_completed`, optional `MMSE`, `education_years`, `gender`).
- `contracts/output.schema.yaml` – validates the statistical output JSON.

These schemas are enforced by the test suite (`tests/contract/validate_output.py`).