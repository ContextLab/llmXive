# Data Model: Quantifying the Information Content of Quantum Entanglement in Many-Body Systems

## Overview

This document defines the data structures, schemas, and flows for the quantum information analysis pipeline. The model supports generating raw wavefunction coefficients (via ED/DMRG), computing metrics, and storing results for statistical analysis.

## Key Entities

### 1. QuantumState
Represents a single configuration of a many-body system.
- **id**: Unique identifier (string).
- **system_type**: Enum: `heisenberg`, `ising`.
- **spin_count**: Integer (10-40).
- **parameters**: Dictionary of Hamiltonian parameters (e.g., `J`, `h`).
- **wavefunction_path**: Path to HDF5/NumPy file (sparse format).
- **timestamp**: ISO 8601 string.
- **generation_method**: Enum: `ed`, `dmrg`.

### 2. EntanglementMetric
Result of the SVD-based entropy calculation.
- **state_id**: Foreign key to QuantumState.
- **entropy_value**: Float (von Neumann entropy).
- **entropy_per_spin**: Float (normalized entropy).
- **singular_values**: Array of floats (sparse, stored for debugging).
- **cut_position**: Integer (location of bipartition).
- **computation_time**: Float (seconds).

### 3. ComplexityMetric
Result of the compression-based complexity estimation.
- **state_id**: Foreign key to QuantumState.
- **compression_ratio_gzip**: Float.
- **compression_ratio_lzma**: Float.
- **compression_ratio_bzip2**: Float.
- **ncd_gzip**: Float (Normalized Compression Distance relative to random baseline).
- **ncd_lzma**: Float.
- **ncd_bzip2**: Float.
- **quantization_bits**: Integer (fixed at 16).
- **raw_size_bytes**: Integer.
- **compressed_size_bytes**: Integer.
- **representation_type**: Enum: `singular_values`, `subsystem_vector`.

### 4. CorrelationResult
Aggregated statistical outcome.
- **dataset_label**: String (e.g., "physical", "random_product", "haar_mixed").
- **correlation_pearson**: Float.
- **correlation_spearman**: Float.
- **p_value_pearson**: Float.
- **p_value_spearman**: Float.
- **partial_corr_n**: Float (Partial correlation controlling for N).
- **ci_lower_95**: Float.
- **ci_upper_95**: Float.
- **n_samples**: Integer.
- **stratification**: String (e.g., "within_N", "partial_N").

## Data Flow

1. **Ingestion**: `data_loader.py` generates or reads raw HDF5/NumPy files -> `QuantumState` objects.
2. **Processing**:
   - `metrics.py` computes `EntanglementMetric` and `ComplexityMetric`.
   - Data is written to `data/processed/metrics.parquet`.
3. **Analysis**: `statistics.py` reads metrics -> computes `CorrelationResult`.
4. **Visualization**: `viz.py` reads `CorrelationResult` and raw metrics -> generates plots.

## Storage Strategy

- **Raw Data**: Stored in `data/raw/` as `.h5` or `.npy` (sparse format). Read-only.
- **Processed Data**: Stored in `data/processed/` as `.parquet` (efficient columnar storage) or `.csv`.
- **Intermediate Files**: Compression artifacts stored in temporary directories (`/tmp/`) and deleted after processing.

## Error Handling

- **NaN/Inf**: If `entropy_value` or `compression_ratio` is NaN/Inf, the record is flagged and excluded from correlation analysis.
- **Insufficient Data**: If valid records < 8, the pipeline exits with `E_DATA_INSUFFICIENT`.