# Data Model: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

## Entities

### 1. AlloySample
Represents a single processed aluminum alloy entry.
*   `id`: Unique identifier (string).
*   `source`: Original dataset source (string).
*   `source_study`: Identifier for the specific study or batch (string, nullable). Used for stratified splitting to prevent leakage.
*   `temperature`: Rolling temperature in Celsius (float).
*   `grain_size`: Measured grain size in micrometers (float).
*   `alloy_series`: Series classification (e.g., "6xxx", "5xxx") (string, nullable).
*   `process_type`: Classification of the manufacturing process (e.g., "Rolling", "Casting", "SPD") (string). **Required** for filtering.
*   `composition`: Dictionary of element:weight_percent (object).
    *   Keys: "Mg", "Si", "Cu", "Zn", "Mn", etc.
    *   Values: Float (0.0 - 100.0).

### 2. InteractionFeature
Derived features created during preprocessing.
*   `feature_name`: String (e.g., "temp_mg_interaction").
*   `base_variable_1`: String (e.g., "temperature").
*   `base_variable_2`: String (e.g., "Mg").
*   `value`: Float.

### 3. ModelArtifact
Output of the training process.
*   `model_type`: String ("LinearRegression", "RandomForest").
*   `hyperparameters`: Object (e.g., `{"n_estimators": 100, "max_depth": 8}`).
*   `metrics`: Object (`{"r2": float, "mae": float}`).
*   `feature_importances`: Dictionary (feature_name: importance_score).
*   `collinearity_report`: Object (see below).

### 4. CollinearityReport
Diagnostic output for predictor relationships.
*   `pairs`: List of objects.
    *   `variables`: List of two strings.
    *   `correlation`: Float.
    *   `classification`: String ("ChemicalCoupling", "Spurious", "None").
    *   `interpretation`: String (e.g., "Report as joint effect").

### 5. ConfounderReport
Diagnostic output for unmeasured confounding.
*   `status`: String ("Computed", "N/A").
*   `e_value`: Float (if computed). The minimum strength of association an unmeasured confounder must have with both the treatment and outcome to explain away the observed effect.
*   `r2_without_proxies`: Float (if computed).
*   `r2_with_proxies`: Float (if computed).

## Data Flow
1.  **Ingestion**: Raw CSV from source -> `AlloySample` (filtered for nulls and `process_type == "Rolling"`).
2.  **Preprocessing**: `AlloySample` -> `InteractionFeature` -> Normalized Feature Matrix.
3.  **Splitting**: Split by `source_study` (if available) to prevent leakage.
4.  **Training**: Feature Matrix -> `ModelArtifact` (Conditional on N >= 100 for RF).
5.  **Diagnostics**: Feature Matrix -> `CollinearityReport`; Model -> `ConfounderReport`.
6.  **Output**: `ModelArtifact` + `CollinearityReport` + `ConfounderReport` -> JSON/CSV.