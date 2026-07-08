# Data Model: 001-gene-regulation

## Overview

This document defines the data structures used throughout the pipeline. All data flows from `raw` (immutable) to `processed` (derived) to `results` (final).

## Core Entities

### 1. StressDataset (Raw & Processed)

Represents a single GEO accession.

**Fields**:
- `accession_id` (str): e.g., `"GSE51148"`.
- `source_url` (str): The FTP URL used to fetch the data.
- `raw_counts` (pd.DataFrame): Rows = Genes, Columns = Samples. Raw integer counts.
- `metadata` (pd.DataFrame): Rows = Samples. Columns=`['sample_id','stress_type','control','species','duration','severity']`.
- `processed_counts` (pd.DataFrame): TPM‑normalized, CPM‑filtered matrix.
- `checksum` (str): SHA‑256 hash of the raw archive.
- `included` (bool): `true` if organism is plant **and** at least two stress types are present.

**Lifecycle**:
1. **Raw** – download from NCBI GEO.  
2. **Verified** – organism & stress‑type check (FR‑012). **GSE40677 excluded here**.
3. **Filtered** – genes with <1 CPM in <3 samples removed (FR‑002).  
4. **Normalized** – TPM conversion (FR‑002).  
5. **Harmonized** – gene IDs mapped via Biopython; **only genes present in the [deferred] intersection of all included datasets are retained** (Constitution Principle VII).

### 2. FeatureSpace

The unified feature set across all **included** datasets.

**Fields**:
- `gene_ids` (List[str]): Intersection of genes present in **all** included datasets.  
- `top_k_genes` (List[str]): Subset of `gene_ids` with highest variance (default top 1500).  
- `variance_scores` (Dict[str, float]): Variance of each gene across all samples.

**Constraints**:
- If `len(top_k_genes) < 1500`, the pipeline aborts with a “Feature Space Insufficient” error (Edge Case).  

### 3. ClassificationModel

Stores the trained Random Forest and its metadata.

**Fields**:
- `model_id` (str): Hash of hyperparameters + seed.  
- `hyperparameters` (Dict): `n_estimators`, `max_depth`, `random_state`.  
- `feature_importances` (Dict[str, float]): Importance for each gene in `top_k_genes`.  
- `stability_scores` (Dict[str, float]): Frequency (0‑1) a gene appears in the top‑k across bootstrap replicates (Stability Selection).  
- `metrics` (Dict):
  - `within_dataset`: `{'accuracy': float, 'f1_macro': float}`.  
  - `cross_dataset`: `{'accuracy': float, 'f1_macro': float, 'generalization_gap': float}`.  
  - `null_distribution`: `{'mean': float, 'std': float, 'p_value': float}` (permutation test).  
  - `posthoc_power`: `float` (estimated power to detect observed lift).  
 - `mdes`: `float` (minimum detectable effect size at [deferred] power).
- `confusion_matrix` (np.ndarray): Shape `(n_classes, n_classes)`.  
- `classes_used` (List[str]): Stress types actually present after label‑space intersection.

### 4. Embedding

Reduced‑dimensional representation for visualization.

**Fields**:
- `samples` (List[str]): Sample identifiers.  
- `coordinates` (np.ndarray): Shape `(n_samples, 2)` (UMAP/t‑SNE).  
- `labels` (Dict[str, str]): Mapping of sample ID to `stress_type` and `dataset_source`.  
- `silhouette_score` (float): Cluster quality metric.

## Data Flow Diagram

```mermaid
graph TD
    A[NCBI GEO FTP] -->|wget| B(Raw Counts + Metadata)
    B -->|Checksum| C{Raw/processed}
    C --> D[Content Verify: Plant + ≥2 Stress Types]
    D -->|Exclude GSE40677| E[Log Exclusion]
    D -->|Include| F[Filter: >1 CPM]
    F --> G[Normalize: TPM]
    G --> H[Harmonize: 100% Gene Intersection]
    H --> I[Select: Top 1500 Variable Genes]
    I --> J[LODO Split]
    J --> K[Pre-ComBat Confounding Check]
    K -->|Pass| L[Train RF + ComBat (within CV)]
    K -->|Fail| M[Halting Error]
    J --> N[Embed: UMAP (within CV)]
    L --> O[Metrics: Acc, F1, Stability, Power/MDES]
    N --> P[Metrics: Silhouette]
    O --> Q[Results JSON]
    P --> Q
```

## Storage Schema

- `data/raw/{accession_id}.tar.gz` – immutable raw download.  
- `data/processed/{accession_id}_tpm.csv` – TPM‑normalized matrix (post‑filter).  
- `data/processed/feature_space.csv` – gene list + variance.  
- `data/processed/batch_corrected_matrix.csv` – **not stored globally**; generated on‑the‑fly within each CV fold to avoid leakage.  
- `results/model_metrics.json` – all performance, power, MDES, stability information.  
- `results/embedding_coords.csv` – UMAP coordinates for the held‑out test set of each fold.

All files are checksummed and referenced in `state/projects/PROJ-042-predicting-plant-stress-response-from-pu.yaml`.