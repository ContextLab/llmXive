# Data Model: Predicting the Ductility of Additively Manufactured Nickel-Based Superalloys

## Entity-Relationship Overview

The data model consists of three primary entities: `BuildRecord`, `MixedEffectsResult`, and `PredictiveModelArtifact`.

### BuildRecord
Represents a single additive manufacturing experiment.
- **Primary Key**: `record_id`
- **Predictors**: `laser_power_W`, `scan_speed_mm_per_s`, `hatch_spacing_um`, `layer_thickness_um`, `energy_density_J_per_mm3`
- **Outcome**: `ductility_percent`
- **Categorical**: `alloy_family` (e.g., "Inconel 718"), binary flags for elemental presence (`has_Cr`, `has_Al`, `has_Ti`).
- **Source**: Derived from parsed supplementary tables of the four cited papers.

### MixedEffectsResult
Stores the output of the LME analysis.
- **Fixed Effects**: Coefficients, SE, CI, p-values.
- **Random Effects**: Variance components for alloy families.
- **Metrics**: Partial R², Likelihood Ratio Test statistic.
- **Feature Set**: Indicates whether the model used "Components" or "Energy Density".

### PredictiveModelArtifact
Stores the trained XGBoost model and its metadata.
- **Model**: Serialized XGBoost booster.
- **Metrics**: CV Mean R², MAE, RMSE.
- **Importance**: Permutation feature importance scores (aligned with LME feature set).

### ReportOutput
Stores the final report artifacts.
- **Tables**: Standardized coefficients, model metrics.
- **Plots**: Partial Dependence Plots (PDP) for top 3 features.

## Data Flow

1.  **Acquisition**: Parse paper tables (PDF/Excel) → `raw_build_records.csv`.
2.  **Cleaning**: Unit conversion, missing value removal, Composition Mapping → `cleaned_build_records.csv`.
3.  **Engineering**: Energy density calculation, VIF check, **Conditional Feature Selection** → `processed_build_records.csv`.
4.  **Modeling**:
    - `processed_build_records.csv` → LME Model → `lme_results.json`
    - `processed_build_records.csv` → XGBoost Model (LOAFO CV) → `xgboost_model.json`, `model_metrics.json`
5.  **Reporting**: Aggregation of results + **PDP Generation** → `final_report.md`.

## Schema Definitions

See `contracts/` for formal YAML schemas.
