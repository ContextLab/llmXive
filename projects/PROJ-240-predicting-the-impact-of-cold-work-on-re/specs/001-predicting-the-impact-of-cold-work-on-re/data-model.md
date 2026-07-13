# Data Model: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

## 1. Overview

This document defines the data structures, schemas, and relationships used in the project. The model supports the ingestion, validation, training, and evaluation phases defined in `plan.md`.

## 2. Entity Definitions

### 2.1 ExperimentalRecord
Represents a single experimental observation.
- **Attributes**:
  - `record_id`: Unique identifier (UUID).
  - `cold_work_pct`: Float, 0-100.
  - `annealing_temp_c`: Float, >0.
  - `time_to_peak_min`: Float, >0.
  - `composition`: Nested object (Mg, Si, Cu, Mn).
  - `alloy_series`: String (Derived, metadata only, not used in model).
  - `source`: String (Dataset source).
  - `validation_status`: Enum (Valid, Invalid, Warning).

### 2.2 AlloyComposition
Chemical makeup of the sample.
- **Attributes**:
  - `mg_wt`: Weight percent of Magnesium.
  - `si_wt`: Weight percent of Silicon.
  - `cu_wt`: Weight percent of Copper.
  - `mn_wt`: Weight percent of Manganese.
  - `total_solute`: Float (Sum of above, derived).

### 2.3 KineticModel
The trained regression model.
- **Attributes**:
  - `model_type`: String (e.g., "RandomForest").
  - `hyperparameters`: Dict.
  - `feature_importance`: Dict (Feature name -> Importance score).
  - `vif_scores`: Dict (Feature name -> VIF).
  - `performance_metrics`: Dict (R², MAE).

## 3. Data Flow

1.  **Raw Input**: CSV/Parquet file → `data/raw/`.
2.  **Validation**: `ingest.py` validates bounds and types → `data/processed/validated.csv`.
3.  **Split**: `train.csv`, `test.csv` (80/20).
4.  **Model Input**: `train.csv` → `code/train.py` → `artifacts/models/model.pkl`.
5.  **Output**: Predictions and metrics → `artifacts/reports/metrics.json`.

## 4. Constraints & Rules

- **Physical Bounds**:
  - `cold_work_pct`: [0.0, 100.0].
  - `time_to_peak_min`: (>0.0).
  - `composition` values: [0.0, 100.0] and sum ≤ 100.
- **Collinearity Rule**: Do not include `total_solute` and individual elements (`mg_wt`, `si_wt`, etc.) in the same feature vector.
- **Unit Standardization**: All time units converted to minutes. All temperatures to Celsius.
