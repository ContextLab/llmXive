# Data Model: Single-Cell Trajectories of T-Cell Exhaustion

## Overview
Canonical entities and artifacts stored under `data/`, each validated against a JSON‑Schema contract (see `contracts/*.schema.yaml`). All transformations produce new immutable files; raw inputs remain unchanged (Constitution III).

## Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **Dataset** | Raw scRNA‑seq count matrix + metadata for a GEO accession. | `dataset_id`, `source`, `raw_counts_path`, `metadata_path`, `checksum`, `cell_count`, `gene_count`, `marker_gene_fraction`, `status` |
| **Trajectory** | Velocity‑augmented representation per dataset (pseudotime, velocity graph, alignment status). | `dataset_id`, `pseudotime_path`, `velocity_graph_path`, `alignment_status`, `runtime_seconds`, `peak_memory_mb`, `fork_points` |
| **ForkPoint** | Statistically significant branch in the velocity field. | `branch_id`, `dataset_id`, `divergence_score`, `null_mean`, `null_std`, `p_value`, `confidence` |
| **ForkPointGene** | Gene expressed at a fork‑point, ranked by timing. | `gene_symbol`, `branch_id`, `timing_rank`, `expression_level`, `differential_timing` |
| **ValidationResult** | Outcome of enrichment, bootstrap validation and cross‑dataset consistency. | `enrichment_pvalue`, `bootstrap_iterations`, `confidence_interval`, `cross_dataset_correlation`, `significance_level`, `power_adequate`, `discovery_dataset_ids`, `validation_dataset_id`, `disclaimer_included` |
| **Manifest** (SSoT) | Central registry of all result artifacts, their provenance, and the random‑seed used. | `manifest_version`, `generated_at`, `seed`, `artifacts` (list of objects with `path`, `type`, `hash`) |

## Data Flow
1. **Download** → `data/raw/` (Dataset artifact, SHA‑256, marker check).  
2. **QC & Normalization** → `data/processed/` (MT‑filtered, log‑normalized).  
3. **T‑Cell Subsetting** → `data/processed/*_tcells.h5ad`.  
4. **Batch‑Effect Integration** → `data/processed/integrated.h5ad`.  
5. **Velocity & Pseudotime** → `data/processed/*_velocity.h5ad` + Trajectory artifact.  
6. **Fork‑Point Detection & Ranking** → `data/results/fork_points/<dataset>_fork_points.csv` (ForkPoint & ForkPointGene).  
7. **Power Analysis** → `data/results/validation/power_analysis.json`.  
8. **Enrichment & Validation** → `data/results/validation/<dataset>_enrichment.json` (ValidationResult).  
9. **Report** → `data/results/report/final_report.html` (+ figures).  
10. **Manifest** → `data/manifest.yaml` (lists every artifact above with its SHA‑256 hash and records the global random seed).  

All artifacts are schema‑validated in CI; `data/results/` is part of the committed skeleton (satisfies T001). The manifest satisfies Principle IV by providing a unique reference for every downstream figure and statistic.

---


