# Data Model: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

## Overview
Defines the JSON/CSV schemas for raw defect data, intermediate graph representations, and final statistical results. All schemas are version‑controlled and validated with `jsonschema`.

## Entities

### 1. DefectSample
```yaml
sample_id: string          # Unique identifier
material_type: string      # "graphene", "MoS2", or "other"
defect_coordinates:        # List of [x, y] pairs (float, float)
  - - float
    - float
thermal_conductivity: float   # W/mK
source_dataset: string        # Name of the source dataset
```

### 2. TopologyGraph
```yaml
sample_id: string
node_count: integer
edge_count: integer
clustering_coefficient: float
density_normalized_clustering: float   # Clustering coefficient normalized by defect density (C / ρ)
average_path_length: float   # NaN if disconnected or zero defects
lcc_fraction: float          # Nodes in LCC / total nodes
percolation_threshold: float # Critical distance (nm) where LCC > 0.5
is_connected: boolean
degree_distribution:        # List of [degree, frequency] pairs
  - - integer
    - integer
metadata:
  flags:                     # e.g., ["disconnected", "zero_defects"]
    - string
```

### 3. AnalysisResult
```yaml
metric_name: string
correlation_coefficient: float
p_value: float               # 0 ≤ p ≤ 1
adjusted_p_value: float      # Bonferroni or FDR corrected
confidence_interval:         # [lower, upper] 95% CI
  - float
  - float
regression_model_params: {}  # Model‑specific parameters
regression_r_squared: float
sensitivity_analysis:
  thresholds:                # Tested multipliers
    - float
  correlation_sd: float      # SD of correlation across thresholds
```

## Data Flow
1. **Raw Input** (`DefectSample`) → stored in `data/raw/` (CSV/Parquet).  
2. **Graph Construction** (`DefectSample` → `TopologyGraph`) → `data/processed/graphs/`.  
3. **Metric Enrichment** updates `TopologyGraph` with percolation and density‑normalized fields.  
4. **Statistical Analysis** (`TopologyGraph` collection) → `results/analysis_results.json` (`AnalysisResult`).  

## Hygiene Rules
- **Checksums**: SHA‑256 recorded in `state/` for every raw file.  
- **Immutability**: Raw files never overwritten; derived files receive timestamped names.  
- **Versioning**: Content hash of each artifact stored in `state/`; any change updates the hash entry.

---
