# Data Model: Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel

## 1. Entity Definitions

### 1.1 ProcessParameters
Represents the input settings for the LPBF process.
-   **laser_power**: float (W)
-   **scan_speed**: float (mm/s)
-   **hatch_spacing**: float (mm)
-   **layer_thickness**: float (mm)

### 1.2 PorosityMeasurement
The target variable.
-   **porosity**: float (%)

### 1.3 DerivedFeatures
Calculated physical quantities.
-   **volumetric_energy_density**: float (J/mm³)
  -   Formula: $E_v = P / (v \cdot h \cdot t)$

### 1.4 ModelPerformance
Evaluation metrics.
-   **fold_id**: int
-   **model_type**: string (GB, MLP)
-   **rmse**: float
-   **r2**: float

## 2. Data Flow

1.  **Raw Input**: CSV/Parquet/HDF5 from verified URL.
2.  **Preprocessed**:
    -   Columns: `laser_power`, `scan_speed`, `hatch_spacing`, `layer_thickness`, `porosity`.
    -   Derived: `volumetric_energy_density`.
    -   Scaled: `laser_power_norm`, `scan_speed_norm`, etc.
3.  **Training Input**: Either `[raw_norm]` OR `[ev_norm]` (never both).
4.  **Output**:
    -   Model artifacts (`.pkl`).
    -   Metrics (JSON).
    -   Plots (PNG).

## 3. Schema Constraints

-   **Missing Values**: Must be 0 in the final training set.
-   **Ranges**:
    -   Normalized features: $[0, 1]$.
    -   Porosity: $\ge 0$.
-   **Data Types**: All numerical inputs must be `float64`.