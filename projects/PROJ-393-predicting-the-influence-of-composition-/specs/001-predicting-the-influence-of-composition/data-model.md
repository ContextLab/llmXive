# Data Model: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

## 1. Entity Definitions

### AlloyEntry
Represents a single experimental measurement of a Heusler alloy.
-   **id**: Unique string identifier (UUID).
-   **composition**: Dictionary of element -> atomic fraction (sums to 1.0).
-   **hysteresis_coercivity**: Float (Oe).
-   **hysteresis_saturation**: Float (emu/g).
-   **source_type**: Enum ["NIST", "Journal", "Manual"].
-   **synthesis_method**: String (e.g., "Arc-melted", "Sputtered").
-   **crystal_structure**: String (e.g., "L2_1", "B2").
-   **is_dft**: Boolean (Must be False for training targets).
-   **raw_source**: String (URL or citation key).

### CompositionDescriptor
Represents the engineered feature set for an `AlloyEntry`.
-   **alloy_id**: Foreign key to `AlloyEntry`.
-   **avg_electronegativity**: Float.
-   **vec**: Float (Valence Electron Concentration).
-   **atomic_radii_variance**: Float.
-   **avg_d_electrons**: Float.
-   **atomic_size_mismatch**: Float.

### ModelResult
Represents the output of a trained model.
-   **model_type**: Enum ["Linear", "RandomForest"].
-   **target_variable**: Enum ["coercivity", "saturation"].
-   **r2_cv**: Float (Mean cross-validated R²).
-   **mae_cv**: Float (Mean cross-validated MAE).
-   **f_statistic**: Float.
-   **p_value**: Float.
-   **feature_importance**: Dictionary of feature name -> importance score.
-   **bootstrap_ci_lower**: Float (95% CI lower bound for R²).
-   **bootstrap_ci_upper**: Float (95% CI upper bound for R²).
-   **sc006_status**: String ("Exploratory Benchmark Met", "Exploratory Benchmark Not Met").
-   **data_scarcity_warning**: Boolean.
-   **interpretation_disclaimer**: String (Mandatory text).
-   **microstructure_note**: String (Mandatory text).
-   **residual_confounding_check**: String.

## 2. Data Flow Diagram

1.  **Ingestion**: Raw files (JSON, CSV, PDF text) -> `raw/` directory.
2.  **Preprocessing**: `raw/` -> Standardized `processed/alloys_clean.csv` (filters DFT, normalizes units, **MICE imputation**).
3.  **Feature Engineering**: `alloys_clean.csv` -> `processed/alloys_features.csv` (adds descriptors).
4.  **Training**: `alloys_features.csv` -> `models/model_artifacts/` (pickle files) + `reports/metrics.json`.
5.  **Validation**: `models/` + `processed/` -> `reports/figures/` (PDPs, F-test results).
6.  **Reporting**: Aggregation of metrics, warnings, and disclaimers into `docs/reports/final_report.md`.

## 3. Data Integrity Rules

-   **Composition Sum**: $\sum c_i = 1.0 \pm 0.0001$.
-   **Unit Consistency**: All coercivity must be converted to Oe; all saturation to emu/g.
-   **Missing Data**:
    -   **Primary Strategy**: Apply **Multiple Imputation by Chained Equations (MICE)** for missing values.
    -   **Secondary Strategy**: If >50% of a row is missing, perform listwise deletion.
    -   "Not measurable" -> Treated as missing (NaN).
    -   "Zero" -> Treated as valid 0.0.
-   **DFT Exclusion**: Any row with `is_dft == True` is excluded from the training target set.
-   **Completeness Metrics**: Calculate and store the proportion of valid data points per source (SC-004).