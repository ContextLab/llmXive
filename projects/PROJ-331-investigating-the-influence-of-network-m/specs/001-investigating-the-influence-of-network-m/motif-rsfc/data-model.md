# Data Model: Investigating the Influence of Network Motifs on Resting-State Functional Connectivity

**Project**: PROJ-331-investigating-the-influence-of-network-m
**Feature**: Motif-RSFC Analysis
**Version**: 1.0.0
**Last Updated**: 2023-10-27

## 1. Overview

This document defines the data entities, relationships, schemas, and file formats used throughout the Motif-RSFC analysis pipeline. It serves as the single source of truth for data structures, ensuring consistency between the download, preprocessing, motif analysis, and statistical reporting stages.

The pipeline operates on three primary data domains:
1. **Structural Connectome (SC)**: Derived from Diffusion Weighted Imaging (DWI) using Schaefer parcellation.
2. **Functional Connectivity (FC)**: Derived from Resting-State fMRI (rs-fMRI).
3. **Motif Profiles**: Statistical summaries of 3-node subgraph prevalence.

## 2. Directory Structure & Path Conventions

All paths are relative to the project root.

```
data/
├── raw/ # Raw downloaded data (HCP S3) and checksums
│ ├──.checksums.json # SHA256 hashes for integrity verification
│ └── <subject_id>/ # Subject-specific raw files (.nii.gz,.trk)
├── processed/ # Derived, intermediate, and final analysis artifacts
│ ├── subject_list_manifest.json
│ ├── structural_connectome_metadata.json
│ ├── canonical_binary_adj.npy
│ ├── weighted_adjacency.npy (per subject)
│ ├── rsfc.npy (per subject)
│ ├── global_efficiency.json
│ ├── motif_profiles.json
│ ├── sensitivity_z*.json
│ ├── subject_metrics.csv
│ ├── quality_flags.json
│ └── success_rate.json
└── logs/
 └── pipeline.log

results/
├── correlation_results.json
├── permutation_results.json
├── power_analysis.json
└── results.pdf

specs/feature/motif-rsfc/
├── data-model.md # This file
└── contracts/ # YAML schemas for validation
 ├── dataset.schema.yaml
 ├── motif_profile.schema.yaml
 ├── results.schema.yaml
 ├── analysis_results.schema.yaml
 └── structural_connectome.schema.yaml
```

## 3. Data Entities & Schemas

### 3.1. Subject Manifest
**File**: `data/processed/subject_list_manifest.json`
**Source**: `code/download.py` -> `load_subject_list`
**Description**: The canonical list of subjects attempted in the current run.

```json
{
 "total_subjects": 100,
 "subject_ids": ["100307", "100903", "101004"],
 "subjects_attempted": 100,
 "created_at": "2023-10-27T10:00:00Z"
}
```

### 3.2. Structural Connectome Metadata
**File**: `data/processed/structural_connectome_metadata.json`
**Source**: `code/preprocess.py` -> `binarize_by_median_density`
**Description**: Tracks the processing status of each subject's structural data.

```json
{
 "subjects": {
 "100307": {
 "status": "complete",
 "weighted_path": "data/processed/100307_weighted_adjacency.npy",
 "binary_path": "data/processed/100307_canonical_binary_adj.npy",
 "density": 0.15,
 "processed_at": "2023-10-27T10:05:00Z"
 },
 "100903": {
 "status": "skipped",
 "reason": "Missing DWI data"
 }
 },
 "cohort_threshold": 0.12
}
```

### 3.3. Global Efficiency Metrics
**File**: `data/processed/global_efficiency.json`
**Source**: `code/preprocess.py` -> `compute_global_efficiency`
**Description**: Global efficiency calculated on the binary structural connectome.

```json
{
 "100307": {
 "global_efficiency": 0.452,
 "n_nodes": 400
 },
 "100903": {... }
}
```

### 3.4. Motif Profiles
**File**: `data/processed/motif_profiles.json`
**Source**: `code/motifs.py` -> `aggregate_motif_profiles`
**Description**: Aggregated z-scores for all 13 directed 3-node motifs per subject.

```json
{
 "100307": {
 "M1": { "z_score": 1.23, "count": 500 },
 "M2": { "z_score": -0.45, "count": 420 },
...
 "M13": { "z_score": 2.10, "count": 110 }
 },
 "100903": {... }
}
```

**Note on Motif IDs**:
- **M1-M13**: Standard naming for directed 3-node isomorphism classes (Milo et al., 2002).
- **M1**: 3-cycle (fully connected directed loop).
- **M2**: 2-cycle with one outgoing edge.
- (Full mapping defined in `code/motifs.py`).

### 3.5. Subject Metrics (Aggregated)
**File**: `data/processed/subject_metrics.csv`
**Source**: `code/stats.py` -> `main`
**Description**: Flat file joining all metrics for statistical analysis.

| Column | Type | Description |
|:--- |:--- |:--- |
| subject_id | str | Unique identifier |
| motif_id | str | Motif class (M1-M13) |
| z_score | float | Z-scored prevalence |
| rsfc_strength | float | Mean absolute upper-triangle of rsFC matrix |
| global_efficiency | float | Global efficiency of binary SC |
| node_degree | float | Mean row sum of binary adjacency |
| network_density | float | node_degree / (N-1) |

### 3.6. Correlation Results
**File**: `results/correlation_results.json`
**Source**: `code/stats.py` -> `main`
**Description**: Final statistical outputs including Bonferroni-corrected p-values.

```json
{
 "M1": {
 "pearson": { "r": 0.35, "p_raw": 0.002, "p_bonferroni": 0.026 },
 "spearman": { "r": 0.32, "p_raw": 0.004, "p_bonferroni": 0.052 },
 "significant": true
 },
...
}
```

### 3.7. Permutation Results
**File**: `results/permutation_results.json`
**Source**: `code/stats.py` -> `run_permutation_test`
**Description**: Empirical p-values for significant motifs.

```json
[
 {
 "motif_id": "M1",
 "original_r": 0.35,
 "empirical_p": 0.015,
 "n_permutations": 1000
 }
]
```

### 3.8. Quality Flags
**File**: `data/processed/quality_flags.json`
**Source**: `code/stats.py` -> `check_vif_and_select_method`
**Description**: Flags for VIF, zero-variance motifs, and method selection.

```json
{
 "zero_variance": true,
 "vif_value": 1.2,
 "method_selected": "partial_correlation",
 "zero_variance_motifs": ["M5", "M9"]
}
```

### 3.9. Power Analysis
**File**: `results/power_analysis.json`
**Source**: `code/stats.py` -> `main`
**Description**: Parameters for power calculation.

```json
{
 "min_detectable_r": 0.25,
 "power_level": 0.80,
 "adjusted_alpha": 0.0038,
 "n_subjects": 50,
 "statsmodels_version": "0.14.0",
 "seed": 42
}
```

## 4. Relationships & Data Flow

1. **Subject List** (`subject_list_manifest.json`) drives the pipeline.
2. **Download** creates raw files and checksums.
3. **Preprocessing** (T014, T014_agg, T014_bin) generates:
 - `weighted_adjacency.npy` (per subject)
 - `canonical_binary_adj.npy` (per subject)
 - `global_efficiency.json`
 - `structural_connectome_metadata.json`
4. **Motif Analysis** (T025a, T025b, T025c_agg) consumes binary matrices to produce:
 - `motif_profiles.json`
 - `sensitivity_z*.json`
5. **Statistics** (T039, T030a-c) joins:
 - `motif_profiles.json`
 - `global_efficiency.json`
 - `rsfc.npy` (computed in T015a)
 - `structural_connectome_metadata.json`
 - `subject_list_manifest.json`
 -> Outputs `subject_metrics.csv`, `correlation_results.json`, `permutation_results.json`.
6. **Reporting** (T035b) consumes all result JSONs to generate `results.pdf`.

## 5. File Format Specifications

### 5.1. NumPy Arrays (.npy)
- **Weighted Adjacency**: `float32` or `float64`, shape `(N, N)`, symmetric.
- **Binary Adjacency**: `bool` or `int8`, shape `(N, N)`, symmetric.
- **RSFC Matrix**: `float32` or `float64`, shape `(N, N)`, symmetric, values in `[-1, 1]`.

### 5.2. JSON
- UTF-8 encoded.
- Keys are strings.
- No circular references.

### 5.3. CSV
- Comma-separated.
- UTF-8 encoded.
- Header row required.

### 5.4. Log Files
- `pipeline.log`: Text file, ISO 8601 timestamps, levels (INFO, WARNING, ERROR).
- Must contain: Bonferroni alpha, seed, library versions, permutation count, VIF threshold.

## 6. Constraints & Validations

- **N_NODES**: Default 400 (Schaefer 400 parcellation).
- **MOTIF_SIZE**: Default 3 (directed).
- **ZERO_VARIANCE**: If a motif has zero variance across subjects, it is flagged and excluded from correlation tests (replaced with "insufficient variance" note).
- **VIF_THRESHOLD**: 5.0. If VIF > 5, fallback to permutation-only analysis (but still compute partial r).
- **BONFERRONI_ALPHA**: `0.05 / 13` (approx 0.0038) for 13 motifs.
- **PERMUTATIONS**: Minimum 1000.
- **DATA_RETENTION**: Raw data in `data/raw/` must never be deleted (Constitution Principle VI).

## 7. Change Log

- **v1.0.0**: Initial specification based on T009 requirements. Includes all entities defined in tasks.md and spec.md.