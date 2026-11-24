# Data Model: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

## Overview
All data artifacts reside under `data/` with strict versioning, checksums, and provenance metadata. The model defines participant‑level structures, intermediate results, and final outputs.

## Entity Schemas

### 1. Participant
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | Unique identifier (e.g., `sub-001`). |
| `dataset_source` | string | `"OpenNeuro"` (matched dMRI + EEG). |
| `quality_flag` | boolean | `true` if both modalities passed QC; otherwise `false`. |

### 2. StructuralConnectome
| Field | Type | Description |
|-------|------|-------------|
| `adjacency_matrix` | 2‑D array (float) | Weighted connectivity (N × N). |
| `node_degree` | 1‑D array (float) | Degree per node. |
| `clustering_coefficient` | 1‑D array (float) | Local clustering per node. |
| `rich_club_coefficient` | float | Global rich‑club coefficient. |
| `parcellation` | string | Parcellation name (e.g., `HCP-MMP1.0`). |

### 3. AvalancheRecord
| Field | Type | Description |
|-------|------|-------------|
| `size` | integer | Number of active channels in the avalanche. |
| `duration` | float | Duration in seconds (or number of time bins). |
| `time_bins` | list[int] | Indices of active time bins. |
| `participant_id` | string | Link to `Participant.subject_id`. |

### 4. CorrelationResult
| Field | Type | Description |
|-------|------|-------------|
| `metric_pair` | string | `"degree_vs_exponent_size"` etc. |
| `spearman_rho` | float | Spearman correlation coefficient. |
| `p_value` | float | Raw p‑value. |
| `corrected_p_value` | float | Permutation‑corrected family‑wise error p‑value. |
| `vif_score` | float | VIF for the predictor pair (if applicable). |
| `threshold_used` | float | Avalanche threshold percentile (0.75 or 0.80). |
| `collinearity_status` | string | `"low"` or `"high"` (VIF ≥ 5). |
| `sample_size` | integer | Number of participants included. |
| `ci_lower` | float | Lower bound of bootstrap 95 % CI for ρ. |
| `ci_upper` | float | Upper bound of bootstrap 95 % CI for ρ. |

## File Formats

| Directory | Content | Format |
|-----------|---------|--------|
| `data/raw/` | Original downloads (parquet, CSV). | Parquet / CSV (as provided). |
| `data/processed/` | Connectivity matrices, cleaned EEG epochs, avalanche event tables. | `.npy` for arrays, `.csv` for tables. |
| `data/results/` | Participant‑level metrics, correlation tables, collinearity JSON, final report. | `metrics.csv`, `correlations.csv`, `collinearity_status.json`, `report.md`. |
| `data/raw/.checksums.json` | SHA‑256 checksums for each raw file. | JSON. |

## Data Flow
1. **Download** → `data/raw/` (checksum recorded).  
2. **Preprocess dMRI** → `data/processed/` (structural graphs).  
3. **Preprocess EEG** → `data/processed/` (cleaned EEG).  
4. **Metric Computation** → `data/results/metrics.csv`.  
5. **Statistical Validation** → `data/results/correlations.csv` and `collinearity_status.json`.  
6. **Report Generation** → `data/results/report.md`.

All steps are deterministic given the pinned seeds and versioned dependencies.

---


