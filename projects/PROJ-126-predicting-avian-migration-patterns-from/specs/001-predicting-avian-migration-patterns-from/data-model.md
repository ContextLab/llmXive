# Data Model: Predicting Avian Migration Patterns

## Entity-Relationship Overview

The data model revolves around the `GridCellObservation` entity, which aggregates raw eBird checklists and environmental data into a unified spatiotemporal unit. This entity strictly conforms to the `grid_cell_observation.schema.yaml` contract.

### Core Entities

1.  **RawChecklist**
    -   **Source**: eBird Basic Dataset (EBD).
    -   **Description**: Individual observation record.
    -   **Attributes**: `checklist_id`, `date`, `latitude`, `longitude`, `species_code`, `obs_count`, `duration_min`, `distance_km`, `num_observers`.

2.  **GridCellObservation**
    -   **Source**: Aggregated `RawChecklist` + Environmental Data.
    -   **Description**: A 0.5° x 0.5° grid cell for a specific week.
    -   **Attributes**:
        -   `grid_cell_id` (string: "{lat}_{lon}")
        -   `year` (int)
        -   `week_number` (int)
        -   `total_obs_count` (int)
        -   `first_arrival_week` (int, nullable)
        -   `lst_lag_1` (float) - Land Surface Temperature 1 week prior
        -   `lst_lag_2` (float)
        -   `lst_lag_3` (float)
        -   `lst_lag_4` (float)
        -   `evi_lag_1` (float) - Enhanced Vegetation Index 1 week prior
        -   `evi_lag_2` (float)
        -   `evi_lag_3` (float)
        -   `evi_lag_4` (float)
        -   `data_quality_flag` (enum: "valid", "insufficient_data", "missing_env", "low_effort")
        -   `threshold_used` (int: 3, 5, or 10)

3.  **ModelPrediction**
    -   **Source**: XGBoost Model Output.
    -   **Description**: Predicted arrival date and residuals.
    -   **Attributes**:
        -   `grid_cell_id`
        -   `year`
        -   `week_number`
        -   `predicted_arrival_day_of_year` (int)
        -   `actual_arrival_day_of_year` (int)
        -   `residual` (float)
        -   `shap_lst` (float)
        -   `shap_evi` (float)

4.  **ModelPerformanceMetric**
    -   **Source**: Statistical Tests.
    -   **Description**: Aggregated metrics for model evaluation.
    -   **Attributes**:
        -   `model_name` (string)
        -   `metric_type` (string: "RMSE", "MAE", "Pearson_R")
        -   `value` (float)
        -   `p_value_dm` (float, nullable)
        -   `confidence_interval_lower` (float)
        -   `confidence_interval_upper` (float)

## Data Flow

1.  **Ingestion**: `RawChecklist` data is downloaded from EBD.
2.  **Filtering**: Records are filtered for `complete_checklist` criteria.
3.  **Aggregation**: Filtered records are binned into `GridCellObservation` (0.5° grid, weekly).
4.  **Enrichment**: Environmental data (Temp, EVI) is interpolated to the grid cell. Lag features are created.
5.  **Derivation**: `first_arrival_week` is calculated based on cumulative counts.
6.  **Modeling**: `GridCellObservation` (training split) -> `ModelPrediction`.
7.  **Evaluation**: `ModelPrediction` -> `ModelPerformanceMetric`.

## Data Constraints & Validations

-   **Grid Resolution**: Fixed at 0.5°.
-   **Temporal Range**: 2015-2023.
-   **Species**: *Setophaga ruticilla*.
-   **Minimum Observations**: Grid cells with <10 total annual observations are excluded from modeling.
-   **Missing Data**: If environmental data is missing for a grid cell (e.g., no MODIS data within 10km), the `data_quality_flag` is set to "missing_env", and the row is excluded from training but may be included in sensitivity analysis if the target is derivable.
-   **Low Effort**: Grid cells with low observer effort (e.g., short duration, few observers) are flagged as "low_effort" and excluded from modeling to control for bias.
-   **Schema Compliance**: All output data from `preprocessing.py` MUST conform to `grid_cell_observation.schema.yaml`.
