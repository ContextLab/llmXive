# API Reference: Dark Matter Halo Shape Analysis Pipeline

## Module: `utils.config`
**Purpose**: Centralized configuration management and path resolution.

### Functions
- `load_config()`: Loads YAML configuration from `config.yaml`.
- `get_project_root()`: Returns the absolute path to the project root.
- `get_data_raw_path()`: Path to `data/raw/`.
- `get_data_processed_path()`: Path to `data/processed/`.
- `get_figures_path()`: Path to `figures/`.
- `get_millennium_path()`: Path to Millennium-II data if available.
- `get_output_path()`: Generic output directory.

## Module: `utils.logging`
**Purpose**: Pipeline tracking and structured logging.

### Functions
- `get_pipeline_logger()`: Returns a configured logger instance.
- `log_pipeline_start()`: Logs initialization details.
- `log_pipeline_end()`: Logs completion status and duration.
- `log_error()`: Logs error details with stack trace.
- `log_metric()`: Logs performance metrics (e.g., RAM usage, time).
- `log_chunk_info()`: Logs processing progress for current chunk.

## Module: `ingestion.tng_loader`
**Purpose**: Fetches TNG-100 simulation data via the public API.

### Functions
- `fetch_halos_list()`: Retrieves the list of haloes for a snapshot.
- `get_halo_files_for_snapshot()`: Maps haloes to specific HDF5 files.
- `download_file()`: Downloads a specific file with checksum verification.
- `fetch_tng_halo_data()`: High-level fetcher returning halo data structures.

## Module: `processing.inertia_tensor`
**Purpose**: Computes the reduced inertia tensor and eigen-decomposition.

### Functions
- `compute_reduced_inertia_tensor(particles)`: Calculates the tensor $I_{ij}$.
- `compute_eigenvalues_and_eigenvectors(tensor)`: Returns sorted eigenvalues/vectors.
- `compute_shape_from_inertia(eigenvalues)`: Derives axial ratios from eigenvalues.

## Module: `processing.shape_metrics`
**Purpose**: Derives shape descriptors and validates haloes.

### Functions
- `compute_axial_ratios(eigenvalues)`: Returns $(b/a, c/a)$.
- `compute_triaxiality(eigenvalues)`: Returns $T$.
- `filter_halo_by_particle_count(halo, min_count=10000)`: Filters invalid haloes.
- `bin_halo_by_shape(shape_metrics)`: Assigns prolate/triaxial/spherical bins.

## Module: `analysis.stats`
**Purpose**: Statistical testing and mass-matching algorithms.

### Functions
- `nearest_neighbor_matching(df, key, tolerance)`: Matches haloes by mass.
- `kruskal_wallis_test(groups)`: Non-parametric ANOVA.
- `mann_whitney_u_test(group1, group2)`: Pairwise comparison.
- `apply_bonferroni_correction(p_values, alpha)`: Corrects for multiple testing.
- `linear_regression_with_mass_control(df, shape_col, mass_col)`: Regression with covariate.

## Module: `processing.alignment`
**Purpose**: Computes orientation misalignment angles.

### Functions
- `compute_spin_vector(particles)`: Calculates specific angular momentum.
- `compute_major_axis_from_inertia(tensor)`: Extracts primary axis direction.
- `compute_misalignment_angle(vec1, vec2)`: Returns angle in degrees.
- `align_halo_galaxy_pairs(halo_data, galaxy_data)`: Matches pairs and computes angles.

## Module: `analysis.generate_statistical_results`
**Purpose**: Orchestrates the generation of the final statistical CSV.

### Functions
- `add_associational_only_flag(df)`: Adds the `associational_only=true` column.
- `main()`: Entry point for the statistical results generation script.
