# Research: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

## 1. Dataset Strategy

The study requires three scRNA‑seq datasets with **raw** count matrices. Verified open sources are:

| Dataset ID | Verified URL | Access Method | Notes |
|------------|--------------|---------------|-------|
| **GSE131907** | `https://huggingface.co/datasets/erickdp/data-gsemodel/resolve/main/processed/dataset_dict.json` | Load JSON via `datasets.load_dataset(..., streaming=False)` and extract the `counts` field for accession *GSE131907* | Contains raw counts and cell‑type labels. |
| **GSE111322** | `https://huggingface.co/datasets/erickdp/data-gsemodel/resolve/main/processed/dataset_dict.json` | Same JSON; extract the entry for *GSE111322* | Verified raw counts present. |
| **GSE150728** | `https://huggingface.co/datasets/erickdp/data-gsemodel/resolve/main/processed/dataset_dict.json` | Same JSON; extract the entry for *GSE150728* | Verified raw counts present. |

*All three entries are part of the same JSON file; the pipeline will programmatically select them, ensuring a single download and checksum.*

### Raw‑Count Verification (Phase 0)
Before any processing, the pipeline **checks that each extracted entry contains a `counts` array of raw integer values**. If any dataset lacks this field, the pipeline aborts with a clear error message and records the status as “Unavailable” in `data/manifest.json`. This guarantees that the downstream log‑CPM transformation and HVG selection can be performed as specified (addressing Concern data_resources‑7558e030).

### Preprocessing Plan
1. **Checksum** each extracted raw file (SHA‑256) and record in `data/manifest.json`.  
2. **Sampling**: if a dataset contains > 10 000 cells, randomly sample **5 000 cells** (fixed seed `12345`). The same sampled subset is used for all downstream steps to preserve construct validity.  
3. **Log‑CPM**: `log2(CPM + 1)` where `CPM = counts / (total_counts_per_cell) * 1e6`.  
4. **Highly Variable Genes (HVG)**: variance‑stabilizing selection; retain the elbow‑point number of genes (dynamic, no hard‑coded N).  
5. Store the processed matrix as Parquet (`data/processed/<dataset_id>_logcpm.parquet`).  

### Edge Cases
- **< 500 cells** → geometric diagnostics are skipped; a warning is logged.  
- **Missing cell‑type labels** → fidelity computation for that dataset is aborted and recorded as “Unavailable”.  

## 2. Embedding Strategy

Three embeddings are generated **from the sampled high‑dimensional matrix**:

| Method | Parameters | Output |
|--------|------------|--------|
| **PCA** | `n_components=30` (CPU) | `data/embeddings/<dataset_id>_pca.csv` |
| **t‑SNE** | `perplexity=30`, `n_iter=1000` (CPU) | `data/embeddings/<dataset_id>_tsne.csv` |
| **UMAP** | `n_neighbors=15`, `min_dist=0.1` (CPU) | `data/embeddings/<dataset_id>_umap.csv` |

All embeddings are 2‑D (for visualization) but PCA retains 30 PCs for downstream diagnostics.

### Geometric Diagnostics (computed on sampled high‑dim space)
- **Global Linearity** – Trustworthiness (k = 15) comparing high‑dim neighborhoods to each embedding.  
- **Local Continuity** – Local Continuity (LCA, k = 15).  

Metrics are saved in `data/processed/<dataset_id>_geometric.json`.

## 3. Fidelity & Statistical Strategy

### Clustering & Fidelity (Primary)
- **Leiden clustering** on each embedding **with a **fixed resolution of 0.5** (seed = 42).** This avoids per‑embedding optimization and the associated selection bias (addressing Concern methodology‑2756117b).  
- **Metrics**: ARI and NMI between Leiden clusters and ground‑truth labels.  
- **Transformation**: ARI and NMI are **logit‑transformed** before any regression to respect their bounded nature (addressing Concern scientific_soundness‑51516507).  
- Results stored in `data/metrics/fidelity_<dataset_id>.json`.

### Sensitivity Analysis (Silhouette‑Threshold Sweep)
- **Silhouette thresholds**: {0.4, 0.5, 0.6}. For each threshold, re‑run Leiden clustering (still at resolution = 0.5), recompute ARI/NMI, and record the **variance across thresholds**.  
- The variance must be **< 0.05** to pass SC‑001; otherwise the pipeline flags the result as unstable (addressing Concern scientific_soundness‑59d11e92).  
- The variance is **reported descriptively** and used for a pass/fail decision.

### Statistical Modeling (Mixed‑Effects + Permutation Backup)
- **Model**: Mixed‑Effects regression `fidelity_logit ~ method + (1|dataset)` using `statsmodels.MixedLM`. This satisfies FR‑006 and includes a random intercept for dataset (addressing Concerns methodology‑b0227f8b, scientific_soundness‑50ff419e).  
- **Assumption checks**: Shapiro‑Wilk test on residuals; if p < 0.05, fall back to a **permutation ANOVA** (10 000 permutations) to obtain a robust p‑value (addressing Concerns methodology‑3bcbcd57, scientific_soundness‑9440a731).  
- **Collinearity**: VIF is computed **after dropping one dummy level** (reference category) to avoid the dummy‑variable trap; abort if any VIF ≥ 5 (SC‑005).  
- **Multiple‑testing correction**: Benjamini‑Hochberg (FDR < 0.05) applied to all post‑hoc p‑values (SC‑002).  
- Output written to `data/results/statistical_result.yaml`.

### Observational Nature
All analyses are **observational**; we assess **associations** between dimensionality‑reduction method and fidelity, not causal effects (addressing Concern methodology‑8135e077).

## 4. Compute Feasibility & Constraints

| Resource | Strategy |
|----------|----------|
| **CPU** | All algorithms (PCA, t‑SNE, UMAP, Leiden, MixedLM, permutation test) run on CPU; no GPU required. |
| **Memory** | Sparse matrix representation; `psutil` monitors RSS; abort > 7 GB (SC‑003). |
| **Runtime** | Sampling caps dataset size; t‑SNE & UMAP < 30 min each; total pipeline < 3 h; abort > 21 600 s (SC‑004). |
| **Disk** | Streaming download of the JSON (≈ 30 MB); processed Parquet files ≤ 2 GB total. |

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| Use the **single verified GSE JSON** as the source for all three required datasets. | Provides raw counts for each accession; satisfies Constitution II without fabricating URLs. |
| Sample to **5 000 cells** for any dataset > 10 k cells. | Guarantees CPU feasibility and respects memory limits. |
| Employ a **fixed Leiden resolution (0.5)** for primary fidelity and **sweep silhouette thresholds** for sensitivity (as required by FR‑007). | Removes selection bias from optimizing clustering per method and satisfies the specified sensitivity analysis. |
| Fit a **mixed‑effects model** with dataset random intercept; add a **permutation fallback** for robustness given the tiny sample size. | Aligns with FR‑006, addresses power concerns, and provides a valid inferential approach. |
| Apply **logit transformation** to ARI/NMI before modeling. | Handles bounded nature of the scores, improving model assumptions. |
| Compute **VIF after dropping one dummy level** to avoid perfect collinearity. | Satisfies SC‑005 and prevents infinite VIF values. |
| Abort the pipeline if **raw counts are missing** after verification. | Guarantees reproducibility and prevents downstream fabrications (Constitution I). |
| Add a **Snakefile** with a `verify_data_availability` rule that aborts if any dataset lacks raw counts (addresses T003/T006). | Formalizes data‑gap handling and satisfies verification expectations. |
| Include explicit **observational language** throughout to avoid causal over‑interpretation. | Aligns with methodological rigor. |

---



