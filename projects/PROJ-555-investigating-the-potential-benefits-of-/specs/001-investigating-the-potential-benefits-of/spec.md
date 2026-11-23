# Project Specification: Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas

## Overview
This project investigates the correlation between ecotourism activities and the regeneration rates of deforested areas using satellite imagery (Landsat) and economic data.

## User Stories

### US1: Data Acquisition and Preprocessing
Ingest, clean, and align Landsat satellite imagery time series with ecotourism site metadata for the defined study period.

### US2: Deforestation Detection and Recovery Trajectory Modeling
Automatically detect deforestation events and calculate recovery trajectories using non-linear asymptotic models.

### US3: Statistical Inference and Sensitivity Analysis
Fit linear mixed-effects models to test ecotourism association with regeneration, control for covariates, and perform sensitivity analysis.

## Functional Requirements

### FR-001: Data Sources
- Landsat Level 2 Surface Reflectance (USGS)
- World Database of Protected Areas (WDPA)
- CHIRPS Precipitation Data (NOAA)
- MODIS Land Surface Temperature (NASA POWER)

### FR-002: Deforestation Detection
Detect deforestation events as NDVI drops ≥ 0.30 sustained over a period.
*Note: If non-linear asymptotic fitting fails (R² < 0.95), the linear slope fallback is the primary accepted metric for that site.*

### FR-003: Climate Covariates
Control for precipitation and temperature in the final regression model.

### FR-004: Sensitivity Analysis
Output a sensitivity report analyzing the impact of varying thresholds and proxy variables.

### FR-005: Statistical Correction
Apply Bonferroni or Holm correction to p-values to control for multiple comparisons.

### FR-006: Final Report
Generate a final JSON report containing regression coefficients, confidence intervals, sensitivity tables, and data quality flags.

### FR-007: Missing Data Handling
If revenue data is missing entirely for a site, substitute 'visitor count' as the proxy variable. Log all substitutions.

## Success Criteria

### SC-001: Site Processing Capacity
The system must successfully process up to 30 valid sites within the memory constraints (RAM < 7GB) without crashing or data loss.

### SC-002: Model Convergence
The mixed-effects model must converge for ≥ 90% of the test cases.

### SC-003: Data Quality
All output datasets must pass schema validation (Pydantic) and contain no null values in critical fields (site_id, year, ndvi).

## Constraints

- **Memory**: Peak RAM usage must not exceed 7GB.
- **Data**: Only real, programmatically accessible data sources are permitted. No synthetic data generation for inputs.
- **Dependencies**: Must run on standard CPU-only infrastructure.
- **Time**: Study period 2000-2023.