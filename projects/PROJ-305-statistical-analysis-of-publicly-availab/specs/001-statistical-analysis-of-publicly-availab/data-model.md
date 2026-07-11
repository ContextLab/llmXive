# Data Model: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Overview

This document defines the data structures used throughout the pipeline, from raw ingestion to final signal reporting. It ensures alignment with the spec's requirements for filtering, mapping, and statistical analysis.

## Entities

### Report
A single adverse event entry.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `VAERS_ID` | int | Unique identifier | Raw VAERS |
| `VAX_TYPE` | str | Vaccine type (e.g., "COVID-19", "Influenza", "Tetanus") | Raw VAERS |
| `SOC_CODE` | str | MedDRA System Organ Class code (e.g., "100000004880") | Raw VAERS (mapped from `SOC` or `LLT` if available) |
| `SOC_NAME` | str | Human-readable SOC name | MedDRA mapping |
| `REPT_DATE` | date | Date of report | Raw VAERS |
| `AGE` | float | Age of patient (years) | Raw VAERS |
| `SEX` | str | Gender | Raw VAERS |
| `VAX_DATE` | date | Vaccination date (often missing) | Raw VAERS |
| `EVENT_DATE` | date | Date of adverse event | Raw VAERS |
| `OUTCOME` | str | Outcome of event | Raw VAERS |

### Signal
A statistically significant disproportionality result for a specific SOC.

| Field | Type | Description |
|-------|------|-------------|
| `SOC_CODE` | str | MedDRA SOC code |
| `SOC_NAME` | str | Human-readable SOC name |
| `ROR` | float | Reporting Odds Ratio |
| `ROR_CI_lower` | float | Lower bound of 95% CI for ROR |
| `ROR_CI_upper` | float | Upper bound of 95% CI for ROR |
| `PRR` | float | Proportional Reporting Ratio |
| `PRR_CI_lower` | float | Lower bound of 95% CI for PRR |
| `PRR_CI_upper` | float | Upper bound of 95% CI for PRR |
| `IC` | float | Information Component |
| `IC_CI_lower` | float | Lower bound of 95% CI for IC |
| `IC_CI_upper` | float | Upper bound of 95% CI for IC |
| `p_value_raw` | float | Raw p-value (before BH correction) |
| `p_value_adj` | float | BH-adjusted p-value |
| `is_signal` | bool | True if meets 2/3 metric thresholds |
| `signal_metrics` | list | List of metrics that met thresholds (e.g., ["ROR", "PRR"]) |

### TemporalProfile
Weekly reporting counts for a specific SOC.

| Field | Type | Description |
|-------|------|-------------|
| `SOC_CODE` | str | MedDRA SOC code |
| `week_offset` | int | Weeks relative to median report date |
| `count_covid` | int | Number of reports in COVID-19 group |
| `count_non_covid` | int | Number of reports in Non-COVID group |
| `total_count` | int | Total reports |

## Data Flow

1. **Raw Data**: Downloaded from verified source (`chrisvoncsefalvay/vaers-outcomes` or similar).
2. **Cleaned Data**: Filtered by `VAX_TYPE` (COVID-19 vs. **Non-COVID, Non-Flu**), MedDRA mapped to SOC, missing values handled.
3. **Contingency Tables**: Generated for each SOC (Event/No Event vs. COVID/Non-COVID).
4. **Signal Calculation**: ROR, PRR, IC computed; BH correction applied.
5. **Temporal Analysis**: Weekly counts aggregated for top 5 signals.
6. **Sensitivity Analysis**: Flu-only baseline comparison.

## Constraints

- **Memory**: All DataFrames must fit within 7 GB RAM. If not, chunked processing is required.
- **Date Format**: `REPT_DATE` must be parsed as `YYYY-MM-DD`.
- **SOC Mapping**: MedDRA codes must be mapped to SOC using a verified MedDRA-to-SOC mapping table (included in `data/` or generated).
- **Zero Counts**: Continuity correction (0.5) applied if any cell in contingency table is zero.
- **Schema Validation**: The `src/data/validate.py` script must enforce `contracts/dataset.schema.yaml` before processing.