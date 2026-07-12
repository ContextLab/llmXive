# Data Model: Interdisciplinary Bridging Coefficient Analysis

## 1. Overview

This document defines the data structures used throughout the pipeline, from raw ingestion to final analysis. All data is stored in local files (`data/`) and processed in memory using Pandas DataFrames and NetworkX Graphs.

## 2. Entity Definitions

### Node
Represents a scientific publication.
- **Attributes**:
  - `id`: Unique string identifier (OpenAlex ID).
  - `title`: String (required for novelty analysis).
  - `abstract`: String (required for embedding).
  - `citation_count`: Integer (non-negative).
  - `publication_year`: Integer (required for temporal lag).
  - `primary_cluster`: Integer (assigned by Louvain).
  - `topic_cluster`: Integer (assigned by K-Means).
  - `bridging_coefficient`: Float (0.0 to 1.0).
  - `novelty_score`: Float (k-NN average cosine distance).
  - `embedding_vector`: Array of floats (normalized).
  - `average_abstract_similarity`: Float (control variable).

### Edge
Represents a relationship between publications.
- **Attributes**:
  - `source_id`: String.
  - `target_id`: String.
  - `type`: String (e.g., "cites").

### Analysis Result
Aggregated statistical findings.
- **Attributes**:
  - `test_name`: String (e.g., "Bridging vs Citations").
  - `correlation_coefficient`: Float.
  - `p_value_raw`: Float.
  - `p_value_adjusted`: Float.
  - `method`: String (e.g., "Spearman", "Quadratic Regression").
  - `sample_size`: Integer.
  - `bin_trend`: String (e.g., "linear", "inverted_u", "none").

## 3. Data Flow

1. **Raw Input**: `data/raw/openalex_subset.parquet` (queried from API).
2. **Ingested**: `data/intermediate/nodes.csv`, `data/intermediate/edges.csv`.
3. **Processed**: `data/processed/analysis_dataset.parquet` (includes all derived metrics).
4. **Output**: `data/results/statistical_summary.json`.

## 4. Constraints & Validation

- **Bridging Coefficient**: Must be in range $[0.0, 1.0]$.
- **Citation Count**: Must be $\ge 0$.
- **Novelty Score**: Must be $\ge 0$ (Cosine distance is non-negative).
- **Clustering**: Every node must have a valid `primary_cluster` and `topic_cluster` (unless excluded).
- **Missing Data**: Nodes missing `title` or `abstract` are excluded from novelty analysis but may be retained for citation analysis if `citation_count` exists.
- **Temporal**: `publication_year` must be $\le$ current year.

## 5. Schema Contracts

The following YAML schemas define the strict structure of the output data, used for automated validation.