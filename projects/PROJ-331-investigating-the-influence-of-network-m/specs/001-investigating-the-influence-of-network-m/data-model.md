# Data Model: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Overview
This document defines the data structures, file formats, and schemas used throughout the pipeline. All data artifacts are stored in `data/` and validated against the contracts in `contracts/`.

## Directory Structure

```text
data/
├── raw/                   # Raw HCP data (temporary, deleted after processing)
│   ├── sub-XXXX/
│   │   ├── diffusion.nii.gz
│   │   └── rs-fMRI.nii.gz
├── processed/             # Derived, permanent artifacts
│   ├── canonical_binary_adj.npy     # Binary adjacency matrix (100x100)
│   ├── rsfc.npy           # Functional correlation matrix (100x100)
│   ├── global_efficiency.json # Global efficiency per subject
│   ├── motif_profiles.json    # Z-scores for all motifs per subject
│   ├── subject_metrics.csv    # Aggregated metrics for correlation
│   ├── structural_connectome_metadata.json # Status and provenance per subject
│   ├── quality_flags.json   # VIF and method selection flags
│   ├── power_analysis.json  # Power analysis results
│   ├── sensitivity_z1.5.json # Sensitivity analysis results
│   ├── sensitivity_z2.0.json
│   ├── sensitivity_z2.5.json
│   └── pipeline.log       # Execution log
└── logs/                  # Additional logs
```

## Artifact Definitions

### 1. Raw Input (Temporary)
*   **Source**: HCP S Release.
*   **Format**: NIfTI (`.nii.gz`) for diffusion and rs-fMRI.
*   **Lifecycle**: Downloaded, processed, then **deleted** to save disk space.

### 2. Derived Structural Connectome (`data/processed/canonical_binary_adj.npy`)
*   **Type**: NumPy array (uint8 for binary).
*   **Shape**: (100, 100).
*   **Content**: Binary adjacency matrix where $A_{ij} = 1$ if a structural connection exists between node i and j, 0 otherwise.
*   **Parcellation**: Schaefer atlas.
*   **Binarization**: Thresholded at median graph density.
*   **Schema**: `contracts/dataset.schema.yaml` (subset).

### 3. Derived Functional Connectome (`data/processed/rsfc.npy`)
*   **Type**: NumPy array (float32).
*   **Shape**: (100, 100).
*   **Content**: Pearson correlation matrix of BOLD time-series. Values within the standard correlation range.
*   **Processing**: Global Signal Regression (GSR) applied.

### 4. Global Efficiency (`data/processed/global_efficiency.json`)
*   **Type**: JSON.
*   **Schema**: `contracts/results.schema.yaml`.
*   **Fields**:
    *   `subject_id`: string.
    *   `global_efficiency`: float.
    *   `global_degree`: float (for partial correlation control).

### 5. Motif Profiles (`data/processed/motif_profiles.json`)
*   **Type**: JSON.
*   **Schema**: `contracts/motif_profile.schema.yaml`.
*   **Fields**:
    *   `subject_id`: string.
    *   `motif_z_scores`: object (key=motif_type, value=z_score).
    *   `null_model_params`: object (iterations, method).

### 6. Subject Metrics (`data/processed/subject_metrics.csv`)
*   **Type**: CSV.
*   **Schema**: `contracts/results.schema.yaml`.
*   **Columns**:
    *   `subject_id`
    *   `motif_<type>_z` (e.g., `motif_triangle_z`)
    *   `rsfc_strength`
    *   `global_efficiency`
    *   `global_degree`
    *   `network_density`

### 7. Structural Connectome Metadata (`data/processed/structural_connectome_metadata.json`)
*   **Type**: JSON.
*   **Schema**: `contracts/structural_connectome.schema.yaml`.
*   **Fields**:
    *   `subject_id`: string.
    *   `status`: "complete", "skipped", "error".
    *   `reason`: string or null.
    *   `file_paths`: object.

### 8. Quality Flags (`data/processed/quality_flags.json`)
*   **Type**: JSON.
*   **Fields**:
    *   `vif_value`: float.
    *   `method_selected`: "partial_correlation" or "permutation_only".
    *   `zero_variance_flags`: list of motif types.

### 9. Power Analysis (`data/processed/power_analysis.json`)
*   **Type**: JSON.
*   **Fields**:
    *   `min_detectable_r`: float.
    *   `power`: float.
    *   `adjusted_alpha`: float.

### 10. Sensitivity Analysis (`data/processed/sensitivity_z*.json`)
*   **Type**: JSON.
*   **Fields**:
    *   `threshold`: float.
    *   `significant_motifs`: list.

### 11. Results (`results/permutation_results.json`)
*   **Type**: JSON.
*   **Schema**: `contracts/analysis_results.schema.yaml`.
*   **Fields**:
    *   `motif_type`: string.
    *   `metric_type`: string (strength/efficiency).
    *   `partial_r`: float.
    *   `p_value_bonferroni`: float.
    *   `p_value_permutation`: float.
    *   `significant`: boolean.

## Data Flow

1.  **Raw** (HCP) -> **Preprocess** -> **Derived** (`canonical_binary_adj.npy`, `rsfc.npy`).
2.  **Derived** -> **Motifs** -> **Motif Profiles** (`motif_profiles.json`).
3.  **Derived** -> **Stats** -> **Global Efficiency** (`global_efficiency.json`).
4.  **Motif Profiles** + **Global Efficiency** -> **Stats** -> **Subject Metrics** (`subject_metrics.csv`).
5.  **Subject Metrics** -> **Stats** -> **Permutation Results** (`permutation_results.json`).
6.  **Permutation Results** -> **Report** -> **PDF** (`results.pdf`).

## Data Hygiene & Provenance
*   **Checksums**: All *derived* files are checksummed. Raw files are deleted.
*   **Provenance**: Each derived file includes metadata (source file hash, processing date, script version).
*   **Immutability**: Raw files are never modified. Derived files are overwritten only if re-run.