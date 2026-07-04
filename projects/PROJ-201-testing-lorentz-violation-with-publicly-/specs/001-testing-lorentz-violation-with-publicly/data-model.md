# Data Model: Testing Lorentz Violation with Publicly Available CMB Data

## Overview

This document defines the data structures and schemas used throughout the analysis pipeline. The model is designed to ensure reproducibility (Constitution Principle I) and strict data hygiene (Principle III).

## Key Entities

### 1. CMBMap
Represents a processed temperature or polarization map.
*   **Attributes**:
    *   `map_id`: Unique identifier (e.g., "SMICA_TT_Nside2048").
    *   `nside`: HEALPix resolution parameter (integer, e.g., 2048).
    *   `data`: 1D numpy array of pixel values.
    *   `mask`: 1D boolean array (True = valid, False = masked).
    *   `beam_function`: 1D array of beam transfer function values.
    *   `checksum`: SHA-256 hash of the raw file.
    *   `source_url`: URL or path where the data originated (ESA Legacy Archive).

### 2. PowerSpectrum
Represents the angular power spectrum data.
*   **Attributes**:
    *   `spectrum_id`: Identifier (e.g., "TT_2_200").
    *   `multipole`: 1D array of \(\ell\) values (restricted to \(\ell < 200\)).
    *   `cl`: 1D array of power values \(C_\ell\).
    *   `variance`: 1D array of variance \(\sigma^2_\ell\).
    *   `mask_applied`: Boolean flag.
    *   `deconvolved`: Boolean flag.

### 3. AnisotropyMetric
Represents a diagnostic result from dipole or BipoSH analysis.
*   **Attributes**:
    *   `metric_type`: String ("dipole", "BipoSH").
    *   `amplitude`: Float (modulation amplitude or coefficient magnitude).
    *   `phase`: Float (for dipole) or indices \(L, M\) (for BipoSH).
    *   `sigma`: Float (statistical significance).
    *   `p_value`: Float (uncorrected).
    *   `p_value_corrected`: Float (FDR/Bonferroni corrected).

### 4. SMEConstraint
Represents the final statistical inference.
*   **Attributes**:
    *   `coefficient_name`: String (e.g., "k_(V)00^(5)").
    *   `posterior_mean`: Float.
    *   `credible_interval_95`: Tuple (lower, upper).
    *   `likelihood_ratio_stat`: Float.
    *   `ess`: Float (Effective Sample Size).
    *   `converged`: Boolean.

## Data Flow

1.  **Ingestion**: Raw FITS files (ESA) → `CMBMap` (with checksum).
2.  **Processing**: `CMBMap` → `PowerSpectrum` (via `anafast` and masking, \(\ell < 200\)).
3.  **Analysis**: `PowerSpectrum` + Simulations → `AnisotropyMetric`.
4.  **Inference**: `AnisotropyMetric` → `SMEConstraint`.

## Storage Locations

*   `data/raw/`: Raw downloads (checksummed, immutable).
*   `data/processed/`: Masked maps, power spectra (derived).
*   `data/simulations/`: Null hypothesis samples.
*   `data/results/`: Final metrics and constraints (JSON/YAML).