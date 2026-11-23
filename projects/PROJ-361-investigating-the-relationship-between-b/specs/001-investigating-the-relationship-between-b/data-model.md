# Data Model: Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions

## 1. Overview

This document defines the data structures, schemas, and relationships used in the project. It ensures that all data artifacts are consistent, reproducible, and traceable to the source data.

## 2. Core Entities

### 2.1 Subject
Represents a unique participant in the study. This entity contains the core demographic and analysis results.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `subject_id` | String | Unique identifier (e.g., `sub-001`) | OpenNeuro |
| `age` | Integer | Age in years | OpenNeuro |
| `sex` | String | Biological sex (M/F) | OpenNeuro |
| `motion_fd` | Float | Mean Framewise Displacement | Preprocessing |
| `included` | Boolean | Whether subject passed exclusion criteria | Preprocessing |

### 2.2 ConnectivityMatrix
Represents the functional connectivity between brain regions.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `subject_id` | String | Link to Subject | Preprocessing |
| `matrix` | Array[Float] | Flattened correlation matrix (upper triangle) | Connectivity |
| `atlas` | String | Atlas used (e.g., "Schaefer-400") | Preprocessing |

### 2.3 TopologyMetrics
Quantitative metrics derived from the connectivity matrix. **Small-worldness is excluded due to redundancy.**

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `subject_id` | String | Link to Subject | Topology |
| `modularity` | Float | Community structure strength | Graph Theory |
| `path_length` | Float | Average shortest path length | Graph Theory |
| `clustering` | Float | Clustering coefficient | Graph Theory |
| `efficiency` | Float | Global efficiency | Graph Theory |

### 2.4 IllusionScore
Behavioral measures of visual illusion susceptibility. **Note: This data is expected to be missing in ds004285.**

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `subject_id` | String | Link to Subject | OpenNeuro |
| `muller_lyer_error` | Float | Error magnitude in Müller-Lyer task | OpenNeuro |
| `ponzo_error` | Float | Error magnitude in Ponzo task | OpenNeuro |

### 2.5 ExclusionList
Record of subjects excluded from analysis. This list is materialized as `data/processed/excluded_subjects.csv`.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `subject_id` | String | Excluded subject ID | Preprocessing |
| `reason` | String | Reason for exclusion (e.g., "FD > 0.5mm") | Preprocessing |
| `timestamp` | DateTime | When exclusion was recorded | System |

### 2.6 MetadataRegistry
SQLite registry for tracking data integrity and versioning (supports Constitution Principle V). This registry is strictly for **file integrity** and does **not** store core demographic data (which is in `Subject`).

**Schema File**: `code/db/schema.sql`

| Table | Columns | Description | Foreign Keys |
| :--- | :--- | :--- | :--- |
| `subjects` | `subject_id` (PK, String), `checksum` (String) | Tracks subject-level data files (e.g., raw BOLD). | None |
| `files` | `file_id` (PK, Integer), `subject_id` (FK), `path` (String), `checksum` (String), `created_at` (DateTime) | Tracks all data files. `subject_id` references `subjects.subject_id`. | `files.subject_id` -> `subjects.subject_id` |
| `artifacts` | `artifact_id` (PK, Integer), `file_id` (FK), `name` (String), `version` (String), `hash` (String) | Tracks derived artifacts. `file_id` references `files.file_id`. | `artifacts.file_id` -> `files.file_id` |

**Note on IllusionScore**: If behavioral scores exist, they are stored as a file in the `files` table (pointing to the TSV/JSON). If missing, the `merged_dataset.csv` will contain `null` values for `muller_lyer_error` and `ponzo_error`.

## 3. Data Flow

1. **Raw Data**: Downloaded from OpenNeuro (ds004285) -> `data/raw/`.
2. **Preprocessing**: fMRIPrep -> `data/interim/` (nifti files).
3. **Motion QC**: Calculate FD -> `data/processed/excluded_subjects.csv`.
4. **Connectivity**: Extract time series -> Compute correlation -> `data/processed/connectivity_matrices.npz`.
5. **Topology**: Compute metrics -> `data/processed/topology_metrics_raw.json`.
6. **Merging**: Join metrics with illusion scores (if available) -> `data/processed/merged_dataset.csv`.
7. **Analysis**: PCA + Correlation + FDR -> `data/processed/results.json`.

## 4. File Naming Conventions

- **Raw**: `data/raw/{subject_id}/`
- **Interim**: `data/interim/{subject_id}_bold.nii.gz`
- **Processed**: `data/processed/{artifact_name}_{version}.csv`
- **Metadata**: `data/metadata/{artifact_name}.json`

## 5. Versioning

- All data files are versioned with a content hash.
- The `state/projects/...yaml` file tracks the `artifact_hashes` map.
- Any change to raw data invalidates all downstream artifacts.