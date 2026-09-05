# Data Model: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Overview

This document defines the data structures used throughout the pipeline, ensuring type safety and validation against the project's contracts.

## Entity Definitions

### 1. Subject
Represents a single participant in the study.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `subject_id` | `str` | Unique HCP ID (e.g., "100106") | Required, Unique |
| `age` | `int` | Age in years | > 0, < 100 |
| `sex` | `str` | "M" or "F" | Enum |
| `bmrq_total` | `float` | Total BMRQ score | Required (Halt if missing) |
| `fd_mean` | `float` | Mean Framewise Displacement | >= 0 |
| `motion_excluded` | `bool` | True if FD > 0.5 mm | Derived |

### 2. ConnectivityMatrix
Represents the functional connectivity between 200 brain regions (Schaefer Atlas).

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `subject_id` | `str` | Reference to Subject | Required |
| `matrix` | `list[list[float]]` | 200x200 Pearson correlation matrix | Symmetric, Diagonal=1.0, Values in [-1, 1] |
| `atlas` | `str` | Atlas used | "Schaefer200" |

### 3. NetworkMetrics
Derived graph theory metrics for a subject.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `subject_id` | `str` | Reference to Subject | Required |
| `global_efficiency` | `float` | Global network integration | > 0 |
| `modularity` | `float` | Network segregation | 0 < value < 1 |
| `participation_coeff` | `float` | Cross-module connectivity | 0 < value < 1 |
| `dmn_efficiency` | `float` | Within-DMN efficiency | > 0 |
| `salience_efficiency` | `float` | Within-Salience efficiency | > 0 |
| `visual_efficiency` | `float` | Within-Visual efficiency | > 0 |
| `vif_global_efficiency` | `float` | Variance Inflation Factor | Optional, for collinearity check |

### 4. AnalysisResult
Final output of the statistical modeling phase.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `metric_name` | `str` | Name of the network metric (e.g., "global_efficiency") | Required |
| `correlation_r` | `float` | Pearson r with BMRQ | [-1, 1] |
| `p_value` | `float` | Raw p-value | [0, 1] |
| `p_value_fdr` | `float` | FDR-corrected p-value | [0, 1] |
| `significant` | `bool` | True if p_value_fdr < 0.05 | Derived |
| `sample_size` | `int` | Number of subjects used | Required |
| `power_achieved` | `float` | Achieved power for r=0.20 | Required |

## Data Flow

1.  **Raw Data** (OpenNeuro NIfTI/CSV) -> `download.py` -> **Raw Subject Data**
2.  **Raw Subject Data** -> `preprocess.py` (Off-CI) -> **Cleaned Time Series**
3.  **Cleaned Time Series** -> `connectivity.py` -> **ConnectivityMatrix**
4.  **ConnectivityMatrix** -> `graph_metrics.py` -> **NetworkMetrics** (with VIF check)
5.  **NetworkMetrics** + **Subject Data** -> `stats.py` -> **AnalysisResult**

## Constraints & Validation

*   **Symmetry**: All connectivity matrices must be symmetric.
*   **Diagonal**: Diagonal elements must be 1.0 (self-correlation).
*   **Range**: Correlation values must be in [-1, 1].
*   **Missing Data**: Subjects with missing BMRQ or excessive motion (FD > 0.5) are excluded from the final `AnalysisResult` dataset.
*   **Collinearity**: If VIF > 5 for any predictor, the pipeline applies PCA or removes the predictor before regression.