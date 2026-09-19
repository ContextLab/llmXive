# Data Model: Predicting the Impact of Laser Surface Texturing on Wear Resistance

## Overview

This document defines the data structures, schemas, and transformation rules for the LST wear resistance project. It ensures that data flows consistently from ingestion through modeling to reporting.

## Canonical Schema

The core entity is the `LSTRecord`. All intermediate and final datasets will conform to this schema.

| Column Name | Type | Description | Constraints |
|-------------|------|-------------|-------------|
| `pulse_duration` | float | Laser pulse duration (ns or µs) | Required predictor; no missing values allowed. |
| `power` | float | Laser power (W) | Required predictor; no missing values allowed. |
| `scanning_speed` | float | Scanning speed (mm/s) | Required predictor; no missing values allowed. |
| `pattern_geometry` | string | Textured pattern type (e.g., "grid", "dot", "line") | Required predictor; categorical. |
| `hardness` | float | Material hardness (HV or GPa) | Required predictor; no missing values allowed. |
| `elastic_modulus` | float | Elastic modulus (GPa) | Required predictor; no missing values allowed. |
| `contact_load` | float | Contact load (N) | Optional; missing values trigger `normalization_method='raw'`. |
| `sliding_speed` | float | Sliding speed (m/s) | Optional; missing values trigger `normalization_method='raw'`. |
| `wear_rate` | float | Raw wear rate (mm³/N·m or similar) | Required target. |
| `material_class` | string | Base material category (e.g., "Steel", "Aluminum") | Derived from `hardness`/`elastic_modulus` or source metadata. |
| `normalization_method` | string | "archard" or "raw" | Derived: "raw" if `contact_load` or `sliding_speed` missing. |
| `wear_coefficient` | float | Calculated specific wear coefficient (K) | Derived: $K = \frac{V \cdot H}{F \cdot L}$ (Corrected Archard). |
| `unit_conversion_status` | string | "valid", "unavailable", "failed" | Derived: "unavailable" if area/density missing for unit conversion. |
| `data_source` | string | "openml", "zenodo", "literature", "synthetic" | Derived: indicates origin of record. |

## Data Flow

### 1. Raw Data (data/raw)
*   **Source**: Verified CSVs from OpenML, Zenodo.
*   **State**: Immutable. Downloaded once, checksummed.
*   **Schema**: Source-specific (mapped via `schema_map.json`).

### 2. Preprocessed Data (data/processed)
*   **State**: Derived. Contains cleaned, standardized records.
*   **Transformations**:
    *   Column renaming to Canonical Schema.
    *   Dropping records with missing required predictors.
    *   Calculating `wear_coefficient` using the corrected Archard formula ($K = \frac{V \cdot H}{F \cdot L}$) with explicit unit conversion.
    *   One-hot encoding for `pattern_geometry` (handled in `FeatureMatrix`).

### 3. Feature Matrix (In Memory / Temporary)
*   **State**: Transient, used for model training.
*   **Structure**:
    *   `X`: Numerical features (scaled) + One-hot encoded categorical features.
    *   `y`: `wear_rate` or `wear_coefficient` (depending on analysis subset).
    *   `groups`: `material_class` for LOO-CV.

### 4. Model Artifacts (models/)
*   **State**: Serialized models (`.pkl`).
*   **Content**: Best model object, scaler parameters, feature names.

### 5. Reports (reports/)
*   **State**: JSON/CSV/Plots.
*   **Content**: Metrics, SHAP values, validation logs.

## Transformation Logic

### Missing Value Handling
*   **Predictors**: If `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, or `elastic_modulus` is null/NaN -> **DROP RECORD**.
*   **Load/Speed**: If `contact_load` or `sliding_speed` is null -> **RETAIN RECORD**, set `normalization_method='raw'`, keep `wear_rate` as target.

### Archard Normalization (Corrected)
*   **Formula**: $K = \frac{wear\_rate \cdot hardness}{contact\_load \cdot sliding\_speed}$ (assuming wear_rate is volume-based; adjust if rate is length-based).
    *   **Unit Conversion**: Explicitly convert `wear_rate` to volume (if needed), `hardness` to Pa, `contact_load` to N, and `sliding_speed` to m/s to ensure dimensional consistency.
    *   **Condition**: Only applied if `contact_load` and `sliding_speed` are present and > 0, AND `contact_area` or `density` is available for unit conversion if needed.
    *   **Fallback**: If either `contact_load` or `sliding_speed` is missing, `wear_coefficient` = `wear_rate`, `normalization_method` = 'raw'. If unit conversion data is missing, `unit_conversion_status` = 'unavailable' and the record is excluded from the normalized set.

### Feature Engineering
*   **Interaction Terms**: If `power` and `scanning_speed` are present, `line_energy` = `power` / `scanning_speed` (optional, subject to VIF check).
*   **Categorical Encoding**: `pattern_geometry` -> One-Hot Encoding (binary columns).

## Data Quality Checks

1.  **Completeness**: Verify `normalized_count` and `raw_count` meet thresholds (SC-004).
2.  **Variance**: Check for zero-variance features (drop if found).
3.  **Collinearity**: Calculate VIF. If VIF > 5 for any pair, flag for exclusion (FR-010).
4.  **Material Classes**: Count unique `material_class` values. If < 3, trigger LOO-CV fallback warning.
5.  **Physical Validation**: Check for `microstructural_features` column. If missing, set `validation_status: 'validation_target_unavailable'` (SC-002).
6.  **Unit Conversion**: Verify `unit_conversion_status` is 'valid' for normalized records. If 'unavailable', exclude from normalized set.