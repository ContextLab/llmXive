# Data Model: The Effect of Personalized Feedback Timing on Skill Acquisition

## Overview
This document defines the data structures used throughout the analysis pipeline, from raw ingestion to final results. All timestamps are stored in UTC.

**Critical Note on Variables**: The `response_timestamp` field is defined as the timestamp of the **next student event** (forum post or assessment result) following submission, as OULAD lacks instructor feedback timestamps. This is a proxy for "feedback engagement," not "instructor feedback timing."

## Entity: Learner Record
The core unit of analysis is a single learner's aggregated performance in a specific course.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `student_id` | string | Unique student identifier. | `students_data.csv` |
| `course_id` | string | Unique course identifier. | `students_data.csv` |
| `final_grade` | float | Final course grade (0-100 or 0-1). | `students_data.csv` |
| `is_complete` | boolean | Whether the student completed the course. | `students_data.csv` |
| `submission_timestamp` | datetime | Timestamp of assessment submission. | Events Parquet |
| `response_timestamp` | datetime | Timestamp of the **next student event** (proxy for feedback). | Derived (Events Parquet) |
| `proxy_source` | string | "next_forum" or "next_assessment" indicating the event type used. | Derived |
| `feedback_interval` | float | Time delta (hours) between submission and response. | Derived |
| `feedback_group` | string | Binned category: "Immediate", "Delayed", "Variable". | Derived (based on median interval) |
| `num_past_attempts` | int | Number of past attempts (if available). | Events Parquet |
| `total_forum_posts` | int | Total forum posts by student (engagement control). | Events Parquet |
| `total_clicks` | int | Total clicks by student (engagement control). | Events Parquet |

## Entity: Sensitivity Result
Intermediate results from the bin boundary sweep.

| Field | Type | Description |
| :--- | :--- | :--- |
| `boundary_1` | float | Lower bound of "Immediate" (in hours). |
| `boundary_2` | float | Upper bound of "Delayed" (in hours). |
| `p_value` | float | P-value from OLS for the primary comparison. |
| `effect_size` | float | Cohen's d for the primary comparison. |
| `significant` | boolean | Whether p < 0.05. |

## Data Flow

1. **Raw**: `data/raw/students_data.csv`, `data/raw/events_train.parquet`
2. **Processed (Raw)**: `data/processed/learners_raw.csv` (Joined, filtered, cleaned; logs exclusions)
3. **Processed (Binned)**: `data/processed/learners_binned.csv` (Includes `feedback_group`, `proxy_source`)
4. **Results**: `data/processed/results_metrics.csv` (Model outputs, effect sizes)
5. **Sensitivity**: `data/processed/significance_stability_report.csv` (Sweep results)

## Constraints

- **Missing Data**: Records with missing `final_grade` or missing timestamp pairs are excluded. The count of excluded records is logged.
- **Timezone**: All timestamps converted to UTC before interval calculation.
- **Precision**: `feedback_interval` calculated to 0.1h precision.
- **Proxy**: `response_timestamp` is optional in the schema (nullable) but populated for all valid records in the pipeline. `proxy_source` documents the derivation.
