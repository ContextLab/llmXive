# Data Model: Exploring the Impact of Cosmic Microwave Background Anomalies on Early Universe Simulations

## 1. Overview

This document defines the data structures, file formats, and schemas used in the project. The data flow is: `Raw CMB Maps` → `Power Spectra` → `Initial Conditions` → `Simulation Snapshots` → `Statistical Results`.

## 2. Entity Definitions

### 2.1 CMB Temperature Map
- **Description**: Full-sky temperature anisotropy data from Planck PR3.
- **Format**: FITS (`.fits`)
- **Key Attributes**:
  - `Nside`: Resolution parameter (e.g., 2048).
  - `Map Type`: Commander or SMICA.
  - `Galactic Mask`: Boolean mask for |b| > 5°.
  - `Checksum`: MD5/SHA256 hash.
- **Storage**: `data/raw/planck_map.fits`

### 2.2 Power Spectrum
- **Description**: Angular power spectrum Cℓ or matter power spectrum P(k).
- **Format**: NumPy (`.npy`) or JSON.
- **Key Attributes**:
  - `l_values` (for Cℓ): Multipole moments.
  - `C_l_values`: Power amplitudes.
  - `k_values` (for P(k)): Wavenumbers.
  - `P_k_values`: Power amplitudes.
  - `Error_bars`: Cosmic variance/instrumental noise.
- **Storage**: `data/derived/power_spectrum.npy`

### 2.3 Initial Condition (IC) File
- **Description**: Input file for N-body simulation.
- **Format**: GADGET-2 (`.ic`) or HDF5 (nbodykit).
- **Key Attributes**:
  - `Box_Size`: 250 Mpc/h.
  - `Num_Particles`: 128³.
  - `Redshift`: z_start (e.g., 100).
  - `Cosmology`: Ω_m, Ω_Λ, H0, σ8.
  - `Power_Spectrum_File`: Reference to the modified P(k).
  - `Injection_Method`: "Phase-Injected" or "Standard".
- **Storage**: `data/derived/ic_anomaly.ic`, `data/derived/ic_control.ic`

### 2.4 Simulation Snapshot
- **Description**: Output of N-body simulation at z=0.
- **Format**: GADGET-2 (`.snapshot`) or HDF5.
- **Key Attributes**:
  - `Particle_Positions`: (N, 3) array.
  - `Particle_Velocities`: (N, 3) array.
  - `Particle_Masses`: (N,) array.
  - `Redshift`: 0.0.
- **Storage**: `data/derived/snapshot_anomaly.0`, `data/derived/snapshot_control.0`

### 2.5 Statistical Result
- **Description**: Output of statistical tests (Diagnostic).
- **Format**: JSON.
- **Key Attributes**:
  - `test_type`: "KS" or "ChiSquared".
  - `statistic`: Test statistic value.
  - `p_value`: P-value (Diagnostic Metric).
  - `correction_method`: "Bonferroni" or "Benjamini-Hochberg".
  - `delta_values`: (Anomaly - Control) metrics.
  - `interpretation`: "Diagnostic Metric (N=1)" or "Associational".
- **Storage**: `data/results/statistical_results.json`

## 3. Data Flow Diagram

```mermaid
graph TD
    A[Planck Map (FITS)] -->|Download & Validate| B[Raw Data]
    B -->|Calculate C_l| C[Power Spectrum (NPY)]
    C -->|Phase Injection| D[Anomaly Power Spectrum]
    D -->|Generate IC| E[Initial Conditions (IC)]
    F[Standard ΛCDM Power Spectrum] -->|Generate IC| G[Control IC]
    E -->|Run Sim| H[Anomaly Snapshot]
    G -->|Run Sim| I[Control Snapshot]
    H -->|Extract Stats| J[LSS Stats (NPY)]
    I -->|Extract Stats| K[LSS Stats (NPY)]
    J -->|Compare| L[Statistical Results (JSON)]
    K -->|Compare| L
```

## 4. Constraints & Validation

- **Checksums**: All raw data must be checksummed before use.
- **Size Limits**: IC files ≤ 500 MB; Total disk usage ≤ 14 GB.
- **Format Compliance**: IC files must strictly adhere to GADGET-2 or nbodykit specifications.
- **Data Immutability**: Raw data is never modified. Derivations create new files.
- **Versioning**: All artifacts must have a content hash recorded in `state/`.