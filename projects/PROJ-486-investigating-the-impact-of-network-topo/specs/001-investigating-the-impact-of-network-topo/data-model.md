# Data Model: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

## 1. Entity Definitions

### Subject
- **ID**: `subject_id` (string, unique)
- **Attributes**:
  - `topology_clustering`: float (Clustering Coefficient)
  - `topology_path_length`: float (Characteristic Path Length)
  - `entrainment_strength`: float (Phase-Locking Value)
  - `atlas_type`: string (e.g., "Schaefer", "AAL")

### TopologyMetric
- **ID**: Composite (`subject_id`, `metric_type`, `atlas_type`)
- **Attributes**:
  - `value`: float
  - `calculation_date`: timestamp

### EntrainmentMetric
- **ID**: `subject_id`
- **Attributes**:
  - `plv`: float
  - `stimulus_type`: string (Required: must indicate "rhythmic" or similar. If "resting-state", data is rejected.)
  - `stimulus_freq`: float (optional, if available)

### DataGapReport
- **ID**: `gap_report_001`
- **Attributes**:
  - `timestamp`: timestamp
  - `missing_variables`: list of strings (e.g., "rhythmic_plv", "hcp_connectivity")
  - `status`: string (enum: "data_gap", "pipeline_success")
  - `message`: string (Human-readable explanation)

## 2. Data Flow

1.  **Ingestion**:
    - Raw fMRI (Parquet) $\to$ `data/raw/hcp_raw.parquet`
    - Raw Entrainment (CSV) $\to$ `data/raw/entrainment_raw.csv`
2.  **Validation**:
    - Check columns: `subject_id`, `entrainment_metric` (for CSV).
    - **Crucial**: Check for `stimulus_type` or "rhythmic" flag in Entrainment data. If missing or "resting-state", halt with "Data Gap".
    - Check columns: `subject_id`, `correlation_matrix` (or time-series) (for Parquet).
3.  **Processing**:
    - `hcp_raw` $\to$ `processed/connectivity_matrix.csv` (or numpy array).
    - `connectivity_matrix` $\to$ `processed/topology_metrics.csv` (Clustering, Path Length).
4.  **Analysis**:
    - `topology_metrics` + `entrainment_raw` $\to$ `processed/merged_analysis.csv`.
    - `merged_analysis` $\to$ `results/correlation_stats.json` (r, p, adj_p, vif).
5.  **Visualization**:
    - `results/correlation_stats.json` $\to$ `results/plots/scatter_plot.png`, `results/plots/sensitivity_bar.png`.
6.  **Data Gap Handling**:
    - If validation fails, generate `results/data_gap_report.json` and halt.

## 3. Schema Constraints

- **Subject ID**: Must match across both sources (Inner Join).
- **Numeric Fields**: Must be non-NaN for analysis.
- **Missing Data**: Subjects with missing `entrainment_strength` or `topology_metrics` are dropped and logged.
- **Zero Variance**: If `topology_clustering` or `topology_path_length` has 0 variance, the analysis for that metric is skipped and flagged.
- **Stimulus Validation**: If `stimulus_type` is not "rhythmic" or equivalent, the dataset is rejected.
- **Data Gap State**: The `DataGapReport` entity is a valid terminal state for the pipeline, representing a successful execution of the validation logic.

## 4. Error States

- `Invalid Entrainment Data`: Input CSV lacks `subject_id` or `entrainment_metric`.
- `Data Gap`: Verified datasets do not contain required variables (specifically "rhythmic stimulus" entrainment metrics).
- `Power Warning`: Merged N < 30.
- `Collinearity Warning`: VIF > 5.

## 5. Success State Definitions

- **Scientific Success**: All data present, correlation calculated, SC-001 met.
- **Pipeline Success (Data Gap)**: Data missing, pipeline halted with `DataGapReport`, SC-005 met. This is a valid success state for the system's operational requirements.
- **Pipeline Failure**: Unexpected error (e.g., network failure, code crash) not related to data validation.