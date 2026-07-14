# Data Model

## Overview

This document describes the data structures, file formats, and relationships used in the llmXive sleep synchrony research pipeline.

## Directory Structure

```
project_root/
├── code/ # Source code
├── data/
│ ├── raw/ # Original downloaded EDF files
│ ├── processed/ # Cleaned, epoched data (NPZ/CSV)
│ ├── metrics/ # Computed metrics (CSV)
│ └── results/ # Analysis outputs (JSON)
├── reports/ # Final reports (Markdown)
├── tests/ # Unit and integration tests
└── docs/ # Documentation
```

## Entities

### Subject

Represents a single participant in the study.

| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | str | Unique identifier (e.g., "ST50") |
| `waking_night_id` | int | ID of the night for waking data |
| `sleep_night_id` | int | ID of the night for sleep data |

### Epoch

A time-segment of EEG data labeled with a sleep stage.

| Field | Type | Description |
|-------|------|-------------|
| `epoch_id` | str | Unique identifier |
| `subject_id` | str | Foreign key to Subject |
| `start_time` | float | Start time in seconds |
| `duration` | float | Duration in seconds |
| `sleep_stage` | str | Wake, N1, N2, N3, REM |
| `signal_data` | np.ndarray | EEG signal array |

### ConnectivityMatrix

Functional connectivity between electrode pairs.

| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | str | Foreign key to Subject |
| `matrix` | np.ndarray | Symmetric matrix (channels x channels) |
| `metric` | str | Coherence, PLI, etc. |
| `band` | str | Theta, Alpha, etc. |

### CentralityMetrics

Network centrality scores per subject.

| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | str | Foreign key to Subject |
| `degree_centrality` | float | Average degree |
| `betweenness_centrality` | float | Betweenness score |
| `eigenvector_centrality` | float | Eigenvector score |

### SynchronyScores

Neural synchrony metrics per subject and sleep stage.

| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | str | Foreign key to Subject |
| `sleep_stage` | str | Wake, N1, N2, N3, REM |
| `mean_pli` | float | Mean Phase Lag Index |
| `global_coherence` | float | Global coherence score |

## File Formats

### SubjectMetrics.csv

Aggregated metrics for each subject.

```csv
subject_id,degree_centrality,betweenness_centrality,eigenvector_centrality,pli_wake,pli_n1,pli_n2,pli_n3,pli_rem,global_coherence,waking_night_id,sleep_night_id
ST50,0.12,0.05,0.08,0.23,0.25,0.28,0.30,0.22,0.45,1,1
```

### analysis_results.json

Statistical analysis outputs.

```json
{
 "coefficients": {
 "pli": 0.45,
 "global_coherence": 0.10
 },
 "p_values": {
 "pli": 0.03,
 "global_coherence": 0.15
 },
 "fdr_corrected_p_values": {
 "pli": 0.06,
 "global_coherence": 0.20
 },
 "significance_flags": {
 "pli": "Significant",
 "global_coherence": "Non-Significant"
 },
 "diagnostics": {
 "shapiro_wilk": {
 "statistic": 0.96,
 "p_value": 0.15,
 "is_normal": true
 }
 },
 "limitation_notes": {
 "temporal_proximity": false
 }
}
```

## Relationships

- **Subject** has many **Epochs**.
- **Subject** has one **CentralityMetrics** record.
- **Subject** has multiple **SynchronyScores** (one per sleep stage).
- **Analysis** consumes **SubjectMetrics** to produce **analysis_results**.
