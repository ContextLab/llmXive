# Data Model: Predicting Plant Root Architecture from Soil Nutrient Availability

## Entity Definitions

### RootPhenotypeRecord
Represents a single observation of root architecture.
- `species` (string): Scientific name of the plant.
- `root_length` (float): Total root length (cm).
- `branching_density` (float): Number of branches per unit length.
- `surface_area` (float): Total root surface area (cm²).
- `geographic_location` (string): Location code or coordinates.
- `experimental_id` (string): Unique identifier for the experiment.
- `data_source_type` (string): 'observational' or 'experimental'.

### SoilNutrientRecord
Represents soil chemical properties (if available).
- `phosphorus_concentration` (float): mg/kg or ppm.
- `nitrogen_concentration` (float): mg/kg or ppm.
- `measurement_date` (date): Date of soil sampling.
- `depth` (float): Soil depth in cm.

### MergedDataset
The combined dataset.
- `species` (string)
- `root_length` (float, log-transformed)
- `branching_density` (float, log-transformed)
- `surface_area` (float, log-transformed)
- `phosphorus` (float, z-scored)
- `nitrogen` (float, z-scored)
- `sample_size_per_species` (int)
- `data_source_type` (string)

## Data Flow

1.  **Ingestion**: Raw files (TXT/CSV/Parquet) downloaded from verified sources.
2.  **Cleaning**:
    -   Filter `data_source_type == 'observational'`.
    -   Filter `n >= 20` per species.
    -   Impute missing values (KNN -> Mean).
3.  **Transformation**:
    -   `log_root = log(root + 1e-6)`
    -   `z_p = (P - mean(P)) / std(P)`
4.  **Storage**: Processed data saved as `data/processed/merged_dataset.parquet`.

## Schema Constraints
-   **Species**: Must not be null.
-   **Nutrients**: If missing in source, column is dropped (deviation logged).
-   **Outliers**: Values > 3 SD from mean (after log) are capped or flagged.
