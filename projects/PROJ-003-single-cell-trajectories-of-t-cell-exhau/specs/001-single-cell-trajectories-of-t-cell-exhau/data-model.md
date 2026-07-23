# Data Model: Single-Cell Trajectories of T-Cell Exhaustion

## Overview

This document defines the data structures, schemas, and relationships for the T-cell exhaustion trajectory analysis pipeline. All data flows from raw count matrices through preprocessing, velocity estimation, fork-point identification, and validation to final reporting.

## Entities

### Dataset
Represents a raw scRNA-seq count matrix with associated metadata.
- **Fields**: `dataset_id` (string), `source` (string), `raw_counts_path` (string), `metadata_path` (string), `checksum` (string), `cell_count` (integer), `gene_count` (integer).
- **Constraints**: `dataset_id` must be unique; `checksum` must match SHA256 of raw file.

### Trajectory
Represents the inferred developmental path of T-cells for a single dataset.
- **Fields**: `dataset_id` (string), `pseudotime_path` (string), `velocity_graph_path` (string), `alignment_status` (string: "success", "failed", "partial"), `fork_points` (list of ForkPoint).
- **Constraints**: `alignment_status` must be "success" for downstream analysis.

### ForkPoint
Represents a branch point in the trajectory where velocity vectors diverge.
- **Fields**: `fork_id` (string), `dataset_id` (string), `divergence_score` (float), `null_mean` (float), `null_std` (float), `genes` (list of ForkPointGene).
- **Constraints**: `divergence_score` must be > 2.0 * `null_std` to be considered significant.
- **Schema Reference**: `contracts/fork_point.schema.yaml`.

### ForkPointGene
Represents a gene expressed at a fork-point, ranked by timing.
- **Fields**: `gene_symbol` (string), `fork_id` (string), `timing_rank` (integer), `expression_level` (float), `differential_timing` (float).
- **Constraints**: `timing_rank` must be unique per fork-point; `differential_timing` must be > 0.1 pseudotime units.

### ValidationResult
Represents the outcome of cross-dataset validation and enrichment analysis.
- **Fields**: `gene_symbol` (string), `enrichment_pvalue` (float), `bootstrap_iterations` (integer), `confidence_interval` (tuple), `cross_dataset_correlation` (float).
- **Constraints**: `enrichment_pvalue` must be < 0.01 for significant findings (SC-002/003) and < 0.05 for SC-006.

## Data Flow

1. **Raw Data**: Downloaded from SRA/GEO → `data/raw/`.
2. **Preprocessed Data**: QC-filtered, normalized matrices → `data/processed/`.
3. **Velocity Data**: Velocity graphs and pseudotime → `data/processed/`.
4. **Fork-Point Data**: Ranked gene lists → `data/results/fork_points/`.
5. **Validation Data**: Bootstrap results, heatmaps → `data/results/validation/`.
6. **Report**: Final PDF/HTML report → `data/results/report/`.

## Schema Definitions

See `contracts/` for detailed YAML schemas.