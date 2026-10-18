# Data Model: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Overview
The data model defines the schema for the verified HCP parquet dataset (inputs) and the analysis outputs. It is deliberately **flexible** to accommodate the possible absence of a music‑related behavioral column.

## Entity Definitions

### 1. Subject
| Field | Type | Description | Constraints |
|---|---|---|---|
| `subject_id` | `str` | Unique identifier from HCP | required, unique |
| `age` | `int` | Age in years | `0 < age < 120` |
| `sex` | `str` | `"M"` or `"F"` | enum |
| `fd_mean` | `float` | Mean Framewise Displacement (mm) | `>= 0` |
| `behavioral_proxy` | `float` | *Optional* music‑related score (e.g., `music_emotion_score`). May be absent. | `>= 0` if present |
| `motion_excluded` | `bool` | `True` if `fd_mean > 0.5` | derived |

### 2. ConnectivityMatrix
| Field | Type | Description | Constraints |
|---|---|---|---|
| `subject_id` | `str` | FK to `Subject` | required |
| `matrix` | `list[list[float]]` | 200 × 200 Pearson correlation matrix (symmetric) | diagonal = 1.0, values ∈ [‑1, 1] |
| `atlas` | `str` | Atlas name | `"Schaefer200"` |

### 3. NetworkMetrics
| Field | Type | Description | Constraints |
|---|---|---|---|
| `subject_id` | `str` | FK to `Subject` | required |
| `global_efficiency` | `float` | Network integration | `> 0` |
| `modularity` | `float` | Network segregation | `0 < value < 1` |
| `participation_coeff` | `float` | Cross‑module connectivity | `0 ≤ value ≤ 1` |
| `dmn_efficiency` | `float` | Within‑DMN efficiency | `> 0` |
| `salience_efficiency` | `float` | Within‑Salience efficiency | `> 0` |
| `visual_efficiency` | `float` | Within‑Visual efficiency | `> 0` |
| `vif_global_efficiency` | `float` | VIF for global efficiency (optional) | `> 0` |

### 4. AnalysisResult (output)
| Field | Type | Description | Constraints |
|---|---|---|---|
| `metric_name` | `str` | Name of the predictor (e.g., `"global_efficiency"`). | required |
| `correlation_r` | `float` | Pearson *r* with the behavioral proxy. | `[-1, 1]` |
| `p_value` | `float` | Raw two‑tailed p‑value. | `[0, 1]` |
| `p_value_fdr` | `float` | FDR‑adjusted p‑value. | `[0, 1]` |
| `significant` | `bool` | `True` if `p_value_fdr < 0.05`. | derived |
| `sample_size` | `int` | Number of subjects included in this test. | `> 0` |
| `power_achieved` | `float` | Achieved statistical power for detecting an effect size of r = 0.20 at α = 0.05 (computed per metric). | `[0, 1]` |

## Data Flow
1. **Download** → `src/data/download.py` → raw parquet files (`data/`).  
2. **Validate** → `src/data/validate.py` → `data_gap_report.md` (if BMRQ missing and no proxy) and identification of any `behavioral_proxy`.  
3. **Reconstruct Matrix** → `src/analysis/graph_metrics.py` → `ConnectivityMatrix`.  
4. **Compute Metrics** → `src/analysis/graph_metrics.py` → `NetworkMetrics`.  
5. **Merge** (`Subject` + `NetworkMetrics` + optional `behavioral_proxy`).  
6. **Statistical Modeling** → `src/analysis/stats.py` → `AnalysisResult` (`results/analysis_results.csv`).  

## Constraints & Validation Rules
- **Symmetry**: Every `ConnectivityMatrix.matrix` must be symmetric (`matrix[i][j] == matrix[j][i]`).  
- **Diagonal**: All diagonal entries must equal `1.0`.  
- **Range**: All correlation values must be within `[‑1, 1]`.  
- **Missing Data**: Rows lacking any required field (`subject_id`, `age`, `sex`, `fd_mean`) are excluded before metric calculation.  
- **Motion Exclusion**: Subjects with `fd_mean > 0.5` are flagged `motion_excluded=True` and omitted from the final regression dataset.  
- **Collinearity**: VIF > 5 triggers automatic removal of the offending predictor(s) before regression; the action is logged in `results/vif_report.json`.  
- **Construct‑Validity Disclaimer**: The `behavioral_proxy` is used **exploratorily**; it is **not** validated as a measure of musical reward sensitivity and should not be interpreted as equivalent to the BMRQ.

---



