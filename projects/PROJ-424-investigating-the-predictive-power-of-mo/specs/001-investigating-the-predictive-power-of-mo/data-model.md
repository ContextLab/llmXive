# Data Model: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Overview

This document defines the data structures used to store simulation results, experimental benchmarks, and statistical outputs. All data is stored in CSV/JSON format under `data/` with checksums.

## Entities

### 1. Simulation Run
Represents a single MD execution.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique identifier (e.g., `water_1ns_001`) |
| `solvent` | string | Solvent name (water, ethanol, acetone) |
| `timescale_ns` | float | Target duration (1.0, 5.0, 10.0) |
| `force_field` | string | Force field used (e.g., `martini3`) |
| `temperature_k` | float | Simulation temperature |
| `status` | string | `success`, `failed`, `invalid` |
| `r_squared` | float | Linearity of MSD fit ($R^2$). **Threshold**: 0.95 (Constitution). |
| `diffusion_coefficient` | float | Calculated D (m²/s) *before* scaling |
| `scaling_factor` | float | Solvent-specific scaling factor applied |
| `diffusion_coefficient_scaled` | float | Calculated D (m²/s) *after* scaling |
| `error_flag` | string | Reason for invalidation (if any) |

### 2. Experimental Reference
Ground truth values from NIST.

| Field | Type | Description |
|-------|------|-------------|
| `solvent` | string | Solvent name |
| `temperature_k` | float | Reference temperature |
| `diffusion_coefficient` | float | Experimental D (m²/s) |
| `source` | string | "NIST_Curated" |
| `checksum` | string | SHA-256 of reference file |

### 3. Prediction Metric
Error analysis for each run.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Link to Simulation Run |
| `solvent` | string | Solvent name |
| `timescale_ns` | float | Duration |
| `d_pred` | float | Predicted D (scaled) |
| `d_exp` | float | Experimental D |
| `mae` | float | Absolute error (|d_pred - d_exp|) |
| `valid` | bool | Whether run passed $R^2 \ge 0.95$ check |

### 4. Bootstrap Statistics
Confidence intervals for MAE.

| Field | Type | Description |
|-------|------|-------------|
| `solvent` | string | Solvent name |
| `timescale_ns` | float | Duration |
| `mean_mae` | float | Mean MAE across bootstrap |
| `ci_lower_95` | float | Lower 95% CI |
| `ci_upper_95` | float | Upper 95% CI |
| `n_iterations` | int | Number of bootstrap iterations |

### 5. Sensitivity Report
Variance from regression start time sweep.

| Field | Type | Description |
|-------|------|-------------|
| `solvent` | string | Solvent name |
| `timescale_ns` | float | Duration |
| `start_time_pct` | float | Regression start time (0.1, 0.2, 0.3) |
| `diffusion_coefficient` | float | D calculated at this start time |
| `variance` | float | Variance across start times |
| `robust` | bool | `True` if variance < 5% |

## Data Flow

1. **Raw**: `data/raw/nist_refs.json` (curated), `data/raw/topologies/*.gro`
2. **Interim**: `data/interim/simulation_logs/*.log` (MD output)
3. **Processed**: 
   - `data/processed/msd_curves.csv`
   - `data/processed/diffusion_results.csv` (includes scaled values)
   - `data/processed/bootstrap_stats.csv`
   - `data/processed/sensitivity_report.csv`
4. **Final**: `data/processed/summary_table.csv`, `data/processed/timescale_accuracy_plot.png`

## Checksums

All files in `data/raw/` and `data/processed/` must be checksummed and recorded in `state/projects/PROJ-424-...yaml`.