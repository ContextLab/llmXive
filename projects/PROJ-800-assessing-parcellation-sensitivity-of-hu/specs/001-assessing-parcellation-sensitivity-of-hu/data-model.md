# Data Model: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

## 1. Overview

This document defines the data structures, schemas, and file formats used in the project. All data is stored in `data/` with strict versioning and checksumming.

## 2. Data Flow

```mermaid
graph TD
    A[Raw fMRI NIfTI] -->|Streaming| B[Preprocessing (if needed)]
    B --> C[Parcellation: AAL-90]
    B --> D[Parcellation: Schaefer-200]
    B --> E[Parcellation: Schaefer-400]
    C --> F[Adjacency Matrix 90]
    D --> G[Adjacency Matrix 200]
    E --> H[Adjacency Matrix 400]
    F --> I[Centrality: Degree/Betweenness]
    G --> J[Centrality: Degree/Betweenness]
    H --> K[Centrality: Degree/Betweenness]
    I --> L[Hub Set: Top 10%]
    J --> M[Hub Set: Top 10%]
    K --> N[Hub Set: Top 10%]
    L --> O[Overlap Analysis]
    M --> O
    N --> O
    O --> P[Results: Stats, Plots]
```

## 3. File Specifications

### 3.1 Raw Data
-   **Format**: NIfTI (.nii.gz)
-   **Location**: `data/raw/`
-   **Naming**: `{subject_id}_task-rest_space-MNI_desc-preproc_bold.nii.gz`
-   **Checksum**: SHA-256 recorded in `state/...yaml`.

### 3.2 Processed Data
-   **Adjacency Matrices**:
    -   **Format**: NumPy (.npy)
    -   **Shape**: (N_nodes, N_nodes)
    -   **Location**: `data/processed/{subject_id}_{atlas}_adjacency.npy`
    -   **Schema**: See `contracts/adjacency_matrix.schema.yaml`.
-   **Centrality Scores**:
    -   **Format**: CSV (.csv)
    -   **Columns**: `node_id`, `degree_centrality`, `betweenness_centrality`, `is_hub` (bool)
    -   **Location**: `data/processed/{subject_id}_{atlas}_centrality.csv`
    -   **Schema**: See `contracts/hub_set.schema.yaml`.
-   **Spatial Mapping**:
    -   **Format**: NumPy (.npy)
    -   **Content**: Array mapping high-res indices to low-res indices (generated via Voxel-Wise Hub Mask Overlap logic).
    -   **Location**: `data/processed/mapping_schaefer_to_aal.npy`

### 3.3 Results
-   **Overlap Statistics**:
    -   **Format**: JSON (.json)
    -   **Location**: `data/results/overlap_stats.json`
    -   **Schema**: See `contracts/overlap_result.schema.yaml`.
-   **Validation Report**:
    -   **Format**: JSON (.json)
    -   **Location**: `data/results/validation_report.json`
    -   **Content**: Checksums, status, runtime metrics.
-   **Plots**:
    -   **Format**: PNG (.png)
    -   **Location**: `data/results/`

## 4. Data Integrity

-   **Checksumming**: Every file in `data/raw` and `data/processed` is checksummed upon creation.
-   **Immutability**: Raw files are never modified. Derived files are new.
-   **PII**: No PII in data; subject IDs are anonymized.