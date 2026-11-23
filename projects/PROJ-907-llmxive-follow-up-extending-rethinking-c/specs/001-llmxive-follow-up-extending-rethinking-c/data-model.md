# Data Model: llmXive follow-up: extending "Rethinking Cross-Layer Information Routing in Diffusion Transformers"

## Overview

This document defines the data structures for routing traces, canonical maps, and benchmark results. All artifacts are stored in `data/` and must conform to the schemas defined in `contracts/`. Intermediate routing tensors are aggregated on-the-fly to manage memory and disk usage.

## Entity Definitions

### 1. Routing Trace Aggregation (Intermediate)
**Path**: `data/routing_cache/routing_stats_{block_id}.npy` (or similar binary format)
**Description**: Aggregated routing weight statistics (mean/std) recorded during inference, per block.
**Structure**:
-   **Dimensions**: `[num_timesteps, num_targets]` (aggregated across images)
-   **Data Type**: `float32`
-   **Content**: Mean and standard deviation of softmax distributions over historical layers for each block at each timestep.

### 2. Cluster Centers (Intermediate)
**Path**: `data/routing_cache/cluster_centers.json`
**Description**: Results of k-means clustering applied to the routing vectors per block.
**Structure**: A JSON object where keys are `block_id` and values are cluster data.
-   `block_id`: Integer identifier for the transformer block.
-   `clusters`: List of cluster objects.
    -   `cluster_id`: Integer.
    -   `center`: Array of floats (the static weight vector for this cluster).
    -   `size`: Number of timesteps in this cluster.
    -   `silhouette_score`: Float (0.0 to 1.0).
-   `null_hypothesis`: Boolean flag (true if k<2 or silhouette < 0.25).

### 3. Canonical Routing Map (Artifact)
**Path**: `data/routing_cache/canonical_map.json`
**Description**: The final static routing weights to be injected into the model, per block.
**Structure**:
-   `version`: String (schema version).
-   `generated_at`: ISO8601 timestamp.
-   `blocks`: List of objects.
    -   `block_id`: Integer.
    -   `static_weights`: Array of floats (the final static weight vector).
    -   `source`: String ("dominant_cluster" or "global_average").

### 4. Benchmark Result (Artifact)
**Path**: `data/results/benchmark_results.json`
**Description**: Latency and FID scores for a single run.
**Structure**:
-   `run_id`: String (UUID).
-   `model_type`: String ("dynamic" or "static").
-   `seed`: Integer.
-   `latency_seconds`: Float.
-   `fid_score`: Float.
-   `memory_peak_gb`: Float.

### 5. Statistical Analysis (Artifact)
**Path**: `data/results/statistical_analysis.json`
**Description**: Aggregated results of the bootstrap test.
**Structure**:
-   `n_seeds`: Integer (5).
-   `n_resamples`: Integer (1000).
-   `dynamic_mean_fid`: Float.
-   `dynamic_std_fid`: Float.
-   `static_mean_fid`: Float.
-   `static_std_fid`: Float.
-   `p_value`: Float (from bootstrap).
-   `significant`: Boolean.
-   `t_test_p_value`: Float (from paired t-test on image-set means).

### 6. Sensitivity Sweep (Artifact)
**Path**: `data/results/sensitivity_sweep.json`
**Description**: FID scores across different clustering thresholds.
**Structure**:
-   `thresholds`: List of objects.
    -   `threshold`: Float.
    -   `mean_fid`: Float.
    -   `std_fid`: Float.
    -   `degradation`: Float.

## Data Hygiene Rules

1.  **Checksums**: Every file in `data/` must have a corresponding `.sha256` file.
2.  **Immutability**: Once written, `data/` files are never modified. Derivations create new files.
3.  **Schema Validation**: All JSON artifacts must pass validation against the `contracts/` schemas before being used as inputs for subsequent steps.
4.  **Versioning**: Artifacts `canonical_map.json`, `benchmark_results.json`, and `statistical_analysis.json` will carry content hashes in `state/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c.yaml`.
