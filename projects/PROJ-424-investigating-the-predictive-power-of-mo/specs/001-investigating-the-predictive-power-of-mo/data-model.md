# Data Model: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Overview
This document defines the data structures used throughout the project lifecycle, from raw input to final analysis results. All data is stored in local files (`JSON`, `CSV`) to ensure reproducibility and checksumming.

## 1. Raw Data

### `data/raw/nist_refs.json`
Manually curated experimental diffusion coefficients.
*   **Format**: JSON
*   **Schema**:
    ```json
    [
      {
        "solvent": "string",
        "temperature_kelvin": "float",
        "diffusion_coefficient_m2_s": "float",
        "source_reference": "string"
      }
    ]
    ```
*   **Example**:
    ```json
    [
      {
        "solvent": "water",
        "temperature_kelvin": 298.15,
        "diffusion_coefficient_m2_s": 2.3e-9,
        "source_reference": "NIST TRC"
      }
    ]
    ```

### `data/raw/simulations/*.xtc` / `*.gro`
Raw GROMACS trajectory and topology files.
*   **Format**: Binary (GROMACS)
*   **Content**: Atomic coordinates over time.
*   **Naming Convention**: `{solvent}_{duration_ns}_seed{seed}.xtc`

## 2. Processed Data

### `data/processed/diffusion_results.csv`
Aggregated results from MSD analysis and scaling.
*   **Format**: CSV
*   **Columns**:
    *   `solvent` (str): e.g., "water"
    *   `duration_ns` (float): 1.0, 5.0, 10.0
    *   `seed` (int): Random seed used
    *   `msd_slope` (float): Slope of linear MSD fit (t > 100ps)
    *   `r_squared` (float): Goodness of fit (must be >= 0.95)
    *   `d_calc_m2_s` (float): Calculated diffusion coefficient (slope / 6)
    *   `d_scaled_m2_s` (float): Scaled diffusion coefficient (using fixed literature factors)
    *   `mae` (float): Absolute error vs experimental
*   **Constraint**: Rows with `r_squared` < 0.95 are marked as "CONVERGENCE_FAILED" and excluded from MAE calculation.

### `data/processed/bootstrap_stats.json`
Statistical summaries of the error distribution.
*   **Format**: JSON
*   **Schema**:
    ```json
    {
      "duration_ns": "float",
      "iterations": "int",
      "mean_mae": "float",
      "ci_lower": "float",
      "ci_upper": "float",
      "convergence_check": "boolean",
      "n_seeds": "int"
    }
    ```
*   **Note**: `n_seeds` indicates whether N=5 (target) or N=3 (fallback) was used.

### `data/processed/sensitivity_report.json`
Variance analysis across start times.
*   **Format**: JSON
*   **Schema**:
    ```json
    [
      {
        "solvent": "string",
        "duration_ns": "float",
        "start_fraction": "float",
        "d_value": "float",
        "variance_pct": "float"
      }
    ]
    ```

## 3. Scaling Factors (Fixed Constants)
*   **Water**: 0.6
*   **Ethanol**: 0.7
*   **Acetone**: 0.7
*   **Source**: Marrink et al., J. Chem. Theory Comput. 2007, 3, 1, 146–156.

## 4. Data Flow
1.  **Load**: `data/raw/nist_refs.json` -> `data/` (in-memory dict).
2.  **Simulate**: `code/simulations/` -> `data/raw/simulations/` (N=5 or N=3 seeds).
3.  **Analyze**: `data/raw/simulations/` + `data/raw/nist_refs.json` -> `data/processed/diffusion_results.csv`.
4.  **Bootstrap**: `data/processed/diffusion_results.csv` -> `data/processed/bootstrap_stats.json`.
5.  **Report**: `data/processed/` -> `results/paper_tables.md`.