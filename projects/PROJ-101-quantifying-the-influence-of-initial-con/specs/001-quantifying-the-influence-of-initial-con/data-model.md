# Data Model: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Overview

This document defines the schema for synthetic data generated and analyzed in this project. All data is stored in `data/` as NumPy `.npy` or `.npz` files (for arrays) or JSON/CSV (for metadata).

## Entities

### 1. Trajectory
A time-ordered sequence of state vectors for a coupled Lorenz system.

- **Attributes**:
  - `id`: Unique identifier (UUID).
  - `n_oscillators`: Number of coupled oscillators ($N$).
  - `coupling_strength`: Diffusive coupling parameter $D$.
  - `noise_level`: Injected Gaussian noise standard deviation $\sigma_{noise}$.
  - `seed`: Random seed used for generation.
  - `time_steps`: Total number of time steps.
  - `dt`: Time step size.
  - `data_path`: Relative path to the `.npz` file containing the array.
  - `is_physical`: Boolean flag (True if trajectory remains bounded).
  - `escape_time`: Integer (time step of escape, or `null` if bounded).

- **File Format**:
  - `.npz` file containing:
    - `t`: 1D array of time points.
    - `states`: 2D array of shape `(time_steps, 3 * N)`.
    - `noise`: 2D array of shape `(time_steps, 3 * N)` (the injected noise).

### 2. FTLE Result
A single FTLE estimate for a specific window and trajectory.

- **Attributes**:
  - `trajectory_id`: Reference to the parent trajectory UUID.
  - `window_size`: Time window $T$ (or actual time used if escaped).
  - `max_ftle`: The maximum Lyapunov exponent estimate (optional, can be null if escaped before window completion).
  - `full_spectrum`: List of all $3N$ exponents (optional, for debugging).
  - `deviation`: $\Delta \lambda = \text{max\_ftle} - \lambda_{\text{asymptotic}}$ (optional if max_ftle is null).
  - `is_converged`: Boolean (True if $\lambda$ within 5% of baseline for clean case).
  - `escape_event`: Boolean (True if the trajectory escaped during the window).

- **File Format**:
  - `.json` or `.csv` table with one row per estimate.

### 3. Regression Analysis
The statistical summary of the deviation scaling.

- **Attributes**:
  - `model_formula`: String representation of the regression model.
  - `model_type`: String (e.g., "power_law", "additive", "saturation").
  - `selection_metric`: String (AIC or BIC value).
  - `coefficients`: Dictionary of parameter estimates.
  - `p_values`: Dictionary of p-values.
  - `r_squared`: Coefficient of determination.
  - `effect_size`: Cohen's d or similar.
  - `plot_path`: Path to the generated figure (PNG/SVG).
  - `normality_test`: Dictionary (statistic, p-value) from Shapiro-Wilk.
  - `method_used`: String ("t-test" or "bootstrapped").

- **File Format**:
  - `.json` summary file.

### 4. Escape Event Summary
Summary of trajectory stability under noise.

- **Attributes**:
  - `noise_level`: The noise amplitude.
  - `total_trials`: Total number of trials generated.
  - `escape_count`: Number of trials that escaped.
  - `escape_probability`: Fraction of trials that escaped.
  - `mean_escape_time`: Average time step of escape (for escaped trials).

- **File Format**:
  - `.json` or `.csv` table.

## Data Flow

1. **Generation**: `generator.py` reads `config.py` -> writes `data/raw/trajectory_<id>.npz`.
2. **Validation**: `baseline.py` reads `data/raw/*.npz` -> writes `data/processed/baseline_stats.json`.
3. **Analysis**: `ftle.py` reads `data/raw/*.npz` -> writes `data/processed/ftle_results.csv`.
4. **Regression**: `regression.py` reads `data/processed/ftle_results.csv` -> writes `data/processed/regression_summary.json` and figures.
5. **Escape Analysis**: `regression.py` also generates `data/processed/escape_summary.json`.

## Checksums

All raw files in `data/raw/` are checksummed (SHA-256) and recorded in `state/...yaml`.
Derivations in `data/processed/` are derived from raw files; their checksums are recorded upon generation.