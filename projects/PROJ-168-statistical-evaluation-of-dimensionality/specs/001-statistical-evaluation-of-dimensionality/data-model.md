# Data Model: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

## 1. Overview

This document defines the data structures used throughout the pipeline, from raw ingestion to final statistical reporting. All artifacts are stored in `data/` with checksums.

## 2. Entity Definitions

### 2.1 Dataset
Represents a single scRNA‑seq experiment.
* `dataset_id`: String (e.g., "GSE131907")
* `source_url`: String (Verified URL)
* `status`: Enum ["Available", "Unavailable", "Error"]
* `error_message`: String (if Unavailable/Error)
* `checksum`: String (SHA‑256 of raw file)
* `raw_file_path`: String (relative path in `data/raw/`)
* `processed_file_path`: String (relative path in `data/processed/`, nullable)
* `fallback_strategy`: Enum ["skip", "abort", "case_study"] (action when dataset cannot be obtained)

### 2.2 PreprocessedMatrix
Log‑CPM transformed, HVG‑selected matrix (potentially sampled).
* `dataset_id`: String
* `matrix_path`: String (Parquet)
* `n_cells`: Integer (after sampling)
* `n_genes`: Integer (post‑HVG)
* `hvg_count`: Integer
* `geometric_descriptors`: Object
  * `trustworthiness`: Float (computed on sampled high‑D space)
  * `local_continuity`: Float (computed on sampled high‑D space)

### 2.3 Embedding
Low‑dimensional representation of cells.
* `dataset_id`: String
* `method`: Enum ["PCA", "tSNE", "UMAP"]
* `embedding_path`: String (CSV/Parquet)
* `dimensions`: Integer (2 or 3)
* `hyperparameters`: Object (e.g., `{"perplexity": 30}`)
* `clustering_result`: Object
  * `labels`: List[Integer]
  * `silhouette_score`: Float (at optimal resolution)
  * `optimal_resolution`: Float

### 2.4 FidelityMetric
Performance metric for a specific embedding.
* `dataset_id`: String
* `method`: String
* `metric_type`: Enum ["ARI", "NMI"]
* `value`: Float (0.0–1.0)
* `ground_truth_labels`: List[Integer] (reference only)

### 2.5 StatisticalResult
Output of the Fixed‑Effects ANOVA and sensitivity analysis.
* `model_summary`: Object
  * `formula`: String ("fidelity ~ method")
  * `fixed_effects`: List[Object] (term, estimate, std_error, p_value, p_value_fdr)
  * `random_effects_variance`: Null (Fixed‑Effects ANOVA)
  * `vif_values`: Object (method → VIF)
  * `collinearity_passed`: Boolean
* `sensitivity_analysis`: Object
  * `thresholds`: List[Float] (Leiden resolutions)
  * `variance_ari`: Float
  * `variance_nmi`: Float
  * `stability_passed`: Boolean
* `execution_metadata`: Object
  * `peak_memory_bytes`: Integer
  * `total_runtime_seconds`: Number
  * `datasets_processed`: Integer
  * `datasets_skipped`: Integer
  * `exit_code`: Integer (0 = success, 1 = failure)

## 3. Data Flow Diagram

```mermaid
graph TD
    A[Raw GEO Data] -->|Download & Checksum| B(PreprocessedMatrix)
    B -->|Sampling (5k cells if >10k)| C[SampledMatrix]
    C -->|PCA/t‑SNE/UMAP| D[Embedding]
    D -->|Geometric Diagnostics| E[GeometricDescriptors]
    D -->|Leiden Clustering| F[ClusterLabels]
    F -->|ARI/NMI vs GT| G[FidelityMetrics]
    G -->|Fixed‑Effects ANOVA| H[StatisticalResult]
    G -->|Resolution Sweep| I[SensitivityAnalysis]
```

## 4. Storage Formats

* **Raw Data**: CSV/MTX (as provided).  
* **Processed Data**: Parquet (sparse‑friendly).  
* **Embeddings**: CSV (human‑readable) or Parquet.  
* **Metrics/Results**: JSON (pipeline‑friendly) and YAML (schema‑validated).  
* **Checksums**: JSON manifest at `data/manifest.json`.
