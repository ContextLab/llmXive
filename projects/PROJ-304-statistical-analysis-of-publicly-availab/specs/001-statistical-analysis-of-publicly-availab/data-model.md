# Data Model: Statistical Analysis of Urban Noise Pollution

## 1. Entity Relationship Overview
The data model is designed to support the ingestion, harmonization, and modeling of urban noise data. It consists of a primary **SpatialGridCell** entity that aggregates noise metrics and links to covariates. The model now includes a **temporal dimension** to satisfy FR-002 (Daily Aggregation).

### Key Entities
1.  **SpatialGridCell**: The atomic unit of analysis (200m x 200m) for a specific day.
2.  **ModelFit**: The output of a regression model (OLS, Lag, Error).
3.  **CrossValidationFold**: The result of a single spatial CV iteration.

## 2. Data Schema Details

### 2.1 SpatialGridCell (Processed Dataset)
This entity represents a single row in the harmonized GeoDataFrame. **Note**: To satisfy FR-002, the unit of analysis includes a date. Aggregation (mean, median, p95) is performed *per day* per cell.

| Field Name | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `grid_id` | Integer | Unique identifier for the grid cell. | Primary Key (Composite with `date`) |
| `date` | Date | The date of the observation. | Required (FR-002) |
| `geometry` | WKB/WKT | 200m x 200m polygon geometry. | CRS: EPSG:4326 (WGS84) |
| `noise_mean_db` | Float64 | Arithmetic mean of noise readings **for that day**. | Filtered (IQR) |
| `noise_median_db` | Float64 | Median of noise readings **for that day**. | Filtered (IQR) |
| `noise_p95_db` | Float64 | 95th percentile of noise readings **for that day**. | Filtered (IQR) |
| `traffic_volume` | Float64 | Aggregated traffic count **for that day**. | No nulls (imputed or excluded) |
| `land_use_code` | String | Categorical land use (e.g., "Residential"). | No nulls |
| `pop_density` | Float64 | Population per km². | No nulls |
| `missing_flag` | Boolean | True if any covariate was missing and imputed. | Default: False |

### 2.2 ModelFit (Output Artifact)
This entity represents the statistical summary of a fitted model.

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `model_type` | String | "OLS", "Spatial_Lag", "Spatial_Error" |
| `coefficients` | Dict | Map of predictor -> coefficient value |
| `std_errors` | Dict | Map of predictor -> **Robust** standard error (Cluster/Conley) |
| `p_values` | Dict | Map of predictor -> p-value (BH-corrected) |
| `r_squared` | Float | Coefficient of determination |
| `aic` | Float | Akaike Information Criterion |
| `moran_i_residual` | Float | Moran's I of residuals |
| `moran_i_pval` | Float | P-value for Moran's I |
| `spatial_param` | Float | λ (Lag) or ρ (Error) coefficient |

### 2.3 CrossValidationFold
This entity stores metrics for a single fold of the spatial CV.

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `fold_id` | Integer | Fold index (0-4) |
| `model_type` | String | "OLS", "Spatial_Lag", "Spatial_Error" |
| `rmse` | Float | Root Mean Squared Error on test set |
| `r_squared` | Float | R² on test set |
| `train_size` | Integer | Number of training samples |
| `test_size` | Integer | Number of test samples |

## 3. Data Flow
1.  **Ingestion**: Raw CSV/GeoJSON -> `raw/` (Checksummed).
2.  **Daily Aggregation**: `raw/` -> `code/preprocessing.py` -> Aggregate readings **per day** per cell (group by `grid_id` and `date`).
3.  **Harmonization**: `code/ingestion.py` -> `processed/harmonized.parquet` (SpatialGridCell with `date`).
4.  **Modeling**: `harmonized.parquet` -> `code/models.py` (with Robust SEs) -> `processed/model_results.json` (ModelFit).
5.  **Validation**: `harmonized.parquet` + `model_results` -> `code/validation.py` -> `processed/cv_results.json` (CrossValidationFold).

## 4. Data Hygiene Rules
*   **No Nulls**: Predictor columns (`traffic_volume`, `land_use_code`, `pop_density`) must not contain nulls in the final modeling dataset. Rows with missing covariates are excluded and logged.
*   **Outlier Removal**: `noise_db` values outside 1.5 * IQR are capped (not removed) to preserve sample size while reducing extreme outlier influence.
*   **CRS**: All geometries must be reprojected to EPSG:4326 (WGS84) before grid assignment.
*   **Temporal Integrity**: Aggregation is strictly **per day**. If a cell has no readings for a day, that day-cell combination is excluded.
