# Data Model: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

## Entity-Relationship Overview

The data model is designed to support the ingestion, processing, and prediction phases of the pipeline. It centers on the `ProcessingRecord` entity, which links processing conditions to texture outcomes.

### Core Entities

1.  **ProcessingRecord**
    *   **Description**: A single observation of a rolling process experiment.
    *   **Attributes**:
        *   `id`: Unique identifier (UUID).
        *   `alloy_id`: String (e.g., "Al-6061", "Cu-110").
        *   `rolling_speed`: Float (m/s).
        *   `temperature`: Float (°C).
        *   `reduction_ratio`: Float (%).
        *   `composition_vector`: List[Float] (Optional, e.g., [0.0, 0.0, 0.0] for pure metal).
        *   `grain_size`: Float (µm, Optional).
        *   `history`: String (Optional, e.g., "annealed", "cold-rolled").

2.  **TextureDescriptor**
    *   **Description**: Quantitative texture metrics derived from the record.
    *   **Attributes**:
        *   `record_id`: Reference to `ProcessingRecord`.
        *   `odf_100`: Float (MRD).
        *   `odf_110`: Float (MRD).
        *   `odf_111`: Float (MRD).
        *   `source`: Enum ("real", "synthetic").

3.  **ModelArtifact**
    *   **Description**: Serialized model and metadata.
    *   **Attributes**:
        *   `model_id`: String.
        *   `hyperparameters`: Dict.
        *   `metrics`: Dict (R², MAE, RMSE per coefficient).
        *   `feature_importance`: Dict.
        *   `created_at`: Timestamp.

## Data Flow

1.  **Ingestion**: Raw CSV/JSON -> `ProcessingRecord` (raw).
2.  **Preprocessing**:
    *   Unit standardization.
    *   Missing value handling (Median Imputation).
    *   Outlier removal (3σ).
    *   Feature engineering (Zener-Hollomon, Strain Rate).
    *   Result: `ProcessedRecord` (cleaned).
3.  **Training**: `ProcessedRecord` (Train) -> `ModelArtifact`.
4.  **Prediction**: `ProcessedRecord` (New) + `ModelArtifact` -> `PredictionResult`.

## Schema Constraints

-   **Temperature**: Must be > -273.15°C.
-   **Reduction Ratio**: Must be between 0.0 and 100.0.
-   **ODF Values**: Must be >= 0.0 (MRD cannot be negative).
-   **Alloy Family**: Must be one of the predefined set (Al, Cu, Steel, etc.) or "Unknown".

## File Formats

-   **Input**: CSV, JSON, Parquet.
-   **Intermediate**: Parquet (for efficient I/O).
-   **Output**: CSV (predictions), JSON (reports), Pickle (model).
