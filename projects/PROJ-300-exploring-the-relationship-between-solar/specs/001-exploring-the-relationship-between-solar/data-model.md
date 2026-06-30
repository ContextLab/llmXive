# Data Model: Solar Wind and Magnetotail Reconnection Analysis

## Overview

This document defines the data structures, schemas, and transformations used in the analysis of solar wind speed (Vsw) and magnetotail reconnection rates (Ey). The data flow moves from raw ingestion to cleaned, resampled, and lag-adjusted datasets, culminating in statistical output schemas.

## Key Entities

### 1. SolarWindRecord
Represents a single measurement of solar wind conditions at the L1 point.
*   **timestamp**: `datetime` (UTC). The time of the measurement.
*   **vsw**: `float` (km/s). Solar wind speed.
*   **bz**: `float` (nT). Interplanetary magnetic field Bz component.
*   **source**: `str`. Identifier of the data source (e.g., "OMNIWeb").

### 2. MagnetotailRecord
Represents a single measurement of the magnetotail electric field.
*   **timestamp**: `datetime` (UTC). The time of the measurement.
*   **ey**: `float` (mV/m). Cross-tail electric field component.
*   **source**: `str`. Identifier of the data source (e.g., "THEMIS-EFI").

### 3. ProcessedRecord
A unified record after cleaning, resampling, and lag alignment.
*   **timestamp**: `datetime` (UTC). The common timestamp.
*   **vsw_lagged**: `float` (km/s). Vsw shifted by the optimal lag.
*   **ey**: `float` (mV/m). Ey at the current timestamp.
*   **lag_minutes**: `int`. The lag applied (0 if no lag).

## Data Flow & Transformation Rules

1.  **Ingestion**:
    *   Fetch raw data from OMNIWeb (Vsw, Bz) and CDAWeb (Ey).
    *   Parse timestamps to UTC.
    *   Store in `data/raw/` with checksums.
2.  **Cleaning**:
    *   Remove rows where `vsw` or `ey` is NaN.
    *   Filter out timestamps outside the user-specified range.
3.  **Resampling**:
    *   Resample both series to 5-minute intervals (`5T`).
    *   Aggregation function: `mean()`.
    *   Forward-fill or backward-fill only if gaps are < 5 minutes; otherwise, mark as NaN.
4.  **Lagging**:
    *   Shift `vsw` series forward by `L` minutes (where `L` is in [30, 90]).
    *   Create `vsw_lagged` column.
5.  **Alignment**:
    *   Inner join on `timestamp` to ensure only simultaneous observations are used.

## Output Schemas

### 1. CorrelationResult
*   `lag_minutes`: `int`
*   `pearson_r`: `float`
*   `spearman_r`: `float`
*   `p_value_permutation`: `float`
*   `ci_lower`: `float` (95% bootstrap lower bound)
*   `ci_upper`: `float` (95% bootstrap upper bound)

### 2. SensitivityResult
*   `threshold_kms`: `int` (400, 500, or 600)
*   `n_samples`: `int`
*   `pearson_r`: `float`

### 3. ReportSummary
*   `optimal_lag`: `int`
*   `l_phys`: `float`
*   `difference`: `float` (|L* - L_phys|)
*   `data_quality_warnings`: `list[str]`

## Constraints & Validations

*   **Timestamps**: Must be UTC.
*   **Units**: Vsw in km/s, Ey in mV/m, Bz in nT.
*   **Missing Data**: Gaps > 30 minutes must trigger a warning and exclusion of that segment.
*   **Autocorrelation**: The bootstrap and permutation methods are mandatory to handle temporal dependence.
