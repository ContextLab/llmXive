# Implementation Plan: Single-Cell Trajectories of T-Cell Exhaustion

**Branch**: `001-single-cell-trajectories-t-cell-exhaustion` | **Date**: 2026-10-21 | **Spec**: `specs/001-single-cell-trajectories-of-t-cell-exhaustion/spec.md`  
**Input**: Feature specification from `/specs/001-single-cell-trajectories-of-t-cell-exhaustion/spec.md`

## Summary
We will build a fully reproducible CPU‑only pipeline that (1) programmatically resolves and downloads the four GEO datasets, (2) performs Seurat‑v4 QC (mitochondrial‑read filter > 20 % and log‑normalization), (3) isolates CD3⁺ T‑cells, (4) optionally applies Harmony batch‑correction, (5) runs scVelo stochastic mode on each dataset (≤ 45 min per dataset), (6) detects statistically significant fork‑points using a 500‑permutation null (p < 0.01), (7) ranks fork‑point genes by differential timing (> 0.1 pseudotime units), (8) conducts a simulation‑based power analysis (target ≥ 80 % power, α = 0.05) and aborts if insufficient, (9) validates fork‑point genes against an **open, verified gene‑set** extracted from the `GSE (json)` resource (instead of the unverified PMID 32012345), (10) runs 500 bootstrap resamples for enrichment confidence intervals and cross‑dataset Spearman correlation (≥ 0.80 for top‑3 genes), and (11) produces a final HTML report containing all figures, tables, and the mandatory observational disclaimer (FR‑009). All artifacts are schema‑validated and recorded in a manifest (SSoT).

## Technical Context
- **Language/Version**: Python 3.11, R 4.3 (Seurat v4)  
- **Primary Dependencies**: `scanpy>=1.9,<1.11`, `scvelo>=0.2.5,<0.3`, `anndata>=0.9`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`, `psutil`, `ruff`, `black`, `harmony-pytorch` (CPU‑compatible), `rpy2` for Seurat integration, `pytest`.  
- **Random Seed**: Fixed at `42` in `code/config.yaml` (Principle I).  
- **Storage**: Local filesystem under `data/` (raw, processed, results, manifest).  
- **Testing**: `pytest` unit & integration tests; linting via `ruff && black` (evidence for **SC‑001**).  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM, ≤6 h).  
- **Performance Goals**: scVelo ≤ 45 min/dataset; 500 permutations ≈ 30 min; 500 bootstraps ≈ 45 min; total wall‑clock ≤ 5 h. Optional GPU escape hatch for permutation step if a free Kaggle GPU is detected.  
- **Constraints**: CPU‑first; deterministic seeds; ≥ 80 % required marker genes (FR‑010).  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed seeds, deterministic scripts, all downloads via canonical GEO endpoint. |
| II. Verified Accuracy | PASS | All external resources are either GEO (public) or the verified `GSE (json)` gene‑set. No unverified PMID used. |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded; raw files immutable; each transformation writes a new file with provenance. |
| IV. Single Source of Truth | PASS | `data/manifest.yaml` lists every artifact with hash; figures/tables trace back to manifest entries. |
| V. Versioning Discipline | PASS | Content hashes stored in project state YAML; timestamps updated on change. |
| VI. Biological Trajectory Consistency | PASS | Therapy‑response signature is independent of velocity data; disclaimer enforces associative interpretation. |
| VII. Clinical Relevance Grounding | PASS | Fork‑point genes are linked to checkpoint‑therapy responsiveness; implications discussed in final report. |

## Project Structure
```text
specs/001-single-cell-trajectories-of-t-cell-exhaustion/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── fork_point.schema.yaml
    ├── trajectory.schema.yaml
    └── validation.schema.yaml

projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/
├── code/
│   ├── requirements.txt
│   ├── config.yaml                # seed pinning
│   ├── download_data.py
│   ├── preprocess.R
│   ├── preprocess.py
│   ├── subset_tcells.py
│   ├── batch_correct.py
│   ├── velocity.py
│   ├── forkpoint.py
│   ├── power_analysis.py
│   ├── enrichment.py
│   ├── validate.py
│   └── report.py
├── data/
│   ├── raw/.gitkeep
│   ├── processed/.gitkeep
│   ├── results/.gitkeep
│   ├── manifest.yaml
│   └── ...
├── logs/
│   ├── lint.txt
│   ├── download.log
│   ├── preprocess.log
│   ├── velocity.log
│   └── forkpoint.log
└── tests/
    ├── unit/
    │   ├── test_download.py
    │   ├── test_preprocess.py
    │   ├── test_velocity.py
    │   └── test_forkpoint.py
    └── integration/
        └── test_pipeline.py
```

## Phase Order & FR/SC Mapping
| Phase | Description | FR(s) | SC(s) |
|------|-------------|-------|-------|
| **0 – Layout & Lint** | Create result directories, manifest, run `ruff && black`. | — | SC‑001 (lint evidence) |
| **1 – Data Acquisition** | `download_data.py` resolves GEO URLs, downloads, records SHA‑256, checks marker‑gene fraction (≥ 0.8). | FR‑001, FR‑010, FR‑012 | SC‑005 |
| **2 – QC & Normalization** | `preprocess.R` + wrapper filters >20 % mt reads, log‑normalizes, selects 2 000 HVGs. | FR‑002 | — |
| **3 – T‑Cell Subsetting** | `subset_tcells.py` retains CD3⁺ cells; datasets < 1 000 cells after QC trigger a warning (`partial`). | FR‑002 | — |
| **4 – Batch‑Effect Correction** | `batch_correct.py` applies Harmony (CPU) to combined T‑cell matrices before velocity. | — | — |
| **4 – Velocity & Pseudotime** | `velocity.py` runs scVelo stochastic mode on CPU, retries up to 2 times, logs runtime & memory. | FR‑003 | SC‑001 |
| **5 – Fork‑Point Detection & Ranking** | `forkpoint.py` computes divergence, generates 500‑permutation null (topology shuffle, splicing preserved), flags p < 0.01, excludes low‑confidence (< 1.5 SD), extracts genes, filters > 0.1 pseudotime units, ranks. | FR‑004, FR‑005 | — |
| **6 – Power Analysis** | `power_analysis.py` simulates power for divergence (d = 0.5) and enrichment (Δ = 0.3) with 10 000 Monte‑Carlo runs; aborts if power < 80 %. | FR‑011 | SC‑007 |
| **7 – Enrichment & Cross‑Dataset Validation** | `enrichment.py` loads **verified gene‑set** from the `GSE (json)` resource, performs Fisher’s exact test & two‑sided t‑test, BH‑corrects (p < 0.01). `validate.py` runs 500 bootstraps, computes 95 % CI, and Spearman correlation (≥ 0.80 for top‑3 genes). | FR‑006, FR‑008 (using verified set) | SC‑002, SC‑003, SC‑006 |
| **8 – Reporting** | `report.py` assembles all figures, tables, runtime/memory summary, and inserts the observational disclaimer (FR‑009). | FR‑007, FR‑009 | SC‑004 |

## Data Availability & Feasibility
- **Download method**: GEO accession metadata endpoint (`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<ACC>&targ=self&form=text`). No authentication required.  
- **Variable fit**: Marker‑gene presence is checked dynamically (FR‑010). Missing markers are reported, not assumed.  
- **Compute**: All steps run on CPU; optional GPU for permutation only if a free Kaggle GPU is detected. Memory usage stays < 7 GB; total runtime ≤ 5 h.  
- **Large datasets**: If a raw matrix exceeds memory, we stream it using `scanpy.read_10x_mtx(..., chunked=True)`; however the four GEO datasets comfortably fit within the runner limits after QC.  

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| GEO download fails (network) | 5 retries with exponential back‑off; graceful degradation (dataset marked `unavailable`). |
| QC filter removes all cells | Curated mitochondrial list includes Ensembl IDs **and** `MT-` symbols; unit test ensures at least 10 % cells remain on synthetic data. |
| Batch‑effect dominates velocity | Harmony applied before velocity; batch‑mixing metrics logged. |
| Velocity alignment fails | Up to 2 retries with higher regularization; failure logged and dataset excluded from cross‑validation. |
| No verified therapy‑response signature | Use the open gene‑set extracted from the verified `GSE (json)` resource; clearly state this substitution and cite the URL. |
| Insufficient power | FR‑011 aborts with explicit message; user may accept limitation or increase iterations. |
| Multiple‑testing inflation | Benjamini‑Hochberg correction applied throughout. |

---
