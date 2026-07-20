# Data Model: Single-Cell Trajectories of T-Cell Exhaustion

## Overview

This document defines the data structures used throughout the pipeline, from raw download to final report. All data is stored in standard, reproducible formats (`.h5ad`, `.csv`, `.json`) to ensure the "Single Source of Truth" principle.

## Entities

### 1. Raw Dataset
- **Description**: Unprocessed count matrix downloaded from GEO.
- **Format**: `.mtx` (Matrix Market) + `.tsv` (genes/cells) or `.h5` (if available).
- **Storage**: `data/raw/{GSE_ID}/`
- **Fields**:
    - `counts`: Sparse matrix (genes x cells).
    - `metadata`: Cell barcodes, gene symbols.

### 2. Preprocessed Dataset (Annotated)
- **Description**: QC-filtered and normalized data.
- **Format**: `.h5ad` (AnnData).
- **Storage**: `data/processed/{GSE_ID}_preprocessed.h5ad`
- **Fields**:
    - `X`: Normalized counts (sparse).
    - `obs`: Cell metadata (mito_pct, n_counts, n_genes, condition).
    - `var`: Gene metadata (highly_variable, mito_gene).

### 3. Velocity Object
- **Description**: Data with RNA velocity and pseudotime.
- **Format**: `.h5ad` (AnnData).
- **Storage**: `data/processed/{GSE_ID}_velocity.h5ad`
- **Fields**:
    - `uns`: Velocity graph, parameters.
    - `obsm`: `X_umap`, `X_pca`, `pseudotime`.
    - `obsp`: `connectivities`.
    - `layers`: `spliced`, `unspliced`, `velocity`.

### 4. Fork-Point Results
- **Description**: Identified branch points and associated genes.
- **Format**: `.csv`
- **Storage**: `data/results/fork_points_{GSE_ID}.csv`
- **Fields**:
    - `branch_id`: Unique identifier for the branch.
    - `divergence_score`: Statistical divergence metric (derived from permutation test of therapy response labels).
    - `p_value`: From permutation test.
    - `genes`: List of top genes (JSON string or separate table).

### 5. Validation Metrics
- **Description**: Cross-dataset consistency and clinical enrichment.
- **Format**: `.json`
- **Storage**: `data/results/validation_metrics.json`
- **Fields**:
    - `spearman_correlation`: Float (top 3 genes).
    - `jaccard_index`: Float (top 50 genes).
    - `enrichment_p_value`: Float (therapy response).
    - `bootstrap_iterations`: Integer (1000).
    - `datasets_used`: List of dataset IDs used in validation.

## Data Flow

1.  **Download**: `Raw Dataset` -> `data/raw/`
2.  **Preprocess**: `Raw Dataset` -> `Preprocessed Dataset`
3.  **Velocity**: `Preprocessed Dataset` -> `Velocity Object`
4.  **Detect**: `Velocity Object` -> `Fork-Point Results`
5.  **Validate**: `Fork-Point Results` (all datasets) -> `Validation Metrics`
6.  **Report**: `Validation Metrics` + `Fork-Point Results` -> Final Report (PDF/HTML)

## Constraints

- **Immutability**: Raw data in `data/raw/` is never modified.
- **Checksums**: Every file in `data/raw/` and `data/processed/` is checksummed (SHA256) and recorded in `state/`.
- **Privacy**: No PII. Clinical labels (responder/non-responder) are treated as anonymous categorical variables.