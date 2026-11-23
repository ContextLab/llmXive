# Data Model: Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data

## Overview

This document defines the data structures, schemas, and relationships used in the WEP validity project. It ensures the "Single Source of Truth" (Constitution IV) by strictly defining how raw data flows into derived artifacts.

## Entities & Relationships

### 1. PlanetaryOrbit (Raw & Derived)
Represents the trajectory of a planet or moon.
*   **Source**: JPL Horizons (Range/Range-Rate).
*   **Derived**: GR Baseline, Residuals.
*   **Attributes**: `timestamp`, `body_id`, `range_km`, `range_rate_km_s`, `uncertainty_range`, `uncertainty_rate`.

### 2. INPOPReference
Represents the cross-validation data from INPOP19a.
*   **Source**: INPOP19a Ephemeris.
*   **Attributes**: `timestamp`, `body_id`, `range_km_inpop`, `range_rate_km_s_inpop`.
*   **Relationship**: One-to-One with `PlanetaryOrbit` (for the same epoch and body).

### 3. GravitationalBindingEnergy
Static attribute for each planet/moon.
*   **Source**: Peer-reviewed interior structure models (e.g., Seager et al., 2007).
*   **Attributes**: `body_id`, `mass_kg`, `radius_m`, `omega_fraction` (calculated with interior corrections).

### 4. DifferentialResidual
Represents the difference between JPL and INPOP ephemerides.
*   **Source**: `analysis/differential.py`.
*   **Attributes**: `timestamp`, `body_id`, `diff_range_km`, `diff_range_rate_km_s`.
*   **Relationship**: Derived from `PlanetaryOrbit` and `INPOPReference`.

### 5. RegressionResult
Output of the statistical analysis.
*   **Source**: `analysis/regression.py`.
*   **Attributes**: `slope`, `intercept`, `p_value`, `std_err`, `r_squared`, `confidence_interval_95`.

### 6. MonteCarloDistribution
Null distribution of parameters.
*   **Source**: `analysis/monte_carlo.py`.
*   **Attributes**: `parameter_name`, `mean`, `std_dev`, `percentile_2_5`, `percentile_97_5`, `p_value`.

## File Structure & Formats

All data files are stored in `projects/PROJ-348/data/`.

### Raw Data (Immutable)
*   `raw/jpl_horizons_mercury.csv` (Checksummed)
*   `raw/jpl_horizons_venus.csv`
*   `raw/jpl_horizons_earth.csv`
*   `raw/jpl_horizons_mars.csv`
*   `raw/jpl_horizons_moon.csv`
*   `raw/inpop19a_data.csv` (if downloaded)

### Derived Data (Generated)
*   `derived/gr_baseline_mercury.csv`: Output from `rebound` integration.
*   `derived/differential_residuals.csv`: Merged JPL vs INPOP.
*   `derived/binding_energy.csv`: Static $\Omega$ values.
*   `results/regression_stats.json`: Final OLS results.
*   `results/mc_distribution.json`: Monte Carlo histograms.

## Data Processing Pipeline

1.  **Ingestion**: `download_jpl.py` fetches raw CSVs. Validates checksums.
2.  **Baseline Generation**: `integrator.py` reads planetary masses/positions, runs `rebound`, outputs `gr_baseline_*.csv`.
3.  **INPOP Fetch**: `download_inpop.py` fetches INPOP data.
4.  **Differential Calculation**: `validators.py` computes `diff = jpl - inpop` for each epoch.
5.  **Static Join**: `binding_energy.py` joins $\Omega$ data to the differential residuals table.
6.  **Fitting**: `regression.py` performs OLS on the differential signal, outputs `regression_stats.json`.
7.  **Simulation**: `monte_carlo.py` bootstraps residuals, outputs `mc_distribution.json`.

## Constraints & Validation

*   **Timestamps**: All timestamps must be in UTC (ISO 8601).
*   **Units**: Distances in km, velocities in km/s, time in seconds (Julian Date for integration).
*   **Missing Values**: Any row with `NaN` in `range` or `range_rate` must be excluded before regression.
*   **Outliers**: Residuals > 5$\sigma$ from the mean are flagged but not automatically removed (to preserve signal integrity), unless they are clearly data errors.
*   **Minimum Sample**: Regression halts if fewer than 3 bodies have valid $\Omega$ data.
