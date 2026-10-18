# Data Model: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Overview
The project moves data through three explicit models, each persisted to disk in a validated format. All models are described by JSON Schema contracts located in `contracts/`.

### 1. `diffusion_results`
* **Location**: `data/processed/diffusion_results.csv`  
* **Purpose**: Stores per‑trajectory diffusion analysis results, including the MSD linear‑fit quality and the MAE against experimental data.  
* **Key Fields**: `solvent`, `duration_ns`, `seed`, `msd_slope`, `r_squared`, `d_calc_m2_s`, `d_scaled_m2_s` (if scaling applied), `mae`, `status`.  

### 2. `bootstrap_stats`
* **Location**: `data/processed/bootstrap_stats.json`  
* **Purpose**: Summarizes bootstrap resampling of MAE for each simulation duration.  
* **Key Fields**: `duration_ns`, `iterations`, `mean_mae`, `ci_lower`, `ci_upper`, `convergence_check`, `n_seeds`.  

### 3. `sensitivity_report`
* **Location**: `data/processed/sensitivity_report.json`  
* **Purpose**: Records the diffusion coefficients obtained when varying the MSD start‑time fraction, and the resulting coefficient of variation (CV).  
* **Key Fields**: `solvent`, `duration_ns`, `start_fraction`, `d_value`, `variance_pct`.  

## Data Flow

1. **Load** `nist_refs.json` → in‑memory dict.  
2. **Run** simulations → trajectory files (`*.xtc`, `*.pdb`) in `data/raw/simulations/`.  
3. **Analyze** trajectories → generate rows for `diffusion_results.csv`.  
4. **Bootstrap** MAE values → write one entry per duration to `bootstrap_stats.json`.  
5. **Sensitivity** analysis across start fractions → write entries to `sensitivity_report.json`.  
6. **Report Generation** reads the three processed files to produce figures and tables for the manuscript.

All transformations are pure functions; no in‑place modification of raw files occurs (Constitution III). Checksums are recorded for each raw input file.

---
