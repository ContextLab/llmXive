# Data Model: Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records

## Overview

This document defines the data structures, schemas, and relationships used in the pipeline. The data flow is: `Raw Images` -> `Visual Features` -> `Weather Context` -> `Unified Table` -> `Model Outputs`.

## Entities

### 1. ImageRecord
Represents a single leaf image and its extracted visual features.
*   **Primary Key**: `image_id` (derived from filename/path).
*   **Attributes**:
    *   `file_path`: String (relative path to raw image).
    *   `disease_label`: String (class label from PlantVillage).
    *   `lesion_area_ratio`: Float (0.0 - 1.0).
    *   `necrosis_color_index`: Float.
    *   `texture_entropy`: Float.
    *   `location_lat`: Float (Nullable).
    *   `location_lon`: Float (Nullable).
    *   `capture_date`: Date (YYYY-MM-DD).
    *   `processing_status`: String (e.g., "success", "missing_loc", "no_lesion").

### 2. WeatherContext
Represents the aggregated meteorological state for a location and 7-day window.
*   **Primary Key**: `weather_id` (linked to `image_id`).
*   **Attributes**:
    *   `image_id`: String (FK).
    *   `mean_temp_7d`: Float (°C).
    *   `mean_humidity_7d`: Float (%).
    *   `total_precip_7d`: Float (mm).
    *   `temp_std_7d`: Float (variability).
    *   `humidity_std_7d`: Float.
    *   `data_source`: String ("open-meteo", "noaa-ghcn-lightweight").

### 3. UnifiedAnalysisTable
The joined dataset used for modeling.
*   **Attributes**: All fields from `ImageRecord` + `WeatherContext`.
*   **Derived Fields**:
    *   `visual_severity`: Float (Target variable, e.g., `lesion_area_ratio`).
    *   `baseline_pred`: Float (Prediction from Baseline RF using OOF).
    *   `raw_residual`: Float (`visual_severity` - `baseline_pred`).
    *   `calibrated_residual`: Float (Raw residual corrected for systematic bias via isotonic regression/mean-centering). **This is the target for the Augmented Model.**

### 4. ModelFit
Represents the result of a regression training run.
*   **Attributes**:
    *   `model_id`: String (e.g., "baseline_rf", "augmented_rf").
    *   `r2_score`: Float.
    *   `mae`: Float.
    *   `feature_importance`: Dict (JSON).
    *   `permutation_p_value`: Float (for augmented model).
    *   `null_distribution_mean`: Float (Mean R² of shuffled weather models).
    *   `timestamp`: Datetime.

## Data Flow Diagram

```mermaid
graph TD
    A[PlantVillage ZIP] -->|Extract| B(ImageRecord)
    B -->|Filter Missing Loc| C(Valid ImageRecord)
    C -->|Open-Meteo API / NOAA Fallback| D[WeatherContext]
    C -->|OpenCV| E[Visual Features]
    D -->|Join| F[UnifiedAnalysisTable]
    E -->|Join| F
    F -->|Split| G[Train Set]
    F -->|Split| H[Test Set]
    G -->|K-Fold Baseline| I[Baseline Model (OOF)]
    I -->|Predict OOF| J[Raw Residuals]
    J -->|Calibration| K[Calibrated Residuals]
    K -->|Train Augmented| L[Augmented Model]
    L -->|Permutation Test (Shuffle X)| M[Results]
```

## Data Quality Rules

1.  **Completeness**: Records with missing `location_lat`/`lon` are excluded from the analysis set (logged as warnings).
2.  **Consistency**: `lesion_area_ratio` must be between 0.0 and 1.0.
3.  **Weather Failure**: If Open-Meteo fails for a specific coordinate, **use the lightweight NOAA GHCN-Daily fallback** (pre-processed station CSV). If both fail, **exclude the record** with a log warning.
4.  **Outliers**: Images with `lesion_area_ratio` = 0.0 but `disease_label` != "healthy" are flagged as "no_lesion" and excluded from the primary analysis (data quality issue).
5.  **Calibration**: Raw residuals must be calibrated (bias-corrected) before use as the target for the Augmented Model.

## Storage Format

*   **Raw Images**: Stored in `data/raw/` as original ZIP/extracted files.
*   **Intermediate Tables**: Parquet format (`data/interim/*.parquet`) for efficient I/O.
*   **Final Dataset**: CSV (`data/processed/unified_analysis.csv`) for portability.
*   **Models**: Pickle files (`artifacts/models/*.pkl`).
*   **Results**: JSON (`artifacts/results.json`).