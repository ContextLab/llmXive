# Data Model: Quantifying the Effects of Data Noise on Dynamical Systems Reconstruction

## Overview

This document defines the data structures for the noise-degradation analysis pipeline. The model is designed to be immutable, checksum-verified, and directly mappable to the CSV output schema.

## Core Entities

### 1. ChaoticTrajectory
Represents the ground-truth state of a chaotic system.

- **Attributes**:
  - `trajectory_id`: Unique identifier (UUID).
  - `system_type`: Enum (`LORENZ`, `ROSSLER`).
  - `parameters`: Dict of system parameters (e.g., `{"sigma": 10, "rho": 28}`).
  - `time_steps`: Array of float64 (time points).
  - `state_values`: 2D array (3 × N) of float64 (x, y, z).
  - `ground_truth_metrics`: Dict containing literature-verified values for $D_2$ and $\lambda_1$ (for validation only).
  - `checksum`: SHA-256 hash of the raw data.

### 2. NoisyTrajectory
Represents a trajectory with injected noise.

- **Attributes**:
  - `source_trajectory_id`: FK to `ChaoticTrajectory`.
  - `noise_type`: Enum (`GAUSSIAN`, `QUANTIZATION`).
  - `snr_db`: Float (target SNR in dB).
  - `quantization_bits`: Int (if noise_type is QUANTIZATION, else null).
  - `noisy_values`: 2D array (3 × N) of float64.
  - `measured_snr_db`: Float (actual SNR calculated post-injection).
  - `checksum`: SHA-256 hash.

### 3. MetricResult
Represents a computed metric for a specific trajectory.

- **Attributes**:
  - `result_id`: Unique identifier.
  - `trajectory_id`: FK to `NoisyTrajectory`.
  - `metric_name`: Enum (`CORRELATION_DIMENSION`, `LYAPUNOV_EXPONENT`, `FNN_RATE`).
  - `computed_value`: Float.
  - `ground_truth_value`: Float (from the **mean of clean realizations**, not literature).
  - `error_percent`: Float.
  - `status`: Enum (`SUCCESS`, `FAILED`, `INSUFFICIENT_DATA`).

### 4. LookupTableEntry
Aggregated result for a specific SNR/Noise/Metric combination.

- **Attributes**:
  - `snr_db`: Float.
  - `noise_type`: String.
  - `metric_name`: String.
  - `mean_error_percent`: Float.
  - `std_error_percent`: Float.
  - `n_samples`: Int.
  - `critical_threshold_flag`: Boolean (True if mean error > 30%).

## Data Flow

1.  **Generation**: `ChaoticTrajectory` created (N=50 per system) → Checksummed → Saved to `data/raw/` as `.npy`.
2.  **Noise Injection**: `NoisyTrajectory` created from source → Checksummed → Saved to `data/processed/` as `.npy`.
3.  **Metric Computation**: `MetricResult` created → Saved to `data/processed/metrics/` as `.json`.
4.  **Aggregation**: `LookupTableEntry` created from `MetricResult` using **pandas** for statistical aggregation (mean, std, CI) → Exported to `results/lookup_table.csv`.

## Storage Format

- **Raw/Processed Data**: `.npy` (NumPy binary) for efficiency, accompanied by `.json` metadata files.
- **Results**: `.csv` for portability and `lookup_table.schema.yaml` validation. **Pandas** is used for all aggregation and CSV export operations.
- **Logs**: `.log` files with timestamped events and checksums.