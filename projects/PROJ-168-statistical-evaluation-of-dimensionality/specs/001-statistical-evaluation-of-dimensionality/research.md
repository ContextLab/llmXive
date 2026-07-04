# Research: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

## Overview

This research phase investigates the relationship between the geometric properties of scRNA-seq data manifolds (global linearity, local density) and the fidelity of cell-type recovery achieved by different dimensionality reduction techniques (PCA, t-SNE, UMAP). The study aims to validate the hypothesis that linear methods fail on high-curvature manifolds, while non-linear methods may underperform on highly linear, noisy data.

## Dataset Strategy

The study utilizes scRNA-seq datasets with **verified direct download URLs** for raw count matrices. Per the project constitution, datasets without verified URLs are excluded to ensure reproducibility.

| Dataset | Accession | Verified Source URL | Status | Notes |
|:--- |:--- |:--- |:--- |:--- |
| Lung Adenocarcinoma | GSE131907 | ` | **Verified** | Direct Series Matrix link. Contains counts and labels. |
| Unknown 2 | GSE150728 | **NO verified source found** | **Excluded** | No direct raw count URL found. Excluded per 'Verified Accuracy' principle. |
| Unknown 3 | GSE176078 | **NO verified source found** | **Excluded** | No direct raw count URL found. Excluded per 'Verified Accuracy' principle. |

**Dataset Variable Fit Assessment**:
- **Required Variables**: Raw gene counts, Cell-type labels (ground truth).
- **GSE131907**: The Series Matrix URL provides raw counts and metadata. **Action**: Parse matrix for counts and metadata for labels.
- **Fallback Strategy**:
 1. Attempt to download raw counts via the verified Series Matrix URL.
 2. If download fails or data is missing, log error and skip.
 3. **Critical**: If fewer than 2 verified datasets remain after processing, the pipeline **MUST** switch to **Descriptive Mode** (no LMM, no p-values) to avoid statistical invalidity.

*Note: The `# Verified datasets` block contains URLs for "GEO (csv)" that appear to be unrelated to the specific GSE accessions. These are NOT used.*

## Geometric Metrics & Embedding Strategy

### Global Linearity (Revised)
- **Definition**: **Variance Explained Ratio** (Sum of variance explained by top 10 PCs / Total variance of all PCs).
- **Rationale**: Measures the proportion of data structure captured by a linear subspace. A ratio near 1.0 indicates high linearity; a lower ratio indicates significant non-linear structure (curvature) not captured by linear PCA. This is a valid, standard proxy for manifold linearity.
- **Method**: Perform PCA on the HVG matrix, calculate the ratio of the sum of the first 10 eigenvalues to the sum of all eigenvalues.

### Local Density (Revised)
- **Definition**: **Local PCA Reconstruction Error** (Average error of reconstructing k=30 neighbors using local PCA).
- **Rationale**: Measures how well a local linear model fits the data. High error indicates high local non-linearity or density heterogeneity. Avoids the "curse of dimensionality" in raw k-NN distance.
- **Method**: For each cell, fit a local PCA on its k=30 neighbors, calculate the reconstruction error, and average across all cells.

### Embedding Methods
1. **PCA**: Linear. 30 components.
2. **t-SNE**: Non-linear. Perplexity=30, **n_iter=1000** (fixed to satisfy FR-005), metric=euclidean.
3. **UMAP**: Non-linear. n_neighbors=15, min_dist=0.1, n_components=2.

**Compute Feasibility**:
- All methods will be run on a **deterministically sampled** subset of cells (max [deferred]) if the dataset exceeds this limit.
- `scikit-learn` (PCA, t-SNE) and `umap-learn` (UMAP) will be used with default CPU settings. No GPU acceleration.
- **t-SNE Warning**: t-SNE is computationally expensive. `n_iter=1000` is the minimum for convergence; if runtime > 1 hour, the pipeline logs a warning but continues (as per spec).

## Statistical Modeling Strategy

### Model Specification (Revised: Descriptive Focus)
Given the **n=3 dataset** limitation (only 1 verified dataset currently), the primary analysis is **Descriptive Stratified Analysis**.
- **Primary Output**: Plots of Fidelity (ARI/NMI) vs. Global Linearity and Local Density, stratified by Method.
- **Secondary Output (Conditional)**: If >=2 verified datasets are found, fit a **Linear Mixed-Effects Model (LMM)** on **cell-level silhouette scores** (not dataset-level ARI/NMI).
 - **Formula**: `silhouette_score ~ method + global_linearity + local_density + method:global_linearity + method:local_density + (1 | dataset)`
 - **Rationale**: Silhouette score is a valid cell-level metric of clustering quality, allowing for N >> 3 observations.
- **Interaction**: `method:global_linearity` and `method:local_density` are the primary hypotheses.

### Statistical Rigor & Limitations
- **Power Analysis**: With n=3 datasets, **dataset-level** inference is impossible. The study relies on **cell-level** inference (N >> 3) using Silhouette Scores as the outcome **only if** >=2 datasets are available.
- **Multiple Comparisons**: Bonferroni correction (α = 0.025) for ARI vs NMI (if both tested) or Silhouette vs others.
- **Collinearity**: VIF calculated for linearity and density. If VIF > 5, simplify model.
- **Causal Inference**: Observational. Claims framed as associational.
- **Measurement Validity**: Metrics validated against synthetic manifolds.

### Fallback: Descriptive Mode
If < 2 verified datasets are found:
1. Calculate metrics for available datasets.
2. Generate plots (Linearity vs Fidelity by Method).
3. **Do NOT** fit a statistical model.
4. Report: "Insufficient verified datasets for inferential statistics. Descriptive analysis only."

## Compute Feasibility Plan

- **Hardware**: GitHub Actions `ubuntu-latest` (2 CPU, 7GB RAM).
- **Memory Management**:
 - Data loaded in chunks if > 5GB.
 - **Deterministic Sampling**: Max [deferred] cells. `random_state` derived from dataset accession hash.
 - `scikit-learn` uses `n_jobs=1`.
- **Runtime**:
 - Target: < 6 hours total.
 - Monitoring: `/usr/bin/time -v` used to log peak RAM.
 - Fallback: If a step exceeds a predefined duration threshold, log warning.

## Decision/Rationale

- **Why Cell-Level?** To overcome n=3 dataset limitation (if applicable).
- **Why Silhouette Score?** A valid cell-level proxy for clustering fidelity, unlike ARI/NMI.
- **Why Descriptive Fallback?** To prevent invalid statistical claims when data is insufficient.
- **Why CPU-only?** To ensure reproducibility on free-tier CI.
- **Why Variance Explained Ratio?** A standard, valid measure of global linearity, replacing the flawed Pearson correlation metric.
- **Why Local PCA Error?** A robust measure of local density/non-linearity, replacing the flawed k-NN distance metric.