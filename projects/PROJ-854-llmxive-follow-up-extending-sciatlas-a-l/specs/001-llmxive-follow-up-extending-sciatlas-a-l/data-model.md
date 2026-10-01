# Data Model: Interdisciplinary Bridging Coefficient Analysis

## Overview

This document defines the data structures, schemas, and transformations used in the analysis pipeline. The data flows from a raw OpenAlex-derived subgraph to an enriched dataset containing topological and text-based metrics.

## Source Data

### Input: `data/processed/subgraph.parquet`
- **Format**: Apache Parquet.
- **Description**: A subset of the OpenAlex graph containing scientific works and their connections. Derived from the **OpenAlex Full Snapshot (2026-01-01)**.
- **Schema**:
  - `id`: `string` (Unique work identifier)
  - `title`: `string` (Work title, nullable)
  - `cited_by_count`: `int64` (Citation count, nullable)
  - `publication_date`: `datetime64[ns]` (Date of publication)
  - `field`: `string` (Disciplinary field identifier)
  - `neighbors`: `list[string]` (List of connected work IDs). *Derived from the same OpenAlex snapshot as the node data, linked via the `id` field.*

## Derived Data

### Output: `data/processed/subgraph_with_clusters.parquet`
- **Format**: Apache Parquet.
- **Description**: The original dataset enriched with clustering, bridging, and novelty metrics.
- **Schema**:
  - `id`: `string`
  - `title`: `string`
  - `cited_by_count`: `int64`
  - `publication_date`: `datetime64[ns]`
  - `field`: `string`
  - `primary_cluster`: `int32` (Louvain cluster ID)
  - `degree`: `int32` (Total number of connections)
  - `inter_cluster_edges`: `int32` (Number of edges connecting to different clusters)
  - `bridging_coefficient`: `float64` (Calculated as `inter_cluster_edges / degree`)
  - `embedding_vector`: `list[float32]` (384-dimensional vector from MiniLM)
  - `novelty_score`: `float64` (Cosine distance to global centroid)
  - `is_singleton`: `bool` (True if cluster size is 1)
  - `novelty_score_variance`: `float64` (Variance of novelty scores for the dataset, computed for SC-002)

### Logs: `data/processed/excluded_nodes.json`
- **Format**: JSON.
- **Description**: List of nodes excluded from embedding generation due to null titles.
- **Schema**:
  - `excluded_ids`: `list[string]`
  - `reason`: `string` (e.g., "null_title")

## Data Transformations

1. **Ingestion**:
   - Load `subgraph.parquet`.
   - Validate against `data/schema/openalex_works.json` (derived from `contracts/openalex_works.schema.yaml`).
   - Handle missing `cited_by_count` (default to 0).
   - Log null titles to `excluded_nodes.json`.

2. **Embedding**:
   - Filter nodes with non-null titles.
   - Generate embeddings using `all-MiniLM-L6-v2`.
   - Compute global centroid (mean of normalized vectors, float32).
   - Calculate `novelty_score` (cosine distance to centroid).

3. **Topology**:
   - Construct graph from `id` and `neighbors` (convert list of strings to NetworkX edges).
   - Run Louvain clustering to assign `primary_cluster`.
   - Calculate `degree` and `inter_cluster_edges`.
   - Compute `bridging_coefficient`.

4. **Enrichment**:
   - Merge embedding/novelty data with topology data.
   - Save to `subgraph_with_clusters.parquet`.

## Constraints

- **Memory**: All transformations must be optimized to fit within 7GB RAM. Large lists (embeddings) may be stored as compressed arrays or processed in batches.
- **Integrity**: Checksums are recorded for all Parquet files. No in-place modification.
- **Validation**: Every intermediate file must pass schema validation before being used as input for the next step.
