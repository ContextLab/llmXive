# Data Model: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Entities

### Subject
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | Unique identifier (e.g., `S001`). |
| `age` | integer | Age in years (optional). |
| `gender` | string | `"M"` or `"F"` (optional). |
| `has_waking` | boolean | `True` if a waking segment was successfully preprocessed. |
| `has_sleep` | boolean | `True` if sleep epochs were successfully preprocessed. |

### WakingNetwork
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK → Subject. |
| `band` | string | `"theta"` or `"alpha"`. |
| `connectivity_matrix` | numpy.ndarray | Symmetric matrix of coherence values (0 < value < 1). |
| `centrality_degree` | dict[string, float] | Node → degree value. |
| `centrality_betweenness` | dict[string, float] | Node → betweenness value. |
| `centrality_eigenvector` | dict[string, float] | Node → eigenvector value. |
| `global_coherence_mean` | float | Mean of all off‑diagonal coherence values. |

### SleepStageEpoch
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK → Subject. |
| `stage_label` | string | `"Wake"`, `"N1"`, `"N2"`, `"N3"`, or `"REM"`. |
| `epoch_index` | integer | Sequential index of the 30 s epoch. |
| `pli_score` | float | Phase‑Lag Index for this epoch (0 ≤ score ≤ 1). |

### SubjectMetrics (aggregated per subject & stage)
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK → Subject. |
| `stage_label` | string | `"N1"`, `"N2"`, `"N3"`, or `"REM"`. |
| `mean_pli` | float | Mean PLI across all epochs of this stage. |
| `n_epochs` | integer | Number of epochs contributing to `mean_pli`. |
| `centrality_degree_mean` | float | Mean degree centrality across all nodes (waking). |
| `centrality_betweenness_mean` | float | Mean betweenness centrality across all nodes. |
| `centrality_eigenvector_mean` | float | Mean eigenvector centrality across all nodes. |
| `waking_night_id` | string | Identifier (date or hash) of the waking recording night. |
| `sleep_night_id` | string | Identifier of the sleep recording night. |
| `temporal_proximity` | boolean | `True` if `waking_night_id == sleep_night_id`. |
| `age` | integer | Age of the subject (optional, for covariate control). |
| `gender` | string | `"M"` or `"F"` (optional, for covariate control). |
| `total_sleep_time_min` | float | Total sleep time in minutes (derived from stage durations). |

### AnalysisResult
| Field | Type | Description |
|-------|------|-------------|
| `metric_name` | string | `"degree"`, `"betweenness"`, or `"eigenvector"`. |
| `stage_label` | string | `"N1"`, `"N2"`, `"N3"`, or `"REM"`. |
| `band` | string | `"theta"` or `"alpha"` (connectivity band used). |
| `correlation_coefficient` | float | Pearson, Spearman, or partial correlation coefficient. |
| `p_value_raw` | float | Unadjusted *p*‑value (0 ≤ p ≤ 1). |
| `p_value_corrected` | float | Bonferroni‑adjusted *p*‑value (0 ≤ p ≤ 1). |
| `significant` | boolean | `True` if corrected *p* < 0.05. |
| `method` | string | `"pearson"`, `"spearman"`, or `"partial"`. |
| `global_vif_flag` | boolean | `True` if the global VIF across subjects for the three centrality metrics exceeds 5.0. |
| `temporal_proximity_flag` | boolean | Mirrors `temporal_proximity` from `SubjectMetrics`. |

## Data Flow
1. **Raw** – EDF files (`data/raw/`).  
2. **Processed** – Cleaned epochs, connectivity matrices, PLI arrays (`data/processed/`).  
3. **Metrics** – `SubjectMetrics.csv` (`data/metrics/`).  
4. **Results** – `analysis_results.json` (`data/results/`).  

---

