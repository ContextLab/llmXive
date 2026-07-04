# Research: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

## 1. Dataset Strategy

The project requires three specific scRNA‑seq datasets: **GSE131907**, **GSE111322**, and **GSE150728**.

### Verified Sources & Access Strategy

| Dataset ID | Verified URL | Access Method | Notes |
|:--- |:--- |:--- |:--- |
| **GSE131907** | ` | Direct Download (CSV) | **Critical**: This file contains only cluster marker statistics, **not** the raw count matrix required for log‑CPM transformation and geometric diagnostics. No alternative verified raw‑count source exists in the allowed block. |
| **GSE111322** | **NO verified source found** | **Blocker** | Must be skipped; cannot satisfy FR‑001 without a verified raw‑count URL. |
| **GSE150728** | **NO verified source found** | **Blocker** | Same as above. |

> **Data‑Gap Resolution** (Phase 0) will attempt to locate alternative raw‑count sources via GEO (programmatic query). If no raw counts are found for any required dataset, the pipeline **aborts with exit code 1** and logs “No Data”. If at least GSE131907 raw counts become available, the study proceeds as a **single‑dataset case study**; the spec must be updated accordingly before any analysis.

### Data Preprocessing Plan

1. **Ingestion**: Download raw files from verified URLs (or alternative found in Phase 0).
2. **Validation**: Confirm presence of a count matrix and cell‑type label column.
3. **Sampling strategy** (explicit to satisfy FR‑002/FR‑003):
 * If `n_cells > 10,000`, **randomly sample [deferred] cells** (maintaining all genes).
 * If `n_cells ≤ 10,000`, use the full cell set.
 * The same sampled subset is used for **all downstream steps** (geometric diagnostics, embeddings, clustering) to maintain construct validity.
4. **Transformation**:
 * **Log‑CPM**: `log2(CPM + 1)`, where CPM = `counts / (total_counts * 1e6)`.
 * **HVG selection**: variance‑stabilizing method retaining the top N genes where N is the elbow point of the variance curve (dynamic).
5. **Geometric Diagnostics** (corrected from original spec):
 * Compute **Trustworthiness (k=15)** and **Local Continuity (LCA, k=15)** **on the sampled high‑dimensional matrix** (relative to the sampled embeddings). This satisfies FR‑002 and FR‑003 while keeping the computation feasible and construct valid.

### Edge‑case handling

* If a dataset has **< 500 cells**, the pipeline logs a warning and **skips geometric diagnostics** for that dataset.
* If ground‑truth labels are missing, fidelity calculation for that dataset is **aborted** and recorded as “Unavailable”.
* If Leiden fails to converge twice, the result is marked “Unavailable” and the pipeline continues.

## 2. Embedding Strategy

Three embeddings will be generated per valid dataset **on the sampled subset**:

| Method | Parameters | Constraints |
|:--- |:--- |:--- |
| **PCA** | `n_components=30` | CPU‑native, fast. |
| **t‑SNE** | `perplexity=30`, `n_iter=1000` | CPU‑only; if sampled subset > 20,000 cells (not the case with our [deferred]‑cell sample), further down‑sample to [deferred]. |
| **UMAP** | `n_neighbors=15`, `min_dist=0.1` | CPU‑only; same sampling rule as t‑SNE. |

**Geometric diagnostics** (Trustworthiness, LCA) are computed **on the sampled high-dimensional space relative to the embeddings**, providing a distortion measure that complements the high-dimensional diagnostics.

## 3. Fidelity & Statistical Strategy

### Clustering & Fidelity Metrics
* **Algorithm**: Leiden clustering on each embedding.
* **Optimization**: Sweep Leiden **resolution** from 0.1 to 1.0 (step 0.1); for each resolution compute Silhouette Score; select resolution with maximal Silhouette.
* **Metrics**:
 * **ARI** and **NMI** between Leiden clusters (at optimal resolution) and ground‑truth labels.
* **Edge case**: If Leiden fails twice, record “Unavailable”.

### Statistical Modeling (FR‑006 – corrected)

* **Model**: **Fixed‑Effects ANOVA** (or Kruskal‑Wallis if normality fails) with formula `fidelity ~ method`.
* **Dataset scope**: **Descriptive comparison within the available dataset(s) only**; no inference about general method superiority across datasets. Mixed-Effects Model is invalid with N≤3 datasets.
* **Assumption checks**:
 * **Normality** via Shapiro‑Wilk; fallback to Kruskal‑Wallis.
 * **Collinearity**: VIF for method dummy variables; abort if any VIF ≥ 5 (SC‑005).
* **Multiple‑comparison correction**: Benjamini‑Hochberg (FDR < 0.05) applied to all post‑hoc p‑values (SC‑002).

### Sensitivity Analysis (FR‑007 – corrected)

* **Sweep**: Leiden **resolution** values {0.1, 0.2, … 1.0}.
* **Output**: Variance of ARI and NMI across the sweep.
* **Success criterion**: Variance < 0.05 (SC‑001).
* **Rationale**: This sweep tests **stability of the clustering solution against ground‑truth** while **decoupling** the unsupervised Silhouette optimization from the supervised fidelity evaluation.

## 4. Compute Feasibility & Constraints

* **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 14 GB Disk).
* **Memory Management**:
 * Data loaded as `scipy.sparse` matrices.
 * `psutil` records peak RSS; if > 7,000,000,000 bytes → **exit code 1** (SC‑003).
* **Time Limit**: 6 h ([deferred] s).
 * Total wall‑clock time measured from start of Phase 0 to end of Phase 3; if > 21,600 s → **exit code 1** (SC‑004).
* **Sampling** guarantees that t‑SNE/UMAP fit comfortably within the runtime budget.

## 5. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use Fixed‑Effects ANOVA** | Mixed‑effects invalid with N≤3 datasets; ANOVA provides a descriptive within‑dataset comparison. |
| **Sample large datasets** | Guarantees CPU feasibility; [deferred]‑cell sample retains biological signal while keeping runtime < 6 h. |
| **Skip GSE111322/GSE150728** | No verified source; cannot fabricate URLs (Constitution II). |
| **Compute Diagnostics on Sampled High‑D Space (relative to embeddings)** | Satisfies FR‑002/FR‑003 while keeping construct validity with embeddings. |
| **Sweep Leiden Resolution** | Removes circularity of Silhouette‑threshold sweep and decouples optimization from evaluation. |
| **Exit Code 1 on Limits** | Meets SC‑003 and SC‑004 hard‑stop requirements. |
| **Case‑Study Framing** | Only one dataset available (if any); results are dataset‑specific and not generalizable. |
| **Abort on Missing Data** | If required raw counts are not found, the pipeline aborts with exit code 1 to prevent invalid analysis. |