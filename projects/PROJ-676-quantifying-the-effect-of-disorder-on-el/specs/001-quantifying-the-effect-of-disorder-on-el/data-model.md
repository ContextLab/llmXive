# Data Model: Quantifying the Effect of Disorder on Electronic Transport in 1D Chains

## Overview

This document defines the data structures, storage formats, and relationships for the 1D Anderson localization study. The model supports the generation of synthetic Hamiltonians, the storage of eigenstates, and the aggregation of localization length statistics.

## Core Entities

### 1. Hamiltonian Instance
A single realization of the 1D tight‑binding model.
*   **Attributes**:
    *   `realization_id`: Unique integer (seed‑based).
    *   `L`: System size (integer).
    *   `W`: Disorder width (float).
    *   `seed`: Random seed used for generation (integer).
    *   `hopping`: Hopping parameter $t$ (float, default 1.0).
    *   `on_site_energies`: Array of shape $(L,)$, float64.
    *   `created_at`: Timestamp.

### 2. Eigenstate
An eigenvector and eigenvalue pair derived from a Hamiltonian.
*   **Attributes**:
    *   `eigenstate_id`: Unique identifier.
    *   `hamiltonian_id`: Foreign key to Hamiltonian Instance.
    *   `energy`: Eigenvalue $E$ (float).
    *   `wavefunction`: Array of shape $(L,)$, complex128.
    *   `probability_density`: Array of shape $(L,)$, float64 ($|\psi|^2$).
    *   `participation_ratio`: Float ($PR$).
    *   `is_band_center`: Boolean ($|E| < 0.1$).
    *   `residual_norm`: Float – Euclidean norm of the residual $H\psi - E\psi$ (for eigenvalue solver verification).

### 3. Localization Measurement
Aggregated statistics for a specific $(W, L)$ pair and method.
*   **Attributes**:
    *   `measurement_id`: Unique identifier.
    *   `W`: Disorder width.
    *   `L`: System size.
    *   `method`: String ("PR" or "TM").
    *   `localization_length`: Float ($\xi$).
    *   `uncertainty`: Float (standard error of the mean).
    *   `n_realizations`: Integer (count of samples averaged).
    *   `energy_range`:
        *   `min`: Float.
        *   `max`: Float.  *(|E| < 0.1)*
    *   `convergence_check`:
        *   `passed`: Boolean – True if finite‑size scaling (PR) or Lyapunov‑exponent convergence (TM) criteria are met.
        *   `relative_change`: Float – Relative change of $\xi$ (PR) or $\gamma$ (TM) between successive $L$ values.
    *   `convergence_trace` (required): List of objects `{ "L": integer, "value": float }` documenting the evolution of $\xi$ (PR) or $\gamma$ (TM) with system size. This trace is mandatory for verifying numerical stability (Principle VI).

### 4. Scaling Result
Final regression result for the disorder‑width dependence.
*   **Attributes**:
    *   `W`: Disorder width.
    *   `slope`: Float (from $\log \xi$ vs $\log W$).
    *   `intercept`: Float.
    *   `r_squared`: Float.
    *   `p_value`: Float.
    *   `bonferroni_corrected_p`: Float.

## Storage Strategy

*   **Raw Data (`data/raw/`)**:
    *   Format: HDF5 (`.h5`).
    *   Structure: One file per $(W, L)$ combination.
    *   Content: `on_site_energies`, `eigenvalues`, `eigenvectors` (sparse if needed).
    *   Rationale: HDF5 allows efficient partial reads and avoids loading entire datasets into RAM.

*   **Processed Data (`data/processed/`)**:
    *   Format: CSV/Parquet.
    *   Content: Aggregated `LocalizationMeasurement` and `ScalingResult` tables.
    *   Rationale: Lightweight for statistical analysis and plotting.

*   **Metadata (`data/metadata/`)**:
    *   Format: JSON.
    *   Content: `provenance.json` (seeds, parameters, timestamps, realization index), `checksums.json`, `residuals.json`, `convergence_trace.json`.

## Constraints & Validation

*   **Data Integrity**: All raw files must include a SHA‑256 checksum in `data/metadata/checksums.json`.
*   **Numerical Precision**: All floats stored as `float64` or `complex128`. No `float32`.
*   **Completeness**: For every $(W, L)$, exactly $N$ realizations (e.g., 100) must exist in the processed table.
*   **Band Center Filter**: Only eigenstates with $|E| < 0.1$ are included in PR/TM analysis.
*   **Convergence Trace**: Required for every measurement to satisfy Constitution Principle VI (numerical stability verification).