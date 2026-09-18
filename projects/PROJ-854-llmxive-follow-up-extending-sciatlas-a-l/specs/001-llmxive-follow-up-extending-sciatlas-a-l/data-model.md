# Data Model: Interdisciplinary Bridging Coefficient Analysis

## Overview

This document defines the data structures used throughout the pipeline. All data is stored in **Parquet** format for efficiency and type safety. The model ensures strict separation between raw inputs, derived graph metrics, and final analysis datasets.

## Entity Definitions

### 1. Node (Publication)
Represents a scientific publication in the graph.
*   **`id`**: `string` (Unique identifier, e.g., OpenAlex ID).
*   **`title`**: `string` (Publication title).
*   **`abstract`**: `string` (Optional).
*   **`publication_year`**: `int16`.
*   **`citation_count`**: `int32` (Non-negative).
*   **`embedding_vector`**: `list[float32]` (384 dimensions from `all-MiniLM-L6-v2`).
*   **`primary_cluster`**: `int32` (Cluster ID from Louvain algorithm).
*   **`topic_cluster`**: `int32` (Cluster ID from K-Means on embeddings).
*   **`bridging_coefficient`**: `float32` (Ratio of inter-cluster edges / total degree). Range [0.0, 1.0].
*   **`novelty_score`**: `float32` (Cosine distance to topic centroid). Range [0.0, 2.0].
*   **`degree`**: `int32` (Total number of edges).

### 2. Edge (Relationship)
Represents a citation or connection between two nodes.
*   **`source_id`**: `string`.
*   **`target_id`**: `string`.
*   **`type`**: `string` (e.g., "cites", "references").

### 3. Cluster (Community)
*   **`cluster_id`**: `int32`.
*   **`type`**: `string` ("topological" or "textual").
*   **`node_count`**: `int32`.
*   **`centroid_embedding`**: `list[float32]` (Only for textual clusters).

## File Artifacts

### `data/raw/openalex_stream.parquet`
*   **Source**: OpenAlex API (streamed).
*   **Content**: Raw node and edge metadata for the sampled IDs.
*   **Schema**: `id`, `title`, `cited_by_count`, `publication_year`, `references` (list of IDs).

### `data/processed/subgraph_with_clusters.parquet`
*   **Source**: Ingested data + Louvain clustering.
*   **Content**: Nodes with `primary_cluster` and `bridging_coefficient`.
*   **Schema**: `id`, `primary_cluster`, `bridging_coefficient`, `degree`.

### `data/processed/nodes_with_embeddings.parquet`
*   **Source**: Subgraph + Embedding inference + K-Means.
*   **Content**: Nodes with `embedding_vector`, `topic_cluster`, `novelty_score`.
*   **Schema**: `id`, `embedding_vector`, `topic_cluster`, `novelty_score`.

### `data/processed/final_analysis_dataset.parquet`
*   **Source**: Join of all processed files.
*   **Content**: Complete feature set for statistical analysis.
*   **Schema**: All fields from `Node` entity.

### `artifacts/results/statistical_outputs.json`
*   **Content**: Correlation coefficients, p-values, FDR-adjusted p-values, regression coefficients.
*   **Schema**:
    ```json
    {
      "correlation_citations": { "rho": 0.0, "p_value": 0.0, "p_adj": 0.0 },
      "correlation_novelty": { "rho": 0.0, "p_value": 0.0, "p_adj": 0.0 },
      "regression_citations": { "coef": 0.0, "p_value": 0.0 },
      "regression_novelty": { "coef": 0.0, "p_value": 0.0 }
    }
    ```

## Data Flow

1.  **Ingest**: `data/raw/openalex_stream.parquet` (Raw)
2.  **Graph Construction**: Build NetworkX graph from raw edges.
3.  **Topological Analysis**: Compute `primary_cluster` (Louvain) and `bridging_coefficient`. Save to `subgraph_with_clusters.parquet`.
4.  **Embedding**: Compute `embedding_vector` for all nodes.
5.  **Text Clustering**: Compute `topic_cluster` (K-Means) and `novelty_score`. Save to `nodes_with_embeddings.parquet`.
6.  **Merge**: Join results into `final_analysis_dataset.parquet`.
7.  **Analysis**: Compute statistics and save to `statistical_outputs.json`.
