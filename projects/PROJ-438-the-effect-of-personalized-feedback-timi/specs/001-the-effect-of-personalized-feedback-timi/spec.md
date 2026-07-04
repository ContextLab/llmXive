# Specification: The Effect of Personalized Feedback Timing on Skill Acquisition

## Overview
This document outlines the requirements for analyzing the effect of personalized feedback timing on skill acquisition using the Open University Learning Analytics Dataset (OULAD).

## Goals
- Determine if immediate feedback (<2h) leads to better skill acquisition than delayed feedback (2h-48h) or variable feedback (>48h).
- Quantify effect sizes and statistical significance.
- Ensure reproducibility and robustness of findings.

## User Stories

### US1: Download and Preprocess OULAD Data
As a researcher, I want to download the OULAD dataset and preprocess it to extract learner records with feedback timestamps, grades, and completion status, so that I can analyze the impact of feedback timing.

### US2: Calculate Feedback Timing Intervals
As a researcher, I want to calculate the time intervals between assessment submissions and feedback responses, and bin students into timing groups, so that I can categorize learners based on their feedback experience.

### US3: Fit Model and Perform Post-hoc Comparisons
As a researcher, I want to fit a Cluster-Robust OLS model and perform Tukey HSD post-hoc tests, so that I can determine the statistical significance of the differences between feedback timing groups.

## Functional Requirements

### FR-001: Data Acquisition
The system must download the OULAD dataset from https://analyse.kmi.open.ac.uk/open_dataset.

### FR-002: Data Preprocessing
The system must filter courses for those with "assessment" and "forum" events and extract learner records including `is_complete` status.

### FR-003: Interval Calculation
The system must calculate the time delta between submission and response in hours with at least 0.1h precision.

### FR-004: Binning Logic
The system must assign learners to "Immediate" (<2h), "Delayed" (2h–48h), or "Variable" (>48h) groups based on their median feedback interval.

### FR-005: Statistical Modeling
The system must fit a Cluster-Robust OLS model with feedback group as a fixed effect and clustering by course ID.

### FR-006: Post-hoc Testing
The system must perform Tukey HSD post-hoc pairwise comparisons to control family-wise error rate.

### FR-007: Sensitivity Analysis
The system must calculate "significance stability" (proportion of shifts where p < 0.05) and "significance flip rate" (proportion of shifts where the conclusion changes) by sweeping bin boundaries.

### FR-008: Proxy Validation
The system must validate the use of "final grade" as a proxy for "skill acquisition" using the automated **Reference-Validator Agent**.

## Non-Functional Requirements

### NFR-001: Reproducibility
All analysis must be reproducible with exact code and data versions.

### NFR-002: Performance
The pipeline must run on 2 CPU cores and ~7 GB RAM within 6 hours.

### NFR-003: Data Integrity
All analysis must use real OULAD data; no synthetic data generation for input metrics.

## Assumptions

1. **Data Availability**: The OULAD dataset is accessible and contains the necessary fields (submission timestamps, feedback timestamps, grades, completion status).
2. **Course Filtering**: Courses with fewer than 50 learners are excluded to ensure statistical power.
3. **Feedback Definition**: Feedback is defined as the response to an assessment submission, and the interval is calculated from submission to response.
4. **Proxy Validity**: The use of "final grade" as a proxy for "skill acquisition" is validated by the automated **Reference-Validator Agent** as per FR-008.
5. **Clustering**: Clustering by course ID accounts for course-level variations in teaching style and difficulty.
6. **Bin Boundaries**: The bin boundaries of 2h and 48h are reasonable and will be tested for sensitivity.

## Constraints

- **CPU Constraint**: No GPU/CUDA usage; models must run on 2 CPU cores.
- **Memory Constraint**: Peak memory usage must not exceed ~7 GB.
- **Time Constraint**: Full pipeline execution must complete within 6 hours.
- **Data Source**: Only real OULAD data is permitted; no synthetic data for input metrics.

## Dependencies

- Python 3.11+
- pandas, numpy, statsmodels, scipy, requests, tqdm, pyyaml
- pytest (for testing)

## Data Model

### Learner Record
- `student_id`: Unique identifier for the learner.
- `course_id`: Unique identifier for the course.
- `submission_timestamp`: Timestamp of the assessment submission.
- `response_timestamp`: Timestamp of the feedback response.
- `final_grade`: The final grade achieved by the learner.
- `is_complete`: Boolean indicating if the learner completed the course.
- `feedback_interval`: Calculated time delta between submission and response in hours.
- `feedback_group`: Binned category ("Immediate", "Delayed", "Variable").

## Success Criteria

- **US1**: `data/processed/learners_raw.csv` contains ≥10,000 records with required fields.
- **US2**: `data/processed/learners_binned.csv` contains interval and group columns.
- **US3**: `data/processed/results_metrics.csv` contains effect sizes, p-values, and sensitivity stats.
- **US3**: `data/processed/significance_stability_report.csv` documents stability metrics and flip rates.
- **FR-008**: Reference-Validator Agent confirms the validity of the "final grade" proxy.