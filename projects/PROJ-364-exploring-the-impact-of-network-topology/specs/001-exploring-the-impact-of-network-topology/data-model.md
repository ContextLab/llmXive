# Data Model: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

## Overview

This document defines the data structures used throughout the pipeline: raw defect coordinate records, intermediate graph representations, and final statistical analysis results. All files are JSON or CSV for portability and reproducibility.

## Key Entities

### 1. DefectSample
Represents a single physical sample.

```yaml
sample_id: string          # Unique identifier
material_type: string      # "graphene", "MoS2", etc.
defect_coordinates: list   # List of [x, y] pairs (float)
thermal_conductivity: float # Bulk thermal conductivity (W/mK)
source_dataset: string     # Name of the source dataset
```

### 2. TopologyGraph
Represents the network abstraction of a sample.

```yaml
sample_id: string
node_count: integer
edge_count: integer
clustering_coefficient: float
average_path_length: float  # NaN if disconnected or zero defects
lcc_fraction: float         # Nodes in LCC / total nodes
percolation_threshold: float # Critical distance where LCC > 0.5 (nm)
is_connected: boolean
degree_distribution: list   # List of [degree, frequency] pairs
metadata: object            # Flags (e.g., "disconnected", "zero_defects")
```

### 3. AnalysisResult
Statistical output for a metric (or PCA component) versus thermal conductivity.

```yaml
metric_name: string         # e.g., "clustering_coefficient" or "PC1"
correlation_coefficient: float
p_value: float
adjusted_p_value: float     # Bonferroni or FDR corrected
confidence_interval: list   # [lower, upper] 95% CI
regression_model_params: object
regression_r_squared: float
sensitivity_analysis: object # Results for 1.5x, 2.0x, 2.5x thresholds
```

## Data Flow

1. **Raw Input** (`DefectSample`) → CSV/Parquet in `data/raw/`.
2. **Graph Construction** (`DefectSample` → `TopologyGraph`) stored in `data/processed/graphs/`.
3. **Metric Calculation** (`TopologyGraph`) → enriched `TopologyGraph` (adds percolation, density‑normalized metrics).
4. **Statistical Analysis** (`TopologyGraph` collection) → `AnalysisResult` records in `results/analysis_results.json`.

## Data Hygiene

- **Checksums**: All raw files in `data/raw/` are SHA‑256 checksummed; hashes recorded in `state/`.  
- **Immutability**: Raw files are never overwritten; derived artifacts receive new filenames with timestamps.  
- **Versioning**: Every artifact’s content hash is stored in `state/`; any change triggers a new hash entry.