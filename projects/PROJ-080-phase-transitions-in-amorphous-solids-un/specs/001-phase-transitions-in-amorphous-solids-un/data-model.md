# Data Model: Phase Transitions in Amorphous Solids Under Shear Stress

## Overview

This document defines the data structures for the molecular dynamics trajectory processing pipeline. The model supports the ingestion of raw particle positions, the computation of non-affine displacement ($D^2_{min}$), and the storage of statistical analysis results.

## Entity Definitions

### 1. Trajectory
A time-series of particle configurations in a simulation box.
- **Attributes**:
  - `trajectory_id`: Unique identifier (string).
  - `source_dataset`: Name of the source dataset.
  - `total_timesteps`: Integer.
  - `particle_count`: Integer (must be ≤ 100,000).
  - `box_dimensions`: Array of 3 floats (Lx, Ly, Lz).
  - `status`: Enum ("valid", "indeterminate", "corrupted").
  - `label`: Enum ("brittle", "ductile").
    - *Constraint*: Derived from **independent** mechanical response metrics (e.g., total strain at failure), NOT from $D^2_{min}$ distribution or stress-drop shape, to avoid tautological correlation.

### 2. ParticleState
Snapshot of a single particle at a specific timestep.
- **Attributes**:
  - `particle_id`: Integer (0 to N-1).
  - `timestep`: Integer.
  - `position`: Array of 3 floats (x, y, z).
  - `displacement_vector`: Array of 3 floats (dx, dy, dz) relative to previous step.
  - `local_strain`: Array of 6 floats (strain tensor components).
  - `D2_min`: Float (non-affine displacement magnitude).

### 3. GlobalMetric
Aggregate metrics for the entire system at a specific timestep.
- **Attributes**:
  - `timestep`: Integer.
  - `global_stress`: Float (shear stress component, e.g., $\sigma_{xy}$).
  - `global_strain`: Float (applied shear strain).
  - `is_yielding`: Boolean (True if stress drop > 5% detected).
  - `time_to_failure`: Float (timesteps until complete structural collapse).
    - *Constraint*: Defined as an **independent** ground truth metric, NOT a function of the $D^2_{min}$ threshold being tested.

### 4. AnalysisResult
Output of the statistical and predictive analysis.
- **Attributes**:
  - `analysis_id`: Unique identifier.
  - `group_label`: Enum ("brittle", "ductile").
  - `test_type`: Enum ("permutation", "ks_test").
    - *Note*: Defaults to "permutation" due to clustered data.
  - `p_value`: Float.
  - `corrected_p_value`: Float (Bonferroni corrected).
  - `threshold_sweep`: Array of objects (threshold, FPR, FNR).
  - `power_limitation_flag`: Boolean (True if n < 30 trajectories).

## Data Flow

1.  **Ingest**: Raw trajectory files (HDF5/XYZ) are read into `Trajectory` objects.
2.  **Compute**: `ParticleState` and `GlobalMetric` are computed and written to `data/processed/`.
3.  **Aggregate**: `ParticleState` data is aggregated to shear bands (clusters of high $D^2_{min}$).
4.  **Analyze**: Permutation Tests and threshold sweeps are performed, generating `AnalysisResult` objects.
5.  **Store**: Results are saved as JSON/Parquet with checksums.

## Constraints & Validations

- **Particle Count**: `particle_count` ≤ 100,000 (FR-006).
- **Precision**: All floating-point calculations use `float64`.
- **Immutability**: Raw data files are never modified; all derived data is written to new files.
- **Completeness**: If `is_yielding` is False for all timesteps, the trajectory is flagged as "indeterminate".
- **Label Independence**: `label` must be derived from independent metrics, not $D^2_{min}$ distribution.