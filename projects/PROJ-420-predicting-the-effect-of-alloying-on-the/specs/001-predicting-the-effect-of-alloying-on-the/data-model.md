# Data Model: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Data Flow Architecture

1.  **Raw Ingestion**: Download from HuggingFace `materials/alloy-elastic` -> `data/raw/al_alloy_raw.json`
2.  **Filtering & Normalization**: Remove non-monolithic, missing values, unit conversion -> `data/processed/alloy_cleaned.csv`
3.  **Transformation**: Apply ILR to composition -> `data/processed/alloy_features.csv`
4.  **Modeling**: Train/Validate (Repeated 5-Fold CV) -> `models/rf_model.pkl`
5.  **Metrics**: Compute CV-MAE (with CI), Permutation Importance -> `data/processed/metrics.json`
6.  **Reporting**: Aggregate -> `results/final_report.md`

## Entity Definitions

### AlloyRecord (Input/Processed)
Represents a single aluminum alloy entry.
-   `id`: Unique identifier (string)
-   `source`: "materials/alloy-elastic"
-   `composition`: Object containing atomic fractions.
    -   `Cu`: float (0.0 - 1.0)
    -   `Mg`: float
    -   `Si`: float
    -   `Zn`: float
    -   `Mn`: float
    -   `Al`: float (Calculated as 1.0 - sum(others))
-   `properties`: Object containing elastic constants.
    -   `poissons_ratio`: float (0.0 - 0.5)
    -   `youngs_modulus`: float (GPa)
-   `metadata`:
    -   `is_independent_measurement`: boolean (True if ultrasonic, False if derived)
    -   `exclusion_reason`: string (null if included)

### ModelMetrics (Output)
-   `cv_mae_mean`: float (Mean Absolute Error from Repeated 5-Fold CV)
-   `cv_mae_ci_lower`: float (95% CI Lower Bound)
-   `cv_mae_ci_upper`: float (95% CI Upper Bound)
-   `n_samples_total`: int
-   `model_type`: "RandomForest"
-   `transform`: "ILR"
-   `cv_repeats`: int (5)

### CollinearityDiagnostic (Output)
-   `vif_scores`: Object mapping element name to VIF float.
    -   `Cu`: float
    -   `Mg`: float
    -   `Si`: float
    -   `Zn`: float
    -   `Mn`: float
-   `max_vif`: float
-   `flag`: boolean (True if max_vif > 5; expected to be True)
-   `interpretation`: string (Explains that high VIF confirms closure problem)

### FeatureImportanceSummary (Output)
-   `rankings`: List of objects (element, importance_score, rank).
-   `top_two_elements`: List of strings (element names).
-   `importance_ratio`: float (Importance of 1st / Importance of 2nd).
-   `method`: "Permutation Importance on ILR Features"

## Schema Constraints

-   **Composition Sum**: `Cu + Mg + Si + Zn + Mn + Al` must equal `1.0` (within tolerance 1e-6).
-   **Exclusion Threshold**: If `Cu + Mg + Si + Zn + Mn < 0.95`, the record is excluded.
-   **Unit Consistency**: `youngs_modulus` must be in GPa. `poissons_ratio` is dimensionless.
-   **Data Types**: All numeric fields must be floats. No NaNs allowed in processed data.

## Error Handling

-   **Missing Data**: If `poissons_ratio` or any required element is missing, the record is dropped and logged.
-   **Unit Mismatch**: If `youngs_modulus` is in MPa, convert to GPa. If ambiguous, drop and log.
-   **API Failure**: If `materials/alloy-elastic` is unreachable, the pipeline exits with code 1.