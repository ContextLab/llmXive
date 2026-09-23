# Data Model: Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

## 1. Entities & Relationships

### 1.1 AtomicSnapshot
Represents a single MD configuration (real or synthetic).
- **Attributes**:
  - `snapshot_id`: Unique identifier (string).
  - `alloy_type`: Enum ["Cu-Ni", "Au-Ag"].
  - `atomic_positions`: List of 3D vectors (float).
  - `species`: List of strings (e.g., "Cu", "Ni").
  - `thermal_conductivity`: Float (W/m·K).
  - `source`: Enum ["real", "synthetic"].
  - `timestamp`: ISO8601 timestamp.

### 1.2 DefectGraph
Represents the topological structure of disorder derived from an `AtomicSnapshot`.
- **Attributes**:
  - `graph_id`: Unique identifier (string).
  - `snapshot_id`: Foreign key to `AtomicSnapshot`.
  - `nodes`: List of node indices (int).
  - `edges`: List of tuples (int, int).
  - `metrics`: Dictionary of computed metrics (float).
    - `clustering_coefficient`: Float.
    - `mean_degree`: Float.
    - `degree_variance`: Float.
    - `percolation_threshold`: Float or NaN.
  - `component_count`: Integer.

### 1.3 CorrelationResult
Represents the statistical outcome of the analysis.
- **Attributes**:
  - `analysis_id`: Unique identifier (string).
  - `metric_name`: String (e.g., "clustering_coefficient").
  - `correlation_coefficient`: Float (Pearson/Spearman).
  - `p_value_raw`: Float.
  - `p_value_corrected`: Float (Bonferroni).
  - `significant`: Boolean.
  - `effect_size`: Float.

## 2. Data Flow

1. **Ingestion**: `AtomicSnapshot` created from file or synthetic generator.
2. **Construction**: `DefectGraph` built from `AtomicSnapshot`.
3. **Extraction**: Metrics computed and stored in `DefectGraph`.
4. **Analysis**: `CorrelationResult` computed from `DefectGraph` metrics and `AtomicSnapshot` thermal conductivity.
5. **Visualization**: Plots generated from `CorrelationResult`.

## 3. Storage Format

- **Raw Data**: `data/raw/snapshots.parquet` (if real data exists) or `data/raw/synthetic_snapshots.parquet`.
- **Processed Data**: `data/processed/graphs.parquet`, `data/processed/metrics.parquet`.
- **Results**: `data/processed/correlations.json`, `data/processed/heatmaps.png`.

## 4. Constraints & Validations

- **Species**: Must be one of the expected alloy elements.
- **Coordinates**: Must be within the simulation box bounds.
- **Thermal Conductivity**: Must be > 0.
- **Graph**: Must be undirected; no self-loops.
- **Metrics**: Must be finite (NaN allowed for undefined cases).