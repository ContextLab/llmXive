# Data Model: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

## Overview
This document defines the data structures used throughout the pipeline. All models are implemented in `code/models/` and validated against the contracts in `contracts/`.

## Core Entities

### 1. AdjacencyMatrix
Represents the connectivity matrix for a single subject under a specific parcellation scheme.

*   **Attributes**:
    *   `subject_id`: Unique identifier for the subject.
    *   `atlas_name`: Name of the atlas (e.g., "AAL-90", "Schaefer-200").
    *   `node_count`: Integer, number of nodes (N).
    *   `matrix`: 2D numpy array (N x N), symmetric, weighted.
    *   `node_labels`: List of strings, names of brain regions.
    *   `checksum`: SHA256 hash of the matrix data.
*   **Constraints**:
    *   Matrix must be symmetric.
    *   Diagonal must be zero.
    *   Values must be non-negative (correlation-based).

### 2. CentralityScore
Stores centrality metrics for a single subject's graph.

*   **Attributes**:
    *   `subject_id`: Unique identifier.
    *   `atlas_name`: Name of the atlas.
    *   `metric_type`: "degree" or "betweenness".
    *   `scores`: 1D numpy array (N,), centrality value for each node.
    *   `rank_order`: 1D numpy array (N,), rank of each node (1 = highest).
*   **Constraints**:
    *   Length of `scores` must equal `node_count` of the corresponding `AdjacencyMatrix`.
    *   No missing values (NaN).

### 3. HubSet
Represents the set of nodes identified as hubs based on a centrality threshold.

*   **Attributes**:
    *   `subject_id`: Unique identifier.
    *   `atlas_name`: Name of the atlas.
    *   `metric_type`: "degree" or "betweenness".
    *   `threshold_percent`: Float, percentage used for cutoff (e.g., 0.10).
    *   `hub_nodes`: List of integers, indices of hub nodes.
    *   `hub_count`: Integer, number of hubs (`floor(N * threshold)`).
*   **Constraints**:
    *   `hub_count` must equal `floor(node_count * threshold_percent)`.

### 4. SpatialMapping
Lookup table for mapping high-resolution nodes to low-resolution nodes.

*   **Attributes**:
    *   `source_atlas`: High-res atlas name (e.g., "Schaefer-200").
    *   `target_atlas`: Low-res atlas name (e.g., "AAL-90").
    *   `mapping_dict`: Dictionary `{source_index: target_index}`.
    *   `unmapped_nodes`: List of source indices with no overlap.
*   **Constraints**:
    *   Each source node maps to at most one target node.

## Data Flow
1.  **Raw Data** -> `loader.py` -> `AdjacencyMatrix` (N=20, 3 resolutions).
2.  `AdjacencyMatrix` -> `centrality.py` -> `CentralityScore`.
3.  `CentralityScore` -> `overlap.py` (thresholding) -> `HubSet`.
4.  `HubSet` (different resolutions) -> `overlap.py` (spatial mapping) -> **Overlap Metrics** (Excess Overlap, Spearman).
5.  **Overlap Metrics** -> `visualization.py` -> Plots & `validation_report.json`.
