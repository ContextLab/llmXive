# Data Model: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Overview
Canonical entities, attributes, constraints, and file representations. All artifacts are checksummed, version-controlled, and validated against the JSON-Schema contracts in `contracts/`.

## 2. Entities

### 2.1 Subject
| Field | Type | Constraints |
|-------|------|-------------|
| `subject_id` | string | Unique |
| `group` | `"musician"` / `"non_musician"` | `"musician"` ⇔ `years_of_training ≥ 1` |
| `years_of_training` | number ≥ 0 | 0 for non-musicians |
| `age` | number | Years |
| `sex` | `"M"` / `"F"` | — |
| `motion_score` | number | Head-motion metric (e.g., FD) |
| `ses_score` | number | SES proxy |
| `rs_fmri_path` | string | Must exist on disk |

### 2.2 ConnectivityMatrix
| Field | Type | Constraints |
|-------|------|-------------|
| `subject_id` | string | FK → Subject |
| `atlas` | string | e.g., `"Schaefer200"`; fixed across dataset |
| `n_rois` | integer ≥ 1 | Matches matrix dims |
| `z_matrix` | 2-D number array | Symmetric, diagonal = 0, Fisher-z |
| `networks` | object | Network name → ROI indices; names ⊆ {auditory, motor, executive} |

### 2.3 NetworkMetric
Aggregated connectivity strength per network, derived from a ConnectivityMatrix by `code/analysis/network_metrics.py`.
| Field | Type | Constraints |
|-------|------|-------------|
| `subject_id` | string | FK → Subject |
| `atlas` | string | Same atlas as the source ConnectivityMatrix |
| `network` | string | One of {auditory, motor, executive} |
| `mean_connectivity` | number | Mean Fisher-z within-network connectivity across all intra-network edges |
| `n_edges` | integer ≥ 1 | Number of intra-network edges averaged |
| `roi_indices` | integer[] | ROI indices defining the network |

### 2.4 StatisticalResult
| Field | Type | Notes |
|-------|------|-------|
| `connection_id` | string | `"ROI1_ROI2"` |
| `network` | string | Network label |
| `test_statistic` | number | t-value (or r for correlations) |
| `p_value` | number ∈ [0,1] | Uncorrected |
| `q_value` | number ∈ [0,1] | FDR-corrected |
| `effect_size` | number | Cohen's d (group) or r-derived (correlation) |
| `confidence_interval` | [number, number] | 95% CI |
| `is_significant` | boolean | `q_value < 0.05` |
| `threshold_sensitivity` | object | `{"0.01": bool, "0.05": bool, "0.10": bool}` |

### 2.5 NetworkComponent (NBS)
| Field | Type | Notes |
|-------|------|-------|
| `component_id` | integer | Sequential |
| `size` | integer | Edge count |
| `p_value_fwer` | number ∈ [0,1] | FWER-corrected |
| `edges` | string[] | `connection_id` list |

## 3. File Formats
| Artifact | Format | Location |
|----------|--------|----------|
| Raw data (real mode only) | CSV + NIfTI | `data/raw/` |
| Subject table | Parquet | `data/processed/subjects.parquet` |
| Connectivity | Per-subject JSON | `data/processed/connectivity/<subject_id>.json` |
| Network metrics | Per-subject JSON | `data/processed/network_metrics/<subject_id>.json` |
| Statistical results | CSV | `data/results/statistical_results.csv` |
| NBS components | JSON | `data/results/nbs_components.json` |
| Sensitivity | CSV | `data/results/sensitivity_analysis.csv` |
| **SSoT summary (FR-010)** | CSV | `data/results/results_summary.csv` |
| Checksums & logs | TXT | `data/logs/` |

## 4. Data Flow
1. `run_synthetic_generator.py` → subjects table + mock NIfTI with seeded quality defects (or `real_ingest.py` → raw copy + manifest).
2. `preprocess.py` → filtered, matched, residualized subject table + exclusion log.
3. `connectivity.py` → per-subject connectivity JSON.
4. `network_metrics.py` → per-subject network-level mean connectivity (NetworkMetric).
5. `stats.py` / `correlation.py` → statistical results + NBS components.
6. `sensitivity.py` → sensitivity table.
7. Summary builder → `results_summary.csv` (sole downstream reference).

Every step writes output hashes; no file is modified in place.