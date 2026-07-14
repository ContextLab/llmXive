# Data Model: Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems

## Overview

This document defines the data structures, schemas, and relationships used in the project. All data flows from raw Monte Carlo configurations through preprocessing to latent representations and final analysis results.

## Key Entities

### 1. SpinConfiguration
Represents a single snapshot of the spin system.
*   **Attributes**:
    *   `lattice_size` (int): $L$ (e.g., 16, 24).
    *   `temperature` (float): $T$ in units of $J$.
    *   `spins` (Tensor): Shape `[3, L, L]`. Values are unit vectors $(S_x, S_y, S_z)$.
    *   `timestamp` (str): ISO 8601 generation time.
    *   `seed` (int): Random seed used for generation.
    *   `checksum` (str): SHA-256 of the raw data file (added for Constitution III).
    *   `tau_int` (float): Integrated autocorrelation time for magnetization at this temperature.

### 2. PreprocessedTensor
The normalized input for the VAE.
*   **Attributes**:
    *   `data` (Tensor): Shape `[N, 3, L, L]`.
    *   `temperatures` (Array): Shape `[N]`.
    *   `split` (str): "train" or "validation".
    *   `checksum` (str): SHA-256 of the file.

### 3. LatentRepresentation
The output of the VAE encoder.
*   **Attributes**:
    *   `mu` (Tensor): Shape `[N, 10]`. Mean of the latent distribution.
    *   `log_var` (Tensor): Shape `[N, 10]`. Log-variance.
    *   `temperature` (float): Associated temperature.
    *   `reconstruction_error` (float): MSE between input and output.

### 4. CriticalSignature
The final derived metric.
*   **Attributes**:
    *   `model_type` (str): "Heisenberg" or "XY".
    *   `t_star` (float): Detected critical temperature.
    *   `ci_lower` (float): 95% CI lower bound.
    *   `ci_upper` (float): 95% CI upper bound.
    *   `significance_metric` (float): Signal-to-noise ratio or peak height (replaces p_value from BCPD).
    *   `ground_truth_chi_extrapolated` (float): Extrapolated critical temperature $T_c(\infty)$ from FSS.
    *   `is_artifact` (bool): True if peak did not sharpen with L.

## Data Flow

1.  **Generation**: `generator.py` $\to$ Raw spin configurations (NumPy `.npy`).
2.  **Preprocessing**: `loader.py` $\to$ Normalized tensors + stratified split.
3.  **Training**: `training.py` $\to$ Trained VAE weights (`.pt`).
4.  **Inference**: `latent_analysis.py` $\to$ Latent means/variances per temperature.
5.  **Analysis**: `bootstrap.py` $\to$ Final CriticalSignature (JSON/CSV).

## Storage Strategy

*   **Raw Data**: `data/raw/` (Checksummed, immutable).
*   **Processed Data**: `data/processed/` (Derived, versioned).
*   **Models**: `models/` (Trained weights).
*   **Results**: `results/` (Final analysis outputs).

## Constraints

*   All tensors must be `float32` to save memory.
*   File sizes for raw data must not exceed a manageable total volume.
*   Random seeds must be recorded in metadata for every data file.
*   `tau_int` must be recorded for every temperature bin to ensure valid bootstrap resampling.