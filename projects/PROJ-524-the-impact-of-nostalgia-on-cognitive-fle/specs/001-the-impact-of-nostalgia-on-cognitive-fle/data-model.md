# Data Model: Nostalgia Cognitive Flexibility Study

## Overview
The data model defines the entities required for the synthetic pipeline and aligns with the input schema in the specification. All tables are stored as CSV files; relationships are enforced by the cleaning scripts.

## Entities

### Participant
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `participant_id` | string | Unique identifier for participant | Primary key, non‑null, unique |
| `age` | integer | Age in years | Minimum 65, non‑null |
| `stimulus_type` | string | Assigned condition | Enum: `["nostalgia","control"]`, non‑null |
| `education_years` | number | Years of education (covariate) | Non‑null, ≥ 0 |
| `gender` | string | Gender (covariate) | Enum: `["female","male","other"]`, non‑null |
| `MMSE` | integer (optional) | Mini‑Mental State Examination score | 0 – 30; if present and `<24` → exclusion (FR‑006) |

### WCSTMetric
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `metric_id` | string | Unique identifier for the metric record | Primary key, non‑null |
| `participant_id` | string | Foreign key to `Participant.participant_id` | Non‑null, must match a participant |
| `perseverative_errors` | number | Number of perseverative errors on the WCST | Non‑null |
| `categories_completed` | number | Number of categories completed on the WCST | Non‑null |

### Stimulus
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `stimulus_id` | string | Unique identifier for the audio file | Primary key, non‑null |
| `stimulus_type` | string | Matches `Participant.stimulus_type` | Enum: `["nostalgia","control"]`, non‑null |
| `file_path` | string | Relative path under `data/stimuli/` | Non‑null |
| `checksum` | string | SHA‑256 hash of the file | Non‑null |

## Relationships
- **Participant ↔ Stimulus**: One‑to‑one via `stimulus_type`.  
- **Participant ↔ WCSTMetric**: One‑to‑many via `participant_id`; each participant has exactly one metric record in this study.

## Validation Rules (implemented in `code/cleaning.py`)
1. **Age Filter (FR‑001)** – Exclude rows where `age` < 65 or missing.  
2. **Missing WCST Metrics** – Exclude rows with null `perseverative_errors` or `categories_completed`.  
3. **MMSE Exclusion (FR‑006)** – If `MMSE` column exists, exclude participants with `MMSE` < 24; log `"MMSE_EXCLUDED"` in `exclusion_log.json`.  
4. **Stimulus Integrity (VI)** – Verify each stimulus file’s SHA‑256 matches `manifest.json`; abort on mismatch.  

## Schema Representation
The logical schema is captured in JSON‑Schema files under `contracts/`:

- `contracts/dataset.schema.yaml` – validates each row of the **cleaned participant** dataset (`participant_id`, `age`, `stimulus_type`, optional covariates, and `MMSE`).  
- `contracts/metrics.schema.yaml` – validates each row of `wcst_metrics.csv` (`metric_id`, `participant_id`, `perseverative_errors`, `categories_completed`).  
- `contracts/output.schema.yaml` – validates the JSON reports (`statistical_report.json`, `sensitivity_report.json`).  

These schemas are enforced by the test suite (`tests/contract/validate_output.py`).

---



