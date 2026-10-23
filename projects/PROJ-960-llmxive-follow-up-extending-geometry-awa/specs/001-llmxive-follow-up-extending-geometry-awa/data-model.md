# Data Model: Geometry-Aware Representation Denoising for Robust Multi-view 3D Reconstruction

**Feature**: `001-geometry-aware-denoising`  
**Date**: 2026-10-22

## Overview
Defines the persistent data artifacts, schemas, and file‑format conventions used throughout the research pipeline. All schemas are validated against the contract files in `contracts/`.

## Data Flow Diagram
```text
DA3 (raw parquet) ──► 00_extract_features.py ──► Feature Maps (.npy)
      │
      ▼
01_construct_graphs.py ──► Feature Graphs (sparse .npz + .npy)
      │
      ▼
02_spectral_analysis.py ──► Spectral Properties (eigenvalues/eigenvectors/.npy, curvature/.npy)
      │
      ▼
03_optimize_filter.py ──► Filter Parameters (JSON)
      │
      ▼
04_apply_filter.py ──► Filtered Feature Maps (.npy)
      │
      ▼
06_compute_metrics.py ──► Reconstruction Outputs (point clouds .ply, metrics .csv)
      │
      ▼
08_statistical_testing.py ──► Statistical Results (JSON, CSV)
```

## Core Data Structures

### 1. Feature Maps
- **Format**: `.npy` (NumPy binary)  
- **Shape**: `(num_views, channels, H, W)`  
- **Dtype**: `float32`  
- **Location**: `data/processed/feature_maps/`  
- **Schema**: `contracts/feature-map.schema.yaml` (not shown here but enforced).

### 2. Feature Graphs
- **Adjacency**: Sparse CSR matrix saved as `.npz`.  
- **Node Features**: `.npy` with shape `(num_nodes, channels)`.  
- **Metadata Table**: Parquet `data/processed/feature_graphs/graphs.parquet` adhering to `contracts/feature-graph.schema.yaml`.  
- **Key Columns**: `scene_id`, `num_nodes`, `num_edges`, `k`, `adjacency_matrix_path`, `node_features_path`, `is_connected`, `fallback_applied`.

### 3. Spectral Properties
- **Eigenvalues**: `.npy` (shape `(num_eigenmodes,)`).  
- **Eigenvectors**: `.npy` (shape `(num_nodes, num_eigenmodes)`).  
- **Curvature**: `.npy` (shape `(num_nodes,)`).  
- **Summary Table**: Parquet `data/processed/spectral_properties/spectral_analysis.parquet` validated by `contracts/spectral-analysis.schema.yaml`.  
- **Columns** include paths to the three `.npy` files, correlation statistics, and significance flag.

### 4. Reconstruction Outputs
- **Point Clouds**: `.ply` (or `.xyz`) per scene & method.  
- **Metrics Table**: Parquet `data/processed/reconstructions/metrics.parquet` validated by `contracts/reconstruction-output.schema.yaml`.  
- **Columns**: `scene_id`, `method`, `chamfer_distance`, `f_score`, `inference_time_sec`, `peak_memory_mb`, `filter_params`.

### 5. Sensitivity Sweep
- **CSV**: `data/processed/metrics/sensitivity_sweep.csv` (columns: `scene_id`, `k`, `chamfer_distance`, `mse`).  
- **Summary CSV**: `data/processed/metrics/sensitivity_summary.csv` (mean, std, CV per `k`).

### 6. Statistical Testing Results
- **Wilcoxon**: `data/processed/metrics/wilcoxon_results.json`.  
- **Spectral Correlation Summary**: `data/processed/spectral_properties/correlation_summary.csv`.

## Invariants & Validation Rules
1. **Referential Integrity** – Every `_path` field points to an existing file; missing files raise a contract failure.  
2. **Checksums** – All raw files (`data/raw/`) and every intermediate artifact are listed in `data/metadata/checksums.yaml`.  
3. **Deterministic Reproducibility** – Given identical inputs and fixed seeds, the binary content of each artifact is byte‑identical across runs.  
4. **Schema Conformance** – All tables must pass YAML‑defined JSON‑Schema validation before downstream steps execute.

---

