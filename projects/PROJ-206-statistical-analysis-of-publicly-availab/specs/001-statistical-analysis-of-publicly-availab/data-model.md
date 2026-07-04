# Data Model: Statistical Analysis of Publicly Available Election Poll Aggregates

## Overview

This document defines the data structures, schemas, and transformation logic used throughout the analysis pipeline. It ensures that all data artifacts are consistent, validated, and traceable to the source.

## Entity Definitions

### 1. PollRecord
Represents a single raw poll entry.
- **Attributes**:
  - `poll_id`: Unique identifier (hash of date + pollster + source).
  - `source`: "fivethirtyeight" (RCP is excluded from scope).
  - `date`: Date of the poll (ISO 8601).
  - `pollster`: Name of the polling organization.
  - `candidate_a_share`: Float (0-100).
  - `candidate_b_share`: Float (0-100).
  - `sample_size`: Integer.
  - `margin_of_error`: Float (optional).
  - `state`: String (optional, e.g., "US" for national).
  - `election_year`: Integer.

### 2. HarmonizedWeeklyRecord
Aggregated data for a specific week.
- **Attributes**:
  - `week_start`: ISO 8601 date (Monday).
  - `week_end`: ISO 8601 date (Sunday).
  - `election_year`: Integer.
  - `poll_count`: Integer.
  - `pollster_list`: List of strings.
  - `avg_vote_share`: Float (Simple average).
  - `weighted_vote_share`: Float (RMSE weighted).
  - `historical_rmse_median`: Float.

### 3. ForecastOutput
Result of an aggregation method.
- **Attributes**:
  - `method`: "simple", "weighted", "bayesian".
  - `week_start`: ISO 8601.
  - `point_estimate`: Float.
 - `lower_ci`: Float ([deferred] lower bound).
 - `upper_ci`: Float ([deferred] upper bound).
  - `actual_outcome`: Float (if available).
  - `error`: Float (Absolute difference).

## Data Flow

1. **Raw Ingestion**: Download CSVs from `https://projects.fivethirtyeight.com/polls/` and outcome data from MEDSL/538.
2. **Harmonization**: Convert dates to weekly bins, calculate weights (out-of-sample).
3. **Modeling**: Generate `ForecastOutput` for each method.
4. **Evaluation**: Compute RMSE, MAE, and Coverage.

## Validation Rules

- **Date Consistency**: All dates must be valid and within the range 2000-2024.
- **Vote Share**: Must be between 0 and 100.
- **Sample Size**: Must be > 0.
- **Weight Normalization**: Sum of weights for any week must be 1.0 (within tolerance 1e-6).
- **Source Constraint**: `source` field must be "fivethirtyeight".