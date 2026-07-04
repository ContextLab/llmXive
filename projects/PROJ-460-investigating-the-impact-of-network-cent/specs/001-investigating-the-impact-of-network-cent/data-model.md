# Data Model: Investigating Network Centrality in ASD Resting-State fMRI

## 1. Entity Definitions

### Participant
- **Description**: Individual subject with fMRI scan and diagnosis.
- **Attributes**:
  - `participant_id` (str): Unique identifier.
  - `diagnosis` (str): "ASD" or "Control".
  - `age` (float): Age in years.
  - `sex` (str): "M" or "F".
  - `motion_fd` (float): Mean Framewise Displacement.
  - `raw_path` (str): Path to raw NIfTI file.
  - `preprocessed_path` (str): Path to preprocessed NIfTI file.

### TimeSeries
- **Description**: Preprocessed fMRI signal for each ROI.
- **Attributes**:
  - `participant_id` (str): Link to Participant.
  - `roi_index` (int): 0 to 399.
  - `signal` (array[float]): Time-series values (T timepoints).
  - `shape` (tuple): (T, 400).

### ConnectivityMatrix
- **Description**: Pearson correlation matrix between ROIs.
- **Attributes**:
  - `participant_id` (str): Link to Participant.
  - `matrix` (array[float]): 400x400 symmetric matrix.
  - `threshold` (float): Percentage of edges kept (e.g., 0.10).

### CentralityMetrics
- **Description**: Graph topology measures per node.
- **Attributes**:
  - `participant_id` (str): Link to Participant.
  - `roi_index` (int): 0 to 399.
  - `degree_centrality` (float): Normalized degree.
  - `betweenness_centrality` (float): Normalized betweenness.
  - `eigenvector_centrality` (float): Normalized eigenvector.

### GroupComparison
- **Description**: Statistical test results.
- **Attributes**:
  - `roi_index` (int): 0 to 399.
  - `metric_type` (str): "degree", "betweenness", "eigenvector".
  - `t_statistic` (float): t-value.
  - `p_value` (float): Uncorrected p-value.
  - `q_value` (float): FDR-corrected q-value.
  - `mean_asd` (float): Mean value in ASD group.
  - `mean_control` (float): Mean value in Control group.

## 2. Data Flow

1. **Raw**: `data/raw/` (NIfTI files) -> **Preprocessed**: `data/processed/preprocessed/` (NIfTI).
2. **Preprocessed** -> **TimeSeries**: `data/processed/timeseries/` (CSV/Parquet).
3. **TimeSeries** -> **ConnectivityMatrix**: `data/processed/matrices/` (NPZ).
4. **ConnectivityMatrix** -> **CentralityMetrics**: `data/processed/centrality/` (CSV).
5. **CentralityMetrics** -> **GroupComparison**: `data/processed/results/` (CSV).
6. **CentralityMetrics** -> **Classifier**: `data/processed/classification/` (Pickle).

## 3. Storage Constraints

- **Raw Data**: ~14GB limit. If full ABIDE exceeds this, sampling is enforced.
- **Processed Data**: Stored as compressed NPZ/Parquet to minimize size.
- **Intermediate**: Deleted after use to save space (except final results).
