# Data Model: Reconstructing Early Universe Phase Transitions from CMB B-Mode Polarization

## Overview

This document defines the data structures used throughout the project. All data is stored in `data/` with checksums. Derived data is versioned and immutable.

## Data Entities

### 1. Raw Observation Data

-   **Source**: Planck 2015 SMICA Q/U maps, BICEP/Keck 2018.
-   **Format**: FITS (Flexible Image Transport System) for maps; JSON/CSV for power spectra.
-   **Storage**: `data/raw/planck_smica_q_u.fits`, `data/raw/bicep_keck_2018_cl.json`.

### 2. Processed Maps

-   **Masked B-mode Map**: HEALPix map with Galactic mask applied, derived from Q/U using `pyhealpix`.
-   **Format**: FITS.
-   **Storage**: `data/derived/masked_bmode_nside64.fits`.
-   **Attributes**: `Nside`, `Mask`, `Map_Type` (B-mode), `Checksum`.

### 3. Power Spectra

-   **Observed Spectrum**: $C_\ell^{BB}$ with covariance matrix.
-   **Format**: JSON (list of objects with `ell`, `cl`, `covariance`).
-   **Storage**: `data/derived/observed_cl_bb.json`.

### 4. Theoretical Models

-   **Model Grid**: Pre-computed theoretical spectra for a grid of parameters ($r$, $E_{\text{PT}}$).
-   **Format**: HDF5 or JSON.
-   **Storage**: `data/derived/theoretical_grid.h5`.

### 5. Inference Results

-   **Posterior Samples**: Nested Sampling or MCMC chain samples.
-   **Format**: HDF5 or NumPy `.npy`.
-   **Storage**: `data/derived/posterior_samples.h5`.
-   **Attributes**: `r_mean`, `r_std`, `E_PT_mean`, `E_PT_std`, `log_evidence`, `convergence_status`.

### 6. Validation Data

-   **Synthetic Data**: Generated from known ground truth (Inflation and Phase Transition).
-   **Storage**: `data/synthetic/test_r0.01_cl.json`, `data/synthetic/test_pt_cl.json`.

## Data Flow

1.  **Ingestion**: Raw data downloaded to `data/raw/`. Checksums computed.
2.  **Preprocessing**: Masks applied; Q/U maps converted to B-mode using `pyhealpix`; spectra computed. Output to `data/derived/`.
3.  **Inference**: Spectra + Models $\to$ Nested Sampling $\to$ Posterior samples.
4.  **Comparison**: Posterior samples $\to$ Bayes Factors $\to$ Decision metrics.
5.  **Validation**: Synthetic data $\to$ Pipeline $\to$ Recovery metrics.

## Constraints

-   **Immutability**: Files in `data/raw/` and `data/derived/` are never overwritten. New versions use timestamps or hashes in filenames.
-   **Checksums**: Every file must have a corresponding `.sha256` file.
-   **Size Limits**: Derived spectra and maps must fit within 14 GB disk limit (trivial for Nside=64).