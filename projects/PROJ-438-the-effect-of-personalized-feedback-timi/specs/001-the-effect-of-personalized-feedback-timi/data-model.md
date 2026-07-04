# Data Model: The Effect of Personalized Feedback Timing on Skill Acquisition

## Overview
This document defines the schema for the data pipeline, including the raw input, intermediate processed data, and final analysis output. All data is stored in CSV format (for interoperability) or JSON (for raw input) within the `data/` directory.

## Entity Definitions

### 1. Learner (Core Entity)
Represents an individual student's participation in a course.
- **student_id**: Unique identifier for the learner.
- **course_id**: Unique identifier for the course.
- **submission_timestamp**: UTC timestamp of learner submission.
- **response_proxy_timestamp**: UTC timestamp of system/instructor response (or forum reply proxy).
- **interval_hours**: Calculated time difference (response - submission) in hours.
- **feedback_group**: Categorical assignment (Immediate, Delayed, Variable).
- **final_grade**: Numeric score (0-100).
- **is_complete**: Boolean (1=completed, 0=incomplete).
- **missing_response_flag**: Boolean (1 if `response_proxy_timestamp` was null).
- **engagement_count**: Total number of submissions/forum posts (covariate).

### 2. Course (Context Entity)
Represents a course offering.
- **course_id**: Unique identifier.
- **has_assessment**: Boolean.
- **has_forum**: Boolean.
- **learner_count**: Number of learners in the course.
- **exclusion_reason**: String (e.g., "insufficient_learners", "missing_events").

### 3. Analysis Result (Output Entity)
Aggregated statistical findings.
- **comparison_pair**: String (e.g., "Immediate vs Delayed").
- **mean_diff**: Difference in means.
- **cohen_d**: Effect size.
- **p_value**: Raw p-value.
- **p_adjusted**: Tukey-adjusted p-value.
- **significant**: Boolean.
- **model_type**: String (e.g., "Clustered OLS").

## Data Flow

1.  **Raw Input**: `data/raw/oulad.json` (Downloaded from verified URL).
2.  **Intermediate 1**: `data/processed/courses_filtered.csv` (Courses with assessment/forum events).
3.  **Intermediate 2**: `data/processed/learner_intervals.csv` (Calculated intervals, binned groups, engagement counts).
4.  **Output**: `data/processed/ols_results.csv` (Model estimates, p-values).
5.  **Output**: `data/processed/sensitivity_results.csv` (Boundary sweep results).

## Data Hygiene Rules
- **Checksums**: All files in `data/` must have a corresponding SHA256 hash in `data/checksums.txt`.
- **Immutability**: `data/raw/` files are never modified. `data/processed/` files are overwritten only if the source changes.
- **PII**: No personal identifiers (names, emails) are stored. `student_id` is an anonymized hash.
- **Timezone**: All timestamps stored in UTC.