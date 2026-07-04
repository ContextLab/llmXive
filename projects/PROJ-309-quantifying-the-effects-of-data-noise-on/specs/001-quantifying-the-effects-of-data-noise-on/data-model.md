# Data Model: Quantifying the Effects of Data Noise on Dynamical Systems Reconstruction

## Overview

This document defines the data structures, schemas, and file formats used in the project. All data is stored in local files (`data/raw`, `data/processed`, `data/results`) with checksums recorded for reproducibility.

## Entities

### 1. ChaoticTrajectory
Represents a clean time-series from a chaotic system.

**Attributes**:
- `trajectory_id`: Unique identifier (UUID).
- `system_type`: Enum ["Lorenz", "Rössler"].
- `parameters`: Dictionary of system parameters (e.g., `{"sigma": 10, "rho": 28, "beta": 8/3}`).
- `time_points`: 1D array of time values.
- `state_values`: 2D array (3 × N) of state variables (x, y, z).
- `ground_truth_metrics`: Dictionary of pre-computed metrics (correlation_dim, lyapunov_exp, fnn_rate).
- `checksum`: SHA-256 hash of the file content.
- `replicate_id`: Integer (1-10) identifying the specific replicate of this trajectory.

**File Format**: `.npz` (NumPy).
**Location**: `data/raw/clean/<system_type>_<trajectory_id>.npz`
*Note: The filename includes the `trajectory_id` (UUID) to ensure unique identification. The `replicate_id` is stored within the file metadata.*

### 2. NoisyTrajectory
Represents a trajectory with injected noise.

**Attributes**:
- `source_trajectory_id`: Reference to the clean trajectory (UUID).
- `noise_type`: Enum ["Gaussian", "Quantization"].
- `snr_db`: Target SNR in dB.
- `quantization_bits`: Integer (4-16) if noise_type is Quantization.
- `noisy_values`: 2D array (3 × N).
- `measured_snr`: Actual SNR measured post-injection.
- `checksum`: SHA-256 hash.
- `replicate_id`: Integer (1-10) identifying the specific replicate.

**File Format**: `.npz`.
**Location**: `data/raw/noisy/<system_type>_<noise_type>_<snr>_<replicate_id>.npz`
*Note: The filename includes `replicate_id` to distinguish multiple replicates of the same system/noise/SNR combination.*

### 3. MetricResult
Represents a computed metric for a specific trajectory.

**Attributes**:
- `trajectory_id`: Reference to the trajectory (UUID).
- `metric_name`: Enum ["correlation_dimension", "lyapunov_exponent", "fnn_rate"].
- `value`: Float.
- `error_percent`: Float (calculated against ground truth).
- `algorithm_version`: String (e.g., "GP-v1", "Rosenstein-v1").
- `replicate_id`: Integer (1-10) identifying the replicate source. **Critical for aggregation.**

**File Format**: `.csv` (aggregated) or `.json` (individual).
**Location**: `data/processed/metrics/<trajectory_id>_<metric>.csv`

### 4. AnalysisResult
Aggregated results for error analysis and visualization.

**Attributes**:
- `snr_db`: Float.
- `noise_type`: String.
- `metric_name`: String.
- `mean_error`: Float.
- `std_error`: Float.
- `n_replicates`: Integer.
- `critical_threshold_flag`: Boolean (if error > 30%).

**File Format**: `.csv`.
**Location**: `data/results/error_vs_snr.csv`

## Data Flow

1.  **Generation**: `code/generators.py` → `data/raw/clean/` (Clean Trajectories, includes `trajectory_id` and `replicate_id` in metadata).
2.  **Noise Injection**: `code/noise.py` → `data/raw/noisy/` (Noisy Trajectories, includes `replicate_id` in filename).
3.  **Metric Computation**: `code/metrics.py` → `data/processed/metrics/` (Metric Results, includes `replicate_id`).
4.  **Error Analysis**: `code/analysis.py` → `data/results/error_vs_snr.csv` (Analysis Results).
5.  **Visualization**: `code/visualize.py` → `data/results/plots/` (PNG files).

## Checksumming & Hygiene

-   Every file written to `data/` is checksummed using SHA-256.
-   Checksums are recorded in `state/projects/PROJ-309-quantifying-the-effects-of-data-noise-on.yaml` under `artifact_hashes`.
-   Raw data is never modified; derivations create new files.