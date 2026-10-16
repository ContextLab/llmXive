# Data Model: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Entities

### Subject
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | Unique identifier (e.g., `S001`). |
| `age` | integer | Age in years (optional; may be absent in some datasets). |
| `gender` | string | `"M"` or `"F"` (optional; may be absent). |
| `has_waking` | boolean | `True` if a waking segment was successfully preprocessed with ≥ 2 min duration. |
| `has_sleep` | boolean | `True` if sleep epochs were successfully preprocessed. |

### WakingNetwork
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK → Subject. |
| `band` | string | `"theta"` or `"alpha"`. |
| `connectivity_matrix` | numpy.ndarray | Symmetric matrix of coherence values (0 < value < 1); shape (n_electrodes, n_electrodes). |
| `centrality_degree` | dict[string, float] | Electrode name → degree centrality value. |
| `centrality_betweenness` | dict[string, float] | Electrode name → betweenness centrality value. |
| `centrality_eigenvector` | dict[string, float] | Electrode name → eigenvector centrality value. |
| `centrality_degree_mean` | float | Mean degree centrality across all electrodes. |
| `centrality_betweenness_mean` | float | Mean betweenness centrality across all electrodes. |
| `centrality_eigenvector_mean` | float | Mean eigenvector centrality across all electrodes. |

### SleepStageEpoch
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK → Subject. |
| `stage_label` | string | `"Wake"`, `"N1"`, `"N2"`, `"N3"`, or `"REM"`. |
| `epoch_index` | integer | Sequential index of the 30 s epoch. |
| `epoch_duration_sec` | integer | Always 30 (per verified reference 1908.11463). |
| `pli_score` | float | Phase‑Lag Index for this epoch (0 ≤ score ≤ 1). |

### SubjectMetrics (aggregated per subject & stage)
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK → Subject. |
| `stage_label` | string | `"N1"`, `"N2"`, `"N3"`, or `"REM"`. |
| `mean_pli` | float | Mean PLI across all epochs of this stage (0 ≤ value ≤ 1). |
| `n_epochs` | integer | Number of epochs contributing to `mean_pli` (≥ 1). |
| `centrality_degree_mean` | float | Mean degree centrality across all nodes in the waking network. |
| `centrality_betweenness_mean` | float | Mean betweenness centrality across all nodes. |
| `centrality_eigenvector_mean` | float | Mean eigenvector centrality across all nodes. |
| `waking_night_id` | string | Identifier (date or hash) of the waking recording night (extracted from EDF header). |
| `sleep_night_id` | string | Identifier of the sleep recording night. |
| `temporal_proximity` | boolean | `True` if `waking_night_id == sleep_night_id`. |
| `age` | integer | Age of the subject (optional; may be null). |
| `gender` | string | `"M"` or `"F"` (optional; may be null). |
| `total_sleep_time_min` | float | Total sleep time in minutes (derived from durations of all sleep stages). |
| `waking_duration_min` | float | Duration of the waking segment in minutes (used for filtering: must be ≥ 2 min). |

### AnalysisResult
| Field | Type | Description |
|-------|------|-------------|
| `metric_name` | string | `"degree"`, `"betweenness"`, or `"eigenvector"`. |
| `stage_label` | string | `"N1"`, `"N2"`, `"N3"`, or `"REM"`. |
| `band` | string | `"theta"` or `"alpha"` (connectivity band used for centrality). |
| `correlation_coefficient` | float | Pearson, Spearman, or partial correlation coefficient (−1 ≤ value ≤ 1). |
| `p_value_raw` | float | Unadjusted *p*‑value (0 ≤ p ≤ 1). |
| `p_value_corrected` | float | Bonferroni‑adjusted *p*‑value (0 ≤ p ≤ 1). |
| `significant` | boolean | `True` if corrected *p* < 0.05. |
| `method` | string | `"pearson"`, `"spearman"`, or `"partial"`. |
| `global_vif_flag` | boolean | `True` if the global VIF across subjects for the three centrality metrics exceeds 5.0. |
| `temporal_proximity_flag` | boolean | Mirrors `temporal_proximity` from `SubjectMetrics`. |
| `n_subjects_used` | integer | Number of subjects included in this correlation (may be < 30 if some subjects lack data for this stage). |

### VIFReport
| Field | Type | Description |
|-------|------|-------------|
| `global_vif_degree` | float | Global VIF for degree centrality across all subjects. |
| `global_vif_betweenness` | float | Global VIF for betweenness centrality across all subjects. |
| `global_vif_eigenvector` | float | Global VIF for eigenvector centrality across all subjects. |
| `global_vif_max` | float | Maximum of the three VIF values. |
| `collinearity_flag` | boolean | `True` if any global VIF > 5.0. |
| `interpretation` | string | Brief note on collinearity (e.g., "High collinearity detected; interpret centrality metrics jointly, not as independent predictors."). |

## Data Flow

```
Raw Data
├── data/raw/*.edf (PhysioNet Sleep‑EDF)
│
Preprocessing
├── data/processed/epochs_{subj}.npz (cleaned EEG epochs)
├── data/processed/metadata_{subj}.json (covariates, night IDs, durations)
│
Connectivity & Centrality
├── data/processed/connectivity_theta_{subj}.npy (coherence matrix)
├── data/processed/connectivity_alpha_{subj}.npy (coherence matrix)
├── data/processed/centrality_{subj}.json (degree, betweenness, eigenvector means)
│
Sleep‑Stage Synchrony
├── data/processed/pli_N1_{subj}.npy (mean PLI for N1)
├── data/processed/pli_N2_{subj}.npy (mean PLI for N2)
├── data/processed/pli_N3_{subj}.npy (mean PLI for N3)
├── data/processed/pli_REM_{subj}.npy (mean PLI for REM)
│
Aggregation
├── data/metrics/SubjectMetrics.csv (one row per subject per stage)
│
Collinearity Diagnostics
├── data/results/vif_report.json (VIF values and flag)
│
Statistical Analysis
├── data/results/analysis_results.json (all correlation statistics)
│
Reporting
├── report.md (human‑readable summary)
```

## Schema Validation

### SubjectMetrics.csv Schema
- **File format**: CSV (comma‑separated values).
- **Header**: `subject_id,stage_label,mean_pli,n_epochs,centrality_degree_mean,centrality_betweenness_mean,centrality_eigenvector_mean,waking_night_id,sleep_night_id,temporal_proximity,age,gender,total_sleep_time_min,waking_duration_min`.
- **Rows**: One row per subject per sleep stage (e.g., 30 subjects × 4 stages = 120 rows).
- **Validation**: Checked by `validate.py` against `contracts/dataset.schema.yaml`.

### analysis_results.json Schema
- **File format**: JSON array of objects.
- **Each object**: Contains `metric_name`, `stage_label`, `band`, `correlation_coefficient`, `p_value_raw`, `p_value_corrected`, `significant`, `method`, `global_vif_flag`, `temporal_proximity_flag`, `n_subjects_used`.
- **Validation**: Checked by tests against `contracts/analysis.schema.yaml`.

### vif_report.json Schema
- **File format**: JSON object.
- **Fields**: `global_vif_degree`, `global_vif_betweenness`, `global_vif_eigenvector`, `global_vif_max`, `collinearity_flag`, `interpretation`.

---
