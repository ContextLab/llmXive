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

### WakingCoherence
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK → Subject. |
| `band` | string | `"theta"` or `"alpha"`. |
| `coherence` | float | Inter‑hemispheric coherence value (0 ≤ ≤ 1). |
| `night_id` | string | Identifier for the waking recording night. |
| `icc_split_half` | float | Split‑half ICC for the coherence of this band (0 ≤ ≤ 1). |
| `icc_flag` | boolean | `True` if ICC < 0.6 (unstable). |

### SleepStageEpoch
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK → Subject. |
| `stage_label` | string | `"N1"`, `"N2"`, `"N3"`, or `"REM"`. |
| `epoch_index` | integer | Sequential index of the 30 s epoch. |
| `pli_score` | float | PLV for this epoch (0 ≤ ≤ 1). |
| `night_id` | string | Identifier for the sleep recording night. |

### SubjectMetrics (aggregated per subject per stage)
| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | FK → Subject. |
| `stage_label` | string | `"N1"`, `"N2"`, `"N3"`, or `"REM"`. |
| `mean_pli` | float | Mean Phase‑Locking Value across all epochs of this stage (0 ≤ ≤ 1). |
| `n_epochs` | integer | Number of epochs contributing to `mean_pli` (≥ 1). |
| `theta_coherence` | float | Inter‑hemispheric theta coherence (0 ≤ ≤ 1). |
| `alpha_coherence` | float | Inter‑hemispheric alpha coherence (0 ≤ ≤ 1). |
| `theta_icc` | float | Split‑half ICC for theta‑band coherence (0 ≤ ≤ 1). |
| `alpha_icc` | float | Split‑half ICC for alpha‑band coherence (0 ≤ ≤ 1). |
| `theta_icc_flag` | boolean | `True` if theta ICC < 0.6. |
| `alpha_icc_flag` | boolean | `True` if alpha ICC < 0.6. |
| `waking_night_id` | string | Identifier for the waking recording night. |
| `sleep_night_id` | string | Identifier for the sleep recording night. |
| `temporal_proximity` | boolean | `True` if waking and sleep nights are the same. |
| `medication_status` | string | Medication status (optional). |
| `sleep_quality_score` | number | Sleep‑quality score (optional). |
| `eeg_noise_level` | number | Estimated EEG‑noise level (optional). |
| `total_sleep_time_min` | number | Total sleep time in minutes (≥ 0). |
| `waking_duration_min` | number | Duration of ≥ 2 min waking segment (minimum 0). |

## Data Flow
```
Raw Data
├── data/raw/*.edf                         # Downloaded EDF files
│
Preprocessing
├── data/processed/epochs_{subj}.npz
├── data/processed/metadata_{subj}.json
│
Coherence & ICC
├── data/processed/coherence_{band}_{subj}.npy      # single coherence value per band
├── data/processed/coherence_icc_{subj}.json        # theta & alpha ICC
│
PLV
├── data/processed/pli_{stage}_{subj}.npy
│
Aggregation
├── data/metrics/SubjectMetrics.csv
│
Statistical Analysis
├── data/results/analysis_results.json
├── data/results/coherence_icc_report.json
│
Reporting
├── report.md
```

## Schema Validation
- **SubjectMetrics.csv** must conform to `contracts/dataset.schema.yaml`.  
- **analysis_results.json** must conform to `contracts/analysis.schema.yaml`.  
- **coherence_icc_report.json** must include `theta_icc`, `alpha_icc`, and corresponding flags per subject (validated by custom test suite).

---


