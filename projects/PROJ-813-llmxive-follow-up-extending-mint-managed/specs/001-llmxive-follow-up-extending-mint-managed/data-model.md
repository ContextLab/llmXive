# Data Model: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

## Overview

This document defines the data structures used for synthetic generation, simulation state, and result aggregation. All data is ephemeral (in-memory) or stored in `data/processed/` as CSV/JSON/Parquet.

## Entities

### 1. LoRA Adapter
Represents a synthetic low-rank adaptation module.
*   **ID**: Unique integer (0 to N-1).
*   **Rank**: Integer (1-256).
*   **Sparsity**: Float (0.0-1.0, proportion of zero weights).
*   **Vector**: Sparse representation of weights (not stored explicitly in logs, only in topology matrix).

### 2. Request Trace
A sequence of adapter requests.
*   **Timestamp**: Float (simulated time).
*   **AdapterID**: Integer (target adapter).
*   **ClusterID**: Integer (logical group for analysis).
*   **IsHotspot**: Boolean (true if requested frequently).

### 3. Topology Graph
A weighted adjacency matrix.
*   **Nodes**: Adapter IDs.
*   **Edges**: Overlap score (0.0-1.0).
*   **Storage**: `scipy.sparse.csr_matrix`.
*   **Note**: Generated ONCE per experiment and **FIXED** across all replications.

### 4. Simulation Result
Aggregated metrics per run.
*   **RunID**: Unique identifier.
*   **Seed**: Random seed used.
*   **Policy**: String ("FCFS", "Greedy", "Topological").
*   **TotalLatency**: Float (ms).
*   **EvictionCount**: Integer.
*   **HitRate**: Float (0.0-1.0).
*   **ColdStartLatency**: Float (p50, p95).
*   **DeltaSize**: Float (Average size of non-overlapping delta loaded, in bytes).

## Data Flow

1.  **Generation**: `code/data/generator.py` creates Adapters and Trace.
2.  **Topology**: `code/data/topology.py` computes Overlap Matrix from Adapters (Fixed).
3.  **Simulation**: `code/simulation/runner.py` consumes Trace + Topology + Policy.
4.  **Analysis**: `code/analysis/statistics.py` aggregates Results across Replications.

## Storage Formats

*   **Intermediate**: Pickled sparse matrices (`.pkl`) for topology (fast load).
*   **Trace**: `.npy` (NumPy binary) for compactness.
*   **Results**: `.csv` for easy inspection and plotting (using `pandas`).
*   **Schemas**: Defined in `contracts/` for validation.

**Pandas Usage**: The `pandas` library is explicitly used for I/O operations (reading/writing CSV/Parquet) and for aggregating simulation results into DataFrames for statistical analysis.