# Data Model: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

## Overview

This document defines the data structures used throughout the simulation pipeline. All data is generated synthetically and processed in memory before being persisted to `data/` in standardized formats (Parquet, JSON, NumPy `.npz`).

## Entities

### 1. LoRA Adapter
Represents a single low-rank adaptation module.
*   **ID**: Unique string identifier (e.g., `adapter_00001`).
*   **Rank**: Integer, range [1, 256].
*   **Sparsity**: Float, ratio of non-zero parameters (0.0 to 1.0).
*   **Parameter Vector**: Sparse representation of weights (stored as CSR format in `data/raw/adapters.npz`).
*   **Generated At**: Timestamp.

### 2. Topology Graph
A weighted graph where nodes are adapters and edges represent parameter overlap.
*   **Nodes**: Adapter IDs.
*   **Edges**: Weighted by overlap metric (e.g., Jaccard similarity of non-zero indices).
*   **Storage**: Sparse adjacency matrix (CSR) stored in `data/processed/topology_graph.npz`.
*   **Properties**: Symmetric, no self-loops (or self-loop weight = 1.0).

### 3. Request Trace
A sequence of adapter requests simulating workload.
*   **Fields**:
    *   `request_id`: Unique integer (0 to $10^6-1$).
    *   `adapter_id`: String ID of the requested adapter.
    *   `timestamp`: Simulated time (float).
    *   `hotspot_cluster`: Integer ID indicating the cluster of the request (for analysis).
    *   `topology_bias`: Float (0.0 to 1.0) indicating the coupling coefficient used for this trace generation. This field is critical for the sensitivity analysis.
*   **Storage**: Parquet file `data/processed/request_trace.parquet`.

### 4. Simulation Log
Records of events during the simulation run.
*   **Fields**:
    *   `event_id`: Integer.
    *   `timestamp`: Simulated time.
    *   `event_type`: String (`LOAD`, `EVICTION`, `REQUEST`, `CACHE_HIT`).
    *   `adapter_id`: String (if applicable).
    *   `memory_usage`: Integer (MB).
    *   `latency`: Float (ms).
*   **Storage**: Parquet file `data/results/simulation_log_{policy}_{seed}.parquet`.

### 5. Results Summary
Aggregated metrics per policy run.
*   **Fields**:
    *   `policy`: String (`FCFS`, `GREEDY`, `TOPOLOGICAL`).
    *   `seed`: Integer.
    *   `total_requests`: Integer.
    *   `total_latency_ms`: Float.
    *   `p50_latency_ms`: Float.
    *   `p99_latency_ms`: Float.
    *   `cache_hit_rate`: Float.
    *   `eviction_count`: Integer.
    *   `total_loads`: Integer.
    *   `topology_bias`: Float (The coupling coefficient used for this run).
*   **Storage**: CSV `data/results/summary_metrics.csv`.

## Data Flow

1.  **Generation**: `synthetic_adapters.py` -> `data/raw/adapters.npz`.
2.  **Graph Construction**: `overlap_graph.py` reads `adapters.npz` -> `data/processed/topology_graph.npz`.
3.  **Trace Generation**: `request_trace.py` (with `--topology-bias` parameter) -> `data/processed/request_trace.parquet`.
4.  **Simulation**: `main.py` reads graph, trace, config -> runs SimPy -> writes `simulation_log_*.parquet`.
5.  **Analysis**: `statistics.py` reads logs -> computes metrics -> writes `summary_metrics.csv`.

## Constraints

*   **Memory**: All intermediate data structures must fit within 7168 MB.
*   **Determinism**: Random seeds must be recorded in the metadata of each output file.
*   **Immutability**: Raw data files are never overwritten; new runs create new timestamped files.
*   **Correlation**: The `topology_bias` field in the trace must match the coupling coefficient used during generation to ensure valid sensitivity analysis.