# Data Model: Linking Resting‑State fMRI Entropy to Creative Problem Solving

## Entity Definitions

### Subject
Represents an individual participant in the HCP cohort.
- `subject_id`: Unique identifier (string).
- `age`: Age in years (float).
- `sex`: Biological sex (string: "M" or "F").
- `framewise_displacement`: Mean head motion metric (float).
- `nih_creativity_score`: NIH Toolbox Creativity Composite score (float).
- `exclusion_reason`: Null if included, or string describing exclusion (e.g., "missing_score", "motion_threshold").

### ParcelTimeSeries
Extracted BOLD signal for a specific parcel.
- `subject_id`: Foreign key to Subject.
- `parcel_id`: Integer (0-359).
- `network_name`: String (DMN, FPN, CON, VAN, SMN, VN).
- `time_series_values`: List of floats (length ~1200 for HCP).

### EntropyMetric
Computed entropy value for a specific parcel/network.
- `subject_id`: Foreign key to Subject.
- `metric_type`: String ("global", "network", "parcel").
- `target_id`: String (e.g., "DMN", "parcel_42", or "global").
- `entropy_value`: Computed entropy (float).
- `scale_factor`: Integer (1-20).
- `parameters`: JSON object (e.g., `{"m": 2, "r": 0.2}`).
- `coefficient_of_variation`: Coefficient of Variation of parcel-wise entropies for the subject (float).

### AssociationResult
Statistical test outcome.
- `network_name`: String (or "global").
- `coefficient`: Regression coefficient (float).
- `standard_error`: Robust SE (float).
- `p_value`: Raw p-value (float).
- `adjusted_p_value`: BH-FDR corrected p-value (float).
- `model_type`: String ("primary", "symmetry_check", "sensitivity").
- `sensitivity_delta_p`: Change in p-value across r-sweep (float).
- `stability_score`: Variance of p-values across r-sweep (float).
- `valid_parcel_count`: Number of valid parcels used for this subject (integer).
- `completeness_pct`: Percentage of valid parcels (float).

## Data Flow

1. **Raw Ingestion**: `data/raw/*.nii.gz` or `*.dconn.nii` (Downloaded from OpenNeuro/HCP S3).
2. **Preprocessed**: `data/processed/subject_metadata.csv`, `data/processed/parcel_timeseries.csv`.
3. **Computed**: `data/results/entropy_metrics.csv`.
4. **Statistical**: `data/results/association_results.csv`.
5. **Reports**: `reports/summary.json`, `reports/figures/`, `reports/data_completeness.csv`.

## Schema Constraints

- **Uniqueness**: `(subject_id, parcel_id)` must be unique in `ParcelTimeSeries`.
- **Completeness**: `EntropyMetric` must exist for all 360 parcels per included subject (SC-005).
- **Range**: `p_value` and `adjusted_p_value` must be in [0, 1].
- **Integrity**: `subject_id` in `AssociationResult` must exist in `Subject` (implied by aggregation).