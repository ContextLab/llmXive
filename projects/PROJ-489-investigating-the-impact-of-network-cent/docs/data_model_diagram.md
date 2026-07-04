# Data Model Diagram

This document describes the data flow and entity relationships in the Network Centrality and Neural Synchrony project.

## Entity Relationship Diagram (Mermaid)

```mermaid
erDiagram
 SUBJECT ||--o{ EPOCH: has
 SUBJECT ||--o{ METRIC_ROW: has
 EPOCH ||--o{ PLI_PAIR: contains
 METRIC_ROW ||--o{ CENTRALITY_METRIC: includes
 METRIC_ROW ||--o{ SYNCHRONY_SCORE: includes
 CONNECTIVITY_MATRIX ||--o{ CENTRALITY_METRIC: generates

 SUBJECT {
 string subject_id PK
 int waking_night_id
 int sleep_night_id
 boolean temporal_proximity_flag
 }

 EPOCH {
 string epoch_id PK
 string subject_id FK
 int start_time
 string sleep_stage
 float[] eeg_signal
 }

 CONNECTIVITY_MATRIX {
 string matrix_id PK
 string subject_id FK
 string frequency_band "theta or alpha"
 float[][] adjacency_matrix
 }

 CENTRALITY_METRIC {
 string metric_id PK
 string matrix_id FK
 string metric_type "degree, betweenness, eigenvector"
 float value
 }

 PLI_PAIR {
 string pair_id PK
 string epoch_id FK
 string channel_pair "e.g., F3-F4"
 float pli_value
 }

 SYNCHRONY_SCORE {
 string score_id PK
 string subject_id FK
 string sleep_stage
 float mean_pli
 }

 METRIC_ROW {
 string row_id PK
 string subject_id FK
 float global_centrality
 float waking_coherence
 float n1_synchrony
 float n2_synchrony
 float n3_synchrony
 float rem_synchrony
 float vif_score
 }

 ANALYSIS_RESULT {
 string result_id PK
 string metric_id FK
 float coefficient
 float p_value_raw
 float p_value_fdr
 boolean is_significant
 }
```

## Data Flow Description

1. **Ingestion**: Raw `.edf` files are ingested from `data/raw` and mapped to `SUBJECT` entities.
2. **Segmentation**: Continuous EEG is split into `EPOCH` entities based on annotations.
3. **Connectivity**: `CONNECTIVITY_MATRIX` is computed for waking data using coherence.
4. **Network Analysis**: `CENTRALITY_METRIC` values are derived from the connectivity matrix.
5. **Synchrony**: `PLI_PAIR` values are calculated per epoch, aggregated into `SYNCHRONY_SCORE` per stage.
6. **Aggregation**: All metrics are flattened into a `METRIC_ROW` per subject.
7. **Analysis**: `ANALYSIS_RESULT` is generated via LME modeling on the aggregated metrics.

## File Artifacts Mapping

| Entity Group | Output File | Location |
|:--- |:--- |:--- |
| Raw Data | `*.edf` | `data/raw/` |
| Epochs | `*_epochs.fif` | `data/processed/` |
| Metrics | `SubjectMetrics.csv` | `data/metrics/` |
| Results | `analysis_results.json` | `data/results/` |
| Report | `final_report.md` | `reports/` |
