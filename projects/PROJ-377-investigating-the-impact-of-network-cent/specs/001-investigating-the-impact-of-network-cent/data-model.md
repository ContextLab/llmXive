# Data Model: Investigating the Impact of Network Centrality on the Consolidation of Motor Memories

## Entities & Attributes

### Subject
Represents a single participant in the study.
- `subject_id`: string (unique identifier)
- `age`: integer (years)
- `sex`: string (M/F/Other)
- `pre_motor_score`: float (performance at pre-consolidation)
- `post_motor_score`: float (performance at post-consolidation)
- `improvement_score`: float (calculated: `(post - pre) / pre * 100`)
- `excluded_reason`: string (optional, if excluded due to motion or missing data)

### ConnectivityMatrix
Represents the functional connectivity graph for a subject.
- `subject_id`: string (foreign key)
- `region_labels`: list of strings (names of the ~90 brain regions)
- `connectivity_matrix`: 2D array (float32, shape [90, 90], symmetric)
- `preprocessing_params`: JSON (snapshot of fMRIPrep/nilearn settings used)

### CentralityMetrics
Derived graph metrics for a subject.
- `subject_id`: string (foreign key)
- `degree_centrality`: list of floats (length 90)
- `betweenness_centrality`: list of floats (length 90)
- `eigenvector_centrality`: list of floats (length 90)
- `global_centrality`: float (aggregated score, e.g., mean of top [deferred] hubs)
- `vif_degree`: float (Variance Inflation Factor for degree if used)
- `vif_betweenness`: float (VIF for betweenness)
- `vif_eigenvector`: float (VIF for eigenvector)

### ModelResults
Outputs of the statistical analysis.
- `model_type`: string (e.g., "LinearRegression", "GAM")
- `coefficient_centrality`: float
- `p_value_centrality`: float
- `p_value_age`: float
- `p_value_sex`: float
- `r_squared`: float
- `rmse`: float
- `permutation_p_value`: float (empirical)
- `cv_r_squared_mean`: float
- `cv_r_squared_std`: float
- `aic`: float (optional, for GAM comparison)
- `bic`: float (optional, for GAM comparison)

## Data Flow

1.  **Raw Data** (OpenNeuro Parquet) -> **Download**: `data/raw/openneuro_data.parquet`
2.  **Download** -> **Preprocess**: `data/processed/subjects.csv` (cleaned, filtered), `data/processed/connectivity_matrices.npz` (or parquet of flattened matrices)
3.  **Preprocess** -> **Centrality**: `data/processed/centrality_metrics.csv`
4.  **Centrality** -> **Analysis**: `data/processed/model_results.json`
5.  **Analysis** -> **Report**: `reproducibility_report.json`

## Constraints

-   **Memory**: All intermediate matrices must be stored in `float32` to minimize RAM usage.
-   **Completeness**: Any subject missing `age`, `sex`, or `improvement_score` must be excluded.
-   **Reproducibility**: All derived data files must be checksummed.
