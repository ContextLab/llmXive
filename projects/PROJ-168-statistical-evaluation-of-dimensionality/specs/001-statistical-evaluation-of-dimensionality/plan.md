# Implementation Plan: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Branch**: `001-gene-regulation` | **Date**: 2026-07-04 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a statistical pipeline to evaluate the fidelity of dimensionality reduction techniques (PCA, t‑SNE, UMAP) on single‑cell RNA‑sequencing (scRNA‑seq) data. Due to critical data gaps (missing raw count matrices for required datasets), the study is currently **blocked** and cannot proceed as a generalizable statistical evaluation. The pipeline is designed to **abort** if the required datasets (GSE131907, GSE111322, GSE150728) are not available as raw count matrices. If a single dataset with raw counts were available, the study would proceed as a **descriptive case study** using Fixed-Effects ANOVA, as a Mixed-Effects Model is statistically invalid with N≤3 datasets. The pipeline:

1. **Verifies** the availability of raw count matrices for the three required datasets (Phase 0).
2. **Downloads** and validates raw count matrices (or aborts if unavailable).  
3. **Preprocesses** (log‑CPM, variance‑stabilizing gene selection) on a **sampled high‑dimensional subset** ([deferred] cells if >10,000 cells).
4. **Computes** geometric diagnostics (Trustworthiness, Local Continuity) **on the sampled high‑dimensional space** (relative to the sampled embeddings) to satisfy FR‑002/003 while maintaining construct validity.  
5. **Generates** three embeddings (PCA, t‑SNE, UMAP) on the same sampled subset.  
6. **Performs** Leiden clustering, optimizes resolution via Silhouette Score, and calculates ARI/NMI against ground‑truth labels.  
7. **Fits** a **Fixed‑Effects ANOVA** (or Kruskal‑Wallis if normality fails) to compare methods **within the single dataset** – results are purely descriptive and not generalizable.  
8. **Conducts** a **Leiden‑resolution sensitivity sweep** (0.1 → 1.0) to assess stability of ARI/NMI, applying Benjamini‑Hochberg correction to all p‑values.

All steps are designed for CPU‑only GitHub Actions runners (≤2 CPU, ≤7 GB RAM, ≤14 GB disk, ≤6 h wall‑clock).

## Phase 0 – Data‑Gap Resolution (Critical Blocker)

| Task | Description | Outcome |
|------|-------------|---------|
| **0.1 Verify raw‑count sources** | Attempt to download raw count matrices for GSE131907, GSE111322, GSE150728 from verified URLs. | GSE131907: only a CSV of cluster markers is available → **raw counts missing**.<br>GSE111322 & GSE150728: **no verified source**. |
| **0.2 Search alternatives** | Programmatically query GEO via `geopy`/`GEOparse` for raw count files; if found, add to verified list. | If none found, proceed to step 0.3. |
| **0.3 Spec update** | If any required raw‑count source remains unavailable, **update `spec.md`** to a *Case‑Study* mode (single dataset) and mark FR‑001 as “Partially Met”. | Required before any downstream task. |
| **0.4 Abort condition** | If after steps 0.1‑0.3 no raw counts are available for **any** dataset, abort the pipeline with exit code 1 and log “No Data”. | Guarantees reproducibility and respects SC‑003/SC‑004. |

*The pipeline will not start unless Phase 0 completes successfully.*

## Phase 1 – Data Ingestion & Preprocessing

1. **Download** each dataset from its verified URL (or alternative found in Phase 0).  
2. **Checksum** the raw file (SHA‑256) and record in `data/manifest.json`.  
3. **Validate** presence of count matrix and cell‑type metadata.  
4. **Sampling strategy** (explicit as required by FR‑002/FR‑003):  
 * If `n_cells > 10,000`, randomly sample **[deferred] cells** (maintaining original gene set).
   * If `n_cells ≤ 10,000`, use all cells.  
   * **The same sampled subset is used for all downstream steps** (geometric diagnostics, embeddings, clustering) to ensure construct validity.
5. **Log‑CPM transformation**: `log(CPM + 1)`.  
6. **Highly variable gene (HVG) selection**: variance‑stabilizing method retaining the top N genes where N is the elbow point of the variance curve (dynamic, no hard‑coded number).  
7. **Store** the processed matrix as Parquet in `data/processed/`.

## Phase 2 – Embedding & Geometric Diagnostics

| Method | Parameters | Output |
|--------|------------|--------|
| **PCA** | `n_components=30` | 30‑dimensional coordinates (saved CSV). |
| **t‑SNE** | `perplexity=30`, `n_iter=1000` | 2‑D coordinates (saved CSV). |
| **UMAP** | `n_neighbors=15`, `min_dist=0.1` | 2‑D coordinates (saved CSV). |

*All embeddings are generated **from the sampled high‑dimensional matrix**.*

### Geometric Diagnostics (computed on **sampled high‑dimensional space** relative to embeddings)

* **Global Linearity** – Trustworthiness (k=15) computed on the **sampled** high-dimensional space, comparing neighborhood preservation to the **sampled** embeddings.  
* **Local Continuity** – Local Continuity (LCA, k=15) computed on the **sampled** high-dimensional space, comparing neighborhood preservation to the **sampled** embeddings.  

Metrics are stored in `data/processed/geometric_descriptors.json`.

## Phase 3 – Fidelity Evaluation & Statistical Modeling

### Clustering & Fidelity

* **Leiden clustering** on each embedding.  
* **Resolution optimization**: sweep resolutions 0.1 → 1.0 (step 0.1), compute Silhouette Score for each; pick resolution with maximal Silhouette.  
* **Metrics**: ARI and NMI against ground‑truth labels.  
* **Edge cases**:  
  * If ground‑truth labels missing → abort fidelity for that dataset, log error.  
  * If Leiden fails twice → mark result as “Unavailable”.

### Statistical Modeling (Fixed‑Effects ANOVA)

* **Model**: `fidelity ~ method` (method = PCA, t‑SNE, UMAP).  
* **Assumption checks**: Shapiro‑Wilk for normality; if violated, use Kruskal‑Wallis.  
* **Collinearity**: VIF computed for method dummy variables; abort if any VIF ≥ 5 (SC‑005).  
* **Multiple‑testing correction**: Benjamini‑Hochberg (FDR < 0.05) applied to all post‑hoc p‑values.  
* **Interpretation**: Results are **descriptive within the available dataset(s) only**; no causal claim about method superiority across datasets.

### Sensitivity Analysis (Leiden‑Resolution Sweep)

* Sweep resolutions {0.1, 0.2, … 1.0}.  
* Re‑compute ARI/NMI for each resolution.  
* Report variance of ARI and NMI across the sweep.  
* **Success criterion** (SC‑001): variance < 0.05 → stability passed.  
* This sweep **decouples** the unsupervised clustering optimization (Silhouette) from the supervised fidelity evaluation (ARI/NMI).

## Compute Feasibility & Constraints

* **Memory monitoring**: `psutil` records peak RSS; if > 7,000,000,000 bytes → **exit code 1** (SC‑003).  
* **Runtime monitoring**: wall‑clock timer; if total > 21,600 s → **exit code 1** (SC‑004).  
* **Sampling** ensures t‑SNE/UMAP fit within the 6 h limit on CPU‑only runners.

## Constitution Check (Updated)

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | **PASS** | Fixed seeds, immutable URLs, deterministic hyper‑parameters. |
| **II. Verified Accuracy** | **FAIL** | Two required datasets lack verified sources; GSE131907 source is invalid (markers only, not raw counts). Phase 0 Data‑Gap Resolution must succeed before proceeding, but currently it cannot. |
| **III. Data Hygiene** | **PASS** | Checksums, immutable raw files, derived artifacts stored separately. |
| **IV. Single Source of Truth** | **PASS** | All metrics trace to `data/` artifacts; no hand‑typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes recorded; state updated on artifact change. |
| **VI. Geometric Characterization** | **PASS** | Diagnostics computed on sampled high‑dimensional space (relative to sampled embeddings) as interpreted from FR‑002/003 with construct validity. |
| **VII. Ground‑Truth Fidelity** | **PASS** | Fidelity metrics calculated against ground‑truth labels; separation of diagnostics and evaluation maintained. |

## Tasks Overview (Ordered)

1. **Phase 0 – Data‑Gap Resolution** (must succeed).  
2. **Phase 1 – Ingestion & Preprocessing** (download → checksum → sample → transform).  
3. **Phase 2 – Embedding Generation & Diagnostics** (sample → embed → compute Trustworthiness/LCA).  
4. **Phase 3 – Fidelity & Statistics** (cluster → ARI/NMI → ANOVA → sensitivity sweep).  
5. **Artifact Export** (JSON/YAML reports, plots, schemas).  

All file paths, library versions, and random seeds are enumerated in `code/requirements.txt` and `code/main.py` (implemented by the Integrator).