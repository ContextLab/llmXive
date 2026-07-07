# Data Model: The Impact of Digital Decluttering on Cognitive Performance and Well-being

## Overview

This document defines the data structures used to store participant information, cognitive/affective measurements, and compliance logs. The model supports a within-subjects design with two phases: `baseline` and `post`.

## Entities

### 1. Participant
Represents a study subject. PII is excluded; only a pseudonymous ID is used.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | string | Unique pseudonymous ID (e.g., `P001`) | Primary Key, Format: `P\d{3}` |
| `demographics` | object | Age, gender, etc. (optional) | Optional, JSON object |
| `enrollment_date` | string | ISO 8601 date | Required |

### 2. MeasurementRecord
Stores a single data point for a cognitive or affective metric.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique record ID | Primary Key |
| `participant_id` | string | FK to Participant | Required |
| `phase` | string | `baseline` or `post` | Required, Enum |
| `metric_type` | string | `SART`, `Ospan`, `PSS-10`, `PANAS-PA`, `PANAS-NA` | Required, Enum |
| `value` | float | Raw score | Required |
| `timestamp` | string | ISO 8601 datetime | Required |
| `quality_flag` | string | `valid`, `low_attention`, `missing` | Default: `valid` |

### 3. ComplianceLog
Stores daily adherence to the digital decluttering rules.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique log ID | Primary Key |
| `participant_id` | string | FK to Participant | Required |
| `date` | string | ISO 8601 date (YYYY-MM-DD) | Required |
| `social_media_minutes` | int | Self-reported minutes | 0 ≤ value ≤ 1440 |
| `news_consumption` | boolean | `true` if news consumed | Required |
| `notifications_off` | boolean | `true` if notifications off | Required |
| `is_compliant` | boolean | Derived: `min ≤ 30` AND `news=false` AND `notif=true` | Derived |
| `notes` | string | Optional user notes | Optional |

## Data Flow

1.  **Ingestion**: Raw data from web forms (SART/Ospan tasks, surveys, logs) is written to `data/raw/`.
2.  **Validation**: Scripts in `code/validation/` check ranges (e.g., SART RT 100-5000ms) and flag anomalies.
3.  **Processing**: Scores are calculated (e.g., PSS-10 sum, Ospan span) and written to `data/processed/`.
4.  **Analysis**: `data/processed/` is loaded into `pandas` DataFrames for statistical testing.

## File Formats

-   **Raw Data**: JSON or CSV (one file per participant or batch).
-   **Processed Data**: CSV (long format: one row per measurement).
-   **Compliance**: CSV (one row per day per participant).