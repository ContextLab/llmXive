# Data Model: Predicting Species‑Specific Responses to Climate Change from Museum Collection Data

## Overview

This document defines the data structures, file formats, and schemas used throughout the project. It ensures data hygiene (Principle III) and serves as the contract for the Implementer Agent.

## Data Flow

1.  **Raw Input**: GBIF JSON/CSV, WorldClim GeoTIFFs.
2.  **Processed**: Filtered occurrences, extracted climate values, centroids.
3.  **Results**: Regression statistics, sensitivity metrics, plots, power analysis report.

## Entity Definitions

### 1. OccurrenceRecord
Represents a single museum specimen record.
*   `species_name` (str): Scientific name.
*   `taxonomic_group` (str): e.g., "Plant", "Bird".
*   `latitude` (float): Decimal degrees.
*   `longitude` (float): Decimal degrees.
*   `collection_date` (str): ISO 8601 or parsed date.
*   `year` (int): Year of collection.
*   `uncertainty` (float): Coordinate uncertainty in meters.
*   `source_id` (str): GBIF key.

### 2. ClimateCentroid
Represents the mean climate conditions for a species in a specific period.
*   `species_name` (str)
*   `period` (str): "1970-2000" or "1991-2020".
*   `mean_temp_c` (float): Mean annual temperature.
*   `mean_prec_mm` (float): Mean annual precipitation.
*   `n_records` (int): Number of records used.
*   `region_band` (int): Latitudinal band (e.g., 30 for 30-40°N).
*   `static_envelope_id` (str): Identifier for the static historical envelope used for ΔT.

### 3. NicheShiftResult
Represents the calculated shift and associated metrics.
*   `species_name` (str)
*   `delta_n` (float): Euclidean distance in standardized space.
*   `delta_t` (float): Regional warming rate (°C).
*   `region_band` (int)
*   `sensitivity_mean` (float): Mean shift from subsampling.
*   `sensitivity_sd` (float): SD of shift from subsampling.
*   `variance_delta_n` (float): Variance of shift (used for WLS weights).
*   `is_flagged` (bool): True if `sensitivity_sd` >= 0.2.

### 4. PowerAnalysisResult
*   `n_species` (int): Number of species in the dataset.
*   `target_power` (float): Target power (e.g., 0.80).
*   `alpha` (float): Significance level (e.g., 0.05).
*   `effect_size` (float): Assumed effect size (slope).
*   `margin_of_error` (float): Calculated margin of error for the slope.
*   `is_adequate` (bool): True if margin_of_error <= 0.15.

## File Schema: `data/processed/centroids.csv`

| Column | Type | Description |
| :--- | :--- | :--- |
| species_name | string | Scientific name |
| period | string | "1970-2000" or "1991-2020" |
| mean_temp_c | float | Mean temperature |
| mean_prec_mm | float | Mean precipitation |
| n_records | integer | Count of records |
| region_band | integer | Latitudinal band |
| static_envelope_id | string | ID of the static historical envelope |

## File Schema: `results/regression_summary.csv`

| Column | Type | Description |
| :--- | :--- | :--- |
| region | string | "Global" or "Band-XX" |
| model_type | string | "PGLS" or "WLS" |
| slope | float | Regression slope |
| slope_ci_lower | float | 95% CI lower bound |
| slope_ci_upper | float | 95% CI upper bound |
| intercept | float | Regression intercept |
| r_squared | float | R² value |
| p_value | float | Two-tailed p-value |
| n_species | integer | Number of species in group |

## File Schema: `results/power_analysis_report.csv`

| Column | Type | Description |
| :--- | :--- | :--- |
| n_species | integer | Number of species |
| target_power | float | Target power |
| alpha | float | Significance level |
| effect_size | float | Assumed effect size |
| margin_of_error | float | Calculated margin of error |
| is_adequate | boolean | True if margin_of_error <= 0.15 |

## Logging

All operations write to `logs/pipeline.log`.
*   **Format**: ISO 8601 timestamp, log level, message.
*   **Content**: Query parameters, record counts, filtering reasons, error details.
*   **R Specific**: `sessionInfo()` output is appended to the log.