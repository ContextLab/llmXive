# Data Model: Assessing the Validity of Modified Newtonian Dynamics with Galaxy Rotation Curves

## Overview

This document defines the data structures, transformations, and schemas used throughout the project. All data flows from raw SPARC downloads through filtering, model fitting, and statistical analysis. Each artifact is checksummed and versioned per the project constitution.

## Entity Definitions

### GalaxyRotationCurve

Represents a single galaxy's kinematic data.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `galaxy_id` | str | Unique identifier (e.g., "UGC001") | SPARC raw file |
| `radial_distances` | list[float] | Radial distances in kpc | SPARC raw file |
| `rotational_velocities` | list[float] | Rotational velocities in km/s | SPARC raw file |
| `velocity_uncertainties` | list[float] | Velocity uncertainties in km/s | SPARC raw file |
| `inclination` | float | Inclination angle in degrees | SPARC raw file |
| `inclination_uncertainty` | float | Inclination uncertainty in degrees | SPARC raw file |
| `baryonic_mass_distribution` | dict | Stellar and gas surface densities | SPARC raw file |

### ModelFit

Represents a fitted model result.

| Attribute | Type | Description |
|-----------|------|-------------|
| `galaxy_id` | str | Unique identifier |
| `model_type` | str | "MOND" or "NFW" |
| `fitted_parameters` | dict | Fitted parameters (e.g., {"M/L": 0.5} for MOND; {"c": 10.5, "r_s": 5.2} for NFW) |
| `reduced_chi_squared` | float | Reduced χ² value |
| `AIC` | float | Akaike Information Criterion |
| `BIC` | float | Bayesian Information Criterion |
| `residual_statistics` | dict | {"mean": x, "median": y, "std": z, "ks_statistic": z} |

### GoodnessOfFitMetric

Represents a computed fit quality metric.

| Attribute | Type | Description |
|-----------|------|-------------|
| `metric_name` | str | e.g., "reduced_chi_squared", "AIC", "KS_test" |
| `metric_value` | float | Computed value |
| `degrees_of_freedom` | int | N - k (N = data points, k = parameters) |
| `reference_value` | float | Threshold for pass/fail (e.g., 1.5 for χ²) |

## Data Flow

```mermaid
graph TD
    A[SPARC Raw Data] -->|download.py| B[Raw Files in data/raw/sparc/]
    B -->|preprocess.py| C[Filtered Galaxies (inclination <10°, ≥15 points)]
    C -->|fit.py| D[ModelFit Results]
    D -->|metrics.py| E[GoodnessOfFitMetric Summary]
    E -->|residuals.py| F[Residual Statistics & Parametric Bootstrap]
    F -->|sensitivity.py| G[Sensitivity Analysis Report]
```

## Transformation Rules

### Filtering (FR-003)

- **Inclination uncertainty**: Exclude if `inclination_uncertainty >= 10.0`
- **Point count**: Exclude if `len(radial_distances) < 15`
- **Malformed files**: Exclude if missing required columns (`radial_distances`, `rotational_velocities`, `velocity_uncertainties`)

### Model Fitting (FR-006)

- **Weighting**: `sigma = velocity_uncertainties` passed to `scipy.optimize.curve_fit`
- **Priors**: NFW concentration prior applied via `bounds` and `sigma` in `curve_fit` (independent of baryonic mass)
- **Convergence**: Max 1000 iterations; fallback to grid search if `curve_fit` fails

### Residual Analysis (FR-009)

- **Parametric Bootstrap**: Synthetic datasets generated under a combined null model with Gaussian noise. Resampling is not performed on observed residuals; instead, new residuals are generated from the null distribution.
- **Iterations**: [deferred] (or [deferred] if runtime >4 hours)
- **Statistic**: Kolmogorov-Smirnov (KS) distance between standardized residual distributions
- **Correction**: Holm-Bonferroni applied to p-values

## Schema Contracts

See `contracts/` directory for formal YAML schemas:
- `dataset.schema.yaml`: Validates filtered galaxy data
- `fit_results.schema.yaml`: Validates model fit outputs

## Checksums and Versioning

- **Raw data**: `sha256` checksum recorded in `data/metadata.yaml`
- **Filtered data**: `sha256` checksum recorded in `data/metadata.yaml`
- **Results**: `sha256` checksum recorded in `state/...yaml`

## Error Handling

| Error Type | Handling |
|------------|----------|
| Missing columns | Log warning; exclude galaxy |
| Convergence failure | Log error; fallback to grid search; if still fails, exclude galaxy |
| HTTP error (download) | Retry 3 times; flag as unavailable; continue with other galaxies |
| Degenerate fit | Log warning; report as "inconclusive"; exclude from final comparison |