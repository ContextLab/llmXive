# Data Model: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

## Overview
Defines the entities that store participant identifiers, cognitive/affective measurements, and daily compliance logs. Supports a within‑subject design with two phases: `baseline` and `post`.

## Entities

### 1. Participant
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `participant_id` | string | Pseudonymous ID (e.g., `P001`) | Primary key, pattern `^P\\d{3}$` |
| `demographics` | object | Optional age, gender, etc. | Nullable |
| `enrollment_date` | string | ISO‑8601 date | Required |

### 2. MeasurementRecord
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | string | Unique record ID | Primary key |
| `participant_id` | string | FK → Participant | Required |
| `phase` | string | `baseline` or `post` | Enum |
| `metric_type` | string | `SART`, `Ospan`, `PSS-10`, `PANAS-PA`, `PANAS-NA` | Enum |
| `value` | float | Raw score | Required |
| `timestamp` | string | ISO‑8601 datetime | Required |
| `quality_flag` | string | `valid`, `low_attention`, `missing` | Default `valid` |

### 3. ComplianceLog
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | string | Unique log ID | Primary key |
| `participant_id` | string | FK → Participant | Required |
| `date` | string | ISO‑8601 date (YYYY‑MM‑DD) | Required |
| `social_media_minutes` | integer | Self‑reported minutes of social media use | 0 ≤ ≤ 1440 |
| `news_consumption` | boolean | `true` if news was consumed | Required |
| `notifications_off` | boolean | `true` if notifications were off | Required |
| `is_compliant` | boolean | Derived: `social_media_minutes` ≤ 30 && !`news_consumption` && `notifications_off` | Derived |
| `notes` | string | Optional free‑text | Optional |

## Data Flow
1. **Ingestion** – Raw JSON/CSV files deposited by participants land in `data/raw/`.  
2. **Validation** – `code/validation/` checks ranges, schema conformity, and generates `data/checksums.sha256`.  
3. **Processing** – Scoring functions produce `data/processed/measurement_records.csv` and `data/processed/compliance_summary.csv`.  
4. **Analysis** – `code/analysis/` consumes processed CSVs, outputs `results/statistical_summary.json`.  
5. **Visualization** – `code/viz/` reads the JSON summary to create plots in `results/plots/`.

## File Formats
- **Raw**: JSON lines or CSV (one file per participant).  
- **Processed**: Long‑format CSV (one row per measurement).  
- **Compliance**: CSV (one row per participant per day).  
- **Checksums**: SHA‑256 digests, one line per file (`<hash>  <relative_path>`).
