# Data Model: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

## 1. Entities

### Subject
Represents an individual participant in the study.
- `subject_id` (str): Unique identifier (Primary Key).
- `dataset_source` (str): Source of the data (e.g., "HCP", "Simulated").

### TopologyMetric
Represents a calculated network property for a subject.
- `subject_id` (str): Foreign Key to Subject.
- `atlas_type` (str): "Schaefer", "AAL", or "Power".
- `metric_name` (str): "clustering_coefficient" or "characteristic_path_length".
- `value` (float): The calculated metric value.
- `flag` (str): "normal", "zero_variance", "non_informative".

### EntrainmentStrength
Represents the quantified neural response.
- `subject_id` (str): Foreign Key to Subject.
- `value` (float): Phase-Locking Value (PLV) or equivalent.
- `source` (str): "Real" or "Simulated (Validation Only)".

### PrecomputedConnectivity
Represents pre-computed connectivity matrices or metrics.
- `subject_id` (str): Foreign Key to Subject.
- `atlas_type` (str): "Schaefer", "AAL", or "Power".
- `connectivity_matrix` (array): The pre-computed connectivity matrix (flattened or 2D).
- `clustering_coefficient` (float): Pre-computed clustering coefficient.
- `characteristic_path_length` (float): Pre-computed characteristic path length.

### RawTimeSeries
Represents raw fMRI time series data.
- `subject_id` (str): Foreign Key to Subject.
- `atlas_type` (str): "Schaefer", "AAL", or "Power".
- `time_series` (array): The raw fMRI time series data (N_timepoints x N_regions).

## 2. Data Flow

1.  **Input**: `data/raw/hcp_connectivity_subset.csv` (or similar), `data/raw/entrainment_metrics.csv`.
2.  **Processing**:
    - Load and validate.
    - Check for `PrecomputedConnectivity` or `RawTimeSeries` in the input.
    - If `RawTimeSeries`, parcellate and compute connectivity matrices.
    - Compute graph metrics (if not pre-computed).
    - Check for zero variance.
    - Filter out non-informative metrics.
    - Join on `subject_id`.
3.  **Output**: `data/processed/joined_data.csv`, `data/processed/correlation_results.csv`.
4.  **Visualization**: `data/visualizations/scatter_topology_entrainment.png`.

## 3. Schema Definitions

### Input Schema: Entrainment CSV
- `subject_id`: string, required.
- `entrainment_metric`: float, required.

### Output Schema: Correlation Results
- `atlas_type`: string.
- `metric_name`: string.
- `r`: float (Spearman correlation).
- `p_value`: float.
- `adjusted_p_value`: float (Holm-Bonferroni).
- `is_significant`: boolean.
- `n_subjects`: integer.
- `status`: string ("Valid", "Data Insufficient", "Collinearity Warning").

### Output Schema: MLR Results (if VIF <= 5)
- `r_squared`: float.
- `adj_r_squared`: float.
- `coefficient_clustering`: float.
- `p_clustering`: float.
- `coefficient_path`: float.
- `p_path`: float.
- `vif_clustering`: float.
- `vif_path`: float.
- `adjusted_p_clustering`: float.
- `adjusted_p_path`: float.