# Data Model: Predicting Plant Stress Response from Publicly Available Transcriptomic Data

## Overview
The pipeline moves data through three logical layers: **raw GEO archives**, **processed harmonized matrices**, and **result artefacts**. All artefacts are immutable once written; any transformation creates a new file and records its SHA‑256 hash.

## Core Entities

### 1. StressDataset (raw & processed)
| Field | Type | Description |
|-------|------|-------------|
| `accession_id` | `string` | GEO series identifier (e.g., `"GSE51148"`). |
| `source_url` | `string` | FTP URL used for download. |
| `raw_counts` | `DataFrame` | Genes × Samples integer count matrix. |
| `metadata` | `DataFrame` | Columns: `sample_id`, `stress_type`, `species`, `duration`, `severity`. |
| `processed_counts` | `DataFrame` | TPM‑normalized, CPM‑filtered matrix (post‑FR‑003). |
| `checksum` | `string` | SHA‑256 of the downloaded archive. |
| `included` | `boolean` | `true` if organism is plant **and** ≥ 2 stress types present (FR‑001, FR‑018). |

Lifecycle: download → verify organism/stress → filter CPM → TMM normalize → gene‑ID harmonization → intersect.

### 2. FeatureSpace
| Field | Type | Description |
|-------|------|-------------|
| `gene_ids` | `list[string]` | Intersection of gene IDs across **all included** datasets (≥ 1,500 required). |
| `top_k_genes` | `list[string]` | Subset of `gene_ids` with highest variance; K ∈ {50, 100, 150}. |
| `variance_scores` | `dict[string → float]` | Variance of each gene across the full sample pool. |

### 3. ClassificationModel
| Field | Type | Description |
|-------|------|-------------|
| `model_id` | `string` | Hash of hyper‑parameters + seed. |
| `hyperparameters` | `dict` | `C` (inverse regularization), `solver='liblinear'`, `random_state`. |
| `feature_importances` | `dict[string → float]` | Absolute logistic‑regression coefficients for each gene in `top_k_genes`. |
| `stability_scores` | `dict[string → float]` | Frequency (0‑1) a gene appears among top‑K coefficients across 100 bootstraps. |
| `metrics` | `dict` | See **Metrics** section below. |
| `confusion_matrix` | `array[int]` | N × N matrix (N = number of stress classes used). |
| `classes_used` | `list[string]` | Stress types present after label‑space intersection. |

#### Metrics Sub‑structure
- `within_dataset`: `accuracy`, `macro_f1`, `precision`, `recall`.  
- `cross_dataset`: `accuracy`, `macro_f1`, `generalization_gap` (= within − cross).  
- `null_distribution`: `mean`, `std`, `p_value` (permutation test).  
- `posthoc_power`: estimated power for detecting observed lift.  
- `mdes`: Minimum Detectable Effect Size at α = 0.05.  

### 4. Embedding
| Field | Type | Description |
|-------|------|-------------|
| `samples` | `list[string]` | Sample identifiers (held‑out test set). |
| `coordinates` | `array[float]` (shape = n × 2) | UMAP 2‑D embedding. |
| `labels` | `dict[string → dict]` | Mapping sample → `{stress_type, dataset_id}`. |
| `silhouette_score_stress` | `float` | Silhouette for stress labels. |
| `silhouette_score_dataset` | `float` | Silhouette for dataset IDs. |
| `delta_silhouette` | `float` | `stress_score − dataset_score`. |

## Data Flow Diagram
```mermaid
graph TD
    A[Entrez GEO Query] --> B[Download (GEOparse)]
    B --> C[Checksum & Verify (FR‑001, FR‑018)]
    C --> D[CPM Filter & TMM Normalize (FR‑003)]
    D --> E[Gene ID Mapping (mygene/biomart) (FR‑004)]
    E --> F[Intersection → FeatureSpace (≥1500 genes) (FR‑004)]
    F --> G[Select Top‑K Variable Genes (FR‑005)]
    G --> H[LODO CV Loop]
    H --> I[Train Logistic Regression (FR‑006)]
    I --> J[Metrics & Permutation Tests (FR‑007, FR‑008, FR‑012)]
    H --> K[Bootstrap Stability (FR‑010)]
    H --> L[UMAP + Silhouette (FR‑011)]
    J --> M[Power & MDES (FR‑009)]
    M & K & L --> N[Assemble Results (JSON, CSV, PNG)]
    N --> O[Update State File (FR‑014)]
    O --> P[Generate Report (US‑5, FR‑015)]
```

## Storage Schema
| Path | Content | Notes |
|------|---------|-------|
| `data/raw/{accession_id}.soft.gz` | Original GEO SOFT archive (immutable). | SHA‑256 recorded in state file. |
| `data/processed/{accession_id}_tpm.csv` | TPM‑normalized, CPM‑filtered matrix. | Gene IDs already mapped to Ensembl. |
| `data/processed/feature_space.csv` | Columns: `gene_id`, `variance`. | Includes intersection list. |
| `results/model_metrics.json` | Full `ClassificationModel` JSON (see contract). |
| `results/robust_biomarkers.csv` | Genes meeting variance ≤ 0.30 & freq ≥ 0.70. |
| `results/embedding_coords.csv` | UMAP coordinates + labels. |
| `results/umap_plot.png` | Visual embedding. |
| `invalid_samples.csv` | Samples excluded due to missing/contradictory stress metadata. |
| `state/projects/PROJ-042-predicting-plant-stress-response-from-pu.yaml` | Project state (hashes, timestamps, `research_complete`). |

All files are checksum‑verified and referenced in the state file (Constitution Principle III & V).
