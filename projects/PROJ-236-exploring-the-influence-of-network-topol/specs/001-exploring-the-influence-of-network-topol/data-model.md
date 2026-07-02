# Data Model: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

## Entities & Relationships

### 1. NetworkRealization
Represents a single generated atomic connectivity graph.
- **Attributes**:
  - `id`: Unique identifier (UUID).
  - `topology_type`: Enum {`small_world`, `scale_free`, `random`}.
  - `node_count`: Integer (N).
  - `edge_count`: Integer (M).
  - `cutoff_factor`: Float (multiplier of nearest-neighbor distance).
  - `seed`: Integer (random seed used).
  - `metrics`: Dict {`clustering_coeff`, `avg_path_length`, `degree_variance`, `spectral_gap`, `betweenness_centrality_mean`}.
  - `is_valid`: Boolean (connected? yes/no).
  - `exclusion_reason`: String (if invalid).

### 2. TransportResult
Represents the calculated thermal conductivity for a realization.
- **Attributes**:
  - `realization_id`: FK to `NetworkRealization.id`.
  - `thermal_conductivity`: Float (W/m·K).
  - `convergence_status`: Enum {`converged`, `failed`, `timeout`}.
  - `force_constant_method`: String (e.g., `bond_distance_approx`).
  - `runtime_seconds`: Float.

### 3. CorrelationAnalysis
Represents the statistical summary of the relationship between a metric and conductivity.
- **Attributes**:
  - `metric_name`: String (e.g., `clustering_coeff`).
  - `topology_type`: String (or `all`).
  - `correlation_coefficient`: Float (r).
  - `p_value`: Float (raw).
  - `p_value_corrected`: Float (FDR).
  - `slope`: Float.
  - `ci_lower`: Float (Lower bound of 95% bootstrap CI).
  - `ci_upper`: Float (Upper bound of 95% bootstrap CI).
  - `ci_width`: Float (Calculated as `ci_upper - ci_lower`, required for SC-004).
  - `r_squared`: Float (R² of the power-law fit between disorder parameters and conductivity, required for SC-005).

## File Formats

### `data/processed/ensembles.jsonl`
JSON Lines file where each line is a `NetworkRealization` object.
```json
{"id": "uuid-1", "topology_type": "small_world", "node_count": 1000, "metrics": {"clustering_coeff": 0.45, ...}, "is_valid": true}
```

### `data/results/transport_results.csv`
CSV with `realization_id`, `thermal_conductivity`, `convergence_status`.

### `data/results/correlation_analysis.json`
JSON object containing the `CorrelationAnalysis` results.

## Data Flow

1. **Generate**: `generate_networks.py` reads `config.yaml` -> writes `data/processed/ensembles.jsonl`.
2. **Compute**: `compute_transport.py` reads `ensembles.jsonl` -> writes `data/results/transport_results.csv`.
3. **Analyze**: `analyze_correlations.py` reads both -> writes `data/results/correlation_analysis.json`.