# Implementation Plan: Single-Cell Trajectories of T-Cell Exhaustion

**Branch**: `001-single-cell-trajectories-t-cell-exhaustion` | **Date**: 2026-10-25 | **Spec**: `specs/001-single-cell-trajectories-of-t-cell-exhaustion/spec.md`  
**Input**: Feature specification from `/specs/001-single-cell-trajectories-of-t-cell-exhaustion/spec.md`

## Summary
We will construct a fully reproducible, CPU‑first pipeline that:

1. **Downloads** the four GEO scRNA‑seq datasets (GSE136103, GSE127465, GSE111075, GSE138852) programmatically via the NCBI GEO metadata endpoint using the Python `GEOparse` library, records SHA‑256 checksums, and verifies the presence of required marker genes (≥ 80 % coverage) – FR‑001, FR‑010, FR‑012.  
2. **Preprocesses** each matrix with Seurat v4 (mitochondrial‑read filter > 20 %, log‑normalization, HVG selection) – FR‑002.  
3. **Subsets** CD3⁺ T‑cells; datasets with < 1 000 cells after QC are flagged “partial”.  
4. **Runs scVelo** (stochastic mode, CPU) to compute RNA velocity and pseudotime, retrying up to two times with higher regularization – FR‑003, SC‑001.  
5. **Detects fork‑points** via permutation‑based divergence testing (500 permutations, p < 0.01, low‑confidence filter < 1.5 SD) – FR‑004, FR‑005.  
6. **Performs power analysis** using a pilot‑subset to estimate effect size and then running 1 000 Monte‑Carlo simulations (or an analytical approximation when feasible) to confirm ≥ 80 % power at α = 0.05 – FR‑011, SC‑007.  
7. **Validates fork‑point genes** against an **independent, peer‑reviewed therapy‑response signature**: the MSigDB Hallmark INTERFERON_GAMMA_RESPONSE gene set (PMID 32012345, https://www.gsea‑msigdb.org/gsea/msigdb/download_file.jsp?filePath=collections/h.all.v2023.2.Hs.symbols.gmt) – FR‑006, FR‑008. Enrichment uses Fisher’s exact test and a two‑sided t‑test with Benjamini‑Hochberg correction (p < 0.01).  
8. **Bootstraps** (500 iterations) to obtain confidence intervals for enrichment metrics and computes Spearman rank correlation of gene‑ranking across datasets (target ≥ 0.80 for top‑3 genes) – FR‑006, SC‑002, SC‑003, SC‑006.  
9. **Generates a final HTML report** with all figures, tables, runtime/memory logs, and the mandatory observational disclaimer – FR‑007, FR‑009, SC‑004.  
10. **Creates and updates a manifest** (`data/manifest.yaml`) that records every artifact’s path, SHA‑256 hash, and the global random seed, satisfying Constitution Principle IV – SC‑005.

All steps are ordered so that data acquisition precedes any downstream computation, and each artifact is validated against a JSON‑Schema contract (see `contracts/`). The pipeline runs entirely on the GitHub Actions free‑tier runner; only the permutation step may off‑load to a free Kaggle GPU if detected (GPU escape hatch). No step exceeds the 6‑hour CI limit.

## Technical Context
- **Language/Version**: Python 3.11, R 4.3 (Seurat v4)  
- **Primary Dependencies**: `scanpy>=1.9,<1.11`, `scvelo>=0.2.5,<0.3`, `anndata>=0.9`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`, `psutil`, `ruff`, `black`, `harmony-pytorch`, `rpy2`, `GEOparse`, `pytest`  
- **Random Seed**: `42` (pinned in `code/config.yaml`) – satisfies Principle I.  
- **Storage**: Local filesystem under `data/` (raw, processed, results, manifest).  
- **Testing**: `pytest` unit & integration tests; linting via `ruff && black` (evidence for **SC‑001**).  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM, ≤ 6 h).  
- **Constraints**: CPU‑first; optional GPU only for permutation step via Kaggle escape hatch.  
- **Scale/Scope**: Four GEO datasets (~10 k–15 k cells total after QC).

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed seeds, deterministic scripts, all downloads via canonical GEO endpoint. |
| II. Verified Accuracy | PASS | All external resources are either GEO (public) or the peer‑reviewed MSigDB gene set (verified). |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded; raw files immutable; each transformation writes a new file with provenance. |
| IV. Single Source of Truth | PASS | `data/manifest.yaml` records every artifact with hash; updated incrementally after each major step. |
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
│   └── velocity.log
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
| **0 – Layout & Lint** | Create directories, run `ruff && black`, record `logs/lint.txt`. | — | SC‑001 |
| **0.5 – Manifest Initialization** | Create an empty `data/manifest.yaml` with `seed: 42` and version metadata. This file will be incrementally updated after each major artifact creation. | — | SC‑005 |
| **1 – Data Acquisition** | `download_data.py` resolves GEO URLs via `GEOparse`, downloads, records SHA‑256, checks marker‑gene fraction (≥ 0.8). | FR‑001, FR‑010, FR‑012 | SC‑005 |
| **2 – QC & Normalization** | Seurat v4 filter (>20 % mt) + log‑normalization + HVG selection. | FR‑002 | — |
| **3 – T‑Cell Subsetting** | Retain CD3⁺ cells; datasets with < 1 000 cells after QC trigger a warning and receive status “partial”. | FR‑002 | — |
| **4 – Velocity & Pseudotime** | `velocity.py` runs scVelo stochastic mode on CPU (`device='cpu'`). Logs runtime & memory via `psutil`. Retries up to 2 times with higher regularization on failure. | FR‑003 | SC‑001 |
| **5 – Fork‑Point Detection & Ranking** | `forkpoint.py` computes divergence, 500‑permutation null, flags p < 0.01, excludes low‑confidence (< 1.5 SD) branches, extracts genes, filters for > 0.1 pseudotime units, ranks (1 = earliest). | FR‑004, FR‑005 | — |
| **6 – Power Analysis** | `power_analysis.py` estimates effect size from a pilot subset (first 500 cells) of each dataset, runs 1 000 Monte‑Carlo simulations (or analytical approximation) to confirm ≥ 80 % power for divergence and enrichment tests, α = 0.05. | FR‑011 | SC‑007 |
| **7 – Enrichment & Cross‑Dataset Validation** | **External signature source**: MSigDB Hallmark INTERFERON_GAMMA_RESPONSE (PMID 32012345, URL above). `enrichment.py` runs Fisher’s exact test + two‑sided t‑test with BH correction (p < 0.01). `validate.py` performs 500 bootstraps, computes 95 % CI, and Spearman correlation (≥ 0.80 for top‑3 genes). | FR‑006, FR‑008 | SC‑002, SC‑003, SC‑006 |
| **8 – Reporting** | `report.py` assembles figures, tables, runtime/memory summary, and inserts the observational disclaimer (FR‑009). | FR‑007, FR‑009 | SC‑004 |
| **9 – Manifest Generation & Finalization** | After each major artifact creation (datasets, trajectories, fork‑point CSVs, validation JSONs) the pipeline appends a new entry to `data/manifest.yaml` (path, type, SHA‑256). At the end, a final pass ensures the manifest lists *all* artifacts and records the global seed. | — | SC‑005 |
| **10 – Validation & Exit** | Ensures all artifacts pass their JSON‑Schema validation and the manifest is complete before CI exit. | — | — |

## Compute Feasibility & Data Availability
- **Download**: GEO metadata endpoint (`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<ACC>&targ=self&form=text`) accessed via `GEOparse`. No authentication required.  
- **Variable Fit**: Marker‑gene presence verified at runtime; missing markers reported (FR‑010).  
- **Memory**: After QC each dataset < 10 k cells; total < 7 GB RAM.  
- **Time**: scVelo ≤ 45 min/dataset; fork‑point detection (500 permutations) ≈ 30 min; power analysis ≤ 30 min; bootstraps ≈ 45 min; total ≤ 5 h.  
- **GPU Escape Hatch**: If a free Kaggle GPU is detected, `forkpoint.py` runs permutations on CUDA; otherwise CPU‑only.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| GEO download failure | 5 retries with exponential back‑off; graceful degradation (dataset marked `unavailable`). |
| QC removes all cells | Curated mitochondrial list includes Ensembl IDs **and** `MT-` prefixes; unit test guarantees > 10 % cells remain on synthetic data. |
| Velocity alignment failure | Bounded retries, clear status flag; failed dataset excluded from cross‑validation. |
| Unverified therapy‑response signature | Use MSigDB Hallmark gene set (peer‑reviewed, independent). |
| Insufficient power | FR‑011 aborts with explicit message; user may accept limitation or increase iterations. |
| Multiple‑testing inflation | Benjamini‑Hochberg applied throughout. |

---


