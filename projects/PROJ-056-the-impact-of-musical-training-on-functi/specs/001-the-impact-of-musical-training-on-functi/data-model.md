# Data Model: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Overview
This document defines the canonical entities, their attributes, constraints, and on‑disk representations used throughout the project. Every artifact is checksummed, version‑controlled, and validated against the JSON‑Schema contracts located in `contracts/`.

## 2. Entities

### 2.1 Subject
| Field | Type | Constraints |
|-------|------|-------------|
| `subject_id` | string | Unique identifier |
| `group` | `"musician"` / `"non_musician"` | `"musician"` ⇔ `years_of_training ≥ 1` |
| `years_of_training` | number ≥ 0 | 0 for non‑musicians |
| `age` | number | Years |
| `sex` | `"M"` / `"F"` | — |
| `motion_score` | number | Head‑motion metric (e.g., FD) |
| `ses_score` | number | Socio‑economic status proxy |
| `rs_fmri_path` | string | Filesystem path to the subject’s NIfTI file (must exist) |

### 2.2 ConnectivityMatrix
| Field | Type | Constraints |
|-------|------|-------------|
| `subject_id` | string | FK → Subject |
| `atlas` | string | Fixed across the dataset (e.g., `"Schaefer200"`). |
| `n_rois` | integer ≥ 1 | Must match matrix dimensions. |
| `z_matrix` | 2‑D number array | Fisher‑z transformed Pearson correlations; symmetric; diagonal = 0. |
| `networks` | object | Mapping of network name → list of ROI indices (must include `auditory`, `motor`, `executive`). |

### 2.3 NetworkMetric
Aggregated intra‑network connectivity per subject.
| Field | Type | Constraints |
|-------|------|-------------|
| `subject_id` | string | FK → Subject |
| `atlas` | string | Same atlas as the source ConnectivityMatrix |
| `network` | string | One of `{auditory, motor, executive}` |
| `mean_connectivity` | number | Mean Fisher‑z across all intra‑network edges |
| `n_edges` | integer ≥ 1 | Number of intra‑network edges used in the mean |
| `roi_indices` | integer[] | ROI indices defining the network |

### 2.4 StatisticalResult
Result of a hypothesis test for a single connection (or correlation).
| Field | Type | Notes |
|-------|------|-------|
| `connection_id` | string | `"ROI1_ROI2"` |
| `network` | string | Network label (`auditory`, `motor`, `executive`). |
| `test_statistic` | number | t‑value (group test) or r (correlation). |
| `p_value` | number ∈ [0, 1] | Uncorrected. |
| `q_value` | number ∈ [0, 1] | BH‑FDR corrected. |
| `effect_size` | number | Cohen’s d (group) or r‑derived d (correlation). |
| `confidence_interval` | [number, number] | 95 % CI. |
| `is_significant` | boolean | `q_value < 0.05`. |
| `threshold_sensitivity` | object | Keys are threshold strings (`"0.01"`, `"0.05"`, `"0.10"`); values are booleans indicating significance at that threshold. |

### 2.5 NetworkComponent (NBS)
Connected component identified by the NBS procedure.
| Field | Type | Notes |
|-------|------|-------|
| `component_id` | integer | Sequential identifier. |
| `size` | integer | Number of edges in the component. |
| `p_value_fwer` | number ∈ [0, 1] | Family‑wise error corrected p-value. |
| `edges` | array of strings | List of `connection_id`s belonging to this component. |

## 3. File Formats & Locations
| Artifact | Format | Location |
|----------|--------|----------|
| Raw data (real mode) | CSV + NIfTI | `data/raw/` |
| Subject table | Parquet | `data/processed/subjects.parquet` |
| Connectivity matrices | Per‑subject JSON | `data/processed/connectivity/<subject_id>.json` |
| Network metrics | Per‑subject JSON | `data/processed/network_metrics/<subject_id>.json` |
| Statistical results | CSV | `data/results/statistical_results.csv` |
| NBS components | JSON | `data/results/nbs_components.json` |
| Sensitivity analysis | CSV | `data/results/sensitivity_analysis.csv` |
| **Single Source of Truth** (FR‑010) | CSV | `data/results/results_summary.csv` |
| Checksums & logs | TXT | `data/logs/` |

## 4. Data Flow
1. **Synthetic generation / Real ingestion** → `subjects.parquet` + raw NIfTI files.  
2. **Preprocessing** → filtered, matched subject table; logs of exclusions.  
3. **Connectivity computation** → per‑subject JSON (`z_matrix`).  
4. **Network‑level aggregation** → `network_metrics/<subject_id>.json`.  
5. **Statistical testing** (`stats.py`, `correlation.py`) → `statistical_results.csv` + `nbs_components.json`.  
6. **Sensitivity sweep** → `sensitivity_analysis.csv`.  
7. **Summary aggregation** → `results_summary.csv`.  

All steps write new files; no in‑place modifications occur, satisfying the Data Hygiene principle.
