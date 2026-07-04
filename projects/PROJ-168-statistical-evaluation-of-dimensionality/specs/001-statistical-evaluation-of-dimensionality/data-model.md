# Data Model: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

## Overview

This document defines the data structures, schemas, and transformations used throughout the project. All data flows through the `Snakemake` workflow, ensuring that every artifact has a clear lineage from raw input to final result.

## Data Flow Diagram

```mermaid
graph TD
    A[Raw GEO Data] -->|download.py| B(Raw Count Matrix)
    B -->|preprocess.py| C{QC Check}
    C -->|Pass| D[Filtered Matrix]
    C -->|Fail| E[Skip Dataset]
    D -->|preprocess.py| F[HVG Matrix (2000 genes)]
    F -->|geometry.py| G[PC Matrix (30 PCs)]
    G -->|geometry.py| H[Linearity Metric (Variance Ratio)]
    G -->|geometry.py| I[Density Metric (Local PCA Error)]
    F -->|embeddings.py| J[PCA Embedding]
    F -->|embeddings.py| K[t-SNE Embedding]
    F -->|embeddings.py| L[UMAP Embedding]
    J -->|clustering.py| M[Leiden Clusters (PCA)]
    K -->|clustering.py| N[Leiden Clusters (t-SNE)]
    L -->|clustering.py| O[Leiden Clusters (UMAP)]
    M -->|clustering.py| P[ARI/NMI (PCA)]
    N -->|clustering.py| Q[ARI/NMI (t-SNE)]
    O -->|clustering.py| R[ARI/NMI (UMAP)]
    M & N & O -->|clustering.py| S[Silhouette Scores (Cell-Level)]
    H & I & P & Q & R & S & Method & Dataset -->|stats.py| T[Statistical Model Output]
```

## Data Entities

### 1. Raw Count Matrix
- **Source**: GEO accession (e.g., GSE131907).
- **Format**: CSV or Matrix Market (MTX).
- **Schema**:
  - Rows: Cells (unique IDs).
  - Columns: Genes (Ensembl IDs or Symbols).
  - Values: Integer counts (UMI).

### 2. Filtered Matrix
- **Transformation**: Filter genes expressed in < 5% of cells.
- **Schema**: Same as Raw, but reduced columns.

### 3. HVG Matrix
- **Transformation**: Select a subset of highly variable genes.
- **Schema**: Same as Filtered, but exactly 2000 columns.

### 4. PC Matrix
- **Transformation**: PCA on HVG Matrix (a reduced set of principal components).
- **Schema**:
  - Rows: Cells.
  - Columns: PC1 to PC30.
  - Values: Float64.

### 5. Embedding Matrix
- **Transformation**: PCA/t-SNE/UMAP on PC Matrix or HVG Matrix.
- **Schema**:
  - Rows: Cells.
  - Columns: X, Y (2D) or X, Y, Z (3D).
  - Values: Float64.

### 6. Metric Record
- **Schema**:
  - `dataset_id`: String (e.g., "GSE131907").
  - `method`: String ("PCA", "t-SNE", "UMAP").
  - `global_linearity`: Float (Variance Explained Ratio).
  - `local_density`: Float (Local PCA Reconstruction Error).
  - `ari`: Float.
  - `nmi`: Float.
  - `silhouette_score`: Float (Cell-level mean).
  - `runtime_seconds`: Float.
  - `peak_ram_gb`: Float.

### 7. Model Output
- **Schema**:
  - `term`: String (e.g., "method[UMAP]:global_linearity").
  - `coef`: Float.
  - `p_value`: Float.
  - `std_err`: Float.
  - `conf_int_low`: Float.
  - `conf_int_high`: Float.
  - `is_descriptive`: Boolean (True if no model was fitted due to insufficient data).

## File Naming Convention

- `data/raw/{accession}_raw.{ext}`
- `data/processed/{accession}_filtered.{ext}`
- `data/processed/{accession}_hvg.{ext}`
- `data/processed/{accession}_{method}_embedding.{ext}`
- `data/results/{accession}_metrics.csv`
- `data/results/model_summary.csv`

## Error Handling

- **Missing Data**: If a dataset cannot be downloaded, log to `logs/download_errors.log` and skip.
- **Insufficient Genes**: If < 2000 genes remain after filtering, log to `logs/qc_warnings.log` and skip.
- **Model Convergence**: If the linear model fails to converge, log to `logs/stats_errors.log` and revert to Descriptive Mode.