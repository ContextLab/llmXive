# Data Model: llmXive follow-up: extending "Rethinking Cross-Layer Information Routing in Diffusion Transformers"

## Overview

This document defines the data structures, schemas, and storage formats used in the `001-llmxive-static-routing` feature. All data is stored in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/data/`.

## Data Flow

1. **Input**: ImageNet validation images (streamed, then cached into Trace Set and Benchmark Set).
2. **Intermediate**: Aggregated per-image routing patterns (traced from dynamic model, one-by-one).
3. **Derived**: Static routing map (clustered/averaged patterns).
4. **Output**: Benchmark results (latency, FID, statistics).

## Schemas

### 1. Trace Patterns (`trace_patterns.npy`)

- **Description**: The aggregated routing patterns for the 60 Trace Set images. Each entry is the mean/mode of the routing vectors across timesteps for a single image.
- **Format**: NumPy Array (`.npy`).
- **Shape**: `[60, N_blocks, N_routes]`
  - `60`: Number of trace images.
  - `N_blocks`: ~28 (SiT-XL/2).
  - `N_routes`: Variable (depends on DAR config, e.g., 8-16).
- **Data Type**: `float32`
- **Storage**: `data/routing_cache/trace_patterns.npy`

### 2. Canonical Routing Map (`static_routing_map.pt`)

- **Description**: The derived static weights. Either a per-block vector (if distinct phases found) or a global average.
- **Format**: PyTorch Tensor (`.pt`).
- **Shape**: `[N_blocks, N_routes]`
- **Data Type**: `torch.float32`
- **Storage**: `data/routing_cache/static_routing_map.pt`

### 3. Benchmark Results (`benchmark_results.csv`)

- **Description**: Aggregated metrics from the comparison of dynamic vs. static models.
- **Format**: CSV.
- **Columns**:
  - `run_id`: Integer (1-5 for the 5 seeds).
  - `model_type`: String ("dynamic" or "static").
  - `seed`: Integer (random seed used).
  - `latency_seconds`: Float (time to generate a set of images).
  - `fid_score`: Float (FID score).
- **Storage**: `data/benchmarks/benchmark_results.csv`

### 4. Sensitivity Analysis (`sensitivity_analysis.json`)

- **Description**: Results of the threshold sweep.
- **Format**: JSON.
- **Structure**:
  ```json
  {
    "thresholds": [0.01, 0.05, 0.1],
    "results": [
      {
        "threshold": 0.01,
        "fid_static": 12.34,
        "fid_dynamic": 12.10,
        "diff": 0.24
      },
      ...
    ]
  }
  ```
- **Storage**: `data/benchmarks/sensitivity_analysis.json`

## Data Hygiene

- **Checksums**: All files in `data/` are checksummed (SHA-256) and recorded in `state/...yaml`.
- **Immutability**: Raw routing patterns are never modified. Derivations (static map) are written to new files.
- **PII**: No PII is present (ImageNet validation set is public and anonymized).