# Data Model: Assessing the Validity of the Cosmological Principle with Public CMB Data

## Overview

This document defines the data structures and file formats used in the project. All data is stored in HEALPix FITS format or NumPy binary formats.

## Entity Definitions

### CMB Temperature Map
*   **Description**: A 1D array of temperature values in µK, indexed by HEALPix pixel ID.
*   **Resolution**: Nside=128 (after downgrading).
*   **Size**: $12 \times 128^2 = 196,608$ pixels.
*   **Type**: `float64`.
*   **Missing Data**: Masked pixels are represented by `NaN` or a specific flag value (e.g., -999.0).

### Angular Power Spectrum ($C_l$)
*   **Description**: Array of power values for multipoles $l=2$ to $l=128$.
*   **Size**: 127 values.
*   **Type**: `float64`.
*   **Units**: $\mu K^2$.

### Monte Carlo Simulation
*   **Description**: A synthetic CMB map generated from a Gaussian random field.
*   **Format**: Same as CMB Temperature Map.
*   **Count**: $N$ simulations (e.g., 1000).

### Hemispherical Variance Statistic
*   **Description**: A scalar value representing the ratio or difference of power between two hemispheres.
*   **Type**: `float64`.

## File Layout

```text
data/
├── raw/
│   ├── planck_2018_smica_nside2048.fits   # Original download
│   └── commander_mask_nside2048.fits      # Original mask
├── processed/
│   ├── planck_masked_nside128.fits        # Masked, downgraded map
│   └── mask_nside128.fits                 # Downgraded mask
├── simulations/
│   └── mc_sims_nside128.npy               # Array of shape (N_sims, N_pix)
└── results/
    ├── cl_fullsky.npy                     # Full sky C_l
    ├── cl_north.npy                       # North hemisphere C_l
    ├── cl_south.npy                       # South hemisphere C_l
    ├── stat_observed.npy                  # Observed hemispherical statistic
    └── stat_null_dist.npy                 # Null distribution array
```

## Data Flow

1.  **Ingest**: `planck_2018_smica_nside2048.fits` → `planck_masked_nside128.fits`
2.  **Transform**: `planck_masked_nside128.fits` → `cl_fullsky.npy`, `cl_north.npy`, etc.
3.  **Simulate**: `theoretical_cl` → `mc_sims_nside128.npy`
4.  **Analyze**: `cl_*.npy` + `mc_sims_nside128.npy` → `stat_null_dist.npy`
5.  **Output**: `stat_observed.npy` vs `stat_null_dist.npy` → p-value.
