# Data Model: Network Topology Energy Transfer in Spin Systems

## Overview

This document defines the data structures, schemas, and relationships for the project. All data artifacts must conform to the schemas defined in `contracts/`.

## Entities

### 1. NetworkGraph
Represents a single synthetic graph.
- **Attributes**:
    - `graph_id`: Unique string identifier (UUID).
    - `topology_type`: Enum ["erdos_renyi", "scale_free", "small_world"].
    - `node_count`: Integer.
    - `edge_count`: Integer.
    - `clustering_coefficient`: Float (0.0 - 1.0).
    - `average_path_length`: Float (or `null` if disconnected).
    - `degree_distribution_params`: Dict (e.g., `{"gamma": 2.5}` for SF, `{"p": 0.05}` for ER).
    - `generation_seed`: Integer.
    - `generation_algorithm`: String (e.g., `nx.watts_strogatz_graph`).
    - `status`: Enum ["valid", "disconnected_retry_exhausted", "clustering_deviation"].

### 2. ExcitationState
Snapshot of energy density at time $t$.
- **Attributes**:
    - `time_step`: Integer.
    - `energy_density`: Array of Floats (length = node_count).
    - `spatial_variance`: Float.
    - `total_energy`: Float (conservation check).

### 3. SimulationRun
Result of one simulation instance.
- **Attributes**:
    - `run_id`: UUID.
    - `graph_id`: FK to NetworkGraph.
    - `seed_node_id`: Integer.
    - `random_seed`: Integer.
    - `total_time_steps`: Integer.
    - `diffusion_rate`: Float (slope of spatial variance over time).
    - `runtime_duration_seconds`: Float.
    - `status`: Enum ["success", "divergence", "timeout"].
    - `energy_profile`: Array of ExcitationState (or path to large file if too big, but for <1000 nodes, in-memory is fine).

### 4. AnalysisResult
Aggregated statistical findings.
- **Attributes**:
    - `analysis_id`: UUID.
    - `regression_model`: String (e.g., "OLS").
    - `coefficients`: Dict (metric -> beta).
    - `p_values`: Dict (metric -> p).
    - `corrected_p_values`: Dict (metric -> p_adj).
    - `r_squared`: Float.
    - `anova_f_statistic`: Float (or `null`).
    - `anova_p_value`: Float (or `null`).
    - `effect_sizes`: Dict.
    - `multiple_comparison_method`: String ("BH", "Bonferroni").

## Data Flow

1.  **Generation**: `NetworkGraph` objects are created and saved to `data/raw/global_batch_manifest.json`.
2.  **Simulation**: `SimulationRun` objects are created for each graph and saved to `data/analysis/simulation_results.json`.
3.  **Aggregation**: `AnalysisResult` objects are computed and saved to `data/analysis/aggregated_results.json`.
4.  **Final Report**: `final_results.json` combines key metrics for the paper.

## File Manifest

| File Path | Content | Schema Contract |
|-----------|---------|-----------------|
| `data/raw/global_batch_manifest.json` | List of `NetworkGraph` | `contracts/network_manifest.schema.yaml` |
| `data/analysis/simulation_results.json` | List of `SimulationRun` | `contracts/simulation_results.schema.yaml` |
| `data/analysis/sensitivity_sweep.json` | Sweep results | `contracts/sensitivity_sweep.schema.yaml` |
| `data/analysis/aggregated_results.json` | `AnalysisResult` | `contracts/analysis_results.schema.yaml` |
| `data/analysis/final_results.json` | Summary for paper | `contracts/final_results.schema.yaml` |
