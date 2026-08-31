# Data Model: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Overview

This document defines the data structures for the project, ensuring strict adherence to the "Single Source of Truth" and "Data Hygiene" principles. All data artifacts are stored in `data/` and validated against schemas in `contracts/`.

## Data Flow

1.  **Input**: Configuration parameters (`N`, `sigma`, `T`, `rho`) from `code/config.py`.
2.  **Generation**: `code/generator.py` produces raw trajectories (Parquet).
3.  **Baseline**: `code/baseline.py` computes asymptotic exponents (JSON) with Richardson extrapolation.
4.  **Analysis**: `code/ftle.py` and `code/analysis.py` produce deviation metrics and regression results (JSON) with model selection.
5.  **Output**: `data/processed/` contains the final results used for visualization.

## Entity Definitions

### 1. Trajectory (Raw Data)
- **Description**: Time-series of state vectors $(x, y, z)$ for $N$ coupled oscillators.
- **Source**: `code/generator.py`
- **Location**: `data/raw/trajectory_N{N}_sigma{sigma}.parquet`
- **Fields**:
  - `t`: float (time step)
  - `state`: array of floats (state vector of size $3N$)
  - `noise_level`: float (injected $\sigma$)
  - `is_physical`: boolean (flag for attractor bounds)
  - `shadowing_valid`: boolean (flag for shadowing lemma check)

### 2. Baseline (Computed)
- **Description**: Asymptotic Lyapunov spectrum for the clean system.
- **Source**: `code/baseline.py`
- **Location**: `data/processed/baseline_N{N}.json`
- **Fields**:
  - `lambda_max`: float (maximum exponent)
  - `lambda_spectrum`: array of floats (all $3N$ exponents)
  - `convergence_error`: float (relative change at end of trajectory)
  - `richardson_error`: float (error estimate from Richardson extrapolation)
  - `trajectory_length`: int
  - `validated`: boolean (true if error $< 5\%$ and Richardson error is small)
  - `is_chaotic`: boolean (true if lambda_max > 0)

### 3. FTLE Results (Processed)
- **Description**: Finite-time estimates and deviations.
- **Source**: `code/ftle.py`
- **Location**: `data/processed/ftle_results_N{N}_sigma{sigma}.json`
- **Fields**:
  - `window_size`: int ($T$)
  - `ftle_estimate`: float
  - `deviation`: float ($\Delta \lambda$)
  - `noise_level`: float
  - `trial_id`: int (for reproducibility)
  - `shadowing_valid`: boolean (flag for shadowing lemma check)

### 4. Regression Output (Final)
- **Description**: Statistical summary of the bias scaling.
- **Source**: `code/analysis.py`
- **Location**: `data/processed/regression_summary_N{N}.json`
- **Fields**:
  - `selected_model`: string (e.g., "power_law", "loess")
  - `model_coefficients`: dict ($\alpha, \beta, k, m$) or dict for LOESS
  - `p_values`: dict (for each coefficient)
  - `effect_size`: float
  - `r_squared`: float
  - `n_trials`: int
  - `numerical_error_floor`: float
  - `bias_significant`: boolean (true if bias > 3 * numerical_error_floor)

## Data Hygiene Rules

- **Immutability**: Files in `data/raw` are never modified. New runs overwrite with versioned filenames (e.g., `_v2`).
- **Checksums**: SHA-256 hashes of all files in `data/` are recorded in `state/artifact_hashes`.
- **Reproducibility**: All random seeds are pinned in `code/config.py`.
- **Validation**: Every file written must pass the schema validation defined in `contracts/`.
