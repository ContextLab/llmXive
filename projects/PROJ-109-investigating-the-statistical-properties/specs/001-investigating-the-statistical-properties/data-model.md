# Data Model: Investigating Statistical Properties of Simulated Dark Matter Halos

## Overview

This document defines the data structures for the dark matter halo analysis pipeline. The model supports ingestion of simulation catalogs, computation of structural metrics, and storage of statistical results.

## Entity Definitions

### 1. Halo (Raw/Processed)
Represents a single dark matter halo from the simulation catalog.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `halo_id` | `int` | Unique identifier for the halo. | Catalog |
| `mass` | `float` | Total mass of the halo ($M_\odot h^{-1}$). | Catalog |
| `particle_count` | `int` | Number of particles in the halo. | Catalog |
| `position` | `List[float]` | 3D position [x, y, z] (Mpc $h^{-1}$). | Catalog |
| `velocity` | `List[float]` | 3D velocity [vx, vy, vz] (km/s). | Catalog |
| `shape_s` | `float` | Shape parameter $c/a$ (0 to 1). | Computed |
| `spin_lambda` | `float` | Dimensionless spin parameter. | Computed |
| `concentration_c` | `float` | NFW concentration parameter. | Computed |
| `overdensity_delta` | `float` | Local overdensity $\Delta$. | Computed |
| `mass_bin` | `str` | Mass bin label (e.g., "1e10-1e11"). | Derived |
| `env_bin` | `str` | Environment bin label ("low", "high"). | Derived |

### 2. MassBin
Stratification by halo mass.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `bin_id` | `str` | Unique label (e.g., "1e10-1e11"). |
| `lower_bound` | `float` | Lower mass bound ($M_\odot h^{-1}$). |
| `upper_bound` | `float` | Upper mass bound. |
| `halo_count` | `int` | Number of halos in bin. |

### 3. EnvironmentBin
Stratification by local overdensity.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `bin_id` | `str` | "low" or "high". |
| `threshold` | `float` | Overdensity threshold ($\Delta = 200$). |
| `halo_count` | `int` | Number of halos in bin. |

### 4. StatisticalResult
Aggregated results of hypothesis tests.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `test_type` | `str` | "KS" or "Spearman". |
| `metric` | `str` | "shape", "spin", "concentration". |
| `bin_comparison` | `str` | "low_vs_high" or "mass_correlation". |
| `p_value_raw` | `float` | Raw p-value. |
| `p_value_corrected` | `float` | FDR/Bonferroni corrected p-value. |
| `effect_size` | `float` | KS statistic or Spearman $\rho$. |
| `significance` | `bool` | True if $p < 0.05$ (corrected). |
| `convergence_rate` | `float` | Percentage of halos with successful NFW fits (SC-004). |

### 5. ConvergenceRate
Tracks the success rate of NFW profile fitting (SC-004).

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `total_halos` | `int` | Total number of halos attempted. |
| `successful_fits` | `int` | Number of halos with successful NFW fits. |
| `rate` | `float` | Percentage of successful fits (0-100). |

## Data Flow

1. **Ingestion**: Raw catalogs (HDF5) → `Halo` (filtered ≥300 particles).
2. **Computation**: `Halo` + Particle Data (via Memory-Mapped Stream) → `shape_s`, `spin_lambda`, `concentration_c`, `overdensity_delta`.
3. **Binning**: `Halo` → `MassBin`, `EnvironmentBin` assignments.
4. **Analysis**: Binned `Halo` data → `StatisticalResult`.
5. **Output**: `StatisticalResult` and `ConvergenceRate` → JSON/CSV.

## Schema Location
Validation schemas are located in `code/contracts/`:
- `code/contracts/halo.schema.yaml`
- `code/contracts/results.schema.yaml`