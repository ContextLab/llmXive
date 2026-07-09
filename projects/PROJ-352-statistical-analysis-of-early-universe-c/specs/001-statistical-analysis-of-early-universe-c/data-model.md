# Data Model: Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

## Overview

This document defines the data structures, file formats, and schemas used throughout the project. All data is stored in the `data/` and `output/` directories.

## Data Entities

### 1. CMB Map (Raw & Processed)

**Description**: The CMB temperature anisotropy map in HEALPix format.
**Source**: Planck Legacy Archive (SMICA component separation).
**Format**: FITS (Flexible Image Transport System).

**Attributes**:
- `nside`: Integer resolution parameter (128).
- `pixels`: Array of temperature values (float32, $\mu K$).
- `mask`: Binary mask array (1 = valid, 0 = masked).
- `checksum`: MD5/SHA256 hash for integrity.

**File Path**: `data/raw/planck_smica_n128.fits`, `data/processed/masked_map.fits`

### 2. Minkowski Functional Vector

**Description**: The computed geometric statistics for a specific map at a specific threshold.
**Format**: JSON or NumPy array.

**Schema**:
- `map_id`: String identifier (e.g., "observed", "sim_001", "sim_alt_001").
- `threshold`: Float ($\nu$ in units of $\sigma$).
- `area`: Float (Fraction of sky).
- `perimeter`: Float (Normalized length).
- `genus`: Float (Euler characteristic).
- `timestamp`: ISO 8601 timestamp.
- `mask_correction_method`: String (e.g., "Schmalzing_Gorski_1998").
- `mask_buffer_pixels`: Integer (Number of pixels in buffer zone, default 2, used for verification only).
- `precision`: Float (Numerical precision of the computation, target ≥6 decimal places).

**File Path**: `data/processed/mf_vectors.csv` (aggregated for all simulations)

### 3. Simulation Batch (Transient)

**Description**: Metadata for a batch of simulations processed together to manage memory.
**Format**: JSON.

**Attributes**:
- `batch_id`: Integer (0 to 9).
- `simulation_ids`: List of integers (e.g., [0-99]).
- `hypothesis`: String ("Gaussian" or "Gaussian+String").
- `start_time`: ISO 8601 timestamp.
- `end_time`: ISO 8601 timestamp.
- `peak_memory_gb`: Float (Peak RAM usage during batch).
- `status`: String ("completed", "failed", "timeout").

**File Path**: `data/processed/batch_metadata.json` (Optional: Diagnostic artifact only. Not a primary data entity. Intermediate simulation maps are NOT stored to disk; only MF vectors are persisted.)

### 4. Statistical Results

**Description**: Final output of the likelihood ratio test and constraint derivation.
**Format**: JSON.

**Attributes**:
- `p_value`: Float (Significance of deviation from Gaussianity).
- `g_mu_upper_bound`: Float (95% confidence upper limit on string tension).
- `degrees_of_freedom`: Integer.
- `covariance_matrix`: 3x3 matrix of MF covariances (or reduced PCA components).
- `model_used`: String ("Gaussian", "Gaussian + Cosmic String").
- `deviation_found`: Boolean (True if $H_0$ rejected).
- `template_fit_parameters`: Object (Contains $G\mu$ value, likelihood score if deviation found).

## File Structure

```text
data/
├── raw/
│   ├── planck_smica_n128.fits       # Raw CMB map
│   ├── u73_mask.fits                # Raw Galactic mask
│   ├── beam_transfer_function.fits  # Planck beam
│   ├── noise_covariance.fits        # Planck noise
│   └── power_spectrum.clik          # Raw power spectrum
├── processed/
│   ├── masked_cmb.fits              # CMB * Mask
│   ├── mf_vectors.csv               # All computed MF vectors (aggregated)
│   ├── batch_metadata.json          # Optional: batch processing logs (diagnostic only)
│   └── pca_components.npy           # Optional: PCA transformed data
└── output/
    └── results.json                 # Final statistical inference
```

## Data Flow Diagram

1.  **Download**: `data/raw/` <- Planck Archive (HTTP).
2.  **Masking**: `data/processed/masked_cmb.fits` <- `data/raw/planck_smica_n128.fits` * `data/raw/u73_mask.fits`.
3.  **Simulation Loop (Streaming)**:
    - Load Batch Config.
    - For each simulation in batch:
        - Generate `Gaussian Map` (in memory).
        - Apply Beam (Planck transfer function) and Noise (Covariance map).
        - Compute `MF Vector` (in memory).
        - Append `MF Vector` to `data/processed/mf_vectors.csv`.
        - Discard `Gaussian Map`.
    - Save `Batch Metadata` (Optional, diagnostic only).
4.  **Analysis**: Read `mf_vectors.csv` -> PCA -> Shrinkage Covariance -> LRT -> `data/output/results.json`.

## Constraints

- **Checksums**: All files in `data/raw/` must have a corresponding `.checksum` file.
- **Immutability**: Raw files are never modified.
- **Precision**: Temperature values stored as `float32` (sufficient for $\mu K$ precision). MFs stored as `float64`.
- **Streaming**: Intermediate simulation maps are NOT stored to disk to conserve disk space; only the MF vectors and optional batch metadata are persisted.