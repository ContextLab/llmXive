# Data Model: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

## Overview

This document defines the data structures, schemas, and file formats used throughout the pipeline. All data is stored in `data/` with strict versioning.

## Entity Definitions

### 1. Participant
A unique research subject.
*   **Attributes**:
    *   `subject_id`: String (e.g., "sub-001")
    *   `dataset_source`: String ("OpenNeuro", "Neurofusion", "Synthetic")
    *   `quality_flag`: Boolean (True if data passes QC)

### 2. StructuralConnectome
Weighted graph derived from dMRI.
*   **Attributes**:
    *   `adjacency_matrix`: 2D Array (N_nodes x N_nodes)
    *   `node_degree`: 1D Array (mean degree per node)
    *   `clustering_coefficient`: 1D Array (local clustering per node)
    *   `rich_club_coefficient`: Float (global coefficient)
    *   `parcellation`: String (e.g., "HCP-MMP1.0")

### 3. AvalancheRecord
Detected neural event from EEG.
*   **Attributes**:
    *   `size`: Integer (number of active channels)
    *   `duration`: Float (time in seconds or bins)
    *   `time_bins`: List of integers (indices of active bins)
    *   `participant_id`: String

### 4. CorrelationResult
Statistical association between metrics.
*   **Attributes**:
    *   `metric_pair`: String (e.g., "degree_vs_exponent")
    *   `spearman_rho`: Float
    *   `p_value`: Float
    *   `corrected_p_value`: Float
    *   `vif_score`: Float (if applicable)
    *   `threshold_used`: Float (e.g., 0.75)

## File Formats

### Raw Data (`data/raw/`)
*   **dMRI**: Parquet or NIfTI (from OpenNeuro).
*   **EEG**: CSV or Parquet (from Neurofusion).
*   **Checksum**: `data/raw/.checksums.json` (SHA256 hashes).

### Processed Data (`data/processed/`)
*   **Connectivity Matrices**: `.npy` or `.csv` (N x N).
*   **EEG Time Series**: `.npy` (Channels x Time).
*   **Avalanche Events**: `.csv` (size, duration, participant_id).

### Results (`data/results/`)
*   **Metrics**: `metrics.csv` (Participant, Degree, Clustering, RichClub, Exponent_Size, Exponent_Duration).
*   **Correlations**: `correlations.csv` (Metric, Theta, P, P_Corr, VIF).
*   **Collinearity**: `collinearity_status.json`.
*   **Report**: `report.md`.

## Data Flow

1.  **Download**: `raw/` (Parquet/CSV) -> **Preprocess** -> `processed/` (Numpy/CSV) -> **Analyze** -> `results/` (CSV/JSON).
2.  **QC**: Any participant failing QC (e.g., disconnected graph, no avalanches) is dropped before `results/` generation.
3.  **Validation**: Unit tests on synthetic data (ground truth) validate the statistical logic.