# Implementation Plan: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Branch**: `001-gene-regulation` | **Date**: 2026-10-19 | **Spec**: `specs/001-gene-regulation/spec.md`  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The pipeline will (1) verify the availability of three open scRNA‑seq datasets, (2) download, checksum, and preprocess each (log‑CPM, HVG selection, deterministic sampling), (3) compute global intrinsic dimensionality (Levina‑Bickel) and local density (average 15‑NN distance) on the high‑dimensional matrix, (4) generate PCA, t‑SNE, and UMAP embeddings with reproducible hyper‑parameters, (5) run Leiden clustering (fixed resolution 0.5) on each embedding, (6) calculate ARI and NMI (logit‑transformed) against ground‑truth labels, (7) perform a sensitivity sweep over silhouette‑score thresholds {0.4, 0.5, 0.6}, (8) fit a mixed‑effects model `logit_fidelity ~ method + intrinsic_dim + local_density + (1|dataset)` with a Benjamini‑Hochberg correction, and (9) produce validated JSON/YAML reports and figures. All steps respect the functional requirements (FR‑001…FR‑008) and success criteria (SC‑001…SC‑006).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `scanpy==1.10.2`, `scikit-learn==1.5.0`, `umap-learn==0.5.6`, `leidenalg==0.10.2`, `pandas==2.2.2`, `numpy==2.0.0`, `psutil==6.0.0`, `statsmodels==0.14.2`, `pingouin==0.5.4`, `pyyaml==6.0.1`  
- **Storage**: File system under `data/` (raw, processed, results).  
- **Testing**: `pytest` with contract validation (`jsonschema`).  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU, ≤7 GB RAM, ≤14 GB disk, ≤6 h). All methods run on CPU; no GPU is required.  
- **Constraints**: Peak RSS ≤ 7 GB (SC‑003), total wall‑clock ≤ 21 600 s (SC‑004).  

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed seeds (42 for random‑pair sampling, 12345 for cell subsampling, 42 for Leiden). All URLs are immutable. |
| II. Verified Accuracy | PASS | All external datasets are fetched from the verified URLs listed in `research.md`. |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded in `data/manifest.json`; raw files never mutated. |
| IV. Single Source of Truth | PASS | Every metric originates from a single row in `data/` and a single script in `code/`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/projects/...yaml`. |
| VI. Geometric Characterization Protocol | PASS | Intrinsic dimensionality and local density are computed **before** any reduction. |
| VII. Ground‑Truth Fidelity Validation | PASS | Fidelity (ARI/NMI) always compared to independent cell‑type labels. |

## Phase Overview & FR/SC Mapping
| Phase | Core Tasks | FR(s) | SC(s) |
|-------|------------|-------|-------|
| **0 – Data Availability Verification** | Load manifest, confirm each dataset contains a `counts` array of raw integers; abort if missing. | FR‑001 (dataset existence) | SC‑003, SC‑004 |
| **1 – Ingestion & Preprocessing** | Download (via `datasets.load_dataset` or `scanpy`), checksum, deterministic subsample (≤ 5 000 cells, seed = 12345), log‑CPM, variance‑stabilizing HVG selection, store Parquet. | FR‑001, FR‑002, FR‑003 | SC‑003, SC‑004 |
| **2 – Geometric Diagnostics** | Compute Levina‑Bickel intrinsic dimensionality (k = 15, 10 000 random unordered cell pairs, seed = 42) and average 15‑NN distance (local density) on the high‑dim matrix. | FR‑002, FR‑003 | SC‑003 |
| **3 – Embedding Generation** | PCA (30 PCs), t‑SNE (perplexity 30, 1 000 iters), UMAP (n_neighbors 15, min_dist 0.1). Save 2‑D coordinates (CSV) and full PCA matrix (Parquet). | FR‑004 | SC‑003, SC‑004 |
| **4 – Primary Fidelity Calculation** | Leiden clustering on each embedding (resolution = 0.5, seed = 42). Compute ARI and NMI vs. ground‑truth, logit‑transform scores, store in `data/metrics/fidelity_*.json`. | FR‑005 | SC‑006 (no missing values) |
| **5 – Sensitivity Sweep** | For silhouette thresholds {0.4, 0.5, 0.6}: re‑run Leiden (same resolution), recompute ARI/NMI, calculate variance across thresholds; enforce variance < 0.05 (SC‑001). | FR‑007 | SC‑001 |
| **6 – Mixed‑Effects Modeling** | Fit `logit_fidelity ~ method + intrinsic_dim + local_density + (1|dataset)` via `statsmodels.MixedLM`. Perform Shapiro‑Wilk on residuals; if p < 0.05, fall back to 10 000‑permutation ANOVA. Compute VIF after dropping one dummy level; abort if any VIF ≥ 5 (SC‑005). Apply Benjamini‑Hochberg to all p‑values (SC‑002). | FR‑006, FR‑008 | SC‑002, SC‑005 |
| **7 – Reporting & Contract Validation** | Assemble JSON/YAML summary, generate sensitivity plots, validate all outputs against schemas in `contracts/`. | All FRs (output artifacts) | All SCs (memory, runtime, completeness) |

## Edge‑Case Handling
- **< 500 cells** → skip intrinsic‑dimensionality & local‑density computation, log warning, continue with embeddings.  
- **Missing ground‑truth labels** → mark fidelity as “Unavailable” for that dataset; continue with others.  
- **Leiden non‑convergence** → retry once with same seed; if still failing, record “Unavailable” and proceed.  

## Compute Feasibility
- Sparse matrix representation keeps peak RSS ≈ 5 GB (well under 7 GB).  
- t‑SNE & UMAP on ≤ 5 000 cells finish < 30 min each on the free runner.  
- Total wall‑clock expected < 3 h; abort if > 21 600 s (SC‑004).  

## Task List (ordered)
1. `code/phase0_verify_raw_counts.py` – verify raw count presence, write `data/manifest.json`.  
2. `code/phase1_preprocess.py` – checksum, deterministic sampling, log‑CPM, HVG, write Parquet.  
3. `code/phase2_geometry.py` – Levina‑Bickel intrinsic dim, 15‑NN local density, store JSON.  
4. `code/phase3_embeddings.py` – PCA, t‑SNE, UMAP, save CSV/Parquet.  
5. `code/phase4_fidelity_fixed.py` – Leiden (resolution 0.5), ARI/NMI, logit‑transform, write `data/metrics/fidelity_*.json`.  
6. `code/phase5_sensitivity.py` – silhouette‑threshold sweep, variance calculation, store variance summary.  
7. `code/phase6_mixed_effects.py` – MixedLM (fallback permutation), VIF, BH correction, write `data/results/statistical_result.yaml`.  
8. `code/phase7_reporting.py` – aggregate tables, generate plots, validate contracts.  
9. `Snakefile` – orchestrates all phases, includes a `verify_data_availability` rule that aborts if any dataset is “Unavailable”.  

---
