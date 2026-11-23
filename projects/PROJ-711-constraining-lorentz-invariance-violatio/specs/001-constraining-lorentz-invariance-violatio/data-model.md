# Data Model: Constraining Lorentz Invariance Violation with Fermi Gamma‑Ray Burst Spectra

## Overview

This document defines the data structures used throughout the pipeline. All data is stored in local files (CSV, JSON, HDF5) and validated against the schemas defined in `contracts/`.

## Entity Definitions

### 1. GRBEvent
Represents a single Gamma-Ray Burst.
*   `grb_id`: Unique identifier (e.g., "090510", "GRB090510").
*   `trigger_time`: ISO 8601 timestamp of the trigger.
*   `redshift`: Float (optional). If null, the burst is excluded from LIV regression.
*   `fluence`: Float (erg/cm²). Used for ranking.
*   `fluence_rank`: Integer (1-30).
*   `sky_position`: Dictionary with `ra` and `dec`.

### 2. LightCurve
Represents the time-series data for a specific energy band.
*   `grb_id`: Foreign key to `GRBEvent`.
*   `energy_band`: String (e.g., "8-50", "50-200", "200-1000").
*   `time_bins`: List of floats (start time of each bin).
*   `photon_counts`: List of integers (observed counts).
*   `background_counts`: List of integers (estimated background).
*   `net_counts`: List of integers (photon_counts - background_counts, clipped to 0).
*   `excluded`: Boolean. True if net_counts < 0 in > 5% of bins (per Spec US-1).

### 3. SpectralLag
Represents the measured time delay.
*   `grb_id`: Foreign key.
*   `low_band`: String (e.g., "8-50").
*   `high_band`: String (e.g., "200-1000").
*   `lag_ms`: Float (time delay in milliseconds).
*   `uncertainty_ms`: Float (95% CI width or standard error).
*   `ccf_peak_position`: Float (bin index of peak).
*   `bootstrap_samples`: Integer (number of resamples used).
*   `valid`: Boolean. False if CCF peak is ambiguous or signal-to-noise is too low.

### 4. LIVConstraint
Represents the derived physical limit.
*   `grb_id`: Foreign key (or "global" for aggregate).
*   `energy_scale_gev`: Float (Upper bound on $E_{\rm QG}$ in GeV).
*   `confidence_level`: Float (e.g., 0.95).
*   `method`: String (e.g., "hierarchical_bayesian", "null_test").
*   `null_consistency`: Boolean. True if the result is consistent with the null distribution.

## Data Flow

1.  **Raw**: `data/raw/grb_XXX_lightcurve.fits` (Downloaded from FSSC).
2.  **Processed**: `data/processed/grb_XXX_lightcurve.csv` (Re-binned, background subtracted).
3.  **Lag**: `data/processed/grb_XXX_lag.csv` (CCF results).
4.  **Constraints**: `results/grb_XXX_constraint.json` (Individual $E_{\rm QG}$).
5.  **Aggregate**: `results/global_constraint.json` (Population limit).

## Storage Strategy

*   **Raw Data**: Preserved as-is. Checksums recorded.
*   **Processed Data**: CSV format for portability and inspection.
*   **Intermediate Results**: JSON for structured metadata.
* **Large Arrays**: HDF5 (if needed for [deferred] null samples) to avoid memory bloat.