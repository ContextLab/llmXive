# Data Model: Single-Cell Trajectories of T-Cell Exhaustion

## Overview
This document defines the canonical data entities, their attributes, and the JSON/YAML schemas used to validate artifacts produced by the pipeline. All files live under `data/` and are described by the contracts in `contracts/`.

## Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **Dataset** | Raw scRNA‑seq count matrix and metadata. Includes a `therapy_response` column when present (e.g., GSE138852). | `dataset_id`, `source`, `raw_counts_path`, `metadata_path`, `checksum`, `cell_count`, `gene_count`, `status` |
| **Trajectory** | Velocity‑augmented representation of a single dataset. Contains pseudotime values, velocity vectors, alignment status, and links to identified fork‑points. | `dataset_id`, `pseudotime_path`, `velocity_graph_path`, `alignment_status`, `fork_points` |
| **ForkPoint** | A statistically significant branch in the velocity field where divergence exceeds the null threshold. | `branch_id`, `dataset_id`, `divergence_score`, `null_mean`, `null_std`, `genes` |
| **ForkPointGene** | Gene expressed at a fork‑point, ranked by its timing of expression relative to the branch. | `gene_symbol`, `branch_id`, `timing_rank`, `expression_level`, `differential_timing` |
| **ValidationResult** | Outcome of enrichment and bootstrap validation against therapy‑response signatures (when available). | `enrichment_pvalue`, `bootstrap_iterations`, `confidence_interval`, `cross_dataset_correlation`, `significance_level`, `discovery_dataset_ids`, `validation_dataset_id` |

## Data Flow
1. **Raw Download** → `data/raw/` (Dataset artifact, `contracts/dataset.schema.yaml`)  
2. **QC & Normalization** → `data/processed/` (Trajectory artifact, `contracts/trajectory.schema.yaml`)  
3. **Velocity Estimation** → same directory (updates Trajectory)  
4. **Fork‑Point Detection** → `data/results/fork_points/` (ForkPoint + ForkPointGene, `contracts/fork_point.schema.yaml`)  
5. **Validation** → `data/results/validation/` (ValidationResult, `contracts/validation.schema.yaml`)  
6. **Report** → `data/results/report/` (HTML, figures, final_report.html)

All artifacts are validated against their respective schema during CI.

---


