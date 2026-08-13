# Data Model: Correlational Analysis of Climate‑Smart Agricultural Practices and Yield Stability Independent of Financial Access

## 1. Conceptual Model

The data model centers on the **Household** entity, which is linked to a **Satellite Pixel** via a spatial join. The model supports two primary analysis tables: one for the raw joined data and one for the aggregated village-level data (if needed).

### Entities

1.  **Household**: Represents a smallholder farming unit.
    - **Attributes**: `household_id`, `latitude`, `longitude`, `land_size`, `education_level`, `financial_access_flag`.
    - **Derived**: `CSA_Index`, `NDVI_CV`, `HFIAS`.

2.  **Satellite Pixel**: Represents a grid cell of Sentinel-2/Landsat data.
    - **Attributes**: `pixel_id`, `centroid_lat`, `centroid_lon`, `ndvi_time_series`.
    - **Derived**: `NDVI_CV` (calculated from NDVI).

3.  **Village** (Aggregation Unit):
    - **Attributes**: `village_id`, `mean_CSA_Index`, `mean_NDVI_CV`, `mean_HFIAS`, `n_households`.

## 2. Logical Data Flow

1.  **Ingest Survey Data**: Raw LSMS-ISA CSV/Parquet -> `raw_survey_data`.
2.  **Ingest Satellite Data**: Raw Sentinel-2 GeoTIFF/NetCDF -> `raw_satellite_data`.
3.  **Spatial Join**: `raw_survey_data` + `raw_satellite_data` -> `joined_data`.
    - *Logic*: Match `household` lat/lon to `pixel` centroid (with fuzzing).
4.  **Feature Engineering**: `joined_data` -> `analysis_dataset`.
    - *Logic*: Calculate `CSA_Index`, `NDVI_CV` (StdDev/Mean), `HFIAS`.
5.  **Aggregation (Optional)**: `analysis_dataset` -> `village_aggregated_data` (if N < 300).
6.  **Analysis**: `analysis_dataset` / `village_aggregated_data` -> `regression_results`.

## 3. Physical Data Model

### `data/raw/survey_data.csv`
- **Source**: LSMS-ISA (Malawi/Tanzania).
- **Format**: CSV/Parquet.
- **Checksum**: Recorded in `state/`.

### `data/raw/satellite_data.nc` (or `.tif`)
- **Source**: Sentinel-2/Landsat.
- **Format**: NetCDF/GeoTIFF.
- **Checksum**: Recorded in `state/`.

### `data/processed/analysis_dataset.csv`
- **Schema**: Defined in `contracts/dataset.schema.yaml`.
- **Columns**:
    - `household_id` (int)
    - `latitude` (float)
    - `longitude` (float)
    - `land_size` (float)
    - `education_level` (int)
    - `financial_access_flag` (int)
    - `CSA_Index` (float)
    - `NDVI_CV` (float)
    - `HFIAS` (float)
    - `cloud_cover` (float)
    - `village_id` (int, optional)

### `data/processed/regression_results.json`
- **Schema**: Defined in `contracts/output.schema.yaml`.
- **Content**: Coefficients, p-values, VIF scores, model diagnostics.

## 4. Data Constraints & Validation

- **Missing Data**: Records with missing `latitude`, `longitude`, or `NDVI_CV` are excluded and logged.
- **Outliers**: Extreme values in `land_size` or `HFIAS` are flagged but not removed unless they violate physical constraints (e.g., negative land size).
- **Spatial Fuzzing**: Coordinates are fuzzed to 0.1 degree resolution before joining to protect privacy.
- **Temporal Alignment**: Satellite data must correspond to the survey year's growing season.

## 5. Data Lineage

Every row in `analysis_dataset.csv` must trace back to:
1.  A specific row in `raw_survey_data`.
2.  A specific pixel in `raw_satellite_data`.
3.  The `src/data/processing/spatial_join.py` and `src/data/processing/feature_engineering.py` scripts.