# Data Model: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Overview

This document defines the data structures and schemas used throughout the project. All data artifacts are stored in the `data/` directory, with raw data in `data/raw` and processed data in `data/processed`.

## Entity Definitions

### 1. Supernova Record
Represents a single Type Ia supernova after ingestion and residual calculation.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique identifier for the supernova (e.g., SN name). | Pantheon+ |
| `ra` | float | Right Ascension in degrees. | Pantheon+ |
| `dec` | float | Declination in degrees. | Pantheon+ |
| `z` | float | Redshift. | Pantheon+ |
| `mu_obs` | float | Observed distance modulus. | Pantheon+ |
| `mu_err` | float | Uncertainty in distance modulus. | Pantheon+ |
| `mu_th` | float | Theoretical distance modulus (model-independent spline fit). | Calculated |
| `residual` | float | $\mu_{obs} - \mu_{th}$. | Calculated |
| `valid` | bool | Flag indicating if the record passed all filters. | Filter Logic |

### 2. Healpix Pixel
Represents a spatial bin on the celestial sphere.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `pixel_index` | int | HEALPix pixel index (Nside=16). | HEALPix |
| `nside` | int | HEALPix resolution parameter (fixed at 16). | Constant |
| `mean_residual` | float | Mean residual of all SNe in this pixel. | Aggregation |
| `count` | int | Number of SNe in this pixel. | Aggregation |
| `mask_value` | int | 1 if pixel is valid, 0 if masked. | Mask Logic |

### 3. Harmonic Coefficient
Represents a term in the spherical harmonic expansion.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `ell` | int | Angular multipole moment ($\ell$). | Calculation |
| `m` | int | Azimuthal order ($m$). | Calculation |
| `real` | float | Real part of $a_{\ell m}$. | Calculation |
| `imag` | float | Imaginary part of $a_{\ell m}$. | Calculation |
| `amplitude` | float | $|a_{\ell m}|$. | Calculation |

### 4. Null Simulation Result
Represents one iteration of the isotropic mock catalog simulation.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `run_id` | int | Simulation iteration number (1 to [deferred]). | Loop Counter |
| `dipole_amp` | float | Extracted dipole amplitude for this run. | Calculation |
| `quadrupole_amp` | float | Extracted quadrupole amplitude for this run. | Calculation |

## File Formats

### `data/processed/residuals.csv`
Contains the filtered and processed supernova records.
- **Format**: CSV
- **Delimiter**: Comma
- **Header**: `id,ra,dec,z,mu_obs,mu_err,mu_th,residual,valid`

### `data/processed/healpix_map.fits`
Contains the HEALPix projection of residuals.
- **Format**: FITS (Flexible Image Transport System)
- **Columns**: `PIXEL`, `MEAN_RESIDUAL`, `COUNT`, `MASK_VALUE`

### `data/processed/simulation_results.csv`
Contains the results of the null distribution simulations.
- **Format**: CSV
- **Header**: `run_id,dipole_amp,quadrupole_amp`

## Data Flow

1. **Raw Data** (`data/raw/Pantheon+_SH0ES.dat`) → **Ingestion** → **Residuals** (`data/processed/residuals.csv`)
2. **Residuals** → **HEALPix Projection** → **Map** (`data/processed/healpix_map.fits`)
3. **Map** → **Spherical Harmonics** → **Coefficients** (Internal/In-memory)
4. **Residuals** → **Rotation Simulation** → **Null Distribution** (`data/processed/simulation_results.csv`)
5. **Coefficients** + **Null Distribution** → **Significance Assessment** → **Report** (`data/reports/final_report.txt`)
