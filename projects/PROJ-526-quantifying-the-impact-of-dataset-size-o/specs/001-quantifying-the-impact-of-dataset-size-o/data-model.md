# Data Model: Quantifying the Impact of Dataset Size on ML Accuracy for Material Properties

## 1. Entity Definitions

### 1.1 MaterialEntry
Represents a single material record with composition and target property.
*   `material_id` (str): Unique identifier.
*   `composition` (dict): Elemental composition (e.g., `{"Fe": 2, "O": 3}`).
*   `property_value` (float): The target property value (e.g., formation energy).
*   `property_class` (str): Classification (e.g., "electronic", "mechanical", "thermal").
*   `source_dataset` (str): Source identifier (e.g., "aflow_thermal").

### 1.2 FeatureVector
Composition-only descriptor representation.
*   `material_id` (str): Foreign key to `MaterialEntry`.
*   `magpie_features` (array[float]): The 145-dimensional Magpie vector.
*   `feature_hash` (str): SHA256 of the feature vector for integrity.

### 1.3 LearningCurve
Records model performance at a specific dataset size.
*   `property_name` (str): Name of the target property.
*   `sample_size` (int): Number of training samples.
*   `mae` (float): Mean Absolute Error on test set.
*   `random_seed` (int): Seed used for this specific training run.
*   `run_id` (str): Unique identifier for the run.

### 1.4 ScalingResult
Aggregated results for a property.
*   `property_name` (str): Name of the property.
*   `scaling_exponent_b` (float or null): The fitted exponent $b$.
*   `intercept_a` (float or null): The fitted intercept $a$.
*   `r_squared` (float): Goodness of fit.
*   `fit_status` (str): "power-law" or "non-power-law".
*   `descriptor_complexity` (float): Shannon entropy of elemental distribution (replaces 'Spatial Locality').
*   `target_heterogeneity` (float): Coefficient of variation of property values (replaces 'Symmetry Sensitivity').
*   `shuffled_baseline_mae` (float): MAE from the shuffled label baseline model.

## 2. Data Flow

1.  **Ingestion**: Raw JSON/Parquet from verified URLs $\to$ `data/raw/`.
2.  **Processing**: Raw $\to$ `data/processed/magpie_features.csv` (with checksum).
3.  **Baseline**: `magpie_features.csv` + `property_values` (shuffled) $\to$ `data/processed/shuffled_baseline.csv`.
4.  **Training**: `magpie_features.csv` + `property_values` $\to$ `data/processed/learning_curves.csv`.
5.  **Analysis**: `learning_curves.csv` $\to$ `data/processed/scaling_results.csv`.
6.  **Final**: `scaling_results.csv` $\to$ `data/processed/final_analysis.csv`.

## 3. Constraints & Validation

*   **No Nulls**: Feature vectors must not contain nulls.
*   **Consistency**: `material_id` must be consistent across raw and processed files.
*   **Type Safety**: All floats must be `float32` or `float64`; integers for counts.
*   **Checksum**: Every file in `data/processed` must have a corresponding entry in `data/checksums.json`.
*   **Descriptor Fidelity**: No structural features (lattice, space group) are included in `magpie_features`.