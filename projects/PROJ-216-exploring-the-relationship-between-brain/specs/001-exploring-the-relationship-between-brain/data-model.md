# Data Model: Exploring the Relationship Between Brain Network Dynamics and Fluid Intelligence

## Overview
This document defines the data structures, schemas, and relationships for the neuroimaging analysis pipeline. The model adheres to BIDS standards for raw data and defines custom schemas for derived graph metrics, behavioral scores, and pipeline statistics.

## Key Entities

### 1. Subject
Represents an individual participant.
- **Attributes**:
  - `subject_id`: Unique identifier (e.g., `sub-001`).
  - `age`: Integer (years).
  - `gender`: String (e.g., `M`, `F`, `Other`).
  - `dataset_source`: String (e.g., `ds000224`).
  - `preprocessed_path`: Path to the cleaned NIfTI file.
  - `exclusion_reason`: String (e.g., `excessive_motion`, `missing_fluid_intelligence`).

### 2. GraphMetric
Represents a computed network property for a subject.
- **Attributes**:
  - `subject_id`: Foreign key to Subject.
  - `metric_name`: String (e.g., `global_efficiency`, `modularity`, `clustering_coeff`).
  - `value`: Float.
  - `confidence_interval_lower`: Float (95% CI).
  - `confidence_interval_upper`: Float (95% CI).
  - `atlas`: String (e.g., `Schaefer200`).

### 3. BehavioralScore
Represents a **Fluid Intelligence** assessment (Pivot from Musical Creativity).
- **Attributes**:
  - `subject_id`: Foreign key to Subject.
  - `score_value`: Float.
  - `source_type`: String (e.g., `Fluid_Intelligence`, `NIH_Toolbox`).
  - `sub_scale_names`: List of Strings (e.g., `crystallized`, `fluid`).
  - `missing`: Boolean (if score was not found).

### 4. PreprocessingStats
Artifact for SC-001 (Success Rate).
- **Attributes**:
  - `total_subjects`: Integer.
  - `successful_subjects`: Integer.
  - `excluded_motion`: Integer.
  - `excluded_missing_data`: Integer.
  - `success_rate_percentage`: Float.

### 5. ResourceProfile
Artifact for SC-005 (Resource Usage).
- **Attributes**:
  - `peak_ram_gb`: Float.
  - `total_runtime_hours`: Float.
  - `subjects_processed`: Integer.

## Data Flow

1.  **Raw Input**: OpenNeuro BIDS dataset (`data/raw/`).
2.  **Preprocessed**: Cleaned NIfTI files (`data/interim/`).
3.  **Derived Metrics**: CSV/Parquet files containing GraphMetrics (`data/processed/metrics.csv`).
4.  **Behavioral Data**: CSV/Parquet containing BehavioralScores (`data/processed/behavioral.csv`).
5.  **Statistics**: `preprocessing_stats.json`, `resource_profile.json`.
6.  **Final Output**: Merged dataset for statistical analysis (`data/processed/analysis_dataset.csv`).

## Schema Definitions

### Preprocessed Data Schema
| Field | Type | Description |
| :--- | :--- | :--- |
| `subject_id` | String | Unique subject ID |
| `nifti_path` | String | Path to preprocessed NIfTI |
| `motion_flag` | Boolean | True if motion > 3mm |
| `time_series_length` | Integer | Number of time points after trimming |

### Graph Metrics Schema
| Field | Type | Description |
| :--- | :--- | :--- |
| `subject_id` | String | Unique subject ID |
| `metric_name` | String | Name of the graph metric |
| `value` | Float | Computed value |
| `atlas_version` | String | Atlas used (e.g., Schaefer200) |

### Behavioral Scores Schema
| Field | Type | Description |
| :--- | :--- | :--- |
| `subject_id` | String | Unique subject ID |
| `score_value` | Float | Fluid Intelligence score |
| `source_type` | String | Type of test (Fluid_Intelligence) |
| `sub_scales` | String | JSON string of sub-scales |

### Preprocessing Stats Schema
| Field | Type | Description |
| :--- | :--- | :--- |
| `total_subjects` | Integer | Total subjects found |
| `successful_subjects` | Integer | Successfully preprocessed |
| `success_rate_percentage` | Float | Percentage of success |

### Resource Profile Schema
| Field | Type | Description |
| :--- | :--- | :--- |
| `peak_ram_gb` | Float | Peak RAM usage |
| `total_runtime_hours` | Float | Total runtime |
| `subjects_processed` | Integer | Number of subjects processed |

## Data Hygiene Rules
- **Immutability**: Raw data (`data/raw/`) is never modified.
- **Provenance**: Every derived file includes a `derivation` field linking to the source file hash.
- **Checksums**: MD5 checksums recorded in `data/manifest.yaml`.
- **PII**: No names or IDs other than `sub-XXX` allowed in committed data.