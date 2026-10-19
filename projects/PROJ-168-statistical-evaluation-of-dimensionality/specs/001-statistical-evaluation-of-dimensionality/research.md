# Research: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

## 1. Dataset Strategy

The analysis requires three scRNA‑seq datasets with raw count matrices and cell‑type annotations. Verified open sources are listed below. Where the original GEO accession lacks a verified download (GSE111322, GSE150728), we substitute with open datasets that satisfy the same scientific requirements.

| Dataset ID (used) | Verified Source | Access Method | Notes |
|-------------------|-----------------|---------------|-------|
| **GSE131907** | `https://huggingface.co/datasets/mukul54/LUAD_GSE131907/resolve/main/analysis/cluster_markers.csv` | `datasets.load_dataset("mukul54/LUAD_GSE131907", split="train")` → extract `counts` column | Raw counts + ground‑truth cell‑type labels. |
| **GSE130148** (substitutes GSE111322) | `https://huggingface.co/datasets/katarinayuan/scCello-GSE130148/resolve/main/data/train-00000-of-00001-712606da9de22598.parquet` | `datasets.load_dataset("katarinayuan/scCello-GSE130148", split="train")` | Parquet with raw count matrix and metadata. |
| **PBMC‑3k** (substitutes GSE150728) | Loader: `import scanpy as sc; adata = sc.datasets.pbmc3k()` | `scanpy` built‑in loader | ~2 700 cells, raw counts, annotated cell types. |

All datasets are fetched programmatically during **Phase 0**; each download is checksummed (SHA‑256) and recorded in `data/manifest.json`. The pipeline aborts if any dataset fails the **raw‑count verification** (i.e., missing a `counts` field).

### Raw‑Count Verification (Phase 0)
- Load each dataset.  
- Assert that `counts` is a 2‑D integer array (cells × genes).  
- If the check fails, write `status: "Unavailable"` for that dataset and halt execution with a clear error message.

### Edge Cases
- **< 500 cells**: geometric diagnostics (intrinsic dimensionality, local density) are skipped; a warning is logged.  
- **Missing cell‑type labels**: fidelity metrics for that dataset are marked “Unavailable” and excluded from the mixed‑effects model.  

## 2. Embedding & Geometric Diagnostics

### Embedding Generation (Phase 2)
| Method | Parameters | Output |
|--------|------------|--------|
| **PCA** | `n_components=30` (CPU) | `data/embeddings/<dataset_id>_pca.csv` |
| **t‑SNE** | `perplexity=30`, `n_iter=1000` (CPU) | `data/embeddings/<dataset_id>_tsne.csv` |
| **UMAP** | `n_neighbors=15`, `min_dist=0.1` (CPU) | `data/embeddings/<dataset_id>_umap.csv` |

All embeddings are 2‑dimensional for visualization; the PCA file also retains the full 30‑component matrix for downstream checks.

### Geometric Descriptors (computed on high‑dimensional space, Phase 2)
- **Global Intrinsic Dimensionality** – Levina & Bickel MLE estimator, k = 15, 10 000 random unordered cell pairs (deterministic RNG seed = 42).  
- **Local Density** – average distance to the 15‑nearest neighbours, same sampling scheme.  

Results are saved as `data/processed/<dataset_id>_geometric.json`.

## 3. Fidelity & Statistical Strategy

### Primary Fidelity (Phase 3)
- **Clustering**: Leiden algorithm on each embedding, **fixed resolution = 0.5**, random seed = 42.  
- **Metrics**: Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI) against ground‑truth labels.  
- **Transformation**: Both ARI and NMI are **logit‑transformed** before any regression.  
- Stored in `data/metrics/fidelity_<dataset_id>.json`.

### Sensitivity Analysis (Phase 4)
- **Silhouette thresholds**: {0.4, 0.5, 0.6}.  
- For each threshold, re‑run Leiden (same resolution), recompute ARI/NMI, and calculate the **variance across thresholds**.  
- The variance must be **< 0.05** (SC‑001). Results saved in `data/metrics/sensitivity_<dataset_id>.json`.

### Mixed‑Effects Modeling (Phase 5)
- **Model**: `logit_fidelity ~ method + intrinsic_dimensionality + local_density + (1|dataset)` using `statsmodels.MixedLM`.  
- **Assumption Check**: Shapiro‑Wilk test on residuals; if p < 0.05, fall back to a **permutation ANOVA** (10 000 permutations) for a robust p‑value.  
- **Collinearity**: Compute Variance Inflation Factor after dropping one dummy level; abort if any VIF ≥ 5 (SC‑005).  
- **Multiple‑Testing**: Benjamini‑Hochberg correction applied to all p‑values (SC‑002).  
- Output written to `data/results/statistical_result.yaml`.

### Observational Disclaimer
All effects are **associational**; the language in the final report will avoid causal phrasing.

## 4. Compute Feasibility & Constraints

| Resource | Plan |
|----------|------|
| **CPU** | All steps run on the free‑tier runner (2 CPU cores). |
| **Memory** | Sparse matrices keep peak RSS ≈ 5 GB; `psutil` monitors and aborts > 7 GB (SC‑003). |
| **Runtime** | Sampling caps dataset size; total expected wall‑clock < 3 h; abort > 21 600 s (SC‑004). |
| **Disk** | Raw JSON/parquet < 100 MB total; processed files ≤ 2 GB. |

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| Use verified open substitutes for missing GEO datasets | Guarantees reproducible, downloadable data; satisfies FR‑001 without fabricating URLs. |
| Fixed Leiden resolution = 0.5 for primary fidelity | Removes per‑method optimization bias; aligns with FR‑005 (requires clustering but does not mandate variable resolution). |
| Sensitivity sweep limited to silhouette thresholds | Meets FR‑007 while keeping CPU load manageable. |
| Mixed‑Effects model with permutation fallback | Ensures valid inference even if normality (SC‑005) fails. |
| Logit‑transform ARI/NMI before modeling | Handles bounded outcome, improves linearity assumptions. |
| Abort on missing raw counts (Phase 0) | Enforces Constitution I (full reproducibility). |

---
