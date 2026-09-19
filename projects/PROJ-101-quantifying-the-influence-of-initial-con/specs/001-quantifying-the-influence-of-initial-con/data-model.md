# Data Model: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Overview

This document defines the data structures, file formats, and schemas used in the project. All data is stored in `data/` with checksums recorded in `state/`.

## Directory Structure

```text
data/
├── raw/
│   ├── trajectories_N{N}_sigma{sigma}_trial{t}.npz
│   └── ... (generated synthetic data)
├── processed/
│   ├── ftle_results.json           # Aggregated FTLE estimates
│   ├── baseline_{N}.json           # Asymptotic baseline for dimension N
│   ├── regression_stats.json       # Regression coefficients and p-values
│   └── plots/                      # Generated figures
└── artifacts/
    └── manifest.yaml               # Checksums and metadata
```

## Entity Definitions

### 1. Trajectory (Raw)
- **Source**: `code/simulation/generator.py`
- **Format**: NumPy `.npz` (compressed)
- **Contents**:
  - `time`: 1D array of time points.
  - `state`: 2D array $(T, 3N)$ of system states.
  - `noise`: 2D array $(T, 3N)$ of injected noise (for verification).
  - `params`: Dict with `N`, `sigma`, `seed`, `rho`, `beta`, `sigma_l`.

### 2. FTLE Result (Processed)
- **Source**: `code/analysis/ftle.py`
- **Format**: JSON
- **Schema**: See `contracts/ftle_result.schema.yaml`
- **Key Fields**:
  - `window_size`: Explicitly recorded sliding window size $T$.
  - `status`: "valid", "unphysical", or "non-chaotic".

### 3. Baseline (Processed)
- **Source**: `code/analysis/baseline.py`
- **Format**: JSON
- **Contents**:
  - `N`: System dimension.
  - `lambda_max`: Maximum Lyapunov exponent (asymptotic).
  - `convergence_error`: % error at $T=5000$.
  - `status`: "valid" or "invalid".
  - `algorithm`: "Rosenstein" (as per Constitution).

### 4. Regression Stats (Processed)
- **Source**: `code/analysis/regression.py`
- **Format**: JSON
- **Contents**:
  - `model_type`: e.g., "power_law".
  - `coefficients`: Dict of fitted parameters.
  - `r_squared`: $R^2$ value.
  - `p_values`: Dict of p-values for coefficients.
  - `scaling_exponent`: Exponent relating dimension to bias (if applicable).
  - `effect_size`: Cohen's d for the bias term.
  - `trial_count`: Number of trials used.

## Data Flow

1.  **Generation**: `generator.py` reads `config.py` -> writes `data/raw/*.npz`.
2.  **Validation**: `baseline.py` reads `data/raw` (clean) -> writes `data/processed/baseline_{N}.json` (using Rosenstein).
3.  **Computation**: `ftle.py` reads `data/raw` -> writes `data/processed/ftle_results.json` (includes `window_size` metadata).
4.  **Analysis**: `regression.py` reads `ftle_results.json` + `baseline` -> writes `data/processed/regression_stats.json`.
5.  **Visualization**: `code/analysis/plotting.py` reads `regression_stats.json` -> writes `data/processed/plots/*.png`.

## Integrity & Hygiene

- **Checksums**: Every file in `data/` is checksummed (SHA-256) upon creation.
- **Immutability**: Raw data files are never modified. Derived files are written with new timestamps.
- **Versioning**: `state/manifest.yaml` tracks the git commit hash and file hashes for every artifact.