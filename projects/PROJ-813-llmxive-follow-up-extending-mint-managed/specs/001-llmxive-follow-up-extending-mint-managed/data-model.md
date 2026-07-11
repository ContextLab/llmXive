# Data Model: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

## Overview

This document defines the data structures, schemas, and relationships for the synthetic LoRA generation, topology construction, and simulation logging. All data is stored in `data/` and validated against the schemas in `contracts/`.

## Entities

### 1. LoRA Adapter (Synthetic)

Represents a single synthetic LoRA adapter.
- **Attributes**:
  - `adapter_id`: Unique string identifier (UUID).
  - `rank`: Integer (1-256).
  - `sparsity`: Float (0.0-1.0).
  - `cluster_id`: Integer (0-49) indicating the latent cluster.
  - `base_correlation`: Float (0.0-1.0) indicating injection level.
  - `weight_hash`: SHA-256 hash of the flattened weight vector (for integrity).
  - `size_bytes`: Approximate memory footprint.

### 2. Overlap Matrix

A symmetric matrix representing pairwise similarity.
- **Attributes**:
  - `source_adapter_id`: String.
  - `target_adapter_id`: String.
  - `overlap_score`: Float (0.0-1.0).
  - `cosine_similarity`: Float (-1.0-1.0).

### 3. Request Trace

A time-ordered sequence of requests.
- **Attributes**:
  - `request_id`: Integer (sequential).
  - `timestamp`: Float (simulated time).
  - `adapter_id`: String (target).
  - `arrival_time`: Float.
  - `cluster_id`: Integer (for analysis, derived from adapter_id).

### 4. Simulation Event

A log entry for a discrete event.
- **Attributes**:
  - `event_id`: Integer.
  - `timestamp`: Float.
  - `event_type`: Enum (REQUEST_ARRIVAL, CACHE_HIT, CACHE_MISS, LOAD_START, LOAD_END, EVICTION, MEMORY_ERROR).
  - `adapter_id`: String (optional).
  - `latency`: Float (optional).
  - `memory_usage`: Float (GB).
  - `delta_factor`: Float (optional, the reduction factor applied due to overlap).

### 5. Policy Result

Aggregated metrics for a specific policy run.
- **Attributes**:
  - `policy_name`: String.
  - `replication_id`: Integer.
  - `trace_id`: String (UUID of the trace used).
  - `total_requests`: Integer.
  - `avg_cold_start_latency`: Float.
  - `cache_hit_rate`: Float.
  - `total_evictions`: Integer.
  - `max_memory_usage`: Float.

## Data Flow

1. **Generation**: `generate_adapters.py` -> `data/raw/adapters.parquet`
2. **Trace**: `generate_trace.py` -> `data/processed/request_trace_{replication_id}.parquet`
3. **Topology**: `compute_overlap.py` -> `data/processed/overlap_matrix.csv` + `data/processed/topology_graph.json`
4. **Simulation**: `run_experiment.py` -> `data/logs/{policy}_{replication_id}.jsonl`
5. **Analysis**: `stats.py` -> `data/processed/results_summary.csv`

## Storage Constraints

- **Raw Adapters**: [deferred] adapters. If stored as full matrices, this exceeds a substantial storage threshold. **Strategy**: Store only metadata and a compressed representation (e.g., rank decomposition factors) or regenerate weights on-the-fly using the seed. The `weight_hash` is stored for verification.
- **Overlap Matrix**: [deferred] x [deferred] float32 = 400 MB. Stored as CSV/Parquet.
- **Logs**: 30 reps x 1M events. Compressed JSONL or Parquet.

