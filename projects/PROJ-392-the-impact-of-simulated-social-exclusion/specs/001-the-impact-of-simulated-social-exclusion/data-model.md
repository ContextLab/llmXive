# Data Model: 001-social-exclusion-reward-neural

## Entity Definitions

### Participant
- **id**: String (unique identifier, e.g., "sub-001")
- **group**: Enum ["excluded", "included"]
- **behavioral_labels**: Dictionary (optional, e.g., `{"distress_score": 3.5}`)
- **motion_params**: Dictionary (optional, e.g., `{"trans_x": 0.5, "rot_z": 0.2}`)
- **validation_status**: Enum ["validated", "proxy", "missing"] (Status of behavioral manipulation check)

### ROI
- **name**: String (e.g., "ventral_striatum", "orbitofrontal_cortex")
- **atlas_source**: String (e.g., "AAL", "Harvard-Oxford")
- **mni_coordinates**: List[float] (x, y, z in mm)
- **radius_mm**: Float (e.g., 10.0)

### Analysis Result
- **roi_name**: String
- **event_type**: Enum ["anticipation", "receipt"]
- **group_comparison**: String (e.g., "excluded_vs_included")
- **t_statistic**: Float
- **p_value_fwe**: Float
- **cohen_d**: Float
- **cluster_coordinates**: List[float] (x, y, z)
- **significance**: Boolean
- **framing_check**: Enum ["pass", "fail"] (Result of causal verb scan)

### Sensitivity Result
- **smoothing_mm**: Float
- **roi_radius_mm**: Float
- **beta_difference**: Float
- **p_value**: Float
- **consistent_with_primary**: Boolean
- **effect_size_stability**: Float (Ratio of current d to primary d)

### Preprocessing Metric
- **participant_id**: String
- **status**: Enum ["success", "failed", "skipped"]
- **memory_peak_mb**: Float
- **resolution_mm**: Float (e.g., 3.0 or 4.0)

## Data Flow

1. **Raw Data**: `data/raw-fmri/` (BIDS format: NIfTI, JSON, TSV).
2. **Processed Data**: `data/processed-fmri/` (Preprocessed NIfTI, GLM estimates).
3. **Extracted Data**: `data/extracted/` (CSV/Parquet: Participant ID, Group, ROI, Beta Value).
4. **Behavioral Data**: `data/behavioral/` (Checksummed condition labels, distress scores).
5. **Synthetic Data**: `data/synthetic/` (Optional: Simulated reward task data).
6. **Analysis Output**: `data/results/` (JSON/Parquet: T-statistics, p-values, effect sizes).
7. **Visualizations**: `docs/paper/figures/` (PNG/SVG: Bar plots, SPM overlays).

## Storage Constraints

- **Raw Data**: ≤14 GB (compressed).
- **Processed Data**: ≤10 GB (preprocessed NIfTI + GLM estimates).
- **Total Disk**: ≤14 GB (GitHub Actions limit).
- **Memory**: ≤7 GB (chunked processing, downsampling if >6GB).
