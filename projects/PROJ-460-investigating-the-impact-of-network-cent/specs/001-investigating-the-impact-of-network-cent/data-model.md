# Data Model: Investigating Network Centrality in ASD Resting-State fMRI

## 1. Entity-Relationship Overview

The project data model consists of three primary layers: **Raw/Preprocessed Inputs**, **Derived Network Metrics**, and **Statistical Outputs**.

### Key Entities

1.  **Participant**: Represents an individual subject.
    *   `id`: Unique string identifier.
    *   `diagnosis`: Enum (`ASD`, `Control`).
    *   `age`: Float.
    *   `sex`: Enum (`M`, `F`).
    *   `motion_mean`: Float (mean framewise displacement).
    *   `status`: Enum (`valid`, `excluded_motion`, `excluded_missing_label`).

2.  **TimeSeries**: Preprocessed fMRI signal.
    *   `participant_id`: FK to Participant.
    *   `roi_indices`: Array of integers (0 to 399).
    *   `timepoints`: Integer (e.g., 300).
    *   `data`: 2D Array (timepoints × 400).

3.  **ConnectivityMatrix**: Functional connectivity graph.
    *   `participant_id`: FK to Participant.
    *   `matrix`: 2D Array (400 × 400), symmetric, values ∈ [-1, 1].
    *   `threshold`: Float (correlation threshold used).

4.  **CentralityMetrics**: Network topology measures.
    *   `participant_id`: FK to Participant.
    *   `roi_index`: Integer (0 to 399).
    *   `degree`: Float.
    *   `betweenness`: Float.
    *   `eigenvector`: Float.

5.  **GroupComparison**: Statistical test results.
    *   `roi_index`: Integer.
    *   `metric_type`: Enum (`degree`, `betweenness`, `eigenvector`).
    *   `mean_asd`: Float.
    *   `mean_control`: Float.
    *   `t_statistic`: Float.
    *   `p_value`: Float.
    *   `q_value`: Float (FDR corrected).
    *   `significant`: Boolean.

## 2. File Formats & Storage

*   **Raw Data**: `.nii.gz` (NIfTI) - stored in `data/raw/`.
*   **TimeSeries**: `.npy` (NumPy) or `.parquet` (Pandas) - stored in `data/processed/timeseries/`.
*   **Connectivity Matrices**: `.npy` (compressed) - stored in `data/processed/connectivity/`.
*   **Centrality Metrics**: `.parquet` (wide format: rows=participants, cols=metrics_per_roi) - stored in `data/processed/centrality/`.
*   **Statistical Results**: `.json` (structured) - stored in `data/outputs/stats/`.
*   **Visualizations**: `.png` - stored in `data/outputs/figures/`.

## 3. Data Flow Diagram

1.  **Input**: `Participant` metadata + `Raw fMRI` (or Synthetic).
2.  **Preprocessing**: `Raw fMRI` → `TimeSeries` (via fMRIPrep or Synthetic Gen).
3.  **Graph Construction**: `TimeSeries` → `ConnectivityMatrix` (Correlation + Thresholding).
4.  **Metric Computation**: `ConnectivityMatrix` → `CentralityMetrics` (NetworkX).
5.  **Statistical Analysis**: `CentralityMetrics` + `Participant` → `GroupComparison` (T-test + FDR).
6.  **Output**: `GroupComparison` → `Visualizations` (Brain Maps) + `Paper Tables`.

## 4. Constraints & Validations

*   **Motion Exclusion**: Participants with `motion_mean > 3.0mm` are excluded.
*   **Label Exclusion**: Participants with missing `diagnosis` are excluded.
*   **Graph Connectivity**: If thresholding disconnects the graph, the top percentile of edges is used as a fallback.
*   **Data Integrity**: All derived files must reference the source file hash in their metadata.
*   **Real Data Requirement**: Scientific outputs must be derived from real data. Synthetic data outputs are marked as "Illustrative Only" and are not included in scientific results.