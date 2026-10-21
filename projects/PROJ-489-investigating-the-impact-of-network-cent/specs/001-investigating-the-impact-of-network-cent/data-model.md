# Data Model: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Entities

### Subject
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | Unique identifier (e.g., `S001`). |
| `age` | integer | Age in years (optional). |
| `gender` | string | `"M"` or `"F"` (optional). |
| `has_waking` | boolean | `True` if a ≥ 2 min clean waking segment exists. |
| `has_sleep` | boolean | `True` if sleep epochs were successfully preprocessed. |

### WakingNetwork
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK → Subject. |
| `band` | string | `"theta"` or `"alpha"`. |
| `connectivity_matrix` | numpy.ndarray | Symmetric coherence matrix (0 < value < 1). |
| `centrality_degree` | dict[string, float] | Node → degree centrality (EEG‑only). |
| `centrality_betweenness` | dict[string, float] | Node → betweenness centrality (EEG‑only). |
| `centrality_eigenvector` | dict[string, float] | Node → eigenvector centrality (EEG‑only). |
| `centrality_degree_mean` | float | Mean degree across EEG nodes. |
| `centrality_betweenness_mean` | float | Mean betweenness across EEG nodes. |
| `centrality_eigenvector_mean` | float | Mean eigenvector across EEG nodes. |
| `centrality_channel_set` | string | `"EEG"` (primary) or `"EEG+peripheral"` (optional secondary analysis). |

### SleepStageEpoch
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK → Subject. |
| `stage_label` | string | `"N1"`, `"N2"`, `"N3"`, or `"REM"`. |
| `epoch_index` | integer | Sequential index of the 30 s epoch. |
| `epoch_duration_sec` | integer | Fixed short interval (source 1908.11463). |
| `pli_score` | float | PLV for this epoch (0 ≤ score ≤ 1). |

### SubjectMetrics (aggregated per subject & stage)
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK → Subject. |
| `stage_label` | string | `"N1"`, `"N2"`, `"N3"`, or `"REM"`. |
| `mean_pli` | float | Mean PLV across epochs of this stage (0 ≤ ≤ 1). |
| `n_epochs` | integer | Number of epochs contributing to `mean_pli` (≥ 1). |
| `centrality_degree_mean` | float | Mean degree centrality (EEG‑only). |
| `centrality_betweenness_mean` | float | Mean betweenness centrality (EEG‑only). |
| `centrality_eigenvector_mean` | float | Mean eigenvector centrality (EEG‑only). |
| `waking_night_id` | string | Identifier for the waking recording night (extracted from EDF header). |
| `sleep_night_id` | string | Identifier for the sleep recording night. |
| `temporal_proximity` | boolean | `True` if waking and sleep recordings are from the same night; indicates potential temporal confounding. |
| `age` | integer | Optional. |
| `gender` | string | Optional (`"M"` or `"F"`). |
| `total_sleep_time_min` | number | Total sleep time in minutes (derived from durations of all sleep stages). |
| `waking_duration_min` | number | Duration of the waking segment in minutes (used for filtering: must be ≥ 2 min). |
| `centrality_icc` | number | Intraclass Correlation Coefficient for split‑half centrality stability (average across metrics). |
| `centrality_icc_flag` | boolean | `True` if ICC < 0.6 (unstable). |
| `centrality_wake_sleep_icc` | number | Intraclass Correlation Coefficient comparing waking centrality to N2‑stage centrality (cross‑state stability). |
| `centrality_wake_sleep_icc_flag` | boolean | `True` if cross‑state ICC < 0.6 (unstable across states). |

### AnalysisResult
| Field | Type | Description |
|-------|------|-------------|
| `metric_name` | string | `"degree"`, `"betweenness"`, or `"eigenvector"`. |
| `stage_label` | string | `"N1"`, `"N2"`, `"N3"`, or `"REM"`. |
| `band` | string | `"theta"` or `"alpha"`. |
| `correlation_coefficient` | number | Pearson, Spearman, or partial correlation (−1 ≤ ≤ 1). |
| `p_value_raw` | number | Unadjusted p‑value (0 ≤ ≤ 1). |
| `p_value_corrected` | number | Bonferroni‑adjusted p‑value (p_raw × 30, capped at 1.0). |
| `significant` | boolean | `True` if corrected p < 0.05. |
| `method` | string | `"pearson"`, `"spearman"`, or `"partial"`. |
| `global_vif_flag` | boolean | `True` if the global VIF across subjects for the three centrality metrics exceeds 5.0; indicates collinearity. |
| `temporal_proximity_flag` | boolean | Mirrors `temporal_proximity`. |
| `n_subjects_used` | integer | Number of subjects included in this correlation (may be < 30 if some subjects lack data for this stage). |
| `power_estimate` | number | Post‑hoc achieved power for this test (0 ≤ ≤ 1). |

### VIFReport
| Field | Type | Description |
|-------|------|-------------|
| `global_vif_degree` | number | VIF for degree centrality across subjects. |
| `global_vif_betweenness` | number | VIF for betweenness centrality. |
| `global_vif_eigenvector` | number | VIF for eigenvector centrality. |
| `global_vif_max` | number | Maximum of the three VIF values. |
| `collinearity_flag` | boolean | `True` if any VIF > 5.0. |
| `interpretation` | string | Narrative interpretation of collinearity. |

## Data Flow
```
Raw Data
├── data/raw/*.edf                         # Downloaded EDF files
│
Preprocessing
├── data/processed/epochs_{subj}.npz
├── data/processed/metadata_{subj}.json
│
Connectivity & Centrality
├── data/processed/connectivity_theta_{subj}.npy
├── data/processed/connectivity_alpha_{subj}.npy
├── data/processed/centrality_{subj}.json          # EEG‑only
├── data/processed/centrality_periph_{subj}.json   # optional peripheral
├── data/processed/centrality_icc_{subj}.json      # split‑half ICC
├── data/processed/centrality_cross_state_icc_{subj}.json  # wake‑vs‑N2 ICC
│
Sleep‑Stage Synchrony
├── data/processed/pli_{stage}_{subj}.npy
│
Aggregation
├── data/metrics/SubjectMetrics.csv
│
Collinearity & Analysis
├── data/results/vif_report.json
├── data/results/analysis_results.json
├── data/results/centrality_stability.json
│
Reporting
├── report.md
```

## Schema Validation
- **SubjectMetrics.csv** must conform to `contracts/dataset.schema.yaml`.  
- **analysis_results.json** must conform to `contracts/analysis.schema.yaml`.  
- **vif_report.json** must match the VIFReport structure described above.  
- **centrality_stability.json** must include `icc` and `icc_flag` fields per subject (validated by custom test suite).

---



