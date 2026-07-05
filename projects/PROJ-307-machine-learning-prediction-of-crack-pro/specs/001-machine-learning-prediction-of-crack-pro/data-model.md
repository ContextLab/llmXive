# Data Model: Machine Learning Prediction of Crack Propagation Rates in Metals

## Entity Relationship Overview

The data model centers on the `FatigueRecord` entity, which represents a single experimental observation. This entity is linked to derived entities for `ModelPerformance` and `RegimeAnalysis`.

### Core Entities

1.  **FatigueRecord**
    *   **Description**: A single row of experimental data containing crack growth metrics and material properties.
    *   **Primary Keys**: `record_id` (generated unique identifier).
    *   **Attributes**:
        *   `da_dN`: Float. Crack growth rate (m/cycle).
        *   `delta_K`: Float. Stress intensity factor range (MPa√m).
        *   `log_da_dN`: Float. $\log_{10}(da/dN)$.
        *   `log_delta_K`: Float. $\log_{10}(\Delta K)$.
        *   `composition`: Dictionary (JSON). Key-value pairs of element: weight_percent (e.g., `{"C": 0.2, "Mn": 1.5}`).
        *   `heat_treatment`: String. Categorical description (e.g., "T6", "Annealed", "Unknown").
        *   `alloy_family`: String. Grouping category (e.g., "Aluminum", "Steel", "Titanium").
        *   `source`: String. Dataset source (e.g., "FCGEC").

2.  **ModelPerformance**
    *   **Description**: Aggregated metrics for a specific model configuration and fold.
    *   **Attributes**:
        *   `model_id`: String. Unique identifier for the model run.
        *   `model_type`: String. "Baseline", "RF", "XGBoost".
        *   `fold`: Integer. Cross-validation fold number (0-4).
        *   `r2_score`: Float. Coefficient of determination.
        *   `rmse`: Float. Root Mean Squared Error.
        *   `p_value`: Float. Significance of the model vs null (for baseline).

3.  **RegimeAnalysis**
    *   **Description**: Metrics specific to a $\Delta K$ region.
    *   **Attributes**:
        *   `regime_id`: String. "Low", "Mid", "High".
        *   `log_delta_K_min`: Float. Lower bound of the regime.
        *   `log_delta_K_max`: Float. Upper bound of the regime.
        *   `local_r2`: Float. $R^2$ within this regime.
        *   `dominant_features`: List. Top 3 features by importance in this regime.
        *   `stability_score`: Float. Consistency metric from sensitivity analysis.

## Data Flow

1.  **Ingestion**: Raw CSV -> `FatigueRecord` (raw attributes).
2.  **Preprocessing**: `FatigueRecord` -> `ProcessedRecord` (log-transformed, encoded, imputed).
3.  **Modeling**: `ProcessedRecord` -> `ModelPerformance` (metrics).
4.  **Analysis**: `ProcessedRecord` + `ModelPerformance` -> `RegimeAnalysis`.

## Storage Schema

- **Raw Data**: `data/raw/fcg_train.csv` (immutable, checksummed).
- **Processed Data**: `data/processed/processed_fcg.parquet` (Parquet format for efficiency).
- **Models**: `models/` (pickle files with version hashes).
- **Results**: `results/` (JSON/CSV for metrics and regime maps).
