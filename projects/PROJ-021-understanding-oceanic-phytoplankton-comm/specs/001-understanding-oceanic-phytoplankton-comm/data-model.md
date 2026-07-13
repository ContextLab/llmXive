# Data Model: Understanding Oceanic Phytoplankton Communities

## Key Entities

### 1. PhytoplanktonSample
Represents a single aligned measurement point from the SeaBASS dataset.
*   **Attributes**:
    *   `sample_id`: Unique identifier (UUID).
    *   `latitude`: float (degrees).
    *   `longitude`: float (degrees).
    *   `timestamp`: ISO8601 string (YYYY-MM).
    *   `chlorophyll_a`: float (mg/m³).
    *   `temperature`: float (°C).
    *   `salinity`: float (PSU).
    *   `nutrients`: dict (e.g., `{"nitrate": float, "phosphate": float}`).
    *   `basin`: string (e.g., "North Atlantic").
    *   `quality_flag`: string (e.g., "valid", "interpolated", "excluded").
    *   `image_patch`: bytes or path to 32x32 pixel array (derived from MODIS).

### 2. OceanBasin
Geographic region for stratification.
*   **Attributes**:
    *   `basin_id`: string (e.g., "NA", "SP", "IO").
    *   `name`: string.
    *   `bounds`: dict (`{"min_lat", "max_lat", "min_lon", "max_lon"}`).

### 3. ModelPerformance
Evaluation results.
*   **Attributes**:
    *   `model_type`: string ("RandomForest", "VLM").
    *   `dataset_split`: string ("train", "val", "test").
    *   `rmse`: float.
    *   `r_squared`: float.
    *   `mae`: float.
    *   `basin`: string (or "global").
    *   `timestamp`: ISO8601.

## Data Flow

1.  **Ingestion**: SeaBASS dataset loaded via `datasets` library.
2.  **Preprocessing**:
    *   Spatial alignment to station grid.
    *   Temporal alignment to monthly composites.
    *   Missing value handling: Linear interpolation for gaps ≤ 2 months; exclusion for larger gaps.
    *   Quality filtering: Exclude "cloud" or "high aerosol" flags.
3.  **Training**:
    *   Input: `PhytoplanktonSample` table (including image patches).
    *   Output: Trained model artifacts + `ModelPerformance` records.
4.  **Evaluation**:
    *   Input: Test set + Trained models.
    *   Output: Feature importance scores, spatial maps.

## Data Constraints

*   **Memory**: All intermediate DataFrames must fit in available RAM.
*   **Missingness**: Final aligned dataset must have ≤ 5% missing values (SC-004).
*   **Integrity**: No in-place modification of raw data; all derivations are new files.