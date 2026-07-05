# Data Model: Network Topology Energy Transfer

## Overview
This document defines the data structures for graph generation, simulation states, and analysis results. All data is stored in `data/` with checksums.

## Core Entities

### 1. NetworkGraph
Represents a single synthetic spin network.
*   **Attributes**:
    *   `graph_id`: Unique string (UUID).
    *   `topology_class`: Enum (`er`, `sw`, `sf`).
    *   `node_count`: Integer (e.g., 500).
    *   `edge_count`: Integer.
    *   `clustering_coefficient`: Float (0.0–1.0).
    *   `average_path_length`: Float.
    *   `degree_distribution`: List of integers (histogram or sequence).
    *   `generation_seed`: Integer.
    *   `generation_params`: Dict (e.g., `{"beta": 0.1, "p": 0.5}`).
    *   `status`: Enum (`valid`, `clustering_deviation`, `disconnected`).

### 2. ExcitationState
Represents the energy profile at a specific time step.
*   **Attributes**:
    *   `simulation_id`: Reference to `SimulationRun`.
    *   `time_step`: Integer (0–100).
    *   `energy_profile`: List of Float (length = node_count).
    *   `spatial_variance`: Float.
    *   `max_energy`: Float (for stability check).

### 3. SimulationRun
Represents one complete simulation instance on a graph.
*   **Attributes**:
    *   `run_id`: Unique string.
    *   `graph_id`: Reference to `NetworkGraph`.
    *   `seed_node`: Integer.
    *   `total_steps`: Integer (100).
    *   `diffusion_rate`: Float (calculated as **OLS slope of spatial variance over the Transient Phase (t=0 to t=20)**).
 * `time_to_saturation`: Float (time step to reach [deferred] energy spread).
    *   `convergence_status`: Enum (`complete`, `divergence`, `timeout`).
    *   `random_seed`: Integer.

### 4. AnalysisResult
Aggregated statistical output.
*   **Attributes**:
    *   `analysis_id`: Unique string.
    *   `metric_name`: String (e.g., `clustering_coefficient`).
    *   `regression_coefficient`: Float.
    *   `p_value`: Float.
    *   `corrected_p_value`: Float (BH/Bonferroni).
    *   `effect_size`: Float (e.g., Cohen's d or R-squared).
    *   `topology_comparison`: Dict (F-statistic, p-value).
    *   `vif_score`: Float (optional, for collinearity check).

## Storage Format
*   **Graphs**: `.gpickle` (NetworkX) or `.json` (adjacency list) in `data/raw/`.
*   **Metadata**: `data/metadata.json` (JSONL or array of objects).
*   **Results**: `.csv` (tabular analysis data) and `.npy` (raw simulation traces if needed).