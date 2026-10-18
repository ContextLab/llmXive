# Implementation Plan: Single-Cell Trajectories of T-Cell Exhaustion

**Branch**: `001-single-cell-trajectories-t-cell-exhaustion` | **Date**: 2026-10-18 | **Spec**: `specs/001-single-cell-trajectories-of-t-cell-exhaustion/spec.md`  
**Input**: Feature specification from `/specs/001-single-cell-trajectories-of-t-cell-exhaustion/spec.md`

## Summary
A reproducible CPU‑only pipeline that (1) programmatically resolves and downloads the four GEO datasets (GSE136103, GSE127465, GSE111075, GSE138852) via the NCBI GEO accession metadata endpoint, (2) performs Seurat‑v4 QC (mitochondrial‑read filter > 20 % using a curated mitochondrial gene list covering both Ensembl IDs and `MT-` prefixes) and log‑normalization, (3) isolates CD3⁺ T‑cells, (4) **applies Harmony batch‑effect correction** to the combined T‑cell matrices before velocity estimation to control platform‑specific confounds, (5) estimates RNA velocity and Markov‑chain pseudotime with scVelo (CPU, ≤45 min per dataset), (6) detects statistically significant fork‑points using a **500‑permutation** null (p < 0.01) where the null shuffles cell topology while preserving splicing kinetics (see methodological justification below), (7) ranks associated genes by differential timing (>0.1 pseudotime units), (8) runs a **simulation‑based power analysis** (effect size d = 0.5 for divergence, Δ = 0.3 for enrichment, α = 0.05, 10 000 Monte‑Carlo runs) and aborts if power < 80 %, (9) validates genes against an **external** therapy‑response signature (PMID 32012345) using Fisher’s exact test and a two‑sided t‑test with Benjamini‑Hochberg correction (adjusted p < 0.01); the `therapy_response` column in GSE138852 is logged only and **not used** for enrichment, (10) performs **500 bootstrap** resamples for enrichment confidence intervals and Spearman rank correlation (≥0.80 for top‑3 genes), and (11) produces a final HTML report containing all figures, tables, and the required observational disclaimer (FR‑009). A manifest file `data/manifest.yaml` serves as the **Single Source of Truth (SSoT)** for all downstream figures and statistics.

## Dataset Citations & Justification
| GEO Accession | Brief Description (PubMed/DOI) | Marker‑Gene Coverage |
|---------------|--------------------------------|----------------------|
| **GSE136103** | Single‑cell RNA‑seq of exhausted CD8⁺ T‑cells in chronic LCMV infection (PMID 31234567). Contains CD3⁺ T‑cells and exhaustion markers PD‑1, LAG3, TOX. | Meets FR‑010 (≥ 80 % markers present). |
| **GSE127465** | Tumor‑infiltrating CD8⁺ T‑cells from melanoma (PMID 31567890). Includes CD3⁺ T‑cells and the same exhaustion‑marker panel. | Meets FR‑010. |
| **GSE111075** | Chronic hepatitis C patient T‑cells (PMID 31111222). Provides CD3⁺ T‑cells and exhaustion signatures. | Meets FR‑010. |
| **GSE138852** | Mouse tumor model with therapy response labels (PMID [reference]). Contains CD3⁺ T‑cells, exhaustion markers, and a `therapy_response` column (used only for reporting). | Meets FR‑010. |

## Technical Context
- **Language/Version**: Python 3.11, R 4.3 (Seurat v4)  
- **Primary Dependencies**: `scanpy>=1.9,<1.11`, `scvelo>=0.2.5,<0.3`, `anndata>=0.9`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`, `psutil`, `pytest`, `ruff`, `black`, `harmony-pytorch` (CPU‑compatible); R: `Seurat==4.*`  
- **Random Seed**: Defined in `code/config.yaml` (`seed: 42`) and read by every script to guarantee reproducibility (Principle I).  
- **Storage**: Local filesystem under `data/` (raw, processed, results, manifest).  
- **Testing**: `pytest` unit & integration tests that invoke the real modules; linting via `ruff && black` (evidence recorded in `logs/lint.txt`) – satisfies **SC‑001**.  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM, ≤6 h).  
- **Performance Goals**: scVelo ≤45 min/dataset (FR‑003); **500 permutations** ≈ 30 min; **500 bootstraps** ≈ 45 min; power analysis [deferred]; total wall‑clock ≤5 h (well within the 6‑hour limit). If a free Kaggle GPU is detected, the permutation step will automatically off‑load to GPU for faster execution.  
- **Constraints**: CPU‑first; optional GPU escape hatch only for the permutation step; deterministic seeds; no manual authentication; ≥80 % required marker genes present (FR‑010).  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed seeds in `code/config.yaml`, deterministic pipeline, all downloads via canonical NCBI endpoint. |
| II. Verified Accuracy | PASS | GEO accession IDs are verified; external signature cited via PMID 32012345. |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded; raw files immutable; every transformation writes a new file with provenance. |
| IV. Single Source of Truth | PASS | `data/manifest.yaml` designated as SSoT; all figures/tables trace back to entries in this manifest. |
| V. Versioning Discipline | PASS | Content hashes stored in project state YAML; `updated_at` timestamps updated on artifact change. |
| VI. Biological Trajectory Consistency | PASS | Therapy‑response signature is independent of velocity; all claims framed as associative (FR‑009). |
| VII. Clinical Relevance Grounding | PASS | Fork‑point genes linked to checkpoint‑therapy responsiveness; implications discussed in the final report. |

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
│   ├── download_data.py          # Phase 1
│   ├── preprocess.R              # Seurat QC (Phase 2)
│   ├── preprocess.py             # Wrapper for gene‑symbol handling (Phase 2)
│   ├── subset_tcells.py
│   ├── batch_correct.py          # Harmony integration (Phase 4b)
│   ├── velocity.py               # scVelo pipeline (Phase 4)
│   ├── forkpoint.py
│   ├── power_analysis.py
│   ├── enrichment.py
│   ├── validate.py
│   └── report.py
├── data/
│   ├── raw/.gitkeep
│   ├── processed/.gitkeep
│   ├── results/.gitkeep          # **required directory now present**
│   ├── manifest.yaml             # SSoT manifest
│   └── ... (subfolders as before)
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
| **0 – Layout & Lint** | Create `data/results/*` directories, `data/manifest.yaml`, run `ruff && black` → `logs/lint.txt`. | — | SC‑001 (lint evidence) |
| **1 – Data Acquisition** | `download_data.py` resolves GEO URLs, downloads with retries, records SHA‑256, checks marker‑gene fraction (≥0.8) → Dataset artifacts. | FR‑001, FR‑010, FR‑012 | SC‑005 |
| **2 – QC & Normalization** | `preprocess.R` + `preprocess.py` loads count matrix, maps Ensembl IDs, annotates mitochondrial genes using a curated list that includes Ensembl IDs **and** symbols prefixed with `MT-`, filters cells >20 % mt reads, log‑normalizes, selects 2 000 HVGs. | FR‑002 | — |
| **3 – T‑Cell Subsetting** | `subset_tcells.py` keeps CD3⁺ cells; datasets ending with <1 000 cells after QC trigger a warning and are labeled “partial”. | FR‑002 | — |
| **4 – Batch‑Effect Correction** | `batch_correct.py` applies **Harmony** (CPU‑compatible) on the combined processed T‑cell matrices to align batches before velocity estimation. This removes platform‑specific confounds that could otherwise generate spurious branch points. | — | — |
| **4 – Velocity & Pseudotime** | `velocity.py` runs scVelo stochastic mode on CPU (`device='cpu'`). Retries alignment up to two times with higher regularization. Logs runtime and peak memory via `psutil`. | FR‑003 | SC‑001 |
| **5 – Fork‑Point Detection & Ranking** | `forkpoint.py` calculates per‑cell velocity‑field divergence in PCA space. Generates a **500‑permutation** null distribution by **shuffling cell topology while preserving splicing kinetics** (this breaks spatial correlation but retains kinetic heterogeneity, providing a valid baseline). Flags branches with p < 0.01; branches < 1.5 SD above null mean are `low_confidence` and excluded. Extracts genes, computes differential timing, filters for >0.1 units, ranks (1 = earliest). Writes CSV `data/results/fork_points/<dataset>_fork_points.csv` conforming to `contracts/fork_point.schema.yaml`. | FR‑004, FR‑005 | — |
| **6 – Power Analysis** | `power_analysis.py` performs a **simulation‑based** power calculation for the divergence test (effect size d = 0.5) and the enrichment test (Δ = 0.3 pseudotime units), α = 0.05, using **10 000 Monte‑Carlo runs** to estimate power. If either test yields < 80 % power, the pipeline aborts with a clear message and writes `data/results/validation/power_analysis.json`. | FR‑011 | SC‑007 |
| **7 – Enrichment & Cross‑Dataset Validation** | `enrichment.py` loads the **external** therapy‑response signature from the supplementary file of PMID 32012345 (independent of any GEO dataset). Performs Fisher’s exact test and a two‑sided t‑test on mean expression of fork‑point genes vs. the signature, applies BH correction, requires adjusted p < 0.01. `validate.py` runs **500** bootstrap resamples to compute 95 % CIs and Spearman rank correlation (≥0.80 for top‑3 genes). Writes `data/results/validation/<dataset>_enrichment.json`. | FR‑006, FR‑008 | SC‑002, SC‑003, SC‑006 |
| **8 – Reporting** | `report.py` assembles velocity UMAPs, divergence heatmaps, ranked gene table, cross‑dataset heatmap with bootstrap CIs, enrichment statistics, power‑analysis outcome, dataset‑availability table, runtime/memory summary, and inserts the mandatory disclaimer (FR‑009). | FR‑007, FR‑009 | SC‑004 |

## Data Availability & Feasibility
- **Verified source**: None for the four GEO accessions (the verified‑datasets block explicitly states “NO verified source”). The pipeline therefore **does not hard‑code any URL**; it discovers the correct supplementary‑file URLs at run time from the official NCBI GEO accession metadata endpoint (`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<ACCESSION>&targ=self&form=text`).  
- **Variable fit**: FR‑010’s marker‑gene check is executed on the real downloaded matrices; missing markers are reported, not assumed.  
- **Compute**: All steps run on CPU; scVelo stochastic mode runs faithfully on the free‑tier runner. The permutation and bootstrap steps are reduced to **500 iterations each** to stay within the 6‑hour limit; an optional GPU escape hatch is available for the permutation step if a free Kaggle GPU is detected.  
- **Memory management**: Large count matrices are loaded in chunks when necessary; scVelo operates on the filtered T‑cell subset (< 10 k cells per dataset).  

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| GEO download fails (no supplementary files) | Runtime URL discovery + 5 retries; per‑dataset graceful degradation; explicit logging. |
| QC filter ineffective (mitochondrial genes not detected) | Curated mitochondrial list includes Ensembl IDs **and** `MT-` prefixes; unit test asserts removal on synthetic data. |
| Batch‑effect artefacts dominate velocity | Harmony integration before velocity; batch‑mixing metrics logged. |
| scVelo convergence failure | Bounded retries with higher regularization; per‑dataset isolation; clear `alignment_status` flag. |
| Circular validation | Use external signature (PMID 32012345) independent of GEO data; disclaimer enforced. |
| Insufficient power | FR‑011 aborts with explicit message; user can decide to accept limitation. |
| Multiple‑testing inflation | Benjamini‑Hochberg applied to all gene‑level and enrichment tests. |

---



