# Data Model: Testing Hubble Constant Isotropy

## Overview

This document defines the data structures used in the project, ensuring consistency between ingestion, analysis, and output. All data is stored in `data/` with checksums recorded in the project state.

## Entities

### 1. Supernova Record
Represents a single Type Ia supernova from the Pantheon+ sample.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `sn_id` | string | Unique supernova identifier (e.g., "SN1998bw") | Pantheon+ |
| `ra` | float | Right Ascension in degrees | Pantheon+ |
| `dec` | float | Declination in degrees | Pantheon+ |
| `z` | float | Redshift | Pantheon+ |
| `mu` | float | Distance modulus | Pantheon+ |
| `mu_err` | float | Uncertainty in distance modulus | Pantheon+ |
| `flags` | string | Quality flags (comma-separated) | Pantheon+ |
| `healpix_index` | int | HEALPix pixel index (Nside=4, NESTED) | Derived |
| `z_cos` | float | Redshift corrected for peculiar velocity | Derived |

### 2. H0 Estimate
Represents a derived $H_0$ value for a specific region or the global sample.

| Field | Type | Description |
|-------|------|-------------|
| `region_id` | string | "global" or HEALPix pixel index (e.g., "42") |
| `h0_value` | float | Estimated Hubble constant (km/s/Mpc) |
| `h0_err` | float | Standard error of the estimate |
| `n_sne` | int | Number of supernovae used |
| `method` | string | "MLE" (Maximum Likelihood Estimation) or "Shrinkage" |
| `shrinkage_factor` | float | Shrinkage factor applied for low-N pixels (1.0 for MLE) |

### 3. Anisotropy Metric
Represents the result of the spherical harmonic analysis.

| Field | Type | Description |
|-------|------|-------------|
| `mode` | string | "dipole" or "quadrupole" |
| `amplitude` | float | Observed amplitude of the mode |
| `p_value` | float | Raw p-value from Monte Carlo |
| `p_value_fdr` | float | FDR-corrected p-value |
| `is_significant` | boolean | True if `p_value_fdr` < 0.05 |
| `n_simulations` | int | Number of Monte Carlo runs (e.g., 1000) |

## Data Flow

1.  **Raw Input**: `data/raw/pantheon_plus.csv` (from Zenodo).
2.  **Cleaned Input**: `data/processed/cleaned_sne.parquet` (filtered, HEALPix assigned, `z_cos` calculated).
3.  **Intermediate**: `data/processed/h0_estimates.parquet` (local and global, with shrinkage factors).
4.  **Results**: `data/results/anisotropy_metrics.json` (dipole, quadrupole, p-values).
5.  **Simulations**: `data/results/mc_simulations.parquet` (optional, if storage permits).

## Constraints

- **Immutability**: Raw data is never modified.
- **Checksums**: All files in `data/` must have a corresponding SHA-256 hash in the project state.
- **Schema Enforcement**: All processed files must conform to the contracts defined in `contracts/`.
- **Versioning**: The `state/projects/...yaml` file is updated with `updated_at` timestamps upon any artifact change.