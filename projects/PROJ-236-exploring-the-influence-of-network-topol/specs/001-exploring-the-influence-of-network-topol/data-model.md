# Data Model: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

## 1. Overview

This document defines the data structures used to represent network realizations, transport results, and correlation analyses. All data is stored in `data/processed/` in JSON or YAML format, with checksums recorded in `data/checksums.json`.

## 2. Core Entities

### 2.1 NetworkRealization
Represents a single instance of an atomic connectivity graph.
*   **Storage**: `data/processed/network_realizations/realization_<id>.yaml`
*   **Compliance**: Stores `construction_params` (cutoff, algorithm, seed) to satisfy Constitution Principle VII.

```yaml
id: string (UUID)
seed: integer
topology_type: enum [Small-World, Scale-Free, Random]
atomic_structure:
  lattice_type: string
  num_atoms: integer
  displacement_sigma: float
  relaxation_method: string # e.g., "Langevin_EAM"
graph:
  num_nodes: integer
  num_edges: integer
  adjacency_matrix_path: string (relative path to data/processed/networks/)
  is_connected: boolean
topological_metrics:
  clustering_coefficient: float
  average_path_length: float
  degree_variance: float
  spectral_gap: float
  betweenness_centrality_mean: float
  betweenness_centrality_std: float
construction_params:
  distance_cutoff_factor: float
  algorithm_seed: integer
  cutoff_sweep_range: string # e.g., "1.0-2.0"
validation_status: enum [Valid, Invalid_Disconnected, Invalid_DegDist]
```

### 2.2 TransportResult
Represents the calculated thermal conductivity for a specific realization.

```yaml
realization_id: string (UUID, FK to NetworkRealization)
method: enum [Green-Kubo, Fallback_Scipy]
thermal_conductivity: float (W/mK)
error_estimate: float
convergence_status: enum [Converged, Failed_Retry_Exhausted, Failed_Singular]
simulation_time_seconds: float
force_constant_source: enum [EAM, Ab-Initio]
regime_flag: enum [Diffusive, Ballistic_Flagged] # Added for stratified analysis
```

### 2.3 CorrelationAnalysis
Represents the statistical relationship between a metric and conductivity.

```yaml
metric_name: string
ensemble_type: enum [Small-World, Scale-Free, Random, All]
correlation_coefficient: float
p_value_raw: float
p_value_corrected: float
confidence_interval:
  lower: float
  upper: float
  width: float # Added for SC-004 validation
bootstrap_iterations: integer
regression_r_squared: float
power_law_r_squared: float # Added for SC-005
power_law_exponent: float # Added for SC-005
significance_flag: boolean (p_corrected < 0.05)
ci_width_target_met: boolean # Added for SC-004
```

## 3. File Organization

```text
data/
├── raw/
│   └── atomic_structures/
│       └── lattice_seed_42.json
├── processed/
│   ├── network_realizations/
│   │   ├── realization_001.yaml
│   │   ├── realization_002.yaml
│   │   └── ...
│   ├── transport_results/
│   │   ├── result_001.yaml
│   │   └── ...
│   └── analysis/
│       ├── correlation_summary.yaml
│       ├── power_analysis.yaml
│       └── sensitivity_report.yaml
└── checksums.json
```

## 4. Data Integrity

*   **Immutability**: Raw data is never modified. Derived files (e.g., `transport_results`) are written once.
*   **Checksums**: Every file in `data/processed/` is checksummed (SHA-256) and recorded in `checksums.json`.
*   **Validation**: Scripts must validate that `realization_id` in `TransportResult` exists in `NetworkRealization`.
*   **Transparency**: `construction_params` in `NetworkRealization` files explicitly record the cutoff, algorithm, and seed used, ensuring Principle VII compliance.
