# Data Model: Single-Cell Trajectories of T-Cell Exhaustion

## Overview

Canonical entities and artifacts under `data/`, validated against the contracts in `contracts/`. Raw data is immutable; every transformation writes a new file with documented derivation (Constitution III).

## Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **Dataset** | Raw scRNA-seq count matrix + metadata; `status` reflects real download outcome (`available`/`unavailable`/`partial`). | `dataset_id`, `source`, `raw_counts_path`, `metadata_path`, `checksum`, `cell_count`, `gene_count`, `status` |
| **Trajectory** | Velocity-augmented representation per dataset: pseudotime, velocity graph, alignment status. | `dataset_id`, `pseudotime_path`, `velocity_graph_path`, `alignment_status`, `fork_points` |
| **ForkPoint** | Statistically significant velocity-field branch (p<0.01 vs. permutation null). | `branch_id`, `dataset_id`, `divergence_score`, `null_mean`, `null_std`, `p_value`, `genes` |
| **ForkPointGene** | Gene at a fork-point ranked by timing (differential timing >0.1 pseudotime units). | `gene_symbol`, `branch_id`, `timing_rank`, `expression_level`, `differential_timing` |
| **ValidationResult** | Enrichment + bootstrap validation outcome. | `enrichment_pvalue`, `bootstrap_iterations`, `confidence_interval`, `cross_dataset_correlation`, `significance_level`, `discovery_dataset_ids`, `validation_dataset_id` |

## Data Flow

1. **Download** → `data/raw/` (Dataset artifact; SHA-256 recorded; marker check FR-010)
2. **QC & normalization** → `data/processed/` (new files; MT-gene-annotated filtering per T003 fix)
3. **T-cell subset** → `data/processed/*_tcells.h5ad`
4. **Velocity & pseudotime** → `data/processed/*_velocity.h5ad` + Trajectory artifact
5. **Fork-point detection** → `data/results/fork_points/<dataset>_fork_points.csv` (ForkPoint/ForkPointGene; `branch_id` field)
6. **Power analysis** → `data/results/validation/power_analysis.json`
7. **Enrichment & bootstrap validation** → `data/results/validation/<dataset>_enrichment.json` (ValidationResult)
8. **Report** → `data/results/report/final_report.html` + figures

All artifacts are schema-validated in CI; `data/results/` is part of the committed skeleton (T001 fix).

---
