# Data Model: Geometry-Aware Representation Denoising for Robust Multi-view 3D Reconstruction

**Feature**: `001-geometry-aware-denoising`  
**Date**: 2026-09-20

## Overview

This document specifies the data structures, schemas, and file formats for the research pipeline. All intermediate and output data are validated against the contracts defined in `contracts/`.

## Data Flow

```
DA3 Dataset (parquet)
    ↓
[00_extract_features.py]
    ↓
Feature Maps (numpy arrays, shape: [views, channels, H, W])
    ↓
[01_construct_graphs.py]
    ↓
Feature Graphs (sparse adjacency matrices, node features)
    ↓
[02_spectral_analysis.py]
    ↓
Spectral Properties (eigenvalues, eigenvectors, curvature)
    ↓
[03_optimize_filter.py] (validation set)
    ↓
Filter Parameters (λ_c, α)
    ↓
[04_apply_deterministic_filter.py] (test set)
    ↓
Filtered Feature Maps
    ↓
[06_compute_metrics.py]
    ↓
Reconstruction Outputs (point clouds, metrics: CD, F-score, latency)
    ↓
[08_statistical_testing.py]
    ↓
Final Report (tables, figures, statistical summaries)
```

## Core Data Structures

### 1. Feature Maps

**File Format**: `.npy` (numpy binary)  
**Shape**: `(num_views, channels, height, width)`  
**Dtype**: `float32`  
**Source**: GARD encoder output on DA3 scenes  
**Location**: `data/processed/feature_maps/`

**Example**:
```python
import numpy as np
feature_map = np.load('data/processed/feature_maps/scene_001_clean.npy')
# shape: (4, 256, 32, 32)  # 4 views, 256 channels, 32×32 spatial resolution
```

**Validation**: Schema in `contracts/feature-map.schema.yaml` (see below).

### 2. Feature Graphs

**File Format**: Parquet (structured data) with sparse adjacency matrix (HDF5 backup)  
**Schema**: See `contracts/feature-graph.schema.yaml`

**Columns**:
- `scene_id` (str): Unique identifier (e.g., "scene_001").
- `num_nodes` (int): Number of feature vectors.
- `num_edges` (int): Number of edges in the k-NN graph.
- `k` (int): Number of nearest neighbors.
- `adjacency_matrix_path` (str): Path to sparse matrix file (`.npz`).
- `node_features_path` (str): Path to node feature vectors (`.npy`).
- `is_connected` (bool): Whether the graph is a single connected component.
- `fallback_applied` (bool): Whether a fallback strategy (smoothing/k-increase) was used.

**Location**: `data/processed/feature_graphs/graphs.parquet`

**Sparse Matrix Format** (`.npz`):
```python
import scipy.sparse as sp
# Save:
sp.save_npz('adjacency_scene_001.npz', adjacency_csr)
# Load:
adjacency = sp.load_npz('adjacency_scene_001.npz')
```

### 3. Spectral Properties

**File Format**: Parquet (table) + numpy arrays (eigenvalues/eigenvectors)

**Parquet Columns**:
- `scene_id` (str): Unique identifier.
- `eigenvalues_path` (str): Path to eigenvalues array (`.npy`).
- `eigenvectors_path` (str): Path to eigenvectors matrix (`.npy`).
- `curvature_path` (str): Path to curvature estimates (`.npy`).
- `correlation_with_cd` (float): Pearson r for top eigenmode vs. Chamfer Distance.
- `correlation_pvalue` (float): Bonferroni-corrected p-value.
- `is_significant` (bool): Whether correlation meets threshold (p < 0.005).

**Location**: `data/processed/spectral_properties/spectral_analysis.parquet`

**Eigenvalue Array** (`.npy`):
```python
# Shape: (num_nodes,)
eigenvalues = np.load('spectral_properties/eigenvalues_scene_001.npy')
```

**Eigenvector Matrix** (`.npy`):
```python
# Shape: (num_nodes, num_nodes)
eigenvectors = np.load('spectral_properties/eigenvectors_scene_001.npy')
```

### 4. Reconstruction Outputs

**File Format**: Parquet (metrics table) + point clouds (`.ply` or `.xyz`)

**Metrics Table** (`reconstructions/metrics.parquet`):
- `scene_id` (str): Unique identifier.
- `method` (str): "deterministic_filter" or "diffusion_baseline" or "raw_noisy".
- `chamfer_distance` (float): CD against ground truth.
- `f_score` (float): F-score at threshold 0.01.
- `inference_time_sec` (float): Wall-clock latency on CPU.
- `peak_memory_mb` (float): Peak RSS memory usage.
- `filter_params` (str): JSON-encoded parameters (λ_c, α, k) if applicable.

**Location**: `data/processed/reconstructions/metrics.parquet`

**Point Cloud Files** (`.ply`):
```
data/processed/reconstructions/
├── scene_001_deterministic.ply
├── scene_001_diffusion.ply
├── scene_001_raw_noisy.ply
├── scene_001_ground_truth.ply
└── ...
```

### 5. Sensitivity Analysis Results

**File Format**: CSV

**Columns**:
- `k` (int): Number of nearest neighbors.
- `scene_id` (str): Unique identifier.
- `chamfer_distance` (float): CD for this k value.
- `mse` (float): Mean squared error of filtered features.

**Location**: `data/processed/metrics/sensitivity_sweep.csv`

**Summary Statistics** (`sensitivity_summary.csv`):
- `k` (int): Number of nearest neighbors.
- `cd_mean` (float): Mean CD across all test scenes.
- `cd_std` (float): Standard deviation of CD.
- `cd_cv` (float): Coefficient of variation (std / mean).
- `mse_mean` (float): Mean MSE.
- `mse_std` (float): Standard deviation of MSE.
- `mse_cv` (float): Coefficient of variation.

### 6. Statistical Testing Results

**File Format**: JSON + CSV

**Wilcoxon Test Output** (`metrics/wilcoxon_results.json`):
```json
{
  "test_statistic": 42.0,
  "p_value": 0.0312,
  "effect_size_rank_biserial": 0.65,
  "n_pairs": 20,
  "interpretation": "Deterministic filter and diffusion baseline differ significantly (p < 0.05)"
}
```

**Spectral Correlation Summary** (`spectral_properties/correlation_summary.csv`):
- `eigenmode_index` (int): Index of the eigenmode (1–10).
- `pearson_r` (float): Correlation coefficient with CD.
- `p_value_bonferroni` (float): Bonferroni-corrected p-value.
- `is_significant` (bool): Whether p < 0.005.

## Schemas (Contracts)

All schemas are defined in YAML and validated during execution. See `contracts/` directory for the authoritative definitions.

### Key Invariants

1. **Referential Integrity**: Every `*_path` field in a parquet table points to an existing file; broken references are a fatal validation error.
2. **Checksums**: Every raw data file in `data/raw/` and intermediate file in `data/processed/` is checksummed and recorded in `data/metadata/checksums.yaml`.
3. **Lineage**: Every derived file includes a comment or metadata field linking it to its source and the code that produced it.
4. **Determinism**: For a fixed input (same feature maps, same parameters), the output is byte-for-byte identical across runs.

---
