# Data Model: The Influence of Network Topology on Neural Synchrony During Cognitive Tasks

## 1. Overview

This document defines the data structures used in the analysis pipeline. All data is stored in CSV or Parquet format for reproducibility.

## 2. Entity Definitions

### 2.1 Subject
Represents a single individual in the dataset.

| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | str | Unique identifier (e.g., "100106"). |
| `dataset_source` | str | "OpenNeuro" or "HCP" (if accessed). |
| `motion_fd` | float | Mean Frame Displacement (mm). |
| `excluded` | bool | True if motion > 0.5mm or missing data. |
| `exclusion_reason` | str | "High Motion", "Missing Task", etc. |

### 2.2 TimeSeries
The parcellated BOLD signal for a subject.

| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | str | Foreign key to Subject. |
| `scan_type` | str | "rest" or "task". |
| `timepoints` | int | Number of timepoints (e.g., 1200). |
| `regions` | int | Number of regions (200). |
| `data_path` | str | Path to CSV/NIfTI file. |

### 2.3 GraphMetric
Resting-state network topology metrics.

| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | str | Foreign key. |
| `clustering_coeff` | float | Global clustering coefficient. |
| `path_length` | float | Characteristic path length. |
| `global_efficiency` | float | Global efficiency. |
| `modularity` | float | Modularity score. |
| `threshold` | float | Proportional threshold used (e.g., 0.20). |

### 2.4 SynchronyMetric
Task-based neural synchrony metrics.

| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | str | Foreign key. |
| `network_pair` | str | "FPN-DMN", "FPN-FPN", etc. |
| `mean_fc_task` | float | Mean Pearson correlation during task. |
| `mean_fc_rest` | float | Mean Pearson correlation during rest. |
| `delta_fc` | float | Task-Evoked Change (Task FC - Rest FC). |
| `task_epoch` | str | "working_memory" or "n-back". |

### 2.5 CorrelationResult
Results of the statistical analysis.

| Field | Type | Description |
|-------|------|-------------|
| `metric_name` | str | e.g., "global_efficiency". |
| `network_pair` | str | e.g., "FPN-DMN". |
| `r_value` | float | Pearson correlation coefficient. |
| `p_value` | float | Uncorrected p-value. |
| `q_value` | float | FDR-corrected q-value. |
| `threshold` | float | Threshold used for this result. |

## 3. File Formats

### 3.1 `data/processed/subjects.csv`
```csv
subject_id,dataset_source,motion_fd,excluded,exclusion_reason
100106,OpenNeuro,0.12,False,
100206,OpenNeuro,0.65,True,High Motion
```

### 3.2 `data/processed/graph_metrics.csv`
```csv
subject_id,clustering_coeff,path_length,global_efficiency,modularity,threshold
100106,0.45,1.23,0.81,0.35,0.20
```

### 3.3 `data/processed/synchrony_metrics.csv`
```csv
subject_id,network_pair,mean_fc_task,mean_fc_rest,delta_fc,task_epoch
100106,FPN-DMN,0.32,0.25,0.07,working_memory
```

### 3.4 `data/processed/correlation_results.csv`
```csv
metric_name,network_pair,r_value,p_value,q_value,threshold
global_efficiency,FPN-DMN,0.24,0.012,0.048,0.20
```