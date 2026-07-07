# Data Model: Exploring the Role of Network Topology on Synchronization in Coupled Oscillators

## Overview

This document defines the data structures, file formats, and schemas used throughout the research pipeline. All data is stored in the `data/` directory under the project root.

## Data Flow

1.  **Generated Topology**: 50 NetworkX graph objects (`.gpickle`) with metadata (synthetic, no external download).
2.  **Simulation Output**: Time-series phases (optional, for debugging) and summary metrics (`.csv`).
3.  **Analysis Results**: Correlation statistics and plots (`.json`, `.png`).

## Entities

### 1. Network Instance
Represents a single graph generated via Watts-Strogatz rewiring.
- **File**: `data/processed/graph_p_{p_value}.gpickle`
- **Attributes**:
  - `nodes`: List of integers (0 to N-1).
  - `edges`: List of tuples (u, v).
  - `metadata`:
    - `rewiring_probability`: Float (0.0 to 1.0).
    - `seed`: Integer (random seed used).
    - `n_nodes`: Integer (500).
    - `k`: Integer (degree of base lattice).
    - `is_connected`: Boolean.

### 2. Simulation Result
Represents the outcome of a Kuramoto simulation on a specific network instance.
- **File**: `data/processed/results.csv`
- **Columns**:
  - `graph_id`: Integer (1 to 50).
  - `rewiring_probability`: Float.
  - `critical_coupling_strength`: Float (K_c).
  - `order_parameter_threshold`: Float (used to define K_c).
  - `final_order_parameter`: Float (R at t=final).
  - `is_connected`: Boolean.
  - `convergence_iterations`: Integer.
  - `transition_slope`: Float (optional, derivative of R(K) at K_c).

### 3. Statistical Analysis
- **File**: `data/processed/analysis_summary.json`
- **Structure**:
  - `correlation_method`: String ("spearman").
  - `correlation_coefficient`: Float.
  - `p_value`: Float.
  - `significance_level`: Float (0.05).
  - `corrected_p_value`: Float (if applicable).
  - `sensitivity_analysis`:
    - `threshold_0.4`: {coeff, p}
    - `threshold_0.5`: {coeff, p}
    - `threshold_0.6`: {coeff, p}
  - `topological_correlations`:
    - `clustering_coefficient`: {coeff, p}
    - `average_path_length`: {coeff, p}

## File Formats

- **Graph**: NetworkX `.gpickle` (binary, Python-specific, ensures reproducibility of object structure).
- **Tabular Data**: CSV (UTF-8, comma-delimited, header row).
- **Metadata**: JSON (UTF-8).
- **Checksums**: Plain text (`data/checksums.txt`) with format `sha256  filename`.