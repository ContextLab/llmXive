# Data Model: Quantifying the Impact of Data Resolution on Simulated Fluid Turbulence

## Overview

This document defines the data structures for input velocity fields, downsampled derivatives, and computed statistical metrics. All data is stored in HDF5 or JSON formats to ensure interoperability and efficient streaming.

## Entities

### 1. TurbulenceSnapshot
Represents a raw or processed velocity field from JHTDB.
*   **ID**: Unique identifier (e.g., `jhtdb_iso_1024_snap_001`).
*   **Grid Dimensions**: $N_x, N_y, N_z$ (e.g., 1024, 1024, 1024).
*   **Resolution Factor**: Integer (1 for ground truth, 2/4/8/16 for variants).
*   **Reynolds Number**: $Re_\lambda$ (float).
*   **File Path**: Absolute path to HDF5 file.
*   **Checksum**: SHA-256 of the raw data content.

### 2. ResolutionVariant
A downsampled version of a `TurbulenceSnapshot`.
*   **Parent ID**: Reference to `TurbulenceSnapshot.ID`.
*   **Downsampling Factor**: Integer (2, 4, 8, 16).
*   **Effective Grid**: $N_{eff} = N / Factor$.
*   **High-K Modes Zeroed**: Boolean (True).
*   **Total Energy**: Scalar (float).

### 3. BiasMetric
Computed statistics comparing a `ResolutionVariant` to its ground truth.
*   **Metric Type**: `energy_spectrum` or `structure_function`.
*   **Order**: $p$ (2 or 3).
*   **Wavenumber/Scale**: Array of $k$ or $r$ values.
*   **Value**: Array of $E(k)$ or $S_p(r)$ values.
*   **Bias**: Array of relative error percentages.
*   **Confidence Interval**: Tuple (lower, upper) for 95% CI.
*   **Scaling Exponent**: Fitted $\zeta_p$ or spectral slope.
*   **Exponent Deviation**: Difference from theoretical value ($-5/3$ or $2/3$).
*   **Inertial Subrange Resolved**: Boolean.

## Storage Layout

```text
data/
├── raw/
│   ├── snap_001.h5          # Original JHTDB data
│   └── ...
├── processed/
│   ├── snap_001_res2.h5     # Downsampled (factor 2)
│   ├── snap_001_res4.h5
│   └── ...
├── stats/
│   ├── snap_001_stats.json  # Aggregated metrics for one snapshot
│   └── ...
└── checksums.json           # Manifest of all file hashes
```

## Processing Flow

1.  **Ingestion**: `download.py` reads JHTDB, computes checksum, saves to `raw/`.
2.  **Transformation**: `downsample.py` reads `raw/`, applies FFT truncation, saves to `processed/`.
3.  **Computation**: `stats.py` reads `processed/`, computes $E(k)$, $S_p(r)$, saves to `stats/`.
4.  **Aggregation**: `analysis.py` loads all `stats/`, performs bootstrap, outputs final report.

## Constraints

*   **Immutability**: Files in `raw/` are never modified.
*   **Naming**: All processed files include the resolution factor in the name.
*   **Size**: No single file in `raw/` exceeds the disk limit or the RAM limit for loading.
