# Data Model: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

## Overview

This document defines the data structures used throughout the pipeline. All data is persisted in CSV or Parquet formats under `data/processed/`.

## Entity Definitions

### 1. PlanetRecord
Represents a single exoplanet observation from the Kepler DR25 catalog.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `planet_id` | string | Unique Kepler identifier (e.g., "Kepler-1234.01") | Unique, Non-null |
| `radius` | float | Planet radius in Earth radii ($R_{\oplus}$) | > 0 |
| `radius_uncertainty` | float | Uncertainty in radius ($R_{\oplus}$) | > 0 |
| `period` | float | Orbital period in days | > 0 |
| `period_uncertainty` | float | Uncertainty in period (days) | > 0 |
| `stellar_radius` | float | Stellar radius in Solar radii ($R_{\odot}$) | > 0 |
| `stellar_mass` | float | Stellar mass in Solar masses ($M_{\odot}$) | > 0 |
| `stellar_temp` | float | Stellar effective temperature (K) | > 0 |
| `confirmed` | boolean | Whether the planet is confirmed | True only |
| `completeness_weight` | float | Weight derived from detection efficiency model | [0, 1] |
| `log_period` | float | Log10 of the orbital period | |

**Filtering Rules**:
-   `radius_uncertainty / radius < 0.20`
-   `period_uncertainty / period < 0.01`
-   `stellar_temp` must not be null.

### 2. PeriodBin
Represents a binned group of planets for gap analysis.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `bin_id` | string | Unique bin identifier (e.g., "bin_0.85") | Unique |
| `bin_center_log_period` | float | Center of the log-period bin | |
| `weighted_mean_log_period` | float | Weighted mean of log(period) for planets in bin | |
| `bin_center_variance` | float | Variance of log(period) within the bin (X-axis error for EIV) | > 0 |
| `planet_count` | integer | Number of planets in the bin (after merging) | $\ge 0$ (flagged if <30) |
| `gap_location` | float | Estimated gap radius ($R_{\oplus}$) from GMM | NaN if unimodal |
| `gap_uncertainty` | float | 95% CI width for gap location (from bootstrap) | > 0 |
| `gap_location_variance` | float | Variance of the gap location (from bootstrap) | > 0 |
| `inverse_gap_variance` | float | Inverse variance of gap location (weight for regression) | > 0 |
| `is_unimodal` | boolean | Flag if BIC diff < 10 | |
| `bimodality_weight` | float | Weight for regression (0 if unimodal) | [0, 1] |
| `low_count` | boolean | Flag if planet_count < 30 | |
| `peak_separation` | float | Separation between GMM peaks | |
| `peak_separation_met` | boolean | True if separation $\ge 0.1 R_{\oplus}$ | |

### 3. GapAnalysisResult
The final output of the analysis.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `measured_slope` | float | Slope of $\log(R_{gap})$ vs $\log(P)$ | |
| `slope_uncertainty` | float | 95% CI for the slope | |
| `p_value_photoevaporation` | float | Monte Carlo p-value vs Owen & Wu model | [0, 1] |
| `p_value_core_powered` | float | Monte Carlo p-value vs Ginzburg et al. model | [0, 1] |
| `validation_status` | string | "PASS" if KDE gap within GMM CI, else "FAIL" | |
| `sensitivity_status` | string | "PASS" if synthetic test recovers ground truth | |

## File Artifacts

-   `data/raw/kepler_dr25.csv`: Raw download (immutable).
-   `data/raw/kic.csv`: Raw download (immutable).
-   `data/processed/filtered_planets.csv`: Output of `ingestion.py` (FR-001, FR-002).
-   `data/processed/binned_data.csv`: Output of `binning.py` (FR-003).
-   `data/processed/gap_results.csv`: Output of `gmm_analysis.py` (FR-004, FR-005).
-   `data/processed/final_analysis.json`: Output of `regression.py` (FR-006, FR-007).