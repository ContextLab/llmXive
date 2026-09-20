# Quickstart: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Prerequisites
*   **Python**: 3.11+
*   **GROMACS**: Installed and available in PATH (required for `gmx` commands).
*   **System**: Linux (Ubuntu recommended).

## Installation

1.  **Clone and Setup Environment**:
    ```bash
    cd projects/PROJ-424-investigating-the-predictive-power-of-mo
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify GROMACS**:
    ```bash
    gmx -version
    ```
    Ensure the version is compatible with the MARTINI force field (2022+ recommended).

## Data Preparation

1.  **Experimental Data**:
    Ensure `data/raw/nist_refs.json` exists and contains the curated values for water, ethanol, and acetone.
    ```bash
    cat data/raw/nist_refs.json
    ```

2.  **Generate Simulations** (or use pre-generated):
    If pre-generated trajectories are not present in `data/raw/simulations/`, run the simulation script:
    ```bash
    python code/simulations/run_simulation.py --solvents water ethanol acetone --durations 1 5 10 --seeds 5
    ```
    *Note: This step may take ~6-7 hours depending on CPU speed. If time > 5.5h, the script will automatically fallback to 3 seeds.*

## Running the Analysis

1.  **Run Full Pipeline**:
    Execute the analysis pipeline which calculates MSD, validates convergence, and performs bootstrapping.
    ```bash
    python code/analysis/analyze_all.py
    ```
    *This script:*
    *   Loads `nist_refs.json`.
    *   Processes `.xtc` files (discarding first 100ps).
    *   Checks $R^2 \ge 0.95$ for each trajectory.
    *   Calculates MAE and 95% CI (1000 iterations).
    *   Generates `data/processed/diffusion_results.csv` and `bootstrap_stats.json`.

2.  **Generate Reports**:
    ```bash
    python code/analysis/generate_report.py
    ```
    This produces the summary tables and plots required for SC-001, SC-002, and SC-004.

## Verification

*   **Check Convergence**: Verify that all accepted trajectories have $R^2 \ge 0.95$ in `data/processed/diffusion_results.csv`.
*   **Check Sensitivity**: Ensure `variance_pct` in `sensitivity_report.json` is < 5%.
*   **Check CI**: Verify that 95% CI intervals are present in `bootstrap_stats.json`.
*   **Check Seeds**: Verify that `n_seeds` in `bootstrap_stats.json` matches the number of seeds actually run (5 or 3).

## Troubleshooting
*   **GROMACS not found**: Install GROMACS via `apt` or `conda`.
*   **Convergence Failure**: If $R^2 < 0.95$, the simulation may be too short or the system not equilibrated. Check logs.
*   **Timeout**: If the bootstrap step exceeds 5.5 hours, the script automatically falls back to 100 iterations (FR-004).
*   **Simulation Timeout**: If the simulation step exceeds 5.5 hours, the script automatically reduces the number of seeds from 5 to 3 (Balanced Fallback).