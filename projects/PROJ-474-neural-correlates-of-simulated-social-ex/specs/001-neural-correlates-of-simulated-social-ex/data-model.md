# Data Model: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## Overview
The model defines immutable entities that trace every derived result back to raw inputs, satisfying the “Single Source of Truth” principle.

## Entities

### Subject
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | Unique identifier. |
| `motion_mean` | number | Mean framewise displacement (mm). |
| `qc_status` | string (`"passed"`/`"failed"`) | Result of motion QC (threshold 0.2 mm). |
| `conditions` | array[string] | Available conditions (`"Inclusion"`, `"Exclusion"`). |

### TimeSeries
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK to Subject. |
| `roi` | string | One of `PCC`, `mPFC`, `L_ANG`, `R_ANG`. |
| `condition` | string | `"Inclusion"` or `"Exclusion"`. |
| `data` | array[number] | BOLD signal values. |
| `tr` | number | Repetition time (seconds). |

### ConnectivityMatrix
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK to Subject. |
| `condition` | string | `"Inclusion"` / `"Exclusion"`. |
| `nodes` | array[string] | Ordered ROI names. |
| `matrix` | array[array[number]] | 4 × 4 Pearson correlation matrix (including self‑correlations). |
| `strength_signed` | number | Mean **signed** correlation across the three unique edges. |
| `strength_absolute` | number | Mean absolute correlation (descriptive only). |
| `edges` | object | Mapping `"{ROI1}-{ROI2}" → correlation`. |

### Result
| Field | Type | Description |
|-------|------|-------------|
| `test_type` | string | `"paired_permutation"`. |
| `metric` | string | `"connectivity_strength_signed"`. |
| `p_value` | number | Two‑tailed permutation p‑value. |
| `effect_size` | number | Cohen’s d. |
| `confidence_interval` | array[number] (len 2) | 95 % CI for the mean difference. |
| `framing` | string (`"associational"`/`"causal"`) | Interpretation framing. |
| `edge_p_values` | object | Raw p‑values per edge. |
| `edge_p_values_fdr` | object | FDR‑corrected p‑values per edge. |
| `sensitivity_curve` | array[object] | `{threshold, p_value}` for each motion‑threshold run. |
| `n_subjects` | integer | Number of subjects included. |
| `motion_threshold` | number | Motion exclusion threshold (mm). |

## Data Flow
1. **Raw**: `data/raw/` (downloaded NIfTI, JSON side‑cars).  
2. **Processed**: `data/processed/` – Parquet files for `TimeSeries` and `ConnectivityMatrix`.  
3. **Results**: `results/` – JSON/CSV for `Result` plus PNG figures.

## Schema Definitions
The concrete JSON‑Schema files reside in `contracts/` and are referenced by the implementation for validation.

---
