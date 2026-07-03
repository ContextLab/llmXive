# Data Model: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

## Overview

This document defines the data structures, schemas, and relationships used in the project. All data is stored in `data/` and validated against schemas in `contracts/`.

## Key Entities

### 1. NetworkRealization
Represents a single atomic connectivity graph.
- **Attributes**:
  - `id`: Unique string (UUID).
  - `topology_type`: Enum ["small_world", "scale_free", "random"].
  - `seed`: Integer (random seed used).
  - `cutoff_factor`: Float (multiplier of nearest-neighbor distance).
  - `algorithm`: String (e.g., "Watts-Strogatz").
  - `n_nodes`: Integer.
  - `n_edges`: Integer.
  - `edge_list`: List of tuples (source, target).
  - `is_connected`: Boolean.
  - `composition`: Dict (e.g., {"Si": 0.5, "Ge": 0.5}).
  - `atomic_masses`: List of floats (mass assigned to each node based on composition, independent of topology).
  - `metrics`: Dict (clustering_coeff, avg_path_len, degree_var, spectral_gap, betweenness).
  - **Note**: All generation metadata (cutoff, seed, algorithm, composition) is stored as **top-level keys** in the JSON file to ensure reproducibility (Constitution Principle VII).

### 2. TransportResult
Represents the calculated thermal conductivity.
- **Attributes**:
  - `realization_id`: String (FK to NetworkRealization).
  - `conductivity`: Float (W/mK).
  - `convergence_status`: Enum ["Converged", "Failed", "Retry_Exhausted"].
  - `error_estimate`: Float.
  - `computation_time`: Float (seconds).

### 3. CorrelationAnalysis
Represents the statistical relationship between a metric and conductivity.
- **Attributes**:
  - `metric_name`: String (e.g., "clustering_coeff").
  - `correlation_coeff`: Float (r).
  - `p_value`: Float.
  - `p_value_corrected`: Float (Bonferroni/FDR).
  - `ci_lower`: Float (2.5th percentile).
  - `ci_upper`: Float (97.5th percentile).
  - `r_squared`: Float (for power-law fit).
  - `control_for_geometry`: Boolean (whether geometric descriptors were included).

### 4. NetworkDisorderParameter
Composite metric for SC-005.
- **Attributes**:
  - `realization_id`: String (FK to NetworkRealization).
  - `degree_variance`: Float.
  - `mass_variance`: Float (variance of atomic masses in the realization).
  - `disorder_score`: Float (composite metric, e.g., weighted sum).

## Data Flow

1. **Generation**: `network_generator.py` -> `data/processed/networks/*.json` (includes composition metadata as top-level keys).
2. **Transport**: `solver.py` -> `data/processed/transport/*.csv`
3. **Analysis**: `regressor.py` -> `data/results/correlations/*.json`
4. **Disorder**: `regressor.py` -> `data/results/disorder/*.csv`

## Storage Format

- **Networks**: JSON (structured, human-readable, with top-level metadata keys).
- **Transport Results**: CSV (optimized for analysis).
- **Analysis Results**: JSON (nested structures for CIs).
- **Disorder Parameters**: CSV (for R² calculation).