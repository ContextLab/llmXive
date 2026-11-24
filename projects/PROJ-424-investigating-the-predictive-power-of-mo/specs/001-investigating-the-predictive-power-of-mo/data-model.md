# Data Model: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Overview
Three persisted artifacts are produced; each is validated against a JSON/YAML contract in `contracts/`.

### 1. `diffusion_results`
- **Location**: `data/processed/diffusion_results.csv` (one row per trajectory).  
- **Fields**: `solvent`, `duration_ns`, `seed`, `msd_slope`, `r_squared`, `loglog_slope`, `d_calc_m2_s`, `d_corr_m2_s`, `mae`, `status`.  
- **Purpose**: Stores raw diffusion calculations and convergence diagnostics; feeds downstream MAE and bootstrap steps.

### 2. `bootstrap_stats`
- **Location**: `data/processed/bootstrap_stats.json`.  
- **Structure**:  
  ```json
  {
    "entries": [ { "solvent": "...", "duration_ns": ..., "iterations": 1000,
                   "mean_mae": ..., "ci_lower": ..., "ci_upper": ...,
                   "n_seeds": ..., "granularity_note": "..." }, ... ],
    "paired_test": [ { "solvent": "...", "mae_1ns": ..., "mae_10ns": ...,
                       "mean_difference": ..., "p_value": ..., 
                       "granularity_note": "..." }, ... ]
  }
  ```
- **Purpose**: Provides a confidence interval for MAE per timescale. and a descriptive paired‑comparison.

### 3. `sensitivity_report`
- **Location**: `data/processed/sensitivity_report.json`.  
- **Fields**: `solvent`, `duration_ns`, `start_fraction` (0.1/0.2/0.3), `variance_pct`, optional `note`.  
- **Purpose**: Quantifies how the choice of MSD start‑fraction influences diffusion estimates.

## Data Flow
1. **Load** `nist_refs.json` → dictionary of experimental `D_exp`.  
2. **Run** simulations → raw `.xtc` files under `data/raw/simulations/`.  
3. **Analyze** each trajectory → append a row to `diffusion_results.csv`.  
4. **Bootstrap** MAE across seeds → write `bootstrap_stats.json`.  
5. **Sensitivity** sweep → write `sensitivity_report.json`.  
6. **Report** reads the two JSON files (and the CSV) to produce figures/tables in `results/`.

All transformations write new files; original raw data remain untouched, satisfying Constitution III.

---
