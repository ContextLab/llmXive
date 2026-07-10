# Data Model: Predicting Yield Strength of BCC Alloys

## 1. Entity Definitions

### AlloyRecord
Represents a single alloy entry from the raw dataset.
*   `system_id`: string (Unique identifier, e.g., "MPEA-001")
*   `elemental_composition`: dict (Key: Element symbol, Value: Atomic fraction)
*   `yield_strength`: float (MPa)
*   `crystal_structure`: string (e.g., "BCC", "FCC", "HCP")
*   `source`: string (e.g., "MPEA_DB")
*   `notes`: string (Optional metadata)

### CompositionalDescriptor
Derived features for a single alloy.
*   `system_id`: string (FK to AlloyRecord)
*   `delta_radius`: float (Atomic radius mismatch %)
*   `vec`: float (Valence Electron Concentration)
*   `mixing_entropy`: float (J/mol-K)
*   `mixing_enthalpy`: float (kJ/mol)
*   `electronegativity_diff`: float (Electronegativity difference)
*   `ilr_features`: list[float] (Transformed compositional features)
*   `raw_composition`: dict (Preserved for traceability)
*   `feature_source`: string (e.g., "MPEA_Supp_Data" for enthalpy parameters)
*   `vif_score`: float (Optional; Variance Inflation Factor for scalar descriptors)

### ModelPerformance
Evaluation results for a specific model.
*   `model_type`: string ("RandomForest", "GradientBoosting", "Ridge")
*   `r_squared`: float
*   `mae`: float (MPa)
*   `rmse`: float (MPa)
*   `confidence_interval`: tuple[float, float] (95% CI for R²)
*   `feature_importance`: list[tuple] (Feature name, importance score)
*   `validation_method`: string ("Repeated5FoldCV")

## 2. Data Flow

1.  **Raw Input**: Parquet/CSV with mixed structures.
2.  **Filtering**: Keep only `crystal_structure == "BCC"` and `yield_strength` is not null.
3.  **Normalization**: Atomic fractions normalized to sum to 1.0.
4.  **Feature Engineering**: Calculate descriptors and apply ILR.
5.  **VIF Check**: Calculate VIF for scalar descriptors; exclude if > 5.
6.  **Modeling**: Train models, generate metrics.

## 3. File Formats

*   **Input**: Parquet (preferred) or CSV.
*   **Intermediate**: JSON logs for rejected entries.
*   **Output**: Parquet (processed data), JSON (model metrics).
