# Data Model: Normalized Gaps Between Consecutive Squarefree Numbers

## Overview

This document defines the data structures, schemas, and flow for the squarefree gap analysis project. All data is stored locally in `data/` and validated against the schemas in `contracts/`. All data files use the **Parquet** format for efficiency and type safety.

## Entities

### 1. SquarefreeSequence
Ordered list of squarefree integers up to $N$.
- **Attributes**:
  - `id`: Unique run identifier (UUID).
  - `N`: Cutoff value (integer).
  - `count`: Number of squarefree integers found.
  - `sequence_path`: Path to the stored sequence file (Parquet).
  - `generated_at`: Timestamp.
  - `algorithm`: String ("linear_sieve").

### 2. GapDataset
Collection of raw and normalized gaps.
- **Attributes**:
  - `id`: Unique run identifier.
  - `sequence_id`: Reference to SquarefreeSequence.
  - `N`: Cutoff value.
  - `raw_gaps_path`: Path to raw gap array (Parquet).
  - `normalized_gaps_path`: Path to normalized gap array (Parquet).
  - `mean_gap`: Empirical mean of raw gaps.
  - `count`: Number of gaps.
  - `normalized_mean`: Mean of normalized gaps (should be 1.0).

### 3. TestResult
Results of the Lilliefors test.
- **Attributes**:
  - `id`: Unique run identifier.
  - `gap_dataset_id`: Reference to GapDataset.
  - `KS_statistic`: Maximum difference between empirical and theoretical CDF.
  - `p_value`: Monte Carlo p-value.
  - `N_sim`: Number of Monte Carlo resamples.
  - `timestamp`: Time of test.
  - `dataset_type`: "squarefree", "control", or "gamma_control".
  - `N`: Cutoff value.

### 4. ConvergenceAnalysis
Aggregated results across multiple $N$ values.
- **Attributes**:
  - `id`: Unique run identifier.
  - `results`: List of TestResult IDs.
  - `plot_path`: Path to the convergence chart.
  - `summary`: JSON object with trend statistics (e.g., KS * sqrt(N) values).

## Data Flow

1. **Generate**: `sieve.py` creates `SquarefreeSequence` (stored in `data/raw/` as **Parquet**).
2. **Transform**: `gaps.py` reads sequence, computes gaps, stores `GapDataset` (in `data/processed/` as **Parquet**).
3. **Test**: `stats.py` reads gaps, runs Monte Carlo, writes `TestResult` (in `data/processed/` as **JSON**).
4. **Visualize**: `viz.py` reads all results, generates plots (in `data/figures/`).

## File Formats

- **Sequence**: **Parquet** with columns `index` (int64), `value` (int64).
- **Gaps**: **Parquet** with columns `index` (int64), `raw_gap` (int64), `normalized_gap` (float64).
- **Results**: **JSON** with keys `ks_statistic`, `p_value`, `n`, `type`, `n_sim`.
- **Figures**: **PNG** (300 DPI).
