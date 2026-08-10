# Data Model: Statistical Discrepancies in Publicly Available Election Data

## Overview

This document defines the data schemas for the election discrepancy analysis pipeline. The model ensures that all data transformations are traceable and that the statistical tests operate on validated inputs.

## Entity Definitions

### Jurisdiction
A geographic unit (precinct or county) with vote counts.
- `jurisdiction_id`: Unique string identifier (e.g., "county_precinct").
- `state_fips`: String (5 digits).
- `county_fips`: String (3 digits).
- `county_name`: String.
- `precinct_id`: String.
- `vote_count`: Integer (non-negative).
- `precinct_sum`: Integer (sum of votes in this precinct, if aggregated).
- `election_year`: Integer (for temporal alignment validation).

### Discrepancy Record
The calculated difference between aggregated precinct sums and reported county totals.
- `county_id`: String (composite key).
- `county_reported`: Integer (reported total votes).
- `precinct_sum`: Integer (sum of precinct-level votes).
- `discrepancy_abs`: Integer (`|precinct_sum - county_reported|`).
- `discrepancy_pct`: Float (`discrepancy_abs / county_reported`).
- `flag_missing`: Boolean (true if data was imputed or missing).
- `flag_directional`: Boolean (true if precinct_sum > county_reported).
- `anomaly_p_value`: Float (p-value against null distribution; NaN if not calculated).

### Predictor Variables (Optional for Extended Analysis)
- `population_density`: Float.
- `precinct_size`: Integer.
- `voter_turnout_pct`: Float.

## Schema Validation

The pipeline enforces the following constraints before statistical analysis:
1.  **Non-Negative Counts**: All vote counts must be $\ge 0$.
2.  **Non-Zero Denominator**: `county_reported` must be $> 0$ for relative discrepancy calculation.
3.  **Key Alignment**: `precinct_id` and `county_name` must exist in both the source and target tables.
4.  **Temporal Alignment**: `election_year` in the dataset must match the expected election cycle (e.g., 2020, 2024) to ensure precinct boundaries are valid.

## Primary Threshold Definition

-   **Primary Threshold**: `0.5%` (0.005) is the fixed reference point for the primary measurement (SC-001).
- **Sensitivity Thresholds**: `{0.01%, 0.05%, 0.1%, [deferred]}` are used for the sensitivity sweep (FR-005).

## Collinearity & Predictor Diagnostics

-   If predictor variables are used in regression analysis:
    -   **VIF Threshold**: Variance Inflation Factor (VIF) > 5 indicates significant collinearity.
    -   **Action**: If VIF > 5, report collinearity and describe relationships descriptively. Do not claim independent effects.
-   If no regression is performed, this section is skipped.

## Data Flow

1.  **Raw Input**: CSV/Parquet from verified sources OR Synthetic Data Generator.
2.  **Normalization**: Unified schema (Jurisdiction).
3.  **Temporal Validation**: Check `election_year` alignment.
4.  **Aggregation**: Precincts summed to County level.
5.  **Discrepancy Calculation**: Join with reported totals; compute differences.
6.  **Filtering**: Remove records with zero reported votes; flag missing data.
7.  **Statistical Input**: `discrepancy_pct` and `discrepancy_abs` arrays.
8.  **Anomaly Scoring**: Calculate p-values for each jurisdiction against the null distribution.