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
| `roi` | string | One of `PCC`, `mPFC`, `ANG` (bilateral Angular Gyrus). |
| `condition` | string | `"Inclusion"` or `"Exclusion"`. |
| `data` | array[number] | BOLD signal values after any optional preprocessing. |
| `tr` | number | Repetition time (seconds). |

### ConnectivityMatrix
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK to Subject. |
| `condition` | string | `"Inclusion"` / `"Exclusion"`. |
| `nodes` | array[string] | Ordered ROI names (`["PCC","mPFC","ANG"]`). |
| `matrix` | array[array[number]] | 3 × 3 Pearson correlation matrix (including self‑correlations). |
| `strength_absolute` | number | **Primary metric** – mean absolute correlation across the three ROI‑pair edges. |
| `strength_signed` | number | Mean **signed** correlation (optional, for descriptive purposes). |
| `edges` | object | Mapping `"{ROI1}-{ROI2}" → correlation` for each of the three unique edges. |

### DynamicSeries
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK to Subject. |
| `condition` | string | `"Inclusion"` / `"Exclusion"`. |
| `window_center` | array[number] | Center time (seconds) of each sliding window. |
| `strength_series` | array[number] | Mean **absolute** connectivity strength for each window (descriptive). |
| `mean_strength` | number | Mean of `strength_series`. |
| `std_strength` | number | Standard deviation of `strength_series`. |

### Result
| Field | Type | Description |
|-------|------|-------------|
| `test_type` | string | `"paired_permutation"`. |
| `metric` | string | `"mean_absolute_correlation"` (primary DMN strength metric). |
| `p_value` | number | Two‑tailed permutation p‑value. |
| `effect_size` | number | Cohen’s d. |
| `confidence_interval` | array[number] (len 2) | 95 % CI for the mean difference. |
| `framing` | string (`"associational"`/`"causal"`) | Interpretation framing. |
| `n_subjects` | integer | Number of subjects included. |
| `motion_threshold` | number | Motion exclusion threshold (mm). |
| `sensitivity_curve` | array[object] | `{threshold, p_value}` for each motion‑threshold run. |

## Data Flow
1. **Raw**: `data/raw/` (downloaded NIfTI, JSON side‑cars).  
2. **Processed**: `data/processed/` – Parquet files for `TimeSeries`, `ConnectivityMatrix`, and `DynamicSeries`.  
3. **Results**: `results/` – JSON/CSV for `Result` plus PNG figures.

## Schema Definitions
Concrete JSON‑Schema files reside in `contracts/` and are referenced by the implementation for validation.

---

