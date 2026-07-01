# Data Model: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

## 1. Entities and Relationships

### 1.1 Participant
The core entity linking dMRI and EEG data.
- **Attributes**:
  - `subject_id` (str): Unique identifier (e.g., "HCP_100103").
  - `age` (int): Age at scan.
  - `sex` (str): Male/Female.
  - `status` (str): "included", "excluded_artifact", "excluded_disconnected".
  - `exclusion_reason` (str): Optional, e.g., ">30% channels removed".

### 1.2 StructuralConnectome
Derived from dMRI tractography.
- **Attributes**:
  - `subject_id` (str): FK to Participant.
  - `adjacency_matrix_path` (str): Path to `.npy` or `.csv` file (360x360).
  - `mean_degree` (float): Average node degree (normalized).
  - `clustering_coefficient` (float): Global clustering coefficient.
  - `rich_club_auc` (float): Area Under the Curve of normalized rich-club coefficient.
  - `graph_connected` (bool): True if the graph is a single component.

### 1.3 AvalancheRecord
Derived from EEG time series.
- **Attributes**:
  - `subject_id` (str): FK to Participant.
  - `threshold_value` (float): The amplitude threshold used (e.g., 0.75).
  - `bin_size_ms` (int): Fixed at 4 (or 8, 12 for sensitivity).
  - `size_exponent` (float): Scaling exponent (α) for avalanche size.
  - `duration_exponent` (float): Scaling exponent (α) for avalanche duration.
  - `fit_quality` (str): "good" (KS p > 0.05), "poor" (KS p <= 0.05).
  - `fit_model` (str): "power_law", "log_normal", or "exponential".

### 1.4 CorrelationResult
The final statistical output.
- **Attributes**:
  - `metric_pair` (str): e.g., "degree_vs_size_exponent".
  - `spearman_rho` (float): Correlation coefficient.
  - `p_value` (float): Raw p-value.
  - `corrected_p_value` (float): Permutation-corrected p-value.
  - `vif_value` (float): Variance Inflation Factor (if applicable).
  - `threshold_used` (float): The avalanche threshold used for this result.
  - `ci_lower` (float): Lower bound of bootstrap CI.
  - `ci_upper` (float): Upper bound of bootstrap CI.

## 2. Data Flow

1.  **Raw Input**: `data/raw/dMRI/`, `data/raw/EEG/` (OpenNeuro downloads).
2.  **Preprocessed**: `data/processed/connectomes/`, `data/processed/eeg_clean/`.
3.  **Metrics**: `data/processed/metrics/network_metrics.csv`, `data/processed/metrics/avalanche_metrics.csv`.
4.  **Analysis**: `data/processed/results/correlation_results.csv`.
5.  **Final Output**: `data/processed/results/final_report.json`.

## 3. Constraints and Validation

- **Subject ID Matching**: A participant must exist in both dMRI and EEG processed sets to be included.
- **Graph Connectivity**: Participants with disconnected graphs (0 mean degree or multiple components) are excluded.
- **Power-Law Fit**: Participants where `fit_quality` != "good" are excluded from correlation analysis.
- **Artifact Threshold**: Participants with >30% channels removed are excluded.
- **Normalization**: Rich-Club AUC must be normalized against degree-preserving null models.