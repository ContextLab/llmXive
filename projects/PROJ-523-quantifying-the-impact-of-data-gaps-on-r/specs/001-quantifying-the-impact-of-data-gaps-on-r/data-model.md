# Data Model: Quantifying the Impact of Data Gaps on Reconstructed CMB Maps

## Overview

This document defines the data structures used to represent CMB simulations, gap configurations, recovered power spectra, parameter estimates, and sensitivity analysis results. All data is stored in `data/` as `.fits` (maps) and `.yaml`/`.json` (metadata/results).

## Entities

### 1. CMB Simulation Map

Represents a simulated CMB map with ground-truth parameters.

*   **File Format**: `.fits` (HEALPix)
*   **Attributes**:
    *   `pixel_values`: Float32 array (T, E, B components).
    *   `nside`: Integer (512).
    *   `ground_truth_params`: Dict {H0, Omega_m, ns, tau}. **(Required for bias calculation)**
    *   `random_seed`: Integer.
    *   `realization_id`: String (UUID).
    *   `is_null_model`: Boolean (True if gaps are random/uncorrelated).

### 2. Gap Configuration

Describes the mask applied to the map.

*   **File Format**: `.yaml` (Metadata) + `.fits` (Mask)
*   **Attributes**:
    *   `gap_fraction`: Float (0.0 to 1.0).
    *   `spatial_distribution`: Enum {random, clustered}.
    *   `morphology`: Enum {point-source, galactic-plane}.
    *   `mask_file`: Path to mask `.fits`.

### 3. Mode-Coupling Correction

Represents the leakage matrix calculated from the gap mask to correct the Fisher Matrix.

*   **File Format**: `.npy` (NumPy array) + `.yaml` (Metadata)
*   **Attributes**:
    *   `leakage_matrix`: 2D array (ℓ x ℓ).
    *   `mask_file`: Path to the mask used for calculation.
    *   `algorithm_version`: String.

### 4. Recovered Power Spectrum

The angular power spectrum (Cℓ) derived from a gap-filled map.

*   **File Format**: `.yaml` or `.json`
*   **Attributes**:
    *   `multipole_range`: List [ℓ_min, ℓ_max].
    *   `cl_values`: List of floats.
    *   `algorithm_used`: String (harmonic, wiener, iterative).
    *   `execution_time_ms`: Integer.
    *   `has_nan`: Boolean.

### 5. Parameter Posterior

Estimated cosmological parameters from the power spectrum (using corrected Fisher Matrix).

*   **File Format**: `.yaml`
*   **Attributes**:
    *   `parameter_name`: String (H0, Omega_m, ns, tau).
    *   `median_estimate`: Float.
    *   `ci_68`: List [lower, upper].
    *   `ci_95`: List [lower, upper].
    *   `ground_truth_value`: Float.
    *   `bias_magnitude`: Float (|recovered - truth|). **(Required for analysis)**
    *   `p_value`: Float (from LMM). **(Required for analysis)**
    *   `leakage_matrix_file`: Path to the correction matrix used.

### 6. Sensitivity Analysis

Captures the results of the threshold sweep (FR-007).

*   **File Format**: `.yaml`
*   **Attributes**:
    *   `alpha_sweep`: List of floats (e.g., [0.01, 0.05, 0.1]).
    *   `tolerance_sweep`: List of floats (e.g., [0.03, 0.05, 0.07]).
    *   `bias_variance`: Float (Variance in bias rates across sweep).
    *   `significance_change`: Float (Change in statistical significance across sweep).
    *   `sweep_results`: List of objects (one per combination of alpha/tolerance).

## Relationships

*   **One-to-Many**: One `CMB Simulation Map` -> Many `Gap Configurations` (different masks applied).
*   **One-to-Many**: One `Gap Configuration` -> One `Mode-Coupling Correction` (calculated once per mask).
*   **One-to-Many**: One `Gap Configuration` -> Three `Recovered Power Spectra` (one per algorithm).
*   **One-to-Many**: One `Recovered Power Spectrum` -> One `Parameter Posterior` (per parameter).
*   **One-to-Many**: One `Parameter Posterior` -> One `Sensitivity Analysis` (aggregated results).

## Storage Rules

*   **Raw**: `data/raw/sim_{id}.fits` (Original map).
*   **Mask**: `data/raw/mask_{id}_{frac}_{morph}.fits`.
*   **Leakage**: `data/derived/leakage_{id}_{frac}_{morph}.npy`.
*   **Derived**: `data/derived/cls_{id}_{algo}.yaml`.
*   **Results**: `data/derived/params_{id}.yaml`.
*   **Sensitivity**: `data/derived/sensitivity_sweep.yaml`.
*   **Metadata**: `data/metadata/run_log.yaml` (Pilot stats, final N, configuration changes).