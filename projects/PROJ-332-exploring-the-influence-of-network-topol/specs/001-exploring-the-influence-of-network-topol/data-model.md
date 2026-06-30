# Data Model: Influence of Network Topology on Thermal Conductivity

## Overview

This document defines the data structures for the simulation pipeline. The primary data artifact is the `simulation_results.csv` file, which aggregates graph metrics, thermal properties, and regression outputs.

## Entity Definitions

### 1. NetworkGraph
Represents a single synthetic nanowire network.
- **Attributes**:
  - `graph_id`: Unique identifier (UUID).
  - `seed`: Random seed used for generation.
  - `N`: Number of nodes.
  - `p`: Connection probability.
  - `avg_degree`: Measured average degree.
  - `is_connected`: Boolean (True if source-sink path exists).
  - `avg_path_length`: Average shortest path length (if connected).
  - `clustering_coeff`: Global clustering coefficient.
  - `percolation_status`: "Connected", "Disconnected", or "Critical".

### 2. ThermalResistorModel
Represents the physical mapping of edges to resistances.
- **Attributes**:
  - `material`: String (e.g., "Si", "CNT").
  - `bulk_k`: Bulk thermal conductivity (W/(m·K)).
  - `diameter`: Wire diameter (nm).
  - `length`: Wire length (nm).
  - `size_correction_factor`: Fuchs-Sondheimer factor.
  - `effective_k`: Conductivity after size correction.
  - `edge_resistance`: Calculated resistance (K/W).

### 3. SimulationResult
Aggregated result for a single simulation run.
- **Attributes**:
  - `run_id`: Unique run identifier.
  - `effective_k`: Effective thermal conductivity (W/(m·K)).
  - `convergence_residual`: Solver residual norm.
  - `solver_status`: "Converged", "Failed", "Disconnected".
  - `scaling_factor`: Sensitivity scaling factor used.
  - `regression_exponent`: $\alpha$ from log-log fit (if applicable).
  - `regression_p_value`: p-value for $\alpha$.
  - `regression_ci_lower`, `regression_ci_upper`: 95% CI.

### 4. MaterialProperty
Lookup table for material constants.
- **Attributes**:
  - `name`: Material name.
  - `bulk_k`: Value at 300K (W/(m·K)).
  - `source`: "NIST" or "User".

## Data Flow

1. **Input**: Parameters ($N, p, \text{material}, d, \ell$) → `generate_networks.py`.
2. **Process**: Graph generation → Resistance assignment → Solver → Metrics calculation.
3. **Aggregation**: `regression_analysis.py` reads CSV → computes scaling law → appends summary row. `sensitivity_analysis.py` reads CSV → computes deviation → appends summary row.
4. **Checksum**: **After** all aggregation steps are complete, `update_state.py` generates the SHA-256 checksum of `simulation_results.csv`.
5. **State Update**: `update_state.py` records the checksum in `state/projects/...yaml`.

## File Formats

### CSV Schema (`data/processed/simulation_results.csv`)
- **Delimiter**: `,`
- **Encoding**: UTF-8
- **Columns**:
  - `run_id` (int)
  - `seed` (int)
  - `N` (int)
  - `p` (float)
  - `avg_degree` (float)
  - `is_connected` (bool)
  - `effective_k` (float)
  - `convergence_residual` (float)
  - `solver_status` (string)
  - `material` (string)
  - `diameter` (float)
  - `length` (float)
  - `scaling_factor` (float)

### Log File (`logs/simulation.log`)
- **Format**: JSON Lines (one JSON object per line).
- **Content**: Detailed solver iterations, error messages, and parameter dumps.

## State Management (Constitution Principle V)

- **Script**: `code/update_state.py`.
- **Trigger**: Executed automatically at the end of `main.py` after all simulations and analyses are complete.
- **Action**:
  1. Calculates SHA-256 hash of `data/processed/simulation_results.csv`.
  2. Updates `state/projects/PROJ-332-exploring-the-influence-of-network-topol.yaml` with the new hash and timestamp.
  3. Logs the hash to `logs/simulation.log`.
