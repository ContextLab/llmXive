# Data Model: Investigating Microbial Community Succession in Constructed Wetlands

## Overview

This document defines the data structures, schemas, and relationships used in the microbial succession pipeline. It ensures consistency between data retrieval, processing, and analysis.

## Entities & Relationships

### Sample
A single wetland observation.
*   **Attributes**: `sample_id`, `wetland_stage` (categorical: early, intermediate, mature), `n_removal_rate` (float), `p_removal_rate` (float), `location`, `dataset_source`.
*   **Relationship**: Contains multiple `Taxon` counts.

### Taxon
A microbial OTU/ASV.
*   **Attributes**: `taxon_id`, `taxonomy_string` (e.g., "k__Bacteria; p__Proteobacteria...").
*   **Relationship**: Associated with counts in multiple `Sample`s.

### Feature Table
A matrix of Taxon counts per Sample.
*   **Structure**: Rows = Samples, Columns = Taxa.
*   **Values**: Integer counts (or relative abundance after subsampling).

### Network
A co-occurrence graph.
*   **Nodes**: Taxa.
*   **Edges**: Significant Spearman correlations (weight = ρ, metadata = p-value).
*   **Metrics**: Modularity, Density, Average Degree.

## Data Flow

1.  **Raw**: `data/raw/` (Downloaded feature tables + metadata).
2.  **Config**: `data/config/dataset_ids.json` (List of IDs).
3.  **Processed**: `data/processed/` (Filtered, subsampled, merged).
4.  **Results**: `data/results/` (Diversity stats, Network graphs, Correlation tables).

## Schema Definitions

See `contracts/` for formal YAML schemas.
*   `dataset_config.schema.yaml`: Structure of `data/config/dataset_ids.json`.
*   `feature_table.schema.yaml`: Structure of processed 16S count tables.
*   `metadata.schema.yaml`: Structure of sample metadata (N/P removal, stage).
*   `network_output.schema.yaml`: Structure of network metrics and edge lists.

## Constraints

* **Subsampling**: Max [deferred] reads per sample (Constitution Principle VII).
*   **Completeness**: Samples must have both 16S data AND N/P metrics (FR-002).
*   **Types**: Counts are integers; rates are floats; stages are categorical.
