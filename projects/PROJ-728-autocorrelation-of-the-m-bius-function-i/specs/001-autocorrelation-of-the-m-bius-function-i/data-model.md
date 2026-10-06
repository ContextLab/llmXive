# Data Model: Autocorrelation of the Möbius Function in Short Intervals

## Overview

This document defines the data structures, file formats, and schemas used to store the Möbius sequence, statistical results, and visualizations. All data is stored in the `data/` and `outputs/` directories.

## Data Flow

1.  **Input**: None (Algorithmic generation).
2.  **Raw Data**: `data/raw/mobius_array.npy` (The generated $\mu(n)$ sequence).
3.  **Intermediate**: In-memory arrays for sliding windows and permutation results.
4.  **Processed**: `data/processed/autocorrelation_stats.csv` (Aggregated statistics).
5.  **Output**: `outputs/figures/heatmap_*.png` (Visualizations).

## File Specifications

### 1. Möbius Array (Raw)
- **Path**: `data/raw/mobius_array.npy`
- **Format**: NumPy `.npy` (binary).
- **Shape**: `(10000000,)`
- **Dtype**: `int8` (values: -1, 0, 1).
- **Description**: The deterministic sequence $\mu(n)$.
- **Checksum**: SHA-256 (recorded in state file).

### 2. Autocorrelation Statistics (Processed)
- **Path**: `data/processed/autocorrelation_stats.csv`
- **Format**: CSV (Comma Separated Values).
- **Headers**: `interval_start`, `interval_length`, `lag`, `autocorrelation`, `p_value`, `ci_lower`, `ci_upper`, `zero_count`, `sensitivity_flag`, `theoretical_variance`.
- **Description**: One row per (interval, lag) pair. Contains the observed autocorrelation, p-value from permutation test, 95% CI, and metadata.

### 3. Permutation Null Distribution (Processed)
- **Path**: `data/processed/null_distributions.parquet` (or CSV if Parquet is not available, but Parquet is preferred for size).
- **Format**: Parquet.
- **Description**: Stores the raw permuted autocorrelation values for each tested interval/lag to allow re-analysis.
- **Note**: If storage is constrained, only the quantiles (2.5th, 97.5th) are stored in the main CSV, and the raw distribution is discarded after p-value calculation. *Decision*: Store only quantiles in CSV to save space; raw distribution is transient.

## Data Dictionary

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `interval_start` | int | Starting index $k$ of the window in the Möbius sequence. |
| `interval_length` | int | Length $L$ of the window (varying magnitudes). |
| `lag` | int | Lag $h$ ($1 \le h \le L/2$). |
| `autocorrelation` | float | Observed normalized autocorrelation value. |
| `p_value` | float | Two-sided p-value from the permutation test. |
| `ci_lower` | float | 2.5th percentile of the null distribution. |
| `ci_upper` | float | 97.5th percentile of the null distribution. |
| `zero_count` | int | Number of zeros in the specific window. |
| `sensitivity_flag` | string | "stable" or "sensitive" based on FR-007 analysis. |
| `theoretical_variance` | float | Theoretical variance under the Prime Number Theorem (PNT) assumption. Used to distinguish arithmetic structure from random fluctuation. |

## Integrity Constraints

- **Möbius Values**: All values in `mobius_array.npy` MUST be in $\{-1, 0, 1\}$.
- **P-Values**: All `p_value` entries MUST be in $[0, 1]$.
- **Lag Range**: `lag` MUST be $\le interval\_length / 2$.
- **Reproducibility**: The `mobius_array.npy` MUST be identical across runs (deterministic sieve).