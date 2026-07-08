# Data Model: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

## Overview

This document defines the data structures for the harmonized dataset, model outputs, and validation results. All data is stored in `data/processed/` and `data/results/`.

## Entities

### 1. HarmonizedDataset

The unified dataset containing aligned force-distance measurements and the full or diagonal covariance matrix.

**Schema**:
-   `separation`: 1D array (float64), unit: meters (m).
-   `force`: 1D array (float64), unit: Newtons (N).
-   `force_stat_err`: 1D array (float64), unit: Newtons (N).
-   `force_sys_err`: 1D array (float64), unit: Newtons (N).
-   `covariance_matrix`: 2D array (float64), shape `(N, N)`, unit: $N^2$.
-   `covariance_type`: String, "full", "diagonal", or "banded" (indicating the approximation used).
-   `source_id`: String, identifier of the original experiment (e.g., "2106.08611-run-1").
-   `metadata`: JSON object containing original units, conversion factors, and checksum.

**Constraints**:
-   `separation` must be strictly increasing and within [10⁻⁵, 10⁻⁴] m.
-   `covariance_matrix` must be symmetric and positive-definite.
-   No missing values allowed.
-   If `covariance_type` is "diagonal", the matrix must be stored as a 2D array with zeros off-diagonal, but the type must be explicitly flagged.

### 2. ModelPosterior

Output from the `emcee` MCMC run.

**Schema**:
-   `samples`: 2D array (float64), shape `(n_walkers * n_steps, 2)`.
    -   Column 0: $\alpha$ (dimensionless).
    -   Column 1: $\lambda$ (meters).
-   `burn_in`: Integer, number of steps discarded.
-   `gelman_rubin`: Float, convergence statistic.
-   `metadata`: JSON with random seed, walker count, step count, and prior bounds.

### 3. BayesianEvidence

Output from the `dynesty` nested sampling run.

**Schema**:
-   `model_name`: String ("Newtonian" or "Yukawa").
-   `log_evidence`: Float, $\ln Z$.
-   `evidence_error`: Float, uncertainty on $\ln Z$.
-   `samples`: 2D array of weighted samples (optional, for plotting).
-   `bayes_factor`: Float, $K = Z_{Yukawa} / Z_{Newtonian}$ (computed relative to Newtonian).

### 4. RobustnessResult

Output from cross-validation and sensitivity tests.

**Schema**:
-   `test_type`: String ("leave_one_out", "uncertainty_inflation", "injection_recovery", "null_simulation").
-   `parameter`: String ("alpha", "lambda", "bayes_factor").
-   `value`: Float, the measured quantity.
-   `uncertainty`: Float, 95% credible interval width or error.
-   `iteration`: Integer, for leave-one-out index.
-   `status`: String ("passed", "failed", "warning").

## Data Flow

1.  **Raw Data** (arXiv) → `data/raw/` (Checksummed).
2.  **Harmonization** → `data/processed/harmonized_dataset.csv` (plus separate `.npz` for covariance).
3.  **Inference** → `data/results/posterior_samples.npz`, `data/results/evidence.json`.
4.  **Robustness** → `data/results/robustness_summary.json`.
