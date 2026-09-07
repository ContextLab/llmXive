# Data Model: Testing the Equivalence Principle with Satellite Laser Ranging

## Key Entities

### NormalPoint
Represents a single SLR observation.
*   `timestamp`: `datetime64[ns]` (UTC)
*   `range`: `float64` (meters)
*   `satellite_id`: `string` (e.g., "LAGEOS-1")
*   `station_id`: `string` (e.g., "7110")
*   `quality_flag`: `int` (0=good, 1=outlier, etc.)
*   `residual`: `float64` (meters) - post-fit residual
*   `mass`: `float64` (kg) - from `satellite_constants.yaml`
*   `composition`: `string` - from `satellite_constants.yaml`

### OrbitSolution
Represents the result of the dynamical model fit.
*   `satellite_id`: `string`
*   `orbital_elements`: `dict` (semi-major axis, eccentricity, inclination, etc.)
*   `non_gravitational_acceleration`: `dict` (drag coefficient, SRP coefficient)
*   `differential_acceleration`: `float64` ($a_c$) - from joint fit
*   `covariance_matrix`: `array` (covariance of estimated parameters)
*   `chi_squared`: `float64`
*   `residuals`: `array` (post-fit residuals)
*   `correlation_coefficient`: `float64` ($\rho$) - estimated shared error term

### EotvosResult
Represents the final test outcome.
*   `eta`: `float64` (Eötvös parameter)
*   `eta_std`: `float64` (Standard error)
*   `confidence_interval_95`: `tuple` (lower, upper)
*   `p_value`: `float64` (Holm-Bonferroni corrected)
*   `chi2_improvement`: `float64` ($\chi^2_{null} - \chi^2_{alt}$)
*   `sensitivity_sweep`: `list` (Z-scores per geopotential model)
*   `systematic_error_sweep`: `list` (Z-scores per systematic model)
*   `benchmark_comparison`: `dict` (target precision vs achieved, source citation)
*   `simulation_validation`: `dict` (injected vs estimated $\eta$, 2-sigma check)
*   `consistency_check`: `dict` (joint vs separate estimate, 2-sigma check)

## Data Flow

1.  **Ingestion**: Raw SLR data (Parquet) $\rightarrow$ `data/raw/`
2.  **Metadata Merge**: Merge with `satellite_constants.yaml` (mass, composition) $\rightarrow$ `data/processed/cleaned_slr_data.csv`
3.  **Preprocessing**: Filtering (quality < 2cm), outlier removal, bias correction $\rightarrow$ `data/processed/cleaned_slr_data.csv`
4.  **Estimation**: Cleaned data + Dynamical Model + Shared Error Term $\rightarrow$ `OrbitSolution` (in memory)
5.  **Analysis**: `OrbitSolution` $\rightarrow$ `EotvosResult`
6.  **Output**: `EotvosResult` $\rightarrow$ Diagnostic Report (JSON/CSV)

## Assumptions & Constraints
*   **Missing Data**: If a required satellite is missing from the verified dataset, the `EotvosResult` will be marked as `incomplete` with a specific error code.
*   **Collinearity**: The model assumes that the differential acceleration parameter is orthogonal to the standard drag/SRP parameters within the joint estimation space, aided by the shared error term.
*   **Reference 'g'**: The 'g' in $\eta$ is derived from a standard geopotential model (EGM2008), not the estimated parameters.