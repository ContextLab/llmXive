# Data Model: Fractal Dimension and Energy Dissipation in Turbulent Flows

## Overview

This document defines the data structures, schemas, and flow for the turbulent flow analysis pipeline. It ensures that all artifacts are traceable, versioned, and compliant with the project constitution.

## Key Entities

### 1. VelocityField
Represents the 3D velocity field data.
- **Attributes**:
  - `u`: 3D array (float64) - x-component
  - `v`: 3D array (float64) - y-component
  - `w`: 3D array (float64) - z-component
  - `re_lambda`: float - Taylor Reynolds number
  - `viscosity`: float - Kinematic viscosity $\nu$
  - `dimensions`: tuple - Grid size (e.g., (512, 512, 512))
  - `checksum`: string - SHA256 of the raw data
  - `snapshot_id`: string - Unique identifier for the time snapshot (for multi-snapshot pooling)

### 2. VorticityIsoSurface
Geometric structure derived from velocity gradients.
- **Attributes**:
  - `threshold`: float - Vorticity threshold (e.g., 3.0 * RMS or absolute value)
  - `threshold_type`: string - "RMS" or "Absolute"
  - `fractal_dimension`: float - Estimated $D_f$
  - `surface_area`: float - Total surface area
  - `voxels_count`: int - Number of voxels above threshold
  - `subdomain_id`: string - Unique identifier for the spatial subdomain
  - `snapshot_id`: string - Link to the source snapshot

### 3. EnergyDissipationMap
3D map of local energy dissipation rates.
- **Attributes**:
  - `epsilon`: 3D array (float64) - $\epsilon$ values
  - `mean_epsilon`: float - Average dissipation
  - `max_epsilon`: float - Maximum dissipation
  - `intermittency_ratio`: float - $\epsilon_{max} / \epsilon_{mean}$
  - `subdomain_id`: string - Unique identifier

### 4. CorrelationResult
Statistical output from the regression analysis.
- **Attributes**:
  - `re_lambda`: float - Reynolds number
  - `threshold_type`: string - "RMS" or "Absolute"
  - `threshold_multiplier`: float - e.g., 3.0 (for RMS) or absolute value (for Absolute)
  - `pearson_r`: float - Correlation coefficient
  - `p_value`: float - Raw p-value from the correlation test
  - `ci_lower`: float - 95% CI lower bound
  - `ci_upper`: float - 95% CI upper bound
  - `sample_size`: int - $n$
  - `method`: string - "Bonferroni" or "Benjamini-Hochberg"
  - `adjusted_p_value`: float - Corrected p-value
  - `null_model_r`: float - Correlation coefficient from the Phase-Shifted DNS null model
  - `robustness_check_passed`: boolean - True if correlation holds across both RMS and Absolute methods

## Data Flow

1. **Input**: Raw DNS data (or Phase-Shifted DNS) $\rightarrow$ `VelocityField`.
2. **Processing**:
   - `VelocityField` $\rightarrow$ `Gradients` $\rightarrow$ `Vorticity` & `StrainRate`.
   - `Vorticity` $\rightarrow$ `VorticityIsoSurface` (via Box-Counting) for multiple thresholds.
   - `StrainRate` $\rightarrow$ `EnergyDissipationMap`.
3. **Aggregation**:
   - `VorticityIsoSurface` + `EnergyDissipationMap` $\rightarrow$ `CorrelationResult` (per snapshot).
   - Aggregate results across snapshots.
4. **Output**: `CorrelationResult` stored in `data/results/correlation_results.csv`.

## Storage Strategy

- **Raw Data**: Stored in `data/raw/` with checksums.
- **Intermediate**: Stored in `data/intermediate/` (e.g., `gradients.npy`, `vorticity.npy`).
- **Final Results**: Stored in `data/results/` (CSV/JSON).
- **Artifacts**: All files are versioned with content hashes in the state file.

## Constraints

- **Memory**: No single array > 2 GB. Use chunking for 512³ grids.
- **Precision**: All floating-point calculations in `float64`.
- **Reproducibility**: Random seeds fixed at the start of the pipeline.
- **Independence**: Subdomains must be separated by $\ge 10 \lambda$ (achieved via multi-snapshot pooling).