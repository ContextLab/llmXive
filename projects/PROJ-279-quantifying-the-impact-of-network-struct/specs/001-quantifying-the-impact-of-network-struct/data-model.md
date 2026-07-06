# Data Model: Quantifying the Impact of Network Structure on Heat Transport in Amorphous Silicon

## Entities & Relationships

### AtomicConfiguration
Represents a single snapshot of the a-Si system.
- **Attributes**:
    - `config_id`: Unique identifier (string).
    - `source_url`: URL of the original trajectory (string).
    - `atom_count`: Number of atoms in the system (integer).
    - `thermal_conductivity`: Target value (float, W/m·K). **Optional**: May be null if Structure-Only Mode.
    - `source_type`: "Experimental" or "Simulation" (string).
    - `system_size_converged`: Boolean (true if atom_count >= 1000 or experimental).
    - `coordinates`: List of (x, y, z) floats.
    - `elements`: List of element symbols (e.g., "Si").
    - `distinct_ensemble_flag`: Boolean (true if k/VDOS derived from distinct ensemble).

### TopologicalDescriptor
Derived metrics from the atomic graph.
- **Attributes**:
    - `config_id`: Foreign key to `AtomicConfiguration`.
    - `cutoff_radius`: The radius used for graph construction (float).
    - `avg_degree`: Average number of bonds per atom (float).
    - `ring_distribution`: Dictionary mapping ring size (int) to count (int).
    - `q6_order_parameter`: Steinhardt Q6 value (float).
    - `clustering_coefficient`: Average clustering coefficient (float).
    - `num_components`: Number of disconnected graph components (integer).
    - `local_density`: Atomic density (float, atoms/Å³) - **Covariate**.
    - `mean_coordination`: Average coordination number (float) - **Covariate**.

### VibrationalDescriptor
Derived metrics from vibrational analysis. **Conditional Entity**:
- **Attributes**:
    - `config_id`: Foreign key to `AtomicConfiguration`.
    - `vdos_peak_frequency`: Dominant frequency in VDOS (float, THz).
    - `participation_ratio`: Average participation ratio (float).
    - `low_freq_weight`: Integral of VDOS below 2 THz (float).
- **Constraint**: This entity is **omitted** from the feature matrix if pre-calculated VDOS is not present in the dataset. It is **not** populated with nulls.

### RegressionResult
Output of the statistical modeling phase.
- **Attributes**:
    - `model_type`: "Ridge" or "RandomForest" (string).
    - `r2_score`: Cross-validated R² (float).
    - `std_dev`: Standard deviation of R² across folds (float).
    - `top_predictor`: Name of the most important feature (string).
    - `top_predictor_pvalue`: P-value for the top predictor (float).
    - `feature_importances`: Dictionary of feature name -> importance score.
    - `correlation_r`: Pearson r between top predictor and target (float).
    - `correlation_p`: P-value for Pearson r (float).
    - `stability_score`: Mean rank stability of top features across bootstraps (float).
    - `partial_corr_r`: Pearson r between top predictor and target **controlling for density** (float).

## Data Flow

1.  **Ingestion**: `AtomicConfiguration` raw data is downloaded and checksummed.
2.  **Transformation**:
    - `AtomicConfiguration` + `cutoff_radius` -> `TopologicalDescriptor` (via graph construction).
    - `AtomicConfiguration` -> `VibrationalDescriptor` (via **pre-calculated data only**). If missing, entity is skipped.
    - `TopologicalDescriptor` + `AtomicConfiguration` -> `Covariates` (Local Density, Mean Coordination).
3.  **Aggregation**: Descriptors and Covariates are merged into a single feature matrix.
4.  **Dimensionality Reduction**: PCA or Lasso applied if N is small.
5.  **Modeling**: Feature matrix + `thermal_conductivity` -> `RegressionResult`.
6.  **Output**: Results are serialized to CSV/JSON and used for visualization.

## Constraints & Validations

- **AtomicConfiguration**: `atom_count` must be > 0. `thermal_conductivity` must be > 0 if present.
- **TopologicalDescriptor**: `ring_distribution` keys must be integers $\ge 3$.
- **VibrationalDescriptor**: **Omitted** if data is missing. Not populated with nulls.
- **RegressionResult**: `r2_score` can be negative (worse than mean) but must be reported. `pvalue` must be in [0, 1].
- **Data Hygiene**: All raw files must be stored in `data/raw/` with checksums. Processed files in `data/processed/`.
- **Independence**: If `distinct_ensemble_flag` is false, samples are excluded from regression.