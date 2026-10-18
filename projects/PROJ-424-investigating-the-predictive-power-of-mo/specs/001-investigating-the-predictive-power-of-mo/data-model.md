# Data Model: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Overview

Three persisted models, each validated against a contract in `contracts/`.

### 1. `diffusion_results`
- **Location**: `data/processed/diffusion_results.csv` (one row per trajectory)
- **Fields**: `solvent`, `duration_ns`, `seed`, `msd_slope`, `r_squared`, `d_calc_m2_s`, `d_scaled_m2_s` (equal to `d_calc_m2_s`; no CG scaling is applied in this atomistic workflow — retained per spec §6), `mae`, `status`.

### 2. `bootstrap_stats`
- **Location**: `data/processed/bootstrap_stats.json` (one entry per solvent × duration, plus paired‑test results)
- **Fields**: `solvent`, `duration_ns`, `iterations` (fixed 1000), `mean_mae`, `ci_lower`, `ci_upper`, `n_seeds`, and a top‑level `paired_test` block with `solvent`, `mae_1ns`, `mae_10ns`, `mean_difference`, `p_value`, **and** an optional `granularity_note` string explaining the statistical granularity limitation when seed counts are low.

### 3. `sensitivity_report`
- **Location**: `data/processed/sensitivity_report.json`
- **Fields**: `solvent`, `duration_ns`, `start_fraction` (0.1, 0.2, 0.3), `variance_pct` (must be < 5 % per the implied sensitivity criterion), and any additional descriptive notes.

## Data Flow

1. Load `nist_refs.json` → validated dict (checksum recorded).
2. Run simulations → `data/raw/simulations/*.xtc` (+ logs with wall‑clock times).
3. MSD + fit + R² gate **and** log‑log slope check → rows in `diffusion_results.csv`.
4. Bootstrap of MAE + descriptive paired comparison → `bootstrap_stats.json`.
5. **Sensitivity analysis** (start‑fraction sweep) → `sensitivity_report.json`.
6. `report.py` reads only the two processed files (`diffusion_results.csv`, `bootstrap_stats.json`) and the sensitivity report to produce figures/tables (Constitution IV).

Raw files are never modified in place; all derivations write new files (Constitution III).
