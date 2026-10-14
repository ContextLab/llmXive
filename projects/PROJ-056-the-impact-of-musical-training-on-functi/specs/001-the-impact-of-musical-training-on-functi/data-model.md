# Data Model: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Overview
Defines the canonical entities, their attributes, constraints, and file representations used throughout the pipeline. All artifacts are version‑controlled, checksummed, and validated against JSON‑Schema contracts.

## 2. Entities

### 2.1 Subject
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `subject_id` | string | Unique identifier | Must be unique |
| `group` | string (`"musician"` / `"non_musician"`) | Group assignment based on training duration | `group == "musician"` ⇔ `years_of_training ≥ 1` |
| `years_of_training` | number ≥ 0 | Training duration (0 for non‑musicians) | `years_of_training ≥ 1` implies `group == "musician"` |
| `age` | number | Age in years | – |
| `sex` | string (`"M"` / `"F"`) | Sex | – |
| `motion_score` | number | Head‑motion metric (e.g., FD) | – |
| `ses_score` | number | Socio‑economic status proxy | – |
| `rs_fmri_path` | string | Path to the subject’s resting‑state NIfTI file | Must exist on disk |

### 2.2 ConnectivityMatrix
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `subject_id` | string | FK → Subject | Must exist in Subject table |
| `atlas` | string | Parcellation name (e.g., `"Schaefer200"`) | Fixed across dataset |
| `n_rois` | integer ≥ 1 | Number of regions of interest | Matches matrix dimensions |
| `z_matrix` | 2‑D array of numbers | Fisher‑z transformed correlation matrix | Symmetric, diagonal = 0 |
| `networks` | object (dict) | Mapping network name → list of ROI indices | Network names limited to `"auditory"`, `"motor"`, `"executive"` |

### 2.3 StatisticalResult
| Field | Type | Description |
|-------|------|-------------|
| `connection_id` | string | `"ROI1_ROI2"` |
| `network` | string | Network label |
| `test_statistic` | number | t‑value |
| `p_value` | number ∈ [0,1] | Uncorrected |
| `q_value` | number ∈ [0,1] | BY‑corrected |
| `effect_size` | number | Cohen’s d |
| `confidence_interval` | array[2] of numbers | 95 % CI `[lower, upper]` |
| `is_significant` | boolean | `q_value < 0.05` |
| `threshold_sensitivity` | object | `{ "0.01": bool, "0.05": bool, "0.10": bool }` |

### 2.4 NetworkComponent (NBS Output)
| Field | Type | Description |
|-------|------|-------------|
| `component_id` | integer | Sequential ID |
| `size` | integer | Number of edges in the component |
| `p_value_fwer` | number ∈ [0,1] | Family‑wise error corrected |
| `edges` | array of strings | List of `connection_id` strings belonging to the component |

## 3. File Formats

| Artifact | Format | Location |
|----------|--------|----------|
| Raw behavioral & imaging data | CSV + NIfTI | `data/raw/` |
| Processed subject table | Parquet | `data/processed/subjects.parquet` |
| Connectivity matrices | Per‑subject JSON (one file per subject) | `data/processed/connectivity/<subject_id>.json` |
| Statistical results | CSV | `data/results/statistical_results.csv` |
| NBS components | JSON | `data/results/nbs_components.json` |
| Sensitivity analysis | CSV | `data/results/sensitivity_analysis.csv` |
| Checksums & logs | TXT | `data/logs/` |
| Master results (SSoT) | JSON | `data/results/master_results.json` |

## 4. Data Flow
1. `synthetic_generator.py` → `subjects.parquet`, mock NIfTI files.  
2. `preprocess.py` → filtered, matched `subjects.parquet`.  
3. `connectivity.py` → per‑subject JSON files under `data/processed/connectivity/`.  
4. `stats.py` / `correlation.py` → `statistical_results.csv`, `nbs_components.json`.  
5. `sensitivity.py` → `sensitivity_analysis.csv`.  
6. `master_results.json` aggregates key outputs for reporting.

All steps log output hashes for constitution‑compliant versioning. The `NetworkComponent` entity is validated against `contracts/network_component.schema.yaml`.

---


